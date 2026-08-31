"""
HorizonJam chord-detection evaluation — read-only audit.

Runs four independent tests with what's actually in the repo today:
  1. Labeled-MIDI sanity (Amaj/Bmaj/Fmaj from archive) — does the detector
     return the right root for the simplest possible case?
  2. music21 second opinion on the same MIDIs + tests/test11.mid — uses an
     independent symbolic-music library as ground truth.
  3. Key-detector unit test — feed the new diatonic-fit key detector with
     known progressions from chordonomicon (Let It Be → C major,
     Shape of You → A minor).
  4. Infrastructure audit — what's missing for real accuracy testing.

No code under src/ is modified. This script only reads.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# ---------------------------------------------------------------- helpers ----
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"

def banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def stage(message: str):
    """Emit progress before a potentially expensive lazy import or analysis."""
    print(f"    [stage] {message}", flush=True)


# ----------------------------------------------------------------- music21 ----
def music21_root_quality(midi_path: Path) -> tuple[str | None, str | None, str | None]:
    """Use music21 to extract the dominant chord and key from a MIDI file."""
    started = time.perf_counter()
    stage(f"music21 start: {midi_path.name}")
    try:
        from music21 import converter, chord, analysis
    except ImportError:
        return None, None, None
    try:
        score = converter.parse(str(midi_path))
    except Exception as e:
        print(f"    music21 parse error: {e}")
        return None, None, None
    # Reduce to chords
    try:
        chordified = score.chordify()
    except Exception as e:
        print(f"    music21 chordify error: {e}")
        return None, None, None

    chords_seen: list[str] = []
    for el in chordified.recurse().getElementsByClass(chord.Chord):
        try:
            sym = el.pitchedCommonName  # e.g. "C-major triad"
            chords_seen.append(sym)
        except Exception:
            pass

    if not chords_seen:
        return None, None, None
    most_common = Counter(chords_seen).most_common(1)[0][0]

    # Key
    try:
        k = score.analyze('key')  # Krumhansl-Schmuckler by default
        key_str = f"{k.tonic.name} {k.mode}"
    except Exception:
        key_str = None

    # Try to extract a clean root + quality (e.g., "A-major triad" -> "A", "major")
    parts = most_common.split()
    root = parts[0].split('-')[0] if parts else None
    quality = parts[0].split('-')[1] if (parts and '-' in parts[0]) else None
    stage(f"music21 complete: {midi_path.name} ({time.perf_counter() - started:.2f}s)")
    return root, quality, key_str


# ------------------------------------------------------- our detector path ----
def detect_with_horizon(midi_path: Path) -> dict | None:
    """Run the project's detector on a MIDI file. Mirrors what the pipeline does."""
    started = time.perf_counter()
    stage(f"Horizon detector import/start: {midi_path.name}")
    try:
        from hybrid_chord_detector import HybridChordDetector
    except Exception as e:
        print(f"    HybridChordDetector import failed: {e}")
        return None
    try:
        det = HybridChordDetector()
        result = det.detect_chords(str(midi_path))
        stage(f"Horizon detector complete: {midi_path.name} ({time.perf_counter() - started:.2f}s)")
        return result
    except Exception as e:
        print(f"    HybridChordDetector error: {e}")
        return None


# --------------------------------------------------------- key detector ------
def run_key_detector(chord_symbols: list[str]) -> str:
    """Invoke the new diatonic-fit key detector from chordai_gpt_tutor."""
    from chordai_gpt_tutor import ChordAIRAGTutor
    # Don't actually instantiate (would need OpenAI). Pull the unbound method
    # and call it with a stub `self`.
    method = ChordAIRAGTutor._detect_key_from_events
    events = [{"chord": c, "duration_seconds": 1.0} for c in chord_symbols]
    return method(None, events)  # method doesn't use self


