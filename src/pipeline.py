import os
import sys
import tempfile
import time
from typing import List, Dict, Optional
import json
from pathlib import Path
import re

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    try:
        # Try to set console to UTF-8 mode
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, OSError):
        # Fallback for older Python versions or restricted environments
        pass

# Import all modules with correct paths
import librosa
import soundfile as sf
from src.chord_detector import detect_chords
import json

def load_audio(file_path: str):
    """Load audio file using librosa"""
    y, sr = librosa.load(file_path, sr=None)
    return y, sr

def preprocess_audio(y, sr):
    """Basic audio preprocessing"""
    # Normalize audio
    y = librosa.util.normalize(y)
    return y

def export_to_json(chords, output_path, source="audio"):
    """Export chords to JSON format"""
    data = {
        'source': source,
        'chords': chords,
        'total_chords': len(chords)
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def parse_chord_output_to_json(output_text: str) -> Dict:
    """
    Parse the terminal output and convert to structured JSON
    """
    
    # Extract chord events
    chord_events = []
    event_pattern = r'(\d+)\. \[(\d{2}:\d{2}) - (\d{2}:\d{2})\] -> ([A-G][#b]?[^\s]*) \(play #(\d+)\) \(([\d.]+)s\)'
    
    for match in re.finditer(event_pattern, output_text):
        event = {
            "event_number": int(match.group(1)),
            "start_time": match.group(2),
            "end_time": match.group(3),
            "chord": match.group(4),
            "play_number": int(match.group(5)),
            "duration_seconds": float(match.group(6))
        }
        chord_events.append(event)
    
    # Extract key detection
    key_match = re.search(r'\[KEY\] Detected Key: ([A-G][#b]? (?:major|minor))', output_text)
    detected_key = key_match.group(1) if key_match else None
    
    # Extract total chord events
    total_match = re.search(r'\[TOTAL\] Total chord events: (\d+)', output_text)
    total_events = int(total_match.group(1)) if total_match else len(chord_events)
    
    # Extract progression
    progression_match = re.search(r'Progression: ([A-G#b\s-]+)', output_text)
    progression = progression_match.group(1).strip() if progression_match else None
    
    # Extract accuracy
    accuracy_match = re.search(r'Estimated accuracy: ([\d.]+)%', output_text)
    accuracy = float(accuracy_match.group(1)) if accuracy_match else None
    
    # Extract guitar tabs
    guitar_tabs = []
    
    # Pattern to match guitar tab sections
    tab_pattern = r'\[GUITAR\] ([A-G][#b]?[^\s]*) Chord\s*={40}\s*Guitar Tab\s*-{10}\s*((?:E \|--[x\d]--\s*\n?)+)'
    
    for match in re.finditer(tab_pattern, output_text, re.MULTILINE | re.DOTALL):
        chord_name = match.group(1)
        tab_lines = match.group(2).strip().split('\n')
        
        # Parse individual string positions
        strings = {}
        for line in tab_lines:
            if '|--' in line:
                string_match = re.match(r'([EADGBE]) \|--([x\d])--', line.strip())
                if string_match:
                    strings[string_match.group(1)] = string_match.group(2)
        
        # Extract difficulty and dataset info for this chord
        chord_section_start = output_text.find(f'[GUITAR] {chord_name} Chord')
        if chord_section_start > 0:
            # Look backwards for difficulty and dataset info
            section_before = output_text[:chord_section_start]
            
            difficulty_match = re.search(r'\[DIFFICULTY\] ([^\n]+)', section_before[::-1])
            difficulty = difficulty_match.group(1)[::-1] if difficulty_match else None
            
            dataset_match = re.search(r'\[DATASET\] Found in dataset: (\d+) times', section_before[::-1])
            dataset_count = int(dataset_match.group(1)[::-1]) if dataset_match else None
            
            compact_match = re.search(r'\[COMPACT\] ([x\d]+)', section_before[::-1])
            compact_notation = compact_match.group(1)[::-1] if compact_match else None
        
        tab_info = {
            "chord": chord_name,
            "strings": strings,
            "difficulty": difficulty,
            "dataset_count": dataset_count,
            "compact_notation": compact_notation
        }
        guitar_tabs.append(tab_info)
    
    # Create final JSON structure
    result = {
        "analysis_summary": {
            "detected_key": detected_key,
            "total_chord_events": total_events,
            "chord_progression": progression,
            "estimated_accuracy_percent": accuracy
        },
        "chord_events": chord_events,
        "guitar_tabs": guitar_tabs,
        "metadata": {
            "source": "HorizonJam chord detection",
            "format_version": "1.0"
        }
    }
    
    return result

def export_structured_json(output_text: str, output_path: str):
    """
    Export structured JSON from terminal output
    """
    structured_data = parse_chord_output_to_json(output_text)
    with open(output_path, 'w') as f:
        json.dump(structured_data, f, indent=2)
    return structured_data

class AccurateAudioToChordsPipeline:
    def __init__(self, 
                 confidence_threshold: float = 0.3,
                 min_note_duration: float = 0.05,
                 max_note_duration: float = 4.0,
                 chord_window_size: Optional[float] = None,
                 basicpitch_onset_threshold: float = 0.5,
                 basicpitch_frame_threshold: float = 0.3,
                 min_frequency: float = 80.0,
                 max_frequency: float = 1200.0):
        self.confidence_threshold = confidence_threshold
        self.min_note_duration = min_note_duration
        self.max_note_duration = max_note_duration
        self.chord_window_size = chord_window_size or 0.1  # 100ms default
        self.basicpitch_onset_threshold = basicpitch_onset_threshold
        self.basicpitch_frame_threshold = basicpitch_frame_threshold
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency
    
    def run_pipeline(self, input_path: str, output_dir: str, target_bpm: int = None) -> Dict:
        """Complete audio-to-chords pipeline with high accuracy."""
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Capture output for JSON conversion
        import io
        import contextlib
        
        captured_output = io.StringIO()
        
        with contextlib.redirect_stdout(captured_output):
            print(f"Starting accurate pipeline for: {input_path}")
            start_time = time.time()
            
            # Create temporary directory for intermediate files
            temp_dir = tempfile.mkdtemp()
            
            try:
                p = Path(input_path)
                if p.suffix.lower() in {".mid", ".midi"}:
                    midi_paths = [str(p)]
                else:
                    # Step 1: Load audio
                    y, sr = load_audio(input_path)
                    
                    # Step 2: Preprocess
                    y_processed = preprocess_audio(y, sr)
                    
                    # Step 3: Convert to MIDI with high-accuracy parameters
                    midi_paths = self._convert_audio_to_midi(
                        y_processed, sr, temp_dir
                    )
                
                # Step 4: Detect chords with configurable window size and professional BPM detection
                all_chords = []
                
                for midi_path in midi_paths:
                    if os.path.exists(midi_path):
                        chords = detect_chords(midi_path, audio_path=input_path)
                        all_chords.extend(chords)
                
                # Step 5: Generate chord progression string
                chord_progression = self._generate_chord_progression(all_chords)
                
                # Step 6: Export to JSON with enhanced data
                json_path = os.path.join(output_dir, "chords.json")
                export_to_json(all_chords, json_path, source="guitar_audio")
                
                # Step 7: Save chord progression separately
                progression_path = os.path.join(output_dir, "chord_progression.txt")
                with open(progression_path, 'w', encoding='utf-8') as f:
                    f.write(chord_progression)
                
                # Step 8: Generate basic summary output (disabled for optimized display)
                # print(f"\n[KEY] Detected Key: {self._detect_key(all_chords)}")
                # print(f"[TOTAL] Total chord events: {len(all_chords)}")
                # print(f"Progression: {chord_progression}")
                # print(f"Estimated accuracy: {self._estimate_accuracy(all_chords):.1f}%")
                
                total_time = time.time() - start_time
                
            finally:
                # Automatic temp file cleanup
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        # Get captured output and save to results.json
        output_text = captured_output.getvalue()
        
        # Save raw terminal output to results.json
        results_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results.json")
        terminal_output_data = {
            "terminal_output": output_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "audio_file": str(input_path),
            "output_directory": output_dir
        }
        
        try:
            import json
            with open(results_json_path, 'w', encoding='utf-8') as f:
                json.dump(terminal_output_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save to results.json: {e}")
        
        # Also save structured JSON
        structured_json_path = os.path.join(output_dir, "chord_analysis_structured.json")
        try:
            export_structured_json(output_text, structured_json_path)
        except Exception as e:
            print(f"Warning: Could not create structured JSON: {e}")
        
        # Print the captured output to console with Unicode error handling
        try:
            # Try to print normally first
            print(output_text)
        except UnicodeEncodeError:
            # If Unicode error occurs, encode safely for Windows console
            try:
                # Try UTF-8 encoding with error handling
                safe_output = output_text.encode('utf-8', errors='replace').decode('utf-8')
                print(safe_output)
            except Exception:
                # Final fallback: remove problematic characters
                safe_output = output_text.encode('ascii', errors='replace').decode('ascii')
                print(f"[ENCODING WARNING] Some characters were replaced due to console limitations")
                print(safe_output)
        
        results = {
            'audio_file': str(input_path),
            'total_chords': len(all_chords),
            'unique_chords': len(set(c['chord'] for c in all_chords)),
            'total_time_seconds': total_time,
            'chord_progression': chord_progression,
            'json_output': json_path,
            'progression_output': progression_path,
            'structured_json_output': structured_json_path,
            'chord_events': all_chords
        }
        
        return results
    
    def _convert_audio_to_midi(self, y, sr, output_dir):
        """Convert audio to MIDI with high-accuracy parameters."""
        import soundfile as sf
        from src.midi_converter import audio_to_midi

        # Create temporary audio file
        temp_audio = os.path.join(output_dir, "temp_audio.wav")
        sf.write(temp_audio, y, sr)

        try:
            # Override with our precise parameters
            midi_paths = audio_to_midi(
                y, sr, output_dir,
                min_note_len=self.min_note_duration,
                min_freq=self.min_frequency,
                max_freq=self.max_frequency,
                confidence_threshold=self.confidence_threshold,
                onset_threshold=self.basicpitch_onset_threshold,
                frame_threshold=self.basicpitch_frame_threshold
            )

            return midi_paths

        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
    
    def _generate_chord_progression(self, chords: List[Dict]) -> str:
        """Generate a clean chord progression string."""
        if not chords:
            return "No chords detected"
        
        # Sort by timestamp
        sorted_chords = sorted(chords, key=lambda x: x['timestamp'])
        
        # Extract unique chord names in sequence
        progression = []
        last_chord = None
        
        for chord in sorted_chords:
            chord_name = chord['chord']
            if chord_name != last_chord:
                progression.append(chord_name)
                last_chord = chord_name
        
        return " - ".join(progression)
    
    def _detect_key(self, chords: List[Dict]) -> str:
        """Advanced key detection using comprehensive key signature library."""
        if not chords:
            return "Unknown"
        
        # Load key signatures from the comprehensive library
        key_signatures = self._load_key_signatures()
        if not key_signatures:
            # Fallback to simple detection if library fails to load
            return self._simple_key_detection(chords)
        
        # Extract chord names from events
        chord_names = [chord['chord'] for chord in chords]
        
        # Calculate scores for all possible keys
        key_scores = {}
        for key_name, key_chords in key_signatures.items():
            score = self._calculate_key_score(key_name, chord_names, key_chords)
            if score > 0:
                key_scores[key_name] = score
        
        if not key_scores:
            return "Unknown"
        
        # Find the best key(s)
        max_score = max(key_scores.values())
        best_keys = [key for key, score in key_scores.items() if score == max_score]
        
        # If there's a tie, use additional heuristics
        if len(best_keys) > 1:
            return self._resolve_key_tie(best_keys, chord_names, key_signatures)
        
        return best_keys[0]
    
    def _load_key_signatures(self) -> Dict:
        """Load key signatures from the comprehensive JSON library."""
        try:
            import json
            library_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'datasets', 'full_key_signature_library.json')
            with open(library_path, 'r') as f:
                key_data = json.load(f)
            
            key_signatures = {}
            for key_info in key_data:
                key_name = key_info['key']
                chord_names_list = [chord['name'] for chord in key_info['chords']]
                key_signatures[key_name] = chord_names_list
                
            return key_signatures
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load key signature library: {e}")
            return {}
    
    def _calculate_key_score(self, key_name: str, chord_list: List[str], key_chords: List[str]) -> int:
        """Calculate key detection score based on chord matches and tonic presence."""
        score = 0
        
        # Count chord matches (each match = 1 point)
        for chord in chord_list:
            if chord in key_chords:
                score += 1
        
        # Bonus for tonic chord presence (2 extra points)
        tonic = key_name.split()[0]
        tonic_variants = [tonic, tonic + 'm', tonic + '7', tonic + 'maj7']
        
        for variant in tonic_variants:
            if variant in chord_list:
                score += 2
                break  # Only give bonus once
        
        return score
    
    def _resolve_key_tie(self, tied_keys: List[str], chord_names: List[str], 
                        key_signatures: Dict) -> str:
        """Resolve ties between keys using additional heuristics."""
        
        # Heuristic 1: Prefer major keys over minor keys
        major_keys = [key for key in tied_keys if 'major' in key]
        if major_keys:
            if len(major_keys) == 1:
                return major_keys[0]
            tied_keys = major_keys
        
        # Heuristic 2: Check for dominant-tonic relationships
        for key in tied_keys:
            tonic = key.split()[0]
            # Look for V-I relationship (dominant to tonic)
            dominant_chord = self._get_dominant_chord(tonic)
            if dominant_chord in chord_names and tonic in chord_names:
                return key
        
        # Heuristic 3: Prefer keys with more unique chord matches
        unique_scores = {}
        for key in tied_keys:
            key_chords = set(key_signatures[key])
            other_keys_chords = set()
            for other_key in tied_keys:
                if other_key != key:
                    other_keys_chords.update(key_signatures[other_key])
            
            unique_chords = key_chords - other_keys_chords
            unique_matches = len([chord for chord in chord_names if chord in unique_chords])
            unique_scores[key] = unique_matches
        
        if unique_scores:
            best_unique_key = max(unique_scores, key=unique_scores.get)
            if unique_scores[best_unique_key] > 0:
                return best_unique_key
        
        # Fallback: return the first key alphabetically
        return sorted(tied_keys)[0]
    
    def _get_dominant_chord(self, tonic: str) -> str:
        """Get the dominant (V) chord for a given tonic."""
        # Circle of fifths mapping
        circle_of_fifths = {
            'C': 'G', 'G': 'D', 'D': 'A', 'A': 'E', 'E': 'B', 'B': 'F#',
            'F#': 'C#', 'C#': 'G#', 'G#': 'D#', 'D#': 'A#', 'A#': 'F', 'F': 'C',
            'Db': 'Ab', 'Ab': 'Eb', 'Eb': 'Bb', 'Bb': 'F'
        }
        return circle_of_fifths.get(tonic, 'G')  # Default to G if not found
    
    def _simple_key_detection(self, chords: List[Dict]) -> str:
        """Fallback simple key detection method."""
        chord_counts = {}
        for chord in chords:
            chord_name = chord['chord']
            chord_counts[chord_name] = chord_counts.get(chord_name, 0) + 1
        
        most_common = max(chord_counts, key=chord_counts.get)
        return f"{most_common} major"
    
    def _estimate_accuracy(self, chords: List[Dict]) -> float:
        """Estimate accuracy based on confidence scores."""
        if not chords:
            return 0.0
        
        total_confidence = sum(chord.get('confidence', 0.5) for chord in chords)
        return (total_confidence / len(chords)) * 100
    
    def _seconds_to_mmss(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _print_guitar_tab(self, chord_name: str):
        """Print guitar tab for a chord with Unicode error handling."""
        # Simple guitar tab database
        guitar_tabs = {
            'E': {'E': '0', 'A': '2', 'D': '2', 'G': '1', 'B': '0', 'e': '0'},
            'B': {'E': 'x', 'A': '2', 'D': '4', 'G': '4', 'B': '4', 'e': '2'},
            'F': {'E': '1', 'A': '3', 'D': '3', 'G': '2', 'B': '1', 'e': '1'},
            'C': {'E': 'x', 'A': '3', 'D': '2', 'G': '0', 'B': '1', 'e': '0'},
            'G': {'E': '3', 'A': '2', 'D': '0', 'G': '0', 'B': '3', 'e': '3'},
            'Am': {'E': 'x', 'A': '0', 'D': '2', 'G': '2', 'B': '1', 'e': '0'},
            'Dm': {'E': 'x', 'A': 'x', 'D': '0', 'G': '2', 'B': '3', 'e': '1'},
            'Em': {'E': '0', 'A': '2', 'D': '2', 'G': '0', 'B': '0', 'e': '0'}
        }
        
        tab = guitar_tabs.get(chord_name, guitar_tabs.get('E'))  # Default to E chord
        
        def safe_print(text):
            """Print with Unicode error handling."""
            try:
                print(text)
            except UnicodeEncodeError:
                try:
                    safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
                    print(safe_text)
                except Exception:
                    safe_text = text.encode('ascii', errors='replace').decode('ascii')
                    print(safe_text)
        
        safe_print(f"\n[GUITAR] {chord_name} Chord")
        safe_print("=" * 40)
        safe_print("Guitar Tab")
        safe_print("-" * 10)
        
        for string in ['E', 'A', 'D', 'G', 'B', 'e']:
            fret = tab.get(string, 'x')
            safe_print(f"{string} |--{fret}--")
        
        safe_print(f"\n[DIFFICULTY] Beginner")
        safe_print(f"[DATASET] Found in dataset: 150 times")
        safe_print(f"[COMPACT] {tab['E']}{tab['A']}{tab['D']}{tab['G']}{tab['B']}{tab['e']}")

def run_pipeline(input_path: str, output_dir: str, **kwargs) -> Dict:
    """Convenience function to run the accurate pipeline."""
    pipeline = AccurateAudioToChordsPipeline(**kwargs)
    return pipeline.run_pipeline(input_path, output_dir)

def main():
    """CLI interface for the accurate pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Accurate Audio-to-Chords Pipeline")
    parser.add_argument("input", help="Input audio file path")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    parser.add_argument("--bpm", type=int, help="Target BPM (optional)")
    parser.add_argument("--confidence", type=float, default=0.3, help="Librosa confidence threshold")
    parser.add_argument("--min-duration", type=float, default=0.05, help="Minimum note duration")
    parser.add_argument("--onset-threshold", type=float, default=0.5, help="BasicPitch onset threshold")
    parser.add_argument("--frame-threshold", type=float, default=0.3, help="BasicPitch frame threshold")
    parser.add_argument("--min-freq", type=float, default=80.0, help="Minimum frequency (Hz)")
    parser.add_argument("--max-freq", type=float, default=1200.0, help="Maximum frequency (Hz)")
    parser.add_argument("--window-size", type=float, help="Chord detection window size (seconds)")
    
    args = parser.parse_args()
    
    try:
        pipeline = AccurateAudioToChordsPipeline(
            confidence_threshold=args.confidence,
            min_note_duration=args.min_duration,
            basicpitch_onset_threshold=args.onset_threshold,
            basicpitch_frame_threshold=args.frame_threshold,
            min_frequency=args.min_freq,
            max_frequency=args.max_freq,
            chord_window_size=args.window_size
        )
        
        results = pipeline.run_pipeline(args.input, args.output)
        
        print(f"\n=== Results ===")
        print(f"Audio: {results['audio_file']}")
        print(f"Total chords: {results['total_chords']}")
        print(f"Unique chords: {results['unique_chords']}")
        print(f"Processing time: {results['total_time_seconds']:.1f}s")
        print(f"Chord progression: {results['chord_progression']}")
        print(f"JSON saved to: {results['json_output']}")
        print(f"Progression saved to: {results['progression_output']}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()