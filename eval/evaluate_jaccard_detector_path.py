"""Compare baseline and Jaccard after the frozen transcription boundary.

This benchmark deliberately injects each fixture's paired MIDI at
`detection._wav_to_midi`, then exercises the remaining production detector
path through `detection.run_detection()` and mir_eval. Results are L2
post-transcription evidence, not audio-recognition accuracy.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.evaluate_chords import MANIFEST, score_one


EVAL_DIR = Path(__file__).parent
JSON_REPORT = EVAL_DIR / "jaccard_detector_path_report.json"
MARKDOWN_REPORT = EVAL_DIR / "jaccard_detector_path_report.md"
DETECTORS = ("hybrid", "rule_jaccard")
METRICS = ("root", "majmin", "sevenths", "mirex")
MAX_ALLOWED_REGRESSION = 0.02


def injected_midi(source: Path):
    def copy_fixture(_wav_path: str, _runtime_trace=None) -> str:
        handle, destination = tempfile.mkstemp(suffix=".mid", prefix="hj_oracle_")
        os.close(handle)
        Path(destination).unlink(missing_ok=True)
        shutil.copyfile(source, destination)
        return destination

    return copy_fixture


def aggregate(rows: dict[str, dict]) -> dict:
    completed = [row for row in rows.values() if "scores" in row]
    return {
        **{
            metric: float(np.mean([row["scores"][metric] for row in completed]))
            if completed else None
            for metric in METRICS
        },
        "files_ok": len(completed),
        "files_failed": len(rows) - len(completed),
        "events_total": sum(row.get("events_count", 0) for row in completed),
        "warnings_total": sum(row.get("warnings_count", 0) for row in completed),
    }


def decide(summary: dict, song_count: int) -> dict:
    baseline = summary["hybrid"]
    candidate = summary["rule_jaccard"]
    deltas = {
        metric: candidate[metric] - baseline[metric]
        for metric in METRICS
    }
    complete = all(
        summary[name]["files_ok"] == song_count and summary[name]["events_total"] > 0
        for name in DETECTORS
    )
    bounded = all(deltas[metric] >= -MAX_ALLOWED_REGRESSION for metric in ("root", "majmin", "mirex"))
    seventh_gain = deltas["sevenths"] > 0

    if complete and bounded and seventh_gain:
        outcome = "A. ADVANCE_TO_REAL_AUDIO"
        reason = "Jaccard improves seventh scoring without a material post-transcription regression."
    elif complete:
        outcome = "B. MIXED_POST_TRANSCRIPTION_RESULT"
        reason = "The candidate completed but failed at least one frozen product-path criterion."
    else:
        outcome = "C. INCOMPLETE"
        reason = "At least one detector failed to complete the frozen fixture set."
    return {
        "outcome": outcome,
        "reason": reason,
        "metric_deltas": deltas,
        "criteria": {
            "all_files_complete": complete,
            "sevenths_improves": seventh_gain,
            "root_majmin_mirex_regression_at_most": MAX_ALLOWED_REGRESSION,
            "bounded_regression_pass": bounded,
            "activation_allowed": False,
        },
    }


def build_report() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    songs = manifest["songs"]
    per_song = {name: {} for name in DETECTORS}

    for index, song in enumerate(songs, 1):
        print(f"[{index:2d}/{len(songs)}] {song['name']}", flush=True)
        midi_path = Path(song["midi"])
        for detector in DETECTORS:
            with patch("detection._wav_to_midi", side_effect=injected_midi(midi_path)):
                per_song[detector][song["name"]] = score_one(
                    song["wav"], song["labels"], detector
                )

    summary = {name: aggregate(rows) for name, rows in per_song.items()}
    confusions = {}
    for detector, rows in per_song.items():
        counter = Counter()
        for row in rows.values():
            counter.update(dict(row.get("confusions", [])))
        confusions[detector] = counter.most_common(10)

    return {
        "schema_version": "jaccard-detector-path-v1",
        "command": "python eval/evaluate_jaccard_detector_path.py",
        "evidence_level": "L2 harmony / post-transcription production detector path",
        "dataset": {
            "count": len(songs),
            "source": "eval/synth_manifest.json",
            "transcription": "paired synthetic MIDI injected at detection._wav_to_midi",
        },
        "frozen_controls": [
            "MIDI fixtures and Harte labels",
            "segmentation and windowing",
            "bass and E-major preliminary key prior",
            "candidate templates and non-match score terms",
            "event grouping, smoothing, hybrid adapter, and normalization",
        ],
        "changed_variable": "simple classifier versus advanced scorer with Jaccard pitch-set match",
        "summary": summary,
        "decision_gate": decide(summary, len(songs)),
        "top_confusions": confusions,
        "per_song": per_song,
        "limitations": [
            "BasicPitch is bypassed, so this does not measure L0/L1 or audio-recognition accuracy.",
            "Synthetic MIDI and sine fixtures do not represent real musicians.",
            "Diminished templates remain absent; confidence remains uncalibrated.",
            "A successful gate advances the candidate to real-audio validation only.",
        ],
    }


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def render_markdown(report: dict) -> str:
    baseline = report["summary"]["hybrid"]
    candidate = report["summary"]["rule_jaccard"]
    decision = report["decision_gate"]
    lines = [
        "# Jaccard Post-Transcription Detector-Path Benchmark v1",
        "",
        "This is L2 post-transcription evidence. It is not an audio or real-musician accuracy result.",
        "",
        "| Detector | Root | MajMin | Sevenths | MIREX | Files | Warnings |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, values in (("hybrid", baseline), ("rule_jaccard", candidate)):
        lines.append(
            f"| {name} | {pct(values['root'])} | {pct(values['majmin'])} | "
            f"{pct(values['sevenths'])} | {pct(values['mirex'])} | "
            f"{values['files_ok']}/{report['dataset']['count']} | {values['warnings_total']} |"
        )
    lines.extend([
        "",
        "## Decision gate",
        "",
        f"**{decision['outcome']}**. {decision['reason']}",
        "",
        f"Metric deltas: `{json.dumps(decision['metric_deltas'], sort_keys=True)}`",
        "",
        "Default activation remains prohibited until real-audio evidence exists.",
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"decision: {report['decision_gate']['outcome']}")
    print(f"wrote {JSON_REPORT}")
    print(f"wrote {MARKDOWN_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
