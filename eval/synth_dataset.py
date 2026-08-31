"""Synthetic chord-detection ground truth dataset.

Generates short MIDI files of common chord progressions across many keys,
emits matching .lab files in mir_eval Harte format, and (when possible)
renders each MIDI to a WAV that the detection pipeline can consume.

WAV rendering strategy:
  1. Try midi2audio + FluidSynth (realistic instrument timbre)
  2. Fall back to pretty_midi.synthesize() (sine-wave additive — clean
     pitch info but unrealistic timbre)
  3. If neither works, write MIDIs + labels only and report which step
     to run after installing FluidSynth.

The dataset is intentionally small (~40 songs) — it's a synthetic upper
bound, not a benchmark. Real numbers come from GuitarSet later.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pretty_midi

EVAL_DIR = Path(__file__).parent
DATA_DIR = EVAL_DIR / "data" / "synth"
MIDI_DIR = DATA_DIR / "midi"
WAV_DIR = DATA_DIR / "wav"
LABEL_DIR = DATA_DIR / "labels"
MANIFEST = EVAL_DIR / "synth_manifest.json"

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_TO_PC = {n: i for i, n in enumerate(NOTES)}
# Accept flat spellings too so progressions can name keys like "Bb major"
for flat, sharp in {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}.items():
    NOTE_TO_PC[flat] = NOTE_TO_PC[sharp]

# Semitone intervals for each scale degree (0-indexed by degree-1)
# Major scale: I  ii  iii IV  V   vi  vii°
MAJOR = [
    (0, "maj"), (2, "min"), (4, "min"), (5, "maj"),
    (7, "maj"), (9, "min"), (11, "dim"),
]
# Harmonic minor: i  ii°  III  iv   V    VI   VII
MINOR = [
    (0, "min"), (2, "dim"), (3, "maj"), (5, "min"),
    (7, "maj"), (8, "maj"), (10, "maj"),
]

# Triad / 7th interval stacks above the root
QUALITY_INTERVALS = {
    "maj":  (0, 4, 7),
    "min":  (0, 3, 7),
    "dim":  (0, 3, 6),
    "aug":  (0, 4, 8),
    "7":    (0, 4, 7, 10),
    "min7": (0, 3, 7, 10),
    "maj7": (0, 4, 7, 11),
    "dim7": (0, 3, 6, 9),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
}


def _resolve_chord(tonic_pc: int, degree: int, scale, quality_override: str | None):
    """Map (key, scale degree, optional quality override) -> (root_pc, quality)."""
    offset, default_q = scale[degree - 1]
    root_pc = (tonic_pc + offset) % 12
    return root_pc, (quality_override or default_q)


def _harte(root_pc: int, quality: str) -> str:
    """Encode (root, quality) as a mir_eval-compatible Harte label."""
    return f"{NOTES[root_pc]}:{quality}"


def _build_song(name: str, tonic: str, scale, progression, chord_duration: float = 2.0):
    """progression: iterable of (degree_1_indexed, optional_quality_override) tuples."""
    tonic_pc = NOTE_TO_PC[tonic]
    pm = pretty_midi.PrettyMIDI()
    instr = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano

    labels: list[tuple[float, float, str]] = []
    t = 0.0
    for step in progression:
        degree, override = step if isinstance(step, tuple) else (step, None)
        root_pc, quality = _resolve_chord(tonic_pc, degree, scale, override)
        # Place the triad/7th in a comfortable mid-register
        root_midi = 48 + root_pc  # C3 + offset
        for iv in QUALITY_INTERVALS[quality]:
            instr.notes.append(pretty_midi.Note(
                velocity=92, pitch=root_midi + iv, start=t, end=t + chord_duration
            ))
        labels.append((t, t + chord_duration, _harte(root_pc, quality)))
        t += chord_duration
    pm.instruments.append(instr)

    midi_path = MIDI_DIR / f"{name}.mid"
    pm.write(str(midi_path))

    lab_path = LABEL_DIR / f"{name}.lab"
    with open(lab_path, "w") as f:
        for start, end, label in labels:
            f.write(f"{start:.3f}\t{end:.3f}\t{label}\n")

    return pm, midi_path, lab_path, t


def _render_wav(pm: pretty_midi.PrettyMIDI, name: str) -> tuple[Path | None, str]:
    """Try FluidSynth (better timbre) first, fall back to pure-sine synthesis.
    Returns (wav_path or None, renderer label)."""
    wav_path = WAV_DIR / f"{name}.wav"

    # Try midi2audio + FluidSynth
    try:
        from midi2audio import FluidSynth  # type: ignore
        fs = FluidSynth()
        fs.midi_to_audio(str(MIDI_DIR / f"{name}.mid"), str(wav_path))
        if wav_path.exists() and wav_path.stat().st_size > 1000:
            return wav_path, "fluidsynth"
    except Exception:
        pass

    # Fall back to pretty_midi's built-in additive sine synthesizer.
    # Produces clean pitch information but a non-instrument timbre — fine
    # for testing chord-detection logic; weaker for basic_pitch which is
    # trained on real instruments.
    try:
        sr = 22050
        audio = pm.synthesize(fs=sr)
        if audio.size == 0:
            return None, "pretty_midi-empty"
        # Normalize, leave a little headroom
        peak = float(np.max(np.abs(audio))) or 1.0
        audio = (audio / peak) * 0.7
        import soundfile as sf
        sf.write(str(wav_path), audio.astype(np.float32), sr)
        return wav_path, "pretty_midi-sine"
    except Exception as e:
        return None, f"failed: {e}"


def _progressions():
    """Yield (name, tonic, scale, progression, chord_duration). ~40 songs."""
    # I-IV-V-I in all 12 major keys (12 songs)
    for tonic in NOTES:
        yield f"I-IV-V-I_{tonic}_major", tonic, MAJOR, [(1,None),(4,None),(5,None),(1,None)], 2.0

    # i-iv-V-i in all 12 minor keys — V is major (harmonic minor) (12 songs)
    for tonic in NOTES:
        yield f"i-iv-V-i_{tonic}_minor", tonic, MINOR, [(1,None),(4,None),(5,None),(1,None)], 2.0

    # Jazz ii-V-I as 7th chords in 6 keys (6 songs)
    for tonic in ["C", "F", "Bb", "G", "D", "A"]:
        yield f"ii-V-I_{tonic}_major", tonic, MAJOR, [(2,"min7"),(5,"7"),(1,"maj7")], 2.0

    # Pop vi-IV-I-V in 6 keys (6 songs)
    for tonic in ["C", "G", "D", "A", "E", "F"]:
        yield f"vi-IV-I-V_{tonic}_major", tonic, MAJOR, [(6,None),(4,None),(1,None),(5,None)], 2.0

    # 12-bar blues with dominant 7ths in 4 keys (4 songs)
    for tonic in ["E", "A", "G", "C"]:
        prog = [(1,"7"),(1,"7"),(1,"7"),(1,"7"),
                (4,"7"),(4,"7"),(1,"7"),(1,"7"),
                (5,"7"),(4,"7"),(1,"7"),(5,"7")]
        yield f"blues_{tonic}_major", tonic, MAJOR, prog, 1.5


def main():
    for d in (MIDI_DIR, WAV_DIR, LABEL_DIR):
        d.mkdir(parents=True, exist_ok=True)

    songs: list[dict] = []
    renderers: dict[str, int] = {}
    for name, tonic, scale, prog, chord_dur in _progressions():
        pm, midi_path, lab_path, total_dur = _build_song(name, tonic, scale, prog, chord_dur)
        wav_path, renderer = _render_wav(pm, name)
        renderers[renderer] = renderers.get(renderer, 0) + 1

        songs.append({
            "name": name,
            "midi": str(midi_path),
            "wav": str(wav_path) if wav_path else None,
            "labels": str(lab_path),
            "duration": total_dur,
            "renderer": renderer,
        })

    manifest = {"count": len(songs), "renderers": renderers, "songs": songs}
    MANIFEST.write_text(json.dumps(manifest, indent=2))

    n_with_wav = sum(1 for s in songs if s["wav"])
    print(f"Generated {len(songs)} songs.")
    print(f"  MIDIs:  {MIDI_DIR}")
    print(f"  Labels: {LABEL_DIR}")
    print(f"  WAVs:   {n_with_wav}/{len(songs)} rendered  -> {WAV_DIR}")
    print(f"  Renderer breakdown: {renderers}")
    if n_with_wav == 0:
        print("\n⚠️ No WAVs rendered. Install FluidSynth + `pip install midi2audio` for")
        print("   instrument-quality audio, or check why pretty_midi.synthesize() failed.")
    print(f"\n  Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
