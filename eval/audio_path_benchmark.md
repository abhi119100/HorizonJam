# Single-WAV Analysis Performance Gate v1

Runtime evidence only. No detector-accuracy claim is made.

## Cold and warm

| Measurement | Seconds |
| --- | ---: |
| Process A first 3s WAV | 13.033 |
| Process A repeated 3s WAV | 1.307 |
| Process B first 3s WAV | 10.479 |

## First-run stages

| Stage | Seconds |
| --- | ---: |
| audio_decode_resample | 1.883213 |
| audio_loader_import | 2.249081 |
| audio_window_construction | 0.005611 |
| basic_pitch_import | 1.066263 |
| basic_pitch_predict_total | 3.881855 |
| midi_serialization | 0.190030 |
| model_inference | 1.756080 |
| model_initialization | 0.785501 |
| note_event_extraction_and_midi_generation | 0.204215 |
| trace_hashing | 0.166582 |
| transcription_total | 8.345035 |
| candidate_scoring | 0.001588 |
| file_validation | 0.019473 |
| harmony_postprocessing | 0.231615 |
| harmony_total | 0.273447 |
| hybrid_detector_import | 3.990005 |
| hybrid_detector_initialization | 0.270994 |
| midi_parsing | 0.019296 |
| normalization | 0.000054 |
| post_transcription_detector | 0.278194 |
| total | 13.028600 |
| window_construction | 0.000125 |

## Duration scaling

| Duration | Warm seconds | Model windows |
| ---: | ---: | ---: |
| 3.0 | 2.137 | 2 |
| 10.0 | 5.575 | 7 |
| 30.0 | 10.440 | 19 |

## Equivalence

`{"model_outputs_equal": true, "normalized_chord_events_equal": true, "note_events_equal": true}`

## Decision

**F. MIXED**

- G. ENVIRONMENT_SPECIFIC: Numba cache validation under user site-packages was pathological
- C. PREPROCESSING_OVERHEAD: audioread backend discovery added about 15 seconds before SoundFile WAV decoding
- A. COLD_START_ONLY: imports and detector initialization are paid once and warm calls reuse model state

The default detector remains unchanged. `rule_jaccard` remains opt-in.
