"""
Training Data Collection System for Chord Detection
Collects user corrections and extracts features for supervised learning
"""

import json
import time
import os
import numpy as np
import librosa
import pretty_midi
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class ChordTrainingDataCollector:
    """Collects training data from user corrections and audio analysis"""
    
    def __init__(self, data_dir: str = "training_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.training_db_path = self.data_dir / "chord_training_database.json"
        self.features_dir = self.data_dir / "features"
        self.features_dir.mkdir(exist_ok=True)
        
        # Load existing training data
        self.training_db = self.load_training_database()
        
    def load_training_database(self) -> List[Dict]:
        """Load existing training database"""
        if self.training_db_path.exists():
            with open(self.training_db_path, 'r') as f:
                return json.load(f)
        return []
    
    def save_training_database(self):
        """Save training database to disk"""
        with open(self.training_db_path, 'w') as f:
            json.dump(self.training_db, f, indent=2)
    
    def collect_user_correction(self, 
                              audio_file: str,
                              detected_chords: List[Dict],
                              corrected_chords: List[Dict],
                              metadata: Optional[Dict] = None) -> str:
        """
        Collect a training sample from user correction
        
        Args:
            audio_file: Path to audio/MIDI file
            detected_chords: What the system detected
            corrected_chords: User's corrections (ground truth)
            metadata: Additional info (key, tempo, etc.)
        
        Returns:
            sample_id: Unique identifier for this training sample
        """
        
        sample_id = f"sample_{int(time.time())}_{len(self.training_db)}"
        
        # Extract comprehensive features
        print(f"🔍 Extracting features for {Path(audio_file).name}...")
        features = self.extract_comprehensive_features(audio_file)
        
        # Create training sample
        training_sample = {
            'sample_id': sample_id,
            'audio_file': str(audio_file),
            'timestamp': time.time(),
            'detected_chords': detected_chords,
            'ground_truth_chords': corrected_chords,
            'features': features,
            'metadata': metadata or {},
            'accuracy_metrics': self.calculate_accuracy_metrics(detected_chords, corrected_chords)
        }
        
        # Add to database
        self.training_db.append(training_sample)
        self.save_training_database()
        
        print(f"✅ Training sample {sample_id} collected!")
        print(f"📊 Database now contains {len(self.training_db)} samples")
        
        return sample_id
    
    def extract_comprehensive_features(self, audio_file: str, detected_chords: List[Dict], corrected_chords: List[Dict]) -> List[Dict]:
        """Extract comprehensive features for ML training"""
        
        features_list = []
        
        try:
            # Handle MIDI files
            if Path(audio_file).suffix.lower() in ['.mid', '.midi']:
                features_list = self.extract_ml_features(audio_file, corrected_chords)
            else:
                # Handle audio files
                features = self.extract_audio_features(audio_file)
                features_list.append({
                    'timestamp': 0,
                    'end_time': features['audio_stats']['duration'],
                    'duration': features['audio_stats']['duration'],
                    'chord': 'Unknown',
                    'confidence': 1.0,
                    'features': features,
                    'tempo_bpm': None,
                    'beat_duration': None
                })
                
            # Add file metadata
            for features_dict in features_list:
                features_dict['file_info'] = {
                    'filename': Path(audio_file).name,
                    'file_size': Path(audio_file).stat().st_size,
                    'file_type': Path(audio_file).suffix.lower()
                }
            
        except Exception as e:
            print(f"⚠️ Error extracting features: {e}")
            features_list = [{'error': str(e)}]
            
        return features_list
    
    def extract_ml_features(self, midi_path: str, chord_events: List[Dict]) -> List[Dict]:
        """
        Extract comprehensive features for ML training from MIDI and chord events
        Uses beat-synchronous windowing for better boundary alignment
        """
        try:
            # Load MIDI for feature extraction
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            
            # Estimate tempo for beat-synchronous windowing
            tempo_bpm = self._estimate_tempo(midi_data)
            beat_duration = 60.0 / tempo_bpm if tempo_bpm > 0 else 0.5  # fallback to 120 BPM
            
            features_list = []
            
            for event in chord_events:
                # Align to beat grid for better boundary consistency
                aligned_start, aligned_end = self._align_to_beat_grid(
                    event['timestamp'], event['end_time'], beat_duration
                )
                
                features = self._extract_window_features(
                    midi_data, aligned_start, aligned_end
                )
                
                # Add beat-synchronous metadata
                features.extend([
                    tempo_bpm,
                    beat_duration,
                    (aligned_end - aligned_start) / beat_duration,  # duration in beats
                    aligned_start % beat_duration,  # beat phase
                ])
                
                features_dict = {
                    'timestamp': aligned_start,
                    'end_time': aligned_end,
                    'duration': aligned_end - aligned_start,
                    'chord': event['chord'],
                    'confidence': event.get('confidence', 1.0),
                    'features': features,
                    'tempo_bpm': tempo_bpm,
                    'beat_duration': beat_duration
                }
                
                features_list.append(features_dict)
            
            return features_list
            
        except Exception as e:
            print(f"❌ Feature extraction failed: {e}")
            return []
    
    def _estimate_tempo(self, midi_data: pretty_midi.PrettyMIDI) -> float:
        """Estimate tempo from MIDI data"""
        try:
            # Use tempo changes if available
            if midi_data.tempo_changes:
                return midi_data.tempo_changes[0].tempo
            
            # Estimate from note onsets
            all_onsets = []
            for instrument in midi_data.instruments:
                if not instrument.is_drum:
                    all_onsets.extend([note.start for note in instrument.notes])
            
            if len(all_onsets) < 4:
                return 120.0  # default
            
            all_onsets.sort()
            intervals = [all_onsets[i+1] - all_onsets[i] for i in range(len(all_onsets)-1)]
            intervals = [i for i in intervals if 0.1 < i < 2.0]  # filter reasonable intervals
            
            if not intervals:
                return 120.0
            
            # Find most common interval (quantized)
            import numpy as np
            hist, bins = np.histogram(intervals, bins=50)
            most_common_interval = bins[np.argmax(hist)]
            
            # Convert to BPM (assuming quarter note intervals)
            estimated_bpm = 60.0 / most_common_interval
            return max(60.0, min(200.0, estimated_bpm))  # clamp to reasonable range
            
        except Exception:
            return 120.0  # fallback
    
    def _align_to_beat_grid(self, start_time: float, end_time: float, beat_duration: float) -> tuple:
        """Align time boundaries to beat grid for consistency"""
        # Snap to nearest beat boundaries
        aligned_start = round(start_time / beat_duration) * beat_duration
        aligned_end = round(end_time / beat_duration) * beat_duration
        
        # Ensure minimum duration of one beat
        if aligned_end <= aligned_start:
            aligned_end = aligned_start + beat_duration
            
        return aligned_start, aligned_end
    
    def _extract_window_features(self, midi_data: pretty_midi.PrettyMIDI, start_time: float, end_time: float) -> List[float]:
        """Extract features for a specific time window"""
        # Basic MIDI statistics
        features = []
        
        all_notes = []
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                if start_time <= note.start < end_time:
                    all_notes.append({
                        'start': note.start,
                        'end': note.end,
                        'pitch': note.pitch,
                        'velocity': note.velocity
                    })
        
        if all_notes:
            # Timing features
            note_starts = [n['start'] for n in all_notes]
            note_durations = [n['end'] - n['start'] for n in all_notes]
            velocities = [n['velocity'] for n in all_notes]
            pitches = [n['pitch'] for n in all_notes]
            
            features.extend([
                np.mean(note_durations),
                np.std(note_durations),
                len(all_notes) / (end_time - start_time),
                np.mean(velocities),
                np.std(velocities)
            ])
            
            # Pitch features
            features.extend([
                max(pitches) - min(pitches),  # pitch_range
                np.mean(pitches),  # avg_pitch
                np.std(pitches),  # std_pitch
                len(set(pitches))  # unique_pitches
            ])
                
            # Harmonic features
            features.extend(self.extract_harmonic_features(all_notes))
                
        else:
            # No notes in window - return default features
            features.extend([0.0] * 9)  # 5 timing + 4 pitch features
            
        return features
    
    def extract_audio_features(self, audio_file: str) -> Dict:
        """Extract features from audio file"""
        features = {}
        
        try:
            y, sr = librosa.load(audio_file, sr=22050)
            
            # Basic audio features
            features['audio_stats'] = {
                'duration': len(y) / sr,
                'sample_rate': sr,
                'rms_energy': float(np.sqrt(np.mean(y**2)))
            }
            
            # Spectral features
            features['spectral_features'] = {
                'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
                'spectral_bandwidth': float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))),
                'spectral_rolloff': float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))),
                'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y)))
            }
            
            # Harmonic features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma_features'] = {
                'chroma_mean': chroma.mean(axis=1).tolist(),
                'chroma_std': chroma.std(axis=1).tolist()
            }
            
            # MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_features'] = {
                'mfcc_mean': mfcc.mean(axis=1).tolist(),
                'mfcc_std': mfcc.std(axis=1).tolist()
            }
            
            # Tempo estimation
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                features['rhythm_features'] = {
                    'estimated_tempo': float(tempo)
                }
            except:
                features['rhythm_features'] = {'estimated_tempo': None}
                
        except Exception as e:
            features['audio_error'] = str(e)
            
        return features
    
    def extract_harmonic_features(self, notes: List[Dict]) -> Dict:
        """Extract harmonic and chord-specific features"""
        
        if not notes:
            return {}
        
        # Group notes by time windows
        time_windows = self.group_notes_by_time(notes, window_size=1.0)
        
        harmonic_features = {
            'num_time_windows': len(time_windows),
            'avg_notes_per_window': np.mean([len(w) for w in time_windows]),
            'chord_complexity_scores': [],
            'interval_patterns': []
        }
        
        for window in time_windows:
            if len(window) >= 2:
                pitches = sorted([n['pitch'] for n in window])
                
                # Chord complexity (number of unique pitch classes)
                pitch_classes = [p % 12 for p in pitches]
                complexity = len(set(pitch_classes))
                harmonic_features['chord_complexity_scores'].append(complexity)
                
                # Interval patterns
                intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
                harmonic_features['interval_patterns'].extend(intervals)
        
        # Summary statistics
        if harmonic_features['chord_complexity_scores']:
            harmonic_features['avg_chord_complexity'] = np.mean(harmonic_features['chord_complexity_scores'])
            harmonic_features['std_chord_complexity'] = np.std(harmonic_features['chord_complexity_scores'])
        
        if harmonic_features['interval_patterns']:
            harmonic_features['common_intervals'] = self.get_common_intervals(harmonic_features['interval_patterns'])
        
        return harmonic_features
    
    def group_notes_by_time(self, notes: List[Dict], window_size: float = 1.0) -> List[List[Dict]]:
        """Group notes into time windows"""
        if not notes:
            return []
        
        # Sort by start time
        sorted_notes = sorted(notes, key=lambda x: x['start'])
        
        windows = []
        current_window = []
        window_start = sorted_notes[0]['start']
        
        for note in sorted_notes:
            if note['start'] - window_start <= window_size:
                current_window.append(note)
            else:
                if current_window:
                    windows.append(current_window)
                current_window = [note]
                window_start = note['start']
        
        if current_window:
            windows.append(current_window)
            
        return windows
    
    def get_common_intervals(self, intervals: List[int]) -> Dict:
        """Get statistics on common intervals"""
        if not intervals:
            return {}
        
        interval_counts = defaultdict(int)
        for interval in intervals:
            interval_counts[interval] += 1
        
        # Convert to percentages
        total = len(intervals)
        interval_percentages = {k: (v/total)*100 for k, v in interval_counts.items()}
        
        return {
            'most_common_interval': max(interval_counts.items(), key=lambda x: x[1])[0],
            'interval_distribution': dict(interval_percentages)
        }
    
    def calculate_accuracy_metrics(self, detected: List[Dict], ground_truth: List[Dict]) -> Dict:
        """Calculate accuracy metrics for this sample"""
        
        if not detected or not ground_truth:
            return {'accuracy': 0.0, 'error': 'Empty chord lists'}
        
        # Simple chord name matching
        detected_chords = [c.get('chord', 'Unknown') for c in detected]
        truth_chords = [c.get('chord', 'Unknown') for c in ground_truth]
        
        # Align sequences (simple approach)
        min_len = min(len(detected_chords), len(truth_chords))
        
        if min_len == 0:
            return {'accuracy': 0.0}
        
        matches = sum(1 for i in range(min_len) if detected_chords[i] == truth_chords[i])
        accuracy = matches / min_len
        
        return {
            'accuracy': accuracy,
            'matches': matches,
            'total_compared': min_len,
            'detected_count': len(detected_chords),
            'ground_truth_count': len(truth_chords)
        }
    
    def create_ground_truth_template(self, audio_file: str, detected_chords: List[Dict]) -> Dict:
        """Create a template for user to fill in ground truth"""
        
        template = {
            'audio_file': str(audio_file),
            'instructions': 'Please correct the detected chords below. Set chord to null to remove.',
            'detected_chords': detected_chords,
            'corrected_chords': [
                {
                    'start_time': chord.get('timestamp', 0),
                    'end_time': chord.get('end_time', 0),
                    'detected_chord': chord.get('chord', 'Unknown'),
                    'correct_chord': chord.get('chord', 'Unknown'),  # User should modify this
                    'confidence': chord.get('confidence', 0.5),
                    'notes': 'Add any notes about this correction'
                }
                for chord in detected_chords
            ],
            'metadata': {
                'key_signature': 'E major',  # User should correct
                'tempo': 120,  # User should correct
                'genre': 'unknown',  # User should specify
                'instrument': 'guitar'  # User should specify
            }
        }
        
        return template
    
    def get_training_statistics(self) -> Dict:
        """Get statistics about collected training data"""
        
        if not self.training_db:
            return {'message': 'No training data collected yet'}
        
        total_samples = len(self.training_db)
        accuracies = [s['accuracy_metrics'].get('accuracy', 0) for s in self.training_db if 'accuracy_metrics' in s]
        
        stats = {
            'total_samples': total_samples,
            'avg_accuracy': np.mean(accuracies) if accuracies else 0,
            'accuracy_std': np.std(accuracies) if accuracies else 0,
            'accuracy_range': [min(accuracies), max(accuracies)] if accuracies else [0, 0],
            'data_sources': list(set(Path(s['audio_file']).suffix for s in self.training_db)),
            'collection_timespan': {
                'first_sample': min(s['timestamp'] for s in self.training_db),
                'last_sample': max(s['timestamp'] for s in self.training_db)
            }
        }
        
        return stats
    
    def export_training_data_for_ml(self, output_file: str = None) -> str:
        """Export training data in format suitable for ML training"""
        
        if not output_file:
            output_file = self.data_dir / "ml_training_data.json"
        
        # Prepare data for ML
        ml_data = {
            'metadata': {
                'total_samples': len(self.training_db),
                'export_timestamp': time.time(),
                'feature_description': {
                    'midi_stats': 'Basic MIDI file statistics',
                    'timing_features': 'Note timing and duration features',
                    'pitch_features': 'Pitch range and distribution features',
                    'harmonic_features': 'Chord complexity and interval patterns',
                    'spectral_features': 'Audio spectral characteristics (if audio)',
                    'chroma_features': 'Harmonic content features (if audio)'
                }
            },
            'samples': []
        }
        
        for sample in self.training_db:
            ml_sample = {
                'sample_id': sample['sample_id'],
                'features': sample['features'],
                'ground_truth': sample['ground_truth_chords'],
                'accuracy': sample['accuracy_metrics'].get('accuracy', 0)
            }
            ml_data['samples'].append(ml_sample)
        
        with open(output_file, 'w') as f:
            json.dump(ml_data, f, indent=2)
        
        print(f"📊 ML training data exported to: {output_file}")
        return str(output_file)
