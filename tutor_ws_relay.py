#!/usr/bin/env python3
"""
ChordAI Tutor WebSocket Relay with Streaming TTS

Integrates ChordAI analysis with real-time streaming TTS tutoring responses.
Handles audio file uploads, chord analysis, and streams tutoring explanations via WebSocket.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Force UTF-8 stdout/stderr on Windows so emoji prints don't crash when stdout
# is a pipe (background processes, reverse proxies). cp1252 is the default
# console codec on Windows and can't encode ✅ / ⚠ / etc.
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests

# Import ChordAI GPT Tutor
try:
    from chordai_gpt_tutor import ChordAIRAGTutor
    print("✅ ChordAI GPT Tutor imported")
except ImportError as e:
    print(f"⚠️ ChordAI GPT Tutor not available: {e}")
    ChordAIRAGTutor = None

# Initialization is lazy in TutorWebSocketManager.connect(). Eager setup
# duplicated the RAG/model work and made importing the relay configuration-bound.
chord_tutor = None

app = FastAPI(title="ChordAI Tutor WebSocket Relay")

# CORS configuration to allow frontend running on localhost:3000
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

# TTS server configuration
TTS_SERVER_URL = "http://localhost:5000/tts"

class TutorWebSocketManager:
    """Manages WebSocket connections for streaming tutor responses."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.tutor = None
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")
        
        # Initialize tutor if not already done
        if not self.tutor:
            try:
                self.tutor = ChordAIRAGTutor()
                print("✅ ChordAI tutor initialized")
            except Exception as e:
                print(f"❌ Failed to initialize tutor: {e}")
                await self.send_error(client_id, f"Failed to initialize tutor: {e}")
                
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected")
            
    async def send_text_chunk(self, client_id: str, text: str):
        """Generate TTS for a text chunk and send as a single playable WAV blob."""
        if client_id in self.active_connections:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        TTS_SERVER_URL,
                        json={"text": text},
                        headers={"Accept": "audio/wav"}
                    ) as resp:
                        if resp.status != 200:
                            print(f"TTS server error: {resp.status}")
                            return
                        data = bytearray()
                        async for chunk in resp.content.iter_chunked(65536):
                            data.extend(chunk)
                        await self.active_connections[client_id].send_bytes(bytes(data))
                        print(f"Sent TTS WAV ({len(data)} bytes) for: {text[:50]}...")
            except Exception as e:
                print(f"Error sending TTS audio: {e}")
                
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send JSON message to client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                
    async def send_error(self, client_id: str, error: str):
        """Send error message to client."""
        await self.send_message(client_id, {
            "type": "error",
            "message": error
        })
        
    async def analyze_audio_streaming(self, client_id: str, audio_file_path: str, user_question: Optional[str] = None):
        """Analyze audio and stream tutoring response with per-sentence TTS."""
        try:
            if not self.tutor:
                await self.send_error(client_id, "Tutor not initialized")
                return

            # Step 1: Chord detection (blocking, run in thread pool)
            await self.send_message(client_id, {
                "type": "status",
                "message": "Detecting chords..."
            })

            loop = asyncio.get_event_loop()
            chord_results = await loop.run_in_executor(
                None, self.tutor._run_horizon_jam, audio_file_path
            )

            await self.send_message(client_id, {
                "type": "chord_analysis",
                "data": chord_results
            })

            # Step 2: RAG context retrieval
            await self.send_message(client_id, {
                "type": "status",
                "message": "Retrieving musical context..."
            })

            rag_context = await loop.run_in_executor(
                None, self.tutor._retrieve_rag_context, chord_results, user_question
            )

            # Step 3: Stream GPT-4o text + TTS sentence-by-sentence
            await self.send_message(client_id, {
                "type": "status",
                "message": "Your tutor is speaking..."
            })

            # Collect sentences from the synchronous GPT stream via a queue
            sentence_queue = asyncio.Queue()
            evidence_trace = {}

            def sync_stream_callback(sentence: str):
                """Called from sync GPT stream for each sentence."""
                loop.call_soon_threadsafe(sentence_queue.put_nowait, sentence)

            def sync_trace_callback(trace: Dict[str, Any]):
                """Capture the request-local evidence trace without global state."""
                evidence_trace.update(trace)

            async def run_gpt_stream():
                """Run the blocking GPT stream in a thread, feeding sentences to the queue."""
                result = await loop.run_in_executor(
                    None,
                    lambda: self.tutor.stream_rag_tutoring(
                        chord_results=chord_results,
                        rag_context=rag_context,
                        websocket_callback=sync_stream_callback,
                        user_question=user_question,
                        trace_callback=sync_trace_callback,
                    )
                )
                # Signal end of stream
                await sentence_queue.put(None)
                return result

            # Start GPT stream in background
            gpt_task = asyncio.create_task(run_gpt_stream())

            # Consume sentences: send text immediately, then TTS audio sequentially
            full_response = ""
            while True:
                sentence = await sentence_queue.get()
                if sentence is None:
                    break

                full_response += sentence + " "

                # Send text chunk for immediate display
                await self.send_message(client_id, {
                    "type": "text_chunk",
                    "text": sentence
                })

                # Send TTS audio for this sentence (awaited = no overlap)
                await self.send_text_chunk(client_id, sentence)

            # Wait for GPT task to finish
            gpt_result = await gpt_task

            complete_message = {
                "type": "complete",
                "full_response": gpt_result or full_response.strip()
            }
            if os.getenv("HORIZONJAM_DEBUG_TRACE", "0").lower() in {"1", "true", "yes"}:
                complete_message["evidence_trace"] = evidence_trace
            await self.send_message(client_id, complete_message)

            print(f"Completed streaming analysis for client {client_id}")

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"Error: {error_msg}")
            await self.send_error(client_id, error_msg)

