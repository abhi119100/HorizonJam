"""HorizonJam centralized chord detection layer.

Single entry point the web app and eval harness both use, so the underlying
detector engine is swappable via the HORIZONJAM_DETECTOR env var.

Supported detectors:
  - production    AccurateAudioToChordsPipeline (current frontend path; kept
                  as fallback/debug only)
  - hybrid        HybridChordDetector(use_viterbi=True) on a basic_pitch
                  transcription. Today identical to rule_viterbi because
                  HybridChordDetector.ml_available is False (no trained
                  model). Default web app detector.
  - rule_viterbi  Same as hybrid until an ML model is trained, then the two
                  diverge (rule_viterbi forces ml_available=False).
  - rule_jaccard  Experimental advanced symbolic scorer using Jaccard pitch
                  matching. Not the default; retained for controlled evidence.

Output contract — every detector returns this dict shape:
  {
    "chord_events": [
      {
        "start": float,            # seconds, >= 0
        "end": float,              # seconds, > start
        "chord": str,              # "G", "Em", "C#m7", "N" for no-chord
        "confidence": float|None,  # 0..1 if available, None otherwise
        "source_detector": str,    # which engine produced it
      },
      ...
    ],
    "estimated_key": str | None,   # left as None here; KS analysis lives in
                                   # ChordAIRAGTutor._detect_key_from_events
    "detector_used": str,
    "warnings": list[str],         # repairs the normalizer performed
  }

Events are guaranteed sorted, non-overlapping, with no zero-duration entries
or invalid chord labels. Safe for mir_eval and safe for frontend display.
"""
from __future__ import annotations

import io
import logging
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

_REPO = Path(__file__).parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

logger = logging.getLogger("horizonjam.detection")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s %(name)s] %(message)s"))
    logger.addHandler(h)
    logger.propagate = False

DEFAULT_DETECTOR = "hybrid"
SUPPORTED = ("production", "hybrid", "rule_viterbi", "rule_jaccard")
EPS = 1e-3


# --------------------------- env-var selection ---------------------------
def selected_detector() -> str:
    """Resolve HORIZONJAM_DETECTOR env var to a supported detector name."""
    name = (os.getenv("HORIZONJAM_DETECTOR", "") or DEFAULT_DETECTOR).strip().lower()
    if name not in SUPPORTED:
        logger.warning(
            "Unknown HORIZONJAM_DETECTOR=%r; supported %s; falling back to %s",
            name, SUPPORTED, DEFAULT_DETECTOR,
        )
        return DEFAULT_DETECTOR
    return name


# --------------------------- internal runners ----------------------------
def _silent(fn, *args, **kwargs):
    """Run fn while swallowing the detector's noisy stdout/stderr."""
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return fn(*args, **kwargs)


def _run_production(wav_path: str) -> list[dict[str, Any]]:
    """AccurateAudioToChordsPipeline — kept as fallback/debug. Known to emit
    overlapping intervals on synthetic clean audio; the normalizer fixes that
    automatically downstream."""
    from pipeline import AccurateAudioToChordsPipeline  # type: ignore

    pipe = AccurateAudioToChordsPipeline(
        confidence_threshold=0.3, min_note_duration=0.05,
        max_note_duration=4.0, basicpitch_onset_threshold=0.5,
        basicpitch_frame_threshold=0.3, min_frequency=80.0,
        max_frequency=1200.0,
    )
    tmp_out = Path(tempfile.mkdtemp(prefix="hj_prod_"))
    try:
        results = _silent(pipe.run_pipeline, wav_path, str(tmp_out))
    finally:
        shutil.rmtree(tmp_out, ignore_errors=True)

    raw = []
    for ev in results.get("chord_events", []):
        start = float(ev.get("timestamp") or ev.get("start_time") or 0.0)
        dur = float(ev.get("duration") or ev.get("duration_seconds") or 0.0)
        end = start + dur
        chord = ev.get("chord") or ev.get("chord_symbol") or "N"
        if end > start:
            raw.append({"start": start, "end": end, "chord": chord,
                        "confidence": ev.get("confidence")})
    return raw


def _wav_to_midi(wav_path: str, runtime_trace: Optional[dict[str, Any]] = None,
                 direct_evidence_sink: Optional[dict[str, Any]] = None) -> str:
    """basic_pitch transcription. Caller is responsible for unlinking."""
    from basic_pitch_runtime import transcribe_wav_to_midi  # type: ignore

    return transcribe_wav_to_midi(
        wav_path, runtime_trace, direct_evidence_sink
    )


