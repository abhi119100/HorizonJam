# tts_server.py
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os

# Load environment variables FIRST so keys are available
load_dotenv()

try:
    from utils.tts_openai import _get_client as get_openai_client
except Exception:
    from utils.openai_client import build_openai_client

    def get_openai_client():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return build_openai_client(api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSReq(BaseModel):
    text: str

# Try to load Moshi TTS (optional — will gracefully skip if not installed)
tts_core = None
try:
    from moshika_core import MoshikaCore
    tts_core = MoshikaCore()
    print("Moshi TTS model loaded successfully!")
except Exception as e:
    print(f"Moshi TTS not available ({e}), using OpenAI TTS only")

ALLOW_OPENAI_FALLBACK = os.getenv("TTS_ALLOW_OPENAI_FALLBACK", "1").lower() in {"1", "true", "yes"}

def synthesize_with_openai_as_wav(text: str) -> bytes:
    """Synthesize speech using OpenAI TTS (wav bytes)."""
    client = get_openai_client()
    resp = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="wav",
    )
    if hasattr(resp, "content") and resp.content is not None:
        return resp.content
    if hasattr(resp, "read"):
        return resp.read()
    data = b""
    for chunk in resp.iter_bytes():
        data += chunk
    return data

@app.post("/tts", response_class=Response)
async def synth(req: TTSReq):
    # Try local Moshi first (if available)
    if tts_core is not None:
        try:
            audio_data = tts_core.generate_audio(req.text)
            return Response(content=audio_data, media_type="audio/wav")
        except Exception as e:
            print(f"Moshi TTS failed: {e}")

    # OpenAI fallback (enabled by default)
    if ALLOW_OPENAI_FALLBACK:
        try:
            audio_data = synthesize_with_openai_as_wav(req.text)
            return Response(content=audio_data, media_type="audio/wav")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI TTS failed: {str(e)}")

    raise HTTPException(status_code=500, detail="No TTS backend available")
