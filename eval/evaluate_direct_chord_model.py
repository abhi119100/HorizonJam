"""Phase 4 isolated LV-Chordia feasibility and complementarity gate."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.direct_chord_adapter import DirectChordAdapterError, run_lv_chordia


JSON_REPORT = ROOT / "eval" / "direct_chord_model_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "direct_chord_model_report.md"
SAMPLE_RATE = 22050
PYTHON = ROOT / ".venv" / "lvchordia" / "Scripts" / "python.exe"


FIXTURES = {
    "c_major": ("C", [60, 64, 67]),
    "a_minor": ("Am", [57, 60, 64]),
    "g_dominant7": ("G7", [55, 59, 62, 65]),
    "c_major7": ("Cmaj7", [60, 64, 67, 71]),
    "d_minor7": ("Dm7", [62, 65, 69, 72]),
    "d_sus2": ("Dsus2", [62, 64, 69]),
    "a_sus4": ("Asus4", [57, 62, 64]),
    "b_diminished": ("Bdim", [59, 62, 65]),
}


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


def _prediction(events) -> str:
    if not events:
        return "N"
    winner = max(events, key=lambda event: (event.end - event.start, -event.start))
    return winner.label


def _run_case(name: str, path: Path, expected: str | None) -> dict[str, Any]:
    try:
        result = run_lv_chordia(
            str(path), timeout_sec=300, python_executable=str(PYTHON)
        )
        prediction = _prediction(result["events"])
        return {
            "name": name,
            "expected": expected,
            "prediction": prediction,
            "correct": prediction == expected if expected is not None else None,
            "events": [event.to_dict() for event in result["events"]],
            "warnings": result["warnings"],
            "runtime": result["runtime"],
            "metadata": result["metadata"],
            "error": None,
        }
    except DirectChordAdapterError as exc:
        return {
            "name": name,
            "expected": expected,
            "prediction": None,
            "correct": False if expected is not None else None,
            "events": [],
            "warnings": [],
            "runtime": {},
            "metadata": {},
            "error": str(exc),
        }


def _checkpoint_register() -> list[dict[str, Any]]:
    root = ROOT / ".venv" / "lvchordia" / "share" / "lv-chordia" / "cache_data"
    return [
        {
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "license_status": "bundled under package MIT claim; checkpoint-specific terms not independently located",
        }
        for path in sorted(root.glob("*.sdict"))
    ]


def _freeze() -> list[str]:
    completed = subprocess.run(
        [str(PYTHON), "-m", "pip", "freeze"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        shell=False,
    )
    return sorted(line for line in completed.stdout.splitlines() if line.strip())


def build_report() -> dict[str, Any]:
    phase3 = json.loads((ROOT / "eval" / "dsp_chroma_report.json").read_text(encoding="utf-8"))
    phase3_cases = {case["name"]: case for case in phase3["cases"]}
    generated: list[Path] = []
    cases = []
    runtime_scaling = []
    try:
        for name, (expected, pitches) in FIXTURES.items():
            path = ROOT / "eval" / "data" / f"phase4_{name}.wav"
            generated.append(path)
            _render(path, 2.0, pitches)
            result = _run_case(name, path, expected)
            prior = phase3_cases[name]
            result["paired_sources"] = {
                "rule_jaccard": prior["rule_jaccard_prediction"],
                "dsp": prior["dsp_prediction"],
            }
            if result["correct"]:
                if prior["dsp_correct"] and prior["rule_jaccard_correct"]:
                    category = "all_agree_correct"
                elif prior["dsp_correct"] or prior["rule_jaccard_correct"]:
                    category = "two_correct_one_differs"
                else:
                    category = "lv_chordia_only_correct"
            elif prior["dsp_correct"] and prior["rule_jaccard_correct"]:
                category = "two_correct_lv_chordia_differs"
            elif prior["dsp_correct"] or prior["rule_jaccard_correct"]:
                category = "one_prior_correct"
            else:
                category = "all_fail"
            result["comparison_category"] = category
            cases.append(result)

        source = ROOT / "tests" / "audio" / "pop.wav"
        audio, sample_rate = sf.read(source, dtype="float32", always_2d=True)
        for duration in (3, 10, 30):
            frames = int(round(duration * sample_rate))
            repeats = int(np.ceil(frames / len(audio)))
            repeated = np.tile(audio, (repeats, 1))[:frames]
            path = ROOT / "eval" / "data" / f"phase4_runtime_{duration}s.wav"
            generated.append(path)
            sf.write(path, repeated, sample_rate, subtype="PCM_16")
            item = _run_case(f"runtime_{duration}s", path, None)
            runtime_scaling.append({
                "duration_sec": duration,
                "prediction": item["prediction"],
                "event_count": len(item["events"]),
                "runtime": item["runtime"],
                "error": item["error"],
            })
    finally:
        for path in generated:
            path.unlink(missing_ok=True)

    exact = sum(case["correct"] is True for case in cases)
    unique = sum(
        case["comparison_category"] == "lv_chordia_only_correct" for case in cases
    )
    completed_cases = sum(case["error"] is None for case in cases)
    if completed_cases == 0:
        decision = "E DIRECT_MODEL_UNUSABLE"
    elif exact >= 6:
        decision = "A DIRECT_MODEL_STRONG"
    elif unique > 0 or exact >= 3:
        decision = "B DIRECT_MODEL_COMPLEMENTARY"
    elif any(
        item["runtime"].get("adapter_wall_sec", 0) > 60
        for item in runtime_scaling if item["error"] is None
    ):
        decision = "D DIRECT_MODEL_TOO_EXPENSIVE"
    else:
        decision = "C DIRECT_MODEL_REDUNDANT"

    checkpoints = _checkpoint_register()
    return {
        "schema_version": "direct-chord-model-gate-v1",
        "command": "python eval/evaluate_direct_chord_model.py",
        "evidence_level": "L2 deterministic synthetic diagnostic and L6 runtime; RESEARCH_ONLY",
        "environment": {
            "host_python": sys.version,
            "platform": platform.platform(),
            "isolated_python": str(PYTHON.relative_to(ROOT)),
            "dependencies": _freeze(),
        },
        "artifact_audit": {
            "package": "lv-chordia==1.1.0",
            "source_commit": "990f00177029f043be24478f867005a52c6c304e",
            "source_tag": "v1.1.0",
            "wheel_sha256": "292241f03e1029e6739ee7a2a91fbe348c25c97b8b3641db76cbef9f9dee0cb0",
            "code_license": "MIT (package declaration)",
            "checkpoint_provenance": "package states original ISMIR 2019 ensemble weights; five files bundled in wheel",
            "checkpoint_license": "UNRESOLVED_SEPARATELY_FROM_PACKAGE",
            "distribution_status": "RESEARCH_ONLY; do not redistribute environment or checkpoints from HorizonJam",
            "checkpoint_total_bytes": sum(item["bytes"] for item in checkpoints),
            "checkpoints": checkpoints,
            "network_surface": "upstream supports URL downloads; HorizonJam runner rejects URLs and disables urllib",
            "checkpoint_loading_risk": "legacy torch.load on trusted locally hashed package artifacts",
        },
        "adapter": {
            "protocol": "local subprocess, marker-prefixed JSON, shell=False",
            "timeout_sec": 300,
            "output_limit_chars": 2_000_000,
            "chord_dictionary": "submission",
            "score_semantics": "no score exposed; HorizonJam confidence remains null",
        },
        "cases": cases,
        "runtime_scaling": runtime_scaling,
        "comparison": {
            "case_count": len(cases),
            "completed_cases": completed_cases,
            "lv_chordia_exact": exact,
            "lv_chordia_only_correct": unique,
            "categories": {
                category: sum(case["comparison_category"] == category for case in cases)
                for category in sorted({case["comparison_category"] for case in cases})
            },
        },
        "decision_gate": {
            "outcome": decision,
            "eligible_fusion_weight": 0.0 if decision in {
                "C DIRECT_MODEL_REDUNDANT",
                "D DIRECT_MODEL_TOO_EXPENSIVE",
                "E DIRECT_MODEL_UNUSABLE",
            } else None,
            "default_detector_changed": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Direct Chord Model Gate",
        "",
        f"Decision: **{report['decision_gate']['outcome']}**.",
        "",
        "LV-Chordia execution is RESEARCH_ONLY. Checkpoint-specific rights remain unresolved independently of the package MIT declaration.",
        "",
        "## Controlled cases",
        "",
        "| Case | Expected | LV-Chordia | Jaccard | DSP | Category | Wall |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for case in report["cases"]:
        wall = case["runtime"].get("adapter_wall_sec")
        wall_text = f"{wall:.2f}s" if wall is not None else "failed"
        lines.append(
            f"| {case['name']} | {case['expected']} | {case['prediction']} | "
            f"{case['paired_sources']['rule_jaccard']} | {case['paired_sources']['dsp']} | "
            f"{case['comparison_category']} | {wall_text} |"
        )
    lines.extend([
        "",
        "## Runtime scaling",
        "",
        "| Audio | Events | Prediction | Adapter wall | Error |",
        "| ---: | ---: | --- | ---: | --- |",
    ])
    for item in report["runtime_scaling"]:
        wall = item["runtime"].get("adapter_wall_sec")
        wall_text = f"{wall:.2f}s" if wall is not None else "n/a"
        lines.append(
            f"| {item['duration_sec']}s | {item['event_count']} | {item['prediction']} | "
            f"{wall_text} | {item['error'] or ''} |"
        )
    lines.extend([
        "",
        "The external model is never imported by HorizonJam's active environment. URL input is rejected, network helpers are disabled in the runner, and no model score is mapped to HorizonJam confidence.",
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