def _run_hybrid(wav_path: str, use_viterbi: bool = True,
                classifier_mode: str = "simple",
                runtime_trace: Optional[dict[str, Any]] = None,
                evidence_sink: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """HybridChordDetector on basic_pitch MIDI. Today this == rule_viterbi
    because HybridChordDetector.ml_available is False (no models/*.joblib)."""
    import_started = perf_counter()
    from hybrid_chord_detector import HybridChordDetector  # type: ignore
    if runtime_trace is not None:
        runtime_trace["stages_sec"]["hybrid_detector_import"] = perf_counter() - import_started

    transcription_trace = {} if runtime_trace is not None else None
    direct_evidence: Optional[dict[str, Any]] = (
        {} if evidence_sink is not None else None
    )
    if direct_evidence is None:
        midi_path = _wav_to_midi(wav_path, transcription_trace)
    else:
        midi_path = _wav_to_midi(
            wav_path, transcription_trace, direct_evidence
        )
    try:
        if evidence_sink is not None:
            from src.chord_detector import parse_midi_notes
            from src.harmonic_evidence import compare_note_evidence, notes_to_evidence

            parse_started = perf_counter()
            parsed_notes, parsed_duration = _silent(parse_midi_notes, midi_path)
            if transcription_trace is not None:
                transcription_trace["timings_sec"]["midi_read_and_parse"] = (
                    perf_counter() - parse_started
                )
            midi_evidence = notes_to_evidence(
                parsed_notes, source="basic_pitch"
            )
            direct_notes = list((direct_evidence or {}).get("notes", []))
            evidence_sink["notes"] = direct_notes
            evidence_sink["direct_notes"] = direct_notes
            evidence_sink["midi_notes"] = midi_evidence
            evidence_sink["direct_vs_midi"] = compare_note_evidence(
                direct_notes, midi_evidence
            )
            evidence_sink["duration"] = float(parsed_duration)

        init_started = perf_counter()
        det = HybridChordDetector(use_viterbi=use_viterbi)
        if runtime_trace is not None:
            runtime_trace["stages_sec"]["hybrid_detector_initialization"] = perf_counter() - init_started
        post_started = perf_counter()
        result = _silent(
            det.detect_chords,
            midi_path,
            classifier_mode=classifier_mode,
            runtime_trace=runtime_trace,
        )
        if runtime_trace is not None:
            runtime_trace["stages_sec"]["post_transcription_detector"] = perf_counter() - post_started
    finally:
        try:
            os.unlink(midi_path)
        except OSError:
            pass

    if not result:
        return []
    if runtime_trace is not None:
        runtime_trace["basic_pitch"] = transcription_trace
    raw = []
    for c in result.get("chords") or []:
        start = float(c.get("start") or c.get("timestamp") or 0.0)
        if "end" in c:
            end = float(c["end"])
        elif "end_time" in c:
            end = float(c["end_time"])
        else:
            end = start + float(c.get("duration", 0.0) or 0.0)
        chord = c.get("chord") or "N"
        if end > start:
            raw.append({"start": start, "end": end, "chord": chord,
                        "confidence": c.get("confidence")})
    return raw


# --------------------------- normalization -------------------------------
def _safe_chord_label(label) -> Optional[str]:
    """Return a normalized chord label, 'N' for explicit no-chord, or None
    if the label can't be salvaged (caller should drop)."""
    if label is None:
        return None
    s = str(label).strip()
    if not s:
        return None
    if s in ("N", "n", "Unknown", "unknown", "X", "x", "?"):
        return "N"
    if not s[0].upper() in "ABCDEFG":
        return None
    return s


def normalize_and_validate(events: list[dict[str, Any]]) -> tuple[list[dict], list[str]]:
    """Repair a raw detector event list into the normalized contract.

    Repairs (in order, each logs a warning when applied):
      1. Drop events with unparseable chord labels
      2. Drop events with non-numeric times
      3. Clamp negative start to 0
      4. Drop zero/negative-duration events
      5. Sort by start time
      6. Clamp overlapping end to next-event start (drop if it collapses)
      7. Merge adjacent identical chords (gap <= EPS, same chord symbol)

    Returns (clean_events, warnings).
    """
    warnings: list[str] = []
    if not events:
        return [], warnings

    # Step 1-4: per-event validation
    cleaned = []
    for e in events:
        chord = _safe_chord_label(e.get("chord"))
        if chord is None:
            warnings.append(f"dropped event with unparseable chord {e.get('chord')!r}")
            continue
        try:
            start = float(e.get("start", 0.0))
            end = float(e.get("end", 0.0))
        except (TypeError, ValueError):
            warnings.append(f"dropped event with non-numeric times: {e}")
            continue
        if start < 0:
            warnings.append(f"clamped negative start {start:.3f} to 0")
            start = 0.0
        if end <= start:
            warnings.append(f"dropped zero-duration event chord={chord} start={start:.3f} end={end:.3f}")
            continue
        cleaned.append({
            "start": start,
            "end": end,
            "chord": chord,
            "confidence": e.get("confidence"),
            "source_detector": e.get("source_detector"),
        })

    if not cleaned:
        return [], warnings

    # Step 5: sort
    pre_sort = [(e["start"], e["end"]) for e in cleaned]
    cleaned.sort(key=lambda e: (e["start"], e["end"]))
    if [(e["start"], e["end"]) for e in cleaned] != pre_sort:
        warnings.append("re-sorted events by start time")

    # Step 6: clamp overlaps
    fixed = []
    overlap_count = 0
    for i, e in enumerate(cleaned):
        if i + 1 < len(cleaned):
            next_start = cleaned[i + 1]["start"]
            if e["end"] > next_start + EPS:
                overlap_count += 1
                e = {**e, "end": next_start}
        if e["end"] > e["start"] + EPS:
            fixed.append(e)
        else:
            warnings.append(f"dropped event that collapsed after overlap clamp: chord={e['chord']}")
    if overlap_count > 0:
        warnings.append(f"clamped {overlap_count} overlapping intervals")

    if not fixed:
        return [], warnings

    # Step 7: merge adjacent identicals
    merged = [fixed[0]]
    for e in fixed[1:]:
        prev = merged[-1]
        if e["chord"] == prev["chord"] and abs(e["start"] - prev["end"]) <= EPS:
            merged[-1] = {**prev, "end": e["end"]}
        else:
            merged.append(e)
    n_merged = len(fixed) - len(merged)
    if n_merged > 0:
        warnings.append(f"merged {n_merged} adjacent identical chords")

    return merged, warnings


# --------------------------- public API ----------------------------------
def run_detection(wav_path: str, detector: Optional[str] = None,
                  include_runtime_trace: bool = False,
                  include_harmonic_evidence: bool = False,
                  include_dsp_evidence: bool = False,
                  include_direct_chord_evidence: bool = False) -> dict[str, Any]:
    """Run the selected chord detector on a WAV; return the normalized contract."""
    total_started = perf_counter()
    runtime_trace = {
        "schema_version": "single-wav-runtime-v1",
        "stages_sec": {},
    } if include_runtime_trace else None
    name = (detector or selected_detector()).strip().lower()
    if name not in SUPPORTED:
        raise ValueError(f"Unsupported detector {name!r}; supported: {SUPPORTED}")

    validation_started = perf_counter()
    if not Path(wav_path).exists():
        raise FileNotFoundError(f"WAV not found: {wav_path}")

    # Header-only WAV inspection so logs include duration without reading samples
    duration_sec = None
    sample_rate = None
    file_size = None
    try:
        import soundfile as _sf
        info = _sf.info(wav_path)
        duration_sec = float(info.frames) / float(info.samplerate) if info.samplerate else None
        sample_rate = info.samplerate
        file_size = Path(wav_path).stat().st_size
    except Exception as _e:
        logger.debug("soundfile.info failed for %s: %s", wav_path, _e)
    if runtime_trace is not None:
        runtime_trace["stages_sec"]["file_validation"] = perf_counter() - validation_started
        runtime_trace["input"] = {
            "path": str(Path(wav_path)),
            "duration_sec": duration_sec,
            "sample_rate": sample_rate,
            "file_size_bytes": file_size,
        }

    logger.info(
        "detector=%s input=%s size=%s sr=%s duration=%s sec",
        name, wav_path,
        f"{file_size}B" if file_size is not None else "?",
        sample_rate if sample_rate is not None else "?",
        f"{duration_sec:.2f}" if duration_sec is not None else "?",
    )
    include_harmonic_evidence = (
        include_harmonic_evidence
        or include_dsp_evidence
        or include_direct_chord_evidence
    )
    evidence_sink: Optional[dict[str, Any]] = (
        {} if include_harmonic_evidence else None
    )
    try:
        if name == "production":
            raw = _run_production(wav_path)
        elif name in ("hybrid", "rule_viterbi"):
            if evidence_sink is None:
                raw = _run_hybrid(
                    wav_path, use_viterbi=True, runtime_trace=runtime_trace
                )
            else:
                raw = _run_hybrid(
                    wav_path,
                    use_viterbi=True,
                    runtime_trace=runtime_trace,
                    evidence_sink=evidence_sink,
                )
        elif name == "rule_jaccard":
            hybrid_kwargs = {
                "use_viterbi": True,
                "classifier_mode": "advanced_jaccard",
                "runtime_trace": runtime_trace,
            }
            if evidence_sink is not None:
                hybrid_kwargs["evidence_sink"] = evidence_sink
            raw = _run_hybrid(wav_path, **hybrid_kwargs)
        else:
            raise AssertionError(f"unhandled detector: {name}")
    except Exception as e:
        logger.error("detector %s raised %s: %s", name, type(e).__name__, e)
        failure = {
            "chord_events": [],
            "estimated_key": None,
            "detector_used": name,
            "warnings": [f"detector raised {type(e).__name__}: {e}"],
        }
        if runtime_trace is not None:
            runtime_trace["stages_sec"]["total"] = perf_counter() - total_started
            failure["runtime_trace"] = runtime_trace
        return failure

    # Tag every event with which engine produced it
    for ev in raw:
        ev["source_detector"] = name

    logger.info("detector %s produced %d raw events", name, len(raw))
    normalize_started = perf_counter()
    events, warnings = normalize_and_validate(raw)
    if runtime_trace is not None:
        runtime_trace["stages_sec"]["normalization"] = perf_counter() - normalize_started
    logger.info("normalized %d -> %d events; %d warnings",
                len(raw), len(events), len(warnings))
    for w in warnings:
        logger.warning("normalize: %s", w)

    if events:
        seq = " - ".join(e["chord"] for e in events)
        logger.info("chord sequence: %s", seq[:200] + ("..." if len(seq) > 200 else ""))

    response = {
        "chord_events": events,
        "estimated_key": None,  # KS analysis happens in ChordAIRAGTutor
        "detector_used": name,
        "warnings": warnings,
    }
    if include_harmonic_evidence:
        from src.harmonic_evidence import (
            HarmonicEvidencePacket,
            normalized_event_to_hypothesis,
        )

        packet_duration = duration_sec
        if packet_duration is None and evidence_sink is not None:
            packet_duration = evidence_sink.get("duration")
        pitch_class_evidence = []
        dsp_metadata = None
        dsp_warnings: list[str] = []
        if include_dsp_evidence:
            try:
                from src.dsp_chroma import extract_pitch_class_evidence

                pitch_class_evidence, dsp_metadata = (
                    extract_pitch_class_evidence(wav_path)
                )
            except Exception as exc:
                dsp_warnings.append(
                    f"librosa_chroma unavailable: {type(exc).__name__}: {exc}"
                )
        direct_chord_evidence = []
        direct_metadata = None
        direct_warnings: list[str] = []
        if include_direct_chord_evidence:
            try:
                from src.direct_chord_adapter import run_lv_chordia

                direct_result = run_lv_chordia(wav_path)
                direct_chord_evidence = direct_result["events"]
                direct_metadata = {
                    **direct_result["metadata"],
                    "runtime": direct_result["runtime"],
                }
                direct_warnings.extend(direct_result["warnings"])
            except Exception as exc:
                direct_warnings.append(
                    f"lv_chordia unavailable: {type(exc).__name__}: {exc}"
                )
        packet = HarmonicEvidencePacket(
            audio_id=Path(wav_path).name,
            duration=packet_duration,
            notes=list((evidence_sink or {}).get("notes", [])),
            chord_hypotheses=[
                normalized_event_to_hypothesis(event) for event in events
            ],
            pitch_class_evidence=pitch_class_evidence,
            direct_chord_evidence=direct_chord_evidence,
            warnings=[*warnings, *dsp_warnings, *direct_warnings],
            metadata={
                "detector": name,
                "representation": "observational",
                "note_path": (
                    "basic_pitch_direct_with_midi_compatibility"
                    if name in ("hybrid", "rule_viterbi", "rule_jaccard")
                    else "production_compatibility_pipeline"
                ),
                "direct_vs_midi": (evidence_sink or {}).get("direct_vs_midi"),
                "midi_notes": [
                    note.to_dict()
                    for note in (evidence_sink or {}).get("midi_notes", [])
                ],
                "dsp": dsp_metadata,
                "direct_chord_model": direct_metadata,
            },
        )
        response["harmonic_evidence"] = packet.to_dict()
    if runtime_trace is not None:
        runtime_trace["stages_sec"]["total"] = perf_counter() - total_started
        response["runtime_trace"] = runtime_trace
    return response
