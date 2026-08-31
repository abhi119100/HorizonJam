"""Uniform CLI wrapping all three detector configurations.

Usage:
  python eval/run_detector.py --detector {production|hybrid|rule_viterbi|rule_jaccard} --wav <path>

Always prints exactly one JSON line on stdout as the LAST line:
  {"events": [{"start": 0.0, "end": 2.0, "label": "C:maj"}, ...]}

Detectors:
  production    AccurateAudioToChordsPipeline — what the live frontend hits.
                WAV in, full pipeline (basic_pitch → chord_detector). No
                Viterbi, no ML.
  rule_viterbi  HybridChordDetector(use_viterbi=True). Takes MIDI input, so
                we transcribe the WAV with basic_pitch first to keep the
                comparison apples-to-apples.
  hybrid        Identical to rule_viterbi today — HybridChordDetector loads
                an ML model from models/*.joblib if present, but no model
                has been trained yet (ml_available=False). Kept as a
                distinct mode so we can re-run once ML training lands.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import warnings
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

warnings.filterwarnings("ignore")

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


# ----------------------------- label normalization ------------------------
def to_harte(label: str | None) -> str:
    """Convert internal chord symbols (e.g. 'Am', 'F#m7', 'Bb') to mir_eval Harte
    format ('A:min', 'F#:min7', 'Bb:maj'). Unparseable → 'N'."""
    if not label or label.strip() in ("", "N", "Unknown", "X", "?"):
        return "N"
    s = label.strip()
    # Root letter (+ optional accidental)
    if len(s) >= 2 and s[1] in ("#", "b"):
        root, rest = s[:2], s[2:]
    else:
        root, rest = s[:1], s[1:]
    if root[0].upper() not in "ABCDEFG":
        return "N"
    root = root[0].upper() + (root[1:] if len(root) > 1 else "")

    rest = rest.strip()
    # Order matters — check longer prefixes first
    if rest.startswith("maj7"):
        return f"{root}:maj7"
    if rest.startswith("maj"):
        return f"{root}:maj"
    if rest.startswith("min7") or rest.startswith("m7"):
        return f"{root}:min7"
    if rest.startswith("dim7"):
        return f"{root}:dim7"
    if rest.startswith("dim") or rest.startswith("°") or rest.startswith("o"):
        return f"{root}:dim"
    if rest.startswith("aug") or rest.startswith("+"):
        return f"{root}:aug"
    if rest.startswith("sus2"):
        return f"{root}:sus2"
    if rest.startswith("sus4") or rest.startswith("sus"):
        return f"{root}:sus4"
    if rest.startswith("min") or (rest.startswith("m") and not rest.startswith("maj")):
        return f"{root}:min"
    if rest.startswith("7"):
        return f"{root}:7"
    if rest == "":
        return f"{root}:maj"
    # Fallback: assume major (drop unsupported extensions like add9)
    return f"{root}:maj"


# ----------------------------- production path ----------------------------
def run_production(wav_path: str) -> list[dict]:
    from pipeline import AccurateAudioToChordsPipeline

    tmp_out = Path(tempfile.mkdtemp(prefix="hj_prod_"))
    try:
        pipe = AccurateAudioToChordsPipeline(
            confidence_threshold=0.3,
            min_note_duration=0.05,
            max_note_duration=4.0,
            basicpitch_onset_threshold=0.5,
            basicpitch_frame_threshold=0.3,
            min_frequency=80.0,
            max_frequency=1200.0,
        )
        # Pipeline prints a lot — keep that out of stdout where our JSON lives
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            results = pipe.run_pipeline(wav_path, str(tmp_out))
    finally:
        import shutil
        shutil.rmtree(tmp_out, ignore_errors=True)

    events = []
    for ev in results.get("chord_events", []):
        start = float(ev.get("timestamp") or ev.get("start_time") or 0.0)
        dur = float(ev.get("duration") or ev.get("duration_seconds") or 0.0)
        end = start + dur
        label = to_harte(ev.get("chord") or ev.get("chord_symbol"))
        if end > start:
            events.append({"start": start, "end": end, "label": label})
    return events


# ----------------------------- hybrid path --------------------------------
def _wav_to_midi(wav_path: str) -> str:
    """Transcribe WAV → MIDI via basic_pitch (ONNX). Returns MIDI path."""
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH

    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        _, midi_data, _ = predict(wav_path, ICASSP_2022_MODEL_PATH)
    midi_path = tempfile.mktemp(suffix=".mid")
    midi_data.write(midi_path)
    return midi_path


def run_hybrid(wav_path: str, use_viterbi: bool,
               classifier_mode: str = "simple") -> list[dict]:
    from hybrid_chord_detector import HybridChordDetector

    midi_path = _wav_to_midi(wav_path)
    try:
        det = HybridChordDetector(use_viterbi=use_viterbi)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = det.detect_chords(midi_path, classifier_mode=classifier_mode)
    finally:
        try:
            os.unlink(midi_path)
        except Exception:
            pass

    if not result:
        return []
    events = []
    chords = result.get("chords") or []
    for c in chords:
        start = float(c.get("start") or c.get("timestamp") or 0.0)
        # Different schema versions — accept either
        if "end" in c:
            end = float(c["end"])
        elif "end_time" in c:
            end = float(c["end_time"])
        else:
            end = start + float(c.get("duration", 0.0) or 0.0)
        if end <= start:
            continue
        label = to_harte(c.get("chord"))
        events.append({"start": start, "end": end, "label": label})
    return events


# ----------------------------- main ---------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Run a single detector on a WAV.")
    parser.add_argument("--detector", required=True,
                        choices=["production", "hybrid", "rule_viterbi", "rule_jaccard"])
    parser.add_argument("--wav", required=True)
    args = parser.parse_args()

    try:
        if args.detector == "production":
            events = run_production(args.wav)
        elif args.detector == "rule_viterbi":
            events = run_hybrid(args.wav, use_viterbi=True)
        elif args.detector == "hybrid":
            events = run_hybrid(args.wav, use_viterbi=True)
        elif args.detector == "rule_jaccard":
            events = run_hybrid(
                args.wav, use_viterbi=True, classifier_mode="advanced_jaccard"
            )
        else:
            print(json.dumps({"events": [], "error": "unknown detector"}))
            sys.exit(2)
    except Exception as e:
        print(json.dumps({"events": [], "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)

    print(json.dumps({"events": events}))


if __name__ == "__main__":
    main()
