"""Phase 3 product-safe Librosa chroma evidence gate."""
from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from detection import run_detection
from src.dsp_chroma import (
    DEFAULT_CONFIG,
    extract_pitch_class_evidence,
    score_chroma_values,
    score_pitch_class_evidence,
    summarize_frame_candidates,
)


JSON_REPORT = ROOT / "eval" / "dsp_chroma_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "dsp_chroma_report.md"
SAMPLE_RATE = 22050


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _render(path: Path, duration: float, pitches: list[int]) -> None:
    frames = int(round(duration * SAMPLE_RATE))
    timeline = np.arange(frames, dtype=np.float64) / SAMPLE_RATE
    active = (timeline >= 0.2) & (timeline < duration - 0.2)
    audio = np.zeros(frames, dtype=np.float64)
    for pitch in pitches:
        frequency = 440.0 * (2.0 ** ((pitch - 69) / 12.0))
        audio[active] += 0.2 * np.sin(2.0 * np.pi * frequency * timeline[active])
    peak = float(np.max(np.abs(audio)))
    if peak > 0.95:
        audio *= 0.95 / peak
    sf.write(path, audio.astype(np.float32), SAMPLE_RATE, subtype="PCM_16")


def _aggregate_prediction(evidence) -> tuple[str, list[dict[str, Any]]]:
    active = [item for item in evidence if sum(item.values) > 1e-8]
    if not active:
        return "N", []
    aggregate = np.mean(np.asarray([item.values for item in active]), axis=0)
    ranked = score_chroma_values(aggregate.tolist())
    return ranked[0]["label"], ranked[:3]


def _symbolic_prediction(result: dict[str, Any]) -> str:
    events = result.get("chord_events") or []
    if not events:
        return "N"
    winner = max(events, key=lambda event: (event["end"] - event["start"], -event["start"]))
    return winner["chord"]


def _mean_vector(evidence) -> np.ndarray:
    active = [item.values for item in evidence if sum(item.values) > 1e-8]
    return np.mean(np.asarray(active), axis=0) if active else np.zeros(12)


