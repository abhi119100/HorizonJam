# HorizonJam 🎵

**Advanced Audio-to-MIDI and Chord Analysis Toolkit**

HorizonJam is a comprehensive Python toolkit for converting audio files to MIDI and analyzing musical chord progressions. It combines state-of-the-art audio processing libraries with intelligent chord detection algorithms.

## 🚀 Features

- **Audio-to-MIDI Conversion**: High-accuracy pitch detection using CREPE + Librosa
- **Chord Analysis**: Intelligent chord progression detection from MIDI files
- **Integrated Pipeline**: Seamless audio → MIDI → chords workflow
- **Multiple Algorithms**: Support for both CREPE (high accuracy) and Librosa (fallback)
- **Comprehensive Analysis**: Key detection, chord timing, and musical insights
- **Flexible Configuration**: Customizable parameters for different musical styles

## 📋 Requirements

- Python 3.8+
- Audio files: `.wav`, `.mp3`, `.flac`, `.m4a`
- Output: MIDI files (`.mid`) and chord analysis

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/abhi119100/HorizonJam.git
cd HorizonJam
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

**Essential Dependencies:**
```bash
pip install librosa pretty_midi music21 setuptools
```

**For High Accuracy (Optional):**
```bash
pip install crepe tensorflow
```

**All Dependencies at Once:**
```bash
pip install librosa pretty_midi music21 setuptools crepe tensorflow
```

## 🎵 Usage

### 1. Audio-to-MIDI Conversion

**Basic Conversion:**
```bash
python universal_audio_to_midi.py "your_audio.wav"
```
*Output: `your_audio_transcribed.mid`*

**With Custom Settings:**
```bash
python universal_audio_to_midi.py "audio.wav" --confidence 0.5 --min-duration 0.2
```

**With Custom Output:**
```bash
python universal_audio_to_midi.py "audio.wav" -o "my_song.mid"
```

#### Parameters:
- `--confidence`: Pitch detection confidence threshold (0.1-0.9, default: 0.3)
- `--min-duration`: Minimum note duration in seconds (default: 0.1)
- `--max-duration`: Maximum note duration in seconds (default: 4.0)

### 2. MIDI-to-Chords Analysis

**Basic Chord Analysis:**
```bash
python midi_to_chords.py "your_file.mid"
```

**With Custom Window Size:**
```bash
python midi_to_chords.py "your_file.mid" 1.5
```

**Auto-Detect Window Size:**
```bash
python midi_to_chords.py "your_file.mid" auto
```

#### Output Example:
```
🎼 CHORD PROGRESSION SUMMARY
==================================================
[00:00 - 00:02] → G
[00:02 - 00:04] → C  
[00:04 - 00:06] → D
[00:06 - 00:08] → G

🔑 Detected Key: G major
🎯 Found 4 distinct chord events
```

### 3. Complete Audio-to-Chords Pipeline

**Full Pipeline Analysis:**
```bash
python audio_to_chords_pipeline.py "your_audio.wav"
```

**With Custom Settings:**
```bash
python audio_to_chords_pipeline.py "audio.wav" --confidence 0.4 --window-size 1.5
```

**Keep Intermediate MIDI Files:**
```bash
python audio_to_chords_pipeline.py "audio.wav" --keep-midi
```

#### Pipeline Features:
- Automatic audio → MIDI → chords conversion
- Intelligent window size detection
- Key signature analysis
- Chord event detection
- Performance timing analysis

## 📁 Core Files

### Main Scripts
- **`universal_audio_to_midi.py`** - Audio-to-MIDI converter
- **`midi_to_chords.py`** - MIDI chord analysis
- **`audio_to_chords_pipeline.py`** - Complete pipeline
- **`analyze_basicpitch_results.py`** - MIDI analysis tools

### Utilities
- **`example_pipeline_usage.py`** - Usage examples
- **`run_transcription_benchmark.py`** - Performance benchmarking

### Documentation
- **`algorithm_accuracy_analysis.md`** - Technical analysis
- **`tests/`** - Test audio and MIDI files

## 🎛️ Advanced Configuration

### Audio-to-MIDI Settings

```python
from universal_audio_to_midi import AudioToMIDI

converter = AudioToMIDI(
    sample_rate=22050,
    confidence_threshold=0.3,
    min_note_duration=0.1,
    max_note_duration=4.0
)

midi_path = converter.convert("audio.wav", "output.mid")
```

### Chord Analysis Settings

```python
from midi_to_chords import analyze_midi_chords

# Auto-detect window size
chord_progression, chord_events = analyze_midi_chords("file.mid")

# Manual window size
chord_progression, chord_events = analyze_midi_chords("file.mid", window_size=1.5)
```

## 🔧 Troubleshooting

### Common Issues

**1. "No module named 'librosa'"**
```bash
pip install librosa
```

**2. "CREPE not available"**
```bash
pip install crepe tensorflow
```
*Note: CREPE is optional but provides higher accuracy*

**3. "pkg_resources deprecated warning"**
```bash
pip install setuptools
```

**4. No chords detected**
- Try adjusting `--confidence` (lower values detect more notes)
- Use `--window-size` for manual chord segmentation
- Check that audio contains harmonic content (not just percussion)

### Performance Tips

- **For faster processing**: Skip CREPE installation (uses Librosa only)
- **For higher accuracy**: Install CREPE + TensorFlow
- **For guitar/piano**: Use confidence 0.3-0.5
- **For vocals**: Use confidence 0.4-0.7

## 📊 Example Workflow

```bash
# 1. Convert audio to MIDI
python universal_audio_to_midi.py "song.wav"

# 2. Analyze chords from MIDI
python midi_to_chords.py "song_transcribed.mid"

# 3. Or do both in one step
python audio_to_chords_pipeline.py "song.wav"
```

## 🎼 Supported Musical Content

### Works Best With:
- Piano recordings
- Guitar (acoustic/electric)
- Vocal melodies
- Instrumental solos
- Clear harmonic content

### Limitations:
- Complex polyphonic music (multiple simultaneous melodies)
- Heavy percussion/drums
- Very noisy recordings
- Extremely fast passages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Librosa** - Audio analysis library
- **pretty_midi** - MIDI file handling
- **CREPE** - High-accuracy pitch detection
- **music21** - Music analysis toolkit

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/abhi119100/HorizonJam/issues)
- 📖 **Documentation**: See this README and code comments
- 💡 **Feature Requests**: Open an issue with enhancement label

---

**Made with ❤️ for musicians and developers** 