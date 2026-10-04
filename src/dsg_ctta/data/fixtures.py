"""
Synthetic/Curated E2E research fixture generator.
Creates reproducible multi-speaker, multi-group speech recordings with known acoustic confounders.
"""

from __future__ import annotations
import os
import numpy as np
import soundfile as sf
from typing import List, Tuple
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import compute_audio_sha256, estimate_snr_db, estimate_speech_rate


# Canonical test sentence prompts (phonetically rich Arctic / standard sentences)
FIXTURE_SENTENCES = [
    "AUTHOR OF THE DANGER TRAIL PHILIP STEEL ETC",
    "NOT AT THIS PARTICULAR MOMENT HE WISHED TO EXPLAIN",
    "THE SMALL BIRDS REJOICED IN THE BRIGHT SUNSHINE",
    "THERE WAS NO DOUBT THAT THE MACHINE WORKED PERFECTLY",
    "HE ASKED ME TO ACCOMPANY HIM TO THE HARBOR",
    "A GENTLE BREEZE CARRIED THE SCENT OF WILD FLOWERS",
    "SHE OPENED THE DOOR SLOWLY TO AVOID MAKING NOISE",
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "HE HAD NEVER SEEN SUCH A MAGNIFICENT SIGHT BEFORE",
    "WE MUST CAREFULLY EXAMINE ALL THE EVIDENCE AVAILABLE",
    "THE ANCIENT CASTLE STOOD HIGH UPON THE ROCKY HILL",
    "THEY WALKED THROUGH THE FOREST AS THE EVENING FELL"
]

# Multi-group speaker configuration (4 groups, 4 speakers each = 16 distinct speakers)
FIXTURE_SPEAKERS = [
    # Group A (e.g. Native Region 1)
    {"speaker_id": "spk_A1", "group_id": "Region_North", "group_type": "native_region", "f0": 130.0, "noise_level": 0.005, "device_id": "device_mic1"},
    {"speaker_id": "spk_A2", "group_id": "Region_North", "group_type": "native_region", "f0": 210.0, "noise_level": 0.010, "device_id": "device_mic2"},
    {"speaker_id": "spk_A3", "group_id": "Region_North", "group_type": "native_region", "f0": 145.0, "noise_level": 0.008, "device_id": "device_phone"},
    {"speaker_id": "spk_A4", "group_id": "Region_North", "group_type": "native_region", "f0": 190.0, "noise_level": 0.012, "device_id": "device_mic1"},
    # Group B (e.g. Native Region 2)
    {"speaker_id": "spk_B1", "group_id": "Region_South", "group_type": "native_region", "f0": 120.0, "noise_level": 0.008, "device_id": "device_mic1"},
    {"speaker_id": "spk_B2", "group_id": "Region_South", "group_type": "native_region", "f0": 225.0, "noise_level": 0.025, "device_id": "device_phone"},
    {"speaker_id": "spk_B3", "group_id": "Region_South", "group_type": "native_region", "f0": 135.0, "noise_level": 0.014, "device_id": "device_mic2"},
    {"speaker_id": "spk_B4", "group_id": "Region_South", "group_type": "native_region", "f0": 215.0, "noise_level": 0.018, "device_id": "device_mic1"},
    # Group C (e.g. Native Region 3)
    {"speaker_id": "spk_C1", "group_id": "Region_East", "group_type": "native_region", "f0": 140.0, "noise_level": 0.012, "device_id": "device_mic2"},
    {"speaker_id": "spk_C2", "group_id": "Region_East", "group_type": "native_region", "f0": 195.0, "noise_level": 0.006, "device_id": "device_mic1"},
    {"speaker_id": "spk_C3", "group_id": "Region_East", "group_type": "native_region", "f0": 150.0, "noise_level": 0.020, "device_id": "device_phone"},
    {"speaker_id": "spk_C4", "group_id": "Region_East", "group_type": "native_region", "f0": 185.0, "noise_level": 0.009, "device_id": "device_mic2"},
    # Group D (e.g. Native Region 4 / External)
    {"speaker_id": "spk_D1", "group_id": "Region_West", "group_type": "native_region", "f0": 115.0, "noise_level": 0.030, "device_id": "device_phone"},
    {"speaker_id": "spk_D2", "group_id": "Region_West", "group_type": "native_region", "f0": 205.0, "noise_level": 0.015, "device_id": "device_mic1"},
    {"speaker_id": "spk_D3", "group_id": "Region_West", "group_type": "native_region", "f0": 125.0, "noise_level": 0.022, "device_id": "device_mic2"},
    {"speaker_id": "spk_D4", "group_id": "Region_West", "group_type": "native_region", "f0": 210.0, "noise_level": 0.011, "device_id": "device_phone"},
]


