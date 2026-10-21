"""Phase 5 paired evidence-fusion gate using the frozen Phase 3 cases."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_fusion import DEFAULT_SOURCE_WEIGHTS, fuse_ranked_sources


SOURCE_REPORT = ROOT / "eval" / "dsp_chroma_report.json"
JSON_REPORT = ROOT / "eval" / "fusion_v1_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "fusion_v1_report.md"


def build_report() -> dict[str, Any]:
    source_report = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    for source_case in source_report["cases"]:
        ranked_sources = {
            "rule_jaccard": [{
                "label": source_case["rule_jaccard_prediction"],
                "normalized_support": 1.0,
            }],
            "librosa_chroma": [
                {
                    "label": candidate["label"],
                    "normalized_support": candidate["normalized_support"],
                }
                for candidate in source_case["dsp_top3"]
            ],
        }
        result = fuse_ranked_sources(0.0, 2.0, ranked_sources)
        winner = result.winner
        prediction = winner.label if winner else "N"
        cases.append({
            "name": source_case["name"],
            "expected": source_case["expected"],
            "rule_jaccard_prediction": source_case["rule_jaccard_prediction"],
            "dsp_prediction": source_case["dsp_prediction"],
            "fusion_prediction": prediction,
            "fusion_correct": prediction == source_case["expected"],
            "agreement": result.agreement,
            "candidate_margin": result.candidate_margin,
            "source_disagreement": result.source_disagreement,
            "candidates": [candidate.to_dict() for candidate in result.candidates[:3]],
        })

    fusion_exact = sum(case["fusion_correct"] for case in cases)
    jaccard_exact = source_report["comparison"]["rule_jaccard_exact"]
    dsp_exact = source_report["comparison"]["dsp_exact"]
    strongest_exact = max(jaccard_exact, dsp_exact)
    changed = [
        case["name"] for case in cases
        if case["fusion_prediction"] != case["rule_jaccard_prediction"]
    ]
    if fusion_exact >= strongest_exact + 2:
        outcome = "A FUSION_CLEAR_WIN"
    elif fusion_exact > strongest_exact:
        outcome = "B FUSION_SMALL_WIN"
    elif fusion_exact == strongest_exact and changed:
        outcome = "C FUSION_TRADEOFF"
    elif fusion_exact == strongest_exact:
        outcome = "D FUSION_NO_GAIN"
    else:
        outcome = "E FUSION_HARMFUL"
    return {
        "schema_version": "evidence-fusion-v1-gate-v1",
        "command": "python eval/evaluate_fusion_v1.py",
        "evidence_level": "L2 deterministic synthetic paired replay; no real-performance accuracy claim",
        "source_cases": "eval/dsp_chroma_report.json cases and actual recorded top-3 rankings",
        "label_use_policy": "expected labels score predictions only; they do not set weights, supports, or ties",
        "configuration": {
            "source_weights": DEFAULT_SOURCE_WEIGHTS,
            "formula": "sum(source weight * normalized support) / sum(active source weights)",
            "candidate_merge": "canonical root, quality, bass, and pitch-class set",
            "tie_break": "descending score then canonical label",
            "direct_model_policy": "lv_chordia retained in configuration at weight 0.0 after Phase 4 gate",
            "score_semantics": "internal weighted normalized support; not probability or calibrated confidence",
        },
        "cases": cases,
        "comparison": {
            "case_count": len(cases),
            "rule_jaccard_exact": jaccard_exact,
            "dsp_exact": dsp_exact,
            "strongest_individual_exact": strongest_exact,
            "fusion_exact": fusion_exact,
            "fusion_changed_from_jaccard": changed,
            "fusion_unique_correct": sum(
                case["fusion_correct"]
                and case["rule_jaccard_prediction"] != case["expected"]
                and case["dsp_prediction"] != case["expected"]
                for case in cases
            ),
        },
        "decision_gate": {
            "outcome": outcome,
            "activation": "not promoted" if outcome.startswith(("D", "E")) else "experimental only",
            "phase_6_allowed": outcome.startswith(("A", "B", "C")),
            "default_detector_changed": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Evidence Fusion v1 Gate",
        "",
        f"Decision: **{report['decision_gate']['outcome']}**.",
        "",
        "Paired synthetic replay only. Expected labels were used only after ranking for scoring.",
        "",
        "## Controlled cases",
        "",
        "| Case | Expected | Jaccard | DSP | Fusion | Agreement |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            f"| {case['name']} | {case['expected']} | {case['rule_jaccard_prediction']} | "
            f"{case['dsp_prediction']} | {case['fusion_prediction']} | {case['agreement']} |"
        )
    comparison = report["comparison"]
    lines.extend([
        "",
        "## Result",
        "",
        f"Jaccard: {comparison['rule_jaccard_exact']}/{comparison['case_count']}; "
        f"DSP: {comparison['dsp_exact']}/{comparison['case_count']}; "
        f"fusion: {comparison['fusion_exact']}/{comparison['case_count']}.",
        "",
        "Fusion uses equal active weights for Jaccard and Librosa chroma. LV-Chordia has weight 0.0 because its Phase 4 gate found no unique correct case. Scores are internal weighted normalized support, not probabilities or calibrated confidence.",
        "",
        "The fusion activation path stops when this report records no gain; Phase 6 must not be built on this candidate stream.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "decision": report["decision_gate"],
        "comparison": report["comparison"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
