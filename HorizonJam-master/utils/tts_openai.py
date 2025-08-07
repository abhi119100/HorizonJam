import uuid
import tempfile
from pathlib import Path
from openai import OpenAI
import os

# Initialize client as None, will be created when needed
client = None

def _get_client():
    """Get or create OpenAI client."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        client = OpenAI(api_key=api_key)
    return client

def synthesize_to_file(ssml: str, voice="alloy") -> Path:
    """Return path to a temp MP3 file with spoken SSML."""
    try:
        client = _get_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=ssml,
            response_format="mp3",
        )
        
        path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.mp3"
        
        # Handle different response formats based on OpenAI version
        if hasattr(response, 'content'):
            path.write_bytes(response.content)
        elif hasattr(response, 'read'):
            path.write_bytes(response.read())
        else:
            # For newer versions, response might be bytes directly
            with open(path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        
        return path
    except Exception as e:
        print(f"TTS synthesis error: {e}")
        raise