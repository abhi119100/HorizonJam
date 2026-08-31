#!/usr/bin/env python3
"""
Enhanced Music Data Embedding Script
Embeds comprehensive music theory and guitar data into ChromaDB
"""

import json
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found in environment variables")
    print("Please set OPENAI_API_KEY in your .env file")
    exit(1)

print("🚀 Starting Enhanced Music Data Embedding...")
print(f"🔑 Using API key: {openai_api_key[:20]}...")

# Initialize documents list
all_docs = []

# Set the correct path to the enhanced music data
music_data_dir = "HorizonJam-master/RAG/documents/music_rag_data"

if not os.path.exists(music_data_dir):
    print(f"❌ Music data directory not found: {music_data_dir}")
    exit(1)

print(f"📁 Using music data directory: {music_data_dir}")

# Process complete music dataset
print("🎵 Loading complete music dataset...")
complete_music_path = os.path.join(music_data_dir, "complete_music_dataset.json")
if os.path.exists(complete_music_path):
    with open(complete_music_path, 'r', encoding='utf-8') as f:
        complete_music_data = json.load(f)
    
    for item in complete_music_data:
        if isinstance(item, dict) and "content" in item:
            all_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "source": item.get("source", "complete_music_dataset"),
                        "title": item.get("title", "Music Theory Content"),
                        "type": "music_theory",
                        "topic": item.get("metadata", {}).get("topic", "general"),
                        "difficulty": item.get("metadata", {}).get("difficulty", "intermediate"),
                        "instrument": item.get("metadata", {}).get("instrument", "general")
                    }
                )
            )
    print(f"✅ Loaded {len([item for item in complete_music_data if isinstance(item, dict) and 'content' in item])} music theory documents")
else:
    print(f"⚠️ Complete music dataset not found at {complete_music_path}")

# Process enhanced chord dataset
print("🎸 Loading enhanced chord dataset...")
chord_dataset_path = os.path.join(music_data_dir, "enhanced_chord_dataset.json")
if os.path.exists(chord_dataset_path):
    with open(chord_dataset_path, 'r', encoding='utf-8') as f:
        chord_data = json.load(f)
    
    chord_count = 0
    for chord in chord_data:
        if isinstance(chord, dict) and "chord_name" in chord:
            chord_content = f"""Guitar Chord: {chord['chord_name']}
Notation: {chord['notation']}
Fret Positions: {chord['fret_positions']}
Fingers: {', '.join([str(pos) if pos != -1 else 'X' for pos in chord['fret_positions']])}
Source: {chord.get('source', 'database')}"""
            
            all_docs.append(
                Document(
                    page_content=chord_content,
                    metadata={
                        "source": "enhanced_chord_dataset",
                        "chord_name": chord['chord_name'],
                        "type": "chord_diagram",
                        "notation": chord['notation'],
                        "instrument": "guitar"
                    }
                )
            )
            chord_count += 1
    print(f"✅ Loaded {chord_count} enhanced chord diagrams")
else:
    print(f"⚠️ Enhanced chord dataset not found at {chord_dataset_path}")

# Process awesome guitar resources
print("🎯 Loading awesome guitar resources...")
awesome_guitar_path = os.path.join(music_data_dir, "awesome_guitar_resources.json")
if os.path.exists(awesome_guitar_path):
    with open(awesome_guitar_path, 'r', encoding='utf-8') as f:
        awesome_guitar_data = json.load(f)
    
    resource_count = 0
    for item in awesome_guitar_data:
        if isinstance(item, dict) and "content" in item:
            all_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "source": item.get("source", "awesome_guitar_resources"),
                        "type": "guitar_resource",
                        "title": item.get("title", "Guitar Resource")
                    }
                )
            )
            resource_count += 1
    print(f"✅ Loaded {resource_count} guitar resources")
else:
    print(f"⚠️ Awesome guitar resources not found at {awesome_guitar_path}")

