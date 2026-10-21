import unittest

from src.evidence_summary import build_evidence_summaries


def packet(notes=None, chroma=None, warnings=None):
    return {
        "notes": notes or [],
        "pitch_class_evidence": chroma or [],
        "warnings": warnings or [],
    }


def chroma_frame(values, start=0.0, end=1.0):
    return {"start": start, "end": end, "values": values, "source": "librosa_chroma"}


class EvidenceSummaryTests(unittest.TestCase):
    def test_exact_symbolic_and_dsp_agreement_is_strong_and_musical(self):
        values = [0.0] * 12
        for pitch_class in (2, 6, 9, 0):
            values[pitch_class] = 0.25
        notes = [
            {"start": 0.0, "end": 1.0, "pitch_class": pitch_class}
            for pitch_class in (2, 6, 9, 0)
        ]

        summary = build_evidence_summaries(
            [{"start": 0.0, "end": 1.0, "chord": "D7", "source_detector": "rule_jaccard"}],
            packet(notes, [chroma_frame(values)]),
        )[0]

        self.assertEqual(summary.strength, "STRONG_AGREEMENT")
        self.assertEqual(summary.agreement, "SYMBOLIC_DSP_EXACT")
        self.assertEqual(summary.observed_notes, ["C", "D", "F#", "A"])
        self.assertEqual(summary.harmonic_candidate, "D7")
        self.assertNotIn("confidence", summary.short_explanation.lower())

    def test_disagreement_is_mixed_without_changing_symbolic_chord(self):
        values = [0.0] * 12
        for pitch_class in (0, 4, 7):
            values[pitch_class] = 1 / 3

        summary = build_evidence_summaries(
            [{"start": 0.0, "end": 1.0, "chord": "D7", "source_detector": "rule_jaccard"}],
            packet(chroma=[chroma_frame(values)]),
        )[0]

        self.assertEqual(summary.chord, "D7")
        self.assertEqual(summary.harmonic_candidate, "C")
        self.assertEqual(summary.strength, "MIXED_EVIDENCE")

    def test_absent_dsp_is_limited_and_never_exposes_raw_values(self):
        summary = build_evidence_summaries(
            [{"start": 0.0, "end": 1.0, "chord": "Am", "source_detector": "hybrid"}],
            packet(),
        )[0]

        payload = summary.to_dict()
        self.assertEqual(summary.strength, "LIMITED_EVIDENCE")
        self.assertIsNone(summary.harmonic_candidate)
        self.assertNotIn("values", payload)
        self.assertNotIn("score", payload)

    def test_warning_caps_exact_agreement_at_partial(self):
        values = [0.0] * 12
        for pitch_class in (0, 4, 7):
            values[pitch_class] = 1 / 3

        summary = build_evidence_summaries(
            [{"start": 0.0, "end": 1.0, "chord": "C", "source_detector": "hybrid"}],
            packet(chroma=[chroma_frame(values)], warnings=["audio repair applied"]),
        )[0]

        self.assertEqual(summary.strength, "PARTIAL_AGREEMENT")
        self.assertEqual(summary.warnings, ["audio repair applied"])


if __name__ == "__main__":
    unittest.main()
