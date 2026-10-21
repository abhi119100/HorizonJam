"""Bounded subprocess adapter for the research-only LV-Chordia runner."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from time import perf_counter
from typing import Any

from src.chord_labels import normalize_external_chord_label
from src.harmonic_evidence import DirectChordEvidence


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "research" / "detector_tournament" / "lv_chordia_runner.py"
RESULT_PREFIX = "HORIZONJAM_LV_RESULT="
MAX_OUTPUT_CHARS = 2_000_000


class DirectChordAdapterError(RuntimeError):
    pass


def _default_python() -> Path:
    return ROOT / ".venv" / "lvchordia" / "Scripts" / "python.exe"


def _validate_local_audio(path: str) -> Path:
    raw = str(path or "")
    if "://" in raw or raw.lower().startswith(("http:", "https:", "ftp:")):
        raise ValueError("LV-Chordia adapter accepts local files only")
    resolved = Path(raw).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"audio file not found: {resolved}")
    if resolved.suffix.lower() not in {".wav", ".flac", ".mp3", ".ogg", ".m4a"}:
        raise ValueError(f"unsupported audio extension: {resolved.suffix}")
    return resolved


def run_lv_chordia(
    audio_path: str,
    timeout_sec: float = 180.0,
    python_executable: str | None = None,
    chord_dictionary: str = "submission",
) -> dict[str, Any]:
    """Run isolated local inference and validate the versioned result contract."""
    if timeout_sec <= 0:
        raise ValueError("timeout_sec must be > 0")
    if chord_dictionary not in {"submission", "ismir2017", "full"}:
        raise ValueError("unsupported chord dictionary")
    audio = _validate_local_audio(audio_path)
    python = Path(
        python_executable
        or os.getenv("HORIZONJAM_LV_CHORDIA_PYTHON", "")
        or _default_python()
    ).resolve()
    if not python.is_file():
        raise DirectChordAdapterError(
            f"isolated LV-Chordia Python is unavailable: {python}"
        )

    started = perf_counter()
    try:
        completed = subprocess.run(
            [
                str(python),
                str(RUNNER),
                "--input",
                str(audio),
                "--chord-dict",
                chord_dictionary,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise DirectChordAdapterError(
            f"LV-Chordia timed out after {timeout_sec:.1f}s"
        ) from exc
    if len(completed.stdout) > MAX_OUTPUT_CHARS or len(completed.stderr) > MAX_OUTPUT_CHARS:
        raise DirectChordAdapterError("LV-Chordia output exceeded the adapter limit")
    result_line = next(
        (
            line for line in reversed(completed.stdout.splitlines())
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if completed.returncode != 0 or result_line is None:
        detail = completed.stderr[-2000:].strip() or completed.stdout[-2000:].strip()
        raise DirectChordAdapterError(
            f"LV-Chordia runner failed with exit {completed.returncode}: {detail}"
        )
    try:
        payload = json.loads(result_line[len(RESULT_PREFIX):])
    except json.JSONDecodeError as exc:
        raise DirectChordAdapterError("LV-Chordia returned malformed JSON") from exc
    required = {"detector", "events", "warnings", "runtime", "metadata"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise DirectChordAdapterError("LV-Chordia result contract is incomplete")
    if (
        payload["detector"] != "lv_chordia"
        or not isinstance(payload["events"], list)
        or not isinstance(payload["warnings"], list)
        or not isinstance(payload["runtime"], dict)
        or not isinstance(payload["metadata"], dict)
    ):
        raise DirectChordAdapterError("LV-Chordia result contract is invalid")

    evidence = []
    for index, event in enumerate(payload["events"]):
        if not isinstance(event, dict):
            raise DirectChordAdapterError(f"LV-Chordia event {index} must be an object")
        raw_label = str(event.get("raw_label") or event.get("label") or "").strip()
        label, status = normalize_external_chord_label(raw_label)
        evidence.append(DirectChordEvidence(
            start=event.get("start"),
            end=event.get("end"),
            label=label,
            raw_label=raw_label,
            score=None,
            alternatives=[],
            source="lv_chordia",
            metadata={"normalization_status": status},
        ))
    return {
        **payload,
        "events": evidence,
        "runtime": {
            **payload["runtime"],
            "adapter_wall_sec": perf_counter() - started,
        },
    }
