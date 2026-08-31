# Chord Match Formulation Benchmark v1

Fresh deterministic evidence from `python eval/compare_match_formulations.py`.

## Formulations

- `baseline_template_coverage`: overlap / template size.
- `bidirectional_f1`: harmonic mean of template recall and input precision.
- `jaccard`: overlap / union.
- `unexplained_penalty_0.10/0.20/0.30`: template recall minus lambda times unexplained-input ratio.
- `specificity_tie_rule`: baseline score with strict observed supersets preferred only inside equal-score groups.

Penalty rationale: 0.10, 0.20, and 0.30 span 10-30% of the unit match scale and bracket the scorer's 0.10-0.25 contextual adjustments without an exhaustive sweep.

## Complete oracle results

| Formulation | Root | Quality | Exact | Supported exact | Maj/min | Seventh |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_template_coverage | 97.9% | 50.0% | 50.0% | 57.1% | 100.0% | 0.0% |
| bidirectional_f1 | 97.9% | 82.3% | 82.3% | 94.0% | 100.0% | 86.1% |
| jaccard | 92.7% | 86.5% | 86.5% | 98.8% | 100.0% | 97.2% |
| unexplained_penalty_0.10 | 97.9% | 78.1% | 78.1% | 89.3% | 100.0% | 75.0% |
| unexplained_penalty_0.20 | 97.9% | 78.1% | 78.1% | 89.3% | 100.0% | 75.0% |
| unexplained_penalty_0.30 | 97.9% | 78.1% | 78.1% | 89.3% | 100.0% | 75.0% |
| specificity_tie_rule | 97.9% | 78.1% | 78.1% | 89.3% | 100.0% | 75.0% |

## Per-quality complete exact

| Formulation | maj | min | 7 | maj7 | min7 | sus2 | sus4 | dim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_template_coverage | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 0.0% |
| bidirectional_f1 | 100.0% | 100.0% | 83.3% | 83.3% | 91.7% | 100.0% | 100.0% | 0.0% |
| jaccard | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 100.0% | 100.0% | 0.0% |
| unexplained_penalty_0.10 | 100.0% | 100.0% | 75.0% | 75.0% | 75.0% | 100.0% | 100.0% | 0.0% |
| unexplained_penalty_0.20 | 100.0% | 100.0% | 75.0% | 75.0% | 75.0% | 100.0% | 100.0% | 0.0% |
| unexplained_penalty_0.30 | 100.0% | 100.0% | 75.0% | 75.0% | 75.0% | 100.0% | 100.0% | 0.0% |
| specificity_tie_rule | 100.0% | 100.0% | 75.0% | 75.0% | 75.0% | 100.0% | 100.0% | 0.0% |

## Per-root complete exact

| Formulation | C | C# | D | D# | E | F | F# | G | G# | A | A# | B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_template_coverage | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% |
| bidirectional_f1 | 87.5% | 87.5% | 87.5% | 87.5% | 62.5% | 87.5% | 87.5% | 87.5% | 87.5% | 75.0% | 87.5% | 62.5% |
| jaccard | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 87.5% | 75.0% |
| unexplained_penalty_0.10 | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 50.0% |
| unexplained_penalty_0.20 | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 50.0% |
| unexplained_penalty_0.30 | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 50.0% |
| specificity_tie_rule | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 75.0% | 87.5% | 87.5% | 62.5% | 87.5% | 50.0% |

## Robustness tradeoff matrix

| Formulation | complete | omitted_fifth | omitted_root | seventh_without_fifth | duplicated_tones | inversions | extra_tone |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_template_coverage | 57.1% | 54.8% | 2.4% | 0.0% | 57.1% | 38.7% | 58.3% |
| bidirectional_f1 | 94.0% | 86.9% | 3.6% | 75.0% | 94.0% | 62.3% | 91.7% |
| jaccard | 98.8% | 91.7% | 9.5% | 86.1% | 98.8% | 78.9% | 91.7% |
| unexplained_penalty_0.10 | 89.3% | 83.3% | 2.4% | 66.7% | 89.3% | 56.9% | 91.7% |
| unexplained_penalty_0.20 | 89.3% | 84.5% | 2.4% | 69.4% | 89.3% | 58.3% | 91.7% |
| unexplained_penalty_0.30 | 89.3% | 86.9% | 3.6% | 75.0% | 89.3% | 58.8% | 91.7% |
| specificity_tie_rule | 89.3% | 54.8% | 2.4% | 0.0% | 89.3% | 56.9% | 91.7% |

