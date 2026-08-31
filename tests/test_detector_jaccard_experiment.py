import math
import tempfile
import unittest
from unittest.mock import patch

import detection
from eval.evaluate_oracle_classifier import load_classifier_functions


class JaccardProductionExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace, _ = load_classifier_functions()

    def test_coverage_remains_the_default_match_formulation(self):
        observed = {0, 2, 6, 9}
        template = {"root": 2, "pcs": {2, 6, 9}, "quality": "maj"}
        scorer = self.namespace["score_chord_candidate"]
        baseline = scorer(observed, 2, "E major", template)
        explicit = scorer(observed, 2, "E major", template, "coverage")
        self.assertEqual(baseline, explicit)
        self.assertEqual(baseline, 1.25)

    def test_jaccard_penalizes_unexplained_seventh_tone(self):
        observed = {0, 2, 6, 9}
        template = {"root": 2, "pcs": {2, 6, 9}, "quality": "maj"}
        score = self.namespace["score_chord_candidate"](
            observed, 2, "E major", template, "jaccard"
        )
        self.assertTrue(math.isclose(score, 1.0))

    def test_advanced_jaccard_recovers_representative_dominant_sevenths(self):
        classifier = self.namespace["identify_chord_from_pitches_advanced"]
        self.assertEqual(
            classifier([62, 66, 69, 72], bass_pitch=62, match_formulation="jaccard"),
            "D7",
        )
        self.assertEqual(
            classifier([67, 71, 74, 77], bass_pitch=67, match_formulation="jaccard"),
            "G7",
        )

    def test_rule_jaccard_routes_through_experimental_classifier(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "G7", "confidence": None}]
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", return_value=raw) as run_hybrid:
                result = detection.run_detection(wav.name, detector="rule_jaccard")

        run_hybrid.assert_called_once_with(
            wav.name,
            use_viterbi=True,
            classifier_mode="advanced_jaccard",
            runtime_trace=None,
        )
        self.assertEqual(result["detector_used"], "rule_jaccard")
        self.assertEqual(result["chord_events"][0]["source_detector"], "rule_jaccard")

    def test_normalized_contract_is_preserved(self):
        raw = [
            {"start": 1.0, "end": 2.0, "chord": "G7", "confidence": None},
            {"start": 0.0, "end": 1.0, "chord": "C", "confidence": None},
        ]
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", return_value=raw):
                result = detection.run_detection(wav.name, detector="rule_jaccard")

        events = result["chord_events"]
        self.assertEqual([event["chord"] for event in events], ["C", "G7"])
        self.assertTrue(all(event["end"] > event["start"] for event in events))
        self.assertTrue(all(events[i]["end"] <= events[i + 1]["start"] for i in range(len(events) - 1)))


if __name__ == "__main__":
    unittest.main()