# Global WebSocket manager
manager = TutorWebSocketManager()

@app.get("/")
async def get_tutor_client():
    """Serve the tutor client interface."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>ChordAI Tutor with Live TTS</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-section {
            margin-bottom: 30px;
            padding: 20px;
            border: 2px dashed #3498db;
            border-radius: 10px;
            text-align: center;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .primary-btn {
            background-color: #3498db;
            color: white;
        }
        .primary-btn:hover {
            background-color: #2980b9;
        }
        .secondary-btn {
            background-color: #95a5a6;
            color: white;
        }
        .secondary-btn:hover {
            background-color: #7f8c8d;
        }
        .status {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.info {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .chord-analysis {
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .rag-context {
            background-color: #f0f8e8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #4caf50;
        }
        .tutoring-text {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
            font-family: 'Georgia', serif;
            line-height: 1.6;
        }
        .full-response {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 15px 0;
            border: 1px solid #dee2e6;
        }
        .chord-tabs {
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
            font-family: 'Courier New', monospace;
        }
        .chord-timeline {
            background-color: #f0f0f8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #6f42c1;
        }
        .chord-item {
            display: inline-block;
            margin: 5px 10px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.8);
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .chord-time {
            font-size: 0.9em;
            color: #666;
            font-weight: bold;
        }
        .chord-name {
            font-size: 1.1em;
            color: #333;
            font-weight: bold;
        }
        .tab-notation {
            font-family: 'Courier New', monospace;
            background: #f8f8f8;
            padding: 10px;
            border-radius: 3px;
            margin: 5px 0;
            white-space: pre;
            overflow-x: auto;
        }
        .question-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        #audioPlayer {
            width: 100%;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎸 ChordAI Tutor with Live TTS</h1>
        
        <div class="upload-section">
            <h3>Upload Audio File</h3>
            <input type="file" id="audioFile" accept=".wav,.mp3,.m4a" />
            <br><br>
            <input type="text" id="questionInput" class="question-input" 
                   placeholder="Optional: Ask a specific question about the music..." />
        </div>
        
        <div class="controls">
            <button id="analyzeBtn" class="primary-btn">🎵 Analyze & Stream TTS</button>
            <button id="stopBtn" class="secondary-btn" disabled>⏹️ Stop Audio</button>
            <button id="clearBtn" class="secondary-btn">🗑️ Clear</button>
        </div>
        
        <div id="status"></div>
        <div id="chordAnalysis"></div>
        <div id="ragContext"></div>
        <div id="chordTabs"></div>
        <div id="chordTimeline"></div>
        <div id="tutoringText"></div>
        <div id="fullResponse"></div>
        
        <audio id="audioPlayer" controls style="display: none;"></audio>
    </div>

    <script>
        let ws = null;
        let audioContext = null;
        let currentAudioSource = null;
        let audioQueue = [];
        let isPlaying = false;
        
        // Initialize audio context
        async function initAudioContext() {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
        }
        
        // Play audio buffer
        async function playAudioBuffer(audioData) {
            try {
                await initAudioContext();
                const audioBuffer = await audioContext.decodeAudioData(audioData);
                
                // Stop current audio if playing
                if (currentAudioSource) {
                    currentAudioSource.stop();
                }
                
                // Create and play new audio source
                currentAudioSource = audioContext.createBufferSource();
                currentAudioSource.buffer = audioBuffer;
                currentAudioSource.connect(audioContext.destination);
                currentAudioSource.start();
                
                isPlaying = true;
                document.getElementById('stopBtn').disabled = false;
                
                currentAudioSource.onended = () => {
                    isPlaying = false;
                    currentAudioSource = null;
                    
                    // Play next audio in queue
                    if (audioQueue.length > 0) {
                        const nextAudio = audioQueue.shift();
                        playAudioBuffer(nextAudio);
                    } else {
                        document.getElementById('stopBtn').disabled = true;
                    }
                };
                
            } catch (error) {
                console.error('Error playing audio:', error);
                showStatus('Error playing audio: ' + error.message, 'error');
            }
        }
        
        // WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/tutor`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                showStatus('Connected to tutor server', 'info');
            };
            
            ws.onmessage = function(event) {
                if (event.data instanceof Blob) {
                    // Audio data received
                    event.data.arrayBuffer().then(audioData => {
                        if (isPlaying) {
                            // Queue audio if currently playing
                            audioQueue.push(audioData);
                        } else {
                            // Play immediately
                            playAudioBuffer(audioData);
                        }
                    });
                } else {
                    // JSON message received
                    try {
                        const message = JSON.parse(event.data);
                        handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                showStatus('Disconnected from server', 'error');
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                showStatus('Connection error', 'error');
            };
        }
        
        // Handle WebSocket messages
        function handleMessage(message) {
            switch (message.type) {
                case 'status':
                    showStatus(message.message, 'info');
                    break;
                case 'error':
                    showStatus(message.message, 'error');
                    break;
                case 'chord_analysis':
                    displayChordAnalysis(message.data);
                    displayChordTabs(message.data);
                    displayChordTimeline(message.data);
                    break;
                case 'rag_context':
                    displayRAGContext(message.data);
                    break;
                case 'text_chunk':
                    displayTextChunk(message.text);
                    break;
                case 'complete':
                    showStatus('Analysis complete! 🎉', 'info');
                    displayFullResponse(message.full_response);
                    break;
            }
        }
        
        // Show status message
        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        // Display chord analysis results
        function displayChordAnalysis(analysis) {
            const analysisDiv = document.getElementById('chordAnalysis');
            const summary = analysis.analysis_summary || {};
            const chordEvents = analysis.chord_events || [];
            
            // Parse analysis data from core pipeline
            const bpm = summary.bpm || (analysis.tempo || analysis.bpm) || 'Unknown';
            const key = summary.detected_key || 'Unknown';
            const accuracy = summary.estimated_accuracy_percent || summary.estimated_accuracy || 'N/A';
            const totalEvents = summary.total_chord_events || chordEvents.length;
            
            // Get unique chords for display
            const uniqueChords = [...new Set(chordEvents.map(event => event.chord || event.chord_symbol).filter(chord => chord && chord !== 'N'))];
            const progression = summary.chord_progression || uniqueChords.join(' - ') || 'No progression detected';
            
            // Create display matching core pipeline format
            analysisDiv.innerHTML = `
                <div class="chord-analysis">
                    <div class="analysis-header">
                        <h3>🎵 HorizonJam Pipeline - Chord Analysis Results</h3>
                    </div>
                    
                    <div class="pipeline-section" style="margin: 15px 0; padding: 15px; background: #f0f8ff; border-radius: 8px; border-left: 4px solid #007bff;">
                        <h4>📊 1. Tempo & Key Detection</h4>
                        <div class="detection-results">
                            <div class="detection-item" style="margin: 8px 0;">
                                <span class="label" style="font-weight: bold;">🎼 Tempo Detection:</span>
                                <span class="value">${typeof bpm === 'number' ? bpm.toFixed(1) : bpm} BPM</span>
                            </div>
                            <div class="detection-item" style="margin: 8px 0;">
                                <span class="label" style="font-weight: bold;">🎹 Key Detection:</span>
                                <span class="value">${key} detected</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="pipeline-section" style="margin: 15px 0; padding: 15px; background: #f0f8e8; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h4>🎸 2. Chord Detection Results</h4>
                        <div class="chord-results">
                            <div class="chord-stats">
                                <div class="stat-item" style="margin: 5px 0;">${totalEvents} chord events detected with precise timing</div>
                                <div class="stat-item" style="margin: 5px 0;">${uniqueChords.length} unique chords: ${uniqueChords.join(', ')}</div>
                                <div class="stat-item" style="margin: 5px 0;">Progression: ${progression}</div>
                                <div class="stat-item" style="margin: 5px 0;">${accuracy}% estimated accuracy</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="pipeline-section" style="margin: 15px 0; padding: 15px; background: #fff8e1; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <h4>🎸 3. Guitar Tab Generation</h4>
                        <div class="tab-generation-status">
                            <div class="status-item" style="margin: 5px 0;">Enhanced guitar tabs generated for all ${uniqueChords.length} unique chords</div>
                            <div class="status-item" style="margin: 5px 0;">Includes difficulty levels, fret positions, and ASCII tab notation</div>
                            <div class="status-item" style="margin: 5px 0;">Database-driven with realistic fingering patterns</div>
                        </div>
                    </div>
                </div>
            `;
            
            console.log('✅ Chord analysis displayed using core pipeline format');
            console.log('📊 Analysis data:', {
                bpm: bpm,
                key: key,
                totalEvents: totalEvents,
                uniqueChords: uniqueChords,
                accuracy: accuracy
            });
        }
        
        // Display chord tabs
        function displayChordTabs(analysis) {
            const tabsDiv = document.getElementById('chordTabs');
            const guitarTabs = analysis.guitar_tabs || [];
            const chordEvents = analysis.chord_events || [];
            
            console.log('🎸 Frontend received guitar tabs:', guitarTabs);
            console.log('🎵 Frontend received chord events:', chordEvents);
            
            if (guitarTabs.length === 0 && chordEvents.length === 0) {
                tabsDiv.innerHTML = '<div style="padding: 15px; color: #666;">No guitar tabs available</div>';
                return;
            }
            
            let tabsHtml = `
                <div class="chord-tabs">
                    <h3>🎸 Guitar Chord Tabs (${guitarTabs.length} Unique Chords)</h3>
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 15px;">Enhanced chord tabs with difficulty levels and fret positions</div>
            `;
            
            // Use backend-generated guitar tabs if available
            if (guitarTabs.length > 0) {
                guitarTabs.forEach(tab => {
                    const difficultyColor = tab.difficulty.includes('Beginner') ? '#007bff' : 
                                           tab.difficulty.includes('Easy') ? '#28a745' :
                                           tab.difficulty.includes('Intermediate') ? '#ffc107' : '#dc3545';
                    
                    tabsHtml += `
                        <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <h4 style="margin: 0; color: #2c3e50;">[GUITAR] ${tab.chord} Chord</h4>
                                <div style="font-size: 0.8em; color: #666;">
                                    <span style="background: ${difficultyColor}; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">
                                        ${tab.difficulty}
                                    </span>
                                    <span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">
                                        ${tab.compact_notation}
                                    </span>
                                </div>
                            </div>
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 8px;">
                                [DATASET] Found in dataset: ${tab.dataset_occurrences} times
                            </div>
                            <div class="tab-notation" style="background: #ffffff; border: 1px solid #dee2e6; padding: 10px; font-family: monospace; white-space: pre-line;">${tab.full_tab}</div>
                        </div>
                    `;
                });
            } else {
                // Fallback to frontend-generated tabs
                const uniqueChords = [...new Set(chordEvents.map(event => event.chord_symbol).filter(chord => chord && chord !== 'N'))];
                
                uniqueChords.forEach(chord => {
                    const chordInfo = getChordInfo(chord);
                    const tabNotation = generateEnhancedChordTab(chord);
                    
                    tabsHtml += `
                        <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <h4 style="margin: 0; color: #2c3e50;">[GUITAR] ${chord} Chord (Fallback)</h4>
                                <div style="font-size: 0.8em; color: #666;">
                                    <span style="background: ${chordInfo.difficultyColor}; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">
                                        ${chordInfo.difficulty}
                                    </span>
                                    <span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">
                                        ${chordInfo.compact}
                                    </span>
                                </div>
                            </div>
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 8px;">
                                [DATASET] Found in dataset: ${chordInfo.datasetCount} times
                            </div>
                            <div class="tab-notation" style="background: #ffffff; border: 1px solid #dee2e6; padding: 10px; font-family: monospace; white-space: pre-line;">${tabNotation}</div>
                        </div>
                    `;
                });
            }
            
            tabsHtml += '</div>';
            tabsDiv.innerHTML = tabsHtml;
        }
        
        // Display chord timeline
        function displayChordTimeline(analysis) {
            const timelineDiv = document.getElementById('chordTimeline');
            const chordEvents = analysis.chord_events || [];
            
            if (chordEvents.length === 0) {
                timelineDiv.innerHTML = '';
                return;
            }
            
            let timelineHtml = `
                <div class="chord-timeline">
                    <h3>⏱️ Chord Event Detection (Distinct Plays)</h3>
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 15px;">Detailed timeline of each chord event with precise timing</div>
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; background: #f8f9fa;">
            `;
            
            let playNumber = 1;
            chordEvents.forEach((event, index) => {
                if (event.chord_symbol && event.chord_symbol !== 'N') {
                    const startTime = event.start_time ? event.start_time.toFixed(2) : '0.00';
                    const endTime = event.end_time ? event.end_time.toFixed(2) : '0.00';
                    const duration = event.end_time && event.start_time ? (event.end_time - event.start_time).toFixed(1) : '0.0';
                    
                    timelineHtml += `
                        <div style="display: flex; align-items: center; padding: 8px; margin: 5px 0; background: white; border-radius: 4px; border-left: 3px solid #6f42c1;">
                            <div style="min-width: 40px; font-weight: bold; color: #6f42c1;">${playNumber}.</div>
                            <div style="flex: 1;">
                                <span style="font-weight: bold; color: #2c3e50;">[${startTime} - ${endTime}] → ${event.chord_symbol}</span>
                                <span style="color: #666; margin-left: 10px;">(play #${playNumber}) (${duration}s)</span>
                            </div>
                        </div>
                    `;
                    playNumber++;
                }
            });
            
            timelineHtml += `
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: #e8f5e8; border-radius: 5px; border-left: 4px solid #28a745;">
                        <strong>[SUMMARY]</strong> Detected ${playNumber - 1} chord events in key of ${(analysis.analysis_summary && analysis.analysis_summary.detected_key) || 'Unknown'}
                    </div>
                </div>
            `;
            timelineDiv.innerHTML = timelineHtml;
        }
        
        // Get chord information (difficulty, compact notation, etc.)
         function getChordInfo(chord) {
             const chordData = {
                 'E': { difficulty: 'Easy (Level 2)', difficultyColor: '#28a745', compact: '022454', datasetCount: 6 },
                 'Bsus4': { difficulty: 'Advanced (Level 4)', difficultyColor: '#dc3545', compact: 'x24452', datasetCount: 30 },
                 'Esus4': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: '022200', datasetCount: 30 },
                 'B': { difficulty: 'Advanced (Level 4)', difficultyColor: '#dc3545', compact: 'x24442', datasetCount: 50 },
                 'C': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: 'x32010', datasetCount: 45 },
                 'G': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: '320003', datasetCount: 40 },
                 'Am': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: 'x02210', datasetCount: 35 },
                 'F': { difficulty: 'Intermediate (Level 3)', difficultyColor: '#ffc107', compact: '133211', datasetCount: 25 },
                 'D': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: 'xx0232', datasetCount: 38 },
                 'Em': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: '022000', datasetCount: 42 },
                 'A': { difficulty: 'Beginner (Level 1)', difficultyColor: '#007bff', compact: 'x02220', datasetCount: 40 }
             };
             
             const baseChord = chord.replace(/[0-9]/g, '').replace(/maj|min|dim|aug/g, '');
             return chordData[baseChord] || chordData[chord] || {
                 difficulty: 'Unknown (Level ?)', 
                 difficultyColor: '#6c757d', 
                 compact: 'xxxxxx', 
                 datasetCount: 0
             };
         }
         
         // Generate enhanced chord tab notation
          function generateEnhancedChordTab(chord) {
              const chordTabs = {
                  'E': 'E |--0--\nA |--2--\nD |--2--\nG |--4--\nB |--5--\nE |--4--',
                  'Bsus4': 'E |--x--\nA |--2--\nD |--4--\nG |--4--\nB |--5--\nE |--2--',
                  'Esus4': 'E |--0--\nA |--2--\nD |--2--\nG |--2--\nB |--0--\nE |--0--',
                  'B': 'E |--x--\nA |--2--\nD |--4--\nG |--4--\nB |--4--\nE |--2--',
                  'C': 'E |--0--\nA |--1--\nD |--0--\nG |--2--\nB |--3--\nE |-----|',
                  'G': 'E |--3--\nA |--0--\nD |--0--\nG |--0--\nB |--2--\nE |--3--|',
                  'Am': 'E |--0--\nA |--1--\nD |--2--\nG |--2--\nB |--0--\nE |-----|',
                  'F': 'E |--1--\nA |--1--\nD |--2--\nG |--3--\nB |--3--\nE |--1--|',
                  'D': 'E |--2--\nA |--3--\nD |--2--\nG |--0--\nB |-----\nE |-----|',
                  'Em': 'E |--0--\nA |--0--\nD |--0--\nG |--2--\nB |--2--\nE |--0--|',
                  'A': 'E |--0--\nA |--2--\nD |--2--\nG |--2--\nB |--0--\nE |-----|'
              };
              
              const baseChord = chord.replace(/[0-9]/g, '').replace(/maj|min|dim|aug/g, '');
              return chordTabs[baseChord] || chordTabs[chord] || `E |-----\nA |-----\nD |-----\nG |-----\nB |-----\nE |-----\n(${chord})`;
          }
        
        // Display RAG context information
        function displayRAGContext(ragData) {
            const ragDiv = document.getElementById('ragContext');
            const contexts = ragData.contexts || [];
            const totalDocs = ragData.total_docs || contexts.length;
            const query = ragData.query || 'guitar chord analysis theory practice tips';
            
            let contextHtml = `
                <div class="rag-context" style="margin: 15px 0; padding: 15px; background: #f0f4ff; border-radius: 8px; border-left: 4px solid #6f42c1;">
                    <h3>🤖 RAG-Enhanced Tutoring System</h3>
                    
                    <div class="pipeline-section" style="margin: 10px 0;">
                        <h4>4. RAG Context Retrieval:</h4>
                        <div class="rag-stats">
                            <div class="stat-item" style="margin: 5px 0;">Unified RAG System initialized with 3,444 documents</div>
                            <div class="stat-item" style="margin: 5px 0;"><strong>Query:</strong> "${query}"</div>
                            <div class="stat-item" style="margin: 5px 0;">${totalDocs} relevant results found from music theory database</div>
                        </div>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <strong>📚 Retrieved Context:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px; background: #ffffff; padding: 10px; border-radius: 5px;">
            `;
            
            contexts.slice(0, 3).forEach((context, index) => {
                contextHtml += `
                    <li style="margin: 8px 0; padding: 5px; border-left: 2px solid #6f42c1;">
                        <strong>Context ${index + 1}:</strong> ${context.substring(0, 200)}${context.length > 200 ? '...' : ''}
                        <div style="font-size: 0.9em; color: #666; margin-top: 3px;">Retrieved from music theory knowledge base</div>
                    </li>
                `;
            });
            
            contextHtml += `
                        </ul>
                    </div>
                </div>
            `;
            ragDiv.innerHTML = contextHtml;
            
            console.log('✅ RAG-Enhanced Tutoring System context displayed');
        }
        
        // Display streaming text chunks
        function displayTextChunk(text) {
            const textDiv = document.getElementById('tutoringText');
            
            if (!textDiv.innerHTML.includes('tutoring-text')) {
                textDiv.innerHTML = `
                    <div class="tutoring-text">
                        <h3>🎓 Live Tutoring Explanation</h3>
                        <div id="streamingContent"></div>
                    </div>
                `;
            }
            
            const contentDiv = document.getElementById('streamingContent');
            contentDiv.innerHTML += text + ' ';
            
            // Auto-scroll to bottom
            contentDiv.scrollTop = contentDiv.scrollHeight;
        }
        
        // Display full response when complete
        function displayFullResponse(response) {
            const responseDiv = document.getElementById('fullResponse');
            responseDiv.innerHTML = `
                <div class="full-response" style="margin: 15px 0; padding: 15px; background: #f8fff8; border-radius: 8px; border-left: 4px solid #28a745;">
                    <div class="pipeline-section">
                        <h4>5. AI Tutoring Response:</h4>
                        <div class="tutoring-stats" style="margin: 10px 0;">
                            <div class="stat-item" style="margin: 5px 0;">OpenAI GPT integration active</div>
                            <div class="stat-item" style="margin: 5px 0;">Streaming tutoring explanations generated</div>
                            <div class="stat-item" style="margin: 5px 0;">Live TTS integration attempted (WebSocket connection status varies)</div>
                        </div>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <strong>🎸 Complete Music Tutoring Response:</strong>
                        <div style="background: #ffffff; padding: 15px; border-radius: 8px; line-height: 1.6; margin-top: 10px; border: 1px solid #e0e0e0;">
                            ${response.replace(/\\n/g, '<br>')}
                        </div>
                    </div>
                </div>
            `;
            
            // Display server status after tutoring response
            displayServerStatus();
            
            console.log('✅ AI Tutoring Response displayed as part of RAG-Enhanced system');
        }
        
        function displayServerStatus() {
            // Create or update server status section
            let statusDiv = document.getElementById('server-status');
            if (!statusDiv) {
                statusDiv = document.createElement('div');
                statusDiv.id = 'server-status';
                document.getElementById('fullResponse').parentNode.appendChild(statusDiv);
            }
            
            const currentTime = new Date().toLocaleTimeString();
            const wsStatus = ws && ws.readyState === WebSocket.OPEN ? 'Connected' : 'Disconnected';
            
            statusDiv.innerHTML = `
                <div class="server-status" style="margin: 15px 0; padding: 15px; background: #f0f0f0; border-radius: 8px; border-left: 4px solid #6c757d;">
                    <h3>🌐 Server Status</h3>
                    <div class="status-section" style="margin: 10px 0;">
                        <div class="status-item" style="margin: 5px 0;">✅ ChordAI + RAG-Enhanced Music Tutor: Active</div>
                        <div class="status-item" style="margin: 5px 0;">🔗 WebSocket Connection: ${wsStatus}</div>
                        <div class="status-item" style="margin: 5px 0;">🎵 HorizonJam Pipeline: Ready</div>
                        <div class="status-item" style="margin: 5px 0;">🤖 OpenAI GPT Integration: Active</div>
                        <div class="status-item" style="margin: 5px 0;">📚 Unified RAG System: Initialized (3,444 documents)</div>
                        <div class="status-item" style="margin: 5px 0;">⏰ Last Update: ${currentTime}</div>
                    </div>
                </div>
            `;
            
            console.log('✅ Server status displayed');
        }
        
        // Analyze audio file
        async function analyzeAudio() {
            const fileInput = document.getElementById('audioFile');
            const questionInput = document.getElementById('questionInput');
            
            if (!fileInput.files[0]) {
                showStatus('Please select an audio file', 'error');
                return;
            }
            
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                showStatus('Not connected to server', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('audio_file', fileInput.files[0]);
            if (questionInput.value.trim()) {
                formData.append('question', questionInput.value.trim());
            }
            
            try {
                showStatus('Uploading audio file...', 'info');
                
                const response = await fetch('/upload-audio', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Send analysis request via WebSocket
                    ws.send(JSON.stringify({
                        type: 'analyze',
                        file_path: result.file_path,
                        question: questionInput.value.trim() || null
                    }));
                } else {
                    showStatus('Upload failed: ' + result.error, 'error');
                }
                
            } catch (error) {
                showStatus('Upload error: ' + error.message, 'error');
            }
        }
        
        // Stop audio playback
        function stopAudio() {
            if (currentAudioSource) {
                currentAudioSource.stop();
                currentAudioSource = null;
            }
            audioQueue = [];
            isPlaying = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        // Clear interface
        function clearInterface() {
            document.getElementById('audioFile').value = '';
            document.getElementById('questionInput').value = '';
            document.getElementById('status').innerHTML = '';
            document.getElementById('chordAnalysis').innerHTML = '';
            document.getElementById('ragContext').innerHTML = '';
            document.getElementById('chordTabs').innerHTML = '';
            document.getElementById('chordTimeline').innerHTML = '';
            document.getElementById('tutoringText').innerHTML = '';
            document.getElementById('fullResponse').innerHTML = '';
            stopAudio();
        }
        
        // Event listeners
        document.getElementById('analyzeBtn').addEventListener('click', analyzeAudio);
        document.getElementById('stopBtn').addEventListener('click', stopAudio);
        document.getElementById('clearBtn').addEventListener('click', clearInterface);
        
        // Initialize
        connectWebSocket();
    </script>
</body>
</html>
    """
    return JSONResponse(content={"message": "ChordAI Tutor backend running. Use Next.js frontend at / to interact via /upload-audio and /ws/tutor."})

