# TTS (Text-to-Speech) Implementation for ChordAI Backend

This document describes the implementation of TTS functionality that converts the RAG-enhanced music tutoring responses into spoken audio using OpenAI's TTS API.

## 🎯 Overview

The TTS implementation adds voice mode to the ChordAI backend, allowing users to:
1. Upload audio files for chord analysis
2. Receive detailed music tutoring in text format
3. Get the same tutoring as spoken audio (MP3) via TTS
4. Access the audio through a direct URL

## 🏗️ Architecture

### Components Added

1. **`utils/markdown_to_ssml.py`** - Converts markdown tutoring responses to SSML format
2. **`utils/tts_openai.py`** - Handles OpenAI TTS synthesis
3. **Enhanced `api_server.py`** - Integrated TTS into the analyze endpoint
4. **Static file serving** - Serves generated MP3 files

### Workflow

```
Audio Upload → Chord Analysis → RAG Tutoring → Markdown → SSML → TTS → MP3 → URL
```

## 📁 File Structure

```
HorizonJam-master/
├── utils/
│   ├── __init__.py
│   ├── markdown_to_ssml.py    # Markdown to SSML conversion
│   └── tts_openai.py          # OpenAI TTS integration
├── audio/                     # Generated MP3 files (auto-created)
├── api_server.py              # Enhanced with TTS
└── requirements.txt           # Updated dependencies
```

## 🔧 Setup & Installation

### 1. Install Dependencies

```bash
cd HorizonJam-master
pip install -r requirements.txt
```

New dependencies added:
- `openai>=1.86.0` - OpenAI TTS API
- `beautifulsoup4>=4.12.0` - HTML parsing for SSML
- `markdown>=3.5.0` - Markdown processing
- `python-dotenv>=1.0.0` - Environment variables
- `uvicorn` - ASGI server for FastAPI

### 2. Environment Setup

Ensure your `.env` file contains:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Start the Server

```bash
cd HorizonJam-master
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

## 🎵 API Usage

### Enhanced `/analyze` Endpoint

**POST** `/analyze`

**Parameters:**
- `file` (required): Audio file (WAV, MP3, etc.)
- `confidence` (optional): Chord detection confidence (default: 0.3)
- `min_duration` (optional): Minimum chord duration (default: 0.05)
- `enable_tts` (optional): Enable TTS generation (default: true)

**Response:**
```json
{
  "chord_analysis": { ... },
  "tutoring_response": "Detailed markdown tutoring...",
  "audio_url": "/audio/uuid.mp3",
  "tts_enabled": true,
  "metadata": { ... }
}
```

### Example Usage

```python
import requests

# Upload audio file with TTS enabled
with open('test_audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/analyze',
        files={'file': f},
        params={'enable_tts': True}
    )

data = response.json()
if data.get('audio_url'):
    audio_url = f"http://localhost:8000{data['audio_url']}"
    print(f"Listen to tutoring: {audio_url}")
```

## 🔊 TTS Features

### Voice Options
- **Default Voice**: `alloy` (neutral, balanced)
- **Configurable**: Can be changed in `utils/tts_openai.py`
- **Available Voices**: alloy, echo, fable, onyx, nova, shimmer

### SSML Processing
- Converts markdown formatting to speech-friendly text
- Adds pauses before headings (600ms)
- Removes formatting tags (bold, italic, code)
- Handles lists and bullet points

### Audio Format
- **Format**: MP3
- **Quality**: Standard TTS-1 model
- **Bitrate**: OpenAI default (typically 128kbps)

## 🧪 Testing

### Manual Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8000/
   ```

2. **TTS Analysis**:
   ```bash
   curl -X POST "http://localhost:8000/analyze?enable_tts=true" \
        -F "file=@tests/testG.wav"
   ```

### Automated Testing

Run the provided test script:
```bash
python test_tts_api.py
```

## 🔒 Security & Performance

### Security
- API key loaded from environment variables
- Temporary files cleaned up automatically
- MP3 files served through FastAPI static files

### Performance
- TTS generation is optional (can be disabled)
- Graceful fallback if TTS fails
- Lazy loading of OpenAI client
- Temporary file cleanup

### Rate Limits
- Subject to OpenAI TTS API rate limits
- Recommended: Implement caching for repeated requests

## 🐛 Error Handling

### Common Issues

1. **Missing OpenAI API Key**:
   ```
   Error: OPENAI_API_KEY environment variable is not set
   ```
   **Solution**: Add API key to `.env` file

2. **TTS Generation Fails**:
   - API continues without TTS
   - `tts_enabled: false` in response
   - Check API key and network connectivity

3. **Audio File Not Found**:
   - Check `/audio` directory permissions
   - Verify file was generated successfully

## 🚀 Integration with Frontend

### React/JavaScript Example

```javascript
// Upload and get TTS response
const formData = new FormData();
formData.append('file', audioFile);
formData.append('enable_tts', 'true');

fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.audio_url) {
    // Play the audio
    const audio = new Audio(`http://localhost:8000${data.audio_url}`);
    audio.play();
  }
});
```

## 📈 Future Enhancements

1. **Voice Selection**: Allow users to choose TTS voice
2. **Speed Control**: Adjustable speech rate
3. **Caching**: Cache TTS for identical tutoring responses
4. **Streaming**: Real-time TTS streaming
5. **Multiple Languages**: Support for different languages
6. **Audio Effects**: Add background music or effects

## 🔧 Configuration

### Customizing TTS Settings

Edit `utils/tts_openai.py`:

```python
# Change voice
response = client.audio.speech.create(
    model="tts-1",
    voice="nova",  # Change voice here
    input=ssml,
    response_format="mp3",
)
```

### Customizing SSML Processing

Edit `utils/markdown_to_ssml.py`:

```python
# Adjust heading pause duration
def md_to_ssml(md: str, heading_pause_ms: int = 800):  # Longer pause
```

## 📞 Support

For issues or questions:
1. Check the error logs in the terminal
2. Verify OpenAI API key is valid
3. Test with the provided `test_tts_api.py` script
4. Check network connectivity to OpenAI services

---

**Note**: This implementation requires an active OpenAI API key with TTS access. The TTS feature will gracefully degrade if the API key is missing or invalid.