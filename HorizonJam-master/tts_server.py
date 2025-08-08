# tts_server.py
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from moshika_core import MoshikaCore

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

@app.post("/tts", response_class=Response)
async def synth(req: TTSReq):
    try:
        print(f"Generating Moshi audio for: {req.text}")
        audio_data = tts_core.generate_audio(req.text)
        print("Successfully generated Moshi audio")
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=audio.wav"}
        )
    except Exception as e:
        print(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")