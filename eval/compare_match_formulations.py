"""Compare candidate-match formulations with all other scorer terms frozen."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.analyze_advanced_scorer import candidate_summary, score_breakdown
from eval.evaluate_oracle_classifier import (
    CLASSIFIER_SOURCE,
    QUALITIES,
    ROOT,
    ROOT_NAMES,
    chord_label,
    inversion_pitches,
    load_classifier_functions,
    parse_prediction,
    root_position_pitches,
)

JSON_REPORT = ROOT / "eval" / "match_formulation_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "match_formulation_report.md"
DETECTED_KEY = "E major"
TIE_TOLERANCE = 1e-12

FORMULATIONS: dict[str, dict[str, Any]] = {
    "baseline_template_coverage": {"kind": "template_coverage"},
    "bidirectional_f1": {"kind": "f1"},
    "jaccard": {"kind": "jaccard"},
    "unexplained_penalty_0.10": {"kind": "penalty", "lambda": 0.10},
    "unexplained_penalty_0.20": {"kind": "penalty", "lambda": 0.20},
    "unexplained_penalty_0.30": {"kind": "penalty", "lambda": 0.30},
    "specificity_tie_rule": {"kind": "template_coverage", "specificity_tie_rule": True},
}

CONTAMINATION_SPECS = (
    (0, "maj", 2), (2, "maj", 4), (7, "maj", 9), (9, "maj", 11),
    (9, "min", 6), (4, "min", 1), (2, "min", 11),
    (2, "7", 4), (7, "7", 9), (0, "maj7", 2),
    (9, "min7", 6), (0, "sus4", 2),
)


def match_components(observed: set[int], template: set[int]) -> dict[str, float]:
    overlap = len(observed & template)
    recall = overlap / len(template) if template else 0.0
    precision = overlap / len(observed) if observed else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    union = len(observed | template)
    jaccard = overlap / union if union else 0.0
    unexplained_ratio = len(observed - template) / len(observed) if observed else 0.0
    return {
        "overlap_count": overlap,
        "template_recall": recall,
        "input_precision": precision,
        "f1": f1,
        "jaccard": jaccard,
        "unexplained_input_ratio": unexplained_ratio,
    }


def formulation_match(observed: set[int], template: set[int], formulation: dict[str, Any]) -> tuple[float, dict[str, float]]:
    components = match_components(observed, template)
    kind = formulation["kind"]
    if kind == "template_coverage":
        value = components["template_recall"]
    elif kind == "f1":
        value = components["f1"]
    elif kind == "jaccard":
        value = components["jaccard"]
    elif kind == "penalty":
        value = components["template_recall"] - formulation["lambda"] * components["unexplained_input_ratio"]
    else:
        raise ValueError(f"Unknown match formulation: {kind}")
    return value, components


def _specificity_dominance(candidate: dict[str, Any], group: list[dict[str, Any]], observed: set[int]) -> int:
    candidate_template = set(candidate["template_pitch_classes"])
    if not candidate_template <= observed:
        return 0
    return sum(
        set(other["template_pitch_classes"]) < candidate_template
        and candidate_template - set(other["template_pitch_classes"]) <= observed
        for other in group
    )


def apply_specificity_tie_rule(candidates: list[dict[str, Any]], observed: set[int]) -> list[dict[str, Any]]:
    """Reorder only equal-score groups when one observed template dominates a strict subset."""
    ordered: list[dict[str, Any]] = []
    index = 0
    while index < len(candidates):
        end = index + 1
        while end < len(candidates) and math.isclose(candidates[end]["score"], candidates[index]["score"], abs_tol=TIE_TOLERANCE):
            end += 1
        group = candidates[index:end]
        dominance = {
            candidate["template_index"]: _specificity_dominance(candidate, group, observed)
            for candidate in group
        }
        group.sort(key=lambda candidate: (-dominance[candidate["template_index"]], candidate["template_index"]))
        ordered.extend(group)
        index = end
    return ordered


def rank_candidates(
    pitches: list[int], formulation: dict[str, Any], namespace: dict[str, Any]
) -> list[dict[str, Any]]:
    observed = {pitch % 12 for pitch in pitches}
    bass = min(pitches) if pitches else None
    candidates = []
    for index, template in enumerate(namespace["get_chord_templates"]()):
        baseline = score_breakdown(observed, bass, DETECTED_KEY, template, namespace["get_key_prior_weights"])
        match_value, match_detail = formulation_match(observed, template["pcs"], formulation)
        components = dict(baseline["components"])
        components["pitch_match"] = match_value
        candidates.append({
            "template_index": index,
            "label": template["name"],
            "canonical_label": f"{ROOT_NAMES[template['root']]}:{template['quality']}",
            "root": ROOT_NAMES[template["root"]],
            "root_pc": template["root"],
            "quality": template["quality"],
            "template_pitch_classes": sorted(template["pcs"]),
            "score": sum(components.values()),
            "components": components,
            "match_detail": match_detail,
            "matched_pitch_classes": sorted(observed & template["pcs"]),
            "missing_template_tones": sorted(template["pcs"] - observed),
            "unexplained_input_tones": sorted(observed - template["pcs"]),
            "bass_relation": baseline["bass_relation"],
        })
    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["template_index"]))
    if formulation.get("specificity_tie_rule"):
        candidates = apply_specificity_tie_rule(candidates, observed)
    for rank, candidate in enumerate(candidates, 1):
        candidate["rank"] = rank
    return candidates


def true_candidate(candidates: list[dict[str, Any]], root_pc: int, quality: str) -> Optional[dict[str, Any]]:
    return next((candidate for candidate in candidates if candidate["root_pc"] == root_pc and candidate["quality"] == quality), None)


def evaluate_case(case: dict[str, Any], formulation: dict[str, Any], namespace: dict[str, Any]) -> dict[str, Any]:
    candidates = rank_candidates(case["pitches"], formulation, namespace)
    winner, runner_up = candidates[:2]
    true = true_candidate(candidates, case["root_pc"], case["quality"])
    predicted_root, predicted_quality = parse_prediction(winner["label"])
    result = {
        **case,
        "winner": candidate_summary(winner),
        "runner_up": candidate_summary(runner_up),
        "true_candidate": candidate_summary(true) if true else None,
        "true_candidate_rank": true["rank"] if true else None,
        "root_correct": predicted_root == case["root_pc"],
        "quality_correct": predicted_quality == case["quality"],
        "exact_correct": predicted_root == case["root_pc"] and predicted_quality == case["quality"],
        "winner_runner_up_margin": winner["score"] - runner_up["score"],
        "winner_true_margin": winner["score"] - true["score"] if true else None,
        "winner_tie_count": sum(math.isclose(candidate["score"], winner["score"], abs_tol=TIE_TOLERANCE) for candidate in candidates),
        "top_three": [candidate_summary(candidate) for candidate in candidates[:3]],
    }
    return result


def base_case(root_pc: int, quality: str, pitches: list[int], condition: str, variant: str = "") -> dict[str, Any]:
    return {
        "case_id": f"{condition}:{chord_label(root_pc, quality)}:{variant}",
        "condition": condition,
        "variant": variant,
        "true": chord_label(root_pc, quality),
        "root_pc": root_pc,
        "root": ROOT_NAMES[root_pc],
        "quality": quality,
        "pitches": pitches,
        "pitch_classes": sorted({pitch % 12 for pitch in pitches}),
        "bass_pitch": min(pitches),
        "vocabulary_limited": quality == "dim",
    }


def build_datasets() -> dict[str, list[dict[str, Any]]]:
    datasets: dict[str, list[dict[str, Any]]] = {name: [] for name in (
        "complete", "omitted_fifth", "omitted_root", "seventh_without_fifth",
        "duplicated_tones", "inversions", "extra_tone",
    )}
    for quality, definition in QUALITIES.items():
        for root_pc in range(12):
            pitches = root_position_pitches(root_pc, quality)
            datasets["complete"].append(base_case(root_pc, quality, pitches, "complete"))
            datasets["omitted_fifth"].append(base_case(root_pc, quality, [pitch for index, pitch in enumerate(pitches) if index != 2], "omitted_fifth"))
            datasets["omitted_root"].append(base_case(root_pc, quality, pitches[1:], "omitted_root"))
            for inversion in range(1, len(definition["intervals"])):
                datasets["inversions"].append(base_case(root_pc, quality, inversion_pitches(root_pc, quality, inversion), "inversions", str(inversion)))
            duplicate_variants = (pitches + [pitches[0] + 12], [pitches[0], pitches[-1], pitches[0] + 12] + pitches[1:])
            for index, duplicate in enumerate(duplicate_variants, 1):
                datasets["duplicated_tones"].append(base_case(root_pc, quality, duplicate, "duplicated_tones", str(index)))
            if quality in {"7", "maj7", "min7"}:
                datasets["seventh_without_fifth"].append(base_case(root_pc, quality, [pitches[0], pitches[1], pitches[3]], "seventh_without_fifth"))

    for index, (root_pc, quality, extra_pc) in enumerate(CONTAMINATION_SPECS, 1):
        pitches = root_position_pitches(root_pc, quality)
        if extra_pc in {pitch % 12 for pitch in pitches}:
            raise AssertionError(f"Contamination tone is already in {chord_label(root_pc, quality)}")
        extra_midi = 60 + extra_pc
        while extra_midi <= pitches[-1]:
            extra_midi += 12
        datasets["extra_tone"].append(base_case(root_pc, quality, pitches + [extra_midi], "extra_tone", str(index)))
    return datasets


def metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    supported = [case for case in cases if not case["vocabulary_limited"]]
    major_minor = [case for case in cases if case["quality"] in {"maj", "min"}]
    sevenths = [case for case in cases if case["quality"] in {"7", "maj7", "min7"}]
    count = len(cases)
    return {
        "cases": count,
        "root_accuracy": sum(case["root_correct"] for case in cases) / count,
        "quality_accuracy": sum(case["quality_correct"] for case in cases) / count,
        "exact_accuracy": sum(case["exact_correct"] for case in cases) / count,
        "supported_exact_accuracy": sum(case["exact_correct"] for case in supported) / len(supported),
        "major_minor_exact_accuracy": sum(case["exact_correct"] for case in major_minor) / len(major_minor) if major_minor else None,
        "seventh_exact_accuracy": sum(case["exact_correct"] for case in sevenths) / len(sevenths) if sevenths else None,
    }


def grouped_exact(cases: list[dict[str, Any]], field: str) -> dict[str, float]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        groups[str(case[field])].append(case)
    return {key: sum(case["exact_correct"] for case in values) / len(values) for key, values in sorted(groups.items())}


def margin_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    with_true = [case for case in cases if case["true_candidate"]]
    return {
        "mean_true_candidate_rank": mean(case["true_candidate_rank"] for case in with_true),
        "mean_winner_score": mean(case["winner"]["score"] for case in with_true),
        "mean_true_score": mean(case["true_candidate"]["score"] for case in with_true),
        "mean_runner_up_score": mean(case["runner_up"]["score"] for case in with_true),
        "mean_winner_runner_up_margin": mean(case["winner_runner_up_margin"] for case in with_true),
        "mean_winner_true_margin": mean(case["winner_true_margin"] for case in with_true),
        "winner_tie_rate": sum(case["winner_tie_count"] > 1 for case in with_true) / len(with_true),
        "cases_with_true_candidate": len(with_true),
    }


def compact_case(case: dict[str, Any]) -> dict[str, Any]:
    return {key: case[key] for key in (
        "case_id", "condition", "variant", "true", "root", "quality", "pitches",
        "pitch_classes", "bass_pitch", "vocabulary_limited", "winner", "runner_up",
        "true_candidate", "true_candidate_rank", "root_correct", "quality_correct",
        "exact_correct", "winner_runner_up_margin", "winner_true_margin", "winner_tie_count",
        "top_three",
    )}


def baseline_reproduction(namespace: dict[str, Any], complete_cases: list[dict[str, Any]]) -> dict[str, Any]:
    from eval.analyze_advanced_scorer import rank_candidates as forensic_rank

    errors = []
    winner_mismatches = 0
    for case in complete_cases:
        expected = forensic_rank(case["pitches"], DETECTED_KEY, namespace)["candidates"]
        actual = rank_candidates(case["pitches"], FORMULATIONS["baseline_template_coverage"], namespace)
        winner_mismatches += actual[0]["canonical_label"] != expected[0]["canonical_label"]
        errors.extend(abs(left["score"] - right["score"]) for left, right in zip(actual, expected))
    return {"cases": len(complete_cases), "winner_mismatches": winner_mismatches, "max_candidate_score_error": max(errors)}


def choose_decision(results: dict[str, Any]) -> dict[str, Any]:
    comparison = {}
    robustness_names = ("omitted_fifth", "omitted_root", "seventh_without_fifth", "inversions", "duplicated_tones", "extra_tone")
    for name, result in results.items():
        complete = result["datasets"]["complete"]["metrics"]
        robustness = mean(result["datasets"][dataset]["metrics"]["supported_exact_accuracy"] for dataset in robustness_names)
        comparison[name] = {
            "complete_supported": complete["supported_exact_accuracy"],
            "seventh": complete["seventh_exact_accuracy"],
            "robustness_mean": robustness,
            "balanced_mean": mean((complete["supported_exact_accuracy"], complete["seventh_exact_accuracy"], robustness)),
        }
    winner = max(comparison, key=lambda name: (comparison[name]["balanced_mean"], comparison[name]["robustness_mean"], name == "jaccard"))
    if winner == "specificity_tie_rule":
        outcome = "A. SPECIFICITY_TIE_RULE_SUFFICIENT"
    elif winner in {"bidirectional_f1", "jaccard"}:
        outcome = "B. BIDIRECTIONAL_MATCH_WINNER"
    elif winner.startswith("unexplained_penalty"):
        outcome = "C. EXPLICIT_PENALTY_WINNER"
    else:
        outcome = "D. NO_SINGLE_FORMULATION_DOMINATES"
    return {
        "outcome": outcome,
        "winner": winner,
        "selection_metrics": comparison,
        "rule": "Maximize the mean of supported complete exact, complete seventh exact, and mean supported robustness exact; break ties by robustness, then the simpler named formulation.",
    }


def build_report() -> dict[str, Any]:
    namespace, hashes = load_classifier_functions()
    datasets = build_datasets()
    reproduction = baseline_reproduction(namespace, datasets["complete"])
    if reproduction["winner_mismatches"] or reproduction["max_candidate_score_error"] > TIE_TOLERANCE:
        raise AssertionError(f"Baseline did not reproduce forensic scorer: {reproduction}")

    results = {}
    for formulation_name, formulation in FORMULATIONS.items():
        dataset_results = {}
        for dataset_name, cases in datasets.items():
            evaluated = [evaluate_case(case, formulation, namespace) for case in cases]
            dataset_results[dataset_name] = {
                "metrics": metrics(evaluated),
                "per_quality_exact": grouped_exact(evaluated, "quality"),
                "per_root_exact": grouped_exact(evaluated, "root"),
                "margins": margin_metrics(evaluated),
                "cases": [compact_case(case) for case in evaluated],
            }
        results[formulation_name] = {"definition": formulation, "datasets": dataset_results}

    seventh_comparison = []
    for case_index, case in enumerate(datasets["complete"]):
        if case["quality"] not in {"7", "maj7", "min7"}:
            continue
        seventh_comparison.append({
            "true": case["true"],
            "quality": case["quality"],
            "predictions": {
                name: result["datasets"]["complete"]["cases"][case_index]["winner"]["canonical_label"]
                for name, result in results.items()
            },
        })

    report = {
        "schema_version": "chord-match-formulation-benchmark-v1",
        "command": "python eval/compare_match_formulations.py",
        "evidence_level": "L2 harmony / candidate-match isolation",
        "source": {"file": str(CLASSIFIER_SOURCE.relative_to(ROOT)), "hashes_sha256": hashes},
        "frozen_terms": {
            "detected_key": DETECTED_KEY,
            "bass": "minimum MIDI pitch in each voicing",
            "templates": "unchanged 85-candidate inventory",
            "other_score_terms": ["bass_bonus", "key_prior", "suspension_adjustment", "complexity_penalty"],
            "candidate_order": "source template order; only specificity_tie_rule changes equal-score ordering",
        },
        "formulations": FORMULATIONS,
        "penalty_rationale": "0.10, 0.20, and 0.30 span 10-30% of the unit match scale and bracket the scorer's 0.10-0.25 contextual adjustments without an exhaustive sweep.",
        "dataset_counts": {name: len(cases) for name, cases in datasets.items()},
        "baseline_reproduction": reproduction,
        "results": results,
        "seventh_comparison": seventh_comparison,
    }
    report["decision_gate"] = choose_decision(results)
    report["limitations"] = [
        "Diminished templates remain absent and diminished cases are marked vocabulary-limited.",
        "Key priors, bass behavior, suspension adjustment, complexity penalty, and candidate inventory remain frozen even when they cause residual errors.",
        "Oracle and robustness pitch sets do not represent audio transcription or segmentation uncertainty.",
        "Candidate margins are diagnostics, not calibrated confidence.",
    ]
    return report


def pct(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def fmt(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
    ]


def render_markdown(report: dict[str, Any]) -> str:
    results = report["results"]
    names = list(results)
    lines = [
        "# Chord Match Formulation Benchmark v1", "",
        "Fresh deterministic evidence from `python eval/compare_match_formulations.py`.", "",
        "## Formulations", "",
        "- `baseline_template_coverage`: overlap / template size.",
        "- `bidirectional_f1`: harmonic mean of template recall and input precision.",
        "- `jaccard`: overlap / union.",
        "- `unexplained_penalty_0.10/0.20/0.30`: template recall minus lambda times unexplained-input ratio.",
        "- `specificity_tie_rule`: baseline score with strict observed supersets preferred only inside equal-score groups.", "",
        f"Penalty rationale: {report['penalty_rationale']}", "",
        "## Complete oracle results", "",
    ]
    lines.extend(table(
        ["Formulation", "Root", "Quality", "Exact", "Supported exact", "Maj/min", "Seventh"],
        [[name, pct(value["datasets"]["complete"]["metrics"]["root_accuracy"]), pct(value["datasets"]["complete"]["metrics"]["quality_accuracy"]), pct(value["datasets"]["complete"]["metrics"]["exact_accuracy"]), pct(value["datasets"]["complete"]["metrics"]["supported_exact_accuracy"]), pct(value["datasets"]["complete"]["metrics"]["major_minor_exact_accuracy"]), pct(value["datasets"]["complete"]["metrics"]["seventh_exact_accuracy"])] for name, value in results.items()],
    ))

    lines.extend(["", "## Per-quality complete exact", ""])
    qualities = list(QUALITIES)
    lines.extend(table(["Formulation", *qualities], [[name, *(pct(value["datasets"]["complete"]["per_quality_exact"].get(quality)) for quality in qualities)] for name, value in results.items()]))

    lines.extend(["", "## Per-root complete exact", ""])
    roots = list(ROOT_NAMES)
    lines.extend(table(["Formulation", *roots], [[name, *(pct(value["datasets"]["complete"]["per_root_exact"].get(root)) for root in roots)] for name, value in results.items()]))

    lines.extend(["", "## Robustness tradeoff matrix", ""])
    dataset_names = list(report["dataset_counts"])
    lines.extend(table(["Formulation", *dataset_names], [[name, *(pct(value["datasets"][dataset]["metrics"]["supported_exact_accuracy"]) for dataset in dataset_names)] for name, value in results.items()]))

    lines.extend(["", "## Extra-tone retention", ""])
    lines.extend(table(
        ["Formulation", "Root retained", "Quality retained", "Exact retained"],
        [[name, pct(value["datasets"]["extra_tone"]["metrics"]["root_accuracy"]), pct(value["datasets"]["extra_tone"]["metrics"]["quality_accuracy"]), pct(value["datasets"]["extra_tone"]["metrics"]["exact_accuracy"])] for name, value in results.items()],
    ))

    lines.extend(["", "## Seventh predictions", ""])
    lines.extend(table(["True", *names], [[case["true"], *(case["predictions"][name] for name in names)] for case in report["seventh_comparison"]]))

    lines.extend(["", "## Complete-case candidate margins", "", "Margins use only cases with a candidate for the true quality; diminished cases are excluded.", ""])
    lines.extend(table(
        ["Formulation", "True rank", "Winner", "True", "Runner-up", "Winner-runner", "Winner-true", "Tie rate"],
        [[name, fmt(value["datasets"]["complete"]["margins"]["mean_true_candidate_rank"]), fmt(value["datasets"]["complete"]["margins"]["mean_winner_score"]), fmt(value["datasets"]["complete"]["margins"]["mean_true_score"]), fmt(value["datasets"]["complete"]["margins"]["mean_runner_up_score"]), fmt(value["datasets"]["complete"]["margins"]["mean_winner_runner_up_margin"]), fmt(value["datasets"]["complete"]["margins"]["mean_winner_true_margin"]), pct(value["datasets"]["complete"]["margins"]["winner_tie_rate"])] for name, value in results.items()],
    ))

    decision = report["decision_gate"]
    lines.extend(["", "## Selection metrics", ""])
    lines.extend(table(
        ["Formulation", "Complete supported", "Seventh", "Robustness mean", "Balanced mean"],
        [[name, pct(value["complete_supported"]), pct(value["seventh"]), pct(value["robustness_mean"]), pct(value["balanced_mean"])] for name, value in decision["selection_metrics"].items()],
    ))
    lines.extend([
        "", "## Decision gate", "",
        f"**{decision['outcome']}**. Selected `{decision['winner']}`.", "",
        decision["rule"], "",
        "## Frozen controls", "",
        f"`{json.dumps(report['frozen_terms'], sort_keys=True)}`", "",
        "## Limitations", "",
    ])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def write_reports(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=JSON_REPORT)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_REPORT)
    args = parser.parse_args()
    report = build_report()
    write_reports(report, args.json, args.markdown)
    print(f"baseline reproduction: {report['baseline_reproduction']}")
    for name, result in report["results"].items():
        complete = result["datasets"]["complete"]["metrics"]
        print(f"{name}: supported={pct(complete['supported_exact_accuracy'])} seventh={pct(complete['seventh_exact_accuracy'])}")
    print(f"decision: {report['decision_gate']['outcome']} ({report['decision_gate']['winner']})")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
