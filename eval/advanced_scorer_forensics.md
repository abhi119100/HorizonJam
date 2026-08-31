# Advanced Chord Scorer Forensics v1

Fresh deterministic evidence from `python eval/analyze_advanced_scorer.py`.

## Scoring equation

`score = pitch_match + bass_bonus + key_prior + suspension_adjustment + complexity_penalty`

- **pitch_match**: |input pitch classes intersect template| / |template pitch classes|; range 0..1; larger is better
- **bass_bonus**: +0.25 when bass is template root, +0.10 when another template tone, otherwise 0
- **key_prior**: lookup by (candidate root, quality); sparse E-major/A-major table; larger is better
- **suspension_adjustment**: +0.10 for proper sus2/sus4, +0.15 for Bsus4_priority, otherwise -0.20
- **complexity_penalty**: -0.10 for 7/min7/maj7 candidates only when input has at most three pitch classes
- **missing_tone_penalty**: does not exist independently
- **extra_tone_penalty**: does not exist

Tie break: Python stable descending score sort preserves template insertion order; major templates precede seventh templates for each root
Maximum decomposition reconciliation error: `2.220446049250313e-16`.

## Required forensic traces

### D7

Input: `D4 F#4 A4 C5`; bass `D4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |
| 2 | D:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | D:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [6] |
| 4 | D:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |
| 5 | D:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [0, 6] |

Winner margin over runner-up: `0.000`. True-template rank/score: `2` / `1.250`.

### G7

Input: `G4 B4 D5 F5`; bass `G4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | G:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 2 | G:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | G:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |
| 4 | G:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 5 | G:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [5, 11] |

Winner margin over runner-up: `0.000`. True-template rank/score: `2` / `1.250`.

### Cmaj7

Input: `C4 E4 G4 B4`; bass `C4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |
| 2 | C:maj7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | C:7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |
| 4 | E:min | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | [0] |
| 5 | C:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [4, 11] |

Winner margin over runner-up: `0.000`. True-template rank/score: `2` / `1.250`.

### Am7

Input: `A4 C5 E5 G5`; bass `A4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A:min | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [7] |
| 2 | A:min7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | A:maj | 1.067 | 0.667 | 0.250 | 0.150 | 0.000 | 0.000 | [0, 7] |
| 4 | C:maj | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | [9] |
| 5 | A:7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |

Winner margin over runner-up: `0.000`. True-template rank/score: `2` / `1.250`.

### C

Input: `C4 E4 G4`; bass `C4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 2 | C:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [4] |
| 3 | C:7 | 0.900 | 0.750 | 0.250 | 0.000 | 0.000 | -0.100 | [] |
| 4 | C:maj7 | 0.900 | 0.750 | 0.250 | 0.000 | 0.000 | -0.100 | [] |
| 5 | F:sus2 | 0.867 | 0.667 | 0.100 | 0.000 | 0.100 | 0.000 | [4] |

Winner margin over runner-up: `0.333`. True-template rank/score: `1` / `1.250`.

### Am

Input: `A4 C5 E5`; bass `A4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A:min | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 2 | A:maj | 1.067 | 0.667 | 0.250 | 0.150 | 0.000 | 0.000 | [0] |
| 3 | A:min7 | 0.900 | 0.750 | 0.250 | 0.000 | 0.000 | -0.100 | [] |
| 4 | D:sus2 | 0.867 | 0.667 | 0.100 | 0.000 | 0.100 | 0.000 | [0] |
| 5 | E:sus4 | 0.867 | 0.667 | 0.100 | 0.000 | 0.100 | 0.000 | [0] |

Winner margin over runner-up: `0.183`. True-template rank/score: `1` / `1.250`.

### Csus4

Input: `C4 F4 G4`; bass `C4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C:sus4 | 1.350 | 1.000 | 0.250 | 0.000 | 0.100 | 0.000 | [] |
| 2 | F:sus2 | 1.200 | 1.000 | 0.100 | 0.000 | 0.100 | 0.000 | [] |
| 3 | C:maj | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 4 | C:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 5 | G:sus4 | 0.867 | 0.667 | 0.100 | 0.000 | 0.100 | 0.000 | [5] |

Winner margin over runner-up: `0.150`. True-template rank/score: `1` / `1.350`.

### Cdim

Input: `C4 D#4 F#4`; bass `C4`; key `E major`.

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [6] |
| 2 | B:maj | 0.847 | 0.667 | 0.000 | 0.180 | 0.000 | 0.000 | [0] |
| 3 | G#:maj | 0.767 | 0.667 | 0.100 | 0.000 | 0.000 | 0.000 | [6] |
| 4 | G#:7 | 0.750 | 0.750 | 0.100 | 0.000 | 0.000 | -0.100 | [] |
| 5 | D#:min | 0.667 | 0.667 | 0.000 | 0.000 | 0.000 | 0.000 | [0] |

Winner margin over runner-up: `0.070`. True-template rank/score: `absent` / `n/a`.

## All dominant sevenths

