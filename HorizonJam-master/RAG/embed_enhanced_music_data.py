import json
import os
from langchain_community.vectorstores import Chroma
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_core.documents import Document

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please configure your API key.")

# Initialize documents list
all_docs = []

# Load original scraped data
print("📄 Loading original scraped data...")
with open("scraped_data.json") as f:
    scraped_data = json.load(f)

# Convert scraped data to documents
for item in scraped_data:
    all_docs.append(
        Document(
            page_content=item["content"],
            metadata={"source": item["source"], "type": "web_scraped"}
        )
    )

# Load enhanced music datasets from documents folder
music_data_dir = "documents/music_rag_data"

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

# Process enhanced chord dataset
print("🎸 Loading enhanced chord dataset...")
chord_dataset_path = os.path.join(music_data_dir, "enhanced_chord_dataset.json")
if os.path.exists(chord_dataset_path):
    with open(chord_dataset_path, 'r', encoding='utf-8') as f:
        chord_data = json.load(f)
    
    # Process chord visuals if they exist
    if isinstance(chord_data, list) and len(chord_data) > 0:
        if "chord_visuals" in chord_data[0]:
            for entry in chord_data:
                if "chord_visuals" in entry:
                    for chord in entry["chord_visuals"]:
                        chord_content = f"""Chord: {chord['chord_name']}
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

# Process chord visual library
print("🎼 Loading chord visual library...")
chord_visual_path = os.path.join(music_data_dir, "chord_visual_library.json")
if os.path.exists(chord_visual_path):
    with open(chord_visual_path, 'r', encoding='utf-8') as f:
        chord_visual_data = json.load(f)
    
    for chord in chord_visual_data:
        if isinstance(chord, dict) and "chord_name" in chord:
            chord_content = f"""Guitar Chord: {chord['chord_name']}
Tab Notation: {chord['notation']}
Fret Positions (from low E to high E): {chord['fret_positions']}
How to play: Place fingers on frets {', '.join([f"string {i+1} fret {pos}" if pos != -1 else f"string {i+1} open/muted" for i, pos in enumerate(chord['fret_positions'])])}
Diagram available: {chord.get('diagram_path', 'N/A')}"""
            
            all_docs.append(
                Document(
                    page_content=chord_content,
                    metadata={
                        "source": "chord_visual_library",
                        "chord_name": chord['chord_name'],
                        "type": "chord_reference",
                        "notation": chord['notation'],
                        "instrument": "guitar"
                    }
                )
            )

# Process educational websites data
print("📚 Loading educational websites data...")
educational_path = os.path.join(music_data_dir, "educational_websites.json")
if os.path.exists(educational_path):
    with open(educational_path, 'r', encoding='utf-8') as f:
        educational_data = json.load(f)
    
    for item in educational_data:
        if isinstance(item, dict) and "content" in item:
            all_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "source": item.get("source", "educational_websites"),
                        "type": "educational_content",
                        "url": item.get("url", "")
                    }
                )
            )

# Process awesome guitar resources
print("🎯 Loading awesome guitar resources...")
awesome_guitar_path = os.path.join(music_data_dir, "awesome_guitar_resources.json")
if os.path.exists(awesome_guitar_path):
    with open(awesome_guitar_path, 'r', encoding='utf-8') as f:
        awesome_guitar_data = json.load(f)
    
    for item in awesome_guitar_data:
        if isinstance(item, dict) and "content" in item:
            all_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "source": item.get("source", "awesome_guitar_resources"),
                        "type": "guitar_resource",
                        "category": item.get("category", "general")
                    }
                )
            )

# Process local file chunks
print("📁 Loading local file chunks...")
local_chunks_path = os.path.join(music_data_dir, "phase1_local_file_chunks.json")
if os.path.exists(local_chunks_path):
    with open(local_chunks_path, 'r', encoding='utf-8') as f:
        local_chunks_data = json.load(f)
    
    for item in local_chunks_data:
        if isinstance(item, dict) and "content" in item:
            all_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "source": item.get("source", "local_files"),
                        "type": "local_content",
                        "file_type": item.get("file_type", "unknown")
                    }
                )
            )

# Process full chord tab library (comprehensive chord database)
print("🎸 Loading full chord tab library...")
full_chord_library_path = os.path.join(music_data_dir, "full_chord_tab_library.json")
if os.path.exists(full_chord_library_path):
    with open(full_chord_library_path, 'r', encoding='utf-8') as f:
        full_chord_data = json.load(f)
    
    print(f"📊 Processing {len(full_chord_data)} chord variations...")
    
    for chord_record in full_chord_data:
        if isinstance(chord_record, dict):
            # Extract chord information
            chord_name = chord_record.get('chord_name', 'Unknown')
            variation = chord_record.get('variation', [])
            notes = chord_record.get('notes', [])
            midi = chord_record.get('midi', [])
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
            
            # Detect barre chords
            fret_counts = {}
            for v in variation:
                if isinstance(v, int) and v > 0:
                    fret_counts[v] = fret_counts.get(v, 0) + 1
            has_barre = any(count >= 3 for count in fret_counts.values())
            
            # Count active strings and open strings
            active_strings = sum(1 for v in variation if v != "x" and v is not None)
            open_strings = sum(1 for v in variation if v == 0)
            
            # Create comprehensive chord content
            chord_content = f"""Guitar Chord: {chord_name}
