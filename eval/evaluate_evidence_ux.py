"""Deterministic Phase 7 EvidenceSummary and tutor-context comparison."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tutor_evidence import (
    assemble_tutor_context,
    build_performance_evidence,
    select_retrieved_evidence,
    verify_and_repair_response,
)

JSON_REPORT = ROOT / "eval" / "evidence_ux_v1_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "evidence_ux_v1_report.md"


def _result(summary: dict | None) -> dict:
    result = {
        "analysis_summary": {"detected_key": "D Major", "chord_progression": "D7"},
        "chord_events": [{
            "start": 0.0, "end": 2.0, "chord": "D7", "confidence": 0.9,
            "source_detector": "rule_jaccard",
        }],
        "detector_used": "rule_jaccard",
        "warnings": [],
    }
    if summary:
        result["evidence_summaries"] = [summary]
    return result


def _summary(strength: str, agreement: str, candidate: str | None, explanation: str) -> dict:
    return {
        "start": 0.0, "end": 2.0, "chord": "D7", "strength": strength,
        "agreement": agreement, "observed_notes": ["C", "D", "F#", "A"],
        "harmonic_candidate": candidate,
        "supporting_sources": ["rule_jaccard", "basic_pitch"] + (["librosa_chroma"] if candidate else []),
        "warnings": [], "short_explanation": explanation,
    }


def build_report() -> dict:
    cases = [
        ("strong", _summary("STRONG_AGREEMENT", "SYMBOLIC_DSP_EXACT", "D7", "The detected notes and harmonic spectrum both support D7."), False),
        ("mixed", _summary("MIXED_EVIDENCE", "SYMBOLIC_DSP_DISAGREE", "G", "Detected notes favor D7, while the harmonic spectrum favors G."), True),
        ("limited", _summary("LIMITED_EVIDENCE", "SYMBOLIC_ONLY", None, "HorizonJam detected D7, but independent harmonic evidence was unavailable."), True),
    ]
    results = []
    for name, summary, uncertainty_expected in cases:
        baseline_performance = build_performance_evidence(_result(None))
        summary_performance = build_performance_evidence(_result(summary))
        retrieval = select_retrieved_evidence({"results": []}, "D7")
        baseline = assemble_tutor_context(baseline_performance, retrieval, "What chord is this?")
        enriched = assemble_tutor_context(summary_performance, retrieval, "What chord is this?")
        assertion = "You are playing D7."
        before = verify_and_repair_response(assertion, baseline)
        after = verify_and_repair_response(assertion, enriched)
        prompt = enriched["messages"][1]["content"]
        results.append({
            "case": name,
            "strength": summary["strength"],
            "uncertainty_expected": uncertainty_expected,
            "uncertainty_observed": enriched["assessment"]["requires_uncertainty_language"],
            "baseline_repairs": before["repairs"],
            "summary_repairs": after["repairs"],
            "summary_propagated": summary["strength"] in prompt,
            "raw_evidence_absent": all(token not in prompt for token in ('"values"', 'model_output', 'normalized_support')),
            "prompt_chars_baseline": len(baseline["messages"][1]["content"]),
            "prompt_chars_summary": len(prompt),
        })
    return {
        "schema_version": "evidence-ux-v1-evaluation",
        "evidence_level": "fixed deterministic context/verification cases; no teaching or model-quality claim",
        "summary_rules": {
            "STRONG_AGREEMENT": "symbolic and DSP canonical chord agree with no warnings",
            "PARTIAL_AGREEMENT": "same root, or exact agreement affected by warnings",
            "MIXED_EVIDENCE": "symbolic and DSP canonical roots disagree",
            "LIMITED_EVIDENCE": "independent DSP candidate unavailable",
        },
        "cases": results,
        "outcomes": {
            "cases": len(results),
            "summary_propagation_passed": sum(item["summary_propagated"] for item in results),
            "uncertainty_behavior_passed": sum(item["uncertainty_expected"] == item["uncertainty_observed"] for item in results),
            "raw_evidence_exposure_cases": sum(not item["raw_evidence_absent"] for item in results),
            "mixed_or_limited_assertions_repaired": sum(
                "added_uncertainty_caveat" in item["summary_repairs"] for item in results
                if item["case"] in {"mixed", "limited"}
            ),
            "mean_prompt_character_delta": mean(
                item["prompt_chars_summary"] - item["prompt_chars_baseline"] for item in results
            ),
        },
        "ui": {
            "affordance": "collapsed Why this chord? details",
            "feedback": ["correct", "wrong", "not_sure"],
            "persistence": "bounded browser localStorage only; no audio, filename, or server submission",
        },
        "limitations": [
            "No provider model was used; this evaluates deterministic context and verification behavior.",
            "No learning, pedagogy, accuracy, or calibrated-confidence improvement is claimed.",
            "EvidenceSummary categories are fixed rules and require real-performance validation.",
        ],
    }


def render_markdown(report: dict) -> str:
    outcomes = report["outcomes"]
    lines = [
        "# Product Evidence UX v1", "", "## Summary rules", "",
    ]
    lines.extend(f"- `{name}`: {rule}." for name, rule in report["summary_rules"].items())
    lines.extend([
        "", "## Tutor behavior", "",
        f"Fixed context cases: {outcomes['cases']}. Summary propagation: {outcomes['summary_propagation_passed']}/{outcomes['cases']}. Uncertainty behavior: {outcomes['uncertainty_behavior_passed']}/{outcomes['cases']}.",
        f"Mixed/limited hard-label assertions repaired: {outcomes['mixed_or_limited_assertions_repaired']}/2. Raw-evidence exposure cases: {outcomes['raw_evidence_exposure_cases']}.",
        f"Mean prompt growth: {outcomes['mean_prompt_character_delta']:.0f} characters.", "",
        "This is deterministic assembly/verification evidence, not a provider-model or teaching-effect result.", "",
        "## UI behavior", "",
        "The progression view contains a collapsed `Why this chord?` disclosure with categorical strength, musical wording, and observed pitch-class names. It never shows vectors, scores, paths, or internal weights.", "",
        "Feedback choices are Correct chord, Wrong chord, and Not sure. The browser retains at most 50 compact local records under a random session identifier. Audio, filenames, paths, and corrections are not uploaded or retained.", "",
        "## Limitations", "",
    ])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["outcomes"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
