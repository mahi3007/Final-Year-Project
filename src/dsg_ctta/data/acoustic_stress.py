"""
Acoustic Stress Generation Module for Stage 4E.
Generates controlled, deterministic acoustic corruptions with full cryptographic provenance.

Supported Conditions:
1. clean: Uncorrupted reference audio
2. noise_moderate: Additive Gaussian/white noise at SNR = 15 dB
3. noise_severe: Additive Gaussian/white noise at SNR = 5 dB
4. babble_moderate: Additive multi-speaker babble/speech-shaped noise at SNR = 15 dB
5. reverberation: Synthetic exponential-decay room impulse response (T60 = 0.4s)
"""

from __future__ import annotations
import os
import json
import hashlib
import numpy as np
import soundfile as sf
import scipy.signal
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from rich.console import Console

from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.data.splits import load_partition_from_csv

console = Console()


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def add_gaussian_noise(audio: np.ndarray, target_snr_db: float, rng: np.random.RandomState) -> np.ndarray:
    """Add zero-mean Gaussian noise to achieve target SNR in dB."""
    signal_power = np.mean(audio ** 2)
    if signal_power <= 1e-12:
        return audio.copy()
    
    snr_linear = 10.0 ** (target_snr_db / 10.0)
    noise_power = signal_power / snr_linear
    noise = rng.normal(0.0, np.sqrt(noise_power), size=audio.shape)
    noisy_audio = audio + noise
    
    # Clip to prevent digital clipping
    max_val = np.max(np.abs(noisy_audio))
    if max_val > 1.0:
        noisy_audio = noisy_audio / max_val * 0.99
    return noisy_audio.astype(np.float32)


def add_babble_noise(audio: np.ndarray, sample_rate: int, target_snr_db: float, rng: np.random.RandomState) -> np.ndarray:
    """
    Generate speech-shaped / multi-frequency modulated babble noise at target SNR.
    Applies bandpass filtering centered in the human speech range (300 Hz - 3400 Hz)
    with low-frequency syllabic amplitude modulation (3-5 Hz).
    """
    signal_power = np.mean(audio ** 2)
    if signal_power <= 1e-12:
        return audio.copy()

    # White noise baseline
    raw_noise = rng.normal(0.0, 1.0, size=len(audio))
    
    # Bandpass filter for speech frequencies (300 - 3400 Hz)
    nyquist = 0.5 * sample_rate
    low = max(0.01, min(300.0 / nyquist, 0.8))
    high = max(low + 0.05, min(3400.0 / nyquist, 0.95))
    b, a = scipy.signal.butter(4, [low, high], btype="band")
    filtered_noise = scipy.signal.lfilter(b, a, raw_noise)
    
    # Syllabic envelope modulation (simulate multi-talker cadence at 4 Hz)
    t = np.arange(len(audio)) / sample_rate
    mod = 0.5 * (1.0 + np.sin(2 * np.pi * 4.0 * t + rng.uniform(0, 2 * np.pi)))
    babble = filtered_noise * mod

    # Scale to target SNR
    babble_power = np.mean(babble ** 2)
    if babble_power > 1e-12:
        snr_linear = 10.0 ** (target_snr_db / 10.0)
        scale = np.sqrt(signal_power / (snr_linear * babble_power))
        babble = babble * scale

    noisy = audio + babble
    max_val = np.max(np.abs(noisy))
    if max_val > 1.0:
        noisy = noisy / max_val * 0.99
    return noisy.astype(np.float32)


def add_reverberation(audio: np.ndarray, sample_rate: int, t60: float = 0.4, rng: Optional[np.random.RandomState] = None) -> np.ndarray:
    """
    Convolve audio with a synthetic exponential-decay room impulse response (RIR).
    t60 is the reverberation time in seconds (time for decay by 60 dB).
    """
    if rng is None:
        rng = np.random.RandomState(42)
        
    rir_len = int(sample_rate * t60)
    t = np.arange(rir_len) / sample_rate
    decay = np.exp(-3.0 * np.log(10.0) * t / t60)
    noise = rng.normal(0.0, 1.0, size=rir_len)
    rir = decay * noise
    rir = rir / np.sqrt(np.sum(rir ** 2))  # Normalize energy

    # Convolve
    reverbed = scipy.signal.fftconvolve(audio, rir, mode="full")[:len(audio)]
    max_val = np.max(np.abs(reverbed))
    if max_val > 1.0:
        reverbed = reverbed / max_val * 0.99
    return reverbed.astype(np.float32)


