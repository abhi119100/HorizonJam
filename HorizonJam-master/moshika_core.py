# moshika_core.py
import torch
import soundfile as sf
import numpy as np
from pathlib import Path
import io
import sys
import os
import tempfile

# Add the moshi package to the path
sys.path.insert(0, str(Path(__file__).parent / "moshi" / "moshi"))

# Global variables for lazy loading
_moshi_tts_model = None

def _load_moshi_tts_model():
    """Lazy load the Moshi TTS model"""
    global _moshi_tts_model
    if _moshi_tts_model is None:
        print("Loading Moshi TTS model...")
        try:
            from moshi.models import loaders
            from moshi.models.tts import TTSModel
            
            # Load the models from the local directory
            model_dir = Path(__file__).parent / "models" / "kyutai"
            
            if model_dir.exists():
                print(f"Loading Moshi from local directory: {model_dir}")
                
                # Check for required model files
                moshi_weights = model_dir / "model.safetensors"
                mimi_weights = model_dir / "tokenizer-e351c8d8-checkpoint125.safetensors"
                tokenizer_path = model_dir / "tokenizer_spm_32k_3.model"
                
                if all(p.exists() for p in [moshi_weights, mimi_weights, tokenizer_path]):
                    # Create CheckpointInfo for proper model loading
                    checkpoint_info = loaders.CheckpointInfo(
                        moshi_weights=moshi_weights,
                        mimi_weights=mimi_weights,
                        tokenizer=tokenizer_path,
                        model_type="moshi"
                    )
                    
                    # Load the TTS model
                    _moshi_tts_model = TTSModel.from_checkpoint_info(
                        checkpoint_info,
                        device='cpu',  # Use CPU for compatibility
                        dtype=torch.float32  # Use float32 for CPU
                    )
                    
                    print("Moshi TTS model loaded successfully!")
                else:
                    missing_files = [str(p) for p in [moshi_weights, mimi_weights, tokenizer_path] if not p.exists()]
                    raise FileNotFoundError(f"Missing Moshi model files: {missing_files}")
            else:
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
                
        except Exception as e:
            print(f"Error loading Moshi TTS model: {e}")
            raise RuntimeError(f"Failed to load Moshi TTS model: {e}")
    
    return _moshi_tts_model

def generate_moshi_tts(text: str) -> bytes:
    """Generate TTS audio using Moshi model only"""
    try:
        print(f"Generating Moshi TTS for: {text}")
        
        # Load the Moshi TTS model
        tts_model = _load_moshi_tts_model()
        
        # Prepare the script for TTS
        script = [text]
        entries = tts_model.prepare_script(script)
        
        # Create condition attributes (for speaker conditioning)
        from moshi.models.tts import make_condition_attributes
        attributes = [make_condition_attributes()]
        
        # Generate audio
        with torch.no_grad():
            result = tts_model.generate(
                all_entries=[entries],
                attributes=attributes,
                temp=0.7,  # Temperature for generation
                cfg_coef=1.0  # Classifier-free guidance coefficient
            )
        
        # Extract audio from result
        audio_data = result.audio_wavs[0]  # Get first batch item
        
        # Convert to numpy and ensure proper format
        if isinstance(audio_data, torch.Tensor):
            audio_data = audio_data.cpu().numpy()
        
        # Ensure audio is in the right shape (flatten if needed)
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()
        
        # Normalize audio to prevent clipping
        if audio_data.max() > 1.0 or audio_data.min() < -1.0:
            audio_data = audio_data / max(abs(audio_data.max()), abs(audio_data.min()))
        
        # Convert to WAV bytes
        sample_rate = 24000  # Moshi uses 24kHz
        buf = io.BytesIO()
        sf.write(buf, audio_data, sample_rate, format="WAV")
        
        print("Successfully generated Moshi TTS audio")
        return buf.getvalue()
        
    except Exception as e:
        print(f"Moshi TTS generation failed: {e}")
        raise RuntimeError(f"Moshi TTS generation failed: {e}")

def tts_bytes(text: str) -> bytes:
    """Synthesize text to WAV bytes using Moshi TTS only"""
    return generate_moshi_tts(text)

class MoshikaCore:
    """Wrapper class for Moshi TTS functionality"""
    
    def __init__(self):
        print("Initializing MoshikaCore with Moshi TTS only...")
        # Pre-load the model to catch any errors early
        try:
            _load_moshi_tts_model()
            print("MoshikaCore initialized successfully with Moshi TTS")
        except Exception as e:
            print(f"Warning: Failed to initialize Moshi TTS: {e}")
            print("MoshikaCore will attempt to load Moshi TTS on first use")
    
    def generate_audio(self, text: str) -> bytes:
        """Generate audio from text using Moshi TTS only"""
        return tts_bytes(text)