# Process full chord tab library (comprehensive chord database)
print("🎸 Loading full chord tab library...")
full_chord_library_path = os.path.join(music_data_dir, "full_chord_tab_library.json")
if os.path.exists(full_chord_library_path):
    with open(full_chord_library_path, 'r', encoding='utf-8') as f:
        full_chord_data = json.load(f)
    
    print(f"📊 Processing {len(full_chord_data)} chord variations...")
    
    chord_variations_count = 0
    for chord_record in full_chord_data[:5000]:  # Limit to first 5000 for performance
        if isinstance(chord_record, dict):
            # Extract chord information
            chord_name = chord_record.get('chord_name', 'Unknown')
            variation = chord_record.get('variation', [])
            notes = chord_record.get('notes', [])
            intervals = chord_record.get('interval_formula', [])
            chord_id = chord_record.get('id', 'unknown')
            
            # Format variation (tab) for readability
            variation_str = "-".join([str(v) if v != "x" and v is not None else "x" for v in variation])
            
            # Format notes, filtering out None/null values
            notes_list = [note for note in notes if note and note != "x" and note is not None]
            notes_str = ", ".join(notes_list)
            
            # Calculate difficulty based on fret positions
            fret_numbers = [v for v in variation if isinstance(v, int) and v > 0]
            if not fret_numbers:
                difficulty = "beginner"
            else:
                max_fret = max(fret_numbers)
                fret_span = max(fret_numbers) - min(fret_numbers) if len(fret_numbers) > 1 else 0
                if max_fret <= 3 and fret_span <= 3:
                    difficulty = "beginner"
                elif max_fret <= 7 and fret_span <= 4:
                    difficulty = "intermediate"
                else:
                    difficulty = "advanced"
            
            # Create comprehensive chord content
            chord_content = f"""Guitar Chord: {chord_name}
Tab Notation: {variation_str}
Notes: {notes_str}
Interval Formula: {intervals}
Difficulty: {difficulty}
Fret Positions (Low E to High E): {variation}

How to play:
- String 6 (Low E): {variation[0] if len(variation) > 0 else 'x'}
- String 5 (A): {variation[1] if len(variation) > 1 else 'x'}
- String 4 (D): {variation[2] if len(variation) > 2 else 'x'}
- String 3 (G): {variation[3] if len(variation) > 3 else 'x'}
- String 2 (B): {variation[4] if len(variation) > 4 else 'x'}
- String 1 (High E): {variation[5] if len(variation) > 5 else 'x'}

This {chord_name} chord variation is suitable for {difficulty} players."""
            
            # Extract chord root and type
            chord_root = chord_name[0] if chord_name else "Unknown"
            chord_type = chord_name[1:] if len(chord_name) > 1 else "maj"
            
            all_docs.append(
                Document(
                    page_content=chord_content,
                    metadata={
                        "source": "full_chord_tab_library",
                        "chord_id": str(chord_id),
                        "chord_name": chord_name,
                        "chord_root": chord_root,
                        "chord_type": chord_type,
                        "type": "comprehensive_chord_tab",
                        "difficulty": difficulty,
                        "instrument": "guitar",
                        "tab_notation": variation_str,
                        "notes": notes_str
                    }
                )
            )
            chord_variations_count += 1
    
    print(f"✅ Successfully processed {chord_variations_count} chord variations from full chord library")
else:
    print(f"⚠️ Full chord tab library not found at {full_chord_library_path}")

print(f"📊 Total documents to embed: {len(all_docs)}")

if len(all_docs) == 0:
    print("❌ No documents found to embed. Please check the data files.")
    exit(1)

# Create embedding model
print("🔄 Initializing OpenAI embeddings...")
embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Create ChromaDB directory
chroma_dir = "RAG/enhanced_chroma_store"
os.makedirs(chroma_dir, exist_ok=True)

# Remove existing collection if it exists
import shutil
if os.path.exists(chroma_dir):
    try:
        shutil.rmtree(chroma_dir)
        print(f"🗑️ Removed existing {chroma_dir}")
    except PermissionError:
        print(f"⚠️ Could not remove {chroma_dir}, it may be in use.")

os.makedirs(chroma_dir, exist_ok=True)

# Embed and store into ChromaDB
print(f"🔄 Embedding documents into ChromaDB at {chroma_dir}...")
try:
    vectordb = Chroma.from_documents(
        documents=all_docs,
        embedding=embedding_model,
        persist_directory=chroma_dir
    )
    
    vectordb.persist()
    print(f"✅ Successfully embedded {len(all_docs)} documents and stored in ChromaDB.")
    
    print("\n🎸 Enhanced RAG system now includes:")
    print("   - Complete music theory dataset")
    print("   - Enhanced chord diagrams and positions")
    print("   - Guitar resources and educational content")
    print("   - Comprehensive chord tab library (5000+ variations)")
    print("\n🚀 Your RAG bot now has comprehensive music and guitar knowledge!")
    print("🎯 Ready for integration with ChordAI application!")
    
except Exception as e:
    print(f"❌ Error during embedding: {e}")
    exit(1)