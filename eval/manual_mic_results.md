# Manual Mic-Recording Test Results

Fill this in as you work through `manual_mic_test_plan.md`. Each row is one
recording of one progression on the web app. Add new rows below the
template; keep old rows around so we can see how detection accuracy on real
audio trends over time.

Detector used for these runs (default): **hybrid** via `HORIZONJAM_DETECTOR`.
Override at the shell to A/B against a different detector:
```bash
HORIZONJAM_DETECTOR=production python tutor_ws_relay.py
HORIZONJAM_DETECTOR=hybrid     python tutor_ws_relay.py    # default
HORIZONJAM_DETECTOR=rule_viterbi python tutor_ws_relay.py
```

## How to fill a row

After each recording:
1. Watch the relay's terminal log lines (`[upload]`, `[INFO horizonjam.detection]`,
   `Detection complete: detector=...`)
2. In the web app, copy the **Chord Progression** card text and the detected
   **Key**
3. Drop both into the table below, mark Good / Partial / Bad based on the
   rubric in `manual_mic_test_plan.md`
4. Commit (or screenshot) when you've done all 8

## Results

| Test ID | Date | Detector | Instrument | Input type | Expected progression | Detected progression | Estimated key | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|
| _T1_ | _YYYY-MM-DD_ | hybrid | _guitar / piano_ | _mic / file_ | G - D - Em - C | _paste from UI_ | _e.g. G Major_ | _Good / Partial / Bad_ | _e.g. picked Em as G; rest correct_ |
| T1 |  | hybrid |  | mic | G - D - Em - C |  |  |  |  |
| T2 |  | hybrid |  | mic | C - G - Am - F |  |  |  |  |
| T3 |  | hybrid |  | mic | D - A - Bm - G |  |  |  |  |
| T4 |  | hybrid |  | mic | A - E - F#m - D |  |  |  |  |
| T5 |  | hybrid |  | mic | Em - C - G - D |  |  |  |  |
| T6 |  | hybrid |  | mic | Am - F - C - G |  |  |  |  |
| T7 |  | hybrid |  | mic | E - B - C#m - A |  |  |  |  |
| T8 |  | hybrid |  | mic | F - C - Dm - Bb |  |  |  |  |

## Rollup (fill after the table)

- **Total chords scored**: ___ / 32  (4 chords × 8 progressions)
- **Per-chord accuracy** (root match, ignoring quality): ___ %
- **Good progressions (≥ 3 of 4 chords)**: ___ / 8
- **Bad progressions (≤ 1 of 4 chords)**: ___ / 8

## Per-run logging cheat sheet

What you'll see in the relay terminal for each run (these are the lines
Phase 3 wires up — grep on them):

```
[upload] filename='recording_<ts>.wav' bytes=NNNNNN converted_from=native final_path=upload_recording_...wav
[INFO horizonjam.detection] detector=hybrid input=...wav size=NNNNNB sr=44100 duration=10.20 sec
[INFO horizonjam.detection] detector hybrid produced N raw events
[INFO horizonjam.detection] normalized N -> M events; W warnings
[INFO horizonjam.detection] chord sequence: G - D - Em - C
🎹 Detected key: G Major (KS r=0.89)
✅ Detection complete: detector=hybrid events_in=N events_out=M key=G Major warnings=W
```

If `events_out=0`, the recording probably failed (mic level too low, room
noise, or instrument out of tune). Re-record before scoring as Bad.
