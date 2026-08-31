import streamlit as st
import requests
import json
import io
from pathlib import Path
import tempfile
import time
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="HorizonJam",
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
        margin-bottom: 2rem;
    }
    
    .chord-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .analysis-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
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

# API Configuration
API_BASE_URL = "http://localhost:8000"

def main():
    # Header
    st.markdown('<h1 class="main-header">🎸 HorizonJam Music Tutor</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Chord Detection & Music Theory Tutoring")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Settings")
        
        # Analysis parameters
        confidence = st.slider("Confidence Threshold", 0.1, 1.0, 0.3, 0.1)
        min_duration = st.slider("Min Chord Duration (s)", 0.01, 0.5, 0.05, 0.01)
        enable_tts = st.checkbox("Enable Text-to-Speech", value=True)
        
        st.divider()
        
        # Custom question
        st.subheader("💬 Custom Question")
        custom_question = st.text_area(
            "Ask a specific question about the chord progression:",
            placeholder="e.g., What scale should I use for soloing over this progression?"
        )
        
        st.divider()
        
        # RAG Query Section
        st.subheader("🧠 Music Theory Q&A")
        rag_question = st.text_input(
            "Ask about music theory:",
            placeholder="e.g., What are suspended chords?"
        )
        
        if st.button("Ask Music Theory Question"):
            if rag_question:
                with st.spinner("Thinking..."):
                    rag_response = query_rag_system(rag_question)
                    if rag_response:
                        st.success("Answer:")
                        st.write(rag_response.get("response", "No response"))
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎵 Upload Audio File")
        uploaded_file = st.file_uploader(
            "Choose a WAV audio file",
            type=['wav', 'mp3', 'flac'],
            help="Upload an audio file containing guitar chords for analysis"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"📁 **File:** {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Audio player
            st.audio(uploaded_file, format='audio/wav')
            
            # Analyze button
            if st.button("🔍 Analyze Chords", type="primary"):
                analyze_audio_file(uploaded_file, confidence, min_duration, enable_tts, custom_question)
    
    with col2:
        st.header("📊 Quick Stats")
        
        # Display some stats or help
        st.markdown("""
        **🎯 What  Can Do:**
        - 🎸 Detect guitar chords in audio
        - 🎼 Identify musical keys
        - 📈 Show chord progressions with timing
        - 🎵 Generate guitar tabs
        - 👨‍🏫 Provide music theory tutoring
        - 🧠 Answer music theory questions
        """)
        
        # Example files
        st.subheader("🎼 Try Example Files")
        if st.button("📁 Load Test File"):
            st.info("Use the test files in the 'tests' directory for quick testing!")

def analyze_audio_file(uploaded_file, confidence, min_duration, enable_tts, custom_question):
    """Analyze the uploaded audio file using the ChordAI API."""
    
    with st.spinner("🎵 Analyzing your audio... This may take a moment!"):
        try:
            # Prepare the request
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            params = {
                "confidence": confidence,
                "min_duration": min_duration,
                "enable_tts": enable_tts
            }
            
            if custom_question:
                params["question"] = custom_question
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/analyze",
                files=files,
                params=params,
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                display_analysis_results(results)
            else:
                st.error(f"❌ Analysis failed: {response.json().get('error', 'Unknown error')}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to HorizonJam API server. Please ensure the server is running on localhost:8000")
        except requests.exceptions.Timeout:
            st.error("⏰ Analysis timed out. Please try with a shorter audio file.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

def display_analysis_results(results):
    """Display the analysis results in a beautiful format."""
    
    st.success("✅ Analysis Complete!")
    
    # Analysis Summary
    analysis = results.get("analysis", {})
    
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
    
    # Chord Progression
    st.subheader("🎼 Chord Progression")
    chord_progression = analysis.get('chord_progression', 'Unknown')
    st.markdown(f"""
    <div class="chord-card">
        <h2 style="text-align: center; margin: 0;">{chord_progression}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Chord Timeline
    chord_events = results.get("chord_events", [])
    if chord_events:
        st.subheader("📊 Chord Timeline")
        display_chord_timeline(chord_events)
    
    # Guitar Tabs
    chord_tabs = results.get("chord_tabs", {})
    if chord_tabs:
        st.subheader("🎸 Guitar Tabs")
        display_chord_tabs(chord_tabs)
    
    # Tutoring Response
    tutoring_response = results.get("tutoring_response", "")
    if tutoring_response:
        st.subheader("👨‍🏫 Music Theory Tutoring")
        st.markdown(f"""
        <div class="tutor-response">
            {tutoring_response}
        </div>
        """, unsafe_allow_html=True)
    
    # Audio playback (TTS)
    if results.get("tts_enabled") and results.get("audio_url"):
        st.subheader("🔊 Listen to Explanation")
        st.audio(f"{API_BASE_URL}{results['audio_url']}")

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

def query_rag_system(question):
    """Query the RAG system for music theory questions."""
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/rag-query",
            json={"question": question, "context": {}},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"RAG query failed: {response.json().get('error', 'Unknown error')}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server")
        return None
    except Exception as e:
        st.error(f"RAG query error: {str(e)}")
        return None

if __name__ == "__main__":
    main()
