import unittest

from eval.evaluate_readiness_verifier import evaluate
from tutor_evidence import verify_and_repair_response


class TutorCounterexampleTests(unittest.TestCase):
    def test_frozen_counterexamples_remove_assertions_and_preserve_useful_advice(self):
        for case in evaluate()["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["case_passed"], case["verification"])

    def test_hedge_substrings_do_not_count(self):
        context = {"assessment": {"requires_uncertainty_language": True},
                   "performance_evidence": {"chord_events": []}, "retrieval": {"evidence": []}}
        result = verify_and_repair_response("Maybe practice someday.", context)
        self.assertIn("added_uncertainty_caveat", result["repairs"])

    def test_strong_evidence_preserves_observation(self):
        context = {"assessment": {"requires_uncertainty_language": False},
                   "performance_evidence": {"chord_events": [{"chord": "D7"}]}, "retrieval": {"evidence": []}}
        result = verify_and_repair_response("You are playing D7. Practice slowly.", context)
        self.assertEqual(result["final_response"], "You are playing D7. Practice slowly.")


if __name__ == "__main__":
    unittest.main()
