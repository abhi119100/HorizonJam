#!/usr/bin/env python3
"""
RAG Database Initializer

This script automatically initializes the RAG database with OpenAI embeddings
and can be integrated into the main pipeline to ensure the database is ready.
"""

import os
import sys
import logging
import chromadb
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from RAG.embed_chord_analysis import ChordAnalysisEmbedder
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger("initializer")

class RAGDatabaseInitializer:
    """
    Handles automatic initialization of the RAG database with OpenAI embeddings.
    """
    
    def __init__(self, db_path="enhanced_chroma_store", collection_name="music_theory"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedder = None
        
    def check_database_exists(self):
        """
        Check if the database exists and has content.
        
        Returns:
            tuple: (exists, count) - whether DB exists and document count
        """
        try:
            if not os.path.exists(self.db_path):
                logger.info(f"Database directory {self.db_path} does not exist")
                return False, 0
                
            client = chromadb.PersistentClient(path=self.db_path)
            
            try:
                collection = client.get_collection(name=self.collection_name)
                count = collection.count()
                logger.info(f"Found existing database with {count} documents")
                return True, count
            except Exception:
                logger.info(f"Collection {self.collection_name} does not exist")
                return False, 0
                
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            return False, 0
    
    def clear_database(self):
        """
        Clear the existing database to ensure clean state.
        """
        try:
            if os.path.exists(self.db_path):
                client = chromadb.PersistentClient(path=self.db_path)
                try:
                    client.delete_collection(name=self.collection_name)
                    logger.info(f"Cleared existing collection: {self.collection_name}")
                except Exception:
                    logger.info(f"Collection {self.collection_name} did not exist")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
    
    def initialize_database(self, force_recreate=False):
        """
        Initialize the RAG database with OpenAI embeddings.
        
        Args:
            force_recreate: If True, recreate database even if it exists
            
        Returns:
            bool: Success status
        """
        try:
            # Check if database already exists and has content
            exists, count = self.check_database_exists()
            
            if exists and count > 0 and not force_recreate:
                logger.info(f"Database already initialized with {count} documents")
                return True
            
            logger.info("Initializing RAG database with OpenAI embeddings...")
            
            # Clear existing database if force recreate
            if force_recreate:
                self.clear_database()
            
            # Initialize embedder with OpenAI
            self.embedder = ChordAnalysisEmbedder(
                model_name="openai",
                db_path=self.db_path,
                collection_name=self.collection_name
            )
            
            # Initialize the embedder components
            self.embedder.initialize_chromadb()
            self.embedder.load_embedding_model()
            
            # Process sample analyses
            sample_analyses = self._get_sample_analyses()
            
            if not sample_analyses:
                logger.warning("No sample analyses found to embed")
                return False
            
            # Embed the analyses
            success_count = 0
            for i, analysis in enumerate(sample_analyses):
                try:
                    # Create a mock source file name for the sample
                    source_file = f"sample_analysis_{i+1}.json"
                    
                    # Convert our sample format to the expected analysis format
                    analysis_data = {
                        "analysis_summary": {
                            "detected_key": analysis["key"],
                            "chord_progression": analysis["chord_progression"],
                            "total_chord_events": len(analysis["chords"]),
                            "estimated_accuracy_percent": 95
                        },
                        "chord_events": [
                            {
                                "chord": chord,
                                "duration_seconds": 2.0,
                                "start_time": i * 2.0
                            } for i, chord in enumerate(analysis["chords"])
                        ]
                    }
                    
                    self.embedder.embed_analysis(analysis_data, source_file)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to embed analysis: {e}")
            
            # Verify the database
            exists, final_count = self.check_database_exists()
            
            if exists and final_count > 0:
                logger.info(f"RAG database initialized successfully with {final_count} analyses")
                return True
            else:
                logger.error("Database initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def _get_sample_analyses(self):
        """
        Get sample chord analyses for embedding.
        
        Returns:
            list: Sample analyses
        """
        return [
            {
                "id": "sample_1",
                "chord_progression": "C - Am - F - G",
                "key": "C major",
                "analysis": "Classic I-vi-IV-V progression in C major. This is one of the most popular chord progressions in Western music, providing a strong sense of resolution and emotional movement.",
                "chords": ["C", "Am", "F", "G"],
                "metadata": {
                    "root_key": "C",
                    "key_mode": "major",
                    "unique_chords": ["C", "Am", "F", "G"],
                    "chord_sequence": ["C", "Am", "F", "G"]
                }
            },
            {
                "id": "sample_2",
                "chord_progression": "Em - C - G - D",
                "key": "G major",
                "analysis": "vi-IV-I-V progression in G major. This progression creates a melancholic yet hopeful feeling, commonly used in pop and rock ballads.",
                "chords": ["Em", "C", "G", "D"],
                "metadata": {
                    "root_key": "G",
                    "key_mode": "major",
                    "unique_chords": ["Em", "C", "G", "D"],
                    "chord_sequence": ["Em", "C", "G", "D"]
                }
            },
            {
                "id": "sample_3",
                "chord_progression": "Am - F - C - G",
                "key": "C major",
                "analysis": "vi-IV-I-V progression in C major. This creates a sense of movement from minor to major, often used in emotional and uplifting songs.",
                "chords": ["Am", "F", "C", "G"],
                "metadata": {
                    "root_key": "C",
                    "key_mode": "major",
                    "unique_chords": ["Am", "F", "C", "G"],
                    "chord_sequence": ["Am", "F", "C", "G"]
                }
            },
            {
                "id": "sample_4",
                "chord_progression": "Dm - Bb - F - C",
                "key": "F major",
                "analysis": "vi-IV-I-V progression in F major. This progression has a warm, rich sound due to the flat keys, commonly used in jazz and soul music.",
                "chords": ["Dm", "Bb", "F", "C"],
                "metadata": {
                    "root_key": "F",
                    "key_mode": "major",
                    "unique_chords": ["Dm", "Bb", "F", "C"],
                    "chord_sequence": ["Dm", "Bb", "F", "C"]
                }
            },
            {
                "id": "sample_5",
                "chord_progression": "E - A - B - E",
                "key": "E major",
                "analysis": "I-IV-V-I progression in E major. This is a fundamental progression that establishes the key strongly and provides a sense of completion and resolution.",
                "chords": ["E", "A", "B", "E"],
                "metadata": {
                    "root_key": "E",
                    "key_mode": "major",
                    "unique_chords": ["E", "A", "B"],
                    "chord_sequence": ["E", "A", "B", "E"]
                }
            }
        ]

def initialize_rag_system(force_recreate=False):
    """
    Convenience function to initialize the RAG system.
    
    Args:
        force_recreate: If True, recreate database even if it exists
        
    Returns:
        bool: Success status
    """
    initializer = RAGDatabaseInitializer()
    return initializer.initialize_database(force_recreate=force_recreate)

def main():
    """
    Main function for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize RAG Database")
    parser.add_argument("--force", action="store_true", 
                       help="Force recreate database even if it exists")
    parser.add_argument("--check", action="store_true",
                       help="Only check database status")
    
    args = parser.parse_args()
    
    initializer = RAGDatabaseInitializer()
    
    if args.check:
        exists, count = initializer.check_database_exists()
        if exists:
            print(f"Database exists with {count} documents")
        else:
            print("Database does not exist or is empty")
        return
    
    success = initializer.initialize_database(force_recreate=args.force)
    
    if success:
        print("RAG database initialized successfully")
        sys.exit(0)
    else:
        print("RAG database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()