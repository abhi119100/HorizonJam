import os
import tempfile
import json
import requests
import streamlit as st
import streamlit.components.v1
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any

BACKEND_URL = os.getenv("CHORDAI_API_URL", "http://localhost:8000")

def display_chord_timeline(chord_events):
    """Display an interactive chord timeline."""
    
    # Prepare data for timeline
    timeline_data = []
    for event in chord_events:
        timeline_data.append({
            "Chord": event.get("chord", "Unknown"),
            "Start": event.get("start_time_seconds", 0),
            "End": event.get("start_time_seconds", 0) + event.get("duration_seconds", 0),
            "Duration": event.get("duration_seconds", 0),
            "Confidence": event.get("confidence", 0)
        })
    
    df = pd.DataFrame(timeline_data)
    
    if not df.empty:
        # Create timeline chart
        fig = go.Figure()
        
        for i, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["Start"], row["End"]],
                y=[i, i],
                mode="lines+markers",
                name=row["Chord"],
                line=dict(width=8),
                marker=dict(size=10),
                hovertemplate=f"<b>{row['Chord']}</b><br>" +
                            f"Start: {row['Start']:.2f}s<br>" +
                            f"Duration: {row['Duration']:.2f}s<br>" +
                            f"Confidence: {row['Confidence']:.2f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="Chord Timeline",
            xaxis_title="Time (seconds)",
            yaxis_title="Chord Events",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.dataframe(df, use_container_width=True)

def display_chord_tabs(chord_tabs):
    """Display guitar chord tabs."""
    
    # Handle case where chord_tabs might be a list instead of dict
    if isinstance(chord_tabs, list):
        if not chord_tabs:
            st.info("No chord tabs available.")
            return
        # Convert list to dict if needed
        chord_tabs_dict = {}
        for item in chord_tabs:
            if isinstance(item, dict) and 'chord' in item:
                chord_name = item.get('chord', 'Unknown')
                chord_tabs_dict[chord_name] = item
        chord_tabs = chord_tabs_dict
    
    if not chord_tabs:
        st.info("No chord tabs available.")
        return
    
    for chord_name, tab_info in chord_tabs.items():
        with st.expander(f"🎸 {chord_name} Chord"):
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Fingering:**")
                fingering = tab_info.get("fingering", "Not available")
                st.code(fingering, language="text")
                
                difficulty = tab_info.get("difficulty", "Unknown")
                st.write(f"**Difficulty:** {difficulty}")
            
            with col2:
                st.write("**Details:**")
                occurrences = tab_info.get("dataset_occurrences", 0)
                st.write(f"Dataset occurrences: {occurrences}")
                
                compact = tab_info.get("compact_notation", "Not available")
                st.write(f"Compact notation: {compact}")

