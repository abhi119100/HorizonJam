# Jaccard Post-Transcription Detector-Path Benchmark v1

This is L2 post-transcription evidence. It is not an audio or real-musician accuracy result.

| Detector | Root | MajMin | Sevenths | MIREX | Files | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hybrid | 47.2% | 38.9% | 27.5% | 52.0% | 40/40 | 29 |
| rule_jaccard | 52.9% | 52.9% | 40.0% | 55.9% | 40/40 | 27 |

## Decision gate

**A. ADVANCE_TO_REAL_AUDIO**. Jaccard improves seventh scoring without a material post-transcription regression.

Metric deltas: `{"majmin": 0.1399999999999999, "mirex": 0.03875000000000017, "root": 0.05666666666666664, "sevenths": 0.12541666666666657}`

Default activation remains prohibited until real-audio evidence exists.

## Limitations

- BasicPitch is bypassed, so this does not measure L0/L1 or audio-recognition accuracy.
- Synthetic MIDI and sine fixtures do not represent real musicians.
- Diminished templates remain absent; confidence remains uncalibrated.
- A successful gate advances the candidate to real-audio validation only.
