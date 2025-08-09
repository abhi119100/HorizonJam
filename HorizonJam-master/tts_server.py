# tts_server.py
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from moshika_core import MoshikaCore
from dotenv import load_dotenv
from typing import Optional
import os

try:
    # Prefer using the shared OpenAI client helper if available
    from utils.tts_openai import _get_client as get_openai_client
except Exception:
    # Fallback to direct OpenAI import if utils helper is unavailable
    from openai import OpenAI

    def get_openai_client():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return OpenAI(api_key=api_key)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class TTSReq(BaseModel):
    text: str

# Initialize TTS model
print("Loading Moshi TTS model...")
try:
    tts_core = MoshikaCore()
    print("Moshi TTS model loaded successfully!")
except Exception as e:
    print(f"Error loading Moshi TTS model: {e}")
    tts_core = None

# Load environment variables (for OPENAI_API_KEY, fallback, and model dir)
load_dotenv()
ALLOW_OPENAI_FALLBACK = os.getenv("TTS_ALLOW_OPENAI_FALLBACK", "0").lower() in {"1", "true", "yes"}
MOSHI_MODEL_DIR = os.getenv("MOSHI_MODEL_DIR")

def synthesize_with_openai_as_wav(text: str) -> bytes:
    """Synthesize speech using OpenAI TTS (wav bytes)."""
    client = get_openai_client()
    # Some SDK versions return a stream-like object, others return a response with .content
    resp = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="wav",
    )

    # Normalize to raw bytes
    if hasattr(resp, "content") and resp.content is not None:
        return resp.content
    if hasattr(resp, "read"):
        return resp.read()
    # Iterative read as a last resort
    try:
        data = b""
        for chunk in resp.iter_bytes():
            data += chunk
        return data
    except Exception:
        # If object isn't iterable, try bytes() cast (may fail gracefully)
        return bytes(resp)

@app.post("/tts", response_class=Response)
async def synth(req: TTSReq):
    # Try local Moshi first (if present), else fallback to OpenAI
    moshi_attempted = False
    if tts_core is not None:
        try:
            moshi_attempted = True
            print(f"Generating Moshi audio for: {req.text}")
            audio_data = tts_core.generate_audio(req.text)
            print("Successfully generated Moshi audio")
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=audio.wav"}
            )
        except Exception as e:
            print(f"Moshi TTS failed, will try OpenAI fallback: {e}")

    # OpenAI fallback (disabled by default; enable via TTS_ALLOW_OPENAI_FALLBACK=1)
    if ALLOW_OPENAI_FALLBACK:
        try:
            print("Generating OpenAI TTS (fallback)...")
            audio_data = synthesize_with_openai_as_wav(req.text)
            print("Successfully generated OpenAI TTS audio")
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=audio.wav"}
            )
        except Exception as e:
            detail_prefix = "Moshi and OpenAI TTS failed" if moshi_attempted else "OpenAI TTS failed"
            print(f"{detail_prefix}: {e}")
            raise HTTPException(status_code=500, detail=f"{detail_prefix}: {str(e)}")

    # If fallback disabled or failed
    raise HTTPException(status_code=500, detail="Moshi TTS failed and OpenAI fallback is disabled")