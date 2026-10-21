"""Shared, observational harmonic evidence structures.

These types adapt data already produced by HorizonJam. They do not perform
transcription, chord recognition, selection, or confidence calibration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from numbers import Integral
from typing import Any, Iterable, Mapping, Optional, Sequence


def _finite_number(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _source(value: Any, field_name: str = "source") -> str:
    source = str(value or "").strip()
    if not source:
        raise ValueError(f"{field_name} is required")
    return source


@dataclass(frozen=True)
class NoteEvidence:
    start: float
    end: float
    pitch: int
    pitch_class: int
    octave: int
    velocity_or_amplitude: Optional[float]
    confidence: Optional[float]
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start = _finite_number(self.start, "start")
        end = _finite_number(self.end, "end")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < start:
            raise ValueError("end must be >= start")
        if isinstance(self.pitch, bool) or not isinstance(self.pitch, int):
            raise ValueError("pitch must be an integer MIDI note")
        if not 0 <= self.pitch <= 127:
            raise ValueError("pitch must be within 0..127")
        if isinstance(self.pitch_class, bool) or not isinstance(self.pitch_class, int):
            raise ValueError("pitch_class must be an integer")
        if not 0 <= self.pitch_class <= 11:
            raise ValueError("pitch_class must be within 0..11")
        if self.pitch_class != self.pitch % 12:
            raise ValueError("pitch_class must match pitch modulo 12")
        if self.velocity_or_amplitude is not None:
            _finite_number(self.velocity_or_amplitude, "velocity_or_amplitude")
        if self.confidence is not None:
            _finite_number(self.confidence, "confidence")
        _source(self.source)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChordHypothesis:
    start: float
    end: float
    chord: str
    confidence: Optional[float]
    source: str
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    supporting_sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start = _finite_number(self.start, "start")
        end = _finite_number(self.end, "end")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end <= start:
            raise ValueError("end must be greater than start")
        if not str(self.chord or "").strip():
            raise ValueError("chord is required")
        if self.confidence is not None:
            _finite_number(self.confidence, "confidence")
        _source(self.source)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PitchClassEvidence:
    start: float
    end: float
    values: list[float]
    representation: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start = _finite_number(self.start, "start")
        end = _finite_number(self.end, "end")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end <= start:
            raise ValueError("end must be greater than start")
        if len(self.values) != 12:
            raise ValueError("values must contain exactly 12 pitch classes")
        for index, value in enumerate(self.values):
            _finite_number(value, f"values[{index}]")
        if not str(self.representation or "").strip():
            raise ValueError("representation is required")
        _source(self.source)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DirectChordEvidence:
    start: float
    end: float
    label: str
    raw_label: str
    score: Optional[float]
    alternatives: list[dict[str, Any]]
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start = _finite_number(self.start, "start")
        end = _finite_number(self.end, "end")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end <= start:
            raise ValueError("end must be greater than start")
        if not str(self.label or "").strip():
            raise ValueError("label is required")
        if not str(self.raw_label or "").strip():
            raise ValueError("raw_label is required")
        if self.score is not None:
            _finite_number(self.score, "score")
        _source(self.source)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChordCandidate:
    start: float
    end: float
    label: str
    root: Optional[str]
    quality: Optional[str]
    bass: Optional[str]
    score: float
    evidence_sources: list[str]
    evidence_breakdown: dict[str, float]
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start = _finite_number(self.start, "start")
        end = _finite_number(self.end, "end")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end <= start:
            raise ValueError("end must be greater than start")
        if not str(self.label or "").strip():
            raise ValueError("label is required")
        _finite_number(self.score, "score")
        if not self.evidence_sources:
            raise ValueError("evidence_sources must not be empty")
        if any(not str(source or "").strip() for source in self.evidence_sources):
            raise ValueError("evidence_sources must contain non-empty names")
        for source, support in self.evidence_breakdown.items():
            _source(source, "evidence_breakdown source")
            value = _finite_number(support, f"evidence_breakdown[{source}]")
            if not 0.0 <= value <= 1.0:
                raise ValueError("normalized support must be within 0..1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HarmonicEvidencePacket:
    audio_id: Optional[str]
    duration: Optional[float]
    notes: list[NoteEvidence]
    chord_hypotheses: list[ChordHypothesis]
    pitch_class_evidence: list[PitchClassEvidence] = field(default_factory=list)
    direct_chord_evidence: list[DirectChordEvidence] = field(default_factory=list)
    chord_candidates: list[ChordCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration is not None:
            duration = _finite_number(self.duration, "duration")
            if duration < 0:
                raise ValueError("duration must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def to_note_evidence(note: Mapping[str, Any], source: str) -> NoteEvidence:
    """Adapt one existing parsed MIDI note without reinterpreting velocity."""
    pitch_raw = note.get("pitch")
    if isinstance(pitch_raw, bool) or not isinstance(pitch_raw, int):
        raise ValueError("parsed note pitch must be an integer MIDI note")
    pitch = pitch_raw
    metadata: dict[str, Any] = {}
    if "duration" in note:
        metadata["parsed_duration"] = note["duration"]
    return NoteEvidence(
        start=note.get("start"),
        end=note.get("end"),
        pitch=pitch,
        pitch_class=pitch % 12,
        octave=(pitch // 12) - 1,
        velocity_or_amplitude=note.get("velocity"),
        confidence=None,
        source=_source(source),
        metadata=metadata,
    )


def notes_to_evidence(
    notes: Iterable[Mapping[str, Any]], source: str
) -> list[NoteEvidence]:
    return [to_note_evidence(note, source) for note in notes]


def basic_pitch_event_to_note_evidence(event: Sequence[Any]) -> NoteEvidence:
    """Adapt BasicPitch 0.4.0's in-memory note-event tuple."""
    if len(event) != 5:
        raise ValueError("BasicPitch note event must contain five values")
    start, end, pitch_raw, amplitude, bends = event
    if isinstance(pitch_raw, bool) or not isinstance(pitch_raw, Integral):
        raise ValueError("BasicPitch pitch must be an integer MIDI note")
    pitch = int(pitch_raw)
    pitch_bends = None if bends is None else [int(value) for value in bends]
    return NoteEvidence(
        start=start,
        end=end,
        pitch=pitch,
        pitch_class=pitch % 12,
        octave=(pitch // 12) - 1,
        velocity_or_amplitude=amplitude,
        confidence=None,
        source="basic_pitch",
        metadata={
            "value_semantics": "basic_pitch_amplitude",
            "pitch_bends": pitch_bends,
        },
    )


def basic_pitch_events_to_note_evidence(
    events: Iterable[Sequence[Any]],
) -> list[NoteEvidence]:
    return [basic_pitch_event_to_note_evidence(event) for event in events]


def compare_note_evidence(
    direct_notes: Sequence[NoteEvidence],
    midi_notes: Sequence[NoteEvidence],
    onset_tolerance: float = 0.05,
    offset_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Deterministically compare direct and MIDI-derived note evidence."""
    if onset_tolerance < 0 or offset_tolerance < 0:
        raise ValueError("comparison tolerances must be >= 0")

    candidates: list[tuple[float, float, float, int, int]] = []
    for direct_index, direct in enumerate(direct_notes):
        for midi_index, midi in enumerate(midi_notes):
            if direct.pitch != midi.pitch:
                continue
            onset_delta = abs(direct.start - midi.start)
            offset_delta = abs(direct.end - midi.end)
            if onset_delta <= onset_tolerance and offset_delta <= offset_tolerance:
                candidates.append((
                    onset_delta + offset_delta,
                    onset_delta,
                    offset_delta,
                    direct_index,
                    midi_index,
                ))

    matched_direct: set[int] = set()
    matched_midi: set[int] = set()
    matches: list[dict[str, Any]] = []
    for _, onset_delta, offset_delta, direct_index, midi_index in sorted(candidates):
        if direct_index in matched_direct or midi_index in matched_midi:
            continue
        matched_direct.add(direct_index)
        matched_midi.add(midi_index)
        direct = direct_notes[direct_index]
        midi = midi_notes[midi_index]
        midi_amplitude = (
            None
            if midi.velocity_or_amplitude is None
            else float(midi.velocity_or_amplitude) / 127.0
        )
        amplitude_delta = (
            None
            if direct.velocity_or_amplitude is None or midi_amplitude is None
            else abs(float(direct.velocity_or_amplitude) - midi_amplitude)
        )
        matches.append({
            "direct_index": direct_index,
            "midi_index": midi_index,
            "pitch": direct.pitch,
            "onset_difference_sec": onset_delta,
            "offset_difference_sec": offset_delta,
            "amplitude_difference": amplitude_delta,
            "pitch_class_equal": direct.pitch_class == midi.pitch_class,
        })

    direct_only = [
        index for index in range(len(direct_notes)) if index not in matched_direct
    ]
    midi_only = [
        index for index in range(len(midi_notes)) if index not in matched_midi
    ]
    return {
        "matching": {
            "algorithm": "greedy_minimum_timing_delta",
            "pitch_must_match": True,
            "onset_tolerance_sec": onset_tolerance,
            "offset_tolerance_sec": offset_tolerance,
        },
        "direct_note_count": len(direct_notes),
        "midi_note_count": len(midi_notes),
        "matched_note_count": len(matches),
        "direct_only_indices": direct_only,
        "midi_only_indices": midi_only,
        "pitch_match_rate": (
            len(matches) / max(len(direct_notes), len(midi_notes), 1)
        ),
        "ordering_equal": (
            [note.pitch for note in direct_notes]
            == [note.pitch for note in midi_notes]
        ),
        "pitch_class_mismatch_count": sum(
            not match["pitch_class_equal"] for match in matches
        ),
        "onset_differences_sec": [
            match["onset_difference_sec"] for match in matches
        ],
        "offset_differences_sec": [
            match["offset_difference_sec"] for match in matches
        ],
        "amplitude_differences": [
            match["amplitude_difference"] for match in matches
            if match["amplitude_difference"] is not None
        ],
        "matches": matches,
    }


def normalized_event_to_hypothesis(
    event: Mapping[str, Any], warnings: Optional[Iterable[str]] = None
) -> ChordHypothesis:
    """Convert an existing normalized event into an observational hypothesis."""
    return ChordHypothesis(
        start=event.get("start"),
        end=event.get("end"),
        chord=str(event.get("chord") or ""),
        confidence=event.get("confidence"),
        source=_source(event.get("source_detector"), "source_detector"),
        alternatives=list(event.get("alternatives") or []),
        warnings=[str(item) for item in (warnings or [])],
        supporting_sources=list(event.get("supporting_sources") or []),
    )


def hypothesis_to_normalized_event(
    hypothesis: ChordHypothesis,
) -> dict[str, Any]:
    """Return exactly the fields in HorizonJam's normalized event contract."""
    return {
        "start": hypothesis.start,
        "end": hypothesis.end,
        "chord": hypothesis.chord,
        "confidence": hypothesis.confidence,
        "source_detector": hypothesis.source,
    }
