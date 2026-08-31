# HorizonJam v3.0 Research Baseline

HorizonJam v3 preserves the evidence-grounded tutor, sanctioned detector
boundary, opt-in Jaccard research detector, and measured BasicPitch runtime
gate developed during the v2 modernization work. The v2 plan and the original
v1 documentation remain below as historical context; they have not been
deleted or rewritten.

The next research line is a multi-source harmonic-detection tournament. It is
research-only until external technologies pass licensing, feasibility,
benchmark, complementarity, product-suitability, and activation gates.

**An open architecture for turning a musician's recording into chord analysis, grounded instruction, and spoken feedback.**

> Project status: research prototype and local web application. HorizonJam is not yet ready for a public production deployment or an App Store release. This document tracks the work required to publish the architecture, write the paper, open-source the repository, and release the product.

## The Idea

HorizonJam is an AI-assisted music tutor. A musician records or uploads a short performance, asks a question, and receives:

1. A transcription-oriented analysis of the audio.
2. A timed chord progression and estimated musical key.
3. Guitar chord shapes and other structured musical context.
4. A retrieval-grounded tutoring response tailored to the performance.
5. Optional spoken feedback through text-to-speech.

The goal is not merely to label chords. HorizonJam connects signal processing, symbolic music analysis, retrieval-augmented generation (RAG), and a conversational interface into one inspectable pipeline. The architecture is deliberately modular so detectors, retrieval systems, language models, and speech engines can be evaluated or replaced independently.

## Why v2.0

The original HorizonJam was primarily an audio-to-MIDI and chord-analysis toolkit. Version 2.0 expands that foundation into an end-to-end tutoring system with:

- Browser microphone recording and file upload.
- A stable detector-selection and output-normalization layer.
- Multiple chord-detection strategies behind one API.
- RAG-enhanced tutoring generated from the detected musical context.
- Streaming tutor responses over WebSockets.
- Optional local or OpenAI-backed speech synthesis.
- A reproducible synthetic evaluation harness using `mir_eval`.
- A path toward a public web application and an App Store client.

