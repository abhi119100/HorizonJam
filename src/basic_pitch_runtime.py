"""Reusable, instrumented BasicPitch runtime for HorizonJam's WAV boundary."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

import numpy as np


_RUNTIME_LOCK = threading.RLock()
_RUNTIME: Optional[dict[str, Any]] = None
_TRANSCRIPTION_COUNT = 0


def _numba_cache_path() -> Path:
    configured = os.getenv("NUMBA_CACHE_DIR")
    if configured:
        return Path(configured)
    path = Path(tempfile.gettempdir()) / "horizonjam-numba-cache"
    os.environ["NUMBA_CACHE_DIR"] = str(path)
    return path


def _build_runtime() -> tuple[dict[str, Any], dict[str, float]]:
    timings: dict[str, float] = {}
    cache_path = _numba_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    import audioread
    import basic_pitch.inference as inference
    from basic_pitch import ICASSP_2022_MODEL_PATH
    timings["basic_pitch_import"] = perf_counter() - started

    started = perf_counter()
    model = inference.Model(ICASSP_2022_MODEL_PATH)
    timings["model_initialization"] = perf_counter() - started
    return {
        "audioread": audioread,
        "inference": inference,
        "model": model,
        "model_path": str(ICASSP_2022_MODEL_PATH),
        "model_type": model.model_type.name,
        "numba_cache_dir": str(cache_path),
    }, timings


def _get_runtime() -> tuple[dict[str, Any], dict[str, float], bool]:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME, timings = _build_runtime()
        return _RUNTIME, timings, False
    return _RUNTIME, {"basic_pitch_import": 0.0, "model_initialization": 0.0}, True


def _note_event_payload(note_events: list[tuple]) -> list[tuple]:
    return [
        (
            float(start),
            float(end),
            int(pitch),
            float(amplitude),
            [int(value) for value in bends] if bends else None,
        )
        for start, end, pitch, amplitude, bends in note_events
    ]


def transcribe_wav_to_midi(wav_path: str, trace: Optional[dict[str, Any]] = None) -> str:
    """Transcribe one validated WAV and return a caller-owned temporary MIDI."""
    global _TRANSCRIPTION_COUNT
    with _RUNTIME_LOCK:
        total_started = perf_counter()
        runtime, timings, model_reused = _get_runtime()
        inference = runtime["inference"]
        model = runtime["model"]
        audioread = runtime["audioread"]

        soundfile_supported = False
        try:
            import soundfile

            soundfile.info(wav_path)
            soundfile_supported = True
        except (ImportError, RuntimeError):
            pass

        loader_import_started = perf_counter()
        original_load = inference.librosa.load
        timings["audio_loader_import"] = perf_counter() - loader_import_started

        original_available_backends = audioread.available_backends
        original_get_audio_input = inference.get_audio_input
        original_model_predict = model.predict
        original_model_output_to_notes = inference.infer.model_output_to_notes

        timings.update({
            "audio_decode_resample": 0.0,
            "audio_window_construction": 0.0,
            "model_inference": 0.0,
            "note_event_extraction_and_midi_generation": 0.0,
        })
        model_windows = 0

        def timed_load(*args, **kwargs):
            started = perf_counter()
            try:
                return original_load(*args, **kwargs)
            finally:
                timings["audio_decode_resample"] += perf_counter() - started

        def timed_audio_input(*args, **kwargs):
            iterator = iter(original_get_audio_input(*args, **kwargs))
            while True:
                decode_before = timings["audio_decode_resample"]
                started = perf_counter()
                try:
                    item = next(iterator)
                except StopIteration:
                    timings["audio_window_construction"] += perf_counter() - started
                    return
                elapsed = perf_counter() - started
                decode_elapsed = timings["audio_decode_resample"] - decode_before
                timings["audio_window_construction"] += max(
                    0.0, elapsed - decode_elapsed
                )
                yield item

        def timed_model_predict(*args, **kwargs):
            nonlocal model_windows
            started = perf_counter()
            try:
                return original_model_predict(*args, **kwargs)
            finally:
                timings["model_inference"] += perf_counter() - started
                model_windows += 1

        def timed_model_output_to_notes(*args, **kwargs):
            started = perf_counter()
            try:
                return original_model_output_to_notes(*args, **kwargs)
            finally:
                timings["note_event_extraction_and_midi_generation"] += perf_counter() - started

        inference.librosa.load = timed_load
        inference.get_audio_input = timed_audio_input
        model.predict = timed_model_predict
        inference.infer.model_output_to_notes = timed_model_output_to_notes
        # Avoid librosa's unconditional external-codec discovery only when its
        # primary SoundFile decoder has already accepted the input.
        if soundfile_supported:
            audioread.available_backends = lambda: []
        try:
            predict_started = perf_counter()
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                model_output, midi_data, note_events = inference.predict(wav_path, model)
            timings["basic_pitch_predict_total"] = perf_counter() - predict_started
        finally:
            audioread.available_backends = original_available_backends
            inference.librosa.load = original_load
            inference.get_audio_input = original_get_audio_input
            model.predict = original_model_predict
            inference.infer.model_output_to_notes = original_model_output_to_notes

        handle, midi_path = tempfile.mkstemp(suffix=".mid", prefix="hj_basic_pitch_")
        os.close(handle)
        Path(midi_path).unlink(missing_ok=True)
        serialize_started = perf_counter()
        midi_data.write(midi_path)
        timings["midi_serialization"] = perf_counter() - serialize_started

        hash_started = perf_counter()
        note_payload = _note_event_payload(note_events)
        note_hash = hashlib.sha256(
            json.dumps(note_payload, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        output_hashes = {
            name: hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()
            for name, values in model_output.items()
        }
        timings["trace_hashing"] = perf_counter() - hash_started
        timings["transcription_total"] = perf_counter() - total_started

        _TRANSCRIPTION_COUNT += 1
        if trace is not None:
            trace.update({
                "backend": runtime["model_type"],
                "model_path": runtime["model_path"],
                "model_reused": model_reused,
                "first_inference_in_process": _TRANSCRIPTION_COUNT == 1,
                "transcription_index": _TRANSCRIPTION_COUNT,
                "numba_cache_dir": runtime["numba_cache_dir"],
                "external_codec_probe_skipped": soundfile_supported,
                "model_windows": model_windows,
                "note_event_count": len(note_events),
                "midi_note_count": sum(len(instrument.notes) for instrument in midi_data.instruments),
                "note_event_hash_sha256": note_hash,
                "model_output_hashes_sha256": output_hashes,
                "model_output_shapes": {name: list(values.shape) for name, values in model_output.items()},
                "timings_sec": timings,
            })
        return midi_path


def reset_runtime_for_tests() -> None:
    global _RUNTIME, _TRANSCRIPTION_COUNT
    with _RUNTIME_LOCK:
        _RUNTIME = None
        _TRANSCRIPTION_COUNT = 0
