# Evidence Fusion v1 Gate

Decision: **D FUSION_NO_GAIN**.

Paired synthetic replay only. Expected labels were used only after ranking for scoring.

## Controlled cases

| Case | Expected | Jaccard | DSP | Fusion | Agreement |
| --- | --- | --- | --- | --- | --- |
| c_major | C | C | C | C | agreement_high |
| a_minor | Am | Am | Am | Am | agreement_high |
| g_dominant7 | G7 | G7 | G7 | G7 | agreement_high |
| c_major7 | Cmaj7 | Cmaj7 | Cmaj7 | Cmaj7 | agreement_high |
| d_minor7 | Dm7 | Dm7 | Dm7 | Dm7 | agreement_high |
| d_sus2 | Dsus2 | Dsus2 | Asus4 | Dsus2 | agreement_mixed |
| a_sus4 | Asus4 | Asus4 | Asus4 | Asus4 | agreement_high |
| b_diminished | Bdim | Bm | Bdim | Bm | agreement_mixed |

## Result

Jaccard: 7/8; DSP: 7/8; fusion: 7/8.

Fusion uses equal active weights for Jaccard and Librosa chroma. LV-Chordia has weight 0.0 because its Phase 4 gate found no unique correct case. Scores are internal weighted normalized support, not probabilities or calibrated confidence.

The fusion activation path stops when this report records no gain; Phase 6 must not be built on this candidate stream.
