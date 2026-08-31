import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict, Counter
import math

class MusicalIntelligenceEngine:
    """Professional-level musical intelligence for chord progression analysis"""
    
    def __init__(self):
        self.initialize_music_theory_knowledge()
        self.initialize_genre_models()
        self.initialize_harmonic_rhythm_patterns()
    
    def initialize_music_theory_knowledge(self):
        """Initialize comprehensive music theory knowledge base"""
        
        # Circle of fifths for key relationships
        self.circle_of_fifths = {
            'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6,
            'Db': 7, 'Ab': 8, 'Eb': 9, 'Bb': 10, 'F': 11
        }
        
        # Roman numeral analysis for functional harmony
        self.major_scale_functions = {
            1: {'roman': 'I', 'function': 'tonic', 'stability': 1.0},
            2: {'roman': 'ii', 'function': 'subdominant', 'stability': 0.3},
            3: {'roman': 'iii', 'function': 'tonic', 'stability': 0.4},
            4: {'roman': 'IV', 'function': 'subdominant', 'stability': 0.7},
            5: {'roman': 'V', 'function': 'dominant', 'stability': 0.8},
            6: {'roman': 'vi', 'function': 'tonic', 'stability': 0.6},
            7: {'roman': 'vii°', 'function': 'dominant', 'stability': 0.2}
        }
        
        # Common chord progressions with weights
        self.common_progressions = {
            # Pop/Rock progressions
            ('I', 'V', 'vi', 'IV'): {'weight': 1.0, 'genre': 'pop', 'name': 'vi-IV-I-V'},
            ('vi', 'IV', 'I', 'V'): {'weight': 0.95, 'genre': 'pop', 'name': 'vi-IV-I-V'},
            ('I', 'vi', 'IV', 'V'): {'weight': 0.9, 'genre': 'pop', 'name': '50s progression'},
            ('I', 'IV', 'V', 'I'): {'weight': 0.85, 'genre': 'rock', 'name': 'I-IV-V'},
            
            # Jazz progressions
            ('ii', 'V', 'I'): {'weight': 1.0, 'genre': 'jazz', 'name': 'ii-V-I'},
            ('I', 'vi', 'ii', 'V'): {'weight': 0.9, 'genre': 'jazz', 'name': 'circle progression'},
            ('iii', 'vi', 'ii', 'V'): {'weight': 0.8, 'genre': 'jazz', 'name': 'extended circle'},
            
            # Blues progressions
            ('I', 'I', 'I', 'I', 'IV', 'IV', 'I', 'I', 'V', 'IV', 'I', 'V'): {
                'weight': 1.0, 'genre': 'blues', 'name': '12-bar blues'
            }
        }
        
        # Chord substitution rules
        self.substitution_rules = {
            'I': ['iii', 'vi'],  # Tonic substitutions
            'ii': ['IV'],        # Subdominant substitutions
            'V': ['vii°', 'iii'], # Dominant substitutions
            'IV': ['ii', 'vi'],   # Subdominant substitutions
        }
    
    def initialize_genre_models(self):
        """Initialize genre-specific harmonic models"""
        
        self.genre_models = {
            'pop': {
                'common_chords': ['I', 'V', 'vi', 'IV', 'ii'],
                'harmonic_rhythm': [1, 2, 4],  # beats per chord
                'chord_weights': {'I': 0.25, 'V': 0.2, 'vi': 0.2, 'IV': 0.15, 'ii': 0.1},
                'progression_patterns': ['verse', 'chorus', 'bridge'],
                'typical_bpm_range': (80, 140)
            },
            'rock': {
                'common_chords': ['I', 'IV', 'V', 'vi', 'bVII'],
                'harmonic_rhythm': [2, 4, 8],
                'chord_weights': {'I': 0.3, 'IV': 0.25, 'V': 0.25, 'vi': 0.1, 'bVII': 0.1},
                'progression_patterns': ['power_chord', 'verse', 'chorus'],
                'typical_bpm_range': (100, 180)
            },
            'jazz': {
                'common_chords': ['I', 'ii', 'V', 'vi', 'iii', 'IV', 'vii°'],
                'harmonic_rhythm': [0.5, 1, 2],  # Fast harmonic rhythm
                'chord_weights': {'I': 0.2, 'ii': 0.15, 'V': 0.2, 'vi': 0.1, 'iii': 0.1, 'IV': 0.15, 'vii°': 0.1},
                'progression_patterns': ['ii-V-I', 'turnaround', 'cycle'],
                'typical_bpm_range': (60, 200)
            },
            'blues': {
                'common_chords': ['I', 'IV', 'V', 'I7', 'IV7', 'V7'],
                'harmonic_rhythm': [4, 8, 12],  # 12-bar structure
                'chord_weights': {'I': 0.4, 'IV': 0.3, 'V': 0.2, 'I7': 0.05, 'IV7': 0.03, 'V7': 0.02},
                'progression_patterns': ['12-bar', '8-bar', '16-bar'],
                'typical_bpm_range': (60, 140)
            }
        }
    
    def initialize_harmonic_rhythm_patterns(self):
        """Initialize harmonic rhythm analysis patterns"""
        
        self.harmonic_rhythm_patterns = {
            'very_fast': {'beats_per_chord': 0.5, 'description': 'Bebop/fast jazz'},
            'fast': {'beats_per_chord': 1, 'description': 'Medium jazz/complex pop'},
            'medium': {'beats_per_chord': 2, 'description': 'Standard pop/rock'},
            'slow': {'beats_per_chord': 4, 'description': 'Ballad/slow rock'},
            'very_slow': {'beats_per_chord': 8, 'description': 'Ambient/drone'}
        }
    
    def analyze_harmonic_rhythm(self, chord_events: List[Dict], bpm: float) -> Dict:
        """Analyze the harmonic rhythm of the chord progression"""
        
        if not chord_events or not bpm:
            return {'pattern': 'unknown', 'beats_per_chord': 4, 'confidence': 0.0}
        
        # Calculate beats per chord for each event
        beats_per_chord_list = []
        beat_duration = 60.0 / bpm
        
        for event in chord_events:
            duration = event['duration']
            beats = duration / beat_duration
            beats_per_chord_list.append(beats)
        
        # Find the most common harmonic rhythm
        avg_beats_per_chord = np.mean(beats_per_chord_list)
        
        # Classify harmonic rhythm pattern
        pattern = 'medium'  # default
        min_diff = float('inf')
        
        for pattern_name, pattern_info in self.harmonic_rhythm_patterns.items():
            diff = abs(avg_beats_per_chord - pattern_info['beats_per_chord'])
            if diff < min_diff:
                min_diff = diff
                pattern = pattern_name
        
        # Calculate confidence based on consistency
        std_dev = np.std(beats_per_chord_list)
        confidence = max(0.0, 1.0 - (std_dev / avg_beats_per_chord))
        
        return {
            'pattern': pattern,
            'beats_per_chord': avg_beats_per_chord,
            'confidence': confidence,
            'description': self.harmonic_rhythm_patterns[pattern]['description'],
            'consistency': 1.0 - (std_dev / avg_beats_per_chord) if avg_beats_per_chord > 0 else 0.0
        }
    
    def detect_genre_from_progression(self, chord_events: List[Dict], bpm: float) -> Dict:
        """Detect the most likely genre based on chord progression and harmonic rhythm"""
        
        if not chord_events:
            return {'genre': 'unknown', 'confidence': 0.0, 'reasoning': []}
        
        chord_names = [event['chord'] for event in chord_events]
        harmonic_rhythm = self.analyze_harmonic_rhythm(chord_events, bpm)
        
        genre_scores = {}
        reasoning = []
        
        for genre, model in self.genre_models.items():
            score = 0.0
            genre_reasoning = []
            
            # Score based on chord usage
            chord_score = 0
            for chord in chord_names:
                # Simplified chord matching (would need key analysis for full roman numeral)
                if any(common in chord for common in model['common_chords']):
                    chord_score += 1
            
            chord_ratio = chord_score / len(chord_names) if chord_names else 0
            score += chord_ratio * 0.4
            genre_reasoning.append(f"Chord match: {chord_ratio:.2f}")
            
            # Score based on BPM range
            bpm_min, bpm_max = model['typical_bpm_range']
            if bpm_min <= bpm <= bpm_max:
                bpm_score = 1.0
            else:
                # Penalty for being outside range
                if bpm < bpm_min:
                    bpm_score = max(0, 1.0 - (bpm_min - bpm) / bpm_min)
                else:
                    bpm_score = max(0, 1.0 - (bpm - bpm_max) / bpm_max)
            
            score += bpm_score * 0.3
            genre_reasoning.append(f"BPM fit: {bpm_score:.2f}")
            
            # Score based on harmonic rhythm
            rhythm_score = 0
            if harmonic_rhythm['beats_per_chord'] in model['harmonic_rhythm']:
                rhythm_score = 1.0
            else:
                # Find closest match
                closest_rhythm = min(model['harmonic_rhythm'], 
                                   key=lambda x: abs(x - harmonic_rhythm['beats_per_chord']))
                diff = abs(closest_rhythm - harmonic_rhythm['beats_per_chord'])
                rhythm_score = max(0, 1.0 - diff / closest_rhythm)
            
            score += rhythm_score * 0.3
            genre_reasoning.append(f"Rhythm fit: {rhythm_score:.2f}")
            
            genre_scores[genre] = score
            reasoning.append(f"{genre}: {score:.2f} ({', '.join(genre_reasoning)})")
        
        # Find best genre
        best_genre = max(genre_scores, key=genre_scores.get) if genre_scores else 'unknown'
        confidence = genre_scores.get(best_genre, 0.0)
        
        return {
            'genre': best_genre,
            'confidence': confidence,
            'all_scores': genre_scores,
            'reasoning': reasoning,
            'harmonic_rhythm': harmonic_rhythm
        }
    
    def analyze_chord_functions(self, chord_events: List[Dict], detected_key: str) -> List[Dict]:
        """Analyze the harmonic function of each chord in the progression"""
        
        if not chord_events or detected_key == 'Unknown':
            return chord_events
        
        # Parse key (e.g., "C major" -> "C", "major")
        key_parts = detected_key.split()
        if len(key_parts) != 2:
            return chord_events
        
        tonic = key_parts[0]
        mode = key_parts[1]
        
        # Create chromatic scale starting from tonic
        chromatic = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Handle enharmonic equivalents
        enharmonic_map = {
            'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'
        }
        
        tonic_normalized = enharmonic_map.get(tonic, tonic)
        
        if tonic_normalized not in chromatic:
            return chord_events
        
        tonic_index = chromatic.index(tonic_normalized)
        
        # Analyze each chord
        analyzed_events = []
        for event in chord_events:
            chord_name = event['chord']
            
            # Extract root note from chord
            chord_root = chord_name.split('m')[0].split('7')[0].split('sus')[0]
            chord_root = enharmonic_map.get(chord_root, chord_root)
            
            if chord_root in chromatic:
                chord_index = chromatic.index(chord_root)
                scale_degree = (chord_index - tonic_index) % 12
                
                # Map to scale degree (1-7)
                scale_degree_map = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
                
                if scale_degree in scale_degree_map:
                    degree = scale_degree_map[scale_degree]
                    function_info = self.major_scale_functions.get(degree, {
                        'roman': '?', 'function': 'unknown', 'stability': 0.5
                    })
                    
                    analyzed_event = event.copy()
                    analyzed_event.update({
                        'scale_degree': degree,
                        'roman_numeral': function_info['roman'],
                        'harmonic_function': function_info['function'],
                        'stability': function_info['stability']
                    })
                    analyzed_events.append(analyzed_event)
                else:
                    # Non-diatonic chord
                    analyzed_event = event.copy()
                    analyzed_event.update({
                        'scale_degree': None,
                        'roman_numeral': 'N',
                        'harmonic_function': 'chromatic',
                        'stability': 0.3
                    })
                    analyzed_events.append(analyzed_event)
            else:
                analyzed_events.append(event)
        
        return analyzed_events
    
    def detect_progression_patterns(self, analyzed_events: List[Dict]) -> Dict:
        """Detect common chord progression patterns"""
        
        if not analyzed_events:
            return {'patterns': [], 'confidence': 0.0}
        
        roman_sequence = [event.get('roman_numeral', '?') for event in analyzed_events]
        
        detected_patterns = []
        
        # Check for common progressions
        for progression, info in self.common_progressions.items():
            # Look for this progression in the sequence
            prog_len = len(progression)
            
            for i in range(len(roman_sequence) - prog_len + 1):
                subsequence = tuple(roman_sequence[i:i + prog_len])
                
                if subsequence == progression:
                    detected_patterns.append({
                        'pattern': progression,
                        'name': info['name'],
                        'genre': info['genre'],
                        'weight': info['weight'],
                        'start_index': i,
                        'end_index': i + prog_len - 1
                    })
        
        # Calculate overall confidence
        total_weight = sum(pattern['weight'] for pattern in detected_patterns)
        confidence = min(1.0, total_weight / len(roman_sequence)) if roman_sequence else 0.0
        
        return {
            'patterns': detected_patterns,
            'confidence': confidence,
            'roman_sequence': roman_sequence
        }
    
    def enhance_chord_detection(self, chord_events: List[Dict], detected_key: str, 
                              bpm: float) -> Dict:
        """Main function to enhance chord detection with musical intelligence"""
        
        # Analyze harmonic functions
        analyzed_events = self.analyze_chord_functions(chord_events, detected_key)
        
        # Detect genre
        genre_analysis = self.detect_genre_from_progression(chord_events, bpm)
        
        # Detect progression patterns
        pattern_analysis = self.detect_progression_patterns(analyzed_events)
        
        # Analyze harmonic rhythm
        rhythm_analysis = self.analyze_harmonic_rhythm(chord_events, bpm)
        
        return {
            'enhanced_events': analyzed_events,
            'genre_analysis': genre_analysis,
            'pattern_analysis': pattern_analysis,
            'rhythm_analysis': rhythm_analysis,
            'musical_insights': self._generate_musical_insights(
                analyzed_events, genre_analysis, pattern_analysis, rhythm_analysis
            )
        }
    
    def _generate_musical_insights(self, events: List[Dict], genre: Dict, 
                                 patterns: Dict, rhythm: Dict) -> List[str]:
        """Generate human-readable musical insights"""
        
        insights = []
        
        # Genre insights
        if genre['confidence'] > 0.6:
            insights.append(f"Strong {genre['genre']} characteristics detected (confidence: {genre['confidence']:.1%})")
        
        # Harmonic rhythm insights
        if rhythm['confidence'] > 0.7:
            insights.append(f"Consistent {rhythm['pattern']} harmonic rhythm ({rhythm['description']})")
        
        # Pattern insights
        if patterns['patterns']:
            pattern_names = [p['name'] for p in patterns['patterns']]
            insights.append(f"Common progressions found: {', '.join(set(pattern_names))}")
        
        # Functional harmony insights
        functions = [event.get('harmonic_function', 'unknown') for event in events]
        function_counts = Counter(functions)
        
        if 'tonic' in function_counts and 'dominant' in function_counts:
            insights.append("Strong tonic-dominant relationship established")
        
        # Stability analysis
        stabilities = [event.get('stability', 0.5) for event in events]
        avg_stability = np.mean(stabilities)
        
        if avg_stability > 0.7:
            insights.append("Harmonically stable progression")
        elif avg_stability < 0.4:
            insights.append("Harmonically unstable/chromatic progression")
        
        return insights