def generate_synthetic_audio(
    duration: float,
    f0: float,
    noise_level: float,
    sr: int = 16000,
    seed: int = 42
) -> np.ndarray:
    """
    Generate harmonic speech-like formant wave + modulated pink/white noise envelope
    for deterministic audio fixture generation.
    """
    rng = np.random.RandomState(seed)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Formants / harmonics of fundamental frequency f0
    signal = 0.5 * np.sin(2 * np.pi * f0 * t)
    signal += 0.3 * np.sin(2 * np.pi * (2 * f0) * t)
    signal += 0.15 * np.sin(2 * np.pi * (3 * f0) * t)
    signal += 0.08 * np.sin(2 * np.pi * (4 * f0) * t)

    # Low frequency amplitude modulation (simulating speech syllables at 4 Hz)
    envelope = 0.5 * (1.0 + np.sin(2 * np.pi * 4.0 * t))
    signal = signal * envelope

    # Add background noise
    noise = rng.normal(0, noise_level, size=len(t))
    audio = signal + noise

    # Normalize to [-0.95, 0.95]
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = 0.95 * (audio / max_val)

    return audio.astype(np.float32)


def generate_research_fixture_dataset(
    output_dir: str,
    utterances_per_speaker: int = 3,
    sr: int = 16000,
    seed: int = 42
) -> Tuple[List[UtteranceMetadata], List[UtteranceMetadata]]:
    """
    Generate standard multi-group fixture dataset on disk:
    Returns (primary_utterances, external_validation_utterances).
    """
    os.makedirs(os.path.join(output_dir, "audio"), exist_ok=True)
    primary_utterances: List[UtteranceMetadata] = []
    external_utterances: List[UtteranceMetadata] = []

    utt_idx = 0
    for spk_info in FIXTURE_SPEAKERS:
        spk_id = spk_info["speaker_id"]
        grp_id = spk_info["group_id"]
        grp_type = spk_info["group_type"]
        f0 = spk_info["f0"]
        noise_level = spk_info["noise_level"]
        device_id = spk_info["device_id"]

        is_external = (grp_id == "Region_West")

        for i in range(utterances_per_speaker):
            utt_idx += 1
            sent_raw = FIXTURE_SENTENCES[(utt_idx - 1) % len(FIXTURE_SENTENCES)]
            sent_norm = TextNormalizer.normalize(sent_raw)
            word_count = TextNormalizer.count_words(sent_norm)
            char_count = TextNormalizer.count_chars(sent_norm)

            duration = max(1.5, word_count * 0.40 + 0.5)
            audio = generate_synthetic_audio(
                duration=duration,
                f0=f0,
                noise_level=noise_level,
                sr=sr,
                seed=seed + utt_idx
            )

            utt_filename = f"{spk_id}_utt{i+1:03d}.wav"
            audio_path = os.path.join(output_dir, "audio", utt_filename)
            sf.write(audio_path, audio, sr)

            sha256 = compute_audio_sha256(audio_path)
            snr = estimate_snr_db(audio, sr=sr)
            wpm = estimate_speech_rate(duration, word_count=word_count)

            provenance = ProvenanceInfo(
                source_dataset="Synthetic-Regional-Fixture" if not is_external else "Synthetic-External-Corpus",
                dataset_release="v1.0-canonical"
            )

            utt_meta = UtteranceMetadata(
                utterance_id=f"{spk_id}_utt{i+1:03d}",
                speaker_id=spk_id,
                group_id=grp_id,
                group_type=grp_type,
                audio_filepath=audio_path,
                audio_sha256=sha256,
                sampling_rate_hz=sr,
                duration_seconds=round(duration, 3),
                snr_db=round(snr, 2),
                speech_rate_wpm=round(wpm, 1),
                device_id=device_id,
                reference_raw=sent_raw,
                reference_normalized=sent_norm,
                reference_word_count=word_count,
                reference_char_count=char_count,
                provenance=provenance
            )

            if is_external:
                external_utterances.append(utt_meta)
            else:
                primary_utterances.append(utt_meta)

    return primary_utterances, external_utterances
