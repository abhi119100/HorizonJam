# BasicPitch Direct Evidence Gate

Decision: **B DIRECT_BETTER**.

L1 representation/runtime evidence only. Generated cases are synthetic and the repository WAV has no verified real-performance label.

## Cases

| Case | Direct | MIDI | Matched | Ordering | Chords equal |
| --- | ---: | ---: | ---: | --- | --- |
| block_c_major | 3 | 3 | 3 | False | True |
| block_g7 | 4 | 4 | 4 | False | True |
| arpeggio_c_major | 6 | 6 | 6 | False | True |
| overlapping_notes | 9 | 9 | 9 | False | True |
| repository_pop_wav | 4 | 4 | 4 | False | True |

## Aggregate

- Matched notes: 26
- Direct-only / MIDI-only: 0 / 0
- Maximum onset / offset delta: 0.001100s / 0.001100s
- Mean direct conversion: 0.008667s
- Mean MIDI serialization: 0.009065s
- Mean MIDI read/parse: 0.005597s

## Observed information boundary

- MIDI changes: amplitude is quantized to integer MIDI velocity
- MIDI changes: note ordering can differ after serialization/parsing
- MIDI changes: model output tensors are not represented by parsed MIDI notes

Direct evidence is preferred for developer inspection because it retains richer source evidence. The existing MIDI path remains required by the active symbolic detector, and no default detector behavior changed.
