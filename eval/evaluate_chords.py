"""Run every synth WAV through every detector via the centralized detection
layer (`detection.run_detection`), score via mir_eval, write reports.

Using the detection layer means we test the SAME code path the web app uses —
including the normalization that fixes overlapping intervals, sorts events,
and merges adjacent identical chords. This is what closes the gap that
caused mir_eval to refuse to score the production detector before.

Outputs:
  eval/report.md
  eval/report.json
"""
from __future__ import annotations

import io
import json
import sys
import warnings as _warnings
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

_warnings.filterwarnings("ignore")

import numpy as np
import mir_eval

EVAL_DIR = Path(__file__).parent
REPO = EVAL_DIR.parent
MANIFEST = EVAL_DIR / "synth_manifest.json"
REPORT_MD = EVAL_DIR / "report.md"
REPORT_JSON = EVAL_DIR / "report.json"

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


# ----------------------------- label normalization ------------------------
def to_harte(label):
    """Convert internal chord symbols ('Am', 'F#m7', 'Bb') to mir_eval Harte
    format ('A:min', 'F#:min7', 'Bb:maj'). 'N' or unparseable -> 'N'."""
    if not label or str(label).strip() in ("", "N", "Unknown", "X", "?"):
        return "N"
    s = str(label).strip()
    if len(s) >= 2 and s[1] in ("#", "b"):
        root, rest = s[:2], s[2:]
    else:
        root, rest = s[:1], s[1:]
    if not root or root[0].upper() not in "ABCDEFG":
        return "N"
    root = root[0].upper() + (root[1:] if len(root) > 1 else "")
    rest = rest.strip()
    if rest.startswith("maj7"):    return f"{root}:maj7"
    if rest.startswith("maj"):     return f"{root}:maj"
    if rest.startswith("min7") or rest.startswith("m7"): return f"{root}:min7"
    if rest.startswith("dim7"):    return f"{root}:dim7"
    if rest.startswith("dim") or rest.startswith("°") or rest.startswith("o"): return f"{root}:dim"
    if rest.startswith("aug") or rest.startswith("+"): return f"{root}:aug"
    if rest.startswith("sus2"):    return f"{root}:sus2"
    if rest.startswith("sus4") or rest.startswith("sus"): return f"{root}:sus4"
    if rest.startswith("min") or (rest.startswith("m") and not rest.startswith("maj")): return f"{root}:min"
    if rest.startswith("7"):       return f"{root}:7"
    if rest == "":                 return f"{root}:maj"
    return f"{root}:maj"


# ----------------------------- one-time load ------------------------------
print("Loading detection layer...", flush=True)
with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
    import detection  # type: ignore

# Pre-warm both underlying engines so the first per-song call isn't a 10s cold-start.
# A no-op call on a tiny dummy WAV would be ideal but it's simpler to just let the
# first real song eat the cost and report.
print("Detection layer ready.", flush=True)