The original documentation is preserved in full under [Legacy v1 Documentation](#legacy-v1-documentation).

## End-to-End Experience

```text
Musician
  |
  | records audio, uploads a file, and optionally asks a question
  v
Next.js browser client
  |
  | HTTP upload + WebSocket session
  v
FastAPI tutor relay
  |
  +--> audio validation and WAV normalization
  |
  +--> detection.run_detection()
  |      |
  |      +--> production detector
  |      +--> hybrid detector (current default)
  |      +--> rule + Viterbi detector
  |      +--> normalized chord-event contract
  |
  +--> key estimation and guitar-tab generation
  |
  +--> versioned performance evidence
  |      +--> timing, confidence, detector, warnings, key, guitar context
  |
  +--> bounded ChromaDB retrieval with source provenance
  |
  +--> intent/evidence assessment + shared tutor context
  |
  +--> GPT tutoring + deterministic pre-delivery verification
  |
  +--> local Moshi or OpenAI TTS
  v
Timed chords, key, tabs, written guidance, and spoken feedback
```

## Architecture

### 1. Browser client

`nextjs-frontend/pages/index.js` is the current user interface. It supports audio-file selection, microphone recording, WAV conversion, analysis requests, streamed results, and queued TTS playback. Browser recordings are limited to 30 seconds, with a 3-second minimum for analysis.

The frontend currently defaults to local service URLs:

- Web app: `http://localhost:3000`
- Tutor relay: `http://localhost:8001`
- TTS service: `http://localhost:5000`

Production URLs can be supplied through `NEXT_PUBLIC_TUTOR_WS_URL`, `NEXT_PUBLIC_UPLOAD_URL`, and `NEXT_PUBLIC_TTS_URL`.

### 2. Upload and WebSocket relay

`tutor_ws_relay.py` is the main application backend. It accepts an audio upload, converts supported non-WAV formats to mono 44.1 kHz WAV, starts analysis, and streams structured events back to the browser.

This service is suitable for local development only in its current form. Before public deployment it must receive authentication, rate limiting, upload limits, isolated temporary storage, job IDs, cleanup, stricter static-file handling, and production CORS configuration. See [Release Blockers](#release-blockers).

### 3. Detection contract

`detection.py` is the only sanctioned chord-detection entry point for v2.0. It selects a detector through `HORIZONJAM_DETECTOR`, executes it, and normalizes its output into:

```json
{
  "chord_events": [
    {
      "start": 0.0,
      "end": 1.5,
      "chord": "C:maj",
      "confidence": 0.82,
      "source_detector": "hybrid"
    }
  ],
  "estimated_key": null,
  "detector_used": "hybrid",
  "warnings": []
}
```

Normalization sorts events, rejects invalid values, prevents overlapping intervals, and merges adjacent identical chords. All application and evaluation callers should use `detection.run_detection()` instead of calling a detector directly.

Supported detector names:

| Detector | Purpose | Current state |
|---|---|---|
| `production` | Original audio-to-MIDI and chord pipeline | Working, but weak on the synthetic benchmark |
| `hybrid` | Rule-based, Viterbi, dataset, and optional ML integration | Default; no trained ML model is currently loaded |
| `rule_viterbi` | Rule-based recognition with temporal smoothing | Currently functionally identical to `hybrid` |

### 4. Audio and musical analysis

The main implementation lives in `src/`:

- `src/midi_converter.py`: BasicPitch-based audio-to-MIDI conversion with a fallback path.
- `src/chord_detector.py`: chord templates, timing, beat synchronization, key-aware logic, and recognition rules.
- `src/hybrid_chord_detector.py`: detector orchestration, optional ML support, Viterbi smoothing, and dataset integration.
- `src/viterbi_smoothing.py`: temporal smoothing of chord predictions.
- `src/guitar_tab_generator.py`: guitar chord shapes and tab-oriented output.
- `src/pipeline.py`: the earlier integrated production pipeline retained for compatibility.

### 5. Tutor orchestration and RAG

`chordai_gpt_tutor.py` connects detection to the educational layer. It:

1. Runs the sanctioned detection API.
2. Converts events into the backward-compatible application shape.
3. Estimates the key with `music21`.
4. Adds guitar-oriented chord information.
5. Builds a versioned `PerformanceEvidence` packet that preserves event timing, confidence, detector provenance, warnings, key, and guitar context.
6. Assesses the question and available evidence before retrieval.
7. Retrieves a bounded set of actual document text with source and record provenance from ChromaDB.
8. Assembles one explicit context shared by streaming and non-streaming generation.
9. Verifies uncertainty and retrieval-honesty rules before any text is delivered.

`tutor_evidence.py` owns the deterministic evidence contract, query routing, context assembly, response checks, and developer trace. The language model explains and prioritizes guidance; it does not own evidence serialization or verification. Set `HORIZONJAM_DEBUG_TRACE=1` during local development to include the request-local evidence trace in the WebSocket completion message. Traces can contain user questions and retrieved text and must not be enabled indiscriminately in production.

`unified_rag_system.py` and the `RAG/` directory contain the retrieval and embedding workflow. The current vector store and source documents need a licensing and provenance audit before they can be distributed publicly.

### 6. Speech synthesis

`tts_server.py` exposes the `/tts` endpoint. It attempts to use the local Moshi/Kyutai implementation and can fall back to OpenAI TTS when `TTS_ALLOW_OPENAI_FALLBACK=1`.

Speech is an optional presentation layer. Chord detection and written tutoring should remain usable when TTS is unavailable.

## Repository Map

```text
HorizonJam/
|-- detection.py                 # public detector selection and normalization API
|-- chordai_gpt_tutor.py         # analysis, retrieval, model invocation, and tutor output
|-- tutor_evidence.py            # evidence schema, assembly, verification, and trace
|-- tutor_ws_relay.py            # FastAPI upload and WebSocket application backend
|-- tts_server.py                # speech synthesis service
|-- unified_rag_system.py        # unified music-knowledge retrieval
|-- nextjs-frontend/             # browser application
|-- src/                         # transcription and chord-analysis internals
|-- eval/                        # synthetic dataset, evaluator, reports, mic test plan
|-- RAG/                         # retrieval documents, ingestion, and vector-store tools
|-- datasets/                    # local music datasets; provenance review required
|-- training_data/               # collected and generated detector training material
|-- tests/                       # focused tutor tests plus sample audio/MIDI fixtures
|-- _archive/                    # preserved earlier implementations and documentation
|-- SESSION_HANDOFF.md           # detailed development state and implementation notes
|-- .env.example                 # local configuration template without secrets
`-- README.md                    # project vision, operation, research, and release tracker
```

## Run Locally, Step by Step

### Step 1: Prerequisites

Install:

- Python 3.10 or newer.
- Node.js and npm.
- `ffmpeg` for decoding browser and compressed audio formats.
- An OpenAI API key for GPT tutoring and the optional OpenAI TTS fallback.
- Optional local Moshi model files for local speech synthesis.

The current Python dependency manifest is still being consolidated for v2.0. `requirements.txt` declares the core analysis stack, but service and model packages may need to be installed separately until the lockfile work is complete.

### Step 2: Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install fastapi uvicorn python-multipart chromadb basic-pitch
```

### Step 3: Install the web dependencies

```powershell
npm install
```

### Step 4: Configure the environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`. Do not commit `.env`. The template also documents RAG, detector, local-model, and TTS settings.

### Step 5: Start the TTS service

Open a terminal in the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn tts_server:app --host 127.0.0.1 --port 5000
```

### Step 6: Start the tutor relay

Open a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python tutor_ws_relay.py
```

The default detector is `hybrid`. To test another detector:

```powershell
$env:HORIZONJAM_DETECTOR = "production"
python tutor_ws_relay.py
```

Accepted values are `production`, `hybrid`, and `rule_viterbi`.

### Step 7: Start the web application

Open a third terminal:

```powershell
npm run dev
```

Open `http://localhost:3000`, record or select a short audio sample, enter an optional question, and run the analysis.

### Step 8: Run the evaluation tools

```powershell
# Recreate the 40 synthetic progressions, labels, MIDI files, and WAV files
python eval/synth_dataset.py

# Evaluate all detector modes and rewrite eval/report.md + eval/report.json
python eval/evaluate_chords.py

# Exercise the application pipeline without a browser
python _e2e_smoke.py

# Run the current key-estimation checks
python _evaluation.py
```

The evaluation is computationally expensive and can take significant time because every detector processes every generated song.

## Current Evaluation

The latest checked-in report evaluates 40 synthetic sine-wave chord progressions:

| Detector | Root | MajMin | Sevenths | MIREX | Files completed |
|---|---:|---:|---:|---:|---:|
| `production` | 0.319 | 0.270 | 0.211 | 0.356 | 40/40 |
| `hybrid` | 0.585 | 0.517 | 0.356 | 0.588 | 40/40 |
| `rule_viterbi` | 0.585 | 0.517 | 0.356 | 0.588 | 40/40 |

These numbers are engineering baselines, not claims of real-world accuracy. The dataset contains clean synthesized audio rather than recordings from real instruments, rooms, microphones, performers, and noise conditions. `hybrid` and `rule_viterbi` have identical results because no trained ML artifact is currently available.

Known detector issues include dominant seventh chords collapsing to major triads, inconsistent recognition across transpositions, and overlapping raw events that are repaired by the normalization layer. The complete report is in `eval/report.md`; the manual real-instrument protocol is in `eval/manual_mic_test_plan.md`.

## Research Plan

HorizonJam v2.0 should distinguish the engineering system from the research claims made about it.

### Proposed research question

> Can a modular pipeline combining automatic chord recognition, structured musical analysis, retrieval-grounded generation, and spoken interaction provide useful and inspectable feedback on short musician performances?

### Candidate contribution

The strongest current direction is a system or demonstration paper describing an explainable audio-to-tutoring architecture, rather than claiming a new state-of-the-art chord-recognition model. A stronger algorithm paper would require a genuinely new detector and substantially more experimental evidence.

### Evidence required for the paper

- Real, legally distributable labeled audio from multiple instruments and recording conditions.
- Comparisons against established chord-recognition baselines.
- Metrics separated by root, major/minor quality, seventh quality, segmentation, instrument, and noise condition.
- Ablations for normalization, Viterbi smoothing, dataset integration, key context, RAG, and TTS.
- RAG retrieval evaluation: relevance, grounding, source coverage, and failure analysis.
- Tutor evaluation: factual correctness, actionable usefulness, hallucination rate, and musical appropriateness.
- End-to-end latency and cost measurements.
- A small musician user study if the paper makes educational or usability claims.
- Versioned configurations, random seeds, dependency versions, hardware details, and reproducible scripts.
- A limitations, ethics, privacy, and data-provenance section.

### Publication sequence

1. Select the target paper type and venue.
2. Check that venue's anonymity, preprint, and prior-publication rules.
3. Freeze the research question, hypotheses, baselines, and evaluation protocol.
4. Fix the detector correctness issues before collecting final results.
5. Build and license the real-audio evaluation set.
6. Run detection, RAG, tutoring, latency, cost, and ablation experiments.
7. Write the paper and release a reproducibility package.
8. Publish the architecture article at a level allowed by the target venue.
9. Release the paper or preprint and the audited open-source repository.

## Architecture Article Outline

The open architecture article can be developed before the complete paper, but it must clearly separate measured results from future work.

1. The musician problem: turning a short performance into useful feedback.
2. Why transcription, chord recognition, RAG, and speech are separate modules.
3. The browser-to-tutor request lifecycle.
4. The detector contract and why normalization belongs at one boundary.
5. Temporal chord reasoning and the role of Viterbi smoothing.
6. Converting symbolic results into retrieval queries and tutor context.
7. Streaming written and spoken feedback.
8. Evaluation methodology and the current synthetic baseline.
9. Failure cases, privacy, cost, latency, and responsible limitations.
10. How contributors can replace one component without rewriting the system.

## v2.0 Progress Tracker

Legend: `[x]` complete, `[-]` in progress or partially complete, `[ ]` not started.

### Phase 1: Core architecture

- [x] Browser microphone recording and file upload.
- [x] FastAPI upload and WebSocket relay.
- [x] Central detector-selection API.
- [x] Normalized non-overlapping chord-event contract.
- [x] Production, hybrid, and rule/Viterbi detector modes.
- [x] Key estimation and guitar chord output.
- [x] ChromaDB retrieval and GPT tutoring integration.
- [x] Optional local/OpenAI TTS integration.
- [-] Remove duplicate and legacy execution paths from active modules.
- [-] Replace backward-compatible event duplication with a versioned API schema.

### Phase 2: Evaluation and paper

- [x] Synthetic dataset generator.
- [x] `mir_eval` scoring harness and machine-readable report.
- [x] Manual microphone test protocol.
- [ ] Complete and publish manual real-instrument test results.
- [ ] Add one or more licensed real-audio benchmark datasets.
- [ ] Add established external baselines.
- [ ] Fix overlap generation at the detector source.
- [ ] Train or remove the currently inactive ML branch.
- [ ] Add detector and architecture ablations.
- [x] Implement Evidence-Grounded Tutor v1 in the active WebSocket path.
- [x] Add a deterministic 13-case retrieval/reasoning/uncertainty evaluation set and three inspectable demos.
- [-] Expand RAG retrieval evaluation beyond the current fixed structural and adversarial cases.
- [-] Evaluate tutor correctness and grounding structurally; expert usefulness evaluation remains open.
- [ ] Measure end-to-end latency, throughput, and API cost.
- [ ] Conduct a musician user study if educational claims are made.
- [ ] Write the paper and reproducibility statement.

### Phase 3: Open-source release

- [x] `.env.example` and secret exclusions.
- [x] Preserved archive of earlier implementations.
- [-] Updated v2.0 architecture documentation.
- [ ] Choose and add an actual `LICENSE` file.
- [ ] Audit the licenses and provenance of datasets, scraped documents, tabs, models, and vector stores.
- [ ] Decide which generated data and binary artifacts belong in the public repository.
- [ ] Create complete locked Python and Node dependency manifests.
- [-] Add automated unit, integration, API, and browser tests; the tutor contract and in-process active relay path are covered, while HTTP and browser automation remain open.
- [ ] Add continuous integration for formatting, tests, and dependency checks.
- [ ] Add a one-command reproducible local environment, preferably containers.
- [ ] Create contributor, security, citation, code-of-conduct, and governance documents.
- [ ] Run secret, dependency, and source-license scans before publishing.

### Phase 4: Public web application

- [ ] Stop serving the repository root as static content.
- [ ] Replace client-visible filesystem paths with opaque upload/job IDs.
- [ ] Add MIME validation, decoded-audio validation, upload size limits, unique names, and cleanup.
- [ ] Add authentication, authorization, rate limiting, quotas, and API cost controls.
- [ ] Move CPU-heavy analysis into bounded background workers.
- [ ] Add durable job state and object storage.
- [ ] Configure production HTTPS/WSS, CORS, domains, secrets, and service URLs.
- [ ] Add health checks, structured logging, metrics, tracing, and error monitoring.
- [ ] Add privacy policy, terms, consent, retention, and deletion behavior for user audio.
- [ ] Add accessibility, responsive-layout, cross-browser, and low-bandwidth testing.
- [ ] Run a private alpha before opening a rate-limited public beta.

### Phase 5: App Store release

- [ ] Stabilize and measure the public backend first.
- [ ] Select an iOS approach: Capacitor wrapper, React Native, or native SwiftUI.
- [ ] Implement secure microphone, upload, session, and playback behavior on iOS.
- [ ] Add microphone usage descriptions and complete App Privacy disclosures.
- [ ] Provide account and data deletion if accounts are introduced.
- [ ] Implement App Store-compliant subscriptions or purchases if the product is paid.
- [ ] Add offline, interruption, background, network-loss, and device compatibility handling.
- [ ] Complete TestFlight testing, store assets, review notes, and submission.

## Release Blockers

Do not expose the current relay or TTS service directly to the public internet. The following issues are known and must be addressed first:

1. `tutor_ws_relay.py` currently mounts the repository root under `/static`; this must be replaced by a dedicated public directory so configuration and project files cannot be exposed.
2. The WebSocket accepts a client-provided server path; the server must resolve an opaque, session-bound job ID instead.
3. Uploads currently lack strict size limits, collision-resistant storage, reliable expiration, and complete cleanup.
4. The services do not yet enforce authentication, quotas, rate limits, or OpenAI spending controls.
5. CPU-bound analysis needs concurrency isolation and bounded work queues.
6. TTS currently allows broad CORS and must be private behind the application backend or an authenticated gateway.
7. Dependency declarations, production configuration, tests, CI, monitoring, and recovery procedures are incomplete.

## Data, Privacy, and Responsible Use

Audio can contain identifiable voices, background conversations, room information, and original musical performances. A production HorizonJam release should:

- Explain what audio is uploaded and why.
- Obtain clear microphone and processing consent.
- Minimize retention and delete temporary audio automatically.
- Avoid using recordings for training unless the user gives separate, explicit consent.
- Encrypt transport and protected storage.
- Document which data is sent to third-party model providers.
- Let users delete their recordings, sessions, and accounts.
- Avoid presenting generated musical feedback as guaranteed or authoritative.

HorizonJam should display detector confidence and limitations where they help users interpret the result. Low-confidence recognition should lead to uncertainty-aware tutoring rather than invented certainty.

## Definition of v2.0

HorizonJam v2.0 is complete when all of the following are true:

- The architecture and API contract are documented and versioned.
- Real-audio accuracy and end-to-end latency are measured reproducibly.
- The paper's claims are supported by baselines, ablations, and an honest limitations analysis.
- The public repository has an explicit license and contains only distributable data and artifacts.
- Automated tests and CI protect the core detector, API, and browser workflow.
- The web deployment has authentication, bounded resource usage, secure storage, deletion, monitoring, and privacy documentation.
- A public beta demonstrates stable use before an App Store submission begins.

## Current Readiness

These are planning estimates, not performance claims:

| Milestone | Approximate readiness | Main remaining work |
|---|---:|---|
| Architecture article | 65% | diagrams, polished narrative, reproducible demo, explicit limitations |
| Open-source repository | 35% | license, audit, cleanup, dependency locking, tests, CI |
| Research paper or preprint | 25% | research claim, real data, baselines, ablations, RAG/tutor evaluation |
| Private web alpha | 55% | security corrections, deployment packaging, reliability checks |
| Public web beta | 25% | auth, jobs, storage, scaling, observability, privacy, cost control |
| App Store release | 10% | stable backend, iOS client, policy work, TestFlight and review |

The next practical milestone is a **v2.0 research preview**: a secure local architecture, audited open-source package, reproducible real-audio evaluation, architecture article, and clearly scoped paper.

## Development Notes

- `AGENTS.md` is the compact entrypoint for coding agents and repository work.
- `STATUS.md` contains current verified state, blockers, benchmark evidence, and next actions.
- `docs/context/INDEX.md` routes product, architecture, runtime AI, evaluation, security, and modernization tasks to the smallest relevant context.
- `.agents/skills/` contains reusable subsystem verification workflows; canonical project knowledge remains in agent-neutral documents.
- `SESSION_HANDOFF.md` contains detailed implementation history and current technical decisions.
- `eval/report.md` and `eval/report.json` contain the latest detector results.
- `eval/manual_mic_test_plan.md` and `eval/manual_mic_results.md` track real-instrument testing.
- `_archive/` intentionally preserves earlier versions and supporting documentation.
- This directory was observed without Git metadata during the v2.0 review. Initialize or restore version control before collaborative release work, and preserve a clean history from that point onward.

---

## Legacy v1 Documentation

The original README begins below and is preserved intact for history, old commands, earlier design assumptions, and migration reference. Some paths, claims, dependency notes, and encoding are outdated; the v2.0 sections above describe the active architecture.

## TTS Environment Setup (.env)

Create a `.env` file in `HorizonJam-master` to configure TTS:

```
# Required to locate local Kyutai Moshi model files
MOSHI_MODEL_DIR=C:\\models\\kyutai

# Optional: enable OpenAI fallback when Moshi is unavailable
TTS_ALLOW_OPENAI_FALLBACK=0

# Only needed if fallback is enabled
# OPENAI_API_KEY=sk-...
```

Moshi directory must contain:
- `model.safetensors`
- `tokenizer-e351c8d8-checkpoint125.safetensors`
- `tokenizer_spm_32k_3.model`

# HorizonJam ????

**Advanced Audio-to-MIDI and Chord Analysis Toolkit**

HorizonJam is a comprehensive Python toolkit for converting audio files to MIDI and analyzing musical chord progressions. It combines state-of-the-art audio processing libraries with intelligent chord detection algorithms.

## ???? High-Accuracy Modular Pipeline

**New**: Enhanced modular pipeline with configurable parameters, automatic cleanup, and improved accuracy for guitar recordings.

## ???? Features

- **Audio-to-MIDI Conversion**: High-accuracy pitch detection using CREPE + Librosa
- **Chord Analysis**: Intelligent chord progression detection from MIDI files
- **Integrated Pipeline**: Seamless audio ??? MIDI ??? chords workflow
- **Multiple Algorithms**: Support for both CREPE (high accuracy) and Librosa (fallback)
- **Comprehensive Analysis**: Key detection, chord timing, and musical insights
- **Flexible Configuration**: Customizable parameters for different musical styles

## ???? Requirements

- Python 3.8+
- Audio files: `.wav`, `.mp3`, `.flac`, `.m4a`
- Output: MIDI files (`.mid`) and chord analysis

## ??????? Installation

### 1. Clone the Repository
```bash
git clone https://github.com/abhi119100/HorizonJam.git
cd HorizonJam
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

**Essential Dependencies:**
```bash
pip install librosa pretty_midi music21 setuptools
```

**For High Accuracy (Optional):**
```bash
pip install crepe tensorflow
```

**All Dependencies at Once:**
```bash
pip install librosa pretty_midi music21 setuptools crepe tensorflow
```

## ???? New Modular Pipeline Usage

### High-Accuracy Pipeline

The new modular pipeline provides enhanced accuracy with configurable parameters:

```bash
# Basic high-accuracy usage
python run_pipeline.py input.wav -o output/

# Advanced parameter tuning
python run_pipeline.py input.wav -o output/ \
    --min-note-len 0.03 \
    --min-freq 82.4 \
    --max-freq 1318.5 \
    --confidence 0.5 \
    --chord-window 0.08 \
    --onset-threshold 0.4
```

### Pipeline Features
- **Automatic Cleanup**: No temporary files left behind
- **Configurable Parameters**: Fine-tune every aspect of detection
- **Enhanced Accuracy**: Optimized for guitar recordings
- **JSON Export**: Structured output with metadata
- **Chord Progression**: Simple progression string output

## ???? Legacy Usage (Still Available)

### 1. Audio-to-MIDI Conversion

**Basic Conversion:**
```bash
python universal_audio_to_midi.py "your_audio.wav"
```
*Output: `your_audio_transcribed.mid`*

**With Custom Settings:**
```bash
python universal_audio_to_midi.py "audio.wav" --confidence 0.5 --min-duration 0.2
```

**With Custom Output:**
```bash
python universal_audio_to_midi.py "audio.wav" -o "my_song.mid"
```

#### Parameters:
- `--confidence`: Pitch detection confidence threshold (0.1-0.9, default: 0.3)
- `--min-duration`: Minimum note duration in seconds (default: 0.1)
- `--max-duration`: Maximum note duration in seconds (default: 4.0)

### 2. MIDI-to-Chords Analysis

**Basic Chord Analysis:**
```bash
python midi_to_chords.py "your_file.mid"
```

**With Custom Window Size:**
```bash
python midi_to_chords.py "your_file.mid" 1.5
```

**Auto-Detect Window Size:**
```bash
python midi_to_chords.py "your_file.mid" auto
```

#### Output Example:
```
???? CHORD PROGRESSION SUMMARY
==================================================
[00:00 - 00:02] ??? G
[00:02 - 00:04] ??? C  
[00:04 - 00:06] ??? D
[00:06 - 00:08] ??? G

???? Detected Key: G major
???? Found 4 distinct chord events
```

### 3. Complete Audio-to-Chords Pipeline

**Full Pipeline Analysis:**
```bash
python audio_to_chords_pipeline.py "your_audio.wav"
```

**With Custom Settings:**
```bash
python audio_to_chords_pipeline.py "audio.wav" --confidence 0.4 --window-size 1.5
```

**Keep Intermediate MIDI Files:**
```bash
python audio_to_chords_pipeline.py "audio.wav" --keep-midi
```

#### Pipeline Features:
- Automatic audio ??? MIDI ??? chords conversion
- Intelligent window size detection
- Key signature analysis
- Chord event detection
- Performance timing analysis

## ???? Core Files

### New Modular Pipeline
- **`run_pipeline.py`** - Main high-accuracy pipeline CLI
- **`src/pipeline.py`** - AccurateAudioToChordsPipeline class
- **`src/midi_converter.py`** - Enhanced MIDI conversion with parameters
- **`src/chord_detector.py`** - Configurable chord detection
- **`test_accuracy.py`** - Accuracy testing and comparison

### Legacy Scripts (Still Available)
- **`universal_audio_to_midi.py`** - Audio-to-MIDI converter
- **`midi_to_chords.py`** - MIDI chord analysis
- **`audio_to_chords_pipeline.py`** - Complete pipeline
- **`analyze_basicpitch_results.py`** - MIDI analysis tools

### Utilities
- **`example_pipeline_usage.py`** - Usage examples
- **`run_transcription_benchmark.py`** - Performance benchmarking

### Documentation
- **`algorithm_accuracy_analysis.md`** - Technical analysis
- **`tests/`** - Test audio and MIDI files

## ??????? Advanced Configuration

### Audio-to-MIDI Settings

```python
from universal_audio_to_midi import AudioToMIDI

converter = AudioToMIDI(
    sample_rate=22050,
    confidence_threshold=0.3,
    min_note_duration=0.1,
    max_note_duration=4.0
)

midi_path = converter.convert("audio.wav", "output.mid")
```

### Chord Analysis Settings

```python
from midi_to_chords import analyze_midi_chords

# Auto-detect window size
chord_progression, chord_events = analyze_midi_chords("file.mid")

# Manual window size
chord_progression, chord_events = analyze_midi_chords("file.mid", window_size=1.5)
```

## ???? High-Accuracy Parameter Guide

### BasicPitch Parameters
- `--min-note-len`: Minimum note duration (0.02-0.1s, default: 0.05)
- `--min-freq`: Minimum frequency (Hz, default: 82.4 - E2)
- `--max-freq`: Maximum frequency (Hz, default: 1318.5 - E6)
- `--confidence`: Note confidence threshold (0.1-0.9, default: 0.3)
- `--onset-threshold`: Onset detection sensitivity (default: 0.5)
- `--frame-threshold`: Frame-level threshold (default: 0.3)

### Chord Detection Parameters
- `--chord-window`: Analysis window size (0.05-0.2s, default: 0.1)
- `--chord-confidence`: Chord confidence filter (0.1-0.9, default: 0.0)
- `--min-chord-duration`: Minimum chord duration (default: 0.1s)

### Preset Configurations
```bash
# Clean recordings
python run_pipeline.py audio.wav --min-note-len 0.02 --confidence 0.6

# Noisy recordings  
python run_pipeline.py audio.wav --min-note-len 0.08 --confidence 0.4

# Complex chords
python run_pipeline.py audio.wav --chord-window 0.08 --chord-confidence 0.3
```

## ???? Testing & Validation

### Run Accuracy Tests
```bash
python test_accuracy.py
```

### Compare Different Modes
```bash
# Test multiple configurations
python test_accuracy.py --compare-modes
```

## ???? Troubleshooting

### Common Issues

**1. "No module named 'librosa'"**
```bash
pip install librosa
```

**2. "CREPE not available"**
```bash
pip install crepe tensorflow
```
*Note: CREPE is optional but provides higher accuracy*

**3. "pkg_resources deprecated warning"**
```bash
pip install setuptools
```

**4. No chords detected**
- Try adjusting `--confidence` (lower values detect more notes)
- Use `--window-size` for manual chord segmentation
- Check that audio contains harmonic content (not just percussion)

### Performance Tips

- **For faster processing**: Skip CREPE installation (uses Librosa only)
- **For higher accuracy**: Install CREPE + TensorFlow
- **For guitar/piano**: Use confidence 0.3-0.5
- **For vocals**: Use confidence 0.4-0.7

## ???? Example Workflow

```bash
# 1. Convert audio to MIDI
python universal_audio_to_midi.py "song.wav"

# 2. Analyze chords from MIDI
python midi_to_chords.py "song_transcribed.mid"

# 3. Or do both in one step
python audio_to_chords_pipeline.py "song.wav"
```

## ???? Supported Musical Content

### Works Best With:
- Piano recordings
- Guitar (acoustic/electric)
- Vocal melodies
- Instrumental solos
- Clear harmonic content

### Limitations:
- Complex polyphonic music (multiple simultaneous melodies)
- Heavy percussion/drums
- Very noisy recordings
- Extremely fast passages

## ???? Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ???? License

This project is open source. Feel free to use, modify, and distribute.

## ???? Acknowledgments

- **Librosa** - Audio analysis library
- **pretty_midi** - MIDI file handling
- **CREPE** - High-accuracy pitch detection
- **music21** - Music analysis toolkit

## ???? Support

- ???? **Issues**: [GitHub Issues](https://github.com/abhi119100/HorizonJam/issues)
- ???? **Documentation**: See this README and code comments
- ???? **Feature Requests**: Open an issue with enhancement label

---

**Made with ?????? for musicians and developers**

