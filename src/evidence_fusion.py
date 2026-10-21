"""Experimental, deterministic candidate generation and evidence fusion v1."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

from .chord_labels import decompose_chord_label
from .harmonic_evidence import ChordCandidate


DEFAULT_SOURCE_WEIGHTS = {
    "rule_jaccard": 1.0,
    "librosa_chroma": 1.0,
    "lv_chordia": 0.0,
}


@dataclass(frozen=True)
class FusionResult:
    candidates: list[ChordCandidate]
    agreement: str
    candidate_margin: float
    source_disagreement: bool
    active_source_count: int

    @property
    def winner(self) -> ChordCandidate | None:
        return self.candidates[0] if self.candidates else None


def _canonical_key(parts: Mapping[str, Any]) -> tuple[Any, ...]:
    if parts["status"] != "normalized":
        return ("raw", parts["label"])
    return (
        parts["root"],
        parts["quality"],
        parts["bass"],
        tuple(parts["pitch_class_set"]),
    )


def fuse_ranked_sources(
    start: float,
    end: float,
    ranked_sources: Mapping[str, Sequence[Mapping[str, Any]]],
    source_weights: Mapping[str, float] | None = None,
) -> FusionResult:
    """Fuse actual source rankings using explicit weighted normalized support."""
    weights = dict(DEFAULT_SOURCE_WEIGHTS if source_weights is None else source_weights)
    for source, weight in weights.items():
        numeric_weight = float(weight)
        if not isfinite(numeric_weight) or numeric_weight < 0.0:
            raise ValueError(f"source weight for {source} must be finite and >= 0")
    active_sources = [
        source for source, ranking in ranked_sources.items()
        if ranking and float(weights.get(source, 0.0)) > 0.0
    ]
    total_weight = sum(float(weights[source]) for source in active_sources)
    if total_weight <= 0.0:
        return FusionResult([], "agreement_low", 0.0, False, 0)

    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    top_labels: list[tuple[Any, ...]] = []
    for source in sorted(active_sources):
        ranking = ranked_sources[source]
        for index, item in enumerate(ranking):
            support = float(item["normalized_support"])
            if not isfinite(support) or not 0.0 <= support <= 1.0:
                raise ValueError("normalized support must be within 0..1")
            parts = decompose_chord_label(str(item["label"]))
            key = _canonical_key(parts)
            if index == 0:
                top_labels.append(key)
            entry = merged.setdefault(key, {
                "parts": parts,
                "evidence": {},
                "warnings": [],
            })
            # A source can contribute at most once to one canonical candidate.
            entry["evidence"][source] = max(
                support, entry["evidence"].get(source, 0.0)
            )
            if parts["status"] != "normalized":
                entry["warnings"].append("label could not be canonically decomposed")

    candidates: list[ChordCandidate] = []
    for entry in merged.values():
        evidence = dict(sorted(entry["evidence"].items()))
        score = sum(
            evidence.get(source, 0.0) * float(weights[source])
            for source in active_sources
        ) / total_weight
        parts = entry["parts"]
        candidates.append(ChordCandidate(
            start=start,
            end=end,
            label=parts["label"],
            root=parts["root"],
            quality=parts["quality"],
            bass=parts["bass"],
            score=score,
            evidence_sources=list(evidence),
            evidence_breakdown=evidence,
            warnings=sorted(set(entry["warnings"])),
            metadata={
                "score_semantics": "weighted normalized support; not probability",
                "pitch_class_set": parts["pitch_class_set"],
                "source_weights": {
                    source: float(weights[source]) for source in active_sources
                },
            },
        ))
    candidates.sort(key=lambda item: (-item.score, item.label))
    margin = candidates[0].score - candidates[1].score if len(candidates) > 1 else candidates[0].score
    disagreement = len(set(top_labels)) > 1
    winner_sources = len(candidates[0].evidence_sources)
    if not disagreement and winner_sources == len(active_sources) and margin >= 0.15:
        agreement = "agreement_high"
    elif winner_sources > 1 or margin >= 0.15:
        agreement = "agreement_mixed"
    else:
        agreement = "agreement_low"
    return FusionResult(
        candidates=candidates,
        agreement=agreement,
        candidate_margin=margin,
        source_disagreement=disagreement,
        active_source_count=len(active_sources),
    )
