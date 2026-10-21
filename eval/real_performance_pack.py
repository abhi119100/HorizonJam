"""Validation and readiness checks for Real Performance Pack v1."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "real-performance-pack-v1"
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
RIGHTS = {"OWNED", "CONSENTED", "LICENSED"}
REQUIRED_QUALITIES = {"major", "minor", "dominant_seventh", "major_seventh", "minor_seventh", "sus2", "sus4"}
REQUIRED_STYLES = {"block_chords", "strumming", "slow_arpeggios", "faster_arpeggios", "partial_voicings", "inversions", "repeated_transitions"}
REQUIRED_CONDITIONS = {"quiet_room", "moderate_background_noise", "multiple_devices", "different_dynamics", "slight_tuning_difference"}
REQUIRED_HARMONIC_EXAMPLES = {"I-IV-V-I", "i-iv-V-i", "ii-V-I", "vi-IV-I-V", "secondary_dominant", "relative_major_minor_ambiguous"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def held_out_digest(cases: list[dict[str, Any]]) -> str:
    """Identity of held-out audio and labels, not a claim of annotation correctness."""
    payload = [
        {"case_id": case.get("case_id"), "audio_sha256": (case.get("audio") or {}).get("sha256"),
         "annotations": case.get("annotations")}
        for case in cases if isinstance(case, dict) and case.get("split") == "held_out"
    ]
    payload.sort(key=lambda case: str(case["case_id"]))
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _text(value: Any, field: str, errors: list[str]) -> str:
    result = str(value or "").strip()
    if not result:
        errors.append(f"{field} is required")
    return result


def validate_manifest(
    path: Path,
    manifest_override: dict[str, Any] | None = None,
    root_override: Path | None = None,
) -> dict[str, Any]:
    """Validate a manifest; overrides exist only for side-effect-free tests."""
    root = (root_override or path.parent).resolve()
    manifest = (
        manifest_override
        if manifest_override is not None
        else json.loads(path.read_text(encoding="utf-8"))
    )
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("status") not in {"collecting", "frozen"}:
        errors.append("status must be collecting or frozen")
    minimum = manifest.get("minimum_cases")
    if not isinstance(minimum, int) or minimum < 20:
        errors.append("minimum_cases must be an integer >= 20")
        minimum = 20
    split_policy = manifest.get("split_policy")
    if not isinstance(split_policy, dict):
        errors.append("split_policy must be an object")
    else:
        development = split_policy.get("development_fraction")
        held_out = split_policy.get("held_out_fraction")
        if not all(isinstance(value, (int, float)) for value in (development, held_out)):
            errors.append("split fractions must be numeric")
        elif not all(math.isfinite(value) and 0 < value < 1 for value in (development, held_out)):
            errors.append("split fractions must be finite and strictly between zero and one")
        elif not math.isclose(float(development) + float(held_out), 1.0, abs_tol=1e-9):
            errors.append("development and held-out fractions must sum to 1")
        _text(split_policy.get("assignment_policy"), "split assignment_policy", errors)

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []
    ids: set[str] = set()
    coverage = {key: set() for key in ("qualities", "playing_styles", "conditions", "harmonic_examples")}
    counts = {"development": 0, "held_out": 0, "chord_isolation": 0, "progression": 0}
    independent_annotation_cases = 0
    group_splits: dict[tuple[str, str], str] = {}
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = _text(case.get("case_id"), f"{prefix}.case_id", errors)
        if case_id in ids:
            errors.append(f"duplicate case_id {case_id}")
        ids.add(case_id)
        split, category = case.get("split"), case.get("category")
        for field in ("performer_id", "recording_session_id", "device_id"):
            value = _text(case.get(field), f"{prefix}.{field}", errors)
            if value and field != "device_id":
                key = (field, value)
                if key in group_splits and group_splits[key] != split:
                    errors.append(f"{prefix}.{field} leaks across development and held-out splits")
                group_splits[key] = split
        if split not in {"development", "held_out"}:
            errors.append(f"{prefix}.split must be development or held_out")
        else:
            counts[split] += 1
        if category not in {"chord_isolation", "progression"}:
            errors.append(f"{prefix}.category must be chord_isolation or progression")
        else:
            counts[category] += 1

        audio = case.get("audio")
        if not isinstance(audio, dict):
            errors.append(f"{prefix}.audio must be an object")
        else:
            relative = _text(audio.get("path"), f"{prefix}.audio.path", errors)
            digest = str(audio.get("sha256") or "").lower()
            if digest:
                key = ("audio_sha256", digest)
                if key in group_splits and group_splits[key] != split:
                    errors.append(f"{prefix}.audio.sha256 duplicates audio across splits")
                group_splits[key] = split
            if not _SHA256.fullmatch(digest):
                errors.append(f"{prefix}.audio.sha256 must be lowercase SHA-256")
            duration = audio.get("duration_sec")
            if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
                errors.append(f"{prefix}.audio.duration_sec must be finite and > 0")
            if relative:
                resolved = (root / relative).resolve()
                if root not in resolved.parents:
                    errors.append(f"{prefix}.audio.path escapes the pack directory")
                elif not resolved.is_file():
                    errors.append(f"{prefix}.audio.path does not exist")
                elif digest and hashlib.sha256(resolved.read_bytes()).hexdigest() != digest:
                    errors.append(f"{prefix}.audio.sha256 does not match the file")

        provenance = case.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{prefix}.provenance must be an object")
        else:
            if provenance.get("rights_basis") not in RIGHTS:
                errors.append(f"{prefix}.provenance.rights_basis is invalid")
            _text(provenance.get("rights_reference"), f"{prefix}.provenance.rights_reference", errors)
            _text(provenance.get("source"), f"{prefix}.provenance.source", errors)
            if not isinstance(provenance.get("redistribution_allowed"), bool):
                errors.append(f"{prefix}.provenance.redistribution_allowed must be boolean")
        _text(case.get("instrument"), f"{prefix}.instrument", errors)
        for key in coverage:
            values = case.get(key)
            if not isinstance(values, list):
                errors.append(f"{prefix}.{key} must be a list")
            else:
                coverage[key].update(str(value) for value in values)

        annotations = case.get("annotations")
        if not isinstance(annotations, list) or not annotations:
            errors.append(f"{prefix}.annotations must contain at least one annotation")
            continue
        if len({item.get("annotator_id") for item in annotations if isinstance(item, dict)}) >= 2:
            independent_annotation_cases += 1
        for ann_index, annotation in enumerate(annotations):
            ann_prefix = f"{prefix}.annotations[{ann_index}]"
            if not isinstance(annotation, dict):
                errors.append(f"{ann_prefix} must be an object")
                continue
            _text(annotation.get("annotator_id"), f"{ann_prefix}.annotator_id", errors)
            _text(annotation.get("annotation_date"), f"{ann_prefix}.annotation_date", errors)
            if annotation.get("confidence") not in CONFIDENCE:
                errors.append(f"{ann_prefix}.confidence must be HIGH, MEDIUM, or LOW")
            if not isinstance(annotation.get("notes"), str):
                errors.append(f"{ann_prefix}.notes must be a string")
            segments = annotation.get("segments")
            if not isinstance(segments, list) or not segments:
                errors.append(f"{ann_prefix}.segments must not be empty")
                continue
            prior_end = 0.0
            for seg_index, segment in enumerate(segments):
                seg_prefix = f"{ann_prefix}.segments[{seg_index}]"
                if not isinstance(segment, dict):
                    errors.append(f"{seg_prefix} must be an object")
                    continue
                start, end = segment.get("start"), segment.get("end")
                if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (start, end)):
                    errors.append(f"{seg_prefix} timing must be finite numeric values")
                elif start < 0 or end <= start or start < prior_end:
                    errors.append(f"{seg_prefix} must be sorted, non-overlapping, and positive-duration")
                else:
                    prior_end = float(end)
                    duration = (case.get("audio") or {}).get("duration_sec")
                    if isinstance(duration, (int, float)) and end > duration + 1e-6:
                        errors.append(f"{seg_prefix} extends beyond the recording duration")
                _text(segment.get("chord"), f"{seg_prefix}.chord", errors)

    if counts["held_out"] > 0 and (
        not manifest.get("held_out_frozen_at")
        or not _SHA256.fullmatch(str(manifest.get("held_out_labels_sha256") or "").lower())
    ):
        errors.append("held-out labels require frozen_at and SHA-256")
    elif counts["held_out"] > 0 and manifest.get("held_out_labels_sha256") != held_out_digest(cases):
        errors.append("held-out audio/label digest does not match the frozen manifest")
    requirements = {
        "qualities": REQUIRED_QUALITIES, "playing_styles": REQUIRED_STYLES,
        "conditions": REQUIRED_CONDITIONS, "harmonic_examples": REQUIRED_HARMONIC_EXAMPLES,
    }
    gaps = {key: sorted(required - coverage[key]) for key, required in requirements.items()}
    readiness_reasons = []
    if len(cases) < minimum:
        readiness_reasons.append(f"requires at least {minimum} approved cases; found {len(cases)}")
    if manifest.get("status") != "frozen":
        readiness_reasons.append("collection must be frozen before evaluation")
    if counts["chord_isolation"] == 0 or counts["progression"] == 0:
        readiness_reasons.append("requires both chord-isolation and progression cases")
    if counts["development"] == 0 or counts["held_out"] == 0:
        readiness_reasons.append("requires development and held-out cases")
    if cases and independent_annotation_cases != len(cases):
        readiness_reasons.append("each case requires two distinct annotators before evaluation")
    for key, missing in gaps.items():
        if missing:
            readiness_reasons.append(f"missing {key}: {', '.join(missing)}")
    if errors:
        readiness_reasons.append("manifest validation errors must be resolved")
    return {
        "manifest": manifest, "validation_errors": errors, "case_count": len(cases),
        "counts": counts, "coverage": {key: sorted(values) for key, values in coverage.items()},
        "coverage_gaps": gaps, "independent_annotation_cases": independent_annotation_cases,
        "ready": not readiness_reasons, "readiness_reasons": readiness_reasons,
    }