### C7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [10] |
| 2 | C:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | C:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [4] |
| 4 | C:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [10] |
| 5 | C:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [4, 10] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### C#7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C#:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |
| 2 | C#:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | C#:min | 1.037 | 0.667 | 0.250 | 0.120 | 0.000 | 0.000 | [5, 11] |
| 4 | C#:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 5 | C#:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### D7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |
| 2 | D:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | D:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [6] |
| 4 | D:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |
| 5 | D:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [0, 6] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### D#7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | D#:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [1] |
| 2 | D#:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | D#:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [7] |
| 4 | D#:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [1] |
| 5 | D#:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [1, 7] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### E7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | E:maj | 1.450 | 1.000 | 0.250 | 0.200 | 0.000 | 0.000 | [2] |
| 2 | E:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | E:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [8] |
| 4 | E:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [2] |
| 5 | E:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [2, 8] |

Major triad `1.450` vs seventh `1.250`; triad minus seventh `0.200`.

### F7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [3] |
| 2 | F:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | F:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [9] |
| 4 | F:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [3] |
| 5 | F:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [3, 9] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### F#7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F#:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [4] |
| 2 | F#:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | F#:min | 1.037 | 0.667 | 0.250 | 0.120 | 0.000 | 0.000 | [4, 10] |
| 4 | B:sus4_priority | 1.017 | 0.667 | 0.100 | 0.100 | 0.150 | 0.000 | [1, 10] |
| 5 | F#:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [10] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### G7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | G:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 2 | G:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | G:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [11] |
| 4 | G:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [5] |
| 5 | G:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [5, 11] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### G#7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | G#:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [6] |
| 2 | G#:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | G#:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [0] |
| 4 | G#:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [6] |
| 5 | G#:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [0, 6] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### A7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A:maj | 1.400 | 1.000 | 0.250 | 0.150 | 0.000 | 0.000 | [7] |
| 2 | A:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | A:maj7 | 1.050 | 0.750 | 0.250 | 0.050 | 0.000 | 0.000 | [7] |
| 4 | A:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [1] |
| 5 | A:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [1, 7] |

Major triad `1.400` vs seventh `1.250`; triad minus seventh `0.150`.

### A#7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A#:maj | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [8] |
| 2 | A#:7 | 1.250 | 1.000 | 0.250 | 0.000 | 0.000 | 0.000 | [] |
| 3 | A#:min7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [2] |
| 4 | A#:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [8] |
| 5 | A#:min | 0.917 | 0.667 | 0.250 | 0.000 | 0.000 | 0.000 | [2, 8] |

Major triad `1.250` vs seventh `1.250`; triad minus seventh `0.000`.

### B7

| Rank | Candidate | Score | Match | Bass | Key | Sus | Complexity | Unexplained PCs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B:maj | 1.430 | 1.000 | 0.250 | 0.180 | 0.000 | 0.000 | [9] |
| 2 | B:7 | 1.350 | 1.000 | 0.250 | 0.100 | 0.000 | 0.000 | [] |
| 3 | B:min | 1.067 | 0.667 | 0.250 | 0.150 | 0.000 | 0.000 | [3, 9] |
| 4 | B:maj7 | 1.000 | 0.750 | 0.250 | 0.000 | 0.000 | 0.000 | [9] |
| 5 | E:sus2 | 0.917 | 0.667 | 0.100 | 0.050 | 0.100 | 0.000 | [3, 9] |

Major triad `1.430` vs seventh `1.350`; triad minus seventh `0.080`.

## Key-prior sensitivity

| Mode | Context coverage | Root | Exact | Exact delta | Seventh exact | Winner changes | True-rank changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default_e_major | 100.0% | 97.9% | 50.0% | 0.000 | 0.0% | 0 | 0 |
| no_key_context | 0.0% | 100.0% | 50.0% | 0.000 | 0.0% | 2 | 1 |
| matching_supported_context | 13.5% | 100.0% | 50.0% | 0.000 | 0.0% | 2 | 1 |

## Term ablations

| Ablation | Root | Exact | Exact delta | Seventh exact | Winner changes | Dominant-7 winner changes |
| --- | --- | --- | --- | --- | --- | --- |
| without_pitch_match | 87.5% | 26.0% | -0.240 | 0.0% | 49 | 4 |
| without_bass_bonus | 67.7% | 37.5% | -0.125 | 0.0% | 29 | 0 |
| without_key_prior | 100.0% | 50.0% | 0.000 | 0.0% | 2 | 0 |
| without_suspension_adjustment | 97.9% | 50.0% | 0.000 | 0.0% | 1 | 0 |
| without_complexity_penalty | 97.9% | 50.0% | 0.000 | 0.0% | 1 | 0 |

Missing-tone and extra-tone ablations are not run because those penalty terms do not exist.

## Candidate margins