## Extra-tone retention

| Formulation | Root retained | Quality retained | Exact retained |
| --- | --- | --- | --- |
| baseline_template_coverage | 100.0% | 58.3% | 58.3% |
| bidirectional_f1 | 100.0% | 91.7% | 91.7% |
| jaccard | 100.0% | 91.7% | 91.7% |
| unexplained_penalty_0.10 | 100.0% | 91.7% | 91.7% |
| unexplained_penalty_0.20 | 100.0% | 91.7% | 91.7% |
| unexplained_penalty_0.30 | 100.0% | 91.7% | 91.7% |
| specificity_tie_rule | 100.0% | 91.7% | 91.7% |

## Seventh predictions

| True | baseline_template_coverage | bidirectional_f1 | jaccard | unexplained_penalty_0.10 | unexplained_penalty_0.20 | unexplained_penalty_0.30 | specificity_tie_rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C7 | C:maj | C:7 | C:7 | C:7 | C:7 | C:7 | C:7 |
| C#7 | C#:maj | C#:7 | C#:7 | C#:7 | C#:7 | C#:7 | C#:7 |
| D7 | D:maj | D:7 | D:7 | D:7 | D:7 | D:7 | D:7 |
| D#7 | D#:maj | D#:7 | D#:7 | D#:7 | D#:7 | D#:7 | D#:7 |
| E7 | E:maj | E:maj | E:7 | E:maj | E:maj | E:maj | E:maj |
| F7 | F:maj | F:7 | F:7 | F:7 | F:7 | F:7 | F:7 |
| F#7 | F#:maj | F#:7 | F#:7 | F#:7 | F#:7 | F#:7 | F#:7 |
| G7 | G:maj | G:7 | G:7 | G:7 | G:7 | G:7 | G:7 |
| G#7 | G#:maj | G#:7 | G#:7 | G#:7 | G#:7 | G#:7 | G#:7 |
| A7 | A:maj | A:maj | A:7 | A:maj | A:maj | A:maj | A:maj |
| A#7 | A#:maj | A#:7 | A#:7 | A#:7 | A#:7 | A#:7 | A#:7 |
| B7 | B:maj | B:7 | B:7 | B:maj | B:maj | B:maj | B:maj |
| Cmaj7 | C:maj | C:maj7 | C:maj7 | C:maj7 | C:maj7 | C:maj7 | C:maj7 |
| C#maj7 | C#:maj | C#:maj7 | C#:maj7 | C#:maj7 | C#:maj7 | C#:maj7 | C#:maj7 |
| Dmaj7 | D:maj | D:maj7 | D:maj7 | D:maj7 | D:maj7 | D:maj7 | D:maj7 |
| D#maj7 | D#:maj | D#:maj7 | D#:maj7 | D#:maj7 | D#:maj7 | D#:maj7 | D#:maj7 |
| Emaj7 | E:maj | E:maj | E:maj7 | E:maj | E:maj | E:maj | E:maj |
| Fmaj7 | F:maj | F:maj7 | F:maj7 | F:maj7 | F:maj7 | F:maj7 | F:maj7 |
| F#maj7 | F#:maj | F#:maj7 | F#:maj7 | F#:maj7 | F#:maj7 | F#:maj7 | F#:maj7 |
| Gmaj7 | G:maj | G:maj7 | G:maj7 | G:maj7 | G:maj7 | G:maj7 | G:maj7 |
| G#maj7 | G#:maj | G#:maj7 | G#:maj7 | G#:maj7 | G#:maj7 | G#:maj7 | G#:maj7 |
| Amaj7 | A:maj | A:maj7 | A:maj7 | A:maj | A:maj | A:maj | A:maj |
| A#maj7 | A#:maj | A#:maj7 | A#:maj7 | A#:maj7 | A#:maj7 | A#:maj7 | A#:maj7 |
| Bmaj7 | B:maj | B:maj | B:maj7 | B:maj | B:maj | B:maj | B:maj |
| Cm7 | C:min | C:min7 | C:min7 | C:min7 | C:min7 | C:min7 | C:min7 |
| C#m7 | C#:min | C#:min7 | C#:min7 | C#:min | C#:min | C#:min | C#:min |
| Dm7 | D:min | D:min7 | D:min7 | D:min7 | D:min7 | D:min7 | D:min7 |
| D#m7 | D#:min | D#:min7 | D#:min7 | D#:min7 | D#:min7 | D#:min7 | D#:min7 |
| Em7 | E:min | E:min7 | E:min7 | E:min7 | E:min7 | E:min7 | E:min7 |
| Fm7 | F:min | F:min7 | F:min7 | F:min7 | F:min7 | F:min7 | F:min7 |
| F#m7 | F#:min | F#:min7 | F#:min7 | F#:min | F#:min | F#:min | F#:min |
| Gm7 | G:min | G:min7 | G:min7 | G:min7 | G:min7 | G:min7 | G:min7 |
| G#m7 | G#:min | G#:min7 | G#:min7 | G#:min7 | G#:min7 | G#:min7 | G#:min7 |
| Am7 | A:min | A:min7 | A:min7 | A:min7 | A:min7 | A:min7 | A:min7 |
| A#m7 | A#:min | A#:min7 | A#:min7 | A#:min7 | A#:min7 | A#:min7 | A#:min7 |
| Bm7 | B:min | B:min | B:min | B:min | B:min | B:min | B:min |

