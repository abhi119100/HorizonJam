#!/usr/bin/env python3
"""
Audio-to-Chords Analysis Pipeline
Integrated system that converts audio to MIDI and analyzes chord progressions

Pipeline:
Audio File → MIDI Conversion → Chord Analysis → Results

Features:
- Imports AudioToMIDI from universal_audio_to_midi.py
- Imports chord analysis from midi_to_chords.py  
- Seamless audio-to-chord workflow
- Automatic intermediate file cleanup
- Comprehensive analysis output
"""

import sys
import argparse
from pathlib import Path
import time
import tempfile
import os

# Import our custom modules
try:
    from universal_audio_to_midi import AudioToMIDI
    print("✅ Successfully imported AudioToMIDI")
except ImportError as e:
    print(f"❌ Error importing AudioToMIDI: {e}")
    print("Make sure universal_audio_to_midi.py is in the same directory")
    sys.exit(1)

try:
    from midi_to_chords import analyze_midi_chords, parse_midi_notes
    print("✅ Successfully imported chord analysis functions")
except ImportError as e:
    print(f"❌ Error importing chord analysis: {e}")
    print("Make sure midi_to_chords.py is in the same directory")
    sys.exit(1)

class AudioToChordsPipeline:
    def __init__(self, 
                 confidence_threshold=0.3,
                 min_note_duration=0.1,
                 max_note_duration=4.0,
                 chord_window_size=None,
                 cleanup_midi=True):
        """
        Integrated Audio-to-Chords Pipeline
        
        Args:
            confidence_threshold: Audio-to-MIDI confidence threshold
            min_note_duration: Minimum note duration for MIDI
            max_note_duration: Maximum note duration for MIDI
            chord_window_size: Window size for chord analysis (auto if None)
            cleanup_midi: Whether to delete intermediate MIDI files
        """
        self.audio_converter = AudioToMIDI(
            confidence_threshold=confidence_threshold,
            min_note_duration=min_note_duration,
            max_note_duration=max_note_duration
        )
        self.chord_window_size = chord_window_size
        self.cleanup_midi = cleanup_midi
    
    def analyze_audio_file(self, audio_path, output_midi_path=None, verbose=True):
        """
        Complete pipeline: Audio → MIDI → Chord Analysis
        
        Args:
            audio_path: Path to input audio file
            output_midi_path: Path for intermediate MIDI file (temp if None)
            verbose: Whether to show detailed output
            
        Returns:
            dict: Complete analysis results
        """
        if verbose:
            print("🎯 AUDIO-TO-CHORDS ANALYSIS PIPELINE")
            print("=" * 60)
        
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        start_time = time.time()
        
        # Step 1: Audio to MIDI Conversion
        if verbose:
            print("\n📡 STEP 1: Converting Audio to MIDI")
            print("-" * 40)
        
        # Create temporary MIDI file if no output path specified
        use_temp_file = output_midi_path is None
        if use_temp_file:
            temp_dir = tempfile.mkdtemp()
            midi_path = os.path.join(temp_dir, f"{audio_file.stem}_temp.mid")
        else:
            midi_path = output_midi_path
        
        try:
            # Convert audio to MIDI
            conversion_start = time.time()
            midi_file_path = self.audio_converter.convert(audio_path, midi_path)
            conversion_time = time.time() - conversion_start
            
            if verbose:
                print(f"✅ Audio conversion complete in {conversion_time:.1f}s")
                print(f"🎼 Intermediate MIDI: {midi_file_path}")
            
            # Step 2: MIDI to Chords Analysis
            if verbose:
                print(f"\n🎸 STEP 2: Analyzing Chords from MIDI")
                print("-" * 40)
            
            analysis_start = time.time()
            
            # Run chord analysis
            chord_progression, chord_events = analyze_midi_chords(
                midi_file_path, 
                window_size=self.chord_window_size
            )
            
            analysis_time = time.time() - analysis_start
            total_time = time.time() - start_time
            
            # Compile results
            results = {
                'audio_file': str(audio_file),
                'midi_file': midi_file_path if not use_temp_file else None,
                'conversion_time': conversion_time,
                'analysis_time': analysis_time,
                'total_time': total_time,
                'chord_progression': chord_progression,
                'chord_events': chord_events,
                'stats': {
                    'total_chords': len(chord_progression),
                    'unique_chords': len(set(item['chord'] for item in chord_progression)),
                    'chord_events': len(chord_events),
                    'audio_duration': chord_progression[-1]['end'] if chord_progression else 0
                }
            }
            
            if verbose:
                print(f"\n✅ Chord analysis complete in {analysis_time:.1f}s")
                print(f"🎉 PIPELINE COMPLETE in {total_time:.1f}s")
                print("\n📊 PIPELINE SUMMARY")
                print("-" * 40)
                print(f"🎵 Audio file: {audio_file.name}")
                print(f"⏱️  Total processing: {total_time:.1f}s")
                print(f"   • Audio → MIDI: {conversion_time:.1f}s") 
                print(f"   • MIDI → Chords: {analysis_time:.1f}s")
                print(f"🎼 Detected {results['stats']['total_chords']} chord segments")
                print(f"🎯 Found {results['stats']['chord_events']} distinct chord events")
                print(f"🎶 {results['stats']['unique_chords']} unique chord types")
            
            return results
            
        finally:
            # Cleanup temporary MIDI file if requested
            if use_temp_file and self.cleanup_midi:
                try:
                    if os.path.exists(midi_path):
                        os.remove(midi_path)
                    os.rmdir(temp_dir)
                    if verbose:
                        print(f"🧹 Cleaned up temporary MIDI file")
                except:
                    pass  # Ignore cleanup errors
    
    def batch_analyze(self, audio_files, output_dir=None, verbose=True):
        """
        Analyze multiple audio files in batch
        
        Args:
            audio_files: List of audio file paths
            output_dir: Directory to save MIDI files (temp if None)
            verbose: Whether to show detailed output
            
        Returns:
            list: Results for each file
        """
        if verbose:
            print(f"🎯 BATCH AUDIO-TO-CHORDS ANALYSIS")
            print(f"📁 Processing {len(audio_files)} files")
            print("=" * 60)
        
        results = []
        
        for i, audio_file in enumerate(audio_files, 1):
            if verbose:
                print(f"\n📂 File {i}/{len(audio_files)}: {Path(audio_file).name}")
                print("=" * 40)
            
            try:
                # Set MIDI output path if output directory specified
                midi_path = None
                if output_dir:
                    output_path = Path(output_dir)
                    output_path.mkdir(exist_ok=True)
                    midi_path = output_path / f"{Path(audio_file).stem}.mid"
                
                # Analyze file
                result = self.analyze_audio_file(
                    audio_file, 
                    output_midi_path=midi_path,
                    verbose=verbose
                )
                results.append(result)
                
            except Exception as e:
                if verbose:
                    print(f"❌ Error processing {audio_file}: {e}")
                results.append({
                    'audio_file': str(audio_file),
                    'error': str(e)
                })
        
        if verbose:
            print(f"\n🎉 BATCH PROCESSING COMPLETE")
            print(f"✅ Successfully processed: {len([r for r in results if 'error' not in r])}/{len(audio_files)}")
            
        return results