| Quality | Template coverage | Winner tie rate | Mean winner-runner | Mean winner-true | Mean true rank |
| --- | --- | --- | --- | --- | --- |
| 7 | 100.0% | 75.0% | 0.036 | 0.036 | 2.000 |
| dim | 0.0% | 0.0% | 0.131 | n/a | n/a |
| maj | 100.0% | 0.0% | 0.334 | 0.000 | 1.000 |
| maj7 | 100.0% | 75.0% | 0.040 | 0.040 | 2.000 |
| min | 100.0% | 0.0% | 0.315 | 0.000 | 1.000 |
| min7 | 100.0% | 75.0% | 0.045 | 0.045 | 2.083 |
| sus2 | 100.0% | 0.0% | 0.150 | 0.000 | 1.000 |
| sus4 | 100.0% | 0.0% | 0.132 | 0.003 | 1.083 |

## Bass and inversion findings

Across `20` non-root-position representative voicings: `10` winners changed, `8` had a wrong root, `5` kept the root but changed quality, and `2` recovered an exact label that root position missed.

| True | Inversion | Bass | Winner | True rank | Winner-true |
| --- | --- | --- | --- | --- | --- |
| D7 | 0 | D4 | D:maj | 2 | 0.000 |
| D7 | 1 | F#4 | D:maj | 2 | 0.000 |
| D7 | 2 | A4 | D:maj | 2 | 0.000 |
| D7 | 3 | C5 | D:7 | 1 | 0.000 |
| G7 | 0 | G4 | G:maj | 2 | 0.000 |
| G7 | 1 | B4 | G:maj | 2 | 0.000 |
| G7 | 2 | D5 | G:maj | 2 | 0.000 |
| G7 | 3 | F5 | G:7 | 1 | 0.000 |
| Cmaj7 | 0 | C4 | C:maj | 2 | 0.000 |
| Cmaj7 | 1 | E4 | E:min | 4 | 0.150 |
| Cmaj7 | 2 | G4 | C:maj | 2 | 0.000 |
| Cmaj7 | 3 | B4 | B:sus4_priority | 3 | 0.067 |
| Am7 | 0 | A4 | A:min | 2 | 0.000 |
| Am7 | 1 | C5 | C:maj | 3 | 0.150 |
| Am7 | 2 | E5 | C:maj | 3 | 0.000 |
| Am7 | 3 | G5 | C:maj | 2 | 0.000 |
| C | 0 | C4 | C:maj | 1 | 0.000 |
| C | 1 | E4 | C:maj | 1 | 0.000 |
| C | 2 | G4 | C:maj | 1 | 0.000 |
| Am | 0 | A4 | A:min | 1 | 0.000 |
| Am | 1 | C5 | A:min | 1 | 0.000 |
| Am | 2 | E5 | A:min | 1 | 0.000 |
| Csus4 | 0 | C4 | C:sus4 | 1 | 0.000 |
| Csus4 | 1 | F4 | F:sus2 | 2 | 0.150 |
| Csus4 | 2 | G4 | C:sus4 | 1 | 0.000 |
| Cdim | 0 | C4 | C:min | absent | n/a |
| Cdim | 1 | D#4 | B:maj | absent | n/a |
| Cdim | 2 | F#4 | B:maj | absent | n/a |

## Diminished findings

| True | Winner | Score | Runner-up | Margin |
| --- | --- | --- | --- | --- |
| Cdim | C:min | 0.917 | B:maj | 0.070 |
| C#dim | C#:min | 1.037 | A:maj | 0.120 |
| Ddim | D:min | 0.917 | A#:maj | 0.150 |
| D#dim | B:maj | 0.947 | D#:min | 0.030 |
| Edim | E:min | 0.917 | E:maj | 0.133 |
| Fdim | F:min | 0.917 | E:maj | 0.050 |
| F#dim | F#:min | 1.037 | D:maj | 0.270 |
| Gdim | G:min | 0.917 | D#:maj | 0.150 |
| G#dim | E:maj | 0.967 | G#:min | 0.050 |
| Adim | A:min | 0.917 | F:maj | 0.150 |
| A#dim | A#:min | 0.917 | A:maj | 0.100 |
| Bdim | B:min | 1.067 | G:maj | 0.300 |

No diminished candidate template exists, so diminished failure is separate from seventh subset ties.

## Template findings

There are `85` candidates. Quality counts: `{"7": 12, "dim": 0, "maj": 12, "maj7": 12, "min": 12, "min7": 12, "sus2": 12, "sus4": 12, "sus4_priority": 1}`.
Required/optional tones distinguished: `False`. All template tones are equally weighted through set intersection.

## Root cause

Asymmetric template coverage gives a complete triad subset and its seventh extension the same pitch-match score. With no extra-tone penalty, stable template insertion order selects the earlier triad on ties; sparse E-major priors make the triad strictly higher for E7, A7, and B7.

## Decision gate

**C. TEMPLATE_MODEL_PROBLEM**: The asymmetric match formulation systematically allows strict triad subsets to tie complete seventh templates, while diminished candidates are absent entirely.

## Limitations

- Candidate scores and margins are diagnostics, not calibrated confidence.
- Only existing score terms are ablated; no replacement score or production repair is evaluated.
- Matching context is limited to positive priors available in the scorer's E-major and A-major tables.
- No audio, transcription, segmentation, temporal decoding, retrieval, or tutor logic is exercised.
