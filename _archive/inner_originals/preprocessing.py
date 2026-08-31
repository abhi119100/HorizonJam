import librosa
import numpy as np
from scipy.signal import butter, lfilter

def preprocess_audio(y: np.ndarray, sr: float) -> np.ndarray:
    """Normalize, apply high-pass filter, and detect onsets."""
    # Normalize
    y = librosa.util.normalize(y)
    
    # High-pass filter (noise reduction for guitar >80Hz)
    b, a = butter(2, 80 / (sr / 2), btype='high')
    y = lfilter(b, a, y)
    
    # Onset detection (optional for chunking)
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    
    return y

def segment_audio(y: np.ndarray, sr: float, chunk_duration: float = 10.0) -> list:
    """Segment audio into chunks for parallel processing."""
    chunk_size = int(chunk_duration * sr)
    chunks = []
    
    for i in range(0, len(y), chunk_size):
        chunk = y[i:i + chunk_size]
        chunks.append((chunk, sr))
    
    return chunks