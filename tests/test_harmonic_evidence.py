import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import detection
from src.chord_detector import parse_midi_notes
from src.harmonic_evidence import (
    ChordHypothesis,
    HarmonicEvidencePacket,
    NoteEvidence,
    basic_pitch_event_to_note_evidence,
    compare_note_evidence,
    hypothesis_to_normalized_event,
    normalized_event_to_hypothesis,
    notes_to_evidence,
    to_note_evidence,
)


class NoteEvidenceTests(unittest.TestCase):
    def test_basic_pitch_event_adapter_preserves_direct_evidence(self):
        event = (0.1, 0.8, 66, 0.725, [0, 1, -1])

        evidence = basic_pitch_event_to_note_evidence(event)

        self.assertEqual((evidence.start, evidence.end), (0.1, 0.8))
        self.assertEqual((evidence.pitch, evidence.pitch_class), (66, 6))
        self.assertEqual(evidence.velocity_or_amplitude, 0.725)
        self.assertIsNone(evidence.confidence)
        self.assertEqual(evidence.source, "basic_pitch")
        self.assertEqual(evidence.metadata["pitch_bends"], [0, 1, -1])
        self.assertEqual(
            evidence.metadata["value_semantics"], "basic_pitch_amplitude"
        )

    def test_direct_and_midi_comparison_is_deterministic(self):
        direct = [
            basic_pitch_event_to_note_evidence((0.1, 0.8, 66, 0.725, None)),
            basic_pitch_event_to_note_evidence((1.0, 1.5, 69, 0.5, None)),
        ]
        midi = [
            to_note_evidence(
                {"start": 0.101, "end": 0.799, "pitch": 66, "velocity": 92},
                "basic_pitch",
            ),
            to_note_evidence(
                {"start": 1.002, "end": 1.499, "pitch": 69, "velocity": 64},
                "basic_pitch",
            ),
        ]

        first = compare_note_evidence(direct, midi)
        second = compare_note_evidence(direct, midi)

        self.assertEqual(first, second)
        self.assertEqual(first["matched_note_count"], 2)
        self.assertEqual(first["direct_only_indices"], [])
        self.assertEqual(first["midi_only_indices"], [])
        self.assertTrue(first["ordering_equal"])

    def test_parsed_note_adapter_preserves_current_values(self):
        parsed = {
            "start": 0.25,
            "end": 0.75,
            "pitch": 62,
            "velocity": 91,
            "duration": 0.5,
        }

        evidence = to_note_evidence(parsed, source="basic_pitch")

        self.assertEqual(evidence.start, parsed["start"])
        self.assertEqual(evidence.end, parsed["end"])
        self.assertEqual(evidence.pitch, parsed["pitch"])
        self.assertEqual(evidence.pitch_class, 2)
        self.assertEqual(evidence.octave, 4)
        self.assertEqual(evidence.velocity_or_amplitude, parsed["velocity"])
        self.assertIsNone(evidence.confidence)
        self.assertEqual(evidence.source, "basic_pitch")
        self.assertEqual(evidence.metadata, {"parsed_duration": 0.5})

    def test_current_midi_fixture_adapts_without_note_loss(self):
        midi_path = Path(__file__).with_name("test11.mid")
        parsed, duration = parse_midi_notes(str(midi_path))

        adapted = notes_to_evidence(parsed, source="basic_pitch")

        self.assertGreater(duration, 0)
        self.assertGreater(len(parsed), 0)
        self.assertEqual(len(adapted), len(parsed))
        for raw, evidence in zip(parsed, adapted):
            self.assertEqual(
                (evidence.start, evidence.end, evidence.pitch),
                (raw["start"], raw["end"], raw["pitch"]),
            )

    def test_validation_rejects_invalid_note_values(self):
        valid = {
            "start": 0.0,
            "end": 1.0,
            "pitch": 60,
            "pitch_class": 0,
            "octave": 4,
            "velocity_or_amplitude": 80,
            "confidence": None,
            "source": "basic_pitch",
        }
        invalid_values = [
            {"start": float("nan")},
            {"start": -0.1},
            {"end": -0.1},
            {"pitch": 128, "pitch_class": 8},
            {"pitch_class": 11},
            {"source": ""},
        ]
        for replacement in invalid_values:
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    NoteEvidence(**{**valid, **replacement})


class ChordHypothesisTests(unittest.TestCase):
    def test_normalized_event_round_trip_is_lossless(self):
        event = {
            "start": 0.5,
            "end": 1.75,
            "chord": "D7",
            "confidence": 0.8,
            "source_detector": "rule_jaccard",
        }

        hypothesis = normalized_event_to_hypothesis(event)

        self.assertEqual(hypothesis_to_normalized_event(hypothesis), event)

    def test_validation_rejects_invalid_hypothesis_values(self):
        with self.assertRaises(ValueError):
            ChordHypothesis(0, 0, "C", None, "hybrid")
        with self.assertRaises(ValueError):
            ChordHypothesis(0, 1, "", None, "hybrid")
        with self.assertRaises(ValueError):
            ChordHypothesis(0, 1, "C", float("inf"), "hybrid")
        with self.assertRaises(ValueError):
            ChordHypothesis(0, 1, "C", None, "")


class HarmonicEvidencePacketTests(unittest.TestCase):
    def test_packet_serialization_is_deterministic(self):
        note = to_note_evidence(
            {"start": 0.0, "end": 0.5, "pitch": 62, "velocity": 90},
            source="basic_pitch",
        )
        hypothesis = normalized_event_to_hypothesis({
            "start": 0.0,
            "end": 1.0,
            "chord": "D7",
            "confidence": 0.8,
            "source_detector": "rule_jaccard",
        })
        packet = HarmonicEvidencePacket(
            audio_id="fixture.wav",
            duration=1.0,
            notes=[note],
            chord_hypotheses=[hypothesis],
            warnings=[],
            metadata={"representation": "observational"},
        )

        first = json.dumps(packet.to_dict(), sort_keys=True)
        second = json.dumps(packet.to_dict(), sort_keys=True)

        self.assertEqual(first, second)
        self.assertEqual(packet.to_dict()["notes"][0]["pitch_class"], 2)
        self.assertEqual(
            packet.to_dict()["chord_hypotheses"][0]["source"],
            "rule_jaccard",
        )

    def test_run_detection_inspection_is_opt_in_and_observational(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "D7", "confidence": 0.8}]

        def runner(*args, **kwargs):
            sink = kwargs.get("evidence_sink")
            if sink is not None:
                sink["notes"] = [to_note_evidence(
                    {"start": 0.0, "end": 0.5, "pitch": 62, "velocity": 90},
                    source="basic_pitch",
                )]
                sink["duration"] = 1.0
            return [dict(event) for event in raw]

        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", side_effect=runner):
                normal = detection.run_detection(
                    wav.name, detector="rule_jaccard"
                )
                inspected = detection.run_detection(
                    wav.name,
                    detector="rule_jaccard",
                    include_harmonic_evidence=True,
                )

        self.assertNotIn("harmonic_evidence", normal)
        self.assertEqual(
            inspected["chord_events"], normal["chord_events"]
        )
        self.assertEqual(inspected["warnings"], normal["warnings"])
        packet = inspected["harmonic_evidence"]
        self.assertEqual(packet["notes"][0]["source"], "basic_pitch")
        self.assertEqual(
            packet["chord_hypotheses"][0]["source"], "rule_jaccard"
        )


if __name__ == "__main__":
    unittest.main()
