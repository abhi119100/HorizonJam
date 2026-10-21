import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import detection
from src.chord_labels import normalize_external_chord_label
from src.direct_chord_adapter import (
    DirectChordAdapterError,
    RESULT_PREFIX,
    run_lv_chordia,
)
from src.harmonic_evidence import DirectChordEvidence


class DirectChordEvidenceTests(unittest.TestCase):
    def test_label_normalization_preserves_supported_and_unmapped_labels(self):
        cases = {
            "C:maj": ("C", "normalized"),
            "C major": ("C", "normalized"),
            "A:min7": ("Am7", "normalized"),
            "D:7": ("D7", "normalized"),
            "F#:dim": ("F#dim", "normalized"),
            "Bb:maj7": ("Bbmaj7", "normalized"),
            "C:weird(add13)": ("C:weird(add13)", "unmapped"),
            "N": ("N", "normalized"),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_external_chord_label(raw), expected)

    def test_direct_evidence_validation(self):
        evidence = DirectChordEvidence(0.0, 1.0, "C", "C:maj", None, [], "lv_chordia")
        self.assertIsNone(evidence.score)
        with self.assertRaises(ValueError):
            DirectChordEvidence(1.0, 1.0, "C", "C:maj", None, [], "lv_chordia")


class DirectChordAdapterTests(unittest.TestCase):
    def _audio(self):
        return tempfile.NamedTemporaryFile(suffix=".wav")

    def test_rejects_url_input_before_subprocess(self):
        with patch("src.direct_chord_adapter.subprocess.run") as run:
            with self.assertRaises(ValueError):
                run_lv_chordia("https://example.com/audio.wav")
        run.assert_not_called()

    def test_validates_and_normalizes_structured_result(self):
        payload = {
            "detector": "lv_chordia",
            "events": [{"start": 0.0, "end": 1.0, "raw_label": "D:7"}],
            "warnings": [],
            "runtime": {"inference_sec": 1.0},
            "metadata": {},
        }
        completed = subprocess.CompletedProcess(
            [], 0, RESULT_PREFIX + json.dumps(payload) + "\n", ""
        )
        with self._audio() as audio:
            with patch("src.direct_chord_adapter.subprocess.run", return_value=completed) as run:
                result = run_lv_chordia(
                    audio.name, python_executable=audio.name
                )
        self.assertEqual(result["events"][0].label, "D7")
        self.assertIsNone(result["events"][0].score)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_timeout_and_malformed_json_are_errors(self):
        with self._audio() as audio:
            with patch(
                "src.direct_chord_adapter.subprocess.run",
                side_effect=subprocess.TimeoutExpired([], 1),
            ):
                with self.assertRaisesRegex(DirectChordAdapterError, "timed out"):
                    run_lv_chordia(audio.name, python_executable=audio.name, timeout_sec=1)
            malformed = subprocess.CompletedProcess(
                [], 0, RESULT_PREFIX + "{bad}\n", ""
            )
            with patch("src.direct_chord_adapter.subprocess.run", return_value=malformed):
                with self.assertRaisesRegex(DirectChordAdapterError, "malformed JSON"):
                    run_lv_chordia(audio.name, python_executable=audio.name)

    def test_unavailable_environment_is_explicit(self):
        with self._audio() as audio:
            with self.assertRaisesRegex(DirectChordAdapterError, "unavailable"):
                run_lv_chordia(
                    audio.name,
                    python_executable=str(Path(audio.name).with_suffix(".missing")),
                )

    def test_detection_direct_inspection_is_opt_in_and_nonfatal(self):
        raw = [{"start": 0.0, "end": 1.0, "chord": "C", "confidence": 0.8}]
        direct = DirectChordEvidence(
            0.0, 1.0, "C", "C:maj", None, [], "lv_chordia"
        )

        def runner(*_args, **kwargs):
            sink = kwargs.get("evidence_sink")
            if sink is not None:
                sink.update({"notes": [], "midi_notes": [], "duration": 1.0})
            return [dict(item) for item in raw]

        result = {
            "events": [direct],
            "warnings": [],
            "runtime": {"adapter_wall_sec": 1.0},
            "metadata": {"distribution_status": "RESEARCH_ONLY"},
        }
        with self._audio() as audio:
            with patch("detection._run_hybrid", side_effect=runner):
                with patch("src.direct_chord_adapter.run_lv_chordia", return_value=result):
                    inspected = detection.run_detection(
                        audio.name,
                        detector="rule_jaccard",
                        include_direct_chord_evidence=True,
                    )
                with patch(
                    "src.direct_chord_adapter.run_lv_chordia",
                    side_effect=DirectChordAdapterError("missing"),
                ):
                    degraded = detection.run_detection(
                        audio.name,
                        detector="rule_jaccard",
                        include_direct_chord_evidence=True,
                    )

        self.assertEqual(inspected["chord_events"], degraded["chord_events"])
        self.assertEqual(
            inspected["harmonic_evidence"]["direct_chord_evidence"][0]["source"],
            "lv_chordia",
        )
        self.assertTrue(any(
            "lv_chordia unavailable" in warning
            for warning in degraded["harmonic_evidence"]["warnings"]
        ))


if __name__ == "__main__":
    unittest.main()
