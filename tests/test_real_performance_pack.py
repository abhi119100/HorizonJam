import json
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from eval.real_performance_pack import validate_manifest, held_out_digest


class RealPerformancePackTests(unittest.TestCase):
    def paired_manifest(self, root):
        manifest = json.loads(Path("eval/real_performance_demo_pack/manifest.json").read_text())
        manifest["held_out_frozen_at"] = "2026-10-03T00:00:00Z"
        manifest["cases"] = []
        for index, split in enumerate(("development", "held_out")):
            # Byte fixtures test manifest integrity only; no audio accuracy claim.
            path = root / f"fixture{index}.wav"
            path.write_bytes(f"validator fixture {index}".encode())
            annotation = {"annotator_id": "a", "annotation_date": "2026-10-03", "confidence": "HIGH", "notes": "fixture", "segments": [{"start": 0, "end": 1, "chord": "C:maj"}]}
            manifest["cases"].append({
                "case_id": f"case-{index}", "split": split, "category": "chord_isolation" if index == 0 else "progression",
                "performer_id": f"performer-{index}", "recording_session_id": f"session-{index}", "device_id": "device-a",
                "audio": {"path": path.name, "duration_sec": 1, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
                "provenance": {"rights_basis": "OWNED", "rights_reference": "unit-test-only", "source": "unit-test fixture", "redistribution_allowed": False},
                "instrument": "guitar", "qualities": ["major"], "playing_styles": [], "conditions": [], "harmonic_examples": [],
                "annotations": [annotation, {**copy.deepcopy(annotation), "annotator_id": "b"}],
            })
        manifest["held_out_labels_sha256"] = held_out_digest(manifest["cases"])
        return manifest

    def test_performer_session_and_audio_leakage_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.paired_manifest(root)
            self.assertEqual(validate_manifest(root / "manifest.json", original, root)["validation_errors"], [])
            for field in ("performer_id", "recording_session_id", "audio"):
                manifest = copy.deepcopy(original)
                manifest["cases"][1][field] = manifest["cases"][0][field]
                manifest["held_out_labels_sha256"] = held_out_digest(manifest["cases"])
                result = validate_manifest(root / "manifest.json", manifest, root)
                self.assertTrue(any("across" in error for error in result["validation_errors"]), field)

    def test_changed_held_out_labels_do_not_pass_a_format_only_hash_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.paired_manifest(root)
            manifest["cases"][1]["annotations"][0]["segments"][0]["chord"] = "G:maj"
            result = validate_manifest(root / "manifest.json", manifest, root)
            self.assertIn("held-out audio/label digest does not match the frozen manifest", result["validation_errors"])

    def test_single_annotation_and_out_of_audio_segments_block_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.paired_manifest(root)
            manifest["cases"][0]["annotations"] = manifest["cases"][0]["annotations"][:1]
            manifest["cases"][0]["annotations"][0]["segments"][0]["end"] = 2
            result = validate_manifest(root / "manifest.json", manifest, root)
            self.assertTrue(any("two distinct annotators" in reason for reason in result["readiness_reasons"]))
            self.assertTrue(any("beyond" in error for error in result["validation_errors"]))

    def test_empty_collection_is_valid_but_not_evaluation_ready(self):
        result = validate_manifest(Path("eval/real_performance_demo_pack/manifest.json"))
        self.assertEqual(result["validation_errors"], [])
        self.assertEqual(result["case_count"], 0)
        self.assertFalse(result["ready"])
        self.assertTrue(any("at least 20" in reason for reason in result["readiness_reasons"]))

    def test_missing_rights_and_annotations_are_rejected(self):
        manifest = json.loads(Path("eval/real_performance_demo_pack/manifest.json").read_text())
        manifest["cases"] = [{
            "case_id": "real_001", "split": "development", "category": "chord_isolation",
            "audio": {"path": "missing.wav", "sha256": "0" * 64, "duration_sec": 2.0},
            "provenance": {}, "instrument": "acoustic_guitar", "qualities": ["major"],
            "playing_styles": ["block_chords"], "conditions": ["quiet_room"],
            "harmonic_examples": [], "annotations": [],
        }]
        result = validate_manifest(
            Path("manifest.json"), manifest_override=manifest, root_override=Path.cwd()
        )
        self.assertTrue(any("rights_basis" in error for error in result["validation_errors"]))
        self.assertTrue(any("annotations" in error for error in result["validation_errors"]))

    def test_audio_path_cannot_escape_pack(self):
        manifest = json.loads(Path("eval/real_performance_demo_pack/manifest.json").read_text())
        manifest["cases"] = [{
            "case_id": "real_001", "split": "development", "category": "chord_isolation",
            "audio": {"path": "../outside.wav", "sha256": "0" * 64, "duration_sec": 2.0},
            "provenance": {"rights_basis": "OWNED", "rights_reference": "controlled-001", "source": "project recording", "redistribution_allowed": False},
            "instrument": "acoustic_guitar", "qualities": ["major"],
            "playing_styles": ["block_chords"], "conditions": ["quiet_room"],
            "harmonic_examples": [], "annotations": [{
                "annotator_id": "ann-a", "annotation_date": "2026-08-31", "confidence": "HIGH", "notes": "",
                "segments": [{"start": 0.0, "end": 2.0, "chord": "C:maj"}],
            }],
        }]
        result = validate_manifest(
            Path("manifest.json"),
            manifest_override=manifest,
            root_override=Path("eval/real_performance_demo_pack"),
        )
        self.assertTrue(any("escapes" in error for error in result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
