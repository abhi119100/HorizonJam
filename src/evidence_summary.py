"""Compact product-facing explanations derived from existing harmonic evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence

from .chord_labels import decompose_chord_label


STRENGTHS = {
    "STRONG_AGREEMENT", "PARTIAL_AGREEMENT", "MIXED_EVIDENCE", "LIMITED_EVIDENCE",
}
AGREEMENTS = {
    "SYMBOLIC_DSP_EXACT", "SYMBOLIC_DSP_ROOT", "SYMBOLIC_DSP_DISAGREE",
    "SYMBOLIC_ONLY",
}
PITCH_CLASS_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _finite(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


@dataclass(frozen=True)
class EvidenceSummary:
    start: float
    end: float
    chord: str
    strength: str
    agreement: str
    observed_notes: list[str]
    harmonic_candidate: str | None
    supporting_sources: list[str]
    warnings: list[str]
    short_explanation: str
    schema_version: str = "evidence-summary-v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        start, end = _finite(self.start, "start"), _finite(self.end, "end")
        if start < 0 or end <= start:
            raise ValueError("EvidenceSummary requires a positive interval")
        if not str(self.chord or "").strip():
            raise ValueError("chord is required")
        if self.strength not in STRENGTHS:
            raise ValueError(f"unsupported evidence strength: {self.strength}")
        if self.agreement not in AGREEMENTS:
            raise ValueError(f"unsupported evidence agreement: {self.agreement}")
        if any(not str(value or "").strip() for value in self.supporting_sources):
            raise ValueError("supporting_sources must contain non-empty names")
        if not str(self.short_explanation or "").strip():
            raise ValueError("short_explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evidence_summary_from_mapping(raw: Mapping[str, Any]) -> EvidenceSummary:
    """Validate an EvidenceSummary received across an application boundary."""
    return EvidenceSummary(
        start=raw.get("start"), end=raw.get("end"), chord=str(raw.get("chord") or ""),
        strength=str(raw.get("strength") or ""), agreement=str(raw.get("agreement") or ""),
        observed_notes=[str(value) for value in (raw.get("observed_notes") or [])][:12],
        harmonic_candidate=(str(raw["harmonic_candidate"]) if raw.get("harmonic_candidate") else None),
        supporting_sources=[str(value) for value in (raw.get("supporting_sources") or [])][:4],
        warnings=[str(value) for value in (raw.get("warnings") or [])][:8],
        short_explanation=str(raw.get("short_explanation") or ""),
        schema_version=str(raw.get("schema_version") or "evidence-summary-v1"),
        metadata={},
    )


def _overlap(start: float, end: float, item: Mapping[str, Any]) -> float:
    return max(0.0, min(end, float(item["end"])) - max(start, float(item["start"])))


def _canonical_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        left.get("status") == right.get("status") == "normalized"
        and left.get("root") == right.get("root")
        and left.get("quality") == right.get("quality")
        and left.get("bass") == right.get("bass")
        and left.get("pitch_class_set") == right.get("pitch_class_set")
    )


def build_evidence_summaries(
    chord_events: Sequence[Mapping[str, Any]],
    harmonic_packet: Mapping[str, Any] | None,
    detector_warnings: Iterable[str] = (),
) -> list[EvidenceSummary]:
    """Build summaries without changing or ranking the symbolic chord output."""
    packet = harmonic_packet or {}
    notes = [item for item in (packet.get("notes") or []) if isinstance(item, Mapping)]
    chroma = [item for item in (packet.get("pitch_class_evidence") or []) if isinstance(item, Mapping)]
    warnings = [str(value) for value in detector_warnings if str(value).strip()]
    packet_warnings = [str(value) for value in (packet.get("warnings") or []) if str(value).strip()]
    all_warnings = list(dict.fromkeys([*warnings, *packet_warnings]))[:8]
    summaries: list[EvidenceSummary] = []
    for event in chord_events:
        start, end = float(event["start"]), float(event["end"])
        chord = str(event["chord"])
        source = str(event.get("source_detector") or "symbolic_detector")
        event_notes = [item for item in notes if _overlap(start, end, item) > 0.0]
        pitch_classes = sorted({int(item["pitch_class"]) for item in event_notes})
        observed = [PITCH_CLASS_NAMES[value] for value in pitch_classes]

        total = [0.0] * 12
        total_overlap = 0.0
        for frame in chroma:
            overlap = _overlap(start, end, frame)
            values = frame.get("values") or []
            if overlap <= 0.0 or len(values) != 12:
                continue
            total_overlap += overlap
            for index, value in enumerate(values):
                total[index] += float(value) * overlap
        harmonic_candidate = None
        if total_overlap > 0.0 and any(value > 0.0 for value in total):
            from .dsp_chroma import score_chroma_values

            ranked = score_chroma_values([value / total_overlap for value in total])
            if ranked:
                harmonic_candidate = str(ranked[0]["label"])

        symbolic_parts = decompose_chord_label(chord)
        dsp_parts = decompose_chord_label(harmonic_candidate) if harmonic_candidate else None
        sources = [source]
        if event_notes:
            sources.append("basic_pitch")
        if harmonic_candidate:
            sources.append("librosa_chroma")

        if dsp_parts and _canonical_equal(symbolic_parts, dsp_parts):
            agreement = "SYMBOLIC_DSP_EXACT"
            if all_warnings:
                strength = "PARTIAL_AGREEMENT"
                explanation = f"The detected notes and harmonic spectrum support {chord}, with analysis warnings noted."
            else:
                strength = "STRONG_AGREEMENT"
                explanation = f"The detected notes and harmonic spectrum both support {chord}."
        elif dsp_parts and symbolic_parts.get("root") == dsp_parts.get("root"):
            agreement = "SYMBOLIC_DSP_ROOT"
            strength = "PARTIAL_AGREEMENT"
            explanation = f"The harmonic spectrum supports the {symbolic_parts.get('root')} root, but the chord quality is less clear."
        elif harmonic_candidate:
            agreement = "SYMBOLIC_DSP_DISAGREE"
            strength = "MIXED_EVIDENCE"
            explanation = f"Detected notes favor {chord}, while the harmonic spectrum favors {harmonic_candidate}."
        else:
            agreement = "SYMBOLIC_ONLY"
            strength = "LIMITED_EVIDENCE"
            explanation = f"HorizonJam detected {chord}, but independent harmonic evidence was unavailable."

        summaries.append(EvidenceSummary(
            start=start, end=end, chord=chord, strength=strength, agreement=agreement,
            observed_notes=observed, harmonic_candidate=harmonic_candidate,
            supporting_sources=list(dict.fromkeys(sources)), warnings=all_warnings,
            short_explanation=explanation,
            metadata={"semantics": "categorical evidence strength; not calibrated confidence"},
        ))
    return summaries
