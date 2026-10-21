import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import detection
from src.dsp_chroma import (
    DEFAULT_CONFIG,
    extract_pitch_class_evidence,
    score_chroma_values,
    score_pitch_class_evidence,
)
from src.harmonic_evidence import PitchClassEvidence


class PitchClassEvidenceTests(unittest.TestCase):
    def test_configuration_rejects_unknown_or_unimplemented_modes(self):
        wav = Path(__file__).parent / "audio" / "pop.wav"
        with self.assertRaises(ValueError):
            extract_pitch_class_evidence(str(wav), {"unknown": True})
        with self.assertRaises(ValueError):
            extract_pitch_class_evidence(str(wav), {"norm": "l2"})
        with self.assertRaises(ValueError):
            extract_pitch_class_evidence(str(wav), {"harmonic_separation": True})

    def test_validation_requires_twelve_finite_values_and_valid_contract(self):
        valid = {
            "start": 0.0,
            "end": 0.1,
            "values": [0.0] * 12,
            "representation": "chroma_cqt_l1",
            "source": "librosa_chroma",
        }
        for replacement in (
            {"end": 0.0},
            {"values": [0.0] * 11},
            {"values": [0.0] * 11 + [float("nan")]},
            {"representation": ""},
            {"source": ""},
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    PitchClassEvidence(**{**valid, **replacement})

    def test_profile_scorer_is_deterministic_and_keeps_support_semantics(self):
        c_major = [0.0] * 12
        for pitch_class in (0, 4, 7):
            c_major[pitch_class] = 1.0 / 3.0

        first = score_chroma_values(c_major)
        second = score_chroma_values(c_major)

        self.assertEqual(first, second)
        self.assertEqual(first[0]["label"], "C")
        self.assertIn("normalized_support", first[0])
        self.assertNotIn("confidence", first[0])

    def test_repository_wav_is_deterministic_and_time_aligned(self):
        wav = Path(__file__).parent / "audio" / "pop.wav"

        first, first_metadata = extract_pitch_class_evidence(str(wav))
        second, second_metadata = extract_pitch_class_evidence(str(wav))

        self.assertEqual([item.to_dict() for item in first], [item.to_dict() for item in second])
        self.assertEqual(first_metadata["config"], DEFAULT_CONFIG)
        self.assertEqual(first_metadata["frame_count"], second_metadata["frame_count"])
        self.assertEqual(first[0].start, 0.0)
        self.assertLessEqual(first[-1].end, first_metadata["duration_sec"])
        self.assertTrue(all(item.end > item.start for item in first))
        nonzero = [item for item in first if sum(item.values) > 0]
        self.assertTrue(nonzero)
        self.assertTrue(all(abs(sum(item.values) - 1.0) < 1e-5 for item in nonzero))

        frames, timing = score_pitch_class_evidence(first)
        self.assertEqual(len(frames), len(first))
        self.assertIn("candidate_scoring", timing)

    def test_detection_dsp_inspection_is_opt_in_and_preserves_events(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "C", "confidence": 0.8}]
        chroma = PitchClassEvidence(
            start=0.0,
            end=1.0,
            values=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            representation="chroma_cqt_l1",
            source="librosa_chroma",
        )

        def runner(*_args, **kwargs):
            sink = kwargs.get("evidence_sink")
            if sink is not None:
                sink.update({"notes": [], "midi_notes": [], "duration": 1.0})
            return [dict(item) for item in raw]

        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", side_effect=runner):
                normal = detection.run_detection(wav.name, detector="rule_jaccard")
                with patch(
                    "src.dsp_chroma.extract_pitch_class_evidence",
                    return_value=([chroma], {"config": DEFAULT_CONFIG}),
                ):
                    inspected = detection.run_detection(
                        wav.name,
                        detector="rule_jaccard",
                        include_dsp_evidence=True,
                    )

        self.assertEqual(normal["chord_events"], inspected["chord_events"])
        self.assertNotIn("harmonic_evidence", normal)
        packet = inspected["harmonic_evidence"]
        self.assertEqual(len(packet["pitch_class_evidence"]), 1)
        self.assertEqual(packet["pitch_class_evidence"][0]["source"], "librosa_chroma")

    def test_optional_dsp_failure_preserves_symbolic_result(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "C", "confidence": 0.8}]

        def runner(*_args, **kwargs):
            sink = kwargs.get("evidence_sink")
            if sink is not None:
                sink.update({"notes": [], "midi_notes": [], "duration": 1.0})
            return [dict(item) for item in raw]

        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", side_effect=runner):
                baseline = detection.run_detection(wav.name, detector="rule_jaccard")
                with patch(
                    "src.dsp_chroma.extract_pitch_class_evidence",
                    side_effect=RuntimeError("DSP unavailable"),
                ):
                    result = detection.run_detection(
                        wav.name, detector="rule_jaccard", include_dsp_evidence=True
                    )

        self.assertEqual(result["chord_events"], baseline["chord_events"])
        self.assertTrue(any(
            "librosa_chroma unavailable" in warning
            for warning in result["harmonic_evidence"]["warnings"]
        ))


if __name__ == "__main__":
    unittest.main()
