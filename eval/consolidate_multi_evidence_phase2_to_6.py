"""Aggregate completed Phase 2-6 gate reports without inventing missing phases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JSON_REPORT = ROOT / "eval" / "multi_evidence_phase2_to_6_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "multi_evidence_phase2_to_6_report.md"
REPORTS = {
    "phase_2": ROOT / "eval" / "basicpitch_direct_evidence_report.json",
    "phase_3": ROOT / "eval" / "dsp_chroma_report.json",
    "phase_4": ROOT / "eval" / "direct_chord_model_report.json",
    "phase_5": ROOT / "eval" / "fusion_v1_report.json",
}


def _load(path: Path) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def build_report() -> dict[str, Any]:
    loaded = {phase: _load(path) for phase, path in REPORTS.items()}
    return {
        "schema_version": "multi-evidence-phase2-to-6-partial-v1",
        "overall_result": "STOPPED_AFTER_PHASE_5",
        "final_decision_gate": "E FUSION_NOT_JUSTIFIED",
        "phases": {
            phase: {
                "status": "PASS" if phase != "phase_5" else "STOP_GATE",
                "decision": report["decision_gate"]["outcome"],
                "report": str(REPORTS[phase].relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest,
            }
            for phase, (report, digest) in loaded.items()
        } | {
            "phase_6": {
                "status": "NOT_RUN",
                "decision": None,
                "report": None,
                "reason": "Phase 5 D FUSION_NO_GAIN prohibits the temporal activation path",
            }
        },
        "comparison": {
            "controlled_case_count": loaded["phase_5"][0]["comparison"]["case_count"],
            "rule_jaccard_exact": loaded["phase_5"][0]["comparison"]["rule_jaccard_exact"],
            "dsp_exact": loaded["phase_5"][0]["comparison"]["dsp_exact"],
            "lv_chordia_exact": loaded["phase_4"][0]["comparison"]["lv_chordia_exact"],
            "fusion_exact": loaded["phase_5"][0]["comparison"]["fusion_exact"],
            "multi_evidence": None,
            "scope": "deterministic synthetic diagnostic; not real-performance accuracy",
        },
        "behavior": {
            "default_detector_changed": False,
            "multi_evidence_detector_created": False,
            "phase_6_temporal_resolver_created": False,
            "production_contracts_changed": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Multi-Evidence Phases 2-6 Consolidated Gate",
        "",
        "Overall result: **STOPPED_AFTER_PHASE_5**.",
        "",
        "| Phase | Status | Decision | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for phase, item in report["phases"].items():
        evidence = f"[{item['report']}]({Path(item['report']).name})" if item["report"] else item["reason"]
        lines.append(
            f"| {phase.replace('_', ' ').title()} | {item['status']} | "
            f"{item['decision'] or 'not available'} | {evidence} |"
        )
    comparison = report["comparison"]
    lines.extend([
        "",
        "## Paired controlled comparison",
        "",
        "| Source | Exact cases |",
        "| --- | ---: |",
        f"| rule_jaccard | {comparison['rule_jaccard_exact']}/{comparison['controlled_case_count']} |",
        f"| Librosa DSP | {comparison['dsp_exact']}/{comparison['controlled_case_count']} |",
        f"| LV-Chordia | {comparison['lv_chordia_exact']}/{comparison['controlled_case_count']} |",
        f"| fusion v1 | {comparison['fusion_exact']}/{comparison['controlled_case_count']} |",
        "| multi_evidence | not implemented |",
        "",
        "These are deterministic synthetic diagnostics, not real-performance accuracy. Fusion offered no gain over either strongest individual source, so the hard gate stopped Phase 6. Default product behavior remains unchanged.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "overall_result": report["overall_result"],
        "final_decision_gate": report["final_decision_gate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