def add_tts_controls(text):
    """Add TTS controls for text content."""
    
    # Clean the text for JavaScript
    clean_text = text.replace('`', "'").replace('"', '\"').replace('\n', ' ').replace('\r', '')
    
    st.components.v1.html(f"""
        <div style="display: flex; gap: 10px; margin: 10px 0;">
            <button onclick="startTTS()" style="
                background: #ff6b6b; color: white; border: none; padding: 8px 16px; 
                border-radius: 5px; cursor: pointer; font-size: 14px;
            ">🔊 Read Aloud</button>
            
            <button onclick="stopTTS()" style="
                background: #4ecdc4; color: white; border: none; padding: 8px 16px; 
                border-radius: 5px; cursor: pointer; font-size: 14px;
            ">⏹️ Stop</button>
            
            <span id="ttsStatus" style="
                padding: 8px 16px; background: #f8f9fa; border-radius: 5px; 
                font-size: 14px; color: #666;
            ">🎧 TTS Ready</span>
        </div>
        
        <script>
            window.currentUtterance = null;
            
            function startTTS() {{
                var synth = window.speechSynthesis;
                var utter = new window.SpeechSynthesisUtterance(`{clean_text}`);
                utter.rate = 0.9;
                utter.pitch = 1;
                utter.volume = 0.8;
                
                var voices = synth.getVoices();
                var englishVoice = voices.find(v => v.lang.startsWith('en'));
                if (englishVoice) {{
                    utter.voice = englishVoice;
                }}
                utter.lang = 'en-US';
                
                // Stop any ongoing speech
                if (synth.speaking) {{
                    synth.cancel();
                }}
                
                window.currentUtterance = utter;
                
                document.getElementById('ttsStatus').textContent = '🔊 Speaking...';
                document.getElementById('ttsStatus').style.background = '#e3f2fd';
                
                utter.onstart = function() {{
                    console.log('TTS started');
                }};
                utter.onend = function() {{
                    console.log('TTS finished');
                    window.currentUtterance = null;
                    document.getElementById('ttsStatus').textContent = '✅ Finished';
                    document.getElementById('ttsStatus').style.background = '#e8f5e8';
                }};
                utter.onerror = function(event) {{
                    console.error('TTS error:', event.error);
                    window.currentUtterance = null;
                    document.getElementById('ttsStatus').textContent = '❌ TTS Error';
                    document.getElementById('ttsStatus').style.background = '#ffebee';
                }};
                
                synth.speak(utter);
            }}
            
            function stopTTS() {{
                if (window.speechSynthesis) {{
                    if (window.currentUtterance) {{
                        window.currentUtterance.onend = null;
                        window.currentUtterance.onerror = null;
                        window.currentUtterance = null;
                    }}
                    
                    window.speechSynthesis.cancel();
                    
                    document.getElementById('ttsStatus').textContent = '🔇 Stopped';
                    document.getElementById('ttsStatus').style.background = '#fff3e0';
                    
                    console.log('TTS stopped');
                }}
            }}
        </script>
    """, height=80)

