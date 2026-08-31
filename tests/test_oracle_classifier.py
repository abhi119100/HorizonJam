import unittest

from eval.evaluate_oracle_classifier import (
    QUALITIES,
    build_report,
    load_classifier_functions,
    parse_prediction,
    root_position_pitches,
)


class OracleClassifierBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        namespace, _ = load_classifier_functions()
        cls.simple = staticmethod(namespace["identify_chord_from_pitches"])

    def test_oracle_vocabulary_covers_eight_qualities_and_all_roots(self):
        report = build_report()
        self.assertEqual(report["vocabulary"]["headline_cases_per_classifier"], 96)
        self.assertEqual(set(report["vocabulary"]["qualities"]), set(QUALITIES))
        self.assertEqual(report["results"]["active_simple"]["headline"]["cases"], 96)
        self.assertEqual(report["results"]["advanced"]["headline"]["cases"], 96)

    def test_active_simple_is_order_and_duplicate_invariant(self):
        pitches = root_position_pitches(0, "maj")
        expected = self.simple(pitches)
        self.assertEqual(self.simple(list(reversed(pitches))), expected)
        self.assertEqual(self.simple(pitches + [pitches[0] + 12]), expected)

    def test_metric_parser_treats_unicode_and_ascii_accidentals_equally(self):
        self.assertEqual(parse_prediction("C\u266fmaj7"), parse_prediction("C#maj7"))
        self.assertEqual(parse_prediction("B\u266dm7"), parse_prediction("Bbm7"))

    @unittest.expectedFailure
    def test_active_simple_should_recognize_dominant_sevenths(self):
        self.assertEqual(self.simple([62, 66, 69, 72]), "D7")
        self.assertEqual(self.simple([67, 71, 74, 77]), "G7")

    @unittest.expectedFailure
    def test_active_simple_should_recognize_all_major_roots(self):
        expected = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
        actual = tuple(self.simple(root_position_pitches(root, "maj")) for root in range(12))
        self.assertEqual(actual, expected)

    @unittest.expectedFailure
    def test_active_simple_should_recognize_all_minor_roots(self):
        expected = tuple(f"{root}m" for root in ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"))
        actual = tuple(self.simple(root_position_pitches(root, "min")) for root in range(12))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
