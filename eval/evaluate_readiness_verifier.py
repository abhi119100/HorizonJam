"""Append-only fixed counterexample evaluation; never rewrites accepted reports."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tutor_evidence import verify_and_repair_response


def evaluate():
    context = {
        "assessment": {"requires_uncertainty_language": True},
        "performance_evidence": {"chord_events": [{"chord": "D7", "confidence": 0.2}]},
        "retrieval": {"evidence": []},
    }
    cases = json.loads((ROOT / "eval/readiness/verifier_cases.json").read_text())["cases"]
    results = []
    for case in cases:
        verification = verify_and_repair_response(case["response"], context)
        output = verification["final_response"]
        passed = (not case.get("forbidden") or case["forbidden"].lower() not in output.lower()) and (not case.get("preserve") or case["preserve"].lower() in output.lower())
        results.append({**case, "context": context, "verification": verification, "case_passed": passed})
    return {"scope": "deterministic response repair; no model, accuracy, or teaching-effect claim", "source_sha256": hashlib.sha256((ROOT / "tutor_evidence.py").read_bytes()).hexdigest(), "passed": sum(r["case_passed"] for r in results), "total": len(results), "cases": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{report['passed']}/{report['total']} fixed cases passed")
