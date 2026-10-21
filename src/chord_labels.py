"""Central normalization for external chord-label vocabularies."""
from __future__ import annotations

import re
from typing import Any, Optional


_LABEL = re.compile(
    r"^(?P<root>[A-Ga-g])(?P<accidental>[#b]?)(?::|\s*)?(?P<quality>[^/]*)?(?:/(?P<bass>.+))?$"
)
_QUALITY_ALIASES = {
    "": "",
    "maj": "",
    "major": "",
    "min": "m",
    "minor": "m",
    "m": "m",
    "7": "7",
    "dom7": "7",
    "dominant7": "7",
    "dominant seventh": "7",
    "maj7": "maj7",
    "major7": "maj7",
    "major seventh": "maj7",
    "min7": "m7",
    "minor7": "m7",
    "m7": "m7",
    "minor seventh": "m7",
    "dim": "dim",
    "diminished": "dim",
    "aug": "aug",
    "augmented": "aug",
    "sus2": "sus2",
    "sus4": "sus4",
}
_QUALITY_NAMES = {
    "": "major",
    "m": "minor",
    "7": "dominant7",
    "maj7": "major7",
    "m7": "minor7",
    "dim": "diminished",
    "aug": "augmented",
    "sus2": "sus2",
    "sus4": "sus4",
}
_QUALITY_INTERVALS = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
}
_PITCH_CLASSES = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def normalize_external_chord_label(raw_label: str) -> tuple[str, str]:
    """Return (label, status), preserving unsupported labels verbatim."""
    raw = str(raw_label or "").strip()
    if not raw:
        raise ValueError("raw chord label is required")
    if raw.upper() in {"N", "X"}:
        return "N", "normalized"
    match = _LABEL.match(raw)
    if not match:
        return raw, "unmapped"
    root = match.group("root").upper() + match.group("accidental")
    quality_raw = (match.group("quality") or "").strip().lower()
    quality = _QUALITY_ALIASES.get(quality_raw)
    bass_raw: Optional[str] = match.group("bass")
    if quality is None:
        return raw, "unmapped"
    if bass_raw:
        bass_match = re.fullmatch(r"[A-Ga-g][#b]?", bass_raw.strip())
        if not bass_match:
            return raw, "unmapped"
        bass = bass_raw[0].upper() + bass_raw[1:]
        return f"{root}{quality}/{bass}", "normalized"
    return f"{root}{quality}", "normalized"


def decompose_chord_label(raw_label: str) -> dict[str, Any]:
    """Return a conservative canonical representation for a supported label."""
    label, status = normalize_external_chord_label(raw_label)
    if status != "normalized" or label == "N":
        return {
            "label": label,
            "root": None,
            "quality": None,
            "bass": None,
            "pitch_class_set": [],
            "status": status,
        }
    match = _LABEL.fullmatch(label)
    if not match:
        raise ValueError(f"normalized label could not be decomposed: {label}")
    root = match.group("root").upper() + match.group("accidental")
    quality_suffix = (match.group("quality") or "").strip()
    bass_raw = match.group("bass")
    quality = _QUALITY_NAMES.get(quality_suffix)
    intervals = _QUALITY_INTERVALS.get(quality_suffix)
    root_pc = _PITCH_CLASSES.get(root)
    if quality is None or intervals is None or root_pc is None:
        return {
            "label": label,
            "root": None,
            "quality": None,
            "bass": None,
            "pitch_class_set": [],
            "status": "unmapped",
        }
    bass = None
    if bass_raw:
        bass = bass_raw[0].upper() + bass_raw[1:]
    return {
        "label": label,
        "root": root,
        "quality": quality,
        "bass": bass,
        "pitch_class_set": sorted({(root_pc + value) % 12 for value in intervals}),
        "status": "normalized",
    }