## Complete-case candidate margins

Margins use only cases with a candidate for the true quality; diminished cases are excluded.

| Formulation | True rank | Winner | True | Runner-up | Winner-runner | Winner-true | Tie rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_template_coverage | 1.452 | 1.310 | 1.293 | 1.160 | 0.150 | 0.018 | 32.1% |
| bidirectional_f1 | 1.083 | 1.297 | 1.293 | 1.130 | 0.166 | 0.004 | 0.0% |
| jaccard | 1.024 | 1.294 | 1.293 | 1.054 | 0.240 | 0.001 | 0.0% |
| unexplained_penalty_0.10 | 1.119 | 1.308 | 1.293 | 1.146 | 0.162 | 0.015 | 0.0% |
| unexplained_penalty_0.20 | 1.119 | 1.305 | 1.293 | 1.134 | 0.171 | 0.012 | 0.0% |
| unexplained_penalty_0.30 | 1.119 | 1.302 | 1.293 | 1.124 | 0.178 | 0.010 | 0.0% |
| specificity_tie_rule | 1.131 | 1.310 | 1.293 | 1.160 | 0.150 | 0.018 | 32.1% |

## Selection metrics

| Formulation | Complete supported | Seventh | Robustness mean | Balanced mean |
| --- | --- | --- | --- | --- |
| baseline_template_coverage | 57.1% | 0.0% | 35.2% | 30.8% |
| bidirectional_f1 | 94.0% | 86.1% | 68.9% | 83.0% |
| jaccard | 98.8% | 97.2% | 76.1% | 90.7% |
| unexplained_penalty_0.10 | 89.3% | 75.0% | 65.0% | 76.4% |
| unexplained_penalty_0.20 | 89.3% | 75.0% | 65.9% | 76.7% |
| unexplained_penalty_0.30 | 89.3% | 75.0% | 67.5% | 77.3% |
| specificity_tie_rule | 89.3% | 75.0% | 49.2% | 71.1% |

## Decision gate

**B. BIDIRECTIONAL_MATCH_WINNER**. Selected `jaccard`.

Maximize the mean of supported complete exact, complete seventh exact, and mean supported robustness exact; break ties by robustness, then the simpler named formulation.

## Frozen controls

`{"bass": "minimum MIDI pitch in each voicing", "candidate_order": "source template order; only specificity_tie_rule changes equal-score ordering", "detected_key": "E major", "other_score_terms": ["bass_bonus", "key_prior", "suspension_adjustment", "complexity_penalty"], "templates": "unchanged 85-candidate inventory"}`

## Limitations

- Diminished templates remain absent and diminished cases are marked vocabulary-limited.
- Key priors, bass behavior, suspension adjustment, complexity penalty, and candidate inventory remain frozen even when they cause residual errors.
- Oracle and robustness pitch sets do not represent audio transcription or segmentation uncertainty.
- Candidate margins are diagnostics, not calibrated confidence.
