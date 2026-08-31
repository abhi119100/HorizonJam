import numpy as np
import librosa
from typing import List, Dict, Optional, Tuple
from scipy import signal
from collections import defaultdict

class BeatGridSystem:
    """Professional beat grid system with multi-resolution tracking"""
    
    def __init__(self):
        self.beat_subdivisions = {
            'whole': 1,
            'half': 2, 
            'quarter': 4,
            'eighth': 8,
            'sixteenth': 16
        }
        
        self.time_signatures = {
            '4/4': {'beats_per_measure': 4, 'beat_unit': 4},
            '3/4': {'beats_per_measure': 3, 'beat_unit': 4},
            '2/4': {'beats_per_measure': 2, 'beat_unit': 4},
            '6/8': {'beats_per_measure': 6, 'beat_unit': 8},
            '12/8': {'beats_per_measure': 12, 'beat_unit': 8}
        }
    
    def detect_advanced_beats(self, audio_path: str) -> Dict:
        """Advanced beat detection with multiple methods and confidence scoring"""
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            beat_results = {}
            
            # Method 1: Standard beat tracking
            tempo, beats_standard = librosa.beat.beat_track(y=y, sr=sr, units='time')
            beat_results['standard'] = {
                'tempo': tempo,
                'beats': beats_standard,
                'method': 'librosa_beat_track'
            }
            
            # Method 2: Dynamic programming beat tracking
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            tempo_dp, beats_dp = librosa.beat.beat_track(
                onset_envelope=onset_envelope, sr=sr, units='time',
                trim=False, start_bpm=tempo
            )
            beat_results['dynamic_programming'] = {
                'tempo': tempo_dp,
                'beats': beats_dp,
                'method': 'dynamic_programming'
            }
            
            # Method 3: Onset-based beat estimation
            onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
            if len(onsets) > 1:
                onset_intervals = np.diff(onsets)
                # Filter out very short intervals (likely not beats)
                valid_intervals = onset_intervals[onset_intervals > 0.2]
                if len(valid_intervals) > 0:
                    avg_interval = np.median(valid_intervals)
                    onset_tempo = 60.0 / avg_interval
                    # Generate beat grid from onsets
                    onset_beats = np.arange(onsets[0], onsets[-1], avg_interval)
                else:
                    onset_tempo = tempo
                    onset_beats = beats_standard
            else:
                onset_tempo = tempo
                onset_beats = beats_standard
            
            beat_results['onset_based'] = {
                'tempo': onset_tempo,
                'beats': onset_beats,
                'method': 'onset_estimation'
            }
            
            # Method 4: Autocorrelation-based tempo
            autocorr_tempo = self._autocorrelation_tempo(y, sr)
            # Use standard beats but with autocorr tempo
            if autocorr_tempo > 0:
                beat_interval = 60.0 / autocorr_tempo
                autocorr_beats = np.arange(0, len(y)/sr, beat_interval)
            else:
                autocorr_beats = beats_standard
                autocorr_tempo = tempo
            
            beat_results['autocorrelation'] = {
                'tempo': autocorr_tempo,
                'beats': autocorr_beats,
                'method': 'autocorrelation'
            }
            
            # Combine results and select best
            best_result = self._select_best_beat_detection(beat_results, y, sr)
            
            return {
                'best_result': best_result,
                'all_methods': beat_results,
                'confidence': self._calculate_beat_confidence(best_result, y, sr)
            }
            
        except Exception as e:
            print(f"⚠️ Advanced beat detection failed: {e}")
            return {
                'best_result': {'tempo': 120.0, 'beats': np.array([]), 'method': 'fallback'},
                'all_methods': {},
                'confidence': 0.0
            }
    
    def _autocorrelation_tempo(self, y: np.ndarray, sr: int) -> float:
        """Estimate tempo using autocorrelation"""
        
        try:
            # Calculate onset strength
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Autocorrelation
            autocorr = np.correlate(onset_env, onset_env, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks in autocorrelation
            # Convert lag to BPM range (60-200 BPM)
            hop_length = 512
            min_lag = int(60 * sr / (200 * hop_length))  # 200 BPM
            max_lag = int(60 * sr / (60 * hop_length))   # 60 BPM
            
            if max_lag < len(autocorr):
                autocorr_segment = autocorr[min_lag:max_lag]
                peak_lag = np.argmax(autocorr_segment) + min_lag
                
                # Convert lag to tempo
                tempo = 60 * sr / (peak_lag * hop_length)
                return tempo
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _select_best_beat_detection(self, beat_results: Dict, y: np.ndarray, sr: int) -> Dict:
        """Select the best beat detection result based on multiple criteria"""
        
        if not beat_results:
            return {'tempo': 120.0, 'beats': np.array([]), 'method': 'fallback'}
        
        scores = {}
        
        for method, result in beat_results.items():
            score = 0.0
            tempo = result['tempo']
            beats = result['beats']
            
            # Score 1: Tempo reasonableness (60-200 BPM gets full score)
            if 60 <= tempo <= 200:
                tempo_score = 1.0
            elif 40 <= tempo <= 250:
                tempo_score = 0.7
            else:
                tempo_score = 0.3
            
            score += tempo_score * 0.3
            
            # Score 2: Beat consistency
            if len(beats) > 1:
                beat_intervals = np.diff(beats)
                consistency = 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals)) if np.mean(beat_intervals) > 0 else 0.0
                consistency = max(0.0, consistency)
            else:
                consistency = 0.0
            
            score += consistency * 0.4
            
            # Score 3: Number of beats detected (more is generally better)
            beat_count_score = min(1.0, len(beats) / 20.0)  # Normalize to 20 beats
            score += beat_count_score * 0.2
            
            # Score 4: Method reliability (some methods are more reliable)
            method_weights = {
                'standard': 1.0,
                'dynamic_programming': 0.9,
                'onset_based': 0.8,
                'autocorrelation': 0.7
            }
            method_score = method_weights.get(method, 0.5)
            score += method_score * 0.1
            
            scores[method] = score
        
        # Select best method
        best_method = max(scores, key=scores.get)
        best_result = beat_results[best_method].copy()
        best_result['selection_score'] = scores[best_method]
        
        return best_result
    
    def _calculate_beat_confidence(self, beat_result: Dict, y: np.ndarray, sr: int) -> float:
        """Calculate confidence in beat detection"""
        
        try:
            beats = beat_result['beats']
            tempo = beat_result['tempo']
            
            if len(beats) < 2:
                return 0.0
            
            # Confidence based on beat interval consistency
            intervals = np.diff(beats)
            expected_interval = 60.0 / tempo
            
            # Calculate how close intervals are to expected
            interval_errors = np.abs(intervals - expected_interval) / expected_interval
            consistency_confidence = np.mean(1.0 - np.clip(interval_errors, 0, 1))
            
            # Confidence based on onset alignment
            onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
            if len(onsets) > 0:
                # Find how many beats align with onsets
                aligned_count = 0
                for beat in beats:
                    if len(onsets) > 0 and np.min(np.abs(onsets - beat)) <= 0.1:
                        aligned_count += 1
                
                onset_confidence = aligned_count / len(beats)
            else:
                onset_confidence = 0.5  # Neutral if no onsets
            
            # Combined confidence
            overall_confidence = (consistency_confidence * 0.6 + onset_confidence * 0.4)
            
            return np.clip(overall_confidence, 0.0, 1.0)
            
        except Exception:
            return 0.0
    
    def create_multi_resolution_grid(self, beats: np.ndarray, tempo: float, 
                                   total_duration: float) -> Dict:
        """Create multi-resolution beat grid for different subdivision levels"""
        
        if len(beats) == 0:
            # Fallback grid
            beat_interval = 60.0 / tempo
            beats = np.arange(0, total_duration, beat_interval)
        
        grids = {}
        
        # Define beat_interval once for all subdivisions
        beat_interval = 60.0 / tempo
        
        for subdivision_name, subdivision_factor in self.beat_subdivisions.items():
            if subdivision_factor == 1:
                # Whole note grid (every 4 beats in 4/4)
                grid_interval = (60.0 / tempo) * 4
                grid_times = np.arange(0, total_duration, grid_interval)
            else:
                # Subdivided grids
                subdivision_interval = beat_interval / (subdivision_factor / 4)
                grid_times = np.arange(0, total_duration, subdivision_interval)
            
            grids[subdivision_name] = {
                'times': grid_times,
                'interval': grid_times[1] - grid_times[0] if len(grid_times) > 1 else beat_interval,
                'subdivision_factor': subdivision_factor,
                'count': len(grid_times)
            }
        
        return grids
    
    def detect_time_signature(self, beats: np.ndarray, tempo: float) -> Dict:
        """Detect the most likely time signature"""
        
        if len(beats) < 8:  # Need at least 2 measures to detect
            return {'time_signature': '4/4', 'confidence': 0.5, 'reasoning': 'Insufficient data'}
        
        beat_interval = 60.0 / tempo
        
        # Test different time signatures
        signature_scores = {}
        
        for sig_name, sig_info in self.time_signatures.items():
            beats_per_measure = sig_info['beats_per_measure']
            measure_duration = beat_interval * beats_per_measure
            
            # Create expected measure boundaries
            expected_measures = np.arange(0, beats[-1], measure_duration)
            
            # Score based on how well beats align with measure boundaries
            alignment_score = 0.0
            for measure_start in expected_measures:
                # Find closest beat to this measure boundary
                if len(beats) > 0:
                    closest_beat_distance = np.min(np.abs(beats - measure_start))
                    # Score inversely proportional to distance
                    alignment_score += max(0, 1.0 - (closest_beat_distance / (beat_interval * 0.5)))
            
            # Normalize by number of measures
            if len(expected_measures) > 0:
                alignment_score /= len(expected_measures)
            
            signature_scores[sig_name] = alignment_score
        
        # Find best time signature
        best_signature = max(signature_scores, key=signature_scores.get)
        confidence = signature_scores[best_signature]
        
        # Generate reasoning
        if confidence > 0.8:
            reasoning = f"Strong alignment with {best_signature} pattern"
        elif confidence > 0.6:
            reasoning = f"Good alignment with {best_signature} pattern"
        elif confidence > 0.4:
            reasoning = f"Moderate alignment with {best_signature} pattern"
        else:
            reasoning = "Weak pattern detection, defaulting to 4/4"
            best_signature = '4/4'
            confidence = 0.5
        
        return {
            'time_signature': best_signature,
            'confidence': confidence,
            'reasoning': reasoning,
            'all_scores': signature_scores
        }
    
    def detect_beat_strength(self, beats: np.ndarray, audio_path: str) -> np.ndarray:
        """Detect the strength/emphasis of each beat"""
        
        try:
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate onset strength
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onset_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr)
            
            beat_strengths = []
            
            for beat_time in beats:
                # Find onset strength at this beat time
                closest_idx = np.argmin(np.abs(onset_times - beat_time))
                
                # Average strength in a small window around the beat
                window_size = 3  # frames
                start_idx = max(0, closest_idx - window_size)
                end_idx = min(len(onset_env), closest_idx + window_size + 1)
                
                strength = np.mean(onset_env[start_idx:end_idx])
                beat_strengths.append(strength)
            
            # Normalize strengths
            beat_strengths = np.array(beat_strengths)
            if np.max(beat_strengths) > 0:
                beat_strengths = beat_strengths / np.max(beat_strengths)
            
            return beat_strengths
            
        except Exception as e:
            print(f"⚠️ Beat strength detection failed: {e}")
            # Return uniform strengths
            return np.ones(len(beats))
    
    def adaptive_grid_sizing(self, chord_events: List[Dict], beats: np.ndarray, 
                           tempo: float) -> Dict:
        """Determine optimal grid sizing based on musical content"""
        
        if not chord_events or len(beats) == 0:
            return {
                'recommended_subdivision': 'quarter',
                'grid_size': 'medium',
                'reasoning': 'Default sizing due to insufficient data'
            }
        
        # Analyze chord change frequency
        chord_durations = [event['duration'] for event in chord_events]
        avg_chord_duration = np.mean(chord_durations)
        
        beat_interval = 60.0 / tempo
        chords_per_beat = beat_interval / avg_chord_duration
        
        # Determine appropriate subdivision
        if chords_per_beat >= 2:
            # Fast chord changes - need fine grid
            recommended_subdivision = 'eighth'
            grid_size = 'fine'
            reasoning = f"Fast chord changes ({chords_per_beat:.1f} chords/beat) require fine grid"
        elif chords_per_beat >= 1:
            # Medium chord changes
            recommended_subdivision = 'quarter'
            grid_size = 'medium'
            reasoning = f"Standard chord changes ({chords_per_beat:.1f} chords/beat) use quarter note grid"
        elif chords_per_beat >= 0.5:
            # Slow chord changes
            recommended_subdivision = 'half'
            grid_size = 'coarse'
            reasoning = f"Slow chord changes ({chords_per_beat:.1f} chords/beat) use half note grid"
        else:
            # Very slow chord changes
            recommended_subdivision = 'whole'
            grid_size = 'very_coarse'
            reasoning = f"Very slow chord changes ({chords_per_beat:.1f} chords/beat) use whole note grid"
        
        return {
            'recommended_subdivision': recommended_subdivision,
            'grid_size': grid_size,
            'reasoning': reasoning,
            'chords_per_beat': chords_per_beat,
            'avg_chord_duration': avg_chord_duration
        }
    
    def generate_professional_beat_grid(self, audio_path: str, 
                                      total_duration: float) -> Dict:
        """Generate a comprehensive professional beat grid system with enhanced tempo detection"""
        
        # Use enhanced BPM detection from chord_detector
        enhanced_tempo = None
        try:
            from src.chord_detector import detect_bpm_from_audio
            enhanced_tempo = detect_bpm_from_audio(audio_path)
            if enhanced_tempo is not None:
                print(f"[BEAT_GRID] Using enhanced tempo detection: {enhanced_tempo:.1f} BPM")
            else:
                print("[BEAT_GRID] Enhanced tempo detection returned None")
        except (ImportError, Exception) as e:
            print(f"[BEAT_GRID] Enhanced tempo detection failed: {e}, using standard methods")
        
        # Advanced beat detection
        beat_analysis = self.detect_advanced_beats(audio_path)
        best_result = beat_analysis['best_result']
        
        beats = best_result['beats']
        tempo = enhanced_tempo if enhanced_tempo else best_result['tempo']
        
        # If we used enhanced tempo, regenerate beats with the corrected tempo
        if enhanced_tempo and abs(enhanced_tempo - best_result['tempo']) > 5:
            print(f"[BEAT_GRID] Regenerating beats with enhanced tempo: {best_result['tempo']:.1f} -> {enhanced_tempo:.1f} BPM")
            try:
                import librosa
                y, sr = librosa.load(audio_path, sr=None)
                # Regenerate beats with the enhanced tempo
                _, new_beats = librosa.beat.beat_track(y=y, sr=sr, units='time', start_bpm=enhanced_tempo)
                beats = new_beats
                best_result['tempo'] = enhanced_tempo
                best_result['beats'] = beats
            except Exception as e:
                print(f"[BEAT_GRID] Failed to regenerate beats: {e}")
        
        # Time signature detection
        time_sig_analysis = self.detect_time_signature(beats, tempo)
        
        # Multi-resolution grids
        multi_res_grids = self.create_multi_resolution_grid(beats, tempo, total_duration)
        
        # Beat strength analysis
        beat_strengths = self.detect_beat_strength(beats, audio_path)
        
        return {
            'primary_beats': beats,
            'tempo': tempo,
            'confidence': beat_analysis['confidence'],
            'time_signature': time_sig_analysis,
            'multi_resolution_grids': multi_res_grids,
            'beat_strengths': beat_strengths,
            'detection_method': best_result['method'],
            'all_detection_methods': beat_analysis['all_methods']
        }