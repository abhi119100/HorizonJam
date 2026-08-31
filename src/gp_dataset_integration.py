#!/usr/bin/env python3
"""
Guitar Pro Dataset Integration System
Leverages all_parsed_gp_data.json for enhanced chord and scale detection
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter

class GPDatasetIntegration:
    """Integrates Guitar Pro dataset for enhanced chord and scale detection"""
    
    def __init__(self, gp_data_path: str = "training_data/all_parsed_gp_data.json"):
        self.gp_data_path = gp_data_path
        self.gp_data = self.load_gp_data()
        self.string_tunings = self.get_string_tunings()  # Initialize tunings first
        self.chord_patterns = self.build_chord_pattern_database()
        self.scale_patterns = self.build_scale_pattern_database()
        
    def load_gp_data(self) -> List[Dict]:
        """Load the parsed Guitar Pro data"""
        try:
            with open(self.gp_data_path, 'r') as f:
                data = json.load(f)
            # Loaded Guitar Pro songs from dataset
            return data
        except Exception as e:
            print(f"❌ Error loading GP data: {e}")
            return []
    
    def get_string_tunings(self) -> Dict[str, List[int]]:
        """Get common string tunings for different instruments"""
        return {
            'guitar_standard': [40, 45, 50, 55, 59, 64],  # E A D G B E (MIDI notes)
            'guitar_drop_d': [38, 45, 50, 55, 59, 64],    # D A D G B E
            'bass_standard': [28, 33, 38, 43],             # E A D G (bass)
            'guitar_7string': [35, 40, 45, 50, 55, 59, 64], # B E A D G B E
        }
    
    def fret_to_midi_pitch(self, string_num: int, fret: int, tuning: List[int]) -> int:
        """Convert string/fret position to MIDI pitch"""
        if 1 <= string_num <= len(tuning):
            # GP uses 1-based string numbering, convert to 0-based
            string_index = string_num - 1
            return tuning[string_index] + fret
        return 60  # Default to middle C if invalid
    
    def extract_chord_patterns_from_gp(self) -> Dict[str, List[Dict]]:
        """Extract chord patterns from Guitar Pro data with string/fret context"""
        
        chord_patterns = defaultdict(list)
        
        for song_idx, song in enumerate(self.gp_data):
            title = song.get('title', f'Song_{song_idx}')
            tempo = song.get('tempo', 120)
            
            for track in song.get('tracks', []):
                if track.get('is_percussion', False):
                    continue
                
                track_name = track.get('name', 'Unknown')
                instrument = track.get('instrument', 0)
                
                # Determine tuning based on instrument
                tuning = self.string_tunings['guitar_standard']  # Default
                if 'bass' in track_name.lower() or instrument in [32, 33, 34, 35]:
                    tuning = self.string_tunings['bass_standard']
                
                for measure_idx, measure in enumerate(track.get('measures', [])):
                    for voice in measure.get('voices', []):
                        for beat in voice.get('beats', []):
                            notes = beat.get('notes', [])
                            
                            if len(notes) >= 3:  # Potential chord
                                # Extract fret pattern
                                fret_pattern = []
                                midi_pitches = []
                                
                                for note in notes:
                                    string_num = note.get('string', 1)
                                    fret = note.get('value', 0)
                                    
                                    fret_pattern.append((string_num, fret))
                                    midi_pitch = self.fret_to_midi_pitch(string_num, fret, tuning)
                                    midi_pitches.append(midi_pitch)
                                
                                # Analyze chord
                                chord_name = self.analyze_chord_from_pattern(fret_pattern, midi_pitches)
                                
                                if chord_name:
                                    pattern_data = {
                                        'chord': chord_name,
                                        'fret_pattern': fret_pattern,
                                        'midi_pitches': midi_pitches,
                                        'pitch_classes': [p % 12 for p in midi_pitches],
                                        'source_song': title,
                                        'tempo': tempo,
                                        'instrument': track_name,
                                        'measure': measure_idx,
                                        'tuning_type': self.detect_tuning_type(tuning)
                                    }
                                    
                                    chord_patterns[chord_name].append(pattern_data)
        
        return dict(chord_patterns)
    
    def analyze_chord_from_pattern(self, fret_pattern: List[Tuple], midi_pitches: List[int]) -> Optional[str]:
        """Analyze chord from fret pattern and MIDI pitches"""
        
        if len(midi_pitches) < 3:
            return None
        
        # Convert to pitch classes
        pitch_classes = sorted(list(set([p % 12 for p in midi_pitches])))
        
        # Enhanced chord recognition with GP context
        chord_intervals = {
            # Major chords
            (0, 4, 7): 'maj',
            (0, 3, 7): 'min',
            (0, 4, 7, 10): '7',
            (0, 4, 7, 11): 'maj7',
            (0, 3, 7, 10): 'm7',
            (0, 2, 7): 'sus2',
            (0, 5, 7): 'sus4',
            (0, 3, 6): 'dim',
            (0, 4, 8): 'aug',
            (0, 4, 7, 9): '6',
            (0, 3, 7, 9): 'm6',
            (0, 2, 4, 7): 'add9',
            (0, 4, 7, 10, 14): '9',
            (0, 3, 7, 10, 14): 'm9',
            # Extended chords
            (0, 4, 7, 11, 14): 'maj9',
            (0, 4, 7, 10, 14, 17): '11',
            (0, 4, 7, 10, 14, 21): '13',
        }
        
        # Find root note and chord type
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for root in range(12):
            for intervals, chord_type in chord_intervals.items():
                expected_pitches = [(root + interval) % 12 for interval in intervals]
                
                # Check if all expected pitches are present
                if all(pitch in pitch_classes for pitch in expected_pitches):
                    # Allow some extra notes for extended chords
                    extra_notes = [p for p in pitch_classes if p not in expected_pitches]
                    
                    if len(extra_notes) <= 2:  # Reasonable tolerance
                        chord_name = note_names[root]
                        if chord_type != 'maj':
                            chord_name += chord_type
                        return chord_name
        
        return None
    
    def detect_tuning_type(self, tuning: List[int]) -> str:
        """Detect the tuning type from MIDI notes"""
        for tuning_name, tuning_notes in self.string_tunings.items():
            if tuning == tuning_notes:
                return tuning_name
        return 'custom'
    
    def build_chord_pattern_database(self) -> Dict[str, Dict]:
        """Build comprehensive chord pattern database from GP data"""
        
        # Building chord pattern database from Guitar Pro data
        
        chord_patterns = self.extract_chord_patterns_from_gp()
        
        # Analyze patterns for each chord
        chord_database = {}
        
        for chord_name, patterns in chord_patterns.items():
            if len(patterns) >= 2:  # Need multiple examples for reliability
                
                # Find most common fret patterns
                fret_pattern_counts = Counter()
                pitch_class_patterns = Counter()
                
                for pattern in patterns:
                    fret_tuple = tuple(sorted(pattern['fret_pattern']))
                    pitch_tuple = tuple(sorted(pattern['pitch_classes']))
                    
                    fret_pattern_counts[fret_tuple] += 1
                    pitch_class_patterns[pitch_tuple] += 1
                
                # Get most reliable patterns
                most_common_fret = fret_pattern_counts.most_common(3)
                most_common_pitch = pitch_class_patterns.most_common(1)[0]
                
                chord_database[chord_name] = {
                    'total_occurrences': len(patterns),
                    'common_fret_patterns': most_common_fret,
                    'canonical_pitch_classes': most_common_pitch[0],
                    'confidence_score': min(len(patterns) / 10.0, 1.0),  # Max confidence at 10+ examples
                    'tempo_range': (
                        min(p['tempo'] for p in patterns),
                        max(p['tempo'] for p in patterns)
                    ),
                    'source_songs': list(set(p['source_song'] for p in patterns))[:5]  # Top 5 sources
                }
        
        # Built chord pattern database
        return chord_database
    
    def build_scale_pattern_database(self) -> Dict[str, Dict]:
        """Build scale pattern database from chord progressions in GP data"""
        
        # Building scale pattern database from chord progressions
        
        scale_patterns = defaultdict(list)
        
        for song in self.gp_data:
            title = song.get('title', 'Unknown')
            
            # Extract chord progression from song
            song_chords = []
            
            for track in song.get('tracks', []):
                if track.get('is_percussion', False):
                    continue
                
                track_chords = self.extract_chords_from_track(track)
                song_chords.extend(track_chords)
            
            if len(song_chords) >= 4:  # Minimum progression for scale analysis
                # Detect key/scale from progression
                detected_scale = self.detect_scale_from_progression(song_chords)
                
                if detected_scale != 'Unknown':
                    scale_patterns[detected_scale].append({
                        'song': title,
                        'chord_progression': song_chords,
                        'progression_length': len(song_chords),
                        'unique_chords': len(set(song_chords))
                    })
        
        # Analyze scale patterns
        scale_database = {}
        
        for scale_name, progressions in scale_patterns.items():
            if len(progressions) >= 2:  # Need multiple examples
                
                # Find common chord patterns in this scale
                all_chords = []
                for prog in progressions:
                    all_chords.extend(prog['chord_progression'])
                
                chord_frequency = Counter(all_chords)
                common_chords = chord_frequency.most_common(10)
                
                scale_database[scale_name] = {
                    'total_songs': len(progressions),
                    'common_chords': common_chords,
                    'confidence_score': min(len(progressions) / 5.0, 1.0),
                    'example_progressions': [p['chord_progression'][:8] for p in progressions[:3]]
                }
        
        # Built scale pattern database
        return scale_database
    
    def extract_chords_from_track(self, track: Dict) -> List[str]:
        """Extract chord names from a track"""
        
        chords = []
        tuning = self.string_tunings['guitar_standard']  # Default
        
        if 'bass' in track.get('name', '').lower():
            tuning = self.string_tunings['bass_standard']
        
        for measure in track.get('measures', []):
            for voice in measure.get('voices', []):
                for beat in voice.get('beats', []):
                    notes = beat.get('notes', [])
                    
                    if len(notes) >= 3:  # Chord
                        fret_pattern = [(n.get('string', 1), n.get('value', 0)) for n in notes]
                        midi_pitches = [self.fret_to_midi_pitch(s, f, tuning) for s, f in fret_pattern]
                        
                        chord_name = self.analyze_chord_from_pattern(fret_pattern, midi_pitches)
                        if chord_name:
                            chords.append(chord_name)
        
        return chords
    
    def detect_scale_from_progression(self, chord_progression: List[str]) -> str:
        """Detect scale/key from chord progression"""
        
        # Key signatures and their common chords
        key_signatures = {
            'C major': ['C', 'Dm', 'Em', 'F', 'G', 'Am', 'Bdim'],
            'G major': ['G', 'Am', 'Bm', 'C', 'D', 'Em', 'F#dim'],
            'D major': ['D', 'Em', 'F#m', 'G', 'A', 'Bm', 'C#dim'],
            'A major': ['A', 'Bm', 'C#m', 'D', 'E', 'F#m', 'G#dim'],
            'E major': ['E', 'F#m', 'G#m', 'A', 'B', 'C#m', 'D#dim'],
            'B major': ['B', 'C#m', 'D#m', 'E', 'F#', 'G#m', 'A#dim'],
            'F major': ['F', 'Gm', 'Am', 'Bb', 'C', 'Dm', 'Edim'],
            'Bb major': ['Bb', 'Cm', 'Dm', 'Eb', 'F', 'Gm', 'Adim'],
            'Eb major': ['Eb', 'Fm', 'Gm', 'Ab', 'Bb', 'Cm', 'Ddim'],
            # Minor keys
            'A minor': ['Am', 'Bdim', 'C', 'Dm', 'Em', 'F', 'G'],
            'E minor': ['Em', 'F#dim', 'G', 'Am', 'Bm', 'C', 'D'],
            'B minor': ['Bm', 'C#dim', 'D', 'Em', 'F#m', 'G', 'A'],
            'D minor': ['Dm', 'Edim', 'F', 'Gm', 'Am', 'Bb', 'C'],
            'G minor': ['Gm', 'Adim', 'Bb', 'Cm', 'Dm', 'Eb', 'F'],
            'C minor': ['Cm', 'Ddim', 'Eb', 'Fm', 'Gm', 'Ab', 'Bb'],
        }
        
        # Normalize chord names
        def normalize_chord(chord):
            return chord.replace('sus2', '').replace('sus4', '').replace('7', '').replace('maj7', '').replace('m7', '').strip()
        
        normalized_chords = [normalize_chord(chord) for chord in chord_progression]
        unique_chords = list(set(normalized_chords))
        
        # Score each key
        key_scores = {}
        for key, key_chords in key_signatures.items():
            score = 0
            for chord in unique_chords:
                if chord in key_chords:
                    score += 1
            
            # Bonus for tonic presence
            tonic = key.split()[0]
            if tonic in unique_chords:
                score += 2
            
            key_scores[key] = score
        
        # Return best match
        if key_scores:
            best_key = max(key_scores, key=key_scores.get)
            if key_scores[best_key] > 0:
                return best_key
        
        return 'Unknown'
    
    def enhance_chord_detection(self, detected_chord: str, fret_pattern: List[Tuple] = None) -> Dict:
        """Enhance chord detection using GP dataset knowledge"""
        
        enhancement = {
            'original_chord': detected_chord,
            'enhanced_chord': detected_chord,
            'confidence_boost': 0.0,
            'gp_support': False,
            'alternative_names': [],
            'common_patterns': []
        }
        
        if detected_chord in self.chord_patterns:
            pattern_data = self.chord_patterns[detected_chord]
            
            enhancement.update({
                'enhanced_chord': detected_chord,
                'confidence_boost': pattern_data['confidence_score'] * 0.2,  # Up to 20% boost
                'gp_support': True,
                'occurrences_in_dataset': pattern_data['total_occurrences'],
                'common_patterns': [p[0] for p in pattern_data['common_fret_patterns']],
                'source_songs': pattern_data['source_songs']
            })
        
        return enhancement
    
    def enhance_scale_detection(self, chord_progression: List[str]) -> Dict:
        """Enhance scale detection using GP dataset knowledge"""
        
        detected_scale = self.detect_scale_from_progression(chord_progression)
        
        enhancement = {
            'detected_scale': detected_scale,
            'confidence': 0.5,  # Base confidence
            'gp_support': False,
            'supporting_evidence': []
        }
        
        if detected_scale in self.scale_patterns:
            scale_data = self.scale_patterns[detected_scale]
            
            enhancement.update({
                'confidence': min(0.5 + scale_data['confidence_score'] * 0.4, 0.9),  # Up to 90%
                'gp_support': True,
                'songs_in_dataset': scale_data['total_songs'],
                'common_chords_in_scale': scale_data['common_chords'][:5],
                'example_progressions': scale_data['example_progressions']
            })
        
        return enhancement
    
    def get_dataset_statistics(self) -> Dict:
        """Get comprehensive statistics about the GP dataset"""
        
        stats = {
            'total_songs': len(self.gp_data),
            'total_chord_types': len(self.chord_patterns),
            'total_scale_types': len(self.scale_patterns),
            'most_common_chords': [],
            'most_common_scales': [],
            'tempo_range': (0, 0),
            'dataset_coverage': {}
        }
        
        if self.chord_patterns:
            # Most common chords
            chord_counts = [(chord, data['total_occurrences']) 
                          for chord, data in self.chord_patterns.items()]
            stats['most_common_chords'] = sorted(chord_counts, key=lambda x: x[1], reverse=True)[:10]
        
        if self.scale_patterns:
            # Most common scales
            scale_counts = [(scale, data['total_songs']) 
                          for scale, data in self.scale_patterns.items()]
            stats['most_common_scales'] = sorted(scale_counts, key=lambda x: x[1], reverse=True)[:10]
        
        # Tempo analysis
        tempos = [song.get('tempo', 120) for song in self.gp_data if song.get('tempo')]
        if tempos:
            stats['tempo_range'] = (min(tempos), max(tempos))
            stats['average_tempo'] = sum(tempos) / len(tempos)
        
        return stats

def main():
    """Test the GP dataset integration"""
    
    print("🎸" + "="*60)
    print("🎯 GUITAR PRO DATASET INTEGRATION")
    print("="*60)
    
    # Initialize integration
    gp_integration = GPDatasetIntegration()
    
    # Get dataset statistics
    stats = gp_integration.get_dataset_statistics()
    
    print(f"📊 Dataset Statistics:")
    print(f"   Total songs: {stats['total_songs']}")
    print(f"   Chord types: {stats['total_chord_types']}")
    print(f"   Scale types: {stats['total_scale_types']}")
    
    if stats['most_common_chords']:
        print(f"   Most common chords:")
        for chord, count in stats['most_common_chords'][:5]:
            print(f"     • {chord}: {count} occurrences")
    
    if stats['most_common_scales']:
        print(f"   Most common scales:")
        for scale, count in stats['most_common_scales'][:5]:
            print(f"     • {scale}: {count} songs")
    
    print(f"   Tempo range: {stats['tempo_range'][0]}-{stats['tempo_range'][1]} BPM")
    
    print("\n✅ Guitar Pro dataset integration ready!")
    print("💡 Use this system to enhance chord and scale detection accuracy")

if __name__ == "__main__":
    main()