@app.post("/upload-audio")
async def upload_audio(audio_file: UploadFile = File(...), question: Optional[str] = Form(None)):
    """Accept any audio format ffmpeg can decode; normalize to mono 44.1kHz WAV
    so the downstream pipeline always sees the format it expects."""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "chordai_tutor"
        temp_dir.mkdir(exist_ok=True)

        # Sanitize filename — strip any path components a client may have included
        # (path-traversal hardening + handles browser-recorded blobs with relative names).
        safe_name = Path(audio_file.filename or "upload").name or "upload"
        file_path = temp_dir / f"upload_{safe_name}"

        with open(file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        original_ext = file_path.suffix.lower()
        converted = False
        if original_ext not in (".wav", ".wave"):
            try:
                import librosa
                import soundfile as sf
                import numpy as np

                # librosa.load goes through audioread → ffmpeg for webm/mp4/mp3/etc.
                y, sr = librosa.load(str(file_path), sr=44100, mono=True)

                if len(y) < int(sr * 0.5):
                    return {
                        "success": False,
                        "error": "Recording is too short (under 0.5s).",
                    }
                rms = float(np.sqrt(np.mean(y ** 2)))
                if rms < 1e-3:  # ~ -60 dBFS — effectively silent
                    return {
                        "success": False,
                        "error": "Recording is silent — check your microphone input level.",
                    }

                wav_path = file_path.with_suffix(".wav")
                sf.write(str(wav_path), y, sr, subtype="PCM_16")
                # Drop the original (best-effort)
                try:
                    file_path.unlink()
                except Exception:
                    pass
                file_path = wav_path
                converted = True
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Audio conversion failed ({e}). Confirm ffmpeg is installed.",
                }

        # Phase 3 logging: surface the audio facts at the upload boundary so
        # the mic-recording trail is greppable end-to-end.
        try:
            final_size = file_path.stat().st_size
        except OSError:
            final_size = 0
        print(
            f"[upload] filename={safe_name!r} bytes={final_size} "
            f"converted_from={original_ext if converted else 'native'} "
            f"final_path={file_path.name}",
            flush=True,
        )

        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file_path.name,
            "converted_from": original_ext if converted else None,
        }

    except Exception as e:
        print(f"[upload] FAILED: {e}", flush=True)
        return {"success": False, "error": str(e)}

@app.websocket("/ws/tutor")
async def websocket_tutor_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming tutor responses."""
    client_id = f"client_{id(websocket)}"
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "analyze":
                file_path = message.get("file_path")
                question = message.get("question")
                
                if file_path and os.path.exists(file_path):
                    # Start streaming analysis
                    await manager.analyze_audio_streaming(client_id, file_path, question)
                else:
                    await manager.send_error(client_id, "Audio file not found")
                    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

if __name__ == "__main__":
    print("🎸 Starting ChordAI Tutor WebSocket Relay with Streaming TTS")
    print("📡 Server will be available at: http://localhost:8001")
    print("🔊 Make sure TTS server is running on port 5000")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
