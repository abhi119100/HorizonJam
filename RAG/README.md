This Music RAG Data Scraper collects guitar tabs, music theory content, and educational materials for AI training. It processes both local files and web content, then stores everything in a searchable ChromaDB vector database.
# How It Works
Phase 1: Local File Processing

Parses TuxGuitar files (.gp3/.gp4/.gp5) for guitar tablature
Processes MIDI files to extract musical notes and timing
Reads ASCII tab files and chord charts
Converts everything into structured JSON chunks

Phase 2: Web Scraping

Scrapes educational music websites (Wikipedia, music theory sites, etc.)
Attempts to get Ultimate Guitar tabs
Processes GitHub awesome-guitar resources
Extracts and chunks text content for AI training

Data Storage

Saves all content as JSON files
Stores in ChromaDB vector database for semantic search
Creates searchable chunks with metadata (source, difficulty, topic, etc.)

# Installation (prereqs mainly (ignore file structure part - that is automatically handeled by the code)
<img width="418" height="332" alt="image" src="https://github.com/user-attachments/assets/ff38cc75-63dd-433a-8a53-08e8d592ebb4" />






# Output Files
The scraper creates several JSON files in the music_rag_data/ directory:

phase1_local_file_chunks.json - Local file processing results
educational_websites.json - Web scraped educational content
ultimate_guitar_tabs.json - Guitar tabs (if successful)
awesome_guitar_resources.json - GitHub resources
complete_music_dataset.json - Combined dataset
chroma_db/ - ChromaDB vector database




