import sys
import time
import soundfile as sf
import librosa
import numpy as np
import psutil
import os
from pathlib import Path

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def simple_transcription_analysis(audio_path):
    """
    Simple transcription analysis using librosa
    This simulates what BasicPitch would do - analyzing pitch and onset detection
    """
    print(f"\n🎵 Analyzing: {audio_path}")
    print("=" * 50)
    
    # Memory before loading
    mem_before = get_memory_usage()
    
    # Load audio
    load_start = time.time()
    y, sr = librosa.load(audio_path)
    load_time = time.time() - load_start
    
    # Memory after loading
    mem_after_load = get_memory_usage()
    
    print(f"📁 File size: {Path(audio_path).stat().st_size / 1024:.1f} KB")
    print(f"⏱️  Audio loading time: {load_time*1000:.0f} ms")
    print(f"🧠 Memory after load: {mem_after_load:.1f} MB (+{mem_after_load-mem_before:.1f} MB)")
    
    # Analysis phase - simulating transcription
    analysis_start = time.time()
    
    # 1. Pitch tracking (fundamental frequency estimation)
    pitch_start = time.time()
    f0, voiced_flag, voiced_probs = librosa.pyin(y, 
                                                 fmin=librosa.note_to_hz('C2'), 
                                                 fmax=librosa.note_to_hz('C7'))
    pitch_time = time.time() - pitch_start
    
    # 2. Onset detection
    onset_start = time.time()
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    onset_time = time.time() - onset_start
    
    # 3. Chroma features (for note identification)
    chroma_start = time.time()
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_time = time.time() - chroma_start
    
    # 4. Spectral analysis
    spectral_start = time.time()
    stft = librosa.stft(y)
    spectral_time = time.time() - spectral_start
    
    analysis_time = time.time() - analysis_start
    
    # Memory after analysis
    mem_after_analysis = get_memory_usage()
    
    # Create simple "note events" (simulating BasicPitch output)
    note_events = []
    valid_pitches = f0[~np.isnan(f0)]
    
    if len(valid_pitches) > 0 and len(onset_frames) > 0:
        # Create simple note events based on onsets and pitch
        for i, onset_time in enumerate(onset_frames):
            if i < len(onset_frames) - 1:
                duration = onset_frames[i+1] - onset_time
            else:
                duration = len(y)/sr - onset_time
            
            # Get average pitch around this onset
            onset_frame = librosa.time_to_frames(onset_time, sr=sr)
            if onset_frame < len(f0):
                pitch_hz = f0[onset_frame]
                if not np.isnan(pitch_hz):
                    midi_note = librosa.hz_to_midi(pitch_hz)
                    note_events.append({
                        'start': onset_time,
                        'duration': duration,
                        'midi_note': midi_note,
                        'frequency': pitch_hz
                    })
    
    # Results
    print(f"\n📊 Analysis Results:")
    print(f"   Total analysis time: {analysis_time*1000:.0f} ms")
    print(f"   - Pitch tracking: {pitch_time*1000:.0f} ms")
    print(f"   - Onset detection: {onset_time*1000:.0f} ms") 
    print(f"   - Chroma features: {chroma_time*1000:.0f} ms")
    print(f"   - Spectral analysis: {spectral_time*1000:.0f} ms")
    print(f"🧠 Memory after analysis: {mem_after_analysis:.1f} MB (+{mem_after_analysis-mem_after_load:.1f} MB)")
    print(f"🎼 Detected note events: {len(note_events)}")
    print(f"🎵 Detected onsets: {len(onset_frames)}")
    print(f"📈 Valid pitch points: {len(valid_pitches)}/{len(f0)} ({len(valid_pitches)/len(f0)*100:.1f}%)")
    
    # Show detected notes
    if note_events:
        print(f"\n🎹 First few detected notes:")
        for i, note in enumerate(note_events[:5]):
            note_name = librosa.midi_to_note(int(note['midi_note']))
            print(f"   {i+1}. {note_name} at {note['start']:.2f}s ({note['frequency']:.1f} Hz)")
    
    total_time = load_time + analysis_time
    print(f"\n⏱️  TOTAL PROCESSING TIME: {total_time*1000:.0f} ms")
    
    return {
        'total_time_ms': total_time * 1000,
        'load_time_ms': load_time * 1000,
        'analysis_time_ms': analysis_time * 1000,
        'memory_peak_mb': mem_after_analysis,
        'memory_increase_mb': mem_after_analysis - mem_before,
        'note_count': len(note_events),
        'onset_count': len(onset_frames),
        'file_size_kb': Path(audio_path).stat().st_size / 1024,
        'note_events': note_events
    }

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_transcription_benchmark.py <audio_file>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"❌ Error: File {audio_path} not found")
        sys.exit(1)
    
    try:
        results = simple_transcription_analysis(audio_path)
        
        # Summary line for easy logging
        print(f"\n📋 BENCHMARK SUMMARY:")
        print(f"File: {Path(audio_path).name}")
        print(f"Time: {results['total_time_ms']:.0f}ms | Memory: {results['memory_peak_mb']:.1f}MB | Notes: {results['note_count']}")
        
    except Exception as e:
        print(f"❌ Error processing {audio_path}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 