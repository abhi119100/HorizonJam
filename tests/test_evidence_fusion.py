import unittest

from src.chord_labels import decompose_chord_label
from src.evidence_fusion import fuse_ranked_sources


class ChordDecompositionTests(unittest.TestCase):
    def test_supported_vocabularies_share_canonical_structure(self):
        plain = decompose_chord_label("D7")
        external = decompose_chord_label("D:dominant seventh")

        self.assertEqual(plain, external)
        self.assertEqual(plain["root"], "D")
        self.assertEqual(plain["quality"], "dominant7")
        self.assertEqual(plain["pitch_class_set"], [0, 2, 6, 9])

    def test_unsupported_detail_is_not_inferred(self):
        parts = decompose_chord_label("C:add9")

        self.assertEqual(parts["status"], "unmapped")
        self.assertIsNone(parts["quality"])
        self.assertEqual(parts["pitch_class_set"], [])


class EvidenceFusionTests(unittest.TestCase):
    def test_agreement_merges_provenance_and_ranks_true_alternative(self):
        result = fuse_ranked_sources(0.0, 1.0, {
            "rule_jaccard": [{"label": "C", "normalized_support": 1.0}],
            "librosa_chroma": [
                {"label": "C:maj", "normalized_support": 0.9},
                {"label": "Am", "normalized_support": 0.7},
            ],
        })

        self.assertEqual(result.winner.label, "C")
        self.assertEqual(result.winner.evidence_sources, ["librosa_chroma", "rule_jaccard"])
        self.assertEqual(result.candidates[1].label, "Am")
        self.assertEqual(result.agreement, "agreement_high")
        self.assertIn("not probability", result.winner.metadata["score_semantics"])

    def test_disagreement_is_deterministic_and_preserved(self):
        sources = {
            "rule_jaccard": [{"label": "Dsus2", "normalized_support": 1.0}],
            "librosa_chroma": [
                {"label": "Asus4", "normalized_support": 0.99},
                {"label": "Dsus2", "normalized_support": 0.97},
            ],
        }

        first = fuse_ranked_sources(0.0, 1.0, sources)
        second = fuse_ranked_sources(0.0, 1.0, sources)

        self.assertEqual(first, second)
        self.assertTrue(first.source_disagreement)
        self.assertEqual(first.winner.label, "Dsus2")
        self.assertEqual(first.agreement, "agreement_mixed")

    def test_rejected_direct_model_has_zero_weight(self):
        result = fuse_ranked_sources(0.0, 1.0, {
            "rule_jaccard": [{"label": "C", "normalized_support": 1.0}],
            "librosa_chroma": [{"label": "C", "normalized_support": 0.9}],
            "lv_chordia": [{"label": "G", "normalized_support": 1.0}],
        })

        self.assertEqual(result.winner.label, "C")
        self.assertNotIn("lv_chordia", result.winner.evidence_sources)
        self.assertEqual(result.active_source_count, 2)

    def test_support_validation_rejects_probability_like_overflow(self):
        with self.assertRaises(ValueError):
            fuse_ranked_sources(0.0, 1.0, {
                "rule_jaccard": [{"label": "C", "normalized_support": 1.1}],
            })

    def test_empty_and_single_source_inputs_are_explicit(self):
        empty = fuse_ranked_sources(0.0, 1.0, {})
        single = fuse_ranked_sources(0.0, 1.0, {
            "rule_jaccard": [{"label": "C", "normalized_support": 1.0}],
        })

        self.assertIsNone(empty.winner)
        self.assertEqual(empty.agreement, "agreement_low")
        self.assertEqual(single.winner.label, "C")
        self.assertEqual(single.active_source_count, 1)

    def test_invalid_source_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            fuse_ranked_sources(
                0.0,
                1.0,
                {"rule_jaccard": [{"label": "C", "normalized_support": 1.0}]},
                {"rule_jaccard": -1.0},
            )


if __name__ == "__main__":
    unittest.main()
