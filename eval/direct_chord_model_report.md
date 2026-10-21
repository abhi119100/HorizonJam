# Direct Chord Model Gate

Decision: **C DIRECT_MODEL_REDUNDANT**.

LV-Chordia execution is RESEARCH_ONLY. Checkpoint-specific rights remain unresolved independently of the package MIT declaration.

## Controlled cases

| Case | Expected | LV-Chordia | Jaccard | DSP | Category | Wall |
| --- | --- | --- | --- | --- | --- | ---: |
| c_major | C | N | C | C | two_correct_lv_chordia_differs | 11.78s |
| a_minor | Am | N | Am | Am | two_correct_lv_chordia_differs | 10.52s |
| g_dominant7 | G7 | G | G7 | G7 | two_correct_lv_chordia_differs | 10.58s |
| c_major7 | Cmaj7 | N | Cmaj7 | Cmaj7 | two_correct_lv_chordia_differs | 10.77s |
| d_minor7 | Dm7 | N | Dm7 | Dm7 | two_correct_lv_chordia_differs | 10.68s |
| d_sus2 | Dsus2 | N | Dsus2 | Asus4 | one_prior_correct | 10.96s |
| a_sus4 | Asus4 | N | Asus4 | Asus4 | two_correct_lv_chordia_differs | 11.23s |
| b_diminished | Bdim | N | Bm | Bdim | one_prior_correct | 11.42s |

## Runtime scaling

| Audio | Events | Prediction | Adapter wall | Error |
| ---: | ---: | --- | ---: | --- |
| 3s | 1 | N | 11.55s |  |
| 10s | 1 | N | 11.34s |  |
| 30s | 1 | N | 12.41s |  |

The external model is never imported by HorizonJam's active environment. URL input is rejected, network helpers are disabled in the runner, and no model score is mapped to HorizonJam confidence.
