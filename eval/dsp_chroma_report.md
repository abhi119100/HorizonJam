# DSP / Chroma Evidence Gate

Decision: **A DSP_COMPLEMENTARY**.

Synthetic diagnostic and runtime evidence only. No real-performance accuracy claim is made.

## Controlled chord cases

| Case | Expected | DSP | Jaccard | Outcome |
| --- | --- | --- | --- | --- |
| c_major | C | C | C | both_correct |
| a_minor | Am | Am | Am | both_correct |
| g_dominant7 | G7 | G7 | G7 | both_correct |
| c_major7 | Cmaj7 | Cmaj7 | Cmaj7 | both_correct |
| d_minor7 | Dm7 | Dm7 | Dm7 | both_correct |
| d_sus2 | Dsus2 | Asus4 | Dsus2 | rule_jaccard_only_correct |
| a_sus4 | Asus4 | Asus4 | Asus4 | both_correct |
| b_diminished | Bdim | Bdim | Bm | dsp_only_correct |

## Runtime scaling

| Audio | Load | Tuning | CQT/chroma | Scoring | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3s | 0.0015s | 0.0216s | 0.2237s | 0.0204s | 0.2493s |
| 10s | 0.0036s | 0.0712s | 0.3041s | 0.0813s | 0.3855s |
| 30s | 0.0136s | 0.2233s | 0.4987s | 0.2226s | 0.7569s |

Raw `PitchClassEvidence` remains separate from the research-only profile interpretation. Scores are normalized cosine support, not probability or calibrated confidence. The default detector is unchanged.
