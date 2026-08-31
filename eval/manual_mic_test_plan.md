# Manual Mic-Recording Test Plan

Eight progressions to record manually through the HorizonJam web app's
**🎤 Start Recording** flow, to verify the end-to-end mic path works on real
audio with the **hybrid** detector (default after Phase 2).

This is a manual checklist, not an automated scoring harness. The web app
will analyze each recording; you compare the detected progression by eye to
the **expected** column.

## Recording conditions (every test)

- **Length**: 8-12 seconds total
- **Pace**: each chord = 2 beats (~1 sec) or 4 beats (~2 sec)
- **Environment**: quiet room, no fan/AC noise
- **Source**: clean guitar or piano, single instrument, no backing track
- **Mic**: laptop or external, headphones recommended to keep tutor TTS out
  of the recording
- **Tuning**: instrument in standard tuning, A=440

## The progressions

| # | Key | Progression | Common in |
|---|---|---|---|
| 1 | G major | **G - D - Em - C** | folk, country, "Don't Stop Believin'" feel |
| 2 | C major | **C - G - Am - F** | "Let It Be" / Axis-of-Awesome 4-chord |
| 3 | D major | **D - A - Bm - G** | "Boulevard of Broken Dreams" feel |
| 4 | A major | **A - E - F#m - D** | bright pop |
| 5 | E minor | **Em - C - G - D** | classic rock-ballad backbone |
| 6 | A minor | **Am - F - C - G** | "Shape of You" relative-minor case |
| 7 | E major | **E - B - C#m - A** | sharper pop key, tests B-major detection |
| 8 | F major | **F - C - Dm - Bb** | flat-key test (Bb often weak for chroma) |

## How to run a test (one progression)

1. **Start the three services** (defaults to hybrid detector — no env needed):
   ```bash
   # Terminal 1
   python -m uvicorn tts_server:app --host 0.0.0.0 --port 5000
   # Terminal 2
   python tutor_ws_relay.py
   # Terminal 3
   npm run dev
   ```
   To force a non-default detector for an A/B run, set the env var before
   starting the relay: `HORIZONJAM_DETECTOR=production python tutor_ws_relay.py`.

2. **Open** http://localhost:3000.

3. Click **🎤 Start Recording** in the *Record from Microphone* card. Grant
   mic permission on the browser prompt (first time only).

4. **Play the progression cleanly.** Watch the green VU meter — if it stays
   near 0, your mic isn't picking the instrument up; stop and adjust.

5. Click **⏹ Stop** when done. Hit **▶ Play Preview** to confirm the audio
   captured the chords audibly.

6. Click **🎵 Analyze Recording**. Status flows:
   `Encoding recording to WAV...` → `WAV ready (NN KB) — uploading...` →
   `Detecting chords...` → `Analysis complete!`

7. **Capture the result** in the *Chord Progression* card:
   - The detected key (top line: "Key: G Major")
   - The chord pills (the actual detected sequence)

8. **Log a row** in `eval/manual_mic_results.md` — one row per recording.

## Per-progression checklist

For each progression, capture:

- [ ] Recorded cleanly (no clipping, audible chords)
- [ ] Web app status reached `Analysis complete!`
- [ ] **Expected chord sequence:** matches the row above
- [ ] **Detected chord sequence:** ________________
- [ ] **Detected key:** ________________ (expected: column 2)
- [ ] **Any warnings shown in the Developer state panel?** ________________
- [ ] **Row added to `manual_mic_results.md`**

## Quick scoring rubric

For each progression, score one point per matching chord (root match
ignoring quality):

- **8/8**: detector is rock-solid on clean input
- **6-7/8**: working well; isolated errors expected on harder chord shapes
  (Bb, F#m, C#m)
- **4-5/8**: detector is degrading on real-world audio. Tells us source
  separation / pre-processing is the next priority.
- **< 4/8**: investigate before any further demo. Likely cause: instrument
  bleed, room noise, or low signal level. Check the mic VU meter while
  recording.

## What this is *not*

- Not a published accuracy number
- Not statistically meaningful (N=8, single performer, single room)
- Not a substitute for GuitarSet / Isophonics benchmarking

It's a real-world sanity check: does the mic-recording feature actually
identify chords a beginner would recognize, when you play them cleanly into
a laptop mic?

## After running

Save the filled-in version of this checklist to
`eval/mic_test_runs/<YYYY-MM-DD>.md` so we have a record over time of how
detection accuracy on real audio is trending.
