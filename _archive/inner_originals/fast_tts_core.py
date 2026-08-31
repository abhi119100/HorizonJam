import io
import numpy as np
import soundfile as sf
from typing import Dict, List
import hashlib
import os

# Ultra-fast TTS core for live streaming
# Uses pre-computed phoneme-to-audio mapping for instant response

class FastTTSCore:
    def __init__(self):
        self.phoneme_cache = {}
        self.word_cache = {}
        self.sample_rate = 16000
        self._init_basic_sounds()
    
    def _init_basic_sounds(self):
        """Initialize basic phoneme sounds for ultra-fast synthesis"""
        # Create basic vowel and consonant sounds
        duration = 0.1  # 100ms per phoneme
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Basic vowel frequencies (formants)
        vowels = {
            'a': [730, 1090],  # 'ah' sound
            'e': [530, 1840],  # 'eh' sound  
            'i': [270, 2290],  # 'ee' sound
            'o': [570, 840],   # 'oh' sound
            'u': [300, 870],   # 'oo' sound
        }
        
        # Generate vowel sounds
        for vowel, formants in vowels.items():
            # Simple formant synthesis
            sound = np.zeros_like(t)
            for freq in formants:
                sound += 0.3 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 3)
            self.phoneme_cache[vowel] = sound
        
        # Basic consonant sounds (noise-based)
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
        for consonant in consonants:
            # Generate noise-based consonant
            noise = np.random.normal(0, 0.1, len(t))
            # Apply frequency filtering based on consonant
            freq_mod = ord(consonant) * 50 + 200
            envelope = np.exp(-t * 8) * np.sin(2 * np.pi * freq_mod * t)
            sound = noise * envelope * 0.2
            self.phoneme_cache[consonant] = sound
    
    def text_to_phonemes(self, text: str) -> List[str]:
        """Ultra-simple text to phoneme conversion"""
        # Simple character-based approach for speed
        phonemes = []
        text = text.lower().replace(' ', '_')
        
        for char in text:
            if char.isalpha():
                phonemes.append(char)
            elif char == '_':
                phonemes.append('_')  # Pause
        
        return phonemes
    
    def synthesize_fast(self, text: str) -> bytes:
        """Ultra-fast synthesis using pre-computed sounds"""
        # Check word cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        if text_hash in self.word_cache:
            return self.word_cache[text_hash]
        
        # Convert to phonemes
        phonemes = self.text_to_phonemes(text)
        
        # Synthesize by concatenating phoneme sounds
        audio_segments = []
        
        for phoneme in phonemes:
            if phoneme == '_':
                # Add silence for spaces
                silence = np.zeros(int(self.sample_rate * 0.1))
                audio_segments.append(silence)
            elif phoneme in self.phoneme_cache:
                audio_segments.append(self.phoneme_cache[phoneme])
            else:
                # Fallback: simple tone based on character
                freq = 200 + ord(phoneme) * 20
                t = np.linspace(0, 0.1, int(self.sample_rate * 0.1))
                tone = 0.2 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 5)
                audio_segments.append(tone)
        
        # Concatenate all segments
        if audio_segments:
            full_audio = np.concatenate(audio_segments)
        else:
            # Fallback beep
            t = np.linspace(0, 0.5, int(self.sample_rate * 0.5))
            full_audio = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        # Normalize audio
        if np.max(np.abs(full_audio)) > 0:
            full_audio = full_audio / np.max(np.abs(full_audio)) * 0.7
        
        # Convert to WAV bytes
        buf = io.BytesIO()
        sf.write(buf, full_audio, self.sample_rate, format="WAV")
        audio_bytes = buf.getvalue()
        
        # Cache result (limit cache size)
        if len(self.word_cache) < 100:
            self.word_cache[text_hash] = audio_bytes
        
        return audio_bytes

# Global instance for reuse
_fast_tts = None

def get_fast_tts():
    global _fast_tts
    if _fast_tts is None:
        _fast_tts = FastTTSCore()
    return _fast_tts

def fast_tts_bytes(text: str) -> bytes:
    """Ultra-fast TTS synthesis for live streaming"""
    tts = get_fast_tts()
    return tts.synthesize_fast(text)