# ----------------------------- mir_eval scaffolding ----------------------
def load_lab(lab_path):
    intervals, labels = [], []
    with open(lab_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            intervals.append([float(parts[0]), float(parts[1])])
            labels.append(parts[2])
    return np.array(intervals), labels


def detection_events_to_arrays(events, max_time):
    """Convert detection-layer events (chord field) to mir_eval Harte intervals."""
    if not events:
        return np.empty((0, 2)), []
    rows, labs = [], []
    for e in events:
        s = max(0.0, float(e["start"]))
        t = min(max_time, float(e["end"]))
        if t > s:
            rows.append([s, t])
            labs.append(to_harte(e.get("chord")))
    if not rows:
        return np.empty((0, 2)), []
    return np.array(rows), labs


def fill_gaps_with_N(intervals, labels, total_dur):
    """mir_eval requires est to cover the full ref time range — pad with 'N'."""
    if intervals.size == 0:
        return np.array([[0.0, total_dur]]), ["N"]
    order = np.argsort(intervals[:, 0])
    intervals = intervals[order]
    labels = [labels[i] for i in order]
    out_i, out_l, cursor = [], [], 0.0
    for (s, e), lab in zip(intervals, labels):
        if s > cursor + 1e-3:
            out_i.append([cursor, s]); out_l.append("N")
        out_i.append([s, e]); out_l.append(lab)
        cursor = max(cursor, e)
    if cursor < total_dur - 1e-3:
        out_i.append([cursor, total_dur]); out_l.append("N")
    return np.array(out_i), out_l


def confusion_pair(ref, est):
    """'C:maj->A:min' — preserves quality so quality-only confusions show up."""
    return f"{ref or 'N'}->{est or 'N'}"


def score_one(wav_path, lab_path, detector_name):
    ref_intervals, ref_labels = load_lab(lab_path)
    if ref_intervals.size == 0:
        return {"error": "empty reference"}
    total_dur = float(ref_intervals[-1, 1])

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = detection.run_detection(wav_path, detector=detector_name)
    except Exception as e:
        return {"error": f"detection raised {type(e).__name__}: {e}"}

    events = result.get("chord_events", [])
    est_raw_i, est_raw_l = detection_events_to_arrays(events, total_dur)
    est_i, est_l = fill_gaps_with_N(est_raw_i, est_raw_l, total_dur)

    try:
        scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_i, est_l)
    except Exception as e:
        return {"error": f"mir_eval failed: {type(e).__name__}: {e}",
                "events_count": len(events)}

    confusions = Counter()
    try:
        m_i, m_r, m_e = mir_eval.util.merge_labeled_intervals(
            ref_intervals, ref_labels, est_i, est_l)
        for (s, e), r, est in zip(m_i, m_r, m_e):
            if r != est:
                confusions[confusion_pair(r, est)] += float(e - s)
    except Exception:
        pass

    return {
        "scores": {k: float(v) for k, v in scores.items()},
        "events_count": len(events),
        "warnings_count": len(result.get("warnings", [])),
        "confusions": confusions.most_common(3),
    }


