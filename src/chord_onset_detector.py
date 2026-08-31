import numpy as np
import librosa
from typing import List, Dict, Optional, Tuple
from scipy import signal
from scipy.ndimage import gaussian_filter1d
import pretty_midi

class ChordOnsetDetector:
    """Professional chord onset detection with multiple algorithms"""
    
    def __init__(self):
        self.onset_methods = [
            'spectral_flux',
            'complex_domain',
            'harmonic_change',
            'energy_based',
            'phase_deviation'
        ]
    
    def detect_onsets_from_audio(self, audio_path: str, 
                                hop_length: int = 512) -> Tuple[np.ndarray, Dict]:
        """Detect chord onsets from audio using multiple methods"""
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            onset_results = {}
            all_onsets = []
            
            # Method 1: Spectral flux
            onset_frames_flux = librosa.onset.onset_detect(
                y=y, sr=sr, 
                onset_envelope=librosa.onset.onset_strength(y=y, sr=sr, feature=librosa.feature.spectral_centroid),
                hop_length=hop_length,
                units='time'
            )
            onset_results['spectral_flux'] = onset_frames_flux
            all_onsets.extend(onset_frames_flux)
            
            # Method 2: Complex domain onset detection
            stft = librosa.stft(y, hop_length=hop_length)
            onset_complex = librosa.onset.onset_detect(
                y=y, sr=sr,
                onset_envelope=self._complex_domain_onset_strength(stft, sr, hop_length),
                hop_length=hop_length,
                units='time'
            )
            onset_results['complex_domain'] = onset_complex
            all_onsets.extend(onset_complex)
            
            # Method 3: Harmonic change detection
            harmonic_onsets = self._detect_harmonic_change_onsets(y, sr, hop_length)
            onset_results['harmonic_change'] = harmonic_onsets
            all_onsets.extend(harmonic_onsets)
            
            # Method 4: Energy-based onset detection
            energy_onsets = self._detect_energy_onsets(y, sr, hop_length)
            onset_results['energy_based'] = energy_onsets
            all_onsets.extend(energy_onsets)
            
            # Method 5: Phase deviation
            phase_onsets = self._detect_phase_deviation_onsets(y, sr, hop_length)
            onset_results['phase_deviation'] = phase_onsets
            all_onsets.extend(phase_onsets)
            
            # Combine and filter onsets
            combined_onsets = self._combine_onset_detections(onset_results, sr)
            
            return combined_onsets, onset_results
            
        except Exception as e:
            print(f"⚠️ Audio onset detection failed: {e}")
            return np.array([]), {}
    
    def _complex_domain_onset_strength(self, stft: np.ndarray, sr: int, 
                                     hop_length: int) -> np.ndarray:
        """Complex domain onset strength function"""
        
        # Calculate magnitude and phase
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Phase deviation
        phase_dev = np.diff(phase, axis=1)
        phase_dev = np.concatenate([phase_dev[:, :1], phase_dev], axis=1)
        
        # Magnitude change
        mag_diff = np.diff(magnitude, axis=1)
        mag_diff = np.concatenate([mag_diff[:, :1], mag_diff], axis=1)
        
        # Combine magnitude and phase information
        onset_strength = np.sum(magnitude * np.abs(phase_dev) + np.abs(mag_diff), axis=0)
        
        return onset_strength
    
    def _detect_harmonic_change_onsets(self, y: np.ndarray, sr: int, 
                                     hop_length: int) -> np.ndarray:
        """Detect onsets based on harmonic content changes"""
        
        # Extract harmonic and percussive components
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Chromagram for harmonic analysis
        chroma = librosa.feature.chroma_stft(y=y_harmonic, sr=sr, hop_length=hop_length)
        
        # Calculate chroma change
        chroma_diff = np.diff(chroma, axis=1)
        chroma_change = np.sum(np.abs(chroma_diff), axis=0)
        
        # Smooth the change signal
        chroma_change_smooth = gaussian_filter1d(chroma_change, sigma=1.0)
        
        # Find peaks in harmonic change
        peaks, _ = signal.find_peaks(chroma_change_smooth, 
                                   height=np.mean(chroma_change_smooth) + np.std(chroma_change_smooth),
                                   distance=int(sr / hop_length * 0.1))  # Minimum 0.1s between onsets
        
        # Convert to time
        onset_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        return onset_times
    
    def _detect_energy_onsets(self, y: np.ndarray, sr: int, 
                            hop_length: int) -> np.ndarray:
        """Detect onsets based on energy changes"""
        
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Calculate energy derivative
        energy_diff = np.diff(rms)
        energy_diff = np.concatenate([[0], energy_diff])
        
        # Find positive energy changes (attacks)
        positive_changes = np.where(energy_diff > 0, energy_diff, 0)
        
        # Smooth and find peaks
        smoothed = gaussian_filter1d(positive_changes, sigma=2.0)
        peaks, _ = signal.find_peaks(smoothed, 
                                   height=np.mean(smoothed) + 0.5 * np.std(smoothed),
                                   distance=int(sr / hop_length * 0.15))
        
        # Convert to time
        onset_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        return onset_times
    
    def _detect_phase_deviation_onsets(self, y: np.ndarray, sr: int, 
                                      hop_length: int) -> np.ndarray:
        """Detect onsets based on phase deviation"""
        
        # STFT
        stft = librosa.stft(y, hop_length=hop_length)
        
        # Phase
        phase = np.angle(stft)
        
        # Phase deviation (unwrapped)
        phase_unwrapped = np.unwrap(phase, axis=1)
        phase_dev = np.diff(phase_unwrapped, axis=1)
        
        # Sum absolute phase deviations across frequencies
        phase_onset_strength = np.sum(np.abs(phase_dev), axis=0)
        
        # Smooth
        smoothed = gaussian_filter1d(phase_onset_strength, sigma=1.5)
        
        # Find peaks
        peaks, _ = signal.find_peaks(smoothed,
                                   height=np.mean(smoothed) + np.std(smoothed),
                                   distance=int(sr / hop_length * 0.1))
        
        # Convert to time
        onset_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        return onset_times
    
    def _combine_onset_detections(self, onset_results: Dict[str, np.ndarray], 
                                sr: int) -> np.ndarray:
        """Combine multiple onset detection results using consensus"""
        
        if not onset_results:
            return np.array([])
        
        # Collect all onset times
        all_onsets = []
        for method, onsets in onset_results.items():
            all_onsets.extend(onsets)
        
        if not all_onsets:
            return np.array([])
        
        all_onsets = np.array(sorted(all_onsets))
        
        # Cluster nearby onsets (within 0.05 seconds)
        clustered_onsets = []
        current_cluster = [all_onsets[0]]
        
        for onset in all_onsets[1:]:
            if onset - current_cluster[-1] <= 0.05:
                current_cluster.append(onset)
            else:
                # Take median of current cluster
                clustered_onsets.append(np.median(current_cluster))
                current_cluster = [onset]
        
        # Don't forget the last cluster
        if current_cluster:
            clustered_onsets.append(np.median(current_cluster))
        
        return np.array(clustered_onsets)
    
    def refine_chord_boundaries(self, chord_events: List[Dict], 
                              onset_times: np.ndarray) -> List[Dict]:
        """Refine chord boundaries using detected onsets"""
        
        if not chord_events or len(onset_times) == 0:
            return chord_events
        
        refined_events = []
        
        for i, event in enumerate(chord_events):
            start_time = event['start']
            end_time = event['end']
            
            # Find closest onset to start time
            start_onset_idx = np.argmin(np.abs(onset_times - start_time))
            closest_start_onset = onset_times[start_onset_idx]
            
            # Only adjust if onset is reasonably close (within 0.2 seconds)
            if abs(closest_start_onset - start_time) <= 0.2:
                refined_start = closest_start_onset
            else:
                refined_start = start_time
            
            # For end time, look for next onset after start
            future_onsets = onset_times[onset_times > refined_start]
            
            if len(future_onsets) > 0 and i < len(chord_events) - 1:
                # Find onset closest to original end time
                end_onset_idx = np.argmin(np.abs(future_onsets - end_time))
                closest_end_onset = future_onsets[end_onset_idx]
                
                if abs(closest_end_onset - end_time) <= 0.3:
                    refined_end = closest_end_onset
                else:
                    refined_end = end_time
            else:
                refined_end = end_time
            
            # Create refined event
            refined_event = event.copy()
            refined_event['start'] = refined_start
            refined_event['end'] = refined_end
            refined_event['duration'] = refined_end - refined_start
            refined_event['onset_refined'] = True
            
            refined_events.append(refined_event)
        
        return refined_events
    
    def detect_beat_aligned_chords(self, midi_path: str, audio_path: str, 
                                 beat_times: np.ndarray) -> List[Dict]:
        """Detect chords aligned to beat grid with onset refinement"""
        
        # Get onset detections from audio
        onset_times, onset_methods = self.detect_onsets_from_audio(audio_path)
        
        # Parse MIDI notes
        try:
            from src.chord_detector import parse_midi_notes, identify_chord_from_pitches
            notes, total_duration = parse_midi_notes(midi_path)
        except ImportError:
            print("⚠️ Could not import chord detection functions")
            return []
        
        if not notes:
            return []
        
        chord_events = []
        
        # Create beat-aligned windows with onset refinement
        for i in range(len(beat_times) - 1):
            beat_start = beat_times[i]
            beat_end = beat_times[i + 1]
            
            # Check if there's a strong onset near this beat
            nearby_onsets = onset_times[(onset_times >= beat_start - 0.1) & 
                                      (onset_times <= beat_start + 0.1)]
            
            if len(nearby_onsets) > 0:
                # Use onset-refined start time
                window_start = nearby_onsets[0]
            else:
                window_start = beat_start
            
            # Find notes in this window
            window_notes = []
            for note in notes:
                if note['start'] < beat_end and note['end'] > window_start:
                    window_notes.append(note)
            
            if window_notes:
                # Extract pitches and identify chord
                pitches = [note['pitch'] for note in window_notes]
                unique_pitches = list(set(pitches))
                chord_name = identify_chord_from_pitches(unique_pitches)
                
                # Calculate confidence based on onset strength
                onset_confidence = 1.0
                if len(nearby_onsets) > 0:
                    # Higher confidence if strong onset detected
                    onset_confidence = min(1.0, len(nearby_onsets) * 0.3 + 0.7)
                
                chord_events.append({
                    'start': window_start,
                    'end': beat_end,
                    'chord': chord_name,
                    'duration': beat_end - window_start,
                    'notes': len(window_notes),
                    'unique_pitches': len(unique_pitches),
                    'pitches': unique_pitches,
                    'onset_confidence': onset_confidence,
                    'beat_aligned': True,
                    'onset_methods_detected': len([m for m, onsets in onset_methods.items() 
                                                 if len(onsets) > 0])
                })
        
        return chord_events
    
    def analyze_onset_quality(self, onset_results: Dict[str, np.ndarray]) -> Dict:
        """Analyze the quality and consistency of onset detections"""
        
        if not onset_results:
            return {'quality': 'poor', 'consistency': 0.0, 'method_agreement': 0.0}
        
        # Count detections per method
        method_counts = {method: len(onsets) for method, onsets in onset_results.items()}
        
        # Calculate consistency (how similar are the detection counts)
        counts = list(method_counts.values())
        if len(counts) > 1:
            consistency = 1.0 - (np.std(counts) / np.mean(counts)) if np.mean(counts) > 0 else 0.0
        else:
            consistency = 1.0
        
        # Calculate method agreement (how many methods agree on similar onset times)
        all_onsets = []
        for onsets in onset_results.values():
            all_onsets.extend(onsets)
        
        if len(all_onsets) == 0:
            return {'quality': 'poor', 'consistency': 0.0, 'method_agreement': 0.0}
        
        all_onsets = np.array(sorted(all_onsets))
        
        # Count how many onsets have agreement from multiple methods
        agreement_count = 0
        for onset in all_onsets:
            methods_agreeing = 0
            for method_onsets in onset_results.values():
                if len(method_onsets) > 0 and np.min(np.abs(method_onsets - onset)) <= 0.05:
                    methods_agreeing += 1
            
            if methods_agreeing >= 2:
                agreement_count += 1
        
        method_agreement = agreement_count / len(all_onsets) if len(all_onsets) > 0 else 0.0
        
        # Overall quality assessment
        if consistency > 0.7 and method_agreement > 0.6:
            quality = 'excellent'
        elif consistency > 0.5 and method_agreement > 0.4:
            quality = 'good'
        elif consistency > 0.3 and method_agreement > 0.2:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'quality': quality,
            'consistency': consistency,
            'method_agreement': method_agreement,
            'total_onsets': len(all_onsets),
            'method_counts': method_counts
        }