import math
import unittest

from eval.compare_match_formulations import (
    FORMULATIONS,
    build_datasets,
    build_report,
    formulation_match,
    rank_candidates,
)
from eval.evaluate_oracle_classifier import load_classifier_functions, root_position_pitches


class MatchFormulationBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace, _ = load_classifier_functions()

    def test_match_values_for_d7_input_against_d_major_template(self):
        observed = {0, 2, 6, 9}
        triad = {2, 6, 9}
        baseline, _ = formulation_match(observed, triad, FORMULATIONS["baseline_template_coverage"])
        f1, _ = formulation_match(observed, triad, FORMULATIONS["bidirectional_f1"])
        jaccard, _ = formulation_match(observed, triad, FORMULATIONS["jaccard"])
        penalty, _ = formulation_match(observed, triad, FORMULATIONS["unexplained_penalty_0.10"])
        self.assertEqual(baseline, 1.0)
        self.assertTrue(math.isclose(f1, 6 / 7))
        self.assertEqual(jaccard, 0.75)
        self.assertEqual(penalty, 0.975)

    def test_specificity_rule_changes_only_the_d7_tie_winner(self):
        pitches = root_position_pitches(2, "7")
        baseline = rank_candidates(pitches, FORMULATIONS["baseline_template_coverage"], self.namespace)
        specificity = rank_candidates(pitches, FORMULATIONS["specificity_tie_rule"], self.namespace)
        self.assertEqual(baseline[0]["canonical_label"], "D:maj")
        self.assertEqual(specificity[0]["canonical_label"], "D:7")
        self.assertEqual(baseline[0]["score"], specificity[0]["score"])

    def test_dataset_sizes_match_frozen_oracle_and_robustness_corpora(self):
        datasets = build_datasets()
        self.assertEqual({name: len(cases) for name, cases in datasets.items()}, {
            "complete": 96,
            "omitted_fifth": 96,
            "omitted_root": 96,
            "seventh_without_fifth": 36,
            "duplicated_tones": 192,
            "inversions": 228,
            "extra_tone": 12,
        })

    def test_report_reproduces_baseline_and_covers_required_formulations(self):
        report = build_report()
        self.assertEqual(report["baseline_reproduction"]["winner_mismatches"], 0)
        self.assertLessEqual(report["baseline_reproduction"]["max_candidate_score_error"], 1e-12)
        self.assertEqual(set(report["results"]), set(FORMULATIONS))
        self.assertEqual(len(report["seventh_comparison"]), 36)
        self.assertIn(report["decision_gate"]["outcome"].split(". ")[0], {"A", "B", "C", "D", "E"})


if __name__ == "__main__":
    unittest.main()
