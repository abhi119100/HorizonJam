#!/usr/bin/env python3
"""
Embed specialized music theory data from JSON files into ChromaDB
This will create a more relevant RAG system for ChordAI tutoring
"""

import json
import os
import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicRAGEmbedder:
    def __init__(self, db_path: str = "RAG/chroma_store", collection_name: str = "music_theory"):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Initialize embedding model (using ChromaDB's default)
        logger.info("Using ChromaDB's default embedding function...")
        self.embedding_model = None  # Let ChromaDB handle embeddings
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Specialized music theory and guitar instruction data"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def process_complete_music_dataset(self, file_path: str) -> List[Dict[str, Any]]:
        """Process the complete music theory dataset"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            # Create comprehensive text for embedding
            content_parts = []
            
            # Add title and source
            if 'title' in item:
                content_parts.append(f"Title: {item['title']}")
            if 'source' in item:
                content_parts.append(f"Source: {item['source']}")
            
            # Add main content
            if 'content' in item:
                content_parts.append(item['content'])
            
            # Add metadata context
            if 'metadata' in item:
                metadata = item['metadata']
                if 'topic' in metadata:
                    content_parts.append(f"Topic: {metadata['topic']}")
                if 'difficulty' in metadata:
                    content_parts.append(f"Difficulty: {metadata['difficulty']}")
                if 'instrument' in metadata:
                    content_parts.append(f"Instrument: {metadata['instrument']}")
            
            full_content = "\n".join(content_parts)
            
            documents.append({
                'content': full_content,
                'metadata': {
                    'source': item.get('source', 'unknown'),
                    'title': item.get('title', 'untitled'),
                    'topic': item.get('metadata', {}).get('topic', 'general'),
                    'difficulty': item.get('metadata', {}).get('difficulty', 'unknown'),
                    'instrument': item.get('metadata', {}).get('instrument', 'general'),
                    'chunk_id': item.get('chunk_id', ''),
                    'type': 'music_theory'
                }
            })
        
        return documents
    
    def process_chord_dataset(self, file_path: str) -> List[Dict[str, Any]]:
        """Process the enhanced chord dataset"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        
        # Process chord visuals if present
        if isinstance(data, list) and len(data) > 0 and 'chord_visuals' in data[0]:
            chord_visuals = data[0]['chord_visuals']
            
            # Group chords by name for better context
            chord_groups = {}
            for chord in chord_visuals:
                chord_name = chord['chord_name']
                if chord_name not in chord_groups:
                    chord_groups[chord_name] = []
                chord_groups[chord_name].append(chord)
            
            # Create documents for each chord group
            for chord_name, variations in chord_groups.items():
                content_parts = [f"Chord: {chord_name}"]
                
                for i, variation in enumerate(variations):
                    content_parts.append(f"Variation {i+1}:")
                    content_parts.append(f"  Notation: {variation['notation']}")
                    content_parts.append(f"  Fret positions: {variation['fret_positions']}")
                    if 'diagram_path' in variation:
                        content_parts.append(f"  Diagram available: {variation['diagram_path']}")
                
                documents.append({
                    'content': "\n".join(content_parts),
                    'metadata': {
                        'chord_name': chord_name,
                        'variations_count': len(variations),
                        'type': 'chord_diagram',
                        'instrument': 'guitar',
                        'topic': 'chords',
                        'difficulty': 'beginner'
                    }
                })
        
        return documents
    
    def process_guitar_resources(self, file_path: str) -> List[Dict[str, Any]]:
        """Process guitar resources dataset"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            for item in data:
                content_parts = []
                
                if 'title' in item:
                    content_parts.append(f"Resource: {item['title']}")
                if 'description' in item:
                    content_parts.append(item['description'])
                if 'url' in item:
                    content_parts.append(f"URL: {item['url']}")
                if 'category' in item:
                    content_parts.append(f"Category: {item['category']}")
                
                documents.append({
                    'content': "\n".join(content_parts),
                    'metadata': {
                        'title': item.get('title', 'untitled'),
                        'category': item.get('category', 'general'),
                        'type': 'guitar_resource',
                        'instrument': 'guitar',
                        'topic': 'resources'
                    }
                })
            
            return documents
        except Exception as e:
            logger.warning(f"Could not process {file_path}: {e}")
            return []
    
    def embed_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Embed documents into ChromaDB"""
        logger.info(f"Embedding {len(documents)} documents...")
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Prepare batch data
            texts = [doc['content'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            ids = [f"doc_{i + j}" for j in range(len(batch))]
            
            # Add to collection (ChromaDB will handle embeddings automatically)
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
    
    def embed_all_music_data(self):
        """Embed all available music data files"""
        music_data_dir = "RAG/documents/music_rag_data"
        all_documents = []
        
        # Process each JSON file
        json_files = [
            ("complete_music_dataset.json", self.process_complete_music_dataset),
            ("enhanced_chord_dataset.json", self.process_chord_dataset),
            ("awesome_guitar_resources.json", self.process_guitar_resources),
            ("educational_websites.json", self.process_guitar_resources),
            ("full_chord_tab_library.json", self.process_guitar_resources),
            ("ultimate_guitar_tabs.json", self.process_guitar_resources)
        ]
        
        for filename, processor in json_files:
            file_path = os.path.join(music_data_dir, filename)
            if os.path.exists(file_path):
                logger.info(f"Processing {filename}...")
                try:
                    documents = processor(file_path)
                    all_documents.extend(documents)
                    logger.info(f"Added {len(documents)} documents from {filename}")
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
            else:
                logger.warning(f"File not found: {file_path}")
        
        if all_documents:
            logger.info(f"Total documents to embed: {len(all_documents)}")
            self.embed_documents(all_documents)
            
            # Get final count
            final_count = self.collection.count()
            logger.info(f"Successfully embedded music data. Collection now has {final_count} items.")
        else:
            logger.error("No documents found to embed!")
    
    def get_collection_info(self):
        """Get information about the collection"""
        count = self.collection.count()
        logger.info(f"Collection '{self.collection_name}' contains {count} documents")
        
        if count > 0:
            # Sample a few documents
            sample = self.collection.get(limit=3)
            logger.info("Sample documents:")
            for i, (doc, metadata) in enumerate(zip(sample['documents'], sample['metadatas'])):
                logger.info(f"  {i+1}. Type: {metadata.get('type', 'unknown')}, Topic: {metadata.get('topic', 'unknown')}")
                logger.info(f"     Preview: {doc[:100]}...")

def main():
    """Main function to embed music data"""
    embedder = MusicRAGEmbedder()
    
    logger.info("Starting music data embedding process...")
    embedder.embed_all_music_data()
    
    logger.info("\nFinal collection status:")
    embedder.get_collection_info()
    
    logger.info("\nMusic RAG data embedding complete!")
    logger.info("You can now update your .env file to use collection_name='music_theory'")

if __name__ == "__main__":
    main()