from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os
import uuid
from dotenv import load_dotenv
import asyncio
from typing import Optional

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Import TTS utilities
from utils.markdown_to_ssml import md_to_ssml
from utils.tts_openai import synthesize_to_file

# Import the improved ChordAI tutor
try:
    from chordai_gpt_tutor import ChordAIRAGTutor
except ImportError:
    print("Error: ChordAI tutor not available. Please ensure chordai_gpt_tutor.py is in the current directory.")
    ChordAIRAGTutor = None

class RAGQuery(BaseModel):
    question: str
    context: dict = {}

# Create audio directory for TTS files
AUDIO_DIR = Path("./audio")
AUDIO_DIR.mkdir(exist_ok=True)

app = FastAPI()
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Optional: allow only your frontend's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with ["http://localhost:3000"] for React or Streamlit URL
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "online", "message": "ChordAI API Server is running"}

@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    confidence: float = Query(0.3),
    min_duration: float = Query(0.05),
    enable_tts: bool = Query(False),
    question: Optional[str] = Query(None)
):
    """Analyze audio using the improved ChordAI tutor with conversational responses."""
    
    if ChordAIRAGTutor is None:
        return JSONResponse(status_code=500, content={"error": "ChordAI tutor not available"})
    
    # 1. Save file temporarily
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audio_path = temp_path / file.filename
        with open(audio_path, "wb") as f:
            f.write(await file.read())

        try:
            # 2. Initialize the ChordAI tutor
            tutor = ChordAIRAGTutor()
            
            # 3. Run the analysis with the improved tutor
            print(f"🎵 Analyzing audio: {file.filename}")
            results = tutor.analyze_audio(
                wav_path=str(audio_path),
                user_question=question or "Tell me about this chord progression",
                confidence=confidence,
                min_duration=min_duration
            )
            
            if not results:
                return JSONResponse(status_code=500, content={"error": "Analysis failed - no results returned"})
            
            # 4. Generate TTS if enabled
            audio_url = None
            if enable_tts:
                try:
                    # Extract tutoring response for TTS
                    tutoring_text = results.get("tutoring_response", "")
                    if tutoring_text:
                        # Convert to SSML (remove markdown formatting for speech)
                        ssml = md_to_ssml(tutoring_text)
                        
                        # Generate MP3 using OpenAI TTS
                        temp_mp3 = synthesize_to_file(ssml, voice="alloy")
                        
                        # Move MP3 to audio directory
                        audio_id = f"{uuid.uuid4()}.mp3"
                        final_mp3 = AUDIO_DIR / audio_id
                        shutil.move(temp_mp3, final_mp3)
                        
                        # Set audio URL
                        audio_url = f"/audio/{audio_id}"
                        
                except Exception as e:
                    print(f"TTS generation failed: {e}")
                    # Continue without TTS if it fails
                    pass

            # 5. Prepare response with enhanced structure
            # Extract chord analysis data
            chord_analysis = results.get("chord_analysis", {})
            analysis_summary = chord_analysis.get("analysis_summary", {})
            
            response_data = {
                "status": "success",
                "filename": file.filename,
                "analysis": {
                    "detected_key": analysis_summary.get("detected_key", "Unknown"),
                    "chord_progression": analysis_summary.get("chord_progression", "Unknown"),
                    "total_chord_events": len(chord_analysis.get("chord_events", [])),
                    "estimated_accuracy": analysis_summary.get("estimated_accuracy_percent", 0),
                    "tempo_bpm": analysis_summary.get("tempo_bpm", 0)
                },
                "chord_events": chord_analysis.get("chord_events", []),
                "chord_tabs": results.get("chord_tabs", {}),
                "tutoring_response": results.get("tutoring", ""),
                "tutoring": results.get("tutoring", ""),  # Frontend compatibility
                "rag_embedded": results.get("embedding_result", {}).get("success", False),
                "tts_enabled": audio_url is not None
            }
            
            if audio_url:
                response_data["audio_url"] = audio_url
            
            return response_data
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return JSONResponse(status_code=500, content={"error": f"Analysis failed: {str(e)}"})

@app.post("/rag-query")
async def rag_query(query: RAGQuery):
    """Handle RAG system queries for music guidance using unified RAG system"""
    try:
        if ChordAIRAGTutor is None:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "ChordAI tutor not available",
                    "response": "I'm sorry, the music tutoring system is currently unavailable."
                }
            )
        
        # Initialize tutor and query the unified RAG system
        tutor = ChordAIRAGTutor()
        
        # Use the RAG system to get relevant context
        rag_results = tutor.rag_system.query(
            query=query.question,
            n_results=5,
            filter_metadata=query.context
        )
        
        if not rag_results or not rag_results.get('documents'):
            return {
                "response": "I couldn't find specific information about that topic in my music theory knowledge base. Could you try rephrasing your question or ask about chord progressions, music theory, or guitar techniques?",
                "source": "fallback",
                "context": query.context
            }
        
        # Generate a conversational response using the RAG context
        from openai import OpenAI
        client = OpenAI()
        
        # Prepare context from RAG results
        context_text = "\n".join(rag_results['documents'][0][:3])  # Top 3 results
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly guitar instructor and music theory teacher. Answer the user's question using the provided context in a conversational, encouraging way. Keep your response focused and practical."
                },
                {
                    "role": "user",
                    "content": f"Context from music theory knowledge base:\n{context_text}\n\nQuestion: {query.question}"
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return {
            "response": response.choices[0].message.content,
            "source": "unified_rag_system",
            "context": query.context,
            "documents_found": len(rag_results['documents'][0])
        }
        
    except Exception as e:
        print(f"RAG query error: {e}")
        return JSONResponse(
            status_code=500, 
            content={
                "error": f"RAG query failed: {str(e)}",
                "response": "I encountered an error while processing your question. Please try rephrasing or ask a different question."
            }
        )
from kyutai_tts_api import router as kyutai_tts_router
app.include_router(kyutai_tts_router)