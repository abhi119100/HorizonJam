"""Single-WAV cold/warm performance gate for HorizonJam's active detector path."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_WAV = ROOT / "tests" / "audio" / "pop.wav"
SECOND_WAV = ROOT / "eval" / "data" / "synth" / "wav" / "ii-V-I_C_major.wav"
JSON_REPORT = ROOT / "eval" / "audio_path_benchmark.json"
MARKDOWN_REPORT = ROOT / "eval" / "audio_path_benchmark.md"
WORKER_PREFIX = "HORIZONJAM_RUNTIME_RESULT="

LEGACY_OBSERVATION = {
    "evidence": "fresh pre-optimization run on 2026-08-30 with only NUMBA_CACHE_DIR redirected",
    "fixture": "tests/audio/pop.wav",
    "wall_sec": 30.964243300026283,
    "note_event_count": 4,
    "note_event_hash_sha256": "0aac58190ab431e1af76f06da24405a022dcca62a876f87b5474ca1aeaa93679",
    "model_output_hashes_sha256": {
        "contour": "c16bb5fe20b87203d9eed58493f55fe7eb639dd72d6c892bd7e39af007940309",
        "note": "962de23ff519134ee583f727e77cc05d1c23d9fdd6398054817d16b19dbcaf2c",
        "onset": "f7766bb82fe03a913d03fe3c0129e2b12b6ca47c55a00ee23d38f2b2a145dd87",
    },
    "chord_events": [
        {"start": 0.5945454545454546, "end": 1.1890909090909092, "chord": "Am", "confidence": 0.8},
        {"start": 1.1890909090909092, "end": 1.7836363636363637, "chord": "C", "confidence": 1.0},
        {"start": 1.7836363636363637, "end": 2.3781818181818184, "chord": "Em", "confidence": 0.8},
    ],
}


def fixture_metadata(path: Path) -> dict[str, Any]:
    import soundfile as sf

    info = sf.info(str(path))
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "duration_sec": float(info.duration),
        "sample_rate": int(info.samplerate),
        "channels": int(info.channels),
        "frames": int(info.frames),
        "format": info.format,
        "subtype": info.subtype,
        "file_size_bytes": path.stat().st_size,
    }


def compact_events(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "start": event["start"],
            "end": event["end"],
            "chord": event["chord"],
            "confidence": event["confidence"],
        }
        for event in result.get("chord_events", [])
    ]


def worker(wavs: list[Path], detector: str) -> int:
    process_started = perf_counter()
    import detection

    runs = []
    for wav in wavs:
        started = perf_counter()
        result = detection.run_detection(
            str(wav), detector=detector, include_runtime_trace=True
        )
        runs.append({
            "fixture": fixture_metadata(wav),
            "wall_sec": perf_counter() - started,
            "events": compact_events(result),
            "warnings": result.get("warnings", []),
            "trace": result.get("runtime_trace"),
        })
    payload = {
        "process_wall_sec": perf_counter() - process_started,
        "detector": detector,
        "runs": runs,
    }
    print(WORKER_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def run_fresh_process(wavs: list[Path], detector: str, timeout: int) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--detector",
        detector,
    ]
    for wav in wavs:
        command.extend(("--wav", str(wav)))
    started = perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    parent_wall = perf_counter() - started
    line = next(
        (line for line in reversed(completed.stdout.splitlines()) if line.startswith(WORKER_PREFIX)),
        None,
    )
    if completed.returncode != 0 or line is None:
        raise RuntimeError(
            f"benchmark worker failed rc={completed.returncode}: "
            f"stdout={completed.stdout[-2000:]} stderr={completed.stderr[-2000:]}"
        )
    result = json.loads(line[len(WORKER_PREFIX):])
    result["parent_observed_process_wall_sec"] = parent_wall
    return result


def repeated_fixture(source: Path, destination: Path, duration_sec: float) -> Path:
    import numpy as np
    import soundfile as sf

    audio, sample_rate = sf.read(str(source), dtype="float32", always_2d=True)
    frame_count = int(round(duration_sec * sample_rate))
    repeats = int(np.ceil(frame_count / len(audio)))
    output = np.tile(audio, (repeats, 1))[:frame_count]
    sf.write(str(destination), output, sample_rate, subtype="PCM_16")
    return destination


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def equivalent_to_legacy(run: dict[str, Any]) -> dict[str, Any]:
    basic_pitch = run["trace"]["basic_pitch"]
    return {
        "note_events_equal": basic_pitch["note_event_hash_sha256"] == LEGACY_OBSERVATION["note_event_hash_sha256"],
        "model_outputs_equal": basic_pitch["model_output_hashes_sha256"] == LEGACY_OBSERVATION["model_output_hashes_sha256"],
        "normalized_chord_events_equal": run["events"] == LEGACY_OBSERVATION["chord_events"],
    }


def build_report(primary: Path, secondary: Path, detector: str, timeout: int) -> dict[str, Any]:
    process_a = run_fresh_process([primary, primary, secondary], detector, timeout)
    process_b = run_fresh_process([primary], detector, timeout)

    scaling_dir = ROOT / "eval" / "data"
    scaling_paths = [
        scaling_dir / f"runtime_gate_{duration}s.wav" for duration in (3, 10, 30)
    ]
    try:
        for path, duration in zip(scaling_paths, (3, 10, 30)):
            repeated_fixture(primary, path, duration)
        scaling_process = run_fresh_process([primary, *scaling_paths], detector, timeout)
        scaling_runs = scaling_process["runs"][1:]
    finally:
        for path in scaling_paths:
            path.unlink(missing_ok=True)

    first = process_a["runs"][0]
    warm_repeat = process_a["runs"][1]
    fresh_first = process_b["runs"][0]
    equivalence = equivalent_to_legacy(first)
    repeat_equivalence = {
        "note_event_hash_equal": first["trace"]["basic_pitch"]["note_event_hash_sha256"]
        == warm_repeat["trace"]["basic_pitch"]["note_event_hash_sha256"],
        "events_equal": first["events"] == warm_repeat["events"],
    }

    targets = {
        "label": "TARGET",
        "scope": "local research preview on this measured CPU/ONNX architecture",
        "cold_3s_total_sec_max": 15.0,
        "warm_3s_total_sec_max": 5.0,
        "warm_10s_total_sec_max": 10.0,
        "warm_30s_total_sec_max": 25.0,
    }
    achieved = {
        "label": "CURRENTLY_ACHIEVED",
        "cold_process_a_3s_sec": first["wall_sec"],
        "warm_repeat_3s_sec": warm_repeat["wall_sec"],
        "cold_process_b_3s_sec": fresh_first["wall_sec"],
        "warm_scaling_sec": {
            str(round(run["fixture"]["duration_sec"])): run["wall_sec"] for run in scaling_runs
        },
    }

    return {
        "schema_version": "single-wav-analysis-performance-gate-v1",
        "command": "python eval/benchmark_audio_path.py",
        "evidence_level": "L0/L1/L2 runtime; no accuracy claim",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "packages": {
                name: package_version(name)
                for name in ("basic-pitch", "onnxruntime", "librosa", "numba", "soundfile", "pretty-midi")
            },
            "tensorflow": package_version("tensorflow"),
        },
        "fixtures": {
            "primary": fixture_metadata(primary),
            "primary_provenance": "repository test fixture; legal provenance not yet audited",
            "secondary": fixture_metadata(secondary),
            "scaling": "3/10/30-second runtime-only repetitions of the primary fixture",
        },
        "legacy_observation": LEGACY_OBSERVATION,
        "process_a": process_a,
        "process_b": process_b,
        "duration_scaling": scaling_runs,
        "output_equivalence": equivalence,
        "warm_repeat_equivalence": repeat_equivalence,
        "targets": targets,
        "achieved": achieved,
        "decision_gate": {
            "outcome": "F. MIXED",
            "contributors": [
                "G. ENVIRONMENT_SPECIFIC: Numba cache validation under user site-packages was pathological",
                "C. PREPROCESSING_OVERHEAD: audioread backend discovery added about 15 seconds before SoundFile WAV decoding",
                "A. COLD_START_ONLY: imports and detector initialization are paid once and warm calls reuse model state",
            ],
            "model_reuse_verified": warm_repeat["trace"]["basic_pitch"]["model_reused"],
            "real_wav_completed": bool(first["events"]),
            "all_equivalence_checks_pass": all(equivalence.values()) and all(repeat_equivalence.values()),
            "default_detector_changed": False,
        },
        "evidence_loss_boundary": {
            "basic_pitch_returns": ["model_output", "PrettyMIDI", "note_events with amplitude and optional pitch bends"],
            "currently_preserved_downstream": ["temporary MIDI notes and timing"],
            "currently_discarded": ["model note/onset/contour arrays", "note-event amplitude", "pitch-bend evidence"],
            "measured_midi_round_trip": "see midi_serialization and midi_parsing stage timings",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    achieved = report["achieved"]
    first = report["process_a"]["runs"][0]
    warm = report["process_a"]["runs"][1]
    stages = first["trace"]["stages_sec"]
    bp = first["trace"]["basic_pitch"]
    lines = [
        "# Single-WAV Analysis Performance Gate v1",
        "",
        "Runtime evidence only. No detector-accuracy claim is made.",
        "",
        "## Cold and warm",
        "",
        "| Measurement | Seconds |",
        "| --- | ---: |",
        f"| Process A first 3s WAV | {achieved['cold_process_a_3s_sec']:.3f} |",
        f"| Process A repeated 3s WAV | {achieved['warm_repeat_3s_sec']:.3f} |",
        f"| Process B first 3s WAV | {achieved['cold_process_b_3s_sec']:.3f} |",
        "",
        "## First-run stages",
        "",
        "| Stage | Seconds |",
        "| --- | ---: |",
    ]
    for name, value in {**bp["timings_sec"], **stages}.items():
        lines.append(f"| {name} | {value:.6f} |")
    lines.extend([
        "",
        "## Duration scaling",
        "",
        "| Duration | Warm seconds | Model windows |",
        "| ---: | ---: | ---: |",
    ])
    for run in report["duration_scaling"]:
        lines.append(
            f"| {run['fixture']['duration_sec']:.1f} | {run['wall_sec']:.3f} | "
            f"{run['trace']['basic_pitch']['model_windows']} |"
        )
    lines.extend([
        "",
        "## Equivalence",
        "",
        f"`{json.dumps(report['output_equivalence'], sort_keys=True)}`",
        "",
        "## Decision",
        "",
        f"**{report['decision_gate']['outcome']}**",
        "",
    ])
    lines.extend(f"- {item}" for item in report["decision_gate"]["contributors"])
    lines.extend([
        "",
        "The default detector remains unchanged. `rule_jaccard` remains opt-in.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--wav", action="append", type=Path)
    parser.add_argument("--detector", default="rule_jaccard")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--json", type=Path, default=JSON_REPORT)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_REPORT)
    args = parser.parse_args()

    if args.worker:
        return worker(args.wav or [DEFAULT_WAV], args.detector)

    primary = (args.wav or [DEFAULT_WAV])[0].resolve()
    report = build_report(primary, SECOND_WAV.resolve(), args.detector, args.timeout)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["achieved"], indent=2, sort_keys=True))
    print(f"decision: {report['decision_gate']['outcome']}")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
