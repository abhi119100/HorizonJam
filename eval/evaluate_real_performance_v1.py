"""Generate the Phase 7 real-performance gate without fabricating data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.real_performance_pack import validate_manifest

MANIFEST = ROOT / "eval" / "real_performance_demo_pack" / "manifest.json"
JSON_REPORT = ROOT / "eval" / "real_performance_v1_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "real_performance_v1_report.md"


def build_report() -> dict:
    validation = validate_manifest(MANIFEST)
    if validation["ready"]:
        raise RuntimeError("Pack is ready; review and freeze it before enabling detector execution.")
    return {
        "schema_version": "real-performance-v1-gate-v1",
        "command": "python eval/evaluate_real_performance_v1.py",
        "baseline_freeze": "eval/phase7_baseline_freeze.json",
        "dataset": {
            "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "description": "Owned/licensed real-performance pack; collection not yet populated",
            "case_count": validation["case_count"], "counts": validation["counts"],
            "coverage": validation["coverage"], "coverage_gaps": validation["coverage_gaps"],
            "independent_annotation_cases": validation["independent_annotation_cases"],
            "provenance_status": "NO_APPROVED_AUDIO", "annotation_status": "NO_ANNOTATIONS",
            "split_status": "NOT_FROZEN",
        },
        "validation_errors": validation["validation_errors"],
        "readiness_reasons": validation["readiness_reasons"],
        "detector_execution": {
            "hybrid": "NOT_RUN_NO_APPROVED_CORPUS", "rule_jaccard": "NOT_RUN_NO_APPROVED_CORPUS",
            "basic_pitch_direct_evidence": "NOT_CAPTURED_NO_APPROVED_CORPUS",
            "dsp_chroma": "NOT_CAPTURED_NO_APPROVED_CORPUS",
            "lv_chordia": "EXCLUDED_BY_PHASE_7_POLICY",
        },
        "metrics": None, "slice_metrics": None, "error_taxonomy": None,
        "source_disagreement": None, "latency": None,
        "limitations": [
            "No owned, consented, or clearly licensed real-performance cases are present.",
            "Repository runtime fixtures have explicitly unaudited legal/performance provenance.",
            "No real-audio accuracy, complementarity, transcription, segmentation, or latency conclusion is available.",
        ],
        "decision_gate": {
            "outcome": "F DATASET_TOO_SMALL_OR_AMBIGUOUS",
            "basis": "zero approved cases; minimum useful target is 20",
            "architecture_decision_allowed": False,
        },
    }


def render_markdown(report: dict) -> str:
    dataset = report["dataset"]
    lines = [
        "# Real Performance Evaluation Pack v1", "",
        f"Decision: **{report['decision_gate']['outcome']}**.", "", "## Dataset status", "",
        f"Approved cases: **{dataset['case_count']}**. Minimum required: **20**.",
        "Provenance: `NO_APPROVED_AUDIO`. Annotations: `NO_ANNOTATIONS`. Held-out split: `NOT_FROZEN`.", "",
        "Repository WAV fixtures are excluded because their legal and performance provenance is unaudited. Synthetic audio is not real-performance evidence.", "",
        "## Evaluation status", "",
        "Hybrid, rule_jaccard, BasicPitch direct evidence, and DSP/chroma were not run. Metrics, slices, source disagreement, L1/L2 attribution, and real-audio latency are unavailable rather than zero.", "",
        "## Readiness blockers", "",
    ]
    lines.extend(f"- {reason}" for reason in report["readiness_reasons"])
    lines.extend(["", "The collection contract is `eval/real_performance_demo_pack/manifest.schema.json`. Run detectors only after provenance approval, split assignment, annotation, and held-out-label freeze.", ""])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision_gate"]["outcome"], "case_count": report["dataset"]["case_count"], "metrics": report["metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
