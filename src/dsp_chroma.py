"""Product-owned Librosa chroma evidence and research diagnostics."""
from __future__ import annotations

import os
import tempfile
from math import sqrt
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import numpy as np

from src.harmonic_evidence import PitchClassEvidence


DEFAULT_CONFIG = {
    "sample_rate": 22050,
    "hop_length": 512,
    "bins_per_octave": 36,
    "n_chroma": 12,
    "norm": "l1",
    "tuning": "estimate",
    "harmonic_separation": False,
}

ROOT_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
QUALITY_INTERVALS = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "dominant7": (0, 4, 7, 10),
    "major7": (0, 4, 7, 11),
    "minor7": (0, 3, 7, 10),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "diminished": (0, 3, 6),
}
QUALITY_SUFFIX = {
    "major": "",
    "minor": "m",
    "dominant7": "7",
    "major7": "maj7",
    "minor7": "m7",
    "sus2": "sus2",
    "sus4": "sus4",
    "diminished": "dim",
}


def _template_bank() -> tuple[list[dict[str, str]], np.ndarray, np.ndarray]:
    descriptions = []
    rows = []
    lengths = []
    for root in range(12):
        for quality, intervals in QUALITY_INTERVALS.items():
            row = np.zeros(12, dtype=np.float64)
            row[[(root + interval) % 12 for interval in intervals]] = 1.0
            rows.append(row)
            lengths.append(sqrt(len(intervals)))
            descriptions.append({
                "label": ROOT_NAMES[root] + QUALITY_SUFFIX[quality],
                "root": ROOT_NAMES[root],
                "quality": quality,
            })
    return descriptions, np.asarray(rows), np.asarray(lengths)


_TEMPLATE_DESCRIPTIONS, _TEMPLATE_MATRIX, _TEMPLATE_NORMS = _template_bank()


def extract_pitch_class_evidence(
    wav_path: str,
    config: dict[str, Any] | None = None,
) -> tuple[list[PitchClassEvidence], dict[str, Any]]:
    """Extract fixed-configuration L1 CQT chroma on the audio timeline."""
    if not os.getenv("NUMBA_CACHE_DIR"):
        cache = Path(tempfile.gettempdir()) / "horizonjam-numba-cache"
        cache.mkdir(parents=True, exist_ok=True)
        os.environ["NUMBA_CACHE_DIR"] = str(cache)
    import librosa
    import soundfile as sf

    provided = config or {}
    unknown = set(provided) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f"unknown DSP config fields: {sorted(unknown)}")
    settings = {**DEFAULT_CONFIG, **provided}
    if settings["norm"] != "l1":
        raise ValueError("Phase 3 freezes chroma normalization to l1")
    if settings["harmonic_separation"] is not False:
        raise ValueError("harmonic separation is not implemented in Phase 3")
    total_started = perf_counter()
    load_started = perf_counter()
    samples, native_sample_rate = sf.read(
        wav_path, dtype="float32", always_2d=True
    )
    audio = np.mean(samples, axis=1, dtype=np.float64)
    sample_rate = int(settings["sample_rate"])
    if native_sample_rate != sample_rate:
        audio = librosa.resample(
            audio, orig_sr=native_sample_rate, target_sr=sample_rate
        )
    load_sec = perf_counter() - load_started
    duration = len(audio) / sample_rate if sample_rate else 0.0
    if duration <= 0:
        raise ValueError("audio must contain at least one sample")

    tuning_started = perf_counter()
    tuning_setting = settings["tuning"]
    if tuning_setting == "estimate":
        try:
            tuning = float(librosa.estimate_tuning(y=audio, sr=sample_rate))
        except Exception:
            tuning = 0.0
    elif isinstance(tuning_setting, (int, float)):
        tuning = float(tuning_setting)
    else:
        raise ValueError("tuning must be 'estimate' or a numeric bin offset")
    tuning_sec = perf_counter() - tuning_started

    chroma_started = perf_counter()
    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sample_rate,
        hop_length=int(settings["hop_length"]),
        n_chroma=int(settings["n_chroma"]),
        bins_per_octave=int(settings["bins_per_octave"]),
        tuning=tuning,
        norm=1,
    )
    chroma_sec = perf_counter() - chroma_started

    evidence_started = perf_counter()
    frame_duration = float(settings["hop_length"]) / sample_rate
    evidence: list[PitchClassEvidence] = []
    for frame in range(chroma.shape[1]):
        start = frame * frame_duration
        if start >= duration:
            break
        end = min(duration, (frame + 1) * frame_duration)
        values = [float(value) for value in chroma[:, frame]]
        evidence.append(PitchClassEvidence(
            start=start,
            end=end,
            values=values,
            representation="chroma_cqt_l1",
            source="librosa_chroma",
            metadata={"frame_index": frame},
        ))
    evidence_sec = perf_counter() - evidence_started
    return evidence, {
        "config": settings,
        "sample_rate": sample_rate,
        "native_sample_rate": native_sample_rate,
        "duration_sec": duration,
        "estimated_tuning_bins": tuning,
        "frame_count": len(evidence),
        "timings_sec": {
            "audio_load": load_sec,
            "tuning_estimation": tuning_sec,
            "cqt_chroma": chroma_sec,
            "evidence_conversion": evidence_sec,
            "total": perf_counter() - total_started,
        },
    }


def _label(root: int, quality: str) -> str:
    return ROOT_NAMES[root] + QUALITY_SUFFIX[quality]


def score_chroma_values(values: Sequence[float]) -> list[dict[str, Any]]:
    """Rank bounded chord templates by cosine support; scores are not probabilities."""
    if len(values) != 12:
        raise ValueError("chroma values must contain exactly 12 pitch classes")
    vector = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(vector)):
        raise ValueError("chroma values must be finite")
    vector_norm = float(np.linalg.norm(vector))
    if vector_norm == 0.0:
        return []
    scores = (_TEMPLATE_MATRIX @ vector) / (vector_norm * _TEMPLATE_NORMS)
    candidates = [
        {
            **description,
            "normalized_support": float(score),
            "source": "librosa_chroma",
        }
        for description, score in zip(_TEMPLATE_DESCRIPTIONS, scores)
    ]
    return sorted(candidates, key=lambda item: (-item["normalized_support"], item["label"]))


def score_pitch_class_evidence(
    evidence: Sequence[PitchClassEvidence], top_n: int = 3
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    started = perf_counter()
    frames = []
    for item in evidence:
        ranked = score_chroma_values(item.values)
        frames.append({
            "start": item.start,
            "end": item.end,
            "candidates": ranked[:top_n],
        })
    return frames, {"candidate_scoring": perf_counter() - started}


def summarize_frame_candidates(frames: Sequence[dict[str, Any]]) -> str:
    """Return the duration-weighted diagnostic winner, excluding silent frames."""
    totals: dict[str, float] = {}
    for frame in frames:
        candidates = frame.get("candidates") or []
        if not candidates:
            continue
        winner = candidates[0]
        duration = max(0.0, float(frame["end"]) - float(frame["start"]))
        totals[winner["label"]] = totals.get(winner["label"], 0.0) + duration
    if not totals:
        return "N"
    return sorted(totals, key=lambda label: (-totals[label], label))[0]
