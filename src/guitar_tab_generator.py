#!/usr/bin/env python3
"""
Guitar Tab Generator - ChordAI/Chordify Style
Converts detected chords to visual guitar tabs with 6 strings and fret numbers
"""

import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class GuitarTabGenerator:
    """Generates guitar tabs from chord names using curated Guitar Pro data"""
    
    def __init__(self, gp_data_path: str = "training_data/all_parsed_gp_data.json"):
        self.gp_data_path = gp_data_path
        # Standard tuning info must be available before building the database
        self.standard_tuning = ['E', 'A', 'D', 'G', 'B', 'E']  # Low to High
        self.standard_tuning_midi = [40, 45, 50, 55, 59, 64]  # MIDI notes
        self.chord_fingerings = self.build_chord_fingering_database()
        
    def build_chord_fingering_database(self) -> Dict[str, Dict]:
        """Build comprehensive chord fingering database from Guitar Pro data"""
        
        # Building chord fingering database from Guitar Pro data
        
        try:
            with open(self.gp_data_path, 'r') as f:
                gp_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load GP data: {e}")
            return self.get_default_chord_fingerings()
        
        chord_fingerings = {}
        
        for song in gp_data:
            for track in song.get('tracks', []):
                if track.get('is_percussion', False):
                    continue
                
                # Focus on guitar tracks
                track_name = track.get('name', '').lower()
                if 'bass' in track_name:
                    continue
                
                for measure in track.get('measures', []):
                    for voice in measure.get('voices', []):
                        for beat in voice.get('beats', []):
                            notes = beat.get('notes', [])
                            
                            if len(notes) >= 3:  # Potential chord
                                fingering = self.extract_fingering_from_notes(notes)
                                chord_name = self.identify_chord_from_fingering(fingering)
                                
                                if chord_name and fingering:
                                    if chord_name not in chord_fingerings:
                                        chord_fingerings[chord_name] = {
                                            'primary_fingering': fingering,
                                            'alternative_fingerings': [],
                                            'difficulty': self.calculate_fingering_difficulty(fingering),
                                            'occurrences': 1
                                        }
                                    else:
                                        # Track alternative fingerings
                                        if fingering != chord_fingerings[chord_name]['primary_fingering']:
                                            if fingering not in chord_fingerings[chord_name]['alternative_fingerings']:
                                                chord_fingerings[chord_name]['alternative_fingerings'].append(fingering)
                                        chord_fingerings[chord_name]['occurrences'] += 1
        
        # Add default fingerings only if not found in GP data
        default_fingerings = self.get_default_chord_fingerings()
        for chord, fingering_data in default_fingerings.items():
            if chord not in chord_fingerings:
                chord_fingerings[chord] = fingering_data
        
        # Built fingering database
        return chord_fingerings
    
    def extract_fingering_from_notes(self, notes: List[Dict]) -> List[int]:
        """Extract 6-string fingering from Guitar Pro notes"""
        
        # Initialize with -1 (muted/not played)
        fingering = [-1, -1, -1, -1, -1, -1]  # Strings 6,5,4,3,2,1 (low to high)
        
        for note in notes:
            string_num = note.get('string', 1)  # GP uses 1-6
            fret = note.get('value', 0)
            
            # Convert GP string numbering (1=high E, 6=low E) to our array index
            if 1 <= string_num <= 6:
                array_index = 6 - string_num  # Convert to 0-5 index (6th string = index 0)
                fingering[array_index] = fret
        
        return fingering
    
    def identify_chord_from_fingering(self, fingering: List[int]) -> Optional[str]:
        """Identify chord name from fingering pattern"""
        
        # Convert fingering to MIDI pitches
        midi_pitches = []
        for string_idx, fret in enumerate(fingering):
            if fret >= 0:  # Not muted
                midi_pitch = self.standard_tuning_midi[string_idx] + fret
                midi_pitches.append(midi_pitch % 12)  # Pitch class
        
        if len(midi_pitches) < 3:
            return None
        
        # Chord recognition logic
        unique_pitches = sorted(list(set(midi_pitches)))
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Common chord patterns
        chord_patterns = {
            (0, 4, 7): '',          # Major
            (0, 3, 7): 'm',         # Minor
            (0, 4, 7, 10): '7',     # Dominant 7th
            (0, 3, 7, 10): 'm7',    # Minor 7th
            (0, 4, 7, 11): 'maj7',  # Major 7th
            (0, 2, 7): 'sus2',      # Sus2
            (0, 5, 7): 'sus4',      # Sus4
            (0, 3, 6): 'dim',       # Diminished
            (0, 4, 8): 'aug',       # Augmented
        }
        
        # Try each root note
        for root in range(12):
            for intervals, suffix in chord_patterns.items():
                expected_pitches = [(root + interval) % 12 for interval in intervals]
                
                if all(pitch in unique_pitches for pitch in expected_pitches):
                    chord_name = note_names[root] + suffix
                    return chord_name
        
        return None
    
    def calculate_fingering_difficulty(self, fingering: List[int]) -> int:
        """Calculate difficulty level (1-5) of a fingering"""
        
        active_frets = [f for f in fingering if f >= 0]
        if not active_frets:
            return 1
        
        difficulty = 1
        
        # Wide fret span increases difficulty
        fret_span = max(active_frets) - min(active_frets)
        if fret_span > 3:
            difficulty += 1
        if fret_span > 5:
            difficulty += 1
        
        # High fret positions increase difficulty
        if max(active_frets) > 7:
            difficulty += 1
        if max(active_frets) > 12:
            difficulty += 1
        
        # Barre chords (same fret on multiple strings) are harder
        fret_counts = {}
        for fret in active_frets:
            fret_counts[fret] = fret_counts.get(fret, 0) + 1
        
        if any(count >= 3 for count in fret_counts.values()):
            difficulty += 1
        
        return min(difficulty, 5)
    
    def get_default_chord_fingerings(self) -> Dict[str, Dict]:
        """Default chord fingerings for common chords"""
        
        return {
            # Open chords (easiest)
            'C': {
                'primary_fingering': [-1, 3, 2, 0, 1, 0],  # x32010
                'alternative_fingerings': [[-1, 3, 5, 5, 5, 3]],  # Barre version
                'difficulty': 2,
                'occurrences': 100
            },
            'G': {
                'primary_fingering': [3, 2, 0, 0, 3, 3],  # 320033
                'alternative_fingerings': [[3, 2, 0, 0, 0, 3]],
                'difficulty': 2,
                'occurrences': 100
            },
            'D': {
                'primary_fingering': [-1, -1, 0, 2, 3, 2],  # xx0232
                'alternative_fingerings': [[-1, -1, 0, 7, 7, 7]],
                'difficulty': 2,
                'occurrences': 100
            },
            'A': {
                'primary_fingering': [-1, 0, 2, 2, 2, 0],  # x02220
                'alternative_fingerings': [[5, 7, 7, 6, 5, 5]],
                'difficulty': 2,
                'occurrences': 100
            },
            'E': {
                'primary_fingering': [0, 2, 2, 1, 0, 0],  # 022100
                'alternative_fingerings': [[0, 7, 9, 9, 9, 7]],
                'difficulty': 1,
                'occurrences': 100
            },
            'Am': {
                'primary_fingering': [-1, 0, 2, 2, 1, 0],  # x02210
                'alternative_fingerings': [[5, 7, 7, 5, 5, 5]],
                'difficulty': 2,
                'occurrences': 100
            },
            'Em': {
                'primary_fingering': [0, 2, 2, 0, 0, 0],  # 022000
                'alternative_fingerings': [[0, 7, 9, 9, 8, 7]],
                'difficulty': 1,
                'occurrences': 100
            },
            'Dm': {
                'primary_fingering': [-1, -1, 0, 2, 3, 1],  # xx0231
                'alternative_fingerings': [[-1, -1, 0, 7, 6, 5]],
                'difficulty': 2,
                'occurrences': 100
            },
            'F': {
                'primary_fingering': [1, 3, 3, 2, 1, 1],  # 133211 (barre)
                'alternative_fingerings': [[-1, -1, 3, 2, 1, 1]],  # xx3211
                'difficulty': 4,
                'occurrences': 100
            },
            # Suspended chords
            'Esus2': {
                'primary_fingering': [0, 2, 2, 2, 0, 0],  # 022200
                'alternative_fingerings': [[0, 7, 9, 9, 7, 7]],
                'difficulty': 2,
                'occurrences': 50
            },
            'Asus2': {
                'primary_fingering': [-1, 0, 2, 2, 0, 0],  # x02200
                'alternative_fingerings': [[5, 7, 7, 5, 5, 5]],
                'difficulty': 2,
                'occurrences': 50
            },
            'Dsus2': {
                'primary_fingering': [-1, -1, 0, 2, 3, 0],  # xx0230
                'alternative_fingerings': [[-1, -1, 0, 7, 7, 5]],
                'difficulty': 2,
                'occurrences': 50
            },
            # Seventh chords
            'G7': {
                'primary_fingering': [3, 2, 0, 0, 0, 1],  # 320001
                'alternative_fingerings': [[3, 5, 3, 4, 3, 3]],
                'difficulty': 2,
                'occurrences': 50
            },
            'C7': {
                'primary_fingering': [-1, 3, 2, 3, 1, 0],  # x32310
                'alternative_fingerings': [[-1, 3, 5, 3, 5, 3]],
                'difficulty': 3,
                'occurrences': 50
            },
            'D7': {
                'primary_fingering': [-1, -1, 0, 2, 1, 2],  # xx0212
                'alternative_fingerings': [[-1, -1, 0, 7, 6, 7]],
                'difficulty': 2,
                'occurrences': 50
            },
            'A7': {
                'primary_fingering': [-1, 0, 2, 0, 2, 0],  # x02020
                'alternative_fingerings': [[5, 7, 5, 6, 5, 5]],
                'difficulty': 2,
                'occurrences': 50
            },
            'E7': {
                'primary_fingering': [0, 2, 0, 1, 0, 0],  # 020100
                'alternative_fingerings': [[0, 7, 6, 7, 5, 7]],
                'difficulty': 2,
                'occurrences': 50
            },
            'Am7': {
                'primary_fingering': [-1, 0, 2, 0, 1, 0],  # x02010
                'alternative_fingerings': [[-1, 0, 2, 2, 1, 3], [5, 7, 5, 5, 5, 5]],
                'difficulty': 2,
                'occurrences': 50
            },
            'B': {
                'primary_fingering': [-1, 2, 4, 4, 4, 2],  # x24442 (barre)
                'alternative_fingerings': [[7, 9, 9, 8, 7, 7]],
                'difficulty': 4,
                'occurrences': 50
            },
            'B7': {
                'primary_fingering': [-1, 2, 1, 2, 0, 2],  # x21202
                'alternative_fingerings': [[7, 9, 7, 8, 7, 7]],
                'difficulty': 3,
                'occurrences': 50
            },
            # Additional suspended chords
            'Bsus4': {
                'primary_fingering': [-1, 2, 4, 4, 5, 2],  # x24452
                'alternative_fingerings': [[7, 9, 9, 9, 7, 7]],
                'difficulty': 4,
                'occurrences': 30
            },
            'Bsus2': {
                'primary_fingering': [-1, 2, 4, 4, 2, 2],  # x24422
                'alternative_fingerings': [[7, 9, 9, 7, 7, 7]],
                'difficulty': 4,
                'occurrences': 30
            },
            'Csus4': {
                'primary_fingering': [-1, 3, 3, 0, 1, 1],  # x33011
                'alternative_fingerings': [[-1, 3, 5, 5, 6, 3]],
                'difficulty': 3,
                'occurrences': 30
            },
            'Gsus4': {
                'primary_fingering': [3, 3, 0, 0, 3, 3],  # 330033
                'alternative_fingerings': [[3, 5, 5, 5, 3, 3]],
                'difficulty': 2,
                'occurrences': 30
            },
            'Dsus4': {
                'primary_fingering': [-1, -1, 0, 2, 3, 3],  # xx0233
                'alternative_fingerings': [[-1, -1, 0, 7, 8, 7]],
                'difficulty': 2,
                'occurrences': 30
            },
            'Asus4': {
                'primary_fingering': [-1, 0, 2, 2, 3, 0],  # x02230
                'alternative_fingerings': [[5, 7, 7, 7, 5, 5]],
                'difficulty': 2,
                'occurrences': 30
            },
            'Esus4': {
                'primary_fingering': [0, 2, 2, 2, 0, 0],  # 022200
                'alternative_fingerings': [[0, 7, 9, 9, 7, 7]],
                'difficulty': 1,
                'occurrences': 30
            }
        }
    
    def generate_chord_tab(self, chord_name: str, show_alternatives: bool = False) -> Dict:
        """Generate guitar tab for a specific chord"""
        
        # Normalize chord name
        normalized_chord = self.normalize_chord_name(chord_name)
        
        if normalized_chord not in self.chord_fingerings:
            return {
                'chord': chord_name,
                'found': False,
                'message': f"Chord '{chord_name}' not found in database",
                'suggestion': self.suggest_similar_chord(chord_name)
            }
        
        fingering_data = self.chord_fingerings[normalized_chord]
        primary_fingering = fingering_data['primary_fingering']
        
        tab_result = {
            'chord': chord_name,
            'normalized_chord': normalized_chord,
            'found': True,
            'primary_tab': self.format_tab_display(primary_fingering),
            'fingering': primary_fingering,
            'difficulty': fingering_data['difficulty'],
            'difficulty_text': self.get_difficulty_text(fingering_data['difficulty']),
            'occurrences': fingering_data.get('occurrences', 0)
        }
        
        if show_alternatives and fingering_data.get('alternative_fingerings'):
            tab_result['alternatives'] = []
            for alt_fingering in fingering_data['alternative_fingerings'][:3]:  # Max 3 alternatives
                tab_result['alternatives'].append({
                    'tab': self.format_tab_display(alt_fingering),
                    'fingering': alt_fingering,
                    'difficulty': self.calculate_fingering_difficulty(alt_fingering)
                })
        
        return tab_result
    
    def format_tab_display(self, fingering: List[int]) -> str:
        """Format fingering as visual guitar tab"""
        
        string_names = ['E', 'A', 'D', 'G', 'B', 'E']  # Low to High
        
        tab_lines = []
        
        # Header
        tab_lines.append("    Guitar Tab")
        tab_lines.append("    ----------")
        
        # String lines with fret numbers
        for i, (string_name, fret) in enumerate(zip(string_names, fingering)):
            if fret == -1:
                fret_display = 'x'
            else:
                fret_display = str(fret)
            
            # Add string name and fret
            line = f"{string_name} |--{fret_display}--"
            tab_lines.append(line)
        
        return '\n'.join(tab_lines)
    
    def format_compact_tab(self, fingering: List[int]) -> str:
        """Format fingering as compact tab notation"""
        
        fret_display = []
        for fret in fingering:
            if fret == -1:
                fret_display.append('x')
            else:
                fret_display.append(str(fret))
        
        return ''.join(fret_display)
    
    def normalize_chord_name(self, chord_name: str) -> str:
        """Normalize chord name for database lookup"""
        
        # Handle common variations
        chord_name = chord_name.strip()
        
        # Convert flat/sharp notation
        chord_name = chord_name.replace('♭', 'b').replace('♯', '#')
        
        # Handle major chord notation
        if chord_name.endswith('maj') and not chord_name.endswith('maj7'):
            chord_name = chord_name[:-3]  # Remove 'maj' for major chords
        
        return chord_name
    
    def suggest_similar_chord(self, chord_name: str) -> Optional[str]:
        """Suggest similar chord if exact match not found"""
        
        # Extract root note
        root = chord_name[0:2] if len(chord_name) > 1 and chord_name[1] in ['#', 'b'] else chord_name[0]
        
        # Look for chords with same root
        similar_chords = []
        for known_chord in self.chord_fingerings.keys():
            if known_chord.startswith(root):
                similar_chords.append(known_chord)
        
        if similar_chords:
            return similar_chords[0]
        
        return None
    
    def get_difficulty_text(self, difficulty: int) -> str:
        """Convert difficulty number to text"""
        
        difficulty_map = {
            1: "Beginner",
            2: "Easy", 
            3: "Intermediate",
            4: "Advanced",
            5: "Expert"
        }
        
        return difficulty_map.get(difficulty, "Unknown")
    
    def generate_chord_progression_tabs(self, chord_progression: List[str]) -> Dict:
        """Generate tabs for an entire chord progression"""
        
        progression_tabs = {
            'progression': chord_progression,
            'tabs': [],
            'compact_notation': [],
            'difficulty_summary': {
                'average_difficulty': 0,
                'hardest_chord': '',
                'easiest_chord': ''
            }
        }
        
        difficulties = []
        
        for chord in chord_progression:
            tab_result = self.generate_chord_tab(chord)
            progression_tabs['tabs'].append(tab_result)
            
            if tab_result['found']:
                progression_tabs['compact_notation'].append(
                    f"{chord}: {self.format_compact_tab(tab_result['fingering'])}"
                )
                difficulties.append((chord, tab_result['difficulty']))
            else:
                progression_tabs['compact_notation'].append(f"{chord}: Not Found")
        
        # Calculate difficulty summary
        if difficulties:
            avg_difficulty = sum(d[1] for d in difficulties) / len(difficulties)
            progression_tabs['difficulty_summary']['average_difficulty'] = round(avg_difficulty, 1)
            
            hardest = max(difficulties, key=lambda x: x[1])
            easiest = min(difficulties, key=lambda x: x[1])
            
            progression_tabs['difficulty_summary']['hardest_chord'] = f"{hardest[0]} (Level {hardest[1]})"
            progression_tabs['difficulty_summary']['easiest_chord'] = f"{easiest[0]} (Level {easiest[1]})"
        
        return progression_tabs
    
    def print_chord_tab(self, chord_name: str, show_alternatives: bool = False):
        """Print formatted chord tab to console"""
        
        tab_result = self.generate_chord_tab(chord_name, show_alternatives)
        
        if not tab_result['found']:
            print(f"❌ {tab_result['message']}")
            if tab_result.get('suggestion'):
                print(f"💡 Try: {tab_result['suggestion']}")
            return
        
        print(f"\n🎸 {tab_result['chord']} Chord")
        print("=" * 40)
        print(tab_result['primary_tab'])
        print(f"\n📊 Difficulty: {tab_result['difficulty_text']} (Level {tab_result['difficulty']})")
        print(f"📈 Found in dataset: {tab_result['occurrences']} times")
        print(f"🎯 Compact notation: {self.format_compact_tab(tab_result['fingering'])}")
        
        if show_alternatives and tab_result.get('alternatives'):
            print(f"\n🔄 Alternative Fingerings:")
            for i, alt in enumerate(tab_result['alternatives'], 1):
                print(f"\nAlternative {i} (Level {alt['difficulty']}):")
                print(alt['tab'])
    
    def print_progression_tabs(self, chord_progression: List[str]):
        """Print tabs for entire chord progression"""
        
        progression_data = self.generate_chord_progression_tabs(chord_progression)
        
        print(f"\n🎼 Chord Progression Tabs")
        print("=" * 60)
        print(f"Progression: {' - '.join(chord_progression)}")
        print(f"Average Difficulty: {progression_data['difficulty_summary']['average_difficulty']}")
        print(f"Hardest: {progression_data['difficulty_summary']['hardest_chord']}")
        print(f"Easiest: {progression_data['difficulty_summary']['easiest_chord']}")
        
        print(f"\n📋 Compact Notation:")
        for notation in progression_data['compact_notation']:
            print(f"  {notation}")
        
        print(f"\n🎸 Individual Chord Tabs:")
        print("-" * 40)
        
        for tab_result in progression_data['tabs']:
            if tab_result['found']:
                print(f"\n{tab_result['chord']}:")
                print(tab_result['primary_tab'])
            else:
                print(f"\n{tab_result['chord']}: Not Found")

def main():
    """Test the guitar tab generator"""
    
    print("🎸" + "="*60)
    print("🎯 GUITAR TAB GENERATOR - ChordAI Style")
    print("="*60)
    
    # Initialize tab generator
    tab_generator = GuitarTabGenerator()
    
    # Test with common chords
    test_chords = ['Esus2', 'B', 'E', 'C', 'G', 'Am', 'F']
    
    print(f"🎼 Testing chord tabs...")
    
    for chord in test_chords:
        tab_generator.print_chord_tab(chord)
    
    # Test progression
    print(f"\n" + "="*60)
    progression = ['Esus2', 'B', 'E']
    tab_generator.print_progression_tabs(progression)

if __name__ == "__main__":
    main()
