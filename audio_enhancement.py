#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Enhancement Module
Advanced audio preprocessing for robust L2/ESL ASR:
- Voice Activity Detection (VAD)
- Denoising (spectral subtraction & Wiener filtering)
- Normalization
- Resampling
"""

import numpy as np
from typing import Tuple, Optional
import warnings


class AudioEnhancer:
    """
    Enhanced audio preprocessing for L2 learners' speech recognition.

    Handles common issues:
    - Background noise (room noise, keyboard, etc.)
    - Silence trimming
    - Volume normalization
    - Resampling to target SR
    """

    @staticmethod
    def enhance_for_asr(
        audio: np.ndarray,
        sr: int,
        target_sr: int = 16000,
        enable_vad: bool = True,
        enable_denoising: bool = True,
        enable_normalization: bool = True,
        vad_threshold: float = 0.02,
        noise_reduction_strength: float = 0.5
    ) -> Tuple[np.ndarray, int]:
        """
        Complete audio enhancement pipeline for ASR.

        Args:
            audio: Audio waveform (1D numpy array)
            sr: Current sample rate
            target_sr: Target sample rate for ASR
            enable_vad: Enable Voice Activity Detection
            enable_denoising: Enable noise reduction
            enable_normalization: Enable volume normalization
            vad_threshold: VAD sensitivity (lower = more aggressive)
            noise_reduction_strength: Denoising strength (0-1)

        Returns:
            Tuple of (enhanced_audio, sample_rate)
        """

        # Step 1: Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # Step 2: Resample to target SR
        if sr != target_sr:
            audio = AudioEnhancer._resample(audio, sr, target_sr)
            sr = target_sr

        # Step 3: Normalization (pre-processing)
        if enable_normalization:
            audio = AudioEnhancer._normalize_audio(audio)

        # Step 4: Voice Activity Detection (trim silence)
        if enable_vad:
            audio = AudioEnhancer._apply_vad(audio, sr, threshold=vad_threshold)

        # Step 5: Denoising
        if enable_denoising:
            audio = AudioEnhancer._denoise_audio(
                audio,
                sr,
                strength=noise_reduction_strength
            )

        # Step 6: Final normalization
        if enable_normalization:
            audio = AudioEnhancer._normalize_audio(audio)

        return audio, sr

    @staticmethod
    def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        try:
            import librosa
            return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # Fallback: simple decimation/interpolation
            if orig_sr == target_sr:
                return audio

            ratio = target_sr / orig_sr
            new_length = int(len(audio) * ratio)

            return np.interp(
                np.linspace(0, len(audio) - 1, new_length),
                np.arange(len(audio)),
                audio
            )

    @staticmethod
    def _normalize_audio(audio: np.ndarray, target_level: float = 0.95) -> np.ndarray:
        """
        Normalize audio to target peak level.

        Args:
            audio: Input audio
            target_level: Target peak amplitude (0-1)

        Returns:
            Normalized audio
        """
        max_val = np.abs(audio).max()

        if max_val > 0:
            return audio * (target_level / max_val)
        else:
            return audio

    @staticmethod
    def _apply_vad(
        audio: np.ndarray,
        sr: int,
        threshold: float = 0.02,
        min_silence_duration: float = 0.3
    ) -> np.ndarray:
        """
        Voice Activity Detection: trim leading/trailing silence.

        Args:
            audio: Input audio
            sr: Sample rate
            threshold: Energy threshold for voice detection
            min_silence_duration: Minimum silence duration to trim (seconds)

        Returns:
            Trimmed audio
        """
        # Calculate frame-wise energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop

        # Compute energy per frame
        energy = np.array([
            np.sum(audio[i:i + frame_length] ** 2)
            for i in range(0, len(audio) - frame_length, hop_length)
        ])

        # Normalize energy
        energy = energy / (energy.max() + 1e-10)

        # Find voice frames
        voice_frames = energy > threshold

        if not np.any(voice_frames):
            # No voice detected, return original
            return audio

        # Find start and end of voice activity
        voice_indices = np.where(voice_frames)[0]
        start_frame = voice_indices[0]
        end_frame = voice_indices[-1]

        # Convert frame indices to sample indices
        start_sample = start_frame * hop_length
        end_sample = min((end_frame + 1) * hop_length + frame_length, len(audio))

        # Add small padding (50ms on each side)
        padding = int(0.05 * sr)
        start_sample = max(0, start_sample - padding)
        end_sample = min(len(audio), end_sample + padding)

        return audio[start_sample:end_sample]

    @staticmethod
    def _denoise_audio(
        audio: np.ndarray,
        sr: int,
        strength: float = 0.5
    ) -> np.ndarray:
        """
        Simple spectral subtraction denoising.

        Args:
            audio: Input audio
            sr: Sample rate
            strength: Noise reduction strength (0-1)

        Returns:
            Denoised audio
        """
        try:
            # Try using noisereduce library if available
            import noisereduce as nr
            return nr.reduce_noise(
                y=audio,
                sr=sr,
                prop_decrease=strength,
                stationary=True
            )
        except ImportError:
            # Fallback: simple spectral subtraction
            return AudioEnhancer._spectral_subtraction(audio, strength)

    @staticmethod
    def _spectral_subtraction(
        audio: np.ndarray,
        strength: float = 0.5,
        noise_profile_duration: float = 0.5
    ) -> np.ndarray:
        """
        Spectral subtraction noise reduction (fallback method).

        Estimates noise from initial silence and subtracts it.

        Args:
            audio: Input audio
            strength: Subtraction strength (0-1)
            noise_profile_duration: Duration of noise profile (seconds)

        Returns:
            Denoised audio
        """
        try:
            import librosa
        except ImportError:
            # No denoising possible without librosa
            return audio

        # Compute STFT
        stft = librosa.stft(audio)
        magnitude, phase = np.abs(stft), np.angle(stft)

        # Estimate noise spectrum from first few frames
        noise_frames = int(noise_profile_duration * 16000 / 512)  # Approximate
        noise_frames = min(noise_frames, magnitude.shape[1] // 4)

        if noise_frames > 0:
            noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        else:
            # Fallback: use overall median
            noise_spectrum = np.median(magnitude, axis=1, keepdims=True)

        # Spectral subtraction
        denoised_magnitude = magnitude - (strength * noise_spectrum)

        # Apply floor (prevent negative values)
        denoised_magnitude = np.maximum(denoised_magnitude, 0.1 * magnitude)

        # Reconstruct signal
        denoised_stft = denoised_magnitude * np.exp(1j * phase)
        denoised_audio = librosa.istft(denoised_stft, length=len(audio))

        return denoised_audio


class SpeakerDiarization:
    """
    Simple speaker diarization for L2 conversation practice.

    Useful for:
    - Multi-speaker scenarios (group practice)
    - Filtering out tutor's voice
    - Identifying student vs. echo/feedback
    """

    @staticmethod
    def detect_multiple_speakers(
        audio: np.ndarray,
        sr: int,
        min_speakers: int = 1,
        max_speakers: int = 2
    ) -> dict:
        """
        Detect if audio contains multiple speakers.

        Args:
            audio: Input audio
            sr: Sample rate
            min_speakers: Minimum expected speakers
            max_speakers: Maximum expected speakers

        Returns:
            Dict with:
                - num_speakers: Estimated number of speakers
                - is_single_speaker: Boolean
                - confidence: Confidence score (0-1)
        """
        # Placeholder for advanced diarization
        # In practice, would use:
        # - pyannote.audio (best, but heavy)
        # - resemblyzer (speaker embeddings)
        # - simple energy-based clustering

        # Simple heuristic: check energy variance
        frame_length = int(0.1 * sr)  # 100ms frames
        hop_length = int(0.05 * sr)   # 50ms hop

        energies = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            energy = np.sqrt(np.mean(frame ** 2))
            energies.append(energy)

        energies = np.array(energies)

        # Simple check: high variance might indicate multiple speakers
        variance = np.var(energies)
        mean_energy = np.mean(energies)

        # Normalize variance by mean
        normalized_variance = variance / (mean_energy ** 2 + 1e-10)

        # Heuristic threshold
        is_single_speaker = normalized_variance < 0.5

        return {
            "num_speakers": 1 if is_single_speaker else 2,
            "is_single_speaker": is_single_speaker,
            "confidence": 0.7  # Conservative estimate
        }

    @staticmethod
    def extract_student_speech(
        audio: np.ndarray,
        sr: int,
        tutor_reference: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Extract student speech from mixed audio.

        Args:
            audio: Input audio (may contain tutor + student)
            sr: Sample rate
            tutor_reference: Optional reference of tutor's voice

        Returns:
            Student-only audio
        """
        # Placeholder: would implement speaker separation
        # For now, return original
        # TODO: Implement with source separation model (e.g., Demucs, Spleeter)

        return audio


