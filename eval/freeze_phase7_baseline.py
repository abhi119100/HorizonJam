"""Freeze the code/configuration evidence visible before Phase 7 evaluation."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "eval" / "phase7_baseline_freeze.json"
REPORTS = (
    "eval/audio_path_benchmark.json", "eval/jaccard_detector_path_report.json",
    "eval/basicpitch_direct_evidence_report.json", "eval/dsp_chroma_report.json",
    "eval/direct_chord_model_report.json", "eval/fusion_v1_report.json",
    "eval/multi_evidence_phase2_to_6_report.json",
)
SOURCES = (
    "detection.py", "src/basic_pitch_runtime.py", "src/chord_detector.py",
    "src/dsp_chroma.py", "src/harmonic_evidence.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
        shell=False,
    )
    return result.stdout.strip()


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from detection import DEFAULT_DETECTOR, selected_detector
    from src.dsp_chroma import DEFAULT_CONFIG

    diff = subprocess.run(
        ["git", "diff", "--binary"], cwd=ROOT, capture_output=True, check=True,
        shell=False,
    ).stdout
    payload = {
        "schema_version": "phase7-baseline-freeze-v1",
        "git": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("branch", "--show-current"),
            "worktree_status": _git("status", "--short").splitlines(),
            "tracked_diff_sha256": hashlib.sha256(diff).hexdigest(),
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {name: _version(name) for name in (
                "basic-pitch", "librosa", "mir_eval", "numpy", "pretty-midi", "soundfile",
            )},
        },
        "detectors": {
            "environment_value": os.getenv("HORIZONJAM_DETECTOR"),
            "default": DEFAULT_DETECTOR,
            "resolved": selected_detector(),
            "hybrid": {"use_viterbi": True, "classifier_mode": "simple", "basic_pitch_midi_compatibility": True},
            "rule_jaccard": {"use_viterbi": True, "classifier_mode": "advanced_jaccard", "basic_pitch_midi_compatibility": True},
            "dsp": DEFAULT_CONFIG,
        },
        "source_hashes_sha256": {path: _sha256(ROOT / path) for path in SOURCES},
        "report_hashes_sha256": {
            path: _sha256(ROOT / path) for path in REPORTS if (ROOT / path).is_file()
        },
        "freeze_policy": {
            "held_out_labels_used_for_tuning": False,
            "detector_tuning_after_freeze": False,
            "fusion_active": False,
            "lv_chordia_in_primary_evaluation": False,
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT.relative_to(ROOT)),
        "commit": payload["git"]["commit"],
        "resolved_detector": payload["detectors"]["resolved"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