def main():
    parser = argparse.ArgumentParser(description='Audio-to-Chords Analysis Pipeline')
    parser.add_argument('input', nargs='+', help='Input audio file(s) (.wav, .mp3, .flac, etc.)')
    parser.add_argument('-o', '--output-dir', help='Output directory for MIDI files (optional)')
    parser.add_argument('--confidence', type=float, default=0.3,
                       help='Audio-to-MIDI confidence threshold (0.1-0.9, default: 0.3)')
    parser.add_argument('--min-duration', type=float, default=0.1,
                       help='Minimum note duration in seconds (default: 0.1)')
    parser.add_argument('--max-duration', type=float, default=4.0,
                       help='Maximum note duration in seconds (default: 4.0)')
    parser.add_argument('--window-size', type=float,
                       help='Chord analysis window size in seconds (auto if not specified)')
    parser.add_argument('--keep-midi', action='store_true',
                       help='Keep intermediate MIDI files (default: cleanup)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Validate input files
    audio_files = []
    for file_path in args.input:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ Error: File not found: {file_path}")
            return 1
        audio_files.append(str(path))
    
    # Create pipeline
    pipeline = AudioToChordsPipeline(
        confidence_threshold=args.confidence,
        min_note_duration=args.min_duration,
        max_note_duration=args.max_duration,
        chord_window_size=args.window_size,
        cleanup_midi=not args.keep_midi
    )
    
    try:
        if len(audio_files) == 1:
            # Single file analysis
            result = pipeline.analyze_audio_file(
                audio_files[0],
                output_midi_path=Path(args.output_dir) / f"{Path(audio_files[0]).stem}.mid" if args.output_dir else None,
                verbose=not args.quiet
            )
            
            if not args.quiet:
                print(f"\n🎯 Analysis saved for: {result['audio_file']}")
            
        else:
            # Batch analysis
            results = pipeline.batch_analyze(
                audio_files,
                output_dir=args.output_dir,
                verbose=not args.quiet
            )
            
            if not args.quiet:
                print(f"\n📊 Batch analysis complete: {len(results)} files processed")
        
        return 0
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 