"""Offline candidate-level forensics for HorizonJam's advanced chord scorer."""

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


JSON_REPORT = ROOT / "eval" / "advanced_scorer_forensics.json"
MARKDOWN_REPORT = ROOT / "eval" / "advanced_scorer_forensics.md"
SCORE_TERMS = ("pitch_match", "bass_bonus", "key_prior", "suspension_adjustment", "complexity_penalty")
KEY_CONTEXTS = ("E major", "A major")
EXAMPLE_CASES = ((2, "7"), (7, "7"), (0, "maj7"), (9, "min7"), (0, "maj"), (9, "min"), (0, "sus4"), (0, "dim"))


def note_names(pitches: list[int]) -> list[str]:
    return [f"{ROOT_NAMES[pitch % 12]}{int(pitch / 12) - 1}" for pitch in pitches]


def canonical_candidate(root: int, quality: str) -> str:
    return f"{ROOT_NAMES[root]}:{quality}"


def score_breakdown(
    pitch_classes: set[int],
    bass_pitch: Optional[int],
    detected_key: Optional[str],
    template: dict[str, Any],
    get_key_prior_weights: Any,
    disabled: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Decompose the source equation without changing any baseline term."""
    root = template["root"]
    template_pcs = template["pcs"]
    quality = template["quality"]
    matched = pitch_classes & template_pcs
    pitch_match = len(matched) / len(template_pcs) if template_pcs else 0.0

    bass_bonus = 0.0
    bass_relation = "none"
    if bass_pitch is not None:
        bass_pc = bass_pitch % 12
        if bass_pc == root:
            bass_bonus = 0.25
            bass_relation = "root"
        elif bass_pc in template_pcs:
            bass_bonus = 0.10
            bass_relation = "chord_tone"
        else:
            bass_relation = "outside_template"

    key_prior = get_key_prior_weights(detected_key).get((root, quality), 0.0)
    suspension_adjustment = 0.0
    if quality == "sus2":
        proper = (root + 2) % 12 in pitch_classes and not ({(root + 3) % 12, (root + 4) % 12} & pitch_classes)
        suspension_adjustment = 0.10 if proper else -0.20
    elif quality in {"sus4", "sus4_priority"}:
        proper = (root + 5) % 12 in pitch_classes and not ({(root + 3) % 12, (root + 4) % 12} & pitch_classes)
        suspension_adjustment = (0.15 if quality == "sus4_priority" else 0.10) if proper else -0.20

    complexity_penalty = -0.10 if quality in {"maj7", "min7", "7"} and len(pitch_classes) <= 3 else 0.0
    original = {
        "pitch_match": pitch_match,
        "bass_bonus": bass_bonus,
        "key_prior": key_prior,
        "suspension_adjustment": suspension_adjustment,
        "complexity_penalty": complexity_penalty,
    }
    applied = {term: (0.0 if term in disabled else value) for term, value in original.items()}
    result = {
        "components": applied,
        "score": sum(applied.values()),
        "matched_pitch_classes": sorted(matched),
        "missing_template_tones": sorted(template_pcs - pitch_classes),
        "unexplained_input_tones": sorted(pitch_classes - template_pcs),
        "bass_relation": bass_relation,
        "missing_tone_penalty": 0.0,
        "extra_tone_penalty": 0.0,
    }
    if disabled:
        result["baseline_components"] = original
    return result


def candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    """Retain ranking evidence without duplicating complete candidate records."""
    return {
        key: candidate[key]
        for key in (
            "rank", "template_index", "label", "canonical_label", "root", "root_pc",
            "quality", "score", "components", "matched_pitch_classes",
            "missing_template_tones", "unexplained_input_tones", "bass_relation",
        )
    }


def rank_candidates(
    pitches: list[int],
    detected_key: Optional[str],
    namespace: dict[str, Any],
    disabled: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    pitch_classes = {pitch % 12 for pitch in pitches}
    bass_pitch = min(pitches) if pitches else None
    templates = namespace["get_chord_templates"]()
    candidates = []
    max_error = 0.0
    for index, template in enumerate(templates):
        breakdown = score_breakdown(
            pitch_classes, bass_pitch, detected_key, template,
            namespace["get_key_prior_weights"], disabled,
        )
        source_score = namespace["score_chord_candidate"](pitch_classes, bass_pitch, detected_key, template)
        if not disabled:
            max_error = max(max_error, abs(source_score - breakdown["score"]))
        candidates.append({
            "template_index": index,
            "label": template["name"],
            "canonical_label": canonical_candidate(template["root"], template["quality"]),
            "root": ROOT_NAMES[template["root"]],
            "root_pc": template["root"],
            "quality": template["quality"],
            "template_pitch_classes": sorted(template["pcs"]),
            "template_tone_count": len(template["pcs"]),
            "score": breakdown["score"],
            "source_score": source_score if not disabled else None,
            **breakdown,
        })
    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["template_index"]))
    for rank, candidate in enumerate(candidates, 1):
        candidate["rank"] = rank
    return {
        "pitch_classes": sorted(pitch_classes),
        "bass_pitch": bass_pitch,
        "bass_pitch_class": bass_pitch % 12 if bass_pitch is not None else None,
        "detected_key": detected_key,
        "disabled_terms": sorted(disabled),
        "reconciliation_max_abs_error": max_error,
        "candidates": candidates,
    }


def find_true_candidate(ranking: dict[str, Any], root_pc: int, quality: str) -> Optional[dict[str, Any]]:
    return next(
        (candidate for candidate in ranking["candidates"] if candidate["root_pc"] == root_pc and candidate["quality"] == quality),
        None,
    )


def analyze_case(
    root_pc: int,
    quality: str,
    pitches: list[int],
    detected_key: Optional[str],
    namespace: dict[str, Any],
    disabled: frozenset[str] = frozenset(),
    include_full_ranking: bool = True,
) -> dict[str, Any]:
    ranking = rank_candidates(pitches, detected_key, namespace, disabled)
    winner = ranking["candidates"][0]
    runner_up = ranking["candidates"][1]
    true_candidate = find_true_candidate(ranking, root_pc, quality)
    predicted_root, predicted_quality = parse_prediction(winner["label"])
    case = {
        "true": chord_label(root_pc, quality),
        "true_root": ROOT_NAMES[root_pc],
        "true_root_pc": root_pc,
        "true_quality": quality,
        "input_pitches": pitches,
        "input_notes": note_names(pitches),
        "input_pitch_classes": ranking["pitch_classes"],
        "bass_pitch": ranking["bass_pitch"],
        "bass_note": note_names([ranking["bass_pitch"]])[0] if ranking["bass_pitch"] is not None else None,
        "detected_key": detected_key,
        "disabled_terms": sorted(disabled),
        "winner": candidate_summary(winner),
        "runner_up": candidate_summary(runner_up),
        "true_candidate": candidate_summary(true_candidate) if true_candidate else None,
        "winner_runner_up_margin": winner["score"] - runner_up["score"],
        "winner_true_margin": winner["score"] - true_candidate["score"] if true_candidate else None,
        "true_candidate_rank": true_candidate["rank"] if true_candidate else None,
        "root_correct": predicted_root == root_pc,
        "quality_correct": predicted_quality == quality,
        "exact_correct": predicted_root == root_pc and predicted_quality == quality,
        "winner_tie_count": sum(math.isclose(candidate["score"], winner["score"], abs_tol=1e-12) for candidate in ranking["candidates"]),
        "reconciliation_max_abs_error": ranking["reconciliation_max_abs_error"],
        "top_five": [candidate_summary(candidate) for candidate in ranking["candidates"][:5]],
    }
    if include_full_ranking:
        case["complete_ranking"] = ranking["candidates"]
    return case


def case_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(cases)
    seventh = [case for case in cases if case["true_quality"] in {"7", "maj7", "min7"}]
    return {
        "cases": count,
        "root_accuracy": sum(case["root_correct"] for case in cases) / count,
        "quality_accuracy": sum(case["quality_correct"] for case in cases) / count,
        "exact_accuracy": sum(case["exact_correct"] for case in cases) / count,
        "seventh_exact_accuracy": sum(case["exact_correct"] for case in seventh) / len(seventh),
    }


def matching_supported_context(root_pc: int, quality: str, namespace: dict[str, Any]) -> Optional[str]:
    weighted = [
        (namespace["get_key_prior_weights"](context).get((root_pc, quality), 0.0), context)
        for context in KEY_CONTEXTS
    ]
    best_weight, best_context = max(weighted)
    return best_context if best_weight > 0 else None


def evaluate_key_modes(namespace: dict[str, Any]) -> dict[str, Any]:
    modes = {
        "default_e_major": lambda _root, _quality: "E major",
        "no_key_context": lambda _root, _quality: None,
        "matching_supported_context": lambda root, quality: matching_supported_context(root, quality, namespace),
    }
    output = {}
    for mode, context_for in modes.items():
        cases = []
        for quality in QUALITIES:
            for root_pc in range(12):
                context = context_for(root_pc, quality)
                cases.append(analyze_case(root_pc, quality, root_position_pitches(root_pc, quality), context, namespace, include_full_ranking=False))
        output[mode] = {
            "metrics": case_metrics(cases),
            "context_coverage": sum(case["detected_key"] is not None for case in cases) / len(cases),
            "cases": cases,
        }
    baseline = output["default_e_major"]["cases"]
    for mode, result in output.items():
        result["winner_changes_vs_default"] = sum(
            case["winner"]["canonical_label"] != original["winner"]["canonical_label"]
            for case, original in zip(result["cases"], baseline)
        )
        result["true_candidate_rank_changes_vs_default"] = sum(
            case["true_candidate_rank"] != original["true_candidate_rank"]
            for case, original in zip(result["cases"], baseline)
        )
        result["exact_accuracy_delta_vs_default"] = result["metrics"]["exact_accuracy"] - output["default_e_major"]["metrics"]["exact_accuracy"]
        result["seventh_exact_delta_vs_default"] = result["metrics"]["seventh_exact_accuracy"] - output["default_e_major"]["metrics"]["seventh_exact_accuracy"]
    return output


def evaluate_ablations(namespace: dict[str, Any], baseline_cases: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for term in SCORE_TERMS:
        cases = [
            analyze_case(
                case["true_root_pc"], case["true_quality"], case["input_pitches"],
                "E major", namespace, frozenset({term}), include_full_ranking=False,
            )
            for case in baseline_cases
        ]
        output[f"without_{term}"] = {
            "disabled_term": term,
            "metrics": case_metrics(cases),
            "winner_changes": sum(
                case["winner"]["canonical_label"] != baseline["winner"]["canonical_label"]
                for case, baseline in zip(cases, baseline_cases)
            ),
            "dominant_seventh_winner_changes": sum(
                case["true_quality"] == "7" and case["winner"]["canonical_label"] != baseline["winner"]["canonical_label"]
                for case, baseline in zip(cases, baseline_cases)
            ),
            "exact_accuracy_delta": case_metrics(cases)["exact_accuracy"] - case_metrics(baseline_cases)["exact_accuracy"],
            "seventh_exact_delta": case_metrics(cases)["seventh_exact_accuracy"] - case_metrics(baseline_cases)["seventh_exact_accuracy"],
            "cases": cases,
        }
    output["nonexistent_terms"] = {
        "missing_tone_penalty": "absent; missing tones reduce pitch_match only through template coverage",
        "extra_tone_penalty": "absent; unexplained input tones do not affect score",
    }
    return output


def aggregate_margins(cases: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        groups[case["true_quality"]].append(case)
    output = {}
    for quality, quality_cases in sorted(groups.items()):
        winner_runner = [case["winner_runner_up_margin"] for case in quality_cases]
        winner_true = [case["winner_true_margin"] for case in quality_cases if case["winner_true_margin"] is not None]
        output[quality] = {
            "cases": len(quality_cases),
            "true_template_coverage": len(winner_true) / len(quality_cases),
            "mean_winner_runner_up_margin": mean(winner_runner),
            "min_winner_runner_up_margin": min(winner_runner),
            "max_winner_runner_up_margin": max(winner_runner),
            "mean_winner_true_margin": mean(winner_true) if winner_true else None,
            "max_winner_true_margin": max(winner_true) if winner_true else None,
            "winner_tie_rate": sum(case["winner_tie_count"] > 1 for case in quality_cases) / len(quality_cases),
            "mean_true_candidate_rank": mean(case["true_candidate_rank"] for case in quality_cases if case["true_candidate_rank"] is not None) if winner_true else None,
        }
    return output


def evaluate_inversions(namespace: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for root_pc, quality in EXAMPLE_CASES:
        for inversion in range(len(QUALITIES[quality]["intervals"])):
            pitches = inversion_pitches(root_pc, quality, inversion)
            case = analyze_case(root_pc, quality, pitches, "E major", namespace, include_full_ranking=False)
            case["inversion"] = inversion
            cases.append(case)
    root_position = {(case["true_root_pc"], case["true_quality"]): case for case in cases if case["inversion"] == 0}
    inversions = [case for case in cases if case["inversion"] > 0]
    return {
        "cases": cases,
        "metrics": case_metrics(cases),
        "non_root_position_summary": {
            "cases": len(inversions),
            "exact_correct": sum(case["exact_correct"] for case in inversions),
            "wrong_root": sum(not case["root_correct"] for case in inversions),
            "right_root_wrong_quality": sum(case["root_correct"] and not case["quality_correct"] for case in inversions),
            "winner_changes_vs_root_position": sum(
                case["winner"]["canonical_label"] != root_position[(case["true_root_pc"], case["true_quality"])]["winner"]["canonical_label"]
                for case in inversions
            ),
            "inversions_that_recover_exact_from_wrong_root_position": sum(
                case["exact_correct"] and not root_position[(case["true_root_pc"], case["true_quality"])]["exact_correct"]
                for case in inversions
            ),
        },
    }


def dominant_diagnosis(cases: list[dict[str, Any]]) -> dict[str, Any]:
    dominant = [case for case in cases if case["true_quality"] == "7"]
    triad_comparisons = []
    for case in dominant:
        triad = next(candidate for candidate in case["complete_ranking"] if candidate["root_pc"] == case["true_root_pc"] and candidate["quality"] == "maj")
        true = case["true_candidate"]
        triad_comparisons.append({
            "true": case["true"],
            "winner": case["winner"]["canonical_label"],
            "triad_score": triad["score"],
            "seventh_score": true["score"],
            "triad_minus_seventh": triad["score"] - true["score"],
            "triad_unexplained_input_tones": triad["unexplained_input_tones"],
            "seventh_unexplained_input_tones": true["unexplained_input_tones"],
            "seventh_rank": true["rank"],
            "top_five": case["top_five"],
        })
    ties = sum(math.isclose(item["triad_minus_seventh"], 0.0, abs_tol=1e-12) for item in triad_comparisons)
    return {
        "cases": triad_comparisons,
        "template_present": all(case["true_candidate"] is not None for case in dominant),
        "triad_seventh_ties": ties,
        "triad_strictly_higher": sum(item["triad_minus_seventh"] > 0 for item in triad_comparisons),
        "primary_mechanism": "Asymmetric template coverage gives a complete triad subset and its seventh extension the same pitch-match score. With no extra-tone penalty, stable template insertion order selects the earlier triad on ties; sparse E-major priors make the triad strictly higher for E7, A7, and B7.",
    }


def choose_decision(dominant: dict[str, Any], margins: dict[str, Any], diminished_template_coverage: float) -> dict[str, str]:
    if dominant["template_present"] and dominant["triad_seventh_ties"] >= 9 and diminished_template_coverage == 0:
        return {
            "outcome": "C. TEMPLATE_MODEL_PROBLEM",
            "reason": "The asymmetric match formulation systematically allows strict triad subsets to tie complete seventh templates, while diminished candidates are absent entirely.",
        }
    if margins["7"]["winner_tie_rate"] >= 0.75:
        return {"outcome": "A. SMALL_LOCAL_FIX", "reason": "A single deterministic tie mechanism dominates seventh failures."}
    return {"outcome": "F. MIXED", "reason": "No single measured mechanism explains the observed failures."}


def build_report() -> dict[str, Any]:
    namespace, hashes = load_classifier_functions()
    baseline_cases = [
        analyze_case(root_pc, quality, root_position_pitches(root_pc, quality), "E major", namespace)
        for quality in QUALITIES for root_pc in range(12)
    ]
    if max(case["reconciliation_max_abs_error"] for case in baseline_cases) > 1e-12:
        raise AssertionError("Decomposed scores do not reconcile with source score_chord_candidate")
    margins = aggregate_margins(baseline_cases)
    dominant = dominant_diagnosis(baseline_cases)
    diminished_coverage = margins["dim"]["true_template_coverage"]
    examples = {
        chord_label(root, quality): {
            key: value for key, value in next(
                case for case in baseline_cases if case["true_root_pc"] == root and case["true_quality"] == quality
            ).items() if key != "complete_ranking"
        }
        for root, quality in EXAMPLE_CASES
    }
    report = {
        "schema_version": "advanced-chord-scorer-forensics-v1",
        "evidence_level": "L2 harmony / candidate scorer isolation",
        "command": "python eval/analyze_advanced_scorer.py",
        "source": {"file": str(CLASSIFIER_SOURCE.relative_to(ROOT)), "hashes_sha256": hashes},
        "scoring_equation": {
            "formula": "pitch_match + bass_bonus + key_prior + suspension_adjustment + complexity_penalty",
            "terms": {
                "pitch_match": "|input pitch classes intersect template| / |template pitch classes|; range 0..1; larger is better",
                "bass_bonus": "+0.25 when bass is template root, +0.10 when another template tone, otherwise 0",
                "key_prior": "lookup by (candidate root, quality); sparse E-major/A-major table; larger is better",
                "suspension_adjustment": "+0.10 for proper sus2/sus4, +0.15 for Bsus4_priority, otherwise -0.20",
                "complexity_penalty": "-0.10 for 7/min7/maj7 candidates only when input has at most three pitch classes",
                "missing_tone_penalty": "does not exist independently",
                "extra_tone_penalty": "does not exist",
            },
            "tie_break": "Python stable descending score sort preserves template insertion order; major templates precede seventh templates for each root",
            "max_reconciliation_error": max(case["reconciliation_max_abs_error"] for case in baseline_cases),
        },
        "template_inventory": {
            "candidate_count": len(baseline_cases[0]["complete_ranking"]),
            "quality_counts": {quality: sum(candidate["quality"] == quality for candidate in baseline_cases[0]["complete_ranking"]) for quality in ("maj", "min", "sus2", "sus4", "sus4_priority", "7", "min7", "maj7", "dim")},
            "required_optional_distinction": False,
            "tone_weighting": "All template tones are equally weighted through set intersection.",
        },
        "baseline": {"metrics": case_metrics(baseline_cases), "cases": baseline_cases},
        "dominant_seventh": dominant,
        "candidate_margins_by_quality": margins,
        "key_prior_modes": evaluate_key_modes(namespace),
        "term_ablations": evaluate_ablations(namespace, baseline_cases),
        "inversion_forensics": evaluate_inversions(namespace),
        "diminished_forensics": {
            "template_present": False,
            "cases": [
                {
                    "true": case["true"],
                    "winner": case["winner"],
                    "runner_up": case["runner_up"],
                    "winner_runner_up_margin": case["winner_runner_up_margin"],
                }
                for case in baseline_cases if case["true_quality"] == "dim"
            ],
            "mechanism": "No diminished candidate template exists, so diminished failure is separate from seventh subset ties.",
        },
        "required_examples": examples,
    }
    report["decision_gate"] = choose_decision(dominant, margins, diminished_coverage)
    report["limitations"] = [
        "Candidate scores and margins are diagnostics, not calibrated confidence.",
        "Only existing score terms are ablated; no replacement score or production repair is evaluated.",
        "Matching context is limited to positive priors available in the scorer's E-major and A-major tables.",
        "No audio, transcription, segmentation, temporal decoding, retrieval, or tutor logic is exercised.",
    ]
    return report


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def fmt(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
    ]


def candidate_rows(candidates: list[dict[str, Any]]) -> list[list[Any]]:
    return [[
        candidate["rank"], candidate["canonical_label"], fmt(candidate["score"]),
        fmt(candidate["components"]["pitch_match"]), fmt(candidate["components"]["bass_bonus"]),
        fmt(candidate["components"]["key_prior"]), fmt(candidate["components"]["suspension_adjustment"]),
        fmt(candidate["components"]["complexity_penalty"]), candidate["unexplained_input_tones"],
    ] for candidate in candidates]


def render_case(case: dict[str, Any], heading: str) -> list[str]:
    true = case["true_candidate"]
    lines = [
        f"### {heading}", "",
        f"Input: `{' '.join(case['input_notes'])}`; bass `{case['bass_note']}`; key `{case['detected_key']}`.", "",
    ]
    lines.extend(table(
        ["Rank", "Candidate", "Score", "Match", "Bass", "Key", "Sus", "Complexity", "Unexplained PCs"],
        candidate_rows(case["top_five"]),
    ))
    lines.extend(["", f"Winner margin over runner-up: `{fmt(case['winner_runner_up_margin'])}`. True-template rank/score: `{true['rank'] if true else 'absent'}` / `{fmt(true['score']) if true else 'n/a'}`.", ""])
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    equation = report["scoring_equation"]
    lines = [
        "# Advanced Chord Scorer Forensics v1", "",
        "Fresh deterministic evidence from `python eval/analyze_advanced_scorer.py`.", "",
        "## Scoring equation", "",
        f"`score = {equation['formula']}`", "",
    ]
    lines.extend(f"- **{term}**: {description}" for term, description in equation["terms"].items())
    lines.extend(["", f"Tie break: {equation['tie_break']}", f"Maximum decomposition reconciliation error: `{equation['max_reconciliation_error']}`.", "", "## Required forensic traces", ""])
    for label, case in report["required_examples"].items():
        lines.extend(render_case(case, label))

    lines.extend(["## All dominant sevenths", ""])
    for item in report["dominant_seventh"]["cases"]:
        lines.extend([f"### {item['true']}", ""])
        lines.extend(table(["Rank", "Candidate", "Score", "Match", "Bass", "Key", "Sus", "Complexity", "Unexplained PCs"], candidate_rows(item["top_five"])))
        lines.extend(["", f"Major triad `{fmt(item['triad_score'])}` vs seventh `{fmt(item['seventh_score'])}`; triad minus seventh `{fmt(item['triad_minus_seventh'])}`.", ""])

    lines.extend(["## Key-prior sensitivity", ""])
    lines.extend(table(
        ["Mode", "Context coverage", "Root", "Exact", "Exact delta", "Seventh exact", "Winner changes", "True-rank changes"],
        [[mode, pct(value["context_coverage"]), pct(value["metrics"]["root_accuracy"]), pct(value["metrics"]["exact_accuracy"]), fmt(value["exact_accuracy_delta_vs_default"]), pct(value["metrics"]["seventh_exact_accuracy"]), value["winner_changes_vs_default"], value["true_candidate_rank_changes_vs_default"]] for mode, value in report["key_prior_modes"].items()],
    ))
    lines.extend(["", "## Term ablations", ""])
    lines.extend(table(
        ["Ablation", "Root", "Exact", "Exact delta", "Seventh exact", "Winner changes", "Dominant-7 winner changes"],
        [[name, pct(value["metrics"]["root_accuracy"]), pct(value["metrics"]["exact_accuracy"]), fmt(value["exact_accuracy_delta"]), pct(value["metrics"]["seventh_exact_accuracy"]), value["winner_changes"], value["dominant_seventh_winner_changes"]] for name, value in report["term_ablations"].items() if name != "nonexistent_terms"],
    ))
    lines.extend(["", "Missing-tone and extra-tone ablations are not run because those penalty terms do not exist.", "", "## Candidate margins", ""])
    lines.extend(table(
        ["Quality", "Template coverage", "Winner tie rate", "Mean winner-runner", "Mean winner-true", "Mean true rank"],
        [[quality, pct(value["true_template_coverage"]), pct(value["winner_tie_rate"]), fmt(value["mean_winner_runner_up_margin"]), fmt(value["mean_winner_true_margin"]), fmt(value["mean_true_candidate_rank"])] for quality, value in report["candidate_margins_by_quality"].items()],
    ))
    inversion_summary = report["inversion_forensics"]["non_root_position_summary"]
    lines.extend(["", "## Bass and inversion findings", "", f"Across `{inversion_summary['cases']}` non-root-position representative voicings: `{inversion_summary['winner_changes_vs_root_position']}` winners changed, `{inversion_summary['wrong_root']}` had a wrong root, `{inversion_summary['right_root_wrong_quality']}` kept the root but changed quality, and `{inversion_summary['inversions_that_recover_exact_from_wrong_root_position']}` recovered an exact label that root position missed.", ""])
    lines.extend(table(
        ["True", "Inversion", "Bass", "Winner", "True rank", "Winner-true"],
        [[case["true"], case["inversion"], case["bass_note"], case["winner"]["canonical_label"], case["true_candidate_rank"] or "absent", fmt(case["winner_true_margin"])] for case in report["inversion_forensics"]["cases"]],
    ))
    lines.extend(["", "## Diminished findings", ""])
    lines.extend(table(
        ["True", "Winner", "Score", "Runner-up", "Margin"],
        [[case["true"], case["winner"]["canonical_label"], fmt(case["winner"]["score"]), case["runner_up"]["canonical_label"], fmt(case["winner_runner_up_margin"])] for case in report["diminished_forensics"]["cases"]],
    ))
    lines.extend(["", report["diminished_forensics"]["mechanism"]])
    inventory = report["template_inventory"]
    decision = report["decision_gate"]
    lines.extend([
        "", "## Template findings", "",
        f"There are `{inventory['candidate_count']}` candidates. Quality counts: `{json.dumps(inventory['quality_counts'], sort_keys=True)}`.",
        f"Required/optional tones distinguished: `{inventory['required_optional_distinction']}`. {inventory['tone_weighting']}", "",
        "## Root cause", "", report["dominant_seventh"]["primary_mechanism"], "",
        "## Decision gate", "", f"**{decision['outcome']}**: {decision['reason']}", "",
        "## Limitations", "",
    ])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def write_reports(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    # Complete 85-candidate rankings are large; the Markdown artifact is the
    # readable view, while this artifact stays compact and machine-oriented.
    json_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=JSON_REPORT)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_REPORT)
    args = parser.parse_args()
    report = build_report()
    write_reports(report, args.json, args.markdown)
    print(f"baseline: {json.dumps(report['baseline']['metrics'], sort_keys=True)}")
    print(f"dominant seventh: ties={report['dominant_seventh']['triad_seventh_ties']} triad_higher={report['dominant_seventh']['triad_strictly_higher']}")
    print(f"decision: {report['decision_gate']['outcome']}")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
