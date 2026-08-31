"""Deterministic structural/behavioral evaluation for Evidence-Grounded Tutor v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tutor_evidence import (  # noqa: E402
    assemble_tutor_context,
    build_performance_evidence,
    build_retrieval_query,
    assess_tutor_request,
    select_retrieved_evidence,
    verify_and_repair_response,
)

CASES_PATH = ROOT / "eval" / "tutor_evidence_cases.json"
REPORT_JSON = ROOT / "eval" / "tutor_evidence_report.json"
REPORT_MD = ROOT / "eval" / "tutor_evidence_report.md"
DEMO_JSON = ROOT / "eval" / "evidence_grounded_demos.json"


def chord_results(case):
    return {
        "analysis_summary": {
            "detected_key": case.get("key") or "Unknown",
            "chord_progression": " - ".join(event[2] for event in case["events"]),
            "total_chord_events": len(case["events"]),
        },
        "chord_events": [
            {
                "start": event[0], "end": event[1], "chord": event[2],
                "confidence": event[3], "source_detector": "fixture",
            }
            for event in case["events"]
        ],
        "detector_used": "fixture",
        "warnings": case.get("warnings") or [],
        "chord_tabs": [{"chord": event[2], "shape": "fixture"} for event in case["events"]],
    }


def retrieval_results(case):
    return {
        "total_results": len(case.get("retrieval") or []),
        "results": [
            {
                "id": item.get("id"), "rank": item.get("rank"),
                "source_file": item.get("source"),
                "similarity_score": item.get("score"),
                "document": item.get("content"),
                "metadata": {"source_file": item.get("source")},
            }
            for item in case.get("retrieval") or []
        ],
    }


def evaluate_case(case):
    performance = build_performance_evidence(chord_results(case), audio_id=case["id"] + ".wav")
    assessment = assess_tutor_request(performance, case["question"])
    query = build_retrieval_query(performance, assessment, case["question"])
    retrieval = select_retrieved_evidence(retrieval_results(case), query)
    context = assemble_tutor_context(performance, retrieval, case["question"])
    verification = verify_and_repair_response(case["mock_response"], context)
    expect = case["expect"]
    selected_sources = [item.get("source") for item in retrieval["evidence"]]
    model_text = json.dumps(context["messages"])

    checks = {
        "intent": assessment.intent == expect["intent"],
        "retrieval_status": retrieval["status"] == expect["retrieval_status"],
        "uncertainty": assessment.requires_uncertainty_language == expect["uncertainty"],
        "timing_propagated": all(
            str(event.start) in model_text and str(event.end) in model_text
            for event in performance.chord_events
        ),
        "confidence_propagated": all(
            event.confidence is None or str(event.confidence) in model_text
            for event in performance.chord_events
        ),
        "warnings_propagated": all(warning in model_text for warning in performance.warnings),
        "detector_provenance_propagated": (
            performance.detector in model_text
            and all(event.source_detector in model_text for event in performance.chord_events)
        ),
        "estimated_key_propagated": (
            performance.estimated_key is None or performance.estimated_key in model_text
        ),
        "retrieved_content_propagated": all(
            item["content"] in model_text for item in retrieval["evidence"]
        ),
        "verification_passed": verification["passed"],
    }
    if expect.get("selected_sources") is not None:
        checks["selected_sources"] = selected_sources == expect["selected_sources"]
    if expect.get("rejected_sources"):
        checks["rejected_sources"] = not any(
            source in selected_sources for source in expect["rejected_sources"]
        )
    if expect.get("repair"):
        checks["expected_repair"] = expect["repair"] in verification["repairs"]
    if expect.get("final_contains"):
        checks["final_contains"] = expect["final_contains"].lower() in verification["final_response"].lower()

    return {
        "id": case["id"],
        "description": case["description"],
        "passed": all(checks.values()),
        "checks": checks,
        "assessment": assessment.to_dict(),
        "retrieval": retrieval,
        "verification": verification,
        "performance_evidence": performance.to_dict(),
    }


def main():
    corpus = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in corpus["cases"]]
    uncertainty_cases = [r for r in results if r["assessment"]["requires_uncertainty_language"]]
    grounded_cases = [r for r in results if r["retrieval"]["evidence"]]
    no_result_cases = [r for r in results if not r["retrieval"]["evidence"]]
    propagation_checks = {
        "timing": "timing_propagated",
        "confidence": "confidence_propagated",
        "warnings": "warnings_propagated",
        "detector_provenance": "detector_provenance_propagated",
        "estimated_key": "estimated_key_propagated",
    }
    preserved_fields = [
        field
        for field, check in propagation_checks.items()
        if all(result["checks"][check] for result in results)
    ]
    report = {
        "schema_version": corpus["schema_version"],
        "total_cases": len(results),
        "passed_cases": sum(result["passed"] for result in results),
        "structural_evidence_fields": {
            "preserved": len(preserved_fields),
            "total": len(propagation_checks),
            "fields": preserved_fields,
        },
        "grounded_cases": {"passed": sum(r["passed"] for r in grounded_cases), "total": len(grounded_cases)},
        "uncertainty_cases": {"passed": sum(r["passed"] for r in uncertainty_cases), "total": len(uncertainty_cases)},
        "retrieval_absence_cases": {"passed": sum(r["passed"] for r in no_result_cases), "total": len(no_result_cases)},
        "results": results,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Evidence-Grounded Tutor v1 Evaluation", "",
        f"Cases: **{report['passed_cases']}/{report['total_cases']} passed**", "",
        f"Evidence propagation: **{report['structural_evidence_fields']['preserved']}/{report['structural_evidence_fields']['total']} fields preserved**", "",
        f"Grounded cases: **{report['grounded_cases']['passed']}/{report['grounded_cases']['total']} passed**", "",
        f"Uncertainty cases: **{report['uncertainty_cases']['passed']}/{report['uncertainty_cases']['total']} passed**", "",
        f"Retrieval-absence cases: **{report['retrieval_absence_cases']['passed']}/{report['retrieval_absence_cases']['total']} passed**", "",
        "| Case | Result | Repairs |", "|---|---|---|",
    ]
    for result in results:
        repairs = ", ".join(result["verification"]["repairs"]) or "none"
        lines.append(f"| {result['id']} | {'PASS' if result['passed'] else 'FAIL'} | {repairs} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    demo_ids = {"grounded_theory", "low_confidence_chord", "retrieval_miss"}
    demos = []
    for result in results:
        if result["id"] in demo_ids:
            demos.append({
                "id": result["id"],
                "performance_evidence": result["performance_evidence"],
                "retrieved_evidence": result["retrieval"]["evidence"],
                "final_tutor_output": result["verification"]["final_response"],
                "verification": {
                    "passed": result["verification"]["passed"],
                    "checks": result["verification"]["checks"],
                    "repairs": result["verification"]["repairs"],
                },
            })
    DEMO_JSON.write_text(json.dumps({"demos": demos}, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    if report["passed_cases"] != report["total_cases"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