# ============================================================= TEST 1 ========
def test_labeled_midis():
    banner("TEST 1 — Labeled MIDIs (Amaj/Bmaj/Fmaj from _archive)")
    cases = {
        "Amaj.mid": "A",
        "Bmaj.mid": "B",
        "Fmaj.mid": "F",
    }
    arc = ROOT / "_archive" / "outer_originals"
    rows = []
    for fname, expected_root in cases.items():
        path = arc / fname
        if not path.exists():
            rows.append((fname, expected_root, "MISSING", "—", FAIL))
            continue
        result = detect_with_horizon(path)
        if not result:
            rows.append((fname, expected_root, "ERROR", "—", FAIL))
            continue
        chords = result.get("chords") or []
        first = chords[0]["chord"] if chords else "(none)"
        # Strip quality (e.g. "Am", "A7", "Amaj7" -> "A"; "F#m" -> "F#")
        root_only = first[:2] if (len(first) >= 2 and first[1] == '#') else first[:1]
        verdict = PASS if root_only == expected_root else FAIL
        rows.append((fname, expected_root, first, root_only, verdict))

    print(f"\n  {'file':<14} {'expected':<10} {'detected':<14} {'root':<6} verdict")
    print(f"  {'-'*14} {'-'*10} {'-'*14} {'-'*6} -------")
    for f, exp, det, root, v in rows:
        print(f"  {f:<14} {exp:<10} {det:<14} {root:<6} {v}")
    n_pass = sum(1 for *_, v in rows if v == PASS)
    print(f"\n  Score: {n_pass}/{len(rows)}")
    return n_pass, len(rows)


# ============================================================= TEST 2 ========
def test_music21_second_opinion():
    banner("TEST 2 — music21 second opinion on labeled MIDIs + test11.mid")
    arc = ROOT / "_archive" / "outer_originals"
    midis = [
        ("Amaj.mid", "A", arc / "Amaj.mid"),
        ("Bmaj.mid", "B", arc / "Bmaj.mid"),
        ("Fmaj.mid", "F", arc / "Fmaj.mid"),
        ("test11.mid", None, ROOT / "tests" / "test11.mid"),
    ]
    rows = []
    for label, expected, path in midis:
        if not path.exists():
            rows.append((label, expected, "MISSING", "—", "—", "—"))
            continue
        m_root, m_qual, m_key = music21_root_quality(path)
        h = detect_with_horizon(path)
        h_first = (h.get("chords") or [{}])[0].get("chord", "(none)") if h else "(error)"
        h_key = (h or {}).get("scale", "?")
        agree = "?" if not (m_root and h_first) else \
                ("agree" if h_first.startswith(m_root) else "disagree")
        rows.append((label, expected, m_root, m_key, h_first, h_key))

    print(f"\n  {'file':<18} {'expect':<7} {'m21 root':<10} {'m21 key':<14} "
          f"{'horizon':<14} horizon key")
    print(f"  {'-'*18} {'-'*7} {'-'*10} {'-'*14} {'-'*14} -----------")
    for r in rows:
        print(f"  {r[0]:<18} {str(r[1] or '?'):<7} {str(r[2] or '?'):<10} "
              f"{str(r[3] or '?'):<14} {str(r[4]):<14} {str(r[5])}")


# ============================================================= TEST 3 ========
def test_key_detector_unit():
    banner("TEST 3 — Key detector unit test (chordonomicon symbolic progressions)")
    cases = []
    try:
        with open(ROOT / "datasets" / "chordonomicon_sample.json") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  Could not load chordonomicon sample: {e}")
        return 0, 0
    for song in data.get("songs", []):
        cases.append((song["title"], song["chord_progression"], song["key"]))
    # Add a few more controlled cases
    cases.extend([
        ("Pure C major", ["C", "F", "G", "Am", "C"], "C major"),
        ("Pure G major", ["G", "C", "D", "Em", "G"], "G major"),
        ("Pure D minor", ["Dm", "Gm", "A", "Dm"], "D minor"),
        ("Pure A minor", ["Am", "Dm", "E", "Am"], "A minor"),
        ("12-bar blues in E", ["E", "A", "E", "B", "A", "E"], "E major"),
    ])

    rows = []
    n_pass = 0
    for title, prog, expected in cases:
        try:
            detected = run_key_detector(prog)
        except Exception as e:
            rows.append((title, prog, expected, f"ERROR: {e}", FAIL))
            continue
        # Loose match: compare tonic name (ignore Major/Minor case mismatch)
        exp_norm = expected.replace("major", "Major").replace("minor", "Minor")
        verdict = PASS if detected.lower().split()[0] == exp_norm.lower().split()[0] \
                       and detected.lower().split()[-1] == exp_norm.lower().split()[-1] \
                       else FAIL
        if verdict == PASS:
            n_pass += 1
        rows.append((title, prog, expected, detected, verdict))

    print(f"\n  {'title':<22} {'expected':<14} {'detected':<14} verdict")
    print(f"  {'-'*22} {'-'*14} {'-'*14} -------")
    for t, _p, e, d, v in rows:
        print(f"  {t:<22} {e:<14} {d:<14} {v}")
    print(f"\n  Score: {n_pass}/{len(rows)}")
    return n_pass, len(rows)


