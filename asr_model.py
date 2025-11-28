import torch
from transformers import AutoProcessor, AutoModelForCTC
import streamlit as st
from typing import Optional, Tuple
import traceback


# -------------------------------------------------------
# 1. Cache real: fuera de la clase (Streamlit requirement)
# -------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_hf_model_cached(model_name: str, hf_token: Optional[str]):
    """Loads processor + base model from Hugging Face (cached globally)."""
    
    kwargs = {"token": hf_token} if hf_token else {}

    processor = AutoProcessor.from_pretrained(
        model_name,
        trust_remote_code=False,
        local_files_only=False,
        **kwargs
    )

    # Use the ForCTC variant so model outputs logits suitable for CTC decoding
    model = AutoModelForCTC.from_pretrained(
        model_name,
        trust_remote_code=False,
        local_files_only=False,
        **kwargs
    )

    return processor, model


# -------------------------------------------------------
# 2. ASR Manager
# -------------------------------------------------------
class ASRModelManager:
    def __init__(self, default_model: str, model_options: dict):
        self.default_model = default_model
        self.model_options = model_options

        self.processor = None
        self.model = None
        self.model_name = None

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    # -------------------------------------------------------
    # Load model with fallback
    # -------------------------------------------------------
    def load_model(self, model_name: str, hf_token: Optional[str] = None):
        try:
            with st.spinner(f"📥 Loading model: {model_name}..."):
                proc, mdl = load_hf_model_cached(model_name, hf_token)

                # Move model to device here (can't be inside cached function)
                self.processor = proc
                self.model = mdl.to(self.device)
                self.model_name = model_name

                st.toast(f"✅ Model loaded: {model_name}", icon="🎤")

        except Exception as e:
            st.warning(f"⚠️ Failed to load {model_name}: {e}")
            st.text(traceback.format_exc())

            # Try fallback
            if model_name != self.default_model:
                st.info(f"🔄 Trying fallback model: {self.default_model}")

                try:
                    proc, mdl = load_hf_model_cached(self.default_model, hf_token)
                    self.processor = proc
                    self.model = mdl.to(self.device)
                    self.model_name = self.default_model
                    st.success(f"✅ Fallback loaded: {self.default_model}")
                except Exception as e2:
                    st.error(f"❌ Fallback failed: {e2}")
                    st.text(traceback.format_exc())
                    raise

    # -------------------------------------------------------
    # Detect if this is a phoneme tokenizer
    # -------------------------------------------------------
    def _is_phoneme_model(self) -> bool:
        if self.processor is None:
            return False
        
        vocab = self.processor.tokenizer.get_vocab()
        phoneme_markers = ["AA", "AE", "AH", "SH", "NG", "TH", "DH", "ZH"]

        return any(p in vocab for p in phoneme_markers)

    # -------------------------------------------------------
    # Transcription
    # -------------------------------------------------------
    def transcribe(self, audio, sr, use_g2p: bool = True, lang: str = "en-us") -> Tuple[str, str]:

        if self.processor is None or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Preprocess safely
        inputs = self.processor(
            audio,
            sampling_rate=sr,
            return_tensors="pt",
            padding="longest",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Many ASR models output .logits (Wav2Vec2, XLS-R, etc.)
        if hasattr(outputs, "logits"):
            logits = outputs.logits
        else:
            raise RuntimeError("Model output has no logits. Unsupported model type.")

        pred_ids = torch.argmax(logits, dim=-1)
        decoded = self.processor.batch_decode(pred_ids, skip_special_tokens=True)[0]

        # -------------------------------------------------------
        # Output for pronunciation analysis
        # -------------------------------------------------------
        recorded_phoneme_str = decoded

        # If model already emits phonemes, skip G2P
        if self._is_phoneme_model():
            return decoded, decoded

        # Optional G2P (for English, Spanish, etc.)
        if use_g2p:
            try:
                from gruut import sentences
                ph_parts = []
                for sent in sentences(decoded, lang=lang):
                    for w in sent:
                        ph_parts.append(" ".join(w.phonemes) if w.phonemes else w.text)
                recorded_phoneme_str = " ".join(ph_parts)

            except Exception as e:
                st.warning(f"G2P failed: {e}")

        return decoded, recorded_phoneme_str