def build_report() -> dict[str, Any]:
    fixtures = {
        "c_major": ("C", [60, 64, 67]),
        "a_minor": ("Am", [57, 60, 64]),
        "g_dominant7": ("G7", [55, 59, 62, 65]),
        "c_major7": ("Cmaj7", [60, 64, 67, 71]),
        "d_minor7": ("Dm7", [62, 65, 69, 72]),
        "d_sus2": ("Dsus2", [62, 64, 69]),
        "a_sus4": ("Asus4", [57, 62, 64]),
        "b_diminished": ("Bdim", [59, 62, 65]),
    }
    generated: list[Path] = []
    cases = []
    tuning_cases = []
    try:
        for index, (name, (expected, pitches)) in enumerate(fixtures.items()):
            path = ROOT / "eval" / "data" / f"phase3_{name}.wav"
            generated.append(path)
            _render(path, 2.0, pitches)
            evidence, metadata = extract_pitch_class_evidence(str(path))
            frames, scoring_timing = score_pitch_class_evidence(evidence)
            dsp_prediction, alternatives = _aggregate_prediction(evidence)
            symbolic = run_detection(str(path), detector="rule_jaccard")
            symbolic_prediction = _symbolic_prediction(symbolic)
            dsp_correct = dsp_prediction == expected
            symbolic_correct = symbolic_prediction == expected
            cases.append({
                "name": name,
                "expected": expected,
                "fixture_kind": "deterministic synthetic sine block chord",
                "dsp_prediction": dsp_prediction,
                "dsp_top3": alternatives,
                "frame_majority_prediction": summarize_frame_candidates(frames),
                "rule_jaccard_prediction": symbolic_prediction,
                "dsp_correct": dsp_correct,
                "rule_jaccard_correct": symbolic_correct,
                "comparison": (
                    "both_correct" if dsp_correct and symbolic_correct
                    else "dsp_only_correct" if dsp_correct
                    else "rule_jaccard_only_correct" if symbolic_correct
                    else "both_fail"
                ),
                "estimated_tuning_bins": metadata["estimated_tuning_bins"],
                "frame_count": metadata["frame_count"],
                "timings_sec": {
                    **metadata["timings_sec"],
                    **scoring_timing,
                },
            })
            if index < 2:
                zero_evidence, zero_metadata = extract_pitch_class_evidence(
                    str(path), {"tuning": 0.0}
                )
                zero_prediction, _ = _aggregate_prediction(zero_evidence)
                tuning_cases.append({
                    "name": name,
                    "estimated_tuning_bins": metadata["estimated_tuning_bins"],
                    "estimated_prediction": dsp_prediction,
                    "zero_tuning_prediction": zero_prediction,
                    "mean_absolute_chroma_difference": float(np.mean(np.abs(
                        _mean_vector(evidence) - _mean_vector(zero_evidence)
                    ))),
                    "zero_tuning_total_sec": zero_metadata["timings_sec"]["total"],
                })

        source = ROOT / "tests" / "audio" / "pop.wav"
        audio, sample_rate = sf.read(source, dtype="float32", always_2d=True)
        scaling = []
        for duration in (3, 10, 30):
            frames = int(round(duration * sample_rate))
            repeats = int(np.ceil(frames / len(audio)))
            repeated = np.tile(audio, (repeats, 1))[:frames]
            path = ROOT / "eval" / "data" / f"phase3_runtime_{duration}s.wav"
            generated.append(path)
            sf.write(path, repeated, sample_rate, subtype="PCM_16")
            evidence, metadata = extract_pitch_class_evidence(str(path))
            _, scoring_timing = score_pitch_class_evidence(evidence)
            scaling.append({
                "duration_sec": duration,
                "frame_count": len(evidence),
                "timings_sec": {**metadata["timings_sec"], **scoring_timing},
            })
    finally:
        for path in generated:
            path.unlink(missing_ok=True)

    dsp_correct = sum(case["dsp_correct"] for case in cases)
    symbolic_correct = sum(case["rule_jaccard_correct"] for case in cases)
    dsp_only = sum(case["comparison"] == "dsp_only_correct" for case in cases)
    symbolic_only = sum(case["comparison"] == "rule_jaccard_only_correct" for case in cases)
    both_correct = sum(case["comparison"] == "both_correct" for case in cases)
    both_fail = sum(case["comparison"] == "both_fail" for case in cases)
    if dsp_correct >= 4 and (dsp_only > 0 or symbolic_only > 0):
        decision = "A DSP_COMPLEMENTARY"
    elif dsp_correct >= 4:
        decision = "B DSP_STRONG_STANDALONE"
    elif dsp_correct > 0:
        decision = "C DSP_WEAK_BUT_USEFUL_FOR_SUPPORT"
    else:
        decision = "D DSP_NOT_USEFUL"
    return {
        "schema_version": "dsp-chroma-evidence-gate-v1",
        "command": "python eval/evaluate_dsp_chroma.py",
        "evidence_level": "L2 deterministic synthetic diagnostic and L6 runtime; no real-performance accuracy claim",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                name: _version(name)
                for name in ("librosa", "numpy", "numba", "soundfile")
            },
        },
        "pipeline": {
            "audio": "soundfile float32 decode, mono mean, Librosa resample to 22050 Hz when needed",
            "harmonic_separation": False,
            "feature": "librosa.feature.chroma_cqt",
            "normalization": "L1 per frame",
            "bins_per_octave": 36,
            "hop_length": 512,
            "timebase": "frame index * hop_length / sample_rate, clamped to audio duration",
            "diagnostic": "cosine support against fixed binary chord profiles",
            "vocabulary": ["major", "minor", "dominant7", "major7", "minor7", "sus2", "sus4", "diminished"],
            "score_semantics": "normalized support, not probability or calibrated confidence",
        },
        "cases": cases,
        "tuning_audit": {
            "cases": tuning_cases,
            "prediction_changed": any(
                case["estimated_prediction"] != case["zero_tuning_prediction"]
                for case in tuning_cases
            ),
            "policy": "retain Librosa estimated tuning and record it; no larger tuning machinery",
        },
        "runtime_scaling": scaling,
        "comparison": {
            "case_count": len(cases),
            "dsp_exact": dsp_correct,
            "rule_jaccard_exact": symbolic_correct,
            "both_correct": both_correct,
            "dsp_only_correct": dsp_only,
            "rule_jaccard_only_correct": symbolic_only,
            "both_fail": both_fail,
        },
        "decision_gate": {
            "outcome": decision,
            "default_detector_changed": False,
            "activation": "research diagnostic only",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DSP / Chroma Evidence Gate",
        "",
        f"Decision: **{report['decision_gate']['outcome']}**.",
        "",
        "Synthetic diagnostic and runtime evidence only. No real-performance accuracy claim is made.",
        "",
        "## Controlled chord cases",
        "",
        "| Case | Expected | DSP | Jaccard | Outcome |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            f"| {case['name']} | {case['expected']} | {case['dsp_prediction']} | "
            f"{case['rule_jaccard_prediction']} | {case['comparison']} |"
        )
    lines.extend([
        "",
        "## Runtime scaling",
        "",
        "| Audio | Load | Tuning | CQT/chroma | Scoring | Total |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for item in report["runtime_scaling"]:
        timing = item["timings_sec"]
        lines.append(
            f"| {item['duration_sec']}s | {timing['audio_load']:.4f}s | "
            f"{timing['tuning_estimation']:.4f}s | {timing['cqt_chroma']:.4f}s | "
            f"{timing['candidate_scoring']:.4f}s | {timing['total']:.4f}s |"
        )
    lines.extend([
        "",
        "Raw `PitchClassEvidence` remains separate from the research-only profile interpretation. Scores are normalized cosine support, not probability or calibrated confidence. The default detector is unchanged.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "decision": report["decision_gate"]["outcome"],
        "comparison": report["comparison"],
        "runtime_scaling": report["runtime_scaling"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
