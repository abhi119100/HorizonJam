"""Deterministic oracle benchmark for HorizonJam's symbolic classifiers.

This benchmark extracts the exact classifier function definitions from
``src/chord_detector.py`` without importing that audio-heavy module.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_SOURCE = ROOT / "src" / "chord_detector.py"
HYBRID_SOURCE = ROOT / "src" / "hybrid_chord_detector.py"
JSON_REPORT = ROOT / "eval" / "oracle_classifier_report.json"
MARKDOWN_REPORT = ROOT / "eval" / "oracle_classifier_report.md"

ROOT_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
ROOT_TO_PC = {name: index for index, name in enumerate(ROOT_NAMES)}
FLAT_TO_SHARP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
ENHARMONIC_PAIRS = tuple(FLAT_TO_SHARP.items())

QUALITIES = {
    "maj": {"intervals": (0, 4, 7), "suffix": "", "label": "major"},
    "min": {"intervals": (0, 3, 7), "suffix": "m", "label": "minor"},
    "7": {"intervals": (0, 4, 7, 10), "suffix": "7", "label": "dominant seventh"},
    "maj7": {"intervals": (0, 4, 7, 11), "suffix": "maj7", "label": "major seventh"},
    "min7": {"intervals": (0, 3, 7, 10), "suffix": "m7", "label": "minor seventh"},
    "sus2": {"intervals": (0, 2, 7), "suffix": "sus2", "label": "suspended 2"},
    "sus4": {"intervals": (0, 5, 7), "suffix": "sus4", "label": "suspended 4"},
    "dim": {"intervals": (0, 3, 6), "suffix": "dim", "label": "diminished"},
}

EXTRACTED_FUNCTIONS = (
    "midi_to_note_name",
    "get_key_prior_weights",
    "score_chord_candidate",
    "get_chord_templates",
    "identify_chord_from_pitches_advanced",
    "identify_chord_from_pitches",
)


def load_classifier_functions(source_path: Path = CLASSIFIER_SOURCE) -> tuple[dict[str, Any], dict[str, str]]:
    """Load exact function bodies without importing unrelated audio modules."""
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    nodes = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in EXTRACTED_FUNCTIONS
    }
    missing = sorted(set(EXTRACTED_FUNCTIONS) - set(nodes))
    if missing:
        raise RuntimeError(f"Missing classifier functions in {source_path}: {missing}")

    namespace: dict[str, Any] = {
        "Dict": Dict,
        "List": List,
        "Optional": Optional,
        "Tuple": Tuple,
    }
    selected = [nodes[name] for name in EXTRACTED_FUNCTIONS]
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, str(source_path), "exec"), namespace)

    hashes = {
        name: hashlib.sha256(ast.get_source_segment(source, nodes[name]).encode("utf-8")).hexdigest()
        for name in EXTRACTED_FUNCTIONS
    }
    hashes["source_file"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return namespace, hashes


def read_hybrid_rule_confidence(source_path: Path = HYBRID_SOURCE) -> dict[str, Any]:
    """Read the downstream rule weight without importing the hybrid detector."""
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "rule_confidence" for target in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                return {
                    "value": float(node.value.value),
                    "source": "src/hybrid_chord_detector.py",
                    "line": node.lineno,
                    "source_hash_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                }
    raise RuntimeError(f"Could not locate constant rule_confidence in {source_path}")


def chord_label(root_pc: int, quality: str) -> str:
    return f"{ROOT_NAMES[root_pc]}{QUALITIES[quality]['suffix']}"


def root_position_pitches(root_pc: int, quality: str) -> list[int]:
    root_midi = 60 + root_pc
    return [root_midi + interval for interval in QUALITIES[quality]["intervals"]]


def inversion_pitches(root_pc: int, quality: str, inversion: int) -> list[int]:
    pitches = root_position_pitches(root_pc, quality)
    return pitches[inversion:] + [pitch + 12 for pitch in pitches[:inversion]]


def parse_prediction(label: str) -> tuple[Optional[int], Optional[str]]:
    if not isinstance(label, str) or label in {"Unknown", "Silence", "N"}:
        return None, None
    normalized_label = label.strip().replace("\u266f", "#").replace("\u266d", "b")
    match = re.fullmatch(r"([A-G](?:#|b)?)(.*)", normalized_label)
    if not match:
        return None, None
    root_name, suffix = match.groups()
    root_name = FLAT_TO_SHARP.get(root_name, root_name)
    root_pc = ROOT_TO_PC.get(root_name)
    suffix_to_quality = {
        "": "maj", "m": "min", "7": "7", "maj7": "maj7",
        "m7": "min7", "min7": "min7", "sus2": "sus2",
        "sus4": "sus4", "dim": "dim", "o": "dim", "\u00b0": "dim",
    }
    return root_pc, suffix_to_quality.get(suffix)


def classify_case(
    classifier_name: str,
    classifier: Any,
    root_pc: int,
    quality: str,
    pitches: list[int],
) -> dict[str, Any]:
    if classifier_name == "advanced":
        prediction = classifier(pitches, bass_pitch=min(pitches))
    else:
        prediction = classifier(pitches)
    predicted_root, predicted_quality = parse_prediction(prediction)
    root_correct = predicted_root == root_pc
    quality_correct = predicted_quality == quality
    exact = root_correct and quality_correct
    tags: list[str] = []
    if predicted_root is None or predicted_quality is None:
        tags.append("no_classification")
    if not root_correct:
        tags.append("wrong_root")
    if root_correct and not quality_correct:
        tags.append("right_root_wrong_quality")
    if quality in {"7", "maj7", "min7"} and predicted_quality in {"maj", "min"}:
        tags.extend(("seventh_collapse", "triad_collapse"))
    if quality in {"sus2", "sus4", "dim"} and predicted_quality in {"maj", "min"}:
        tags.append("triad_collapse")
    return {
        "true": chord_label(root_pc, quality),
        "true_root": ROOT_NAMES[root_pc],
        "true_quality": quality,
        "pitches": pitches,
        "predicted": prediction,
        "predicted_root": ROOT_NAMES[predicted_root] if predicted_root is not None else None,
        "predicted_quality": predicted_quality,
        "root_correct": root_correct,
        "quality_correct": quality_correct,
        "exact_correct": exact,
        "failure_tags": sorted(set(tags)),
    }


def metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(cases)
    return {
        "cases": count,
        "root_accuracy": sum(case["root_correct"] for case in cases) / count if count else None,
        "quality_accuracy": sum(case["quality_correct"] for case in cases) / count if count else None,
        "exact_accuracy": sum(case["exact_correct"] for case in cases) / count if count else None,
    }


def grouped_metrics(cases: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        groups[str(case[field])].append(case)
    return {key: metrics(groups[key]) for key in sorted(groups)}


def confusion_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = Counter((case["true"], case["predicted"]) for case in cases if not case["exact_correct"])
    tags = Counter(tag for case in cases for tag in case["failure_tags"])
    quality_pairs = Counter(
        (case["true_quality"], case["predicted_quality"] or "unparsed")
        for case in cases if not case["quality_correct"]
    )
    return {
        "failure_tags": dict(sorted(tags.items())),
        "quality_collapses": [
            {"true_quality": true, "predicted_quality": predicted, "count": count}
            for (true, predicted), count in sorted(quality_pairs.items())
        ],
        "chord_confusions": [
            {"true": true, "predicted": predicted, "count": count}
            for (true, predicted), count in sorted(pairs.items())
        ],
        "enharmonic_mismatch": {
            "count": 0,
            "note": "Not observable at the MIDI-integer classifier boundary; spelling is erased before classification.",
        },
        "fallback_misclassification": {
            "count": None,
            "note": "The public classifier returns only a label and does not expose which return branch fired.",
        },
    }


def evaluate_robustness(name: str, classifier: Any) -> dict[str, Any]:
    inversion_cases: list[dict[str, Any]] = []
    duplicate_cases: list[dict[str, Any]] = []
    omitted_fifth_cases: list[dict[str, Any]] = []
    omitted_root_cases: list[dict[str, Any]] = []
    seventh_without_fifth_cases: list[dict[str, Any]] = []
    for quality, definition in QUALITIES.items():
        for root_pc in range(12):
            base = root_position_pitches(root_pc, quality)
            base_case = classify_case(name, classifier, root_pc, quality, base)
            for inversion in range(1, len(definition["intervals"])):
                case = classify_case(name, classifier, root_pc, quality, inversion_pitches(root_pc, quality, inversion))
                case["inversion"] = inversion
                case["matches_root_position_prediction"] = case["predicted"] == base_case["predicted"]
                inversion_cases.append(case)
            for duplicate_index, pitches in enumerate((base + [base[0] + 12], [base[0], base[-1], base[0] + 12] + base[1:])):
                case = classify_case(name, classifier, root_pc, quality, pitches)
                case["variant"] = duplicate_index + 1
                case["matches_root_position_prediction"] = case["predicted"] == base_case["predicted"]
                duplicate_cases.append(case)
            omitted_fifth_cases.append(classify_case(name, classifier, root_pc, quality, [p for i, p in enumerate(base) if i != 2]))
            omitted_root_cases.append(classify_case(name, classifier, root_pc, quality, base[1:]))
            if quality in {"7", "maj7", "min7"}:
                seventh_without_fifth_cases.append(
                    classify_case(name, classifier, root_pc, quality, [base[0], base[1], base[3]])
                )
    inversion_metrics = metrics(inversion_cases)
    inversion_metrics["prediction_invariance_rate"] = sum(case["matches_root_position_prediction"] for case in inversion_cases) / len(inversion_cases)
    duplicate_metrics = metrics(duplicate_cases)
    duplicate_metrics["prediction_invariance_rate"] = sum(case["matches_root_position_prediction"] for case in duplicate_cases) / len(duplicate_cases)
    return {
        "inversions": {"metrics": inversion_metrics, "cases": inversion_cases},
        "duplicated_notes": {"metrics": duplicate_metrics, "cases": duplicate_cases},
        "omitted_fifth": {"metrics": metrics(omitted_fifth_cases), "cases": omitted_fifth_cases},
        "omitted_root": {"metrics": metrics(omitted_root_cases), "cases": omitted_root_cases},
        "seventh_without_fifth": {"metrics": metrics(seventh_without_fifth_cases), "cases": seventh_without_fifth_cases},
    }


def evaluate_classifier(name: str, classifier: Any) -> dict[str, Any]:
    cases = [
        classify_case(name, classifier, root_pc, quality, root_position_pitches(root_pc, quality))
        for quality in QUALITIES
        for root_pc in range(12)
    ]
    return {
        "headline": metrics(cases),
        "major_minor_only": metrics([case for case in cases if case["true_quality"] in {"maj", "min"}]),
        "seventh_only": metrics([case for case in cases if case["true_quality"] in {"7", "maj7", "min7"}]),
        "per_root": grouped_metrics(cases, "true_root"),
        "per_quality": grouped_metrics(cases, "true_quality"),
        "confusion": confusion_summary(cases),
        "cases": cases,
        "robustness": evaluate_robustness(name, classifier),
    }


def evaluate_enharmonics(classifiers: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for flat, sharp in ENHARMONIC_PAIRS:
        root_pc = ROOT_TO_PC[sharp]
        for quality in QUALITIES:
            pitches = root_position_pitches(root_pc, quality)
            predictions = {
                name: (classifier(pitches, bass_pitch=min(pitches)) if name == "advanced" else classifier(pitches))
                for name, classifier in classifiers.items()
            }
            cases.append({
                "flat_name": f"{flat}{QUALITIES[quality]['suffix']}",
                "sharp_name": f"{sharp}{QUALITIES[quality]['suffix']}",
                "midi_pitches": pitches,
                "predictions": predictions,
                "equivalent_input": True,
            })
    return {
        "classifier_input": "ordered MIDI integer pitches; spelling is not representable",
        "spelling_representable": False,
        "cases": cases,
        "equivalent_behavior_rate": 1.0,
        "interpretation": "Enharmonic aliases collapse to the same MIDI input before either classifier runs; output spelling robustness is not tested by this interface.",
    }


def choose_decision(simple: dict[str, Any], advanced: dict[str, Any]) -> dict[str, str]:
    simple_exact = simple["headline"]["exact_accuracy"]
    advanced_exact = advanced["headline"]["exact_accuracy"]
    if simple_exact >= 0.75:
        outcome = "A"
        reason = "The simple classifier is mostly sound on complete oracle inputs."
    elif advanced_exact >= 0.60 and advanced_exact - simple_exact >= 0.15:
        outcome = "B"
        reason = "The existing advanced scorer materially outperforms the active simple classifier."
    elif simple_exact < 0.50 and advanced_exact < 0.50:
        outcome = "C"
        reason = "Both classifiers fail more than half of complete oracle cases."
    else:
        outcome = "D"
        reason = "Results are mixed and need another isolated experiment before activation or replacement."
    return {"outcome": outcome, "reason": reason}


def build_report() -> dict[str, Any]:
    namespace, hashes = load_classifier_functions()
    classifiers = {
        "active_simple": namespace["identify_chord_from_pitches"],
        "advanced": namespace["identify_chord_from_pitches_advanced"],
    }
    results = {name: evaluate_classifier(name, classifier) for name, classifier in classifiers.items()}
    hybrid_confidence = read_hybrid_rule_confidence()
    return {
        "schema_version": "oracle-chord-classifier-v1",
        "evidence_level": "L2 harmony / symbolic classifier isolation",
        "command": "python eval/evaluate_oracle_classifier.py",
        "classifier_boundary": {
            "source": "src/chord_detector.py",
            "active_simple": "identify_chord_from_pitches(pitches) -> chord label string",
            "advanced": "identify_chord_from_pitches_advanced(pitches, bass_pitch=None, detected_key='E major') -> chord label string",
            "input": "MIDI integer pitches; simple classifier converts them to an unordered unique pitch-name set; advanced classifier converts them to pitch classes and uses bass plus its default E-major prior",
            "normalization": "librosa-compatible C-major sharp spelling for integer MIDI notes",
            "output": "single internal chord label; neither function emits confidence or alternatives",
            "loader": "Exact AST-extracted classifier and local MIDI note-name function bodies",
            "source_hashes_sha256": hashes,
        },
        "vocabulary": {
            "roots": list(ROOT_NAMES),
            "qualities": list(QUALITIES),
            "headline_cases_per_classifier": len(ROOT_NAMES) * len(QUALITIES),
            "scope": "All listed qualities are present in current simple maps, advanced templates, or the existing synthetic vocabulary and are treated as intended support.",
        },
        "results": results,
        "enharmonic_robustness": evaluate_enharmonics(classifiers),
        "confidence": {
            "classifier_emits_confidence": False,
            "classifier_output": "label only",
            "hybrid_rule_confidence_added_later": hybrid_confidence["value"],
            "hybrid_rule_confidence_source": hybrid_confidence,
            "semantic_meaning": "A fixed downstream rule weight, not a classifier probability or calibrated correctness estimate.",
            "discriminative_at_classifier_boundary": False,
        },
        "decision_gate": choose_decision(results["active_simple"], results["advanced"]),
        "limitations": [
            "No audio, BasicPitch, segmentation, temporal decoding, retrieval, or tutor logic is exercised.",
            "Enharmonic input spelling cannot be represented by the MIDI-integer classifier interface.",
            "The advanced scorer is evaluated offline with its existing default E-major prior and is not activated in production.",
            "Classifier return branches and candidate score margins are not exposed by the current public functions.",
        ],
    }


def pct(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Oracle Chord Classifier Benchmark v1", "",
        "Fresh deterministic L2 evidence generated by `python eval/evaluate_oracle_classifier.py`.", "",
        "## Classifier boundary", "",
        f"- Active: `{report['classifier_boundary']['active_simple']}`",
        f"- Experimental: `{report['classifier_boundary']['advanced']}`",
        f"- Input: {report['classifier_boundary']['input']}",
        f"- Loader: {report['classifier_boundary']['loader']}", "",
        "## Headline results", "",
    ]
    summary_rows = []
    for name, result in report["results"].items():
        metric = result["headline"]
        summary_rows.append([name, metric["cases"], pct(metric["root_accuracy"]), pct(metric["quality_accuracy"]), pct(metric["exact_accuracy"])])
    lines.extend(markdown_table(["Classifier", "Cases", "Root", "Quality", "Exact"], summary_rows))

    for name, result in report["results"].items():
        lines.extend(["", f"## {name.replace('_', ' ').title()} per-quality", ""])
        lines.extend(markdown_table(
            ["Quality", "Cases", "Root", "Quality", "Exact"],
            [[quality, values["cases"], pct(values["root_accuracy"]), pct(values["quality_accuracy"]), pct(values["exact_accuracy"])] for quality, values in result["per_quality"].items()],
        ))
        lines.extend(["", f"## {name.replace('_', ' ').title()} per-root", ""])
        lines.extend(markdown_table(
            ["Root", "Cases", "Root", "Quality", "Exact"],
            [[root, values["cases"], pct(values["root_accuracy"]), pct(values["quality_accuracy"]), pct(values["exact_accuracy"])] for root, values in result["per_root"].items()],
        ))
        lines.extend(["", f"## {name.replace('_', ' ').title()} complete-input confusion matrix", ""])
        lines.extend(markdown_table(
            ["True", "Predicted", "Root correct", "Quality correct", "Exact", "Failure tags"],
            [[case["true"], case["predicted"], case["root_correct"], case["quality_correct"], case["exact_correct"], ", ".join(case["failure_tags"]) or "-"] for case in result["cases"]],
        ))
        lines.extend(["", f"## {name.replace('_', ' ').title()} robustness", ""])
        lines.extend(markdown_table(
            ["Condition", "Cases", "Root", "Quality", "Exact", "Same prediction as root position"],
            [[condition, values["metrics"]["cases"], pct(values["metrics"]["root_accuracy"]), pct(values["metrics"]["quality_accuracy"]), pct(values["metrics"]["exact_accuracy"]), pct(values["metrics"].get("prediction_invariance_rate"))] for condition, values in result["robustness"].items()],
        ))
        lines.extend(["", f"Failure tags: `{json.dumps(result['confusion']['failure_tags'], sort_keys=True)}`"])

    enharmonic = report["enharmonic_robustness"]
    confidence = report["confidence"]
    decision = report["decision_gate"]
    lines.extend([
        "", "## Enharmonic robustness", "",
        f"- Interface: {enharmonic['classifier_input']}",
        f"- Spelling representable: `{enharmonic['spelling_representable']}`",
        f"- Interpretation: {enharmonic['interpretation']}", "",
        "## Confidence", "",
        f"- Classifier emits confidence: `{confidence['classifier_emits_confidence']}`",
        f"- Downstream hybrid rule weight: `{confidence['hybrid_rule_confidence_added_later']}`",
        f"- Meaning: {confidence['semantic_meaning']}", "",
        "## Decision gate", "",
        f"**Outcome {decision['outcome']}.** {decision['reason']}", "",
        "## Limitations", "",
    ])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def write_reports(report: dict[str, Any], json_path: Path = JSON_REPORT, markdown_path: Path = MARKDOWN_REPORT) -> None:
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=JSON_REPORT)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_REPORT)
    args = parser.parse_args()
    report = build_report()
    write_reports(report, args.json, args.markdown)
    for name, result in report["results"].items():
        headline = result["headline"]
        print(f"{name}: root={pct(headline['root_accuracy'])} quality={pct(headline['quality_accuracy'])} exact={pct(headline['exact_accuracy'])}")
    print(f"decision: {report['decision_gate']['outcome']} - {report['decision_gate']['reason']}")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
