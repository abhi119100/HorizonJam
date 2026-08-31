# 🎸 Enhanced Chord RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for guitar chord data, designed for optimal integration with GPT-4o and other language models.

## 📋 Overview

This system transforms the `full_chord_tab_library.json` into a searchable vector database using ChromaDB and SentenceTransformers. It enables semantic search, metadata filtering, and intelligent chord recommendations for music education and composition.

### 🌟 Key Features

- **Semantic Search**: Natural language queries like "show me jazz chords" or "beginner-friendly C major variations"
- **Metadata Filtering**: Search by difficulty, chord type, fret span, and more
- **Chord Progressions**: Get optimized fingerings for chord sequences
- **Rich Formatting**: ASCII tab diagrams and detailed chord information
- **GPT-4o Ready**: Structured outputs perfect for AI integration
- **Comprehensive Analytics**: Embedding statistics and chord distribution analysis

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements_chords.txt

# Verify ChromaDB installation
python -c "import chromadb; print('ChromaDB installed successfully')"
```

### 2. Create Embeddings

```bash
# Run the embedding script
python embed_chords.py
```

This will:
- Load `full_chord_tab_library.json`
- Create embeddings using SentenceTransformers
- Store in ChromaDB at `chroma_chorddb/`
- Generate statistics in `embedding_stats.json`

### 3. Query the Database

```bash
# Run query demonstrations
python query_chords.py
```

## 📊 System Architecture

```
full_chord_tab_library.json
           ↓
    embed_chords.py
           ↓
    ChromaDB Vector Store
           ↓
    query_chords.py
           ↓
    Structured Results
```

## 🔍 Query Examples

### Semantic Search

```python
from query_chords import ChordQuerySystem

qs = ChordQuerySystem()

# Natural language queries
results = qs.search_chords("Show me Cm7 voicings", n_results=5)
results = qs.search_chords("easy beginner chords", n_results=10)
results = qs.search_chords("jazz chords with extensions", n_results=8)
```

### Chord Name Search

```python
# Get all variations of a specific chord
variations = qs.search_by_chord_name("Cmaj", n_results=10)
variations = qs.search_by_chord_name("Amin", n_results=5)
```

### Difficulty-Based Search

```python
# Search by difficulty level
beginner_chords = qs.search_by_difficulty("beginner", chord_type="maj", n_results=10)
advanced_chords = qs.search_by_difficulty("advanced", n_results=5)
```

### Notes-Based Search

```python
# Find chords containing specific notes
chords_with_ceg = qs.search_by_notes(["C", "E", "G"], n_results=5)
chords_with_fac = qs.search_by_notes(["F", "A", "C"], n_results=3)
```

### Chord Progressions

```python
# Get optimized fingerings for progressions
progression = qs.get_chord_progressions(["Cmaj", "Amin", "Fmaj", "Gmaj"])
jazz_progression = qs.get_chord_progressions(["Cmaj7", "Am7", "Dm7", "G7"])
```

## 📈 Result Structure

All queries return structured dictionaries optimized for GPT-4o processing:

```python
{
    "query": "Show me Cm7 voicings",
    "query_type": "semantic_search",
    "total_results": 5,
    "results": [
        {
            "rank": 1,
            "id": "1234",
            "similarity_score": 0.8945,
            "metadata": {
                "chord_name": "Cm7",
                "difficulty": "intermediate",
                "notes": ["C", "Eb", "G", "Bb"],
                "intervals": [0, 3, 7, 10],
                "active_strings": 4,
                "fret_span": 3,
                "has_barre": false
            },
            "tab_diagram": "\n  Guitar Tab Diagram:\n  --------------------\n  E |-- x--\n  A |-- 3--\n  D |-- 1--\n  G |-- 3--\n  B |-- 4--\n  E |-- 3--\n  --------------------\n     (6th to 1st string)\n",
            "chord_info": {
                "name": "Cm7",
                "root": "C",
                "type": "m7",
                "difficulty": "intermediate",
                "notes": ["C", "Eb", "G", "Bb"],
                "intervals": [0, 3, 7, 10],
                "active_strings": 4,
                "fret_span": 3,
                "highest_fret": 4,
                "has_barre": false,
                "open_strings": 0
            }
        }
    ]
}
```

## 🎯 GPT-4o Integration

### Example Prompt Template

```python
def create_chord_prompt(query_results):
    prompt = f"""
    Based on the following chord search results, provide guitar learning advice:
    
    Query: {query_results['query']}
    Found {query_results['total_results']} relevant chords:
    
    """
    
    for result in query_results['results']:
        chord_info = result['chord_info']
        prompt += f"""
        Chord: {chord_info['name']}
        Difficulty: {chord_info['difficulty']}
        Notes: {', '.join(chord_info['notes'])}
        Tab: {result['tab_diagram']}
        
        """
    
    prompt += """
    Please provide:
    1. Practice recommendations
    2. Common usage contexts
    3. Transition tips between these chords
    4. Alternative fingerings if applicable
    """
    
    return prompt
