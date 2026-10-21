import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import detection
from src import basic_pitch_runtime
from src.harmonic_evidence import NoteEvidence


class BasicPitchRuntimeTests(unittest.TestCase):
    def tearDown(self):
        basic_pitch_runtime.reset_runtime_for_tests()

    def test_runtime_builder_is_called_once_across_repeated_acquisition(self):
        fake_runtime = {"model": object()}
        with patch.object(
            basic_pitch_runtime,
            "_build_runtime",
            return_value=(fake_runtime, {"basic_pitch_import": 1.0, "model_initialization": 2.0}),
        ) as build:
            first, first_timings, first_reused = basic_pitch_runtime._get_runtime()
            second, second_timings, second_reused = basic_pitch_runtime._get_runtime()

        self.assertIs(first, second)
        self.assertEqual(build.call_count, 1)
        self.assertFalse(first_reused)
        self.assertTrue(second_reused)
        self.assertEqual(first_timings["model_initialization"], 2.0)
        self.assertEqual(second_timings["model_initialization"], 0.0)

    def test_runtime_trace_is_opt_in_and_does_not_change_events(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "G7", "confidence": None}]
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
            with patch("detection._run_hybrid", return_value=raw):
                normal = detection.run_detection(wav.name, detector="rule_jaccard")

            def traced_runner(*args, **kwargs):
                kwargs["runtime_trace"]["stages_sec"]["post_transcription_detector"] = 0.1
                return raw

            with patch("detection._run_hybrid", side_effect=traced_runner):
                traced = detection.run_detection(
                    wav.name,
                    detector="rule_jaccard",
                    include_runtime_trace=True,
                )

        self.assertNotIn("runtime_trace", normal)
        self.assertEqual(normal["chord_events"], traced["chord_events"])
        self.assertEqual(traced["runtime_trace"]["schema_version"], "single-wav-runtime-v1")
        self.assertIn("total", traced["runtime_trace"]["stages_sec"])

    def test_hybrid_removes_transcription_midi_after_detection(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as midi:
            midi_path = Path(midi.name)

        class FakeDetector:
            def __init__(self, use_viterbi=True):
                self.use_viterbi = use_viterbi

            def detect_chords(self, *_args, **_kwargs):
                return {"chords": []}

        with patch("detection._wav_to_midi", return_value=str(midi_path)):
            with patch("hybrid_chord_detector.HybridChordDetector", FakeDetector):
                detection._run_hybrid("fixture.wav")

        self.assertFalse(midi_path.exists())

    def test_hybrid_collects_direct_and_midi_evidence_from_one_transcription(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as midi:
            midi_path = Path(midi.name)
        fixture_midi = Path(__file__).with_name("test11.mid")
        midi_path.write_bytes(fixture_midi.read_bytes())
        direct_note = NoteEvidence(
            start=0.0,
            end=0.5,
            pitch=60,
            pitch_class=0,
            octave=4,
            velocity_or_amplitude=0.8,
            confidence=None,
            source="basic_pitch",
        )

        def transcribe(_wav, _trace, sink):
            sink["notes"] = [direct_note]
            return str(midi_path)

        class FakeDetector:
            def __init__(self, use_viterbi=True):
                self.use_viterbi = use_viterbi

            def detect_chords(self, *_args, **_kwargs):
                return {"chords": []}

        sink = {}
        with patch("detection._wav_to_midi", side_effect=transcribe) as acquire:
            with patch("hybrid_chord_detector.HybridChordDetector", FakeDetector):
                detection._run_hybrid("fixture.wav", evidence_sink=sink)

        self.assertEqual(acquire.call_count, 1)
        self.assertEqual(sink["direct_notes"], [direct_note])
        self.assertGreater(len(sink["midi_notes"]), 0)
        self.assertIn("matched_note_count", sink["direct_vs_midi"])
        self.assertFalse(midi_path.exists())


if __name__ == "__main__":
    unittest.main()
