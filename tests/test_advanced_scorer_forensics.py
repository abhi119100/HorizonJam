import math
import unittest

from eval.analyze_advanced_scorer import analyze_case, build_report, rank_candidates
from eval.evaluate_oracle_classifier import load_classifier_functions, root_position_pitches


class AdvancedScorerForensicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace, _ = load_classifier_functions()

    def test_decomposed_scores_reconcile_with_source_function(self):
        ranking = rank_candidates(root_position_pitches(2, "7"), "E major", self.namespace)
        self.assertLessEqual(ranking["reconciliation_max_abs_error"], 1e-12)
        self.assertTrue(all(math.isclose(c["score"], c["source_score"], abs_tol=1e-12) for c in ranking["candidates"]))

    def test_d7_triad_and_seventh_tie_then_template_order_selects_major(self):
        case = analyze_case(2, "7", root_position_pitches(2, "7"), "E major", self.namespace)
        triad = next(c for c in case["complete_ranking"] if c["canonical_label"] == "D:maj")
        seventh = next(c for c in case["complete_ranking"] if c["canonical_label"] == "D:7")
        self.assertEqual(triad["score"], seventh["score"])
        self.assertEqual(triad["score"], 1.25)
        self.assertEqual(triad["unexplained_input_tones"], [0])
        self.assertEqual(triad["extra_tone_penalty"], 0.0)
        self.assertLess(triad["template_index"], seventh["template_index"])
        self.assertEqual(case["winner"]["canonical_label"], "D:maj")

    def test_diminished_template_is_absent(self):
        case = analyze_case(0, "dim", root_position_pitches(0, "dim"), "E major", self.namespace)
        self.assertIsNone(case["true_candidate"])
        self.assertIsNone(case["winner_true_margin"])

    def test_report_covers_rankings_contexts_ablations_and_examples(self):
        report = build_report()
        self.assertEqual(len(report["baseline"]["cases"]), 96)
        self.assertTrue(all(len(case["complete_ranking"]) == 85 for case in report["baseline"]["cases"]))
        self.assertEqual(set(report["key_prior_modes"]), {"default_e_major", "no_key_context", "matching_supported_context"})
        self.assertEqual(report["dominant_seventh"]["triad_seventh_ties"], 9)
        self.assertEqual(report["dominant_seventh"]["triad_strictly_higher"], 3)
        self.assertEqual(report["decision_gate"]["outcome"], "C. TEMPLATE_MODEL_PROBLEM")
        for label in ("D7", "G7", "Cmaj7", "Am7", "C", "Am", "Csus4", "Cdim"):
            self.assertIn(label, report["required_examples"])


if __name__ == "__main__":
    unittest.main()
