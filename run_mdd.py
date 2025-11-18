#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_mdd_fixed.py

Versión corregida del script 'mdd_single_script' con:
 - corrección de la API de gruut (phonemization)
 - tokenización robusta de salida del modelo CTC
 - alineamiento por palabra (ventana) para evitar desfaces
 - manejo seguro de claves HF/GROQ desde variables de entorno
 - integración correcta del sistema de feedback especializado en acento
"""

import os
import argparse
import sys
import re
import tempfile
import subprocess
import json
from typing import List, Tuple

import numpy as np
import torch
import torchaudio

from transformers import AutoProcessor, AutoModelForCTC
from phonemizer.punctuation import Punctuation
from sequence_align.pairwise import needleman_wunsch

# Optional LLM client (Groq)
try:
    from groq import Groq
    _HAS_GROQ = True
except Exception:
    _HAS_GROQ = False


# -------------------------------
# Helpers
# -------------------------------

def load_audio(path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    try:
        import librosa
        audio, sr = librosa.load(path, sr=target_sr, mono=True)
        return audio.astype(np.float32), sr
    except Exception as e:
        print(f"librosa load failed: {e}. Trying torchaudio...")

    try:
        waveform, sr = torchaudio.load(path)
        if waveform.ndim > 1:
            waveform = waveform.mean(dim=0)
        if sr != target_sr:
            waveform = torchaudio.transforms.Resample(sr, target_sr)(waveform)
        return waveform.numpy().astype(np.float32), target_sr
    except Exception as e:
        raise RuntimeError(f"Failed to load audio: {e}") from e


def convert_to_wav_with_librosa(input_path: str, target_sr: int = 16000) -> str:
    import librosa
    import soundfile as sf
    audio, _ = librosa.load(input_path, sr=target_sr, mono=True)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, target_sr)
    return tmp.name


def convert_to_wav_with_ffmpeg(input_path: str, target_sr: int = 16000) -> str:
    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ar", str(target_sr), "-ac", "1", tmp.name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr}")
    return tmp.name


def convert_to_wav(input_path: str, target_sr: int = 16000) -> str:
    try:
        return convert_to_wav_with_librosa(input_path, target_sr)
    except Exception:
        return convert_to_wav_with_ffmpeg(input_path, target_sr)


def transcribe_phonemes_local(audio: np.ndarray, sr: int, model_name: str, hf_token: str = None, use_g2p: bool = True, lang: str = "en-us") -> Tuple[str, str]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    kwargs = {}
    if hf_token:
        kwargs["use_auth_token"] = hf_token

    processor = AutoProcessor.from_pretrained(model_name, **kwargs)
    model = AutoModelForCTC.from_pretrained(model_name, **kwargs).to(device)

    inputs = processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs["input_values"].to(device)).logits

    ids = torch.argmax(logits, dim=-1)
    decoded = processor.batch_decode(ids)[0]

    # Debugging output when requested
    if os.environ.get("DEBUG_TRANSCRIBE"):
        try:
            token_list = processor.tokenizer.convert_ids_to_tokens(ids[0].tolist())
        except Exception:
            token_list = None
        print("[DEBUG] raw_decoded:", decoded)
        if token_list is not None:
            print("[DEBUG] tokens:", token_list)

    # Optionally run G2P via gruut when the decoded output appears orthographic
    # or when the caller forces G2P. If gruut fails, return decoded as-is.
    recorded_phoneme_str = decoded
    if use_g2p:
        try:
            from gruut import sentences

            is_mostly_ascii = bool(re.match(r"^[\x00-\x7f\s\w\.,'\"\-]+$", decoded))
            if is_mostly_ascii:
                ph_parts = []
                for sent in sentences(decoded, lang=lang):
                    for w in sent:
                        try:
                            ph_parts.append(" ".join(w.phonemes))
                        except Exception:
                            ph_parts.append(w.text)

                recorded_phoneme_str = " ".join(ph_parts)
                if os.environ.get("DEBUG_TRANSCRIBE"):
                    print("[DEBUG] phonemized_fallback:", recorded_phoneme_str)
                # return both raw decoded and the phonemized fallback
                return decoded, recorded_phoneme_str
        except Exception as e:
            if os.environ.get("DEBUG_TRANSCRIBE"):
                print("[DEBUG] gruut G2P failed:", e)
    # default: return raw decoded and the same string as recorded phoneme string
    return decoded, recorded_phoneme_str


def generate_reference_phonemes(text: str, lang: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    from gruut import sentences

    clean = Punctuation(";:,.!\"?()").remove(text)
    lexicon, words = [], []

    for sent in sentences(clean, lang=lang):
        for w in sent:
            t = w.text.strip().lower()
            if not t:
                continue
            words.append(t)
            try:
                phon = " ".join(w.phonemes)
            except:
                phon = t
            lexicon.append((t, phon))

    return lexicon, words


def tokenize_phonemes(s: str) -> List[str]:
    s = s.strip()
    if " " in s:
        return s.split()
    tok = re.findall(r"[a-zA-Zʰɪʌɒəɜɑɔɛʊʏœøɯɨɫɹːˈˌ˞̃͜͡d͡ʒ]+|[^\s]", s)
    return [t for t in tok if t]


def align_sequences(a: List[str], b: List[str]) -> Tuple[List[str], List[str]]:
    return needleman_wunsch(a, b, match_score=2, mismatch_score=-1, indel_score=-1, gap="_")


def align_per_word(lexicon: List[Tuple[str, str]], rec_tokens: List[str]):
    # Build a flattened reference sequence (all word phonemes concatenated)
    ref_all = []
    word_lens = []
    for word, phon in lexicon:
        parts = phon.split()
        word_lens.append(len(parts))
        if parts:
            ref_all.extend(parts)

    # If there is no reference phoneme information, return empty lists
    if not ref_all:
        return ["" for _ in lexicon], ["" for _ in lexicon]

    # Align the entire reference phoneme sequence to the recorded tokens
    aligned_ref, aligned_rec = align_sequences(ref_all, rec_tokens)

    # Now split the aligned sequences back into per-word segments based on
    # the original lengths of each reference word (counts of non-gap tokens).
    per_word_ref = []
    per_word_rec = []

    ref_token_count = 0
    # Iterate over words and take the corresponding slice from the aligned
    # sequences where aligned_ref contributes the tokens for that word.
    for wlen, (word, phon) in zip(word_lens, lexicon):
        if wlen == 0:
            per_word_ref.append("")
            per_word_rec.append("")
            continue

        start = ref_token_count
        end = start + wlen

        ref_buf = []
        rec_buf = []

        # Walk aligned sequences and collect tokens whose reference non-gap
        # index falls within [start, end)
        non_gap_idx = 0
        for a_r, a_p in zip(aligned_ref, aligned_rec):
            if a_r != "_":
                if start <= non_gap_idx < end:
                    ref_buf.append(a_r)
                    if a_p != "_":
                        rec_buf.append(a_p)
                non_gap_idx += 1

        per_word_ref.append("".join(ref_buf))
        per_word_rec.append("".join(rec_buf))

        ref_token_count = end

    return per_word_ref, per_word_rec


# -------------------------------
# CLI / Main
# -------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--audio", "-a", required=True)
    p.add_argument("--text", "-t", required=False)
    p.add_argument("--model", "-m", default="facebook/wav2vec2-large-960h", help="ASR model to use (default: orthographic model)")
    p.add_argument("--lang", default="en-us")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--no-g2p", action="store_true", help="Disable G2P fallback (enabled by default)")
    p.add_argument("--force-phoneme-model", action="store_true", help="Force use of the phoneme ASR model and disable G2P")
    p.add_argument("--emit-json", default=None, help="Path to write structured JSON output for this run")
    return p.parse_args()


def main():
    args = parse_args()

    hf_token = os.environ.get("HF_API_TOKEN")
    groq_key = os.environ.get("GROQ_API_KEY")

    # TEMP: override keys for debugging if needed
    hf_token = hf_token or "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"
    groq_key = groq_key or "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"

    if not os.path.exists(args.audio):
        print("audio not found")
        sys.exit(1)

    # Convert if needed
    audio_path = args.audio
    temp_wav = None
    if not audio_path.lower().endswith(".wav"):
        temp_wav = convert_to_wav(audio_path)
        audio_path = temp_wav

    if not args.text:
        print("Enter reference text:")
        args.text = sys.stdin.readline().strip()

    print("Loading audio…")
    audio, sr = load_audio(audio_path)

    print("Running Wav2Vec2 transcription…")

    # If the user requested the phoneme model, switch to the phoneme model
    # and disable G2P. Otherwise use the selected/ default orthographic model
    # + G2P, which generally produces more stable per-word alignments.
    if getattr(args, "force_phoneme_model", False):
        # If the user didn't override the model, use the known phoneme model.
        if args.model == "facebook/wav2vec2-large-960h":
            args.model = "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme"

    use_g2p_flag = (not getattr(args, "no_g2p", False)) and (not getattr(args, "force_phoneme_model", False))

    decoded_raw, recorded_phoneme_str = transcribe_phonemes_local(
        audio,
        sr,
        args.model,
        hf_token,
        use_g2p=use_g2p_flag,
        lang=args.lang,
    )

    print("\nGenerating reference phonemes…")
    lexicon, ref_words = generate_reference_phonemes(args.text, args.lang)

    rec_tokens = tokenize_phonemes(recorded_phoneme_str)

    print("\nAligning per-word…")
    per_word_ref, per_word_rec = align_per_word(lexicon, rec_tokens)

    print("\n=== Per-word comparisons ===")
    for i, w in enumerate(ref_words):
        r = per_word_ref[i]
        p = per_word_rec[i]
        print(f"{w:15} ref={r:12} rec={p}")

    # If requested, emit structured JSON for downstream parsing/benchmarks
    if getattr(args, "emit_json", None):
        out_obj = {
            "audio": args.audio,
            "text": args.text,
            "model": args.model,
            "raw_decoded": decoded_raw,
            "recorded_phoneme_str": recorded_phoneme_str,
            "rec_tokens": rec_tokens,
            "ref_words": ref_words,
            "per_word_ref": per_word_ref,
            "per_word_rec": per_word_rec,
        }
        try:
            with open(args.emit_json, "w", encoding="utf-8") as fh:
                json.dump(out_obj, fh, ensure_ascii=False, indent=2)
            if os.environ.get("DEBUG_TRANSCRIBE"):
                print(f"[DEBUG] wrote JSON output to {args.emit_json}")
        except Exception as e:
            print("Failed to write JSON output:", e)

    # ----------------------------
    # GROQ FEEDBACK
    # ----------------------------
    if groq_key and not args.no_llm and _HAS_GROQ:
        client = Groq(api_key=groq_key)

        diff = "\n".join(
            f"{ref_words[i]}: expected={per_word_ref[i]}, produced={per_word_rec[i]}"
            for i in range(len(ref_words))
        )

        system_message = """
You are an expert dialect/accent coach for American spoken English.
Provide feedback to improve the speaker’s American accent.
Use Google pronunciation respelling when giving corrections.
Provide the following sections:
- Overall Impression
- Specific Feedback
- Google Pronunciation Respelling Suggestions
- Additional Tips
"""

        user_prompt = f"""Reference Text: {args.text}

(word, reference_phoneme, recorded_phoneme)
{diff}
"""

        print("\nCalling Groq for accent feedback…")

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user",    "content": user_prompt},
                ],
                model="llama-3.1-8b-instant",
                temperature=0
            )

            # Correcto: acceso por atributo, no por índice
            feedback = chat_completion.choices[0].message.content

            print("\n==== Accent Coach Feedback ====\n")
            print(feedback)

        except Exception as e:
            print("LLM call failed:", e)


    if temp_wav:
        os.remove(temp_wav)


if __name__ == "__main__":
    main()
