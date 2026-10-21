# Multi-Evidence Phases 2-6 Consolidated Gate

Overall result: **STOPPED_AFTER_PHASE_5**.

| Phase | Status | Decision | Evidence |
| --- | --- | --- | --- |
| Phase 2 | PASS | B DIRECT_BETTER | [eval/basicpitch_direct_evidence_report.json](basicpitch_direct_evidence_report.json) |
| Phase 3 | PASS | A DSP_COMPLEMENTARY | [eval/dsp_chroma_report.json](dsp_chroma_report.json) |
| Phase 4 | PASS | C DIRECT_MODEL_REDUNDANT | [eval/direct_chord_model_report.json](direct_chord_model_report.json) |
| Phase 5 | STOP_GATE | D FUSION_NO_GAIN | [eval/fusion_v1_report.json](fusion_v1_report.json) |
| Phase 6 | NOT_RUN | not available | Phase 5 D FUSION_NO_GAIN prohibits the temporal activation path |

## Paired controlled comparison

| Source | Exact cases |
| --- | ---: |
| rule_jaccard | 7/8 |
| Librosa DSP | 7/8 |
| LV-Chordia | 0/8 |
| fusion v1 | 7/8 |
| multi_evidence | not implemented |

These are deterministic synthetic diagnostics, not real-performance accuracy. Fusion offered no gain over either strongest individual source, so the hard gate stopped Phase 6. Default product behavior remains unchanged.
