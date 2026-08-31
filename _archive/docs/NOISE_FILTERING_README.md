# ChordAI Noise Filtering System

This system implements a comprehensive noise-shield to reduce console clutter from third-party libraries while preserving important error messages and debug information.

## Features

- **Automatic Warning Filtering**: Silences common deprecation warnings from pkg_resources, setuptools, coremltools, etc.
- **Library Log Level Control**: Sets noisy libraries (chromadb, librosa, tensorflow, etc.) to ERROR level
- **Subprocess Output Filtering**: Shows only relevant HorizonJam output (chord detection results, key detection, etc.)
- **Debug Mode Toggle**: Full verbose output available when needed
- **Error Preservation**: Real errors and critical messages are never hidden

## Usage

### Normal Mode (Clean Output)
```bash
python chordai_gpt_tutor.py --wav "path/to/audio.wav"
```

### Debug Mode (Full Verbose Output)
```bash
# Windows
set CHORDAI_DEBUG=1 && python chordai_gpt_tutor.py --wav "path/to/audio.wav"

# Linux/Mac
CHORDAI_DEBUG=1 python chordai_gpt_tutor.py --wav "path/to/audio.wav"
```

## What Gets Filtered

### Warnings Silenced:
- `pkg_resources` deprecation warnings
- `setuptools` deprecation warnings
- `coremltools` installation warnings
- `librosa` FFT size warnings
- General `UserWarning` messages

### Libraries Set to ERROR Level:
- `chromadb`
- `httpx`
- `urllib3`
- `asyncio`
- `matplotlib`
- `numba`
- `markdown`
- `pretty_midi`
- `librosa`
- `tflite_runtime`
- `tensorflow`
- `basic_pitch`

### Subprocess Output Filtering:
Only shows lines containing:
- `[BEAT_GRID]` - Tempo detection
- `[KEY]` - Key detection
- `[ONSET]` - Onset detection
- `Progression:` - Chord progressions
- Musical emojis (🎵, 🎼, 🎹, 🎯, 📊)
- Chord event detection headers

## Implementation Details

The noise filtering is implemented in three layers:

1. **Early Import Filtering** (`utils/log_silencer.py`)
   - Applied before any third-party imports
   - Sets up warning filters and logging levels
   - Automatically imported by main scripts

2. **Subprocess Output Filtering**
   - Filters HorizonJam pipeline output
   - Preserves only musically relevant information
   - Maintains error visibility

3. **Environment Variable Control**
   - `CHORDAI_DEBUG=1` disables all filtering
   - Allows full diagnostic output when needed
   - No code changes required to toggle modes

## Files Modified

- `utils/log_silencer.py` - Core noise filtering utility
- `chordai_gpt_tutor.py` - Main application with filtering
- `HorizonJam-master/run_pipeline.py` - Pipeline with filtering

## Benefits

- **Professional Output**: Clean, focused console output
- **Faster Debugging**: Less noise to sift through
- **Preserved Functionality**: All features work exactly the same
- **Flexible Control**: Easy to enable full output when needed
- **Error Safety**: Real errors are never hidden

The system maintains full backward compatibility while providing a much cleaner user experience.