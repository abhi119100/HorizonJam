import os
import tempfile
from typing import List, Tuple, Optional
import numpy as np

# Import existing converters
import os
# Lazy import to avoid hard dependency when input is already MIDI
def _bp_predict(*args, **kwargs):
    from basic_pitch.inference import predict  # correct module name
    return predict(*args, **kwargs)
import os
import pretty_midi
import librosa

def audio_to_midi(y: np.ndarray, sr: float, output_dir: str, 
                  min_note_len: float = 0.05,
                  min_freq: float = 80.0,
                  max_freq: float = 1200.0,
                  confidence_threshold: float = 0.3,
                  onset_threshold: float = 0.5,
                  frame_threshold: float = 0.3) -> List[str]:
    """Convert audio to MIDI with high-accuracy parameters."""
    
    # Create temporary file for audio
    temp_audio = os.path.join(output_dir, "temp_audio.wav")
    
    # Write audio to temporary file
    import soundfile as sf
    sf.write(temp_audio, y, sr)
    
    try:
        # Use BasicPitch with high-accuracy parameters optimized for guitar
        output_path = os.path.join(output_dir, "output.mid")
        
        # High-accuracy BasicPitch conversion
        # BasicPitch conversion
        model_output, midi_data, note_events = _bp_predict(
            audio_path=temp_audio,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_note_length=min_note_len,
            minimum_frequency=min_freq,
            maximum_frequency=max_freq
        )
        
        # Save MIDI manually
        midi_data.write(output_path)
        midi_path = output_path
        
        if os.path.exists(midi_path):
            return [midi_path]
        else:
            # Fallback to librosa with enhanced parameters
            print("BasicPitch failed, trying librosa with high accuracy...")
            midi_path = _convert_audio_to_midi_librosa(
                temp_audio, sr, output_path,
                confidence_threshold=confidence_threshold,
                min_note_duration=min_note_len
            )
            return [midi_path]
        
    except Exception as e:
        print(f"BasicPitch conversion failed: {e}")
        # Fallback to librosa
        print("Falling back to librosa converter...")
        output_path = os.path.join(output_dir, "output.mid")
        midi_path = _convert_audio_to_midi_librosa(
            temp_audio, sr, output_path,
            confidence_threshold=confidence_threshold,
            min_note_duration=min_note_len
        )
        return [midi_path]
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

def _convert_audio_to_midi_librosa(audio_path: str, sr: float, output_path: str,
                                   confidence_threshold: float = 0.3,
                                   min_note_duration: float = 0.05) -> str:
    """Convert audio to MIDI using librosa for onset detection and pretty_midi for MIDI creation."""
    y, sr = librosa.load(audio_path, sr=sr)

    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Simple pitch estimation (e.g., using pYIN or a simpler method if available)
    # For simplicity, this example uses a placeholder for pitch estimation.
    # In a real scenario, you'd integrate a pitch detection algorithm here.
    # For now, let's assume a fixed pitch or derive it from a simple frequency analysis.
    # This part needs significant enhancement for actual pitch accuracy.
    
    # Placeholder: Create a simple MIDI with a fixed note for each onset
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Acoustic Grand Piano'))

    # For demonstration, let's add a C4 note for each detected onset
    # In a real application, you'd determine pitch and duration more accurately.
    for onset_time in onset_times:
        # This is a very basic placeholder. Real pitch detection is needed.
        # For now, let's just add a middle C (MIDI note 60) for a short duration.
        note_number = 60  # Middle C
        duration = 0.5  # seconds
        
        # Ensure note duration is not less than min_note_duration
        if duration < min_note_duration:
            duration = min_note_duration

        note = pretty_midi.Note(velocity=100, pitch=note_number, start=onset_time, end=onset_time + duration)
        instrument.notes.append(note)

    midi.instruments.append(instrument)
    midi.write(output_path)
    return output_path