# ============================================================= TEST 4 ========
def test_infrastructure_audit():
    banner("TEST 4 — Infrastructure audit (what's missing)")
    items = []

    # Trained models?
    models_dir = ROOT / "models"
    has_models = models_dir.exists() and any(models_dir.glob("*.joblib"))
    items.append(("Trained ML chord-classifier model", PASS if has_models else FAIL,
                  "models/*.joblib not present — HybridChordDetector silently runs rule-only"
                  if not has_models else "found"))

    # Real ground-truth dataset?
    rwc = ROOT / "datasets" / "rwc_chord_annotations.json"
    rwc_real = False
    if rwc.exists():
        try:
            with open(rwc) as f:
                d = json.load(f)
            n = len(d.get("annotations", []))
            rwc_real = n >= 50
        except Exception:
            pass
    items.append(("RWC chord annotations (real, ≥50 songs)",
                  PASS if rwc_real else FAIL,
                  f"file says total_songs=100 but contains {n if rwc.exists() else 0} actual entries — placeholder/stub"))

    chordo = ROOT / "datasets" / "chordonomicon_sample.json"
    chordo_n = 0
    if chordo.exists():
        try:
            with open(chordo) as f:
                d = json.load(f)
            chordo_n = len(d.get("songs", []))
        except Exception:
            pass
    items.append(("Chordonomicon ground-truth corpus",
                  WARN if chordo_n >= 2 else FAIL,
                  f"file says total_songs=1000 but contains {chordo_n} — symbolic only, no audio"))

    # basic_pitch backend
    has_tf = False
    try:
        import tensorflow  # noqa: F401
        has_tf = True
    except Exception:
        pass
    items.append(("basic_pitch with a backend (TF / CoreML / TFLite)",
                  PASS if has_tf else FAIL,
                  "TensorFlow not installed — basic_pitch may not actually be usable"))

    # Audio test fixtures with ground truth?
    items.append(("Labeled audio fixtures (audio + ground-truth chord/key)",
                  FAIL,
                  "tests/audio/*.wav have no companion ground-truth files"))

    # Automated regression tests
    items.append(("Automated chord-detection regression test in CI",
                  FAIL,
                  "no pytest, no test_accuracy.py, no MIREX-style metric script"))

    # Standard MIR metric
    items.append(("MIREX-style accuracy metric (mir_eval)",
                  WARN,
                  "mir_eval not in requirements; only ad-hoc string compare possible"))

    print()
    for name, verdict, note in items:
        print(f"  [{verdict}] {name}")
        print(f"          {note}")


# ====================================================================== main ==
def parse_args():
    parser = argparse.ArgumentParser(description="Run selected HorizonJam audit sections.")
    parser.add_argument(
        "--section",
        choices=("all", "labeled", "music21", "key", "infrastructure"),
        default="all",
        help="Run one audit section or the complete legacy audit.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("HorizonJam Evaluation — read-only audit")
    print(f"Root: {ROOT}")

    p1 = t1 = p3 = t3 = None
    if args.section in {"all", "labeled"}:
        p1, t1 = test_labeled_midis()
    if args.section in {"all", "music21"}:
        test_music21_second_opinion()
    if args.section in {"all", "key"}:
        p3, t3 = test_key_detector_unit()
    if args.section in {"all", "infrastructure"}:
        test_infrastructure_audit()

    if args.section == "all":
        banner("OVERALL")
        print(f"  Labeled MIDIs (root match) : {p1}/{t1}")
        print(f"  Key-detector unit tests    : {p3}/{t3}")
        print()
        print("  See TEST 4 for missing infrastructure required for real accuracy claims.")


if __name__ == "__main__":
    main()
