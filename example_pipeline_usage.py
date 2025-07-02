#!/usr/bin/env python3
"""
Example: Audio-to-Chords Pipeline Usage
Simple demonstration of the integrated pipeline
"""

from audio_to_chords_pipeline import AudioToChordsPipeline
from pathlib import Path

def main():
    print("🎯 AUDIO-TO-CHORDS PIPELINE DEMO")
    print("=" * 50)
    
    # Initialize the pipeline
    pipeline = AudioToChordsPipeline(
        confidence_threshold=0.3,    # Audio-to-MIDI sensitivity
        min_note_duration=0.1,       # Minimum note length
        max_note_duration=4.0,       # Maximum note length
        chord_window_size=None,      # Auto-detect chord timing
        cleanup_midi=True            # Clean up temp files
    )
    
    # Example 1: Analyze a single audio file
    audio_file = "me.wav"  # Your audio file
    
    if Path(audio_file).exists():
        print(f"\n📁 Analyzing: {audio_file}")
        print("-" * 30)
        
        # Run the complete pipeline
        results = pipeline.analyze_audio_file(audio_file)
        
        # Display results
        print(f"\n🎸 CHORD PROGRESSION DETECTED:")
        print("-" * 30)
        
        for i, chord_info in enumerate(results['chord_progression'], 1):
            start_time = chord_info['start']
            end_time = chord_info['end']
            chord_name = chord_info['chord']
            
            # Format time as MM:SS
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)
            
            print(f"{i:2d}. [{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}] → {chord_name}")
        
        print(f"\n🎵 CHORD EVENTS SUMMARY:")
        print("-" * 30)
        
        for event in results['chord_events']:
            chord = event['chord']
            count = event['count']
            total_duration = event['total_duration']
            print(f"🎼 {chord}: {count} times (total: {total_duration:.1f}s)")
        
        print(f"\n📊 PIPELINE STATS:")
        print("-" * 30)
        print(f"⏱️  Total processing time: {results['total_time']:.1f}s")
        print(f"🎼 Total chord segments: {results['stats']['total_chords']}")
        print(f"🎯 Unique chord types: {results['stats']['unique_chords']}")
        print(f"🎶 Audio duration: {results['stats']['audio_duration']:.1f}s")
        
    else:
        print(f"❌ Audio file not found: {audio_file}")
        print("Available audio files in current directory:")
        for audio_ext in ['.wav', '.mp3', '.flac', '.aiff']:
            for file in Path('.').glob(f'*{audio_ext}'):
                print(f"  • {file.name}")

if __name__ == "__main__":
    main() 