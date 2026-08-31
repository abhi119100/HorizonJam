# HorizonJam — Session Handoff

> Paste this as the opening message in a new Claude chat, or drop it next to a `CLAUDE.md`. It's self-contained — a fresh agent should be able to resume without re-reading prior conversation.

---

## 1. Project overview & current state

**HorizonJam** is an AI music tutor with a Discovery-Mode focus:

> A musician records (or uploads) a short audio clip → backend detects the chord progression → an AI tutor explains in beginner-friendly language *why* the progression sounds the way it does.

### Architecture (three services)

```
Browser (Next.js, port 3000)
        │
        │ POST /upload-audio  +  WS /ws/tutor
        ▼
Tutor WebSocket Relay (FastAPI, port 8001) ── tutor_ws_relay.py
        │ calls into ChordAIRAGTutor
        ▼                                    ┌──── HTTP POST /tts ───▶ TTS Server (port 5000)
chordai_gpt_tutor.py                          │                          (Moshi → OpenAI fallback)
        │
        └──▶ detection.py  ←── HORIZONJAM_DETECTOR env var (default: hybrid)
              ├── production    AccurateAudioToChordsPipeline (legacy, kept as fallback)
              ├── hybrid        HybridChordDetector(use_viterbi=True)   ← live default
              └── rule_viterbi  same as hybrid until ML model trained
              │
              └──▶ normalize_and_validate() — sort, dedupe, clamp overlaps
              ▼
        chord_events (normalized) ──▶ KS key detection (music21) ──▶ RAG (ChromaDB) ──▶ GPT-4o tutor ──▶ TTS stream
```

### Where the code lives

```
C:\Users\abhij\Downloads\HorizonJam\           ← flat, single root (414 MB)
├── detection.py                                 ← Phase-2 detector selection + normalization
├── chordai_gpt_tutor.py                         ← orchestrator (RAG + GPT + chord coordination)
├── tutor_ws_relay.py                            ← WS relay, /upload-audio, /ws/tutor
├── tts_server.py                                ← TTS endpoint (Moshi local + OpenAI fallback)
├── unified_rag_system.py                        ← ChromaDB wrapper
├── chord_detection.py                           ← CLI to run/train/collect-data
├── run_pipeline.py                              ← CLI for AccurateAudioToChordsPipeline
├── src/
│   ├── pipeline.py                              ← prod path orchestrator
│   ├── midi_converter.py                        ← basic_pitch (ONNX) wrapper
│   ├── chord_detector.py            (2425 ln)   ← MIDI → chord events; chroma + music21
│   ├── hybrid_chord_detector.py     ( 483 ln)   ← rule + ML + Viterbi (ML branch dormant)
│   ├── gp_dataset_integration.py    ( 463 ln)   ← uses datasets/all_parsed_gp_data.json (22 GP songs)
│   ├── musical_intelligence.py      ( 388 ln)   ← Roman numerals, genre priors (UNUSED today)
│   ├── viterbi_smoothing.py
│   └── ml_chord_trainer.py                      ← ready to use; no model trained yet
├── eval/
│   ├── synth_dataset.py                         ← generates 40 synthetic MIDIs + labels + WAVs
│   ├── run_detector.py                          ← --detector CLI (subprocess wrapper)
│   ├── evaluate_chords.py                       ← in-process eval harness, mir_eval scoring
│   ├── manual_mic_test_plan.md                  ← 8 progressions, recording conditions
│   ├── manual_mic_results.md                    ← results template — USER TO FILL
│   ├── report.md / report.json                  ← latest eval output
│   └── data/synth/{midi,labels,wav}/            ← 40 of each
├── nextjs-frontend/
│   ├── pages/index.js               ( ~900 ln)  ← single-page app (recording UI + analysis display)
│   └── next.config.js                           ← outputFileTracingRoot pinned to workspace root
├── RAG/
│   ├── unified_chroma_store/                    ← 10 docs (4 are scraper failures — see #4)
│   └── scraped_data.json                        ← 11 sources; Wikipedia 107KB dropped on embed
├── datasets/
│   ├── all_parsed_gp_data.json                  ← REAL 22 Guitar Pro songs
│   ├── full_key_signature_library.json          ← REAL 26 keys diatonic chords (used by pipeline)
│   ├── chordonomicon_sample.json                ← STUB (2 songs, claims 1000)
│   └── rwc_chord_annotations.json               ← STUB (1 placeholder song)
├── tests/
│   ├── audio/{piano,pop,rock}.wav               ← unlabeled fixtures
│   └── test11.mid
├── _archive/                                    ← provenance preserved from old nested tree
│   ├── outer_originals/    (22 files)
│   ├── inner_originals/    (7 files)
│   └── docs/               (legacy READMEs)
├── _e2e_smoke.py                                ← Python WS client for end-to-end smoke
├── _evaluation.py                               ← KS unit tests + audit report
├── .env                                         ← OPENAI_API_KEY (rotated this session)
├── .env.example
└── .gitignore                                   ← includes .env, passwords.txt, etc.
```