Tab Notation: {variation_str}
Notes: {notes_str}
Interval Formula: {intervals}
Difficulty: {difficulty}
Fret Positions (Low E to High E): {variation}
Active Strings: {active_strings}
Open Strings: {open_strings}
Barre Chord: {'Yes' if has_barre else 'No'}
MIDI Notes: {[m for m in midi if m is not None]}

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
                        "notes": notes_str,
                        "intervals": str(intervals),
                        "active_strings": active_strings,
                        "open_strings": open_strings,
                        "has_barre": has_barre,
                        "fret_span": max(fret_numbers) - min(fret_numbers) if fret_numbers else 0,
                        "highest_fret": max(fret_numbers) if fret_numbers else 0
                    }
                )
            )
    
    print(f"✅ Successfully processed {len(full_chord_data)} chord variations from full chord library")

# Load sample files from documents/samples
print("🎵 Loading sample files...")
samples_dir = "documents/samples"
if os.path.exists(samples_dir):
    # Load sample_chords.txt
    sample_chords_path = os.path.join(samples_dir, "sample_chords.txt")
    if os.path.exists(sample_chords_path):
        with open(sample_chords_path, 'r', encoding='utf-8') as f:
            sample_chords_content = f.read()
        
        all_docs.append(
            Document(
                page_content=sample_chords_content,
                metadata={
                    "source": "sample_chords.txt",
                    "type": "chord_progression",
                    "instrument": "guitar",
                    "song": "Let It Be"
                }
            )
        )
    
    # Load tab1.txt
    tab1_path = os.path.join(samples_dir, "tab1.txt")
    if os.path.exists(tab1_path):
        with open(tab1_path, 'r', encoding='utf-8') as f:
            tab1_content = f.read()
        
        all_docs.append(
            Document(
                page_content=tab1_content,
                metadata={
                    "source": "tab1.txt",
                    "type": "guitar_tab",
                    "instrument": "guitar"
                }
            )
        )

print(f"📊 Total documents to embed: {len(all_docs)}")

# Create embedding model
embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Create a new ChromaDB with a different name to avoid conflicts
import shutil
chroma_dir = "enhanced_chroma_store"
if os.path.exists(chroma_dir):
    try:
        shutil.rmtree(chroma_dir)
        print(f"🗑️ Removed existing {chroma_dir}")
    except PermissionError:
        print(f"⚠️ Could not remove {chroma_dir}, it may be in use. Using a timestamped directory instead.")
        import time
        chroma_dir = f"enhanced_chroma_store_{int(time.time())}"
        print(f"📁 Using new directory: {chroma_dir}")


# Embed and store into ChromaDB
print(f"🔄 Embedding documents into ChromaDB at {chroma_dir}...")
vectordb = Chroma.from_documents(
    documents=all_docs,
    embedding=embedding_model,
    persist_directory=chroma_dir
)

vectordb.persist()
print(f"✅ Successfully embedded {len(all_docs)} documents and stored in ChromaDB.")
print("🎸 Enhanced RAG system now includes:")
print("   - Original web scraped content")
print("   - Complete music theory dataset")
print("   - Enhanced chord diagrams and positions")
print("   - Chord visual library")
print("   - Educational websites content")
print("   - Guitar resources")
print("   - Full chord tab library (28,000+ chord variations)")
print("   - Local sample files and tabs")
print("\n🚀 Your RAG bot now has comprehensive music and guitar knowledge!")
print("🎯 GPT-4o can now access:")
print("   - Semantic chord search across all variations")
print("   - Difficulty-based chord recommendations")
print("   - Detailed fingering instructions")
print("   - Music theory and educational content")
print("   - Guitar tabs and progressions")
print("\n📊 Total chord variations available for queries: 28,000+")
print("🔍 Query examples for GPT-4o:")
print("   - 'Show me beginner C major chord variations'")
print("   - 'Find jazz chords suitable for intermediate players'")
print("   - 'What are some easy open chords for beginners?'")
print("   - 'Explain how to play a barre chord'")
print("\n✨ Ready for GPT-4o integration with comprehensive guitar knowledge!")