"""
ASR Manager Implementation

Migrated from root asr_model.py with improvements.
"""

import torch
from transformers import AutoProcessor, AutoModelForCTC
from typing import Optional, Tuple, Dict
import numpy as np


class ASRModelManager:
    """
    Manages ASR model loading and transcription.

    Handles model caching, device management, and transcription.
    """

    def __init__(self, default_model: str, model_options: dict, device: Optional[str] = None):
        """
        Initialize ASR manager.

        Args:
            default_model: Default model name for fallback
            model_options: Dictionary of available model options
            device: Device to use ('cuda' or 'cpu'). Auto-detect if None.
        """
        self.default_model = default_model
        self.model_options = model_options

        self.processor = None
        self.model = None
        self.model_name = None

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def load_model(self, model_name: str, hf_token: Optional[str] = None) -> None:
        """
        Load ASR model from Hugging Face.

        Args:
            model_name: Model identifier
            hf_token: Hugging Face API token (optional)

        Raises:
            RuntimeError: If model loading fails
        """
        # Skip if already loaded
        if (self.model is not None and
            self.processor is not None and
            self.model_name == model_name):
            return

        try:
            self._load_model_internal(model_name, hf_token)
        except Exception as e:
            # Try fallback if not already using it
            if model_name != self.default_model:
                self._load_model_internal(self.default_model, hf_token)
            else:
                raise RuntimeError(f"Failed to load ASR model: {e}")

    def _load_model_internal(self, model_name: str, hf_token: Optional[str]) -> None:
        """Internal method to load model."""
        kwargs = {"token": hf_token} if hf_token else {}

        # Load processor and model
        self.processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=False,
            local_files_only=False,
            **kwargs
        )

        self.model = AutoModelForCTC.from_pretrained(
            model_name,
            trust_remote_code=False,
            local_files_only=False,
            **kwargs
        )

        # Move to device
        self.model = self.model.to(self.device)
        self.model_name = model_name

    def _is_phoneme_model(self) -> bool:
        """
        Detect if the model outputs phonemes directly.

        Returns:
            True if model is phoneme-based
        """
        if self.processor is None:
            return False

        vocab = self.processor.tokenizer.get_vocab()
        phoneme_markers = ["AA", "AE", "AH", "SH", "NG", "TH", "DH", "ZH"]

        return any(p in vocab for p in phoneme_markers)

    def transcribe(
        self,
        audio: np.ndarray,
        sr: int,
        use_g2p: bool = True,
        lang: str = "en-us"
    ) -> Tuple[str, str]:
        """
        Transcribe audio to text and phonemes.

        Args:
            audio: Audio waveform (numpy array)
            sr: Sample rate
            use_g2p: Use grapheme-to-phoneme conversion
            lang: Language code for G2P

        Returns:
            Tuple of (decoded_text, phoneme_string)

        Raises:
            RuntimeError: If model not loaded
        """
        if self.processor is None or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Convert to numpy array if needed
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio)

        # Preprocess
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

        # Extract logits
        if hasattr(outputs, "logits"):
            logits = outputs.logits
        else:
            raise RuntimeError("Model output has no logits. Unsupported model type.")

        # Decode
        pred_ids = torch.argmax(logits, dim=-1)
        decoded = self.processor.batch_decode(pred_ids, skip_special_tokens=True)[0]

        # Phoneme conversion
        recorded_phoneme_str = decoded

        # If model already emits phonemes, skip G2P
        if self._is_phoneme_model():
            return decoded, decoded

        # Optional G2P conversion
        if use_g2p:
            try:
                from gruut import sentences
                ph_parts = []
                for sent in sentences(decoded, lang=lang):
                    for w in sent:
                        ph_parts.append(" ".join(w.phonemes) if w.phonemes else w.text)
                recorded_phoneme_str = " ".join(ph_parts)
            except Exception:
                # Fallback to decoded text if G2P fails
                pass

        return decoded, recorded_phoneme_str

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.processor is not None
