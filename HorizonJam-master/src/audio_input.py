import librosa
import numpy as np

def load_audio(file_path: str) -> tuple[np.ndarray, float]:
    """Load audio with Librosa and validate format/duration."""
    try:
        y, sr = librosa.load(file_path, sr=22050, mono=True)  # Downsample for speed
        
        if len(y) == 0:
            raise ValueError("Empty audio file")
        
        # Check duration < 5min for MVP (300s * 22050 = 6,615,000 samples)
        max_duration = 5 * 60 * sr
        if len(y) > max_duration:
            raise ValueError(f"Audio too long: {len(y)/sr:.1f}s > 300s limit")
        
        return y, sr
        
    except Exception as e:
        raise ValueError(f"Audio load failed: {e}")