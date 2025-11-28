#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Processing Module
Handles audio loading, conversion, and TTS generation
"""

import io
from typing import Optional, Tuple
import numpy as np
import streamlit as st


class AudioProcessor:
    """Manages audio processing operations including loading and format conversion"""

    @staticmethod
    def load_from_bytes(audio_bytes: bytes, target_sr: int = 16000) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Load audio from bytes and convert to numpy array

        Tries multiple methods in order:
        1. soundfile (most reliable for WAV)
        2. librosa (good for various formats)
        3. torchaudio (PyTorch-based fallback)

        Args:
            audio_bytes: Audio data as bytes
            target_sr: Target sample rate (default: 16000 Hz)

        Returns:
            Tuple of (waveform as numpy array, sample rate) or (None, None) on failure
        """
        # Method 1: Try with soundfile (most reliable for WAV)
        try:
            import soundfile as sf
            audio_file = io.BytesIO(audio_bytes)
            waveform, sr = sf.read(audio_file, dtype='float32')

            # Convert to mono if stereo
            if waveform.ndim > 1 and waveform.shape[1] > 1:
                waveform = waveform.mean(axis=1)

            # Resample if necessary
            if sr != target_sr:
                waveform = AudioProcessor._resample_with_librosa(waveform, sr, target_sr)

            # Ensure it's a 1D array
            if waveform.ndim > 1:
                waveform = waveform.flatten()

            return waveform.astype(np.float32), target_sr

        except Exception as e1:
            # Method 2: Try with librosa
            try:
                import librosa
                audio_file = io.BytesIO(audio_bytes)
                waveform, sr = librosa.load(audio_file, sr=target_sr, mono=True)
                return waveform.astype(np.float32), target_sr

            except Exception as e2:
                # Method 3: Try with torchaudio
                try:
                    import torchaudio
                    import torch

                    audio_file = io.BytesIO(audio_bytes)
                    waveform, sr = torchaudio.load(audio_file)

                    # Convert to mono if stereo
                    if waveform.ndim > 1 and waveform.shape[0] > 1:
                        waveform = waveform.mean(dim=0)

                    # Resample if necessary
                    if sr != target_sr:
                        waveform = torchaudio.transforms.Resample(sr, target_sr)(waveform)

                    # Convert to numpy
                    waveform_np = waveform.numpy() if isinstance(waveform, torch.Tensor) else waveform

                    # Ensure 1D
                    if waveform_np.ndim > 1:
                        waveform_np = waveform_np.flatten()

                    return waveform_np.astype(np.float32), target_sr

                except Exception as e3:
                    # All methods failed
                    st.error(f"Failed to load audio with all methods:")
                    st.error(f"- soundfile: {e1}")
                    st.error(f"- librosa: {e2}")
                    st.error(f"- torchaudio: {e3}")
                    return None, None

    @staticmethod
    def _resample_with_librosa(waveform: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio using librosa

        Args:
            waveform: Input audio waveform
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled waveform
        """
        import librosa
        return librosa.resample(waveform, orig_sr=orig_sr, target_sr=target_sr)

    @staticmethod
    def convert_to_mono(waveform: np.ndarray) -> np.ndarray:
        """
        Convert stereo audio to mono

        Args:
            waveform: Input audio waveform (can be mono or stereo)

        Returns:
            Mono waveform
        """
        if waveform.ndim > 1 and waveform.shape[1] > 1:
            return waveform.mean(axis=1)
        return waveform

    @staticmethod
    def normalize_audio(waveform: np.ndarray, target_level: float = 0.95) -> np.ndarray:
        """
        Normalize audio to target level

        Args:
            waveform: Input audio waveform
            target_level: Target peak level (0.0 to 1.0)

        Returns:
            Normalized waveform
        """
        max_val = np.abs(waveform).max()
        if max_val > 0:
            return waveform * (target_level / max_val)
        return waveform


class TTSGenerator:
    """Handles Text-to-Speech generation"""

    @staticmethod
    @st.cache_data
    def generate_audio(text: str, lang: str = "en") -> Optional[bytes]:
        """
        Generate TTS audio using gTTS

        Args:
            text: Text to convert to speech
            lang: Language code (default: "en" for English)

        Returns:
            Audio bytes in MP3 format, or None on failure
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=lang, slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp.getvalue()

        except Exception as e:
            st.error(f"TTS generation failed: {e}")
            return None

    @staticmethod
    @st.cache_data
    def generate_slow_audio(text: str, lang: str = "en") -> Optional[bytes]:
        """
        Generate slow TTS audio for pronunciation practice

        Args:
            text: Text to convert to speech
            lang: Language code (default: "en" for English)

        Returns:
            Audio bytes in MP3 format, or None on failure
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=lang, slow=True)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp.getvalue()

        except Exception as e:
            st.error(f"Slow TTS generation failed: {e}")
            return None


class AudioValidator:
    """Validates audio data and properties"""

    @staticmethod
    def is_valid_sample_rate(sr: int) -> bool:
        """Check if sample rate is valid (common audio sample rates)"""
        valid_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 96000]
        return sr in valid_rates

    @staticmethod
    def is_silent(waveform: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Check if audio is silent or near-silent

        Args:
            waveform: Audio waveform
            threshold: Silence threshold (default: 0.01)

        Returns:
            True if audio is silent, False otherwise
        """
        return np.abs(waveform).max() < threshold

    @staticmethod
    def get_duration(waveform: np.ndarray, sr: int) -> float:
        """
        Get audio duration in seconds

        Args:
            waveform: Audio waveform
            sr: Sample rate

        Returns:
            Duration in seconds
        """
        return len(waveform) / sr

    @staticmethod
    def validate_audio_data(waveform: Optional[np.ndarray], sr: Optional[int]) -> Tuple[bool, str]:
        """
        Validate audio data

        Args:
            waveform: Audio waveform
            sr: Sample rate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if waveform is None or sr is None:
            return False, "Audio data is None"

        if len(waveform) == 0:
            return False, "Audio waveform is empty"

        if AudioValidator.is_silent(waveform):
            return False, "Audio appears to be silent"

        if not AudioValidator.is_valid_sample_rate(sr):
            return False, f"Unusual sample rate: {sr} Hz"

        duration = AudioValidator.get_duration(waveform, sr)
        if duration < 0.1:
            return False, f"Audio too short: {duration:.2f} seconds"

        if duration > 300:  # 5 minutes
            return False, f"Audio too long: {duration:.2f} seconds"

        return True, "Valid"