def display_enhanced_results(data: Dict[str, Any]):
    """Display enhanced chord analysis results with improved visualization."""
    
    st.success("✅ Analysis Complete!")
    
    # Analysis Summary Cards
    analysis = data.get("analysis", {})
    if analysis:
        st.subheader("🎼 Analysis Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="analysis-card">
                <h3>🎼 Key</h3>
                <h2>{analysis.get('detected_key', 'Unknown')}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="analysis-card">
                <h3>🎵 Tempo</h3>
                <h2>{analysis.get('tempo_bpm', 0):.0f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="analysis-card">
                <h3>🎯 Accuracy</h3>
                <h2>{analysis.get('estimated_accuracy', 0):.0f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="analysis-card">
                <h3>🎸 Chords</h3>
                <h2>{analysis.get('total_chord_events', 0)}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # Chord Progression Display
    chord_progression = analysis.get('chord_progression', 'Unknown')
    if chord_progression and chord_progression != 'Unknown':
        st.markdown(f"""
        <div class="chord-progression">
            {chord_progression}
        </div>
        """, unsafe_allow_html=True)
    
    # Chord Timeline
    chord_events = data.get("chord_events", [])
    if chord_events:
        st.subheader("📈 Chord Timeline")
        display_chord_timeline(chord_events)
    
    # Guitar Tabs
    chord_tabs = data.get("chord_tabs", {})
    if chord_tabs:
        st.subheader("🎸 Guitar Tabs")
        display_chord_tabs(chord_tabs)
    
    # Conversational Tutoring Response
    tutoring_response = data.get("tutoring_response", "")
    if tutoring_response:
        st.subheader("👨‍🏫 Music Theory Tutoring")
        st.markdown(f"""
        <div class="tutor-response">
            {tutoring_response}
        </div>
        """, unsafe_allow_html=True)
        
        # Add TTS controls for tutoring response
        add_tts_controls(tutoring_response)
    
    # Audio playback (TTS)
    if data.get("tts_enabled") and data.get("audio_url"):
        st.subheader("🔊 Listen to Explanation")
        audio_url = data["audio_url"]
        if audio_url.startswith("/"):
            full_audio_url = f"{BACKEND_URL}{audio_url}"
        else:
            full_audio_url = audio_url
        st.audio(full_audio_url)
    
    # Debug information
    with st.expander("🔍 Full Analysis Output"):
        st.json(data)

# Enhanced page configuration
st.set_page_config(
    page_title="ChordAI - Music Tutor", 
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .analysis-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .chord-progression {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    .tutor-response {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🎸 ChordAI Music Tutor</h1>', unsafe_allow_html=True)
st.markdown(
    "### 🎵 AI-Powered Chord Detection & Conversational Music Theory Tutoring\n"
    "Upload your guitar recordings for intelligent chord analysis and personalized music theory guidance with RAG-enhanced responses."
)

# Add tabs for different functionalities
tab1, tab2 = st.tabs(["🎵 Chord Analysis", "💬 RAG Chatbot"])

with tab2:
    st.subheader("💬 Music Theory RAG Chatbot")
    st.markdown("Have a conversation with our AI music theory assistant powered by RAG (Retrieval-Augmented Generation).")
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Hello! I'm your AI music theory assistant. Ask me anything about chords, scales, guitar techniques, music theory, or any music-related questions!"
        })
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    
                    # Add TTS controls for existing chat history
                    clean_history_response = message["content"].replace('`', "'").replace('"', '\"').replace('\n', ' ').replace('\r', '')
                    message_id = hash(message["content"]) % 10000  # Create unique ID for each message
                    
                    st.components.v1.html(f"""
                        <div style="display: flex; gap: 8px; margin: 8px 0;">
                            <button id="historyReadBtn_{message_id}" onclick="startHistoryTTS_{message_id}()" style="
                                background: #ff9999; color: white; border: none; padding: 4px 8px; 
                                border-radius: 3px; cursor: pointer; font-size: 11px;
                            ">🔊 Read</button>
                            
                            <button id="historyStopBtn_{message_id}" onclick="stopHistoryTTS_{message_id}()" style="
                                background: #99cccc; color: white; border: none; padding: 4px 8px; 
                                border-radius: 3px; cursor: pointer; font-size: 11px;
                            ">⏹️ Stop</button>
                            
                            <span id="historyStatus_{message_id}" style="
                                padding: 4px 8px; background: #f0f0f0; border-radius: 3px; 
                                font-size: 11px; color: #666;
                            ">🎧 TTS available</span>
                        </div>
                        
                        <script>
                            window.historyUtterance_{message_id} = null;
                            
                            function startHistoryTTS_{message_id}() {{
                                var synth = window.speechSynthesis;
                                var utter = new window.SpeechSynthesisUtterance(`{clean_history_response}`);
                                utter.rate = 0.9;
                                utter.pitch = 1;
                                utter.volume = 0.8;
                                
                                var voices = synth.getVoices();
                                var englishVoice = voices.find(v => v.lang.startsWith('en'));
                                if (englishVoice) {{
                                    utter.voice = englishVoice;
                                }}
                                utter.lang = 'en-US';
                                
                                // Stop any ongoing speech
                                if (synth.speaking) {{
                                    synth.cancel();
                                }}
                                
                                window.historyUtterance_{message_id} = utter;
                                
                                // Update status
                                document.getElementById('historyStatus_{message_id}').textContent = '🔊 Speaking...';
                                document.getElementById('historyStatus_{message_id}').style.background = '#e3f2fd';
                                
                                utter.onstart = function() {{
                                    console.log('History TTS {message_id} started');
                                }};
                                utter.onend = function() {{
                                    console.log('History TTS {message_id} finished');
                                    window.historyUtterance_{message_id} = null;
                                    document.getElementById('historyStatus_{message_id}').textContent = '✅ Finished';
                                    document.getElementById('historyStatus_{message_id}').style.background = '#e8f5e8';
                                }};
                                utter.onerror = function(event) {{
                                    console.error('History TTS {message_id} error:', event.error);
                                    window.historyUtterance_{message_id} = null;
                                    document.getElementById('historyStatus_{message_id}').textContent = '❌ Error';
                                    document.getElementById('historyStatus_{message_id}').style.background = '#ffebee';
                                }};
                                
                                synth.speak(utter);
                            }}
                            
                            function stopHistoryTTS_{message_id}() {{
                                if (window.speechSynthesis) {{
                                    if (window.historyUtterance_{message_id}) {{
                                        window.historyUtterance_{message_id}.onend = null;
                                        window.historyUtterance_{message_id}.onerror = null;
                                        window.historyUtterance_{message_id} = null;
                                    }}
                                    
                                    window.speechSynthesis.cancel();
                                    
                                    document.getElementById('historyStatus_{message_id}').textContent = '🔇 Stopped';
                                    document.getElementById('historyStatus_{message_id}').style.background = '#fff3e0';
                                    
                                    console.log('History TTS {message_id} stopped');
                                }}
                            }}
                        </script>
                    """, height=60)
                    
                    # Show context sources if available
                    if "context" in message:
                        context = message["context"]
                        if context and "context_chunks" in context:
                            chunks = context["context_chunks"]
                            if chunks and len(chunks) > 0:
                                source = chunks[0].get("source", "Unknown")
                                st.caption(f"📚 Source: {source}")
    
    # Chat input
    user_input = st.chat_input("Ask me about music theory, chords, scales, guitar techniques...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get RAG response
        try:
            with st.spinner("🤔 Thinking..."):
                rag_response = requests.post(
                    f"{BACKEND_URL}/rag-query",
                    json={"question": user_input}
                )
            
            if rag_response.status_code == 200:
                rag_data = rag_response.json()
                response_text = rag_data.get("response", "I'm sorry, I couldn't generate a response.")
                context = rag_data.get("context", {})
                
                # Add assistant response to chat history
                assistant_message = {
                    "role": "assistant",
                    "content": response_text
                }
                if context:
                    assistant_message["context"] = context
                
                st.session_state.chat_history.append(assistant_message)
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.write(response_text)
                    
                    # Add live TTS for RAG chatbot responses
                    clean_response = response_text.replace('`', "'").replace('"', '\"').replace('\n', ' ').replace('\r', '')
                    
                    # Auto-TTS for RAG responses
                    st.components.v1.html(f"""
                        <script>
                            // Store reference globally for better control
                            window.currentRagUtterance = null;
                            
                            var synth = window.speechSynthesis;
                            var utter = new window.SpeechSynthesisUtterance(`{clean_response}`);
                            utter.rate = 0.9;  // Slightly slower for better comprehension
                            utter.pitch = 1;   // Normal pitch
                            utter.volume = 0.8; // Slightly lower volume
                            
                            // Set voice to English if available
                            var voices = synth.getVoices();
                            var englishVoice = voices.find(v => v.lang.startsWith('en'));
                            if (englishVoice) {{
                                utter.voice = englishVoice;
                            }}
                            utter.lang = 'en-US';
                            
                            // Stop any ongoing speech completely
                            if (synth.speaking) {{
                                synth.cancel();
                                synth.pause();
                                synth.resume();
                                synth.cancel();
                            }}
                            
                            // Store current utterance reference
                            window.currentRagUtterance = utter;
                            
                            // Add a small delay to ensure the component is loaded
                            setTimeout(function() {{
                                if (synth && !synth.speaking) {{
                                    synth.speak(utter);
                                }}
                            }}, 500);
                            
                            // Add event listeners for debugging
                            utter.onstart = function() {{
                                console.log('RAG Auto-TTS started');
                            }};
                            utter.onend = function() {{
                                console.log('RAG Auto-TTS finished');
                                window.currentRagUtterance = null;
                            }};
                            utter.onerror = function(event) {{
                                console.error('RAG Auto-TTS error:', event.error);
                                window.currentRagUtterance = null;
                            }};
                        </script>
                    """, height=0)
                    
                    # Add manual TTS controls for RAG responses
                    st.components.v1.html(f"""
                        <div style="display: flex; gap: 10px; margin: 10px 0;">
                            <button id="ragReadAloudBtn" onclick="startRagTTS()" style="
                                background: #ff6b6b; color: white; border: none; padding: 6px 12px; 
                                border-radius: 4px; cursor: pointer; font-size: 12px;
                            ">🔊 Read Aloud</button>
                            
                            <button id="ragStopSpeechBtn" onclick="stopRagTTS()" style="
                                background: #4ecdc4; color: white; border: none; padding: 6px 12px; 
                                border-radius: 4px; cursor: pointer; font-size: 12px;
                            ">⏹️ Stop Speech</button>
                            
                            <span id="ragTtsStatus" style="
                                padding: 6px 12px; background: #f8f9fa; border-radius: 4px; 
                                font-size: 12px; color: #666;
                            ">🎧 Auto-TTS enabled</span>
                        </div>
                        
                        <script>
                            function startRagTTS() {{
                                var synth = window.speechSynthesis;
                                var utter = new window.SpeechSynthesisUtterance(`{clean_response}`);
                                utter.rate = 0.9;
                                utter.pitch = 1;
                                utter.volume = 0.8;
                                
                                var voices = synth.getVoices();
                                var englishVoice = voices.find(v => v.lang.startsWith('en'));
                                if (englishVoice) {{
                                    utter.voice = englishVoice;
                                }}
                                utter.lang = 'en-US';
                                
                                // Stop any ongoing speech completely
                                if (synth.speaking) {{
                                    synth.cancel();
                                    synth.pause();
                                    synth.resume();
                                    synth.cancel();
                                }}
                                
                                // Store current utterance reference
                                window.currentRagUtterance = utter;
                                
                                // Update status
                                document.getElementById('ragTtsStatus').textContent = '🔊 Reading aloud...';
                                document.getElementById('ragTtsStatus').style.background = '#e3f2fd';
                                
                                // Add event listeners
                                utter.onstart = function() {{
                                    console.log('RAG Manual TTS started');
                                    document.getElementById('ragTtsStatus').textContent = '🔊 Speaking...';
                                }};
                                utter.onend = function() {{
                                    console.log('RAG Manual TTS finished');
                                    window.currentRagUtterance = null;
                                    document.getElementById('ragTtsStatus').textContent = '✅ Finished reading';
                                    document.getElementById('ragTtsStatus').style.background = '#e8f5e8';
                                }};
                                utter.onerror = function(event) {{
                                    console.error('RAG Manual TTS error:', event.error);
                                    window.currentRagUtterance = null;
                                    document.getElementById('ragTtsStatus').textContent = '❌ TTS Error';
                                    document.getElementById('ragTtsStatus').style.background = '#ffebee';
                                }};
                                
                                // Start speaking
                                if (!synth.speaking) {{
                                    synth.speak(utter);
                                }}
                            }}
                            
                            function stopRagTTS() {{
                                // Force stop all speech synthesis
                                if (window.speechSynthesis) {{
                                    // Cancel any current utterance
                                    if (window.currentRagUtterance) {{
                                        window.currentRagUtterance.onend = null;
                                        window.currentRagUtterance.onerror = null;
                                        window.currentRagUtterance = null;
                                    }}
                                    
                                    // Multiple cancel attempts to ensure stopping
                                    window.speechSynthesis.cancel();
                                    window.speechSynthesis.pause();
                                    window.speechSynthesis.resume();
                                    window.speechSynthesis.cancel();
                                    
                                    // Wait a bit and cancel again to be sure
                                    setTimeout(function() {{
                                        window.speechSynthesis.cancel();
                                    }}, 100);
                                    
                                    console.log('RAG Speech synthesis forcefully stopped');
                                    
                                    // Update status
                                    document.getElementById('ragTtsStatus').textContent = '🔇 Speech stopped';
                                    document.getElementById('ragTtsStatus').style.background = '#fff3e0';
                                }}
                            }}
                        </script>
                    """, height=80)
                    
                    # Show context sources if available
                    if context and "context_chunks" in context:
                        chunks = context["context_chunks"]
                        if chunks and len(chunks) > 0:
                            source = chunks[0].get("source", "Unknown")
                            st.caption(f"📚 Source: {source}")
                
                # Rerun to update the chat display
                st.rerun()
            else:
                error_msg = f"Sorry, I encountered an error: {rag_response.status_code} - {rag_response.text}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.rerun()
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.error(error_msg)
            st.rerun()
    
    # Chat controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = [{
                "role": "assistant",
                "content": "Hello! I'm your AI music theory assistant. Ask me anything about chords, scales, guitar techniques, music theory, or any music-related questions!"
            }]
            st.rerun()
    
    with col2:
        if st.button("🔍 Backend Status", key="status_check"):
            try:
                status_response = requests.get(f"{BACKEND_URL}/")
                if status_response.status_code == 200:
                    st.success(f"✅ Backend is running")
                else:
                    st.warning(f"⚠️ Backend status: {status_response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to backend: {e}")
    
    with col3:
        with st.expander("💡 Example Questions"):
            st.markdown("""
            - What is the C major scale?
            - How do I play a G7 chord?
            - What's the difference between major and minor chords?
            - Can you explain chord progressions?
            - How do I tune my guitar?
            - What are guitar scales and how do I use them?
            """)

with tab1:
    st.subheader("🎵 Enhanced Chord Analysis & Conversational AI Tutoring")
    st.markdown("Upload audio files for intelligent chord detection with RAG-enhanced personalized music theory guidance.")
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Select an audio file", 
            type=["wav", "mp3", "flac"],
            help="Upload guitar recordings for chord analysis"
        )
        
        if uploaded_file is not None:
            st.info(f"📁 **File:** {uploaded_file.name} ({uploaded_file.size} bytes)")
            st.audio(uploaded_file, format='audio/wav')
    
    with col2:
        st.markdown("**⚙️ Analysis Settings**")
        confidence = st.slider("Confidence Threshold", 0.1, 1.0, 0.3, 0.1)
        min_duration = st.slider("Min Chord Duration (s)", 0.01, 0.5, 0.05, 0.01)
        enable_tts = st.checkbox("Enable Text-to-Speech", value=True)
        
        # Custom question input
        st.markdown("**💬 Custom Question**")
        custom_question = st.text_area(
            "Ask about the progression:",
            placeholder="e.g., What scale works for soloing?",
            height=80
        )
    
    analyze_btn = st.button("🔍 Analyze Chords", key="chord_analyze", type="primary")
    
    if analyze_btn:
        if uploaded_file is None:
            st.warning("Please upload an audio file first.")
            st.stop()
    
        # Save to a temporary file because requests needs a real file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
    
        # Enhanced API parameters
        params = {
            "confidence": confidence,
            "min_duration": min_duration,
            "enable_tts": str(enable_tts).lower(),
            "question": custom_question if custom_question else None
        }
    
        try:
            with st.spinner("🎵 Running enhanced chord detection and conversational AI tutoring… this may take a moment"):
                with open(tmp_path, "rb") as f:
                     response = requests.post(f"{BACKEND_URL}/analyze", files={"file": f}, params=params)
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {"error": response.text}
                st.error(f"❌ Analysis failed: {error_data.get('error', 'Unknown error')}")
                st.stop()
    
            data = response.json()
            display_enhanced_results(data)
            
        except Exception as e:
            st.error(f"❌ Request failed: {e}")
            st.stop()
        finally:
            os.remove(tmp_path)
    


def display_chord_timeline(chord_events):
    """Display an interactive chord timeline."""
    
    # Prepare data for timeline
    timeline_data = []
    for event in chord_events:
        timeline_data.append({
            "Chord": event.get("chord", "Unknown"),
            "Start": event.get("start_time_seconds", 0),
            "End": event.get("start_time_seconds", 0) + event.get("duration_seconds", 0),
            "Duration": event.get("duration_seconds", 0),
            "Confidence": event.get("confidence", 0)
        })
    
    df = pd.DataFrame(timeline_data)
    
    if not df.empty:
        # Create timeline chart
        fig = go.Figure()
        
        for i, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["Start"], row["End"]],
                y=[i, i],
                mode="lines+markers",
                name=row["Chord"],
                line=dict(width=8),
                marker=dict(size=10),
                hovertemplate=f"<b>{row['Chord']}</b><br>" +
                            f"Start: {row['Start']:.2f}s<br>" +
                            f"Duration: {row['Duration']:.2f}s<br>" +
                            f"Confidence: {row['Confidence']:.2f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="Chord Timeline",
            xaxis_title="Time (seconds)",
            yaxis_title="Chord Events",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.dataframe(df, use_container_width=True)

def display_chord_tabs_duplicate(chord_tabs):
    """Display guitar chord tabs (duplicate function - should be removed)."""
    
    # Handle case where chord_tabs might be a list instead of dict
    if isinstance(chord_tabs, list):
        if not chord_tabs:
            st.info("No chord tabs available.")
            return
        # Convert list to dict if needed
        chord_tabs_dict = {}
        for item in chord_tabs:
            if isinstance(item, dict) and 'chord' in item:
                chord_name = item.get('chord', 'Unknown')
                chord_tabs_dict[chord_name] = item
        chord_tabs = chord_tabs_dict
    
    if not chord_tabs:
        st.info("No chord tabs available.")
        return
    
    for chord_name, tab_info in chord_tabs.items():
        with st.expander(f"🎸 {chord_name} Chord"):
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Fingering:**")
                fingering = tab_info.get("fingering", "Not available")
                st.code(fingering, language="text")
                
                difficulty = tab_info.get("difficulty", "Unknown")
                st.write(f"**Difficulty:** {difficulty}")
            
            with col2:
                st.write("**Details:**")
                occurrences = tab_info.get("dataset_occurrences", 0)
                st.write(f"Dataset occurrences: {occurrences}")
                
                compact = tab_info.get("compact_notation", "Not available")
                st.write(f"Compact notation: {compact}")

def add_tts_controls(text):
    """Add TTS controls for text content."""
    
    # Clean the text for JavaScript
    clean_text = text.replace('`', "'").replace('"', '\"').replace('\n', ' ').replace('\r', '')
    
    st.components.v1.html(f"""
        <div style="display: flex; gap: 10px; margin: 10px 0;">
            <button onclick="startTTS()" style="
                background: #ff6b6b; color: white; border: none; padding: 8px 16px; 
                border-radius: 5px; cursor: pointer; font-size: 14px;
            ">🔊 Read Aloud</button>
            
            <button onclick="stopTTS()" style="
                background: #4ecdc4; color: white; border: none; padding: 8px 16px; 
                border-radius: 5px; cursor: pointer; font-size: 14px;
            ">⏹️ Stop</button>
            
            <span id="ttsStatus" style="
                padding: 8px 16px; background: #f8f9fa; border-radius: 5px; 
                font-size: 14px; color: #666;
            ">🎧 TTS Ready</span>
        </div>
        
        <script>
            window.currentUtterance = null;
            
            function startTTS() {{
                var synth = window.speechSynthesis;
                var utter = new window.SpeechSynthesisUtterance(`{clean_text}`);
                utter.rate = 0.9;
                utter.pitch = 1;
                utter.volume = 0.8;
                
                var voices = synth.getVoices();
                var englishVoice = voices.find(v => v.lang.startsWith('en'));
                if (englishVoice) {{
                    utter.voice = englishVoice;
                }}
                utter.lang = 'en-US';
                
                // Stop any ongoing speech
                if (synth.speaking) {{
                    synth.cancel();
                }}
                
                window.currentUtterance = utter;
                
                document.getElementById('ttsStatus').textContent = '🔊 Speaking...';
                document.getElementById('ttsStatus').style.background = '#e3f2fd';
                
                utter.onstart = function() {{
                    console.log('TTS started');
                }};
                utter.onend = function() {{
                    console.log('TTS finished');
                    window.currentUtterance = null;
                    document.getElementById('ttsStatus').textContent = '✅ Finished';
                    document.getElementById('ttsStatus').style.background = '#e8f5e8';
                }};
                utter.onerror = function(event) {{
                    console.error('TTS error:', event.error);
                    window.currentUtterance = null;
                    document.getElementById('ttsStatus').textContent = '❌ TTS Error';
                    document.getElementById('ttsStatus').style.background = '#ffebee';
                }};
                
                synth.speak(utter);
            }}
            
            function stopTTS() {{
                if (window.speechSynthesis) {{
                    if (window.currentUtterance) {{
                        window.currentUtterance.onend = null;
                        window.currentUtterance.onerror = null;
                        window.currentUtterance = null;
                    }}
                    
                    window.speechSynthesis.cancel();
                    
                    document.getElementById('ttsStatus').textContent = '🔇 Stopped';
                    document.getElementById('ttsStatus').style.background = '#fff3e0';
                }}
            }}
        </script>
    """, height=80)

# Add footer
st.markdown("---")
st.markdown("© 2025 ChordAI Music Tutor")