def generate_stressed_partition(
    input_split_csv: str = "datasets/splits/stage4_characterization.csv",
    condition_name: str = "noise_moderate",
    output_split_csv: Optional[str] = None,
    output_audio_dir: Optional[str] = None,
    seed: int = 42
) -> Tuple[str, Dict[str, Any]]:
    """
    Deterministically transforms all recordings in input_split_csv under condition_name.
    Saves new audio files and returns the path to the stressed split CSV along with manifest.
    """
    if output_split_csv is None:
        output_split_csv = f"datasets/splits/stage4_{condition_name}.csv"
    if output_audio_dir is None:
        output_audio_dir = f"datasets/corrupted/{condition_name}"

    os.makedirs(output_audio_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_split_csv), exist_ok=True)

    df_in = pd.read_csv(input_split_csv)
    input_sha256 = compute_file_sha256(input_split_csv)

    console.print(f"[bold cyan]Generating Acoustic Stress Partition: {condition_name.upper()}[/bold cyan]")
    console.print(f"Source: [yellow]{input_split_csv}[/yellow] ({len(df_in)} utterances)")

    records = []
    file_hashes: Dict[str, Dict[str, str]] = {}

    for idx, row in df_in.iterrows():
        orig_path = row["audio_filepath"]
        utt_id = row["utterance_id"]
        
        # Deterministic per-utterance seed derived from global seed and utterance hash
        utt_hash_int = int(hashlib.sha256(utt_id.encode("utf-8")).hexdigest()[:8], 16)
        utt_rng = np.random.RandomState((seed + utt_hash_int) % (2**31 - 1))

        audio, sr = sf.read(orig_path)
        orig_sha = compute_file_sha256(orig_path)

        if condition_name == "clean":
            stressed_audio = audio.copy()
        elif condition_name == "noise_moderate":
            stressed_audio = add_gaussian_noise(audio, target_snr_db=15.0, rng=utt_rng)
        elif condition_name == "noise_severe":
            stressed_audio = add_gaussian_noise(audio, target_snr_db=5.0, rng=utt_rng)
        elif condition_name == "babble_moderate":
            stressed_audio = add_babble_noise(audio, sample_rate=sr, target_snr_db=15.0, rng=utt_rng)
        elif condition_name == "reverberation":
            stressed_audio = add_reverberation(audio, sample_rate=sr, t60=0.4, rng=utt_rng)
        else:
            raise ValueError(f"Unknown condition_name: {condition_name}")

        rel_subpath = f"{row['speaker_id']}_{utt_id}_{condition_name}.wav"
        dest_path = os.path.join(output_audio_dir, rel_subpath)
        sf.write(dest_path, stressed_audio, sr)
        dest_sha = compute_file_sha256(dest_path)

        file_hashes[utt_id] = {
            "original_sha256": orig_sha,
            "corrupted_sha256": dest_sha
        }

        row_copy = row.to_dict()
        row_copy["audio_filepath"] = os.path.abspath(dest_path)
        row_copy["acoustic_condition"] = condition_name
        records.append(row_copy)

    df_out = pd.DataFrame(records)
    df_out.to_csv(output_split_csv, index=False)
    output_sha256 = compute_file_sha256(output_split_csv)

    manifest = {
        "protocol_version": "v1.0.0-canonical",
        "stage": "Stage 4E",
        "condition_name": condition_name,
        "seed": seed,
        "input_split": input_split_csv,
        "input_split_sha256": input_sha256,
        "output_split": output_split_csv,
        "output_split_sha256": output_sha256,
        "num_utterances": len(records),
        "file_hashes": file_hashes
    }

    manifest_path = os.path.join(output_audio_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    console.print(f"[bold green]Successfully created {condition_name} partition: {output_split_csv}[/bold green]")
    console.print(f"Output SHA-256: {output_sha256[:16]}... (Manifest: {manifest_path})")
    return output_split_csv, manifest


if __name__ == "__main__":
    for cond in ["noise_moderate", "noise_severe", "babble_moderate", "reverberation"]:
        generate_stressed_partition(condition_name=cond)
