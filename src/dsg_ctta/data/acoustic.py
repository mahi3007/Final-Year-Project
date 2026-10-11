"""
Acoustic feature extractor and confounder measurement module.
Extracts SNR, speech rate, duration, and audio SHA256 hashes.
"""

from __future__ import annotations
import hashlib
import os
from typing import Tuple, Optional
import numpy as np
import soundfile as sf


def compute_audio_sha256(filepath: str) -> str:
    """Compute exact SHA256 checksum of raw audio file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


from pathlib import Path


def load_and_resample_audio(
    filepath_or_array: str | Path | np.ndarray,
    target_sr: int = 16000,
    orig_sr: Optional[int] = None
) -> Tuple[np.ndarray, int]:
    """Load audio and ensure mono 16kHz float32 waveform."""
    if isinstance(filepath_or_array, (str, Path)):
        filepath_str = str(filepath_or_array).replace("\\", "/")
        if not os.path.exists(filepath_str):
            raise FileNotFoundError(f"Audio file not found: {filepath_str}")
        audio, sr = sf.read(filepath_str)
    else:
        audio = filepath_or_array
        sr = orig_sr or target_sr

    # Convert to mono if multi-channel
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Convert to float32
    audio = audio.astype(np.float32)

    # Normalize amplitude if needed
    max_amp = np.max(np.abs(audio)) if len(audio) > 0 else 0
    if max_amp > 1.0:
        audio = audio / max_amp

    # Resample if sample rate differs
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    return audio, sr


def estimate_snr_db(audio: np.ndarray, frame_length_ms: int = 30, hop_length_ms: int = 10, sr: int = 16000) -> float:
    """
    Estimate Signal-to-Noise Ratio (SNR in dB) using an energy percentile decomposition.
    Assumes top 20% frame energies represent speech signal and bottom 20% represent background noise floor.
    """
    if len(audio) < sr * 0.1:
        return 20.0  # Default for very short clips

    frame_len = int(sr * (frame_length_ms / 1000.0))
    hop_len = int(sr * (hop_length_ms / 1000.0))

    if len(audio) < frame_len:
        return 20.0

    # Calculate short-time frame energies
    num_frames = (len(audio) - frame_len) // hop_len + 1
    energies = np.zeros(num_frames)
    for i in range(num_frames):
        start = i * hop_len
        frame = audio[start : start + frame_len]
        energies[i] = np.mean(frame ** 2)

    energies = energies[energies > 1e-12]  # Avoid true zeros
    if len(energies) < 5:
        return 20.0

    # Sort energies
    sorted_e = np.sort(energies)
    noise_idx = max(1, int(len(sorted_e) * 0.20))
    signal_idx = min(len(sorted_e) - 1, int(len(sorted_e) * 0.80))

    noise_energy = np.mean(sorted_e[:noise_idx])
    signal_energy = np.mean(sorted_e[signal_idx:])

    if noise_energy <= 1e-12:
        return 50.0  # Very clean

    snr = 10.0 * np.log10(max(signal_energy / noise_energy, 1.0))
    return float(np.clip(snr, -10.0, 60.0))


def estimate_speech_rate(
    duration_seconds: float,
    word_count: Optional[int] = None,
    audio: Optional[np.ndarray] = None,
    sr: int = 16000
) -> float:
    """
    Compute speech rate in Words Per Minute (WPM).
    If word count is available (offline), uses words/duration.
    If word count is not available, estimates syllable/envelope peaks.
    """
    if duration_seconds <= 0:
        return 120.0

    if word_count is not None and word_count > 0:
        wpm = (word_count / duration_seconds) * 60.0
        return float(np.clip(wpm, 30.0, 350.0))

    if audio is not None and len(audio) > 0:
        # Estimate via energy envelope peaks (approx 1 word per 2.5 syllables)
        frame_len = int(sr * 0.025)
        hop_len = int(sr * 0.010)
        if len(audio) > frame_len:
            frames = (len(audio) - frame_len) // hop_len + 1
            env = np.array([np.sqrt(np.mean(audio[i*hop_len : i*hop_len+frame_len]**2)) for i in range(frames)])
            threshold = np.mean(env) * 0.8
            peaks = np.sum((env[1:-1] > env[:-2]) & (env[1:-1] > env[2:]) & (env[1:-1] > threshold))
            est_words = max(1, int(peaks / 2.5))
            wpm = (est_words / duration_seconds) * 60.0
            return float(np.clip(wpm, 30.0, 350.0))

    return 140.0  # Standard average default