# ----------------------------- main --------------------------------------
def main():
    if not MANIFEST.exists():
        print(f"Manifest not found: {MANIFEST}. Run synth_dataset.py first.")
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    songs = manifest["songs"]
    detectors = ["production", "hybrid", "rule_viterbi", "rule_jaccard"]
    print(f"\nEvaluating {len(songs)} songs x {len(detectors)} detectors "
          f"via detection.run_detection()...\n", flush=True)

    per_song = {d: {} for d in detectors}

    for i, song in enumerate(songs, 1):
        name = song["name"]
        wav = song.get("wav")
        lab = song["labels"]

        if not wav or not Path(wav).exists():
            for d in detectors:
                per_song[d][name] = {"error": "no wav"}
            continue

        print(f"  [{i:2d}/{len(songs)}] {name}", flush=True)
        for d in detectors:
            try:
                per_song[d][name] = score_one(wav, lab, d)
            except Exception as e:
                per_song[d][name] = {"error": f"{type(e).__name__}: {e}"}

    # ----- aggregate -----
    METRICS = ["root", "majmin", "sevenths", "mirex"]
    summary = {}
    for det, rows in per_song.items():
        ok = [r for r in rows.values() if "scores" in r]
        failed = [r for r in rows.values() if "error" in r]
        agg = {m: (float(np.mean([r["scores"][m] for r in ok])) if ok else None)
               for m in METRICS}
        n_warnings = sum(r.get("warnings_count", 0) for r in ok)
        summary[det] = {**agg, "wcsr": agg["majmin"],
                        "files_ok": len(ok), "files_failed": len(failed),
                        "warnings_total": n_warnings}

    failures = {}
    for det, rows in per_song.items():
        agg = Counter()
        for row in rows.values():
            if "scores" not in row:
                continue
            for pair, weight in row.get("confusions", []):
                agg[pair] += weight
        failures[det] = agg.most_common(5)

    import os as _os
    default_det = detection.selected_detector()
    env_set = _os.environ.get("HORIZONJAM_DETECTOR")

    report = {
        "dataset": {
            "count": len(songs),
            "songs_with_wav": sum(1 for s in songs if s.get("wav")),
            "renderers": manifest.get("renderers", {}),
        },
        "default_detector": default_det,
        "env_HORIZONJAM_DETECTOR": env_set,
        "summary": summary,
        "failure_patterns": failures,
        "per_song": per_song,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # ----- markdown -----
    lines = []
    lines.append("# HorizonJam Chord Detection - Synthetic Eval Report")
    lines.append("")
    lines.append(f"Dataset: **{len(songs)} synthetic progressions**, renderer: {manifest.get('renderers')}")
    lines.append(f"Default detector (HORIZONJAM_DETECTOR): **{default_det}** "
                 f"{'(env set to ' + env_set + ')' if env_set else '(env not set, using default)'}")
    lines.append("")
    lines.append("All detectors run via `detection.run_detection()` so events are "
                 "sorted, non-overlapping, and adjacent identicals are merged before "
                 "scoring. This is the same path the web app uses.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Detector | Root | MajMin | Sevenths | MIREX | WCSR | Files OK | Files Failed | Total Warnings |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    def fmt(v): return f"{v:.3f}" if isinstance(v, (int, float)) else "-"
    for det in detectors:
        s = summary[det]
        lines.append(
            f"| {det} | {fmt(s['root'])} | {fmt(s['majmin'])} | "
            f"{fmt(s['sevenths'])} | {fmt(s['mirex'])} | {fmt(s['wcsr'])} | "
            f"{s['files_ok']} | {s['files_failed']} | {s['warnings_total']} |"
        )

    lines.append("")
    lines.append("**Reading the metrics:**")
    lines.append("- `Root` - root note correct, ignoring quality.")
    lines.append("- `MajMin` - root + major/minor quality match. The practical floor.")
    lines.append("- `Sevenths` - same as MajMin plus 7th-chord extensions.")
    lines.append("- `MIREX` - official MIREX comparison metric.")
    lines.append("- `WCSR` - Weighted Chord Symbol Recall (= MajMin under equal-duration songs).")
    lines.append("- `Total Warnings` - normalization repairs the detection layer made (overlaps clamped, etc.).")
    lines.append("")
    lines.append("Today `hybrid` and `rule_viterbi` are functionally identical "
                 "(`HybridChordDetector.ml_available = False`, no trained model). Both rows are kept "
                 "so this harness can re-run unchanged once an ML model is trained.")
    lines.append("`rule_jaccard` is an opt-in production-path experiment. It keeps "
                 "transcription, segmentation, smoothing, normalization, candidate "
                 "templates, key priors, and bass scoring fixed while replacing only "
                 "the advanced scorer's asymmetric template coverage with Jaccard.")

    lines.append("")
    lines.append("## Failure patterns (top confusion pairs, duration-weighted)")
    for det in detectors:
        lines.append(f"\n### `{det}`")
        f = failures.get(det, [])
        if not f:
            lines.append("- (no confusions captured)")
        else:
            for pair, weight in f:
                lines.append(f"- `{pair}` ({weight:.1f}s)")

    lines.append("")
    lines.append("## Detector errors")
    for det in detectors:
        errs = {k: v.get("error") for k, v in per_song[det].items() if "error" in v}
        if not errs:
            lines.append(f"\n### `{det}`: no errors")
            continue
        lines.append(f"\n### `{det}`: {len(errs)} failures")
        kind = Counter([(e[:80] if e else "") for e in errs.values()])
        for msg, n in kind.most_common(5):
            lines.append(f"- ({n}x) `{msg}`")

    lines.append("")
    lines.append("## Per-song scores (first 15)")
    lines.append("")
    lines.append("| Song | Detector | Root | MajMin | Sevenths | Events | Warnings |")
    lines.append("|---|---|---|---|---|---|---|")
    for song in songs[:15]:
        for det in detectors:
            r = per_song[det].get(song["name"], {})
            if "scores" in r:
                lines.append(
                    f"| {song['name']} | {det} | "
                    f"{r['scores'].get('root', 0):.2f} | "
                    f"{r['scores'].get('majmin', 0):.2f} | "
                    f"{r['scores'].get('sevenths', 0):.2f} | "
                    f"{r.get('events_count', 0)} | {r.get('warnings_count', 0)} |"
                )
            else:
                lines.append(f"| {song['name']} | {det} | - | - | - | - | err: {(r.get('error') or '')[:40]} |")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nWrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print()
    print(f"Default detector: {default_det} "
          f"(HORIZONJAM_DETECTOR={'set to ' + env_set if env_set else 'unset, using default'})")
    print("Summary (MajMin):")
    for det in detectors:
        s = summary[det]
        mm = s["majmin"]
        print(f"  {det:14s} MajMin = {fmt(mm)}  "
              f"({s['files_ok']} ok, {s['files_failed']} failed, "
              f"{s['warnings_total']} normalize-warnings)")


if __name__ == "__main__":
    main()