### Current operational state

| Item | State |
|---|---|
| Project root | `C:\Users\abhij\Downloads\HorizonJam\` (flat, all changes applied) |
| Old nested tree | `C:\Users\abhij\Downloads\HorizonJam-final\` (~413 MB, untouched, awaiting user OK to delete) |
| Servers running | **❌ all DOWN** (need restart for next testing session) |
| Git repo | ❌ not initialized — `git init` is pending |
| OpenAI key | ✅ rotated, in `.env` |
| ML chord model | ❌ no `models/*.joblib` — `HybridChordDetector.ml_available = False` |
| RAG corpus | ⚠️ 10 docs; 4 are scraper failures; Wikipedia (107 KB, the biggest source) was dropped during embed |
| Default detector | ✅ `hybrid` via `HORIZONJAM_DETECTOR` env (default) |
| Latest eval numbers | production = 0.270 MajMin · hybrid = 0.517 MajMin (40/40 songs scored) |
| Latest e2e verified | pop.wav → A major, 31 chunks streamed, complete |

---

## 2. What was accomplished in this session

### A. Audit + critique (multi-pass)
- Diff'd the old vs new directory trees; found the project triple-nested
- Found two leaked OpenAI keys (passwords.txt + .env) → user rotated both, deleted passwords.txt
- Discovered production detection path was hardcoded to broken `AccurateAudioToChordsPipeline`
- Discovered `chord_training_database.json` "training data" is actually detector output on test11.mid
- Discovered `combined_training_samples.json` "ground truth" was fake (detected == ground_truth, accuracy=1.0)
- Discovered RAG corpus contains 4 scraper failure pages ("403 Forbidden", "Enable JavaScript")
- Discovered Wikipedia Music_theory article (107 KB) was scraped but never embedded
- Confirmed basic_pitch IS running correctly (uses ONNX, doesn't need TensorFlow)
- Confirmed `mir_eval` was already installed (initial report saying otherwise was wrong)

### B. Code bugs fixed
- **Duplicate dict key bug** in `_detect_key_from_events` (collapsed all candidate keys to one)
- **Fake `85.0` accuracy constant** in 4 places — replaced with `None`
- **UTF-8 stdout** on Windows — added `sys.stdout.reconfigure(encoding='utf-8')` to `chordai_gpt_tutor.py` and `tutor_ws_relay.py` so emoji prints don't crash when piped
- **Path-traversal-ish upload filename** — sanitized via `Path(filename).name`
- **`run_pipeline.py` import** — fixed `parent.parent / utils` → `parent / utils` after flatten
- **next.config.js missing** — created; `outputFileTracingRoot` pins workspace root, kills lockfile-walk warning caused by stray `C:\Users\abhij\Downloads\package-lock.json`
- **Speak/Stop buttons** — single shared `currentAudioRef` + `ttsGenRef` generation counter + sticky `playbackStoppedRef`; fixes parallel-instance and stop-doesn't-stop bugs
- **Mic Stop button** — removed premature `stream.getTracks().forEach(t => t.stop())` from `stopRecording`; that suppressed `MediaRecorder.onstop` on Chromium. Track stop now happens in `teardownRecorder()` called *after* `finishRecording()`. Watchdog 350ms → 800ms.

### C. Major restructure
- Flattened `HorizonJam-final/HorizonJam-final/HorizonJam-master/` → `HorizonJam/`
- Merged outer `utils/log_silencer.py`, outer `tests/audio + tests/midi`, outer `_archive` (provenance preserved under `_archive/{outer_originals,inner_originals,docs}/`)
- Deleted accidental top-level `unified_chroma_store/` (created by running check script from wrong cwd)

### D. Mic-recording feature (Phase 0b–1 of the product)
- Built `RecordPanel` UI in `pages/index.js`: idle / recording / recorded state machine
- Mic permission requested on click (not page load)
- Disabled `echoCancellation` / `noiseSuppression` / `autoGainControl` (kills music quality)
- VU meter via `AudioContext.createAnalyser` + `requestAnimationFrame`
- Hard cap 30s, auto-stops at MAX_RECORD_SECS
- Preview audio + Re-record + Analyze buttons
- **Browser-side WAV encoding** (`audioBufferToWav`) — bypasses server-side ffmpeg, which takes 15s per invocation on this Windows machine

### E. Backend conversion fallback (still used for file uploads)
- `tutor_ws_relay.py /upload-audio` accepts any format ffmpeg can decode
- Detects silence (`rms < 1e-3`) and zero-duration recordings
- Mic uploads (already WAV) skip the slow conversion path

### F. Evaluation harness (Phase 1)
- `eval/synth_dataset.py` — generates 40 MIDIs across 12 major keys × {I-IV-V-I}, 12 minor keys × {i-iv-V-i}, 6 keys × {ii-V-I, vi-IV-I-V}, 4 × {12-bar blues}
- Renders WAVs via `pretty_midi.synthesize()` (sine wave, no FluidSynth dep)
- `eval/run_detector.py` — uniform `--detector {production,hybrid,rule_viterbi}` CLI
- `eval/evaluate_chords.py` — in-process orchestrator, mir_eval scoring (Root/MajMin/Sevenths/MIREX/WCSR), writes `report.md` + `report.json`

### G. Detection layer (Phase 2 — most architecturally significant)
- `detection.py` (single top-level module):
  - `HORIZONJAM_DETECTOR` env var with default `hybrid`
  - `run_detection(wav_path, detector=None) → dict`
  - Normalized output contract: `chord_events[]` with `{start, end, chord, confidence, source_detector}` + `estimated_key`, `detector_used`, `warnings`
  - `normalize_and_validate()` — sort, drop bad labels, clamp negative starts, drop zero-duration events, clamp overlapping ends, merge adjacent identical chords
  - Structured logging via `horizonjam.detection` logger
- `chordai_gpt_tutor.py._run_horizon_jam` rewritten to delegate to `detection.run_detection()`, builds backward-compat event dict so old frontend still works
- `eval/evaluate_chords.py` re-routed through detection layer → production's mir_eval failures dropped from 32 to 0

### H. Phase 3 logging
- `detection.py` logs audio duration + sample rate + file size from header
- `tutor_ws_relay.py` `/upload-audio` logs filename + bytes + converted-from
- `chordai_gpt_tutor.py` logs `detector=X events_in=N events_out=M key=K warnings=W`

### I. Eval artifacts produced
- `eval/manual_mic_test_plan.md` — 8 progressions, recording conditions, scoring rubric, how-to-record steps
- `eval/manual_mic_results.md` — results template with 8 pre-stubbed rows + rollup
- `eval/report.md` + `eval/report.json` — latest synthetic eval results

### J. Last measured numbers (from `eval/report.md`)

| Detector | Root | MajMin | Sevenths | MIREX | WCSR | Files OK | Failed |
|---|---|---|---|---|---|---|---|
| production | 0.319 | 0.270 | 0.211 | 0.356 | 0.270 | 40 | 0 |
| **hybrid** ⭐ | 0.585 | **0.517** | 0.356 | 0.588 | 0.517 | 40 | 0 |
| rule_viterbi | 0.585 | 0.517 | 0.356 | 0.588 | 0.517 | 40 | 0 |

- Hybrid is ~2× production
- `rule_viterbi == hybrid` because no ML model trained yet
- Largest residual error: detector collapses 7th chords to triads (`G:7 → G:maj`, etc.)
- This is synthetic SINE-WAVE audio (FluidSynth wasn't installed). Real-instrument audio will move these numbers — possibly up (basic_pitch is trained on real instruments), possibly down (room noise)

---

## 3. Key decisions made — and why

| # | Decision | Reason |
|---|---|---|
| 1 | Flatten to `HorizonJam/` (not `HorizonJam-master/`) | An older 2.2 GB project already existed at `HorizonJam-master/` — chose a new name to avoid clobbering historical work |
| 2 | Browser-side WAV encoding for mic recordings | `ffmpeg` takes **15 seconds per invocation** on this Windows machine (Defender scan + GPU enumeration). Server-side conversion was unviable for any user-facing latency |
| 3 | Keep server-side ffmpeg fallback for file uploads | Users may still upload MP3/M4A/WebM directly; file upload is a secondary path, 15s latency is acceptable there |
| 4 | `HORIZONJAM_DETECTOR` env var, not a config file | Single switch, easy A/B in dev, no new file to maintain |
| 5 | Default detector = `hybrid` | Measured at 51.7% MajMin vs production's 27% on synthetic; ~2× better |
| 6 | Do NOT delete production path | Kept as fallback/debug; can be selected via env var for regression testing |
| 7 | Normalize ALL detector output via `normalize_and_validate()` | mir_eval refuses overlapping intervals (production used to emit them). Frontend display also assumes non-overlapping. Single normalization layer fixes both. |
| 8 | KS key detection via `music21.Stream.analyze('key')` | Hand-rolled chord-set membership had a known relative-major/minor failure (30% on common progressions). music21 implements KS properly. Still misses a couple genuinely ambiguous cases (e.g. Shape of You). |
| 9 | In-process eval, not subprocess-per-detection | Subprocess approach paid basic_pitch's ~10s cold-start cost 120 times; eval stalled at 13 min for one song. In-process: pre-load once, ~6 min total. |
| 10 | Single shared `currentAudioRef` for both WS streaming and TTS button | The previous code created independent `Audio` elements with no reference kept → Stop couldn't pause anything; Speak created parallel instances |
| 11 | `playbackStoppedRef` sticky flag + `ttsGenRef` generation counter | Race-free: Stop sticks until next analysis or explicit Speak; late TTS fetches discard if user already clicked something |
| 12 | DON'T stop mic stream tracks inside `stopRecording` | Chromium suppresses `MediaRecorder.onstop` if the underlying tracks die before the recorder finalizes. Tracks are stopped inside `teardownRecorder()` which runs from `finishRecording()` (i.e., AFTER onstop or watchdog) |
| 13 | 800ms watchdog on `mr.onstop` | Some browsers drop `onstop` silently. Watchdog force-finalizes after 800ms so the UI never hangs in "recording" state |
| 14 | Don't auto-resume WS audio after Stop | User clicked Stop; WS chunks arriving after that should NOT auto-resume. `playbackStoppedRef` sticks until next analysis or Speak. |
| 15 | Synthetic dataset only (no GuitarSet download) | Synthetic gives upper-bound metric in <1 hour; GuitarSet is 3 GB and pending until baseline numbers exist |
| 16 | `pretty_midi.synthesize()` fallback when FluidSynth absent | Don't block the eval harness on a missing system binary. Sine-wave audio gives clean pitch info; basic_pitch is weaker on it but the test still runs. |

---

## 4. Current blockers & open requests

### Blocked on user action
- **Manual mic tests (Phase 3A)** — record 4–6 of the 8 progressions in `eval/manual_mic_test_plan.md`, fill rows in `eval/manual_mic_results.md`, share results. Servers need to be restarted to run these (none listening right now).
- **Delete old tree?** — `C:\Users\abhij\Downloads\HorizonJam-final\` (~413 MB) untouched; awaiting your OK to remove
- **`git init` not done yet** — was pending your OK; ready to do whenever

### Open architectural debts (no immediate action)
- **`models/*.joblib` does not exist** → `HybridChordDetector.ml_available = False` → "hybrid" is currently just "rule + Viterbi". The training infrastructure (`chord_detection.py --collect`, `--train`) exists but has never been run with real labeled data.
- **RAG corpus is polluted** — 4 of 10 documents are scraper-failure pages; the Wikipedia Music_theory article (107 KB, the biggest single source) was dropped during the embed step
- **No real labeled audio dataset** — all measurement is on synthetic sine-wave audio
- **`MusicalIntelligenceEngine`** (Roman numerals, genre priors, progression patterns) exists but is **not wired into the pipeline today**
- **Production path emits overlapping intervals** on synthetic clean audio (root cause: emits one event per note onset, not per chord). Normalizer hides this from mir_eval. Real fix would be in `chord_detector.py`.
- **`chord_detector.py` collapses 7th chords to triads** — biggest residual error in current eval (`G:7 → G:maj`, etc.)

### Known fragility / things you'll trip over
- See section 6 below

---

## 5. Where to resume — exact next steps

**Step 1 (user, ~30 min):** Run the manual mic tests.
```powershell
cd C:\Users\abhij\Downloads\HorizonJam

# Terminal 1
python -m uvicorn tts_server:app --host 0.0.0.0 --port 5000

# Terminal 2 (uses hybrid by default — HORIZONJAM_DETECTOR unset)
python tutor_ws_relay.py

# Terminal 3
npm run dev
```
Open http://localhost:3000, work through `eval/manual_mic_test_plan.md`, fill `eval/manual_mic_results.md`. Aim for at least 4–6 of the 8 progressions.

**Step 2:** Share results in chat. Based on what comes back, choose one branch:

- **If 6+/8 progressions are Good**: detection is shippable for a v1 demo. Move to:
  - Lock the structured JSON contract for the tutor (already 90% done — just confirm field names)
  - Draft the layered tutor system prompt (Feeling → Theory → Understanding)
  - Design the Discovery Mode post-analysis screen (chord timeline + plain-English explanation as the first thing the user sees)

- **If results are Partial/Bad**: detection needs tuning before Discovery Mode UI work:
  - Inspect the failure rows for common patterns
  - Decide between (a) tune existing rule + Viterbi, (b) install FluidSynth + re-eval on realistic audio, (c) train the ML model on synthesized labeled data

**Step 3 (anytime after step 1):**
- `git init` + first commit (low risk, ~2 min)
- Delete old `C:\Users\abhij\Downloads\HorizonJam-final\` tree (~413 MB) once the new tree is confirmed good

**Step 4 (deferred — DO NOT start until step 2 decision made):**
- GuitarSet download (3 GB, real labeled audio for real numbers)
- ML model training
- RAG re-embed (clean failures + restore Wikipedia)

---

## 6. Important context, gotchas, and patterns

### Windows + Python gotchas
- **Default stdout is cp1252 when piped.** Any `print("✅ ...")` crashes with `UnicodeEncodeError`. Fix is `sys.stdout.reconfigure(encoding='utf-8')` early in module. Already applied to `chordai_gpt_tutor.py` and `tutor_ws_relay.py`.
- **`ffmpeg` takes ~15s per invocation** on this machine. Likely Defender real-time scan or GPU backend enumeration. Server-side audio conversion is unviable on the hot path — browser does WAV encoding instead. Don't add `pydub` or `audioread` to the hot path.
- **Python 3.13** + `pkg_resources` deprecation warning from `pretty_midi` — benign, ignore.

### Frontend gotchas
- **MediaRecorder does NOT produce WAV.** Chrome → WebM/Opus, Safari → MP4/AAC. We decode via `AudioContext.decodeAudioData()` and encode WAV in browser (`audioBufferToWav`). Don't try to fix this server-side; ffmpeg is too slow here.
- **Don't kill mic tracks before `MediaRecorder.onstop` fires.** Chromium silently suppresses `onstop` if the underlying tracks die mid-finalization. Tracks are stopped in `teardownRecorder()` which runs from `finishRecording()` AFTER onstop.
- **Audio playback in React with HMR:** the single shared `currentAudioRef` pattern is critical. Without it, every `new Audio(url)` creates a parallel instance that can't be stopped. Same for the `ttsGenRef` generation counter — fetches that resolve after Stop must discard.
- **`window.AudioContext || window.webkitAudioContext`** TypeScript hints are benign — Safari needs the webkit prefix.
- **Stray `C:\Users\abhij\Downloads\package-lock.json` + `node_modules`** outside the project — `nextjs-frontend/next.config.js` sets `outputFileTracingRoot` to pin the workspace and kill the "multiple lockfiles" warning. Don't remove that config without removing those stray files first.

### Detection architecture gotchas
- **Two detection stacks exist.** `AccurateAudioToChordsPipeline` (production, fast on real audio, broken on simple synth) vs `HybridChordDetector` (works on MIDI; rule + Viterbi; ML branch dormant). `detection.py` is the abstraction layer; pick via `HORIZONJAM_DETECTOR`.
- **`HybridChordDetector` takes MIDI input.** When WAV is fed in via `detection.py`, we transcribe via `basic_pitch` first to keep apples-to-apples with production.
- **`basic_pitch` works without TensorFlow.** It ships an ONNX model (`nmp.onnx`) and `onnxruntime` is installed. The TF/CoreML/TFLite warnings at import time are noise — model loads via ONNX. Don't install TensorFlow to "fix" this.
- **`models/` is empty.** `HybridChordDetector.ml_available = False`. `hybrid` and `rule_viterbi` are functionally identical. If you train a model, only `hybrid` will diverge.
- **All detector output MUST go through `normalize_and_validate()`.** Direct callers will hit mir_eval errors (overlap), frontend timeline display bugs, etc. The `detection.run_detection()` API is the only sanctioned entry point.

### Key detection gotchas
- **Krumhansl-Schmuckler via music21** still misses relative-major/minor when chord set fully overlaps (e.g., Shape of You `Am-F-C-G` picks C major). This is a known KS limitation, not our bug.
- **music21's `harmony.ChordSymbol` parser fails on some labels** ("Esus2", "Perfect Fifth", "Perfect Octave"). The KS detector silently skips these and reports the count in the log. Don't try to fix downstream — these come from the detector's interval-label fallback.

### RAG gotchas
- **Top 4/10 retrieved documents may be scraper failures.** The corpus needs re-embedding before tutor quality becomes credible.
- **Wikipedia article (107 KB) was scraped but never embedded.** Bug in `RAG/embed_enhanced_music_data.py`. Largest single source missing.
- **Tutor explanations sometimes feel generic** — likely RAG noise above.

### Eval harness gotchas
- **Subprocess-per-detection caused 30+ minute stalls.** Use `eval/evaluate_chords.py` (in-process). The `eval/run_detector.py` CLI exists for one-off use; don't loop it.
- **Sine-wave synthesis ≠ real audio.** `basic_pitch` is trained on real instruments. Sine waves may give weak transcription. Install FluidSynth + re-render before drawing strong conclusions.
- **`mir_eval` requires non-overlapping intervals.** Always pass output through `normalize_and_validate()` first. The eval harness does this automatically because it routes through `detection.run_detection()`.

### File-system gotchas
- **`HorizonJam-final/` (old nested tree, ~413 MB) still on disk.** Awaiting OK to delete. Don't delete without confirmation.
- **No git repo yet.** `git init` is the obvious first step but hasn't been run; expect a fresh history.
- **`.env` and `passwords.txt` are in `.gitignore`** — verify before first commit.
- **`_archive/` has three subdirs** (`outer_originals/`, `inner_originals/`, `docs/`) preserving the provenance of the old nested tree's archives. Don't reorganize without preserving these.

### Three patterns being used consistently — DON'T break
- **Backward-compat event shape.** `chord_events[i]` has both old fields (`start_time`, `end_time`, `chord_symbol`, `duration_seconds`) AND new contract fields (`start`, `end`, `chord`, `confidence`, `source_detector`). Frontend reads the old names; future tutor code should prefer the new names. Don't drop the old fields.
- **Logging format.** Every analysis emits a greppable line: `✅ Detection complete: detector=X events_in=N events_out=M key=K warnings=W`. Don't lose this when adding new code; it's the only e2e debug surface.
- **`HORIZONJAM_DETECTOR=production` for regression testing.** When changing detection code, run `python eval/evaluate_chords.py` AND verify with both detectors via env var override before declaring done.

---

## Quick reference — useful commands

```powershell
# Start all 3 servers (run each in its own terminal)
cd C:\Users\abhij\Downloads\HorizonJam
python -m uvicorn tts_server:app --host 0.0.0.0 --port 5000
python tutor_ws_relay.py           # defaults to hybrid
npm run dev

# Override detector for A/B testing
$env:HORIZONJAM_DETECTOR = "production"; python tutor_ws_relay.py
# (or)
HORIZONJAM_DETECTOR=production python tutor_ws_relay.py    # Git Bash

# Re-run eval (writes eval/report.md + eval/report.json)
python eval/evaluate_chords.py

# Re-generate synthetic dataset (40 MIDIs + labels + WAVs)
python eval/synth_dataset.py

# End-to-end smoke test from Python (no browser needed)
python _e2e_smoke.py

# Quick KS key-detector unit tests
python _evaluation.py
```

---

## Quick reference — file locations for common questions

| If you want to… | Look at… |
|---|---|
| Add a new detector | `detection.py` — add a runner + `SUPPORTED` entry |
| Change which detector is default | `detection.py` `DEFAULT_DETECTOR` constant or `HORIZONJAM_DETECTOR` env |
| Change normalization rules | `detection.py` `normalize_and_validate()` |
| Tune chord recognition | `src/chord_detector.py` (2425 lines — caution) |
| Tune basic_pitch params | `src/midi_converter.py` |
| Change tutor prompt | `chordai_gpt_tutor.py` `_generate_rag_tutoring()` |
| Add a frontend UI panel | `nextjs-frontend/pages/index.js` (single-file React) |
| Fix mic recording behavior | `pages/index.js` `startRecording` / `stopRecording` / `finishRecording` / `teardownRecorder` |
| Change WAV encoding params | `pages/index.js` `audioBufferToWav()` + `TARGET_SR` constant |
| Re-embed RAG | `RAG/embed_enhanced_music_data.py` (note: Wikipedia drop bug lives here) |
| Train ML chord model | `chord_detection.py --collect` then `--train` (no model exists yet) |

---

**End of handoff. Resume from Section 5, Step 1.**
