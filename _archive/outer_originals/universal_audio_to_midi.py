#!/usr/bin/env python3
"""
Pure Audio-to-MIDI Converter
Uses CREPE + Librosa for accurate pitch detection and MIDI note generation
No chord detection - just clean note transcription

Features:
- CREPE for high-accuracy pitch detection (if available)
- Librosa for robust pitch tracking and onset detection
- Instrument-agnostic design
- Clean MIDI note output
- Noise filtering and note cleaning
"""

import librosa
import numpy as np
import pretty_midi
from pathlib import Path
import argparse
import sys
import time

try:
    import crepe
    CREPE_AVAILABLE = True
except ImportError:
    CREPE_AVAILABLE = False
    print("⚠️  CREPE not available. Install with: pip install crepe tensorflow")

class AudioToMIDI:
    def __init__(self, 
                 sample_rate=22050,
                 hop_length=512,
                 confidence_threshold=0.3,
                 min_note_duration=0.1,
                 max_note_duration=4.0):
        """
        Pure Audio-to-MIDI converter
        
        Args:
            sample_rate: Audio sample rate for analysis
            hop_length: Frame hop length for librosa analysis
            confidence_threshold: Minimum confidence for note detection
            min_note_duration: Minimum note duration in seconds
            max_note_duration: Maximum note duration in seconds
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.confidence_threshold = confidence_threshold
        self.min_note_duration = min_note_duration
        self.max_note_duration = max_note_duration
        
    def load_audio(self, audio_path):
        """Load and preprocess audio"""
        print(f"🎵 Loading audio: {Path(audio_path).name}")
        
        # Load with librosa
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Normalize audio
        y = librosa.util.normalize(y)
        
        # Remove silence from beginning and end
        y, _ = librosa.effects.trim(y, top_db=20)
        
        duration = len(y) / sr
        print(f"   Duration: {duration:.2f}s, Sample rate: {sr}Hz")
        
        return y, sr
    
    def crepe_pitch_detection(self, y, sr):
        """High-accuracy pitch detection using CREPE"""
        if not CREPE_AVAILABLE:
            return None, None, None
            
        print("🧠 Running CREPE pitch detection...")
        start_time = time.time()
        
        # CREPE prediction with high quality settings
        time_axis, frequency, confidence, activation = crepe.predict(
            y, sr,
            model_capacity='large',  # Best accuracy
            viterbi=True,           # Smooth pitch tracking
            step_size=10,           # High time resolution (10ms)
            verbose=0
        )
        
        duration = time.time() - start_time
        print(f"   CREPE analysis: {duration:.1f}s")
        print(f"   Detected {len(frequency)} pitch frames")
        print(f"   Confidence range: {confidence.min():.2f} - {confidence.max():.2f}")
        
        return time_axis, frequency, confidence
    
    def librosa_pitch_detection(self, y, sr):
        """Pitch detection and onset analysis using librosa"""
        print("🔬 Running Librosa pitch analysis...")
        start_time = time.time()
        
        # Harmonic-percussive separation for cleaner pitch detection
        y_harmonic, y_percussive = librosa.effects.hpss(y, margin=3.0)
        
        # Pitch tracking with pyin
        f0_pyin, voiced_flag, voiced_prob = librosa.pyin(
            y_harmonic,
            fmin=librosa.note_to_hz('C1'),   # Wide frequency range
            fmax=librosa.note_to_hz('C8'),
            hop_length=self.hop_length,
            resolution=0.1                   # Fine pitch resolution
        )
        
        # Onset detection for note timing
        onset_frames = librosa.onset.onset_detect(
            y=y, sr=sr,
            hop_length=self.hop_length,
            units='time',
            backtrack=True,
            delta=0.1
        )
        
        # RMS energy for dynamics
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)
        
        duration = time.time() - start_time
        print(f"   Librosa analysis: {duration:.1f}s")
        print(f"   Detected {len(onset_frames)} onsets")
        print(f"   Pitch frames: {len(f0_pyin)}")
        
        return f0_pyin, voiced_prob, onset_frames, rms
    
    def generate_notes(self, crepe_data, librosa_data, sr):
        """Generate MIDI notes from pitch detection data"""
        print("🎼 Generating MIDI notes...")
        
        notes = []
        
        # Choose primary pitch source
        if crepe_data and crepe_data[0] is not None:
            # Use CREPE as primary (higher accuracy)
            time_frames, frequencies, confidences = crepe_data
            print(f"   Using CREPE as primary pitch source")
        else:
            # Use librosa as fallback
            f0_pyin, voiced_prob, onsets, rms = librosa_data
            time_frames = librosa.frames_to_time(
                np.arange(len(f0_pyin)), sr=sr, hop_length=self.hop_length
            )
            frequencies = f0_pyin
            confidences = voiced_prob
            print(f"   Using Librosa as primary pitch source")
        
        # Get onset times for note segmentation
        if librosa_data:
            _, _, onset_times, rms_energy = librosa_data
        else:
            onset_times = []
            rms_energy = None
        
        print(f"   Processing {len(time_frames)} time frames...")
        
        # Generate notes from pitch data
        for i, (time_point, freq_hz, confidence) in enumerate(
            zip(time_frames, frequencies, confidences)
        ):
            # Skip low confidence or invalid pitches
            if confidence < self.confidence_threshold or np.isnan(freq_hz) or freq_hz <= 0:
                continue
            
            # Convert to MIDI pitch
            try:
                midi_pitch = librosa.hz_to_midi(freq_hz)
                if midi_pitch < 21 or midi_pitch > 108:  # Piano range
                    continue
            except:
                continue
            
            # Calculate velocity from energy (if available)
            if rms_energy is not None and rms_energy.shape[1] > 0:
                frame_idx = min(i, rms_energy.shape[1] - 1)
                energy = rms_energy[0, frame_idx]
                velocity = int(np.clip(energy * 127 * 2, 30, 127))
            else:
                velocity = int(confidence * 127)
            
            # Find note duration using onsets
            next_onset = None
            for onset in onset_times:
                if onset > time_point + 0.05:  # Small buffer
                    next_onset = onset
                    break
            
            if next_onset is not None:
                duration = min(next_onset - time_point, self.max_note_duration)
            else:
                duration = 0.5  # Default duration
            
            duration = max(duration, self.min_note_duration)
            
            # Create note
            note = {
                'pitch': int(round(midi_pitch)),
                'start': time_point,
                'end': time_point + duration,
                'velocity': velocity,
                'confidence': confidence
            }
            notes.append(note)
        
        print(f"   Generated {len(notes)} raw notes")
        return notes
    
    def clean_notes(self, notes):
        """Clean up notes by removing duplicates and merging overlaps"""
        print("🧹 Cleaning notes...")
        
        if not notes:
            return notes
        
        # Sort by start time
        notes.sort(key=lambda x: x['start'])
        
        # Remove overlapping duplicates (same pitch, similar timing)
        cleaned_notes = []
        for note in notes:
            is_duplicate = False
            for existing in cleaned_notes:
                if (abs(existing['start'] - note['start']) < 0.1 and
                    abs(existing['pitch'] - note['pitch']) < 1):
                    # Keep the one with higher confidence
                    if note['confidence'] > existing['confidence']:
                        cleaned_notes.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                cleaned_notes.append(note)
        
        # Merge very close notes of same pitch
        merged_notes = []
        i = 0
        while i < len(cleaned_notes):
            current = cleaned_notes[i]
            
            # Look for mergeable notes
            while (i + 1 < len(cleaned_notes) and
                   cleaned_notes[i + 1]['pitch'] == current['pitch'] and
                   cleaned_notes[i + 1]['start'] - current['end'] < 0.1):
                next_note = cleaned_notes[i + 1]
                # Merge notes
                current['end'] = max(current['end'], next_note['end'])
                current['velocity'] = max(current['velocity'], next_note['velocity'])
                i += 1
            
            merged_notes.append(current)
            i += 1
        
        print(f"   Cleaned: {len(notes)} → {len(merged_notes)} notes")
        return merged_notes
    
    def create_midi(self, notes, output_path):
        """Create MIDI file from notes"""
        print(f"💾 Creating MIDI file: {Path(output_path).name}")
        
        # Create MIDI object
        midi = pretty_midi.PrettyMIDI()
        
        # Create instrument (program 0 = acoustic grand piano)
        instrument = pretty_midi.Instrument(program=0, name="Audio Transcription")
        
        # Add notes to instrument
        for note_data in notes:
            note = pretty_midi.Note(
                velocity=note_data['velocity'],
                pitch=note_data['pitch'],
                start=note_data['start'],
                end=note_data['end']
            )
            instrument.notes.append(note)
        
        midi.instruments.append(instrument)
        
        # Write MIDI file
        midi.write(str(output_path))
        
        # Summary
        total_duration = midi.get_end_time()
        note_density = len(notes) / total_duration if total_duration > 0 else 0
        
        print(f"   ✅ MIDI created successfully!")
        print(f"   📊 Total notes: {len(notes)}")
        print(f"   ⏱️  Duration: {total_duration:.2f}s")
        print(f"   🎵 Note density: {note_density:.1f} notes/second")
        
        return output_path
    
    def convert(self, audio_path, output_path=None):
        """Main conversion method"""
        print("🎯 Audio-to-MIDI Conversion")
        print("=" * 50)
        
        # Generate output path if not provided
        if output_path is None:
            audio_file = Path(audio_path)
            output_path = str(audio_file.parent / f"{audio_file.stem}_transcribed.mid")
        
        start_time = time.time()
        
        # Load audio
        y, sr = self.load_audio(audio_path)
        
        # Pitch detection
        crepe_data = self.crepe_pitch_detection(y, sr) if CREPE_AVAILABLE else None
        librosa_data = self.librosa_pitch_detection(y, sr)
        
        # Generate notes
        notes = self.generate_notes(crepe_data, librosa_data, sr)
        
        # Clean notes
        notes = self.clean_notes(notes)
        
        # Create MIDI
        midi_path = self.create_midi(notes, output_path)
        
        total_time = time.time() - start_time
        print(f"\n🎉 Conversion complete in {total_time:.1f}s")
        print(f"🎼 MIDI saved: {midi_path}")
        
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Pure Audio-to-MIDI Converter')
    parser.add_argument('input', help='Input audio file (.wav, .mp3, .flac, etc.)')
    parser.add_argument('-o', '--output', help='Output MIDI file (optional)')
    parser.add_argument('--confidence', type=float, default=0.3, 
                       help='Confidence threshold (0.1-0.9, default: 0.3)')
    parser.add_argument('--min-duration', type=float, default=0.1,
                       help='Minimum note duration in seconds (default: 0.1)')
    parser.add_argument('--max-duration', type=float, default=4.0,
                       help='Maximum note duration in seconds (default: 4.0)')
    
    args = parser.parse_args()
    
    # Check input file
    if not Path(args.input).exists():
        print(f"❌ Error: Input file '{args.input}' not found")
        return 1
    
    # Create converter
    converter = AudioToMIDI(
        confidence_threshold=args.confidence,
        min_note_duration=args.min_duration,
        max_note_duration=args.max_duration
    )
    
    try:
        # Convert audio to MIDI
        midi_path = converter.convert(args.input, args.output)
        print(f"\n✨ Success! Use your MIDI file: {midi_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main()) 