```

### Usage in Applications

```python
# In your GPT-4o application
from query_chords import ChordQuerySystem

qs = ChordQuerySystem()

# User asks: "How do I play a C major chord?"
user_query = "C major chord beginner"
chord_results = qs.search_chords(user_query, n_results=3)

# Send structured results to GPT-4o
gpt_prompt = create_chord_prompt(chord_results)
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": gpt_prompt}]
)
```

## 📁 File Structure

```
RAG/
├── full_chord_tab_library.json     # Source chord data
├── embed_chords.py                 # Embedding creation script
├── query_chords.py                 # Query interface
├── requirements_chords.txt         # Dependencies
├── CHORD_RAG_README.md            # This file
├── chroma_chorddb/                # ChromaDB storage
│   ├── chroma.sqlite3
│   └── [embedding files]
├── embedding_stats.json           # Embedding statistics
└── chord_embedding.log            # Process logs
```

## 🔧 Advanced Configuration

### Custom Embedding Models

```python
# Use different embedding models
embedder = ChordEmbedder(
    model_name="all-mpnet-base-v2",  # Higher quality
    # model_name="all-MiniLM-L12-v2",  # Balanced
    # model_name="all-MiniLM-L6-v2",   # Faster (default)
)
```

### Custom Filters

```python
# Advanced filtering
results = qs.search_chords(
    "jazz chords",
    filters={
        "difficulty": {"$eq": "intermediate"},
        "fret_span": {"$lte": 4},
        "has_barre": {"$eq": False}
    }
)
```

### Batch Processing

```python
# Process multiple queries
queries = [
    "beginner major chords",
    "intermediate minor chords",
    "advanced jazz voicings"
]

all_results = []
for query in queries:
    results = qs.search_chords(query, n_results=5)
    all_results.append(results)
```

## 📊 Metadata Fields

Each chord includes comprehensive metadata:

| Field | Type | Description |
|-------|------|-------------|
| `chord_name` | string | Full chord name (e.g., "Cmaj7") |
| `chord_root` | string | Root note (e.g., "C") |
| `chord_type` | string | Chord type (e.g., "maj7", "min", "dim") |
| `difficulty` | string | "beginner", "intermediate", "advanced" |
| `notes` | array | Note names in the chord |
| `intervals` | array | Interval formula from root |
| `active_strings` | integer | Number of strings played |
| `fret_span` | integer | Span between lowest and highest frets |
| `highest_fret` | integer | Highest fret used |
| `has_barre` | boolean | Whether chord requires barre technique |
| `open_strings` | integer | Number of open strings |

## 🎵 Use Cases

### Music Education Apps
- Chord lookup and learning
- Progressive difficulty curricula
- Practice routine generation

### Composition Tools
- Chord progression suggestions
- Voice leading optimization
- Harmonic analysis

### AI Music Assistants
- Natural language chord queries
- Context-aware recommendations
- Personalized learning paths

## 🔍 Troubleshooting

### Common Issues

1. **ChromaDB not found**
   ```bash
   pip install chromadb>=0.4.15
   ```

2. **Embedding model download fails**
   ```python
   # Manually download model
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer("all-MiniLM-L6-v2")
   ```

3. **Database not found error**
   ```bash
   # Ensure embed_chords.py ran successfully
   python embed_chords.py
   ```

4. **Memory issues with large datasets**
   ```python
   # Process in batches
   embedder = ChordEmbedder()
   embedder.batch_size = 1000  # Reduce batch size
   ```

### Performance Optimization

- Use GPU acceleration for embedding generation
- Adjust batch sizes based on available memory
- Consider model quantization for production deployment

## 📈 Statistics Example

After running `embed_chords.py`, you'll get statistics like:

```json
{
  "total_chords": 28202,
  "embedding_model": "all-MiniLM-L6-v2",
  "database_path": "chroma_chorddb",
  "collection_name": "chord_tabs",
  "chord_types": {
    "maj": 8456,
    "min": 7234,
    "7": 3421,
    "m7": 2876,
    "maj7": 2145
  },
  "difficulty_distribution": {
    "beginner": 9876,
    "intermediate": 12456,
    "advanced": 5870
  },
  "created_at": "2024-01-15T10:30:45.123456"
}
```

## 🤝 Contributing

To extend the system:

1. **Add new query types** in `query_chords.py`
2. **Enhance metadata** in `embed_chords.py`
3. **Improve formatting** for specific use cases
4. **Add visualization** capabilities

## 📄 License

This chord RAG system is designed for educational and development purposes. Ensure compliance with any licensing requirements for the underlying chord data.

---

**Ready to rock! 🎸** Your chord database is now searchable and ready for GPT-4o integration.