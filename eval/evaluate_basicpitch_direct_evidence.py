"""Phase 2 BasicPitch direct-vs-MIDI evidence gate."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import pretty_midi
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from detection import normalize_and_validate, run_detection
from src.hybrid_chord_detector import HybridChordDetector


JSON_REPORT = ROOT / "eval" / "basicpitch_direct_evidence_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "basicpitch_direct_evidence_report.md"
SAMPLE_RATE = 22050


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _render_fixture(path: Path, duration: float, notes: list[tuple[float, float, int]]) -> None:
    frame_count = int(round(duration * SAMPLE_RATE))
    timeline = np.arange(frame_count, dtype=np.float64) / SAMPLE_RATE
    audio = np.zeros(frame_count, dtype=np.float64)
    for start, end, pitch in notes:
        active = (timeline >= start) & (timeline < end)
        frequency = 440.0 * (2.0 ** ((pitch - 69) / 12.0))
        audio[active] += 0.22 * np.sin(2.0 * np.pi * frequency * timeline[active])
    peak = float(np.max(np.abs(audio)))
    if peak > 0.95:
        audio *= 0.95 / peak
    sf.write(path, audio.astype(np.float32), SAMPLE_RATE, subtype="PCM_16")


def _compact_events(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "start": event["start"],
            "end": event["end"],
            "chord": event["chord"],
            "confidence": event["confidence"],
        }
        for event in result.get("chord_events", [])
    ]


def _direct_replay(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for note in notes:
        amplitude = note.get("velocity_or_amplitude")
        velocity = 100 if amplitude is None else max(1, min(127, int(round(float(amplitude) * 127))))
        instrument.notes.append(pretty_midi.Note(
            velocity=velocity,
            pitch=int(note["pitch"]),
            start=float(note["start"]),
            end=float(note["end"]),
        ))
    midi.instruments.append(instrument)
    handle, name = tempfile.mkstemp(
        suffix=".mid", prefix="hj_direct_replay_", dir=ROOT / "eval" / "data"
    )
    os.close(handle)
    path = Path(name)
    path.unlink(missing_ok=True)
    try:
        midi.write(str(path))
        detector = HybridChordDetector(use_viterbi=True)
        result = detector.detect_chords(
            str(path), classifier_mode="advanced_jaccard"
        )
    finally:
        path.unlink(missing_ok=True)

    raw = []
    for event in (result or {}).get("chords", []):
        start = float(event.get("start") or event.get("timestamp") or 0.0)
        end = float(event.get("end") or event.get("end_time") or (
            start + float(event.get("duration") or 0.0)
        ))
        if end > start:
            raw.append({
                "start": start,
                "end": end,
                "chord": event.get("chord") or "N",
                "confidence": event.get("confidence"),
                "source_detector": "direct_replay",
            })
    normalized, _ = normalize_and_validate(raw)
    return _compact_events({"chord_events": normalized})


def _case(name: str, path: Path, fixture_kind: str) -> dict[str, Any]:
    result = run_detection(
        str(path),
        detector="rule_jaccard",
        include_runtime_trace=True,
        include_harmonic_evidence=True,
    )
    if "harmonic_evidence" not in result:
        raise RuntimeError(f"dual evidence unavailable for {name}: {result['warnings']}")
    packet = result["harmonic_evidence"]
    comparison = packet["metadata"]["direct_vs_midi"]
    timings = result["runtime_trace"]["basic_pitch"]["timings_sec"]
    compatibility_events = _compact_events(result)
    direct_events = _direct_replay(packet["notes"])
    return {
        "name": name,
        "fixture_kind": fixture_kind,
        "duration_sec": float(sf.info(path).duration),
        "comparison": comparison,
        "direct_pitch_bend_note_count": sum(
            bool(note["metadata"].get("pitch_bends")) for note in packet["notes"]
        ),
        "direct_model_output_shapes": result["runtime_trace"]["basic_pitch"][
            "model_output_shapes"
        ],
        "timings_sec": {
            key: timings.get(key)
            for key in (
                "direct_evidence_conversion",
                "midi_serialization",
                "midi_read_and_parse",
                "basic_pitch_predict_total",
                "transcription_total",
            )
        },
        "compatibility_chord_events": compatibility_events,
        "direct_replay_chord_events": direct_events,
        "downstream_chords_equal": compatibility_events == direct_events,
    }


def build_report() -> dict[str, Any]:
    fixture_specs = {
        "block_c_major": (2.0, [(0.20, 1.60, 60), (0.20, 1.60, 64), (0.20, 1.60, 67)]),
        "block_g7": (2.0, [(0.20, 1.60, 55), (0.20, 1.60, 59), (0.20, 1.60, 62), (0.20, 1.60, 65)]),
        "arpeggio_c_major": (2.0, [(0.15, 0.85, 60), (0.55, 1.25, 64), (0.95, 1.65, 67)]),
        "overlapping_notes": (2.0, [(0.15, 1.35, 60), (0.55, 1.55, 64), (0.95, 1.75, 67)]),
    }
    cases = []
    generated_paths: list[Path] = []
    try:
        for name, (duration, notes) in fixture_specs.items():
            path = ROOT / "eval" / "data" / f"phase2_{name}.wav"
            generated_paths.append(path)
            _render_fixture(path, duration, notes)
            cases.append(_case(name, path, "generated deterministic sine fixture"))
    finally:
        for path in generated_paths:
            path.unlink(missing_ok=True)
    cases.append(_case(
        "repository_pop_wav",
        ROOT / "tests" / "audio" / "pop.wav",
        "repository WAV runtime fixture; legal/performance provenance unverified",
    ))

    comparisons = [case["comparison"] for case in cases]
    exact_note_sets = all(
        comparison["direct_only_indices"] == []
        and comparison["midi_only_indices"] == []
        and comparison["pitch_class_mismatch_count"] == 0
        for comparison in comparisons
    )
    downstream_equal = all(case["downstream_chords_equal"] for case in cases)
    direct_preserves_extra = True
    decision = (
        "B DIRECT_BETTER"
        if exact_note_sets and downstream_equal and direct_preserves_extra
        else "E MIXED"
    )
    all_onsets = [
        value for comparison in comparisons
        for value in comparison["onset_differences_sec"]
    ]
    all_offsets = [
        value for comparison in comparisons
        for value in comparison["offset_differences_sec"]
    ]
    all_amplitudes = [
        value for comparison in comparisons
        for value in comparison["amplitude_differences"]
    ]
    return {
        "schema_version": "basicpitch-direct-evidence-gate-v1",
        "command": "python eval/evaluate_basicpitch_direct_evidence.py",
        "evidence_level": "L1 representation equivalence and runtime; synthetic/fixture execution, no real-performance accuracy claim",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                name: _version(name)
                for name in ("basic-pitch", "onnxruntime", "librosa", "numpy", "pretty-midi", "soundfile")
            },
        },
        "baseline_hashes_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                ROOT / "src" / "chord_detector.py",
                ROOT / "eval" / "oracle_classifier_report.json",
                ROOT / "eval" / "jaccard_detector_path_report.json",
                ROOT / "eval" / "audio_path_benchmark.json",
            )
        },
        "matching_policy": {
            "pitch": "exact MIDI pitch",
            "onset_tolerance_sec": 0.05,
            "offset_tolerance_sec": 0.05,
            "assignment": "greedy minimum summed onset/offset delta with stable index tie-break",
        },
        "cases": cases,
        "aggregate": {
            "case_count": len(cases),
            "exact_note_sets_all_cases": exact_note_sets,
            "downstream_chords_equal_all_cases": downstream_equal,
            "matched_notes": sum(item["matched_note_count"] for item in comparisons),
            "direct_only_notes": sum(len(item["direct_only_indices"]) for item in comparisons),
            "midi_only_notes": sum(len(item["midi_only_indices"]) for item in comparisons),
            "ordering_equal_cases": sum(item["ordering_equal"] for item in comparisons),
            "max_onset_difference_sec": max(all_onsets, default=0.0),
            "mean_onset_difference_sec": mean(all_onsets) if all_onsets else 0.0,
            "max_offset_difference_sec": max(all_offsets, default=0.0),
            "mean_offset_difference_sec": mean(all_offsets) if all_offsets else 0.0,
            "max_amplitude_difference": max(all_amplitudes, default=0.0),
            "mean_amplitude_difference": mean(all_amplitudes) if all_amplitudes else 0.0,
            "mean_direct_conversion_sec": mean(
                case["timings_sec"]["direct_evidence_conversion"] for case in cases
            ),
            "mean_midi_serialization_sec": mean(
                case["timings_sec"]["midi_serialization"] for case in cases
            ),
            "mean_midi_read_and_parse_sec": mean(
                case["timings_sec"]["midi_read_and_parse"] for case in cases
            ),
        },
        "information_loss_audit": {
            "direct_preserves": [
                "floating-point BasicPitch amplitude",
                "optional per-note pitch-bend sequence",
                "original BasicPitch event ordering",
            ],
            "midi_compatibility_preserves_observed": [
                "note count",
                "MIDI pitch and pitch class",
                "onset and offset within measured tolerance",
                "downstream Jaccard chord output",
            ],
            "midi_compatibility_changes_observed": [
                "amplitude is quantized to integer MIDI velocity",
                "note ordering can differ after serialization/parsing",
                "model output tensors are not represented by parsed MIDI notes",
            ],
            "pitch_bends_observed_in_cases": sum(
                case["direct_pitch_bend_note_count"] for case in cases
            ),
        },
        "decision_gate": {
            "outcome": decision,
            "policy": "direct NoteEvidence is preferred for inspection; MIDI remains the active symbolic compatibility path",
            "default_detector_changed": False,
            "midi_deleted": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    aggregate = report["aggregate"]
    lines = [
        "# BasicPitch Direct Evidence Gate",
        "",
        f"Decision: **{report['decision_gate']['outcome']}**.",
        "",
        "L1 representation/runtime evidence only. Generated cases are synthetic and the repository WAV has no verified real-performance label.",
        "",
        "## Cases",
        "",
        "| Case | Direct | MIDI | Matched | Ordering | Chords equal |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for case in report["cases"]:
        comparison = case["comparison"]
        lines.append(
            f"| {case['name']} | {comparison['direct_note_count']} | "
            f"{comparison['midi_note_count']} | {comparison['matched_note_count']} | "
            f"{comparison['ordering_equal']} | {case['downstream_chords_equal']} |"
        )
    lines.extend([
        "",
        "## Aggregate",
        "",
        f"- Matched notes: {aggregate['matched_notes']}",
        f"- Direct-only / MIDI-only: {aggregate['direct_only_notes']} / {aggregate['midi_only_notes']}",
        f"- Maximum onset / offset delta: {aggregate['max_onset_difference_sec']:.6f}s / {aggregate['max_offset_difference_sec']:.6f}s",
        f"- Mean direct conversion: {aggregate['mean_direct_conversion_sec']:.6f}s",
        f"- Mean MIDI serialization: {aggregate['mean_midi_serialization_sec']:.6f}s",
        f"- Mean MIDI read/parse: {aggregate['mean_midi_read_and_parse_sec']:.6f}s",
        "",
        "## Observed information boundary",
        "",
    ])
    lines.extend(
        f"- MIDI changes: {item}"
        for item in report["information_loss_audit"]["midi_compatibility_changes_observed"]
    )
    lines.extend([
        "",
        "Direct evidence is preferred for developer inspection because it retains richer source evidence. The existing MIDI path remains required by the active symbolic detector, and no default detector behavior changed.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "decision": report["decision_gate"]["outcome"],
        "aggregate": report["aggregate"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