class AudioQualityAnalyzer:
    """
    Analyze audio quality metrics for L2 learners.

    Provides feedback on:
    - Recording quality
    - Background noise levels
    - Clipping/distortion
    - Volume levels
    """

    @staticmethod
    def analyze(audio: np.ndarray, sr: int) -> dict:
        """
        Comprehensive audio quality analysis.

        Args:
            audio: Input audio
            sr: Sample rate

        Returns:
            Dict with quality metrics
        """
        metrics = {}

        # 1. Signal-to-Noise Ratio (SNR) estimate
        metrics['snr_estimate'] = AudioQualityAnalyzer._estimate_snr(audio, sr)

        # 2. Clipping detection
        metrics['clipping_detected'] = np.any(np.abs(audio) > 0.99)
        metrics['clipping_percentage'] = (
            100.0 * np.sum(np.abs(audio) > 0.99) / len(audio)
        )

        # 3. RMS level
        metrics['rms_level'] = np.sqrt(np.mean(audio ** 2))

        # 4. Peak level
        metrics['peak_level'] = np.max(np.abs(audio))

        # 5. Dynamic range
        metrics['dynamic_range_db'] = 20 * np.log10(
            metrics['peak_level'] / (metrics['rms_level'] + 1e-10)
        )

        # 6. Overall quality score (0-100)
        metrics['quality_score'] = AudioQualityAnalyzer._compute_quality_score(metrics)

        # 7. Recommendations
        metrics['recommendations'] = AudioQualityAnalyzer._generate_recommendations(metrics)

        return metrics

    @staticmethod
    def _estimate_snr(audio: np.ndarray, sr: int) -> float:
        """
        Estimate Signal-to-Noise Ratio.

        Args:
            audio: Input audio
            sr: Sample rate

        Returns:
            SNR in dB
        """
        # Use first 0.2s as noise estimate
        noise_duration = int(0.2 * sr)
        noise_duration = min(noise_duration, len(audio) // 4)

        if noise_duration > 0:
            noise = audio[:noise_duration]
            signal = audio[noise_duration:]
        else:
            # Fallback: use quietest 20%
            sorted_abs = np.sort(np.abs(audio))
            split_idx = len(sorted_abs) // 5
            noise = sorted_abs[:split_idx]
            signal = sorted_abs[split_idx:]

        noise_power = np.mean(noise ** 2)
        signal_power = np.mean(signal ** 2)

        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))

        return max(0, min(60, snr))  # Clamp to reasonable range

    @staticmethod
    def _compute_quality_score(metrics: dict) -> int:
        """Compute overall quality score (0-100)."""
        score = 100

        # Penalize low SNR
        if metrics['snr_estimate'] < 20:
            score -= (20 - metrics['snr_estimate']) * 2

        # Penalize clipping
        if metrics['clipping_detected']:
            score -= metrics['clipping_percentage'] * 10

        # Penalize too quiet
        if metrics['rms_level'] < 0.05:
            score -= 20

        # Penalize too loud
        if metrics['peak_level'] > 0.99:
            score -= 10

        return max(0, min(100, int(score)))

    @staticmethod
    def _generate_recommendations(metrics: dict) -> list:
        """Generate user-friendly recommendations."""
        recommendations = []

        if metrics['snr_estimate'] < 15:
            recommendations.append("🔇 Reduce background noise or move to a quieter room")

        if metrics['clipping_detected']:
            recommendations.append("📉 Lower your microphone volume to avoid distortion")

        if metrics['rms_level'] < 0.05:
            recommendations.append("📈 Speak louder or increase microphone gain")

        if metrics['peak_level'] > 0.99:
            recommendations.append("⚠️ Audio is clipping - reduce input volume")

        if not recommendations:
            recommendations.append("✅ Audio quality is good!")

        return recommendations
