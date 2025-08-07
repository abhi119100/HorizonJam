#!/usr/bin/env python3
"""
Test script for TTS-enabled ChordAI API

This script demonstrates how to use the new TTS functionality:
1. Upload an audio file
2. Get chord analysis with RAG-enhanced tutoring
3. Receive an MP3 audio URL for the tutoring response
"""

import requests
import json
from pathlib import Path

def test_tts_api():
    """Test the TTS-enabled analyze endpoint."""
    
    # API endpoint
    url = "http://localhost:8000/analyze"
    
    # Test audio file
    test_file = Path("HorizonJam-master/tests/testG.wav")
    if not test_file.exists():
        test_file = Path("tests/testG.wav")  # Try relative path from HorizonJam-master
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("🎵 Testing TTS-enabled ChordAI API...")
    print(f"📁 Using test file: {test_file}")
    
    # Prepare the request
    with open(test_file, 'rb') as f:
        files = {'file': (test_file.name, f, 'audio/wav')}
        params = {
            'confidence': 0.3,
            'min_duration': 0.05,
            'enable_tts': True  # Enable TTS
        }
        
        try:
            print("🔄 Sending request to API...")
            response = requests.post(url, files=files, params=params, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                print("✅ API Response received!")
                print(f"🎼 Chord Analysis: {data.get('chord_analysis', {}).get('analysis_summary', {}).get('chord_progression', [])}")
                print(f"🎸 Tutoring Response Length: {len(data.get('tutoring_response', ''))} characters")
                print(f"🔊 TTS Enabled: {data.get('tts_enabled', False)}")
                
                if data.get('audio_url'):
                    audio_url = f"http://localhost:8000{data['audio_url']}"
                    print(f"🎧 Audio URL: {audio_url}")
                    print("\n💡 You can now play this MP3 URL in your browser or audio player!")
                else:
                    print("⚠️ No audio URL generated")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"📡 Server response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🎸 ChordAI TTS API Test")
    print("=" * 30)
    
    # Test health check first
    test_health_check()
    print()
    
    # Test TTS functionality
    test_tts_api()
    
    print("\n🎵 Test completed!")