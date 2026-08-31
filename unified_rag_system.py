#!/usr/bin/env python3
"""
Unified RAG System for ChordAI + HorizonJam Integration

This module consolidates all RAG functionality into a single, standardized system:
- Single ChromaDB database with consistent paths
- Unified embedding pipeline for all content types
- Standardized query interface
- Consolidated configuration management

Replaces multiple redundant systems:
- working_rag_query.py
- query_chord_analysis.py  
- embed_chord_analysis.py
- Various other RAG scripts

Usage:
    from unified_rag_system import UnifiedRAGSystem
    
    # Initialize system
    rag = UnifiedRAGSystem()
    
    # Embed chord analysis
    rag.embed_chord_analysis(analysis_data, "song.wav")
    
    # Query system
    response = rag.query("jazz progressions in C major")
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Import centralized logging configuration
utils_path = Path(__file__).parent / "utils"
sys.path.insert(0, str(utils_path))

try:
    from logging_config import setup_logging, suppress_warnings
    setup_logging()
except ImportError:
    logging.basicConfig(level=logging.INFO)

# Remove utils from path to avoid conflicts
if str(utils_path) in sys.path:
    sys.path.remove(str(utils_path))

# Add RAG directory to path for imports
rag_dir = Path(__file__).parent / "RAG"
sys.path.insert(0, str(rag_dir))

try:
    import chromadb
    import numpy as np
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
except ImportError as e:
    logging.error(f"Required packages not installed: {e}")
    logging.error("Install with: pip install chromadb sentence-transformers")
    raise

logger = logging.getLogger(__name__)

class UnifiedRAGSystem:
    """
    Consolidated RAG system for ChordAI + HorizonJam integration.
    
    Features:
    - Single ChromaDB database with standardized paths
    - Unified embedding pipeline for chord analysis and music theory
    - Consistent query interface
    - Automatic collection management
    - OpenAI and SentenceTransformer embedding support
    """
    
    # Standardized configuration
    DEFAULT_DB_PATH = "RAG/unified_chroma_store"
    DEFAULT_COLLECTION = "music_theory"
    DEFAULT_MODEL = "openai"  # or "all-MiniLM-L6-v2"
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 collection_name: Optional[str] = None,
                 model_name: Optional[str] = None,
                 openai_api_key: Optional[str] = None):
        """
        Initialize the unified RAG system.
        
        Args:
            db_path: ChromaDB database path (default: RAG/unified_chroma_store)
            collection_name: Collection name (default: music_theory)
            model_name: Embedding model (default: openai)
            openai_api_key: OpenAI API key (optional, uses env var)
        """
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
            
        # Configuration
        self.db_path = db_path or os.getenv("RAG_DB_PATH", self.DEFAULT_DB_PATH)
        self.collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", self.DEFAULT_COLLECTION)
        self.model_name = model_name or os.getenv("RAG_MODEL_NAME", self.DEFAULT_MODEL)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize components
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        
        # Initialize system
        self._initialize_system()
        
    def _initialize_system(self) -> None:
        """Initialize ChromaDB and embedding model."""
        try:
            logger.info(f"🚀 Initializing Unified RAG System")
            logger.info(f"   Database: {self.db_path}")
            logger.info(f"   Collection: {self.collection_name}")
            logger.info(f"   Model: {self.model_name}")
            
            # Initialize ChromaDB
            self._initialize_chromadb()
            
            # Initialize embedding model
            self._initialize_embedding_model()
            
            # Get collection stats
            count = self.collection.count()
            logger.info(f"✅ Unified RAG System initialized with {count} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG system: {e}")
            raise
            
    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection with OpenAI embedding function."""
        try:
            # Ensure target directory exists
            os.makedirs(self.db_path, exist_ok=True)

            # Initialise client
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)

            # Configure embedding function (only OpenAI permitted)
            embedding_function = OpenAIEmbeddingFunction(
                api_key=self.openai_api_key,
                model_name="text-embedding-3-small"
            )
            from utils.openai_client import build_openai_client
            embedding_function.client = build_openai_client(self.openai_api_key)

            # get_or_create ensures consistent embedding function metadata
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_function,
                metadata={
                    "description": "Unified ChordAI + HorizonJam music theory and analysis",
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            )
            logger.info(f"📦 Collection ready: '{self.collection_name}'")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
            
    def _initialize_embedding_model(self) -> None:
        """Initialize embedding model (OpenAI or SentenceTransformer)."""
        try:
            if self.model_name == "openai":
                # Use OpenAI embeddings
                if not self.openai_api_key:
                    raise ValueError("OpenAI API key required for OpenAI embeddings")
                    
                # ChromaDB will handle OpenAI embeddings automatically
                logger.info("🤖 Using OpenAI embeddings")
                self.embedding_model = "openai"
                
            else:
                # Mixing embedding models in one collection can degrade similarity search
                raise ValueError("Only OpenAI embeddings are allowed to ensure consistent vector space. Set model_name='openai'.")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
            
    def add_document(self, 
                    content: str, 
                    metadata: Optional[Dict[str, Any]] = None,
                    source_identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a general document to the RAG system.
        
        Args:
            content: Document content text
            metadata: Document metadata (will be sanitized for ChromaDB)
            source_identifier: Source file or identifier
            
        Returns:
            Result with success status and document ID
        """
        try:
            if not content or len(content.strip()) < 10:
                return {"success": False, "error": "Content too short or empty"}
            
            # Sanitize metadata for ChromaDB (only str, int, float, bool, None allowed)
            clean_metadata = {}
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        clean_metadata[key] = value
                    elif isinstance(value, list):
                        # Convert lists to comma-separated strings
                        clean_metadata[key] = ", ".join([str(v) for v in value if v is not None])
                    else:
                        # Convert other types to strings
                        clean_metadata[key] = str(value)
            
            # Add standard metadata
            clean_metadata.update({
                "added_at": datetime.now().isoformat(),
                "document_type": "general",
                "source_identifier": source_identifier or "unknown"
            })
            
            # Generate document ID
            import hashlib
            doc_id = hashlib.md5(content.encode()).hexdigest()[:16]
            
            # Add to ChromaDB
            if self.model_name == "openai":
                # Use OpenAI embeddings
                self.collection.add(
                    documents=[content],
                    metadatas=[clean_metadata],
                    ids=[doc_id]
                )
            else:
                # Use SentenceTransformer embeddings
                embedding = self.embedding_model.encode([content])[0].tolist()
                self.collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[clean_metadata],
                    ids=[doc_id]
                )
            
            logger.info(f"✅ Added document: {doc_id}")
            return {
                "success": True,
                "document_id": doc_id,
                "content_length": len(content),
                "metadata_keys": list(clean_metadata.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add document: {e}")
            return {"success": False, "error": str(e)}
    
    def embed_chord_analysis(self, 
                           analysis_data: Dict[str, Any], 
                           source_identifier: str,
                           custom_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Embed chord analysis data into the RAG system.
        
        Args:
            analysis_data: HorizonJam chord analysis results
            source_identifier: Source file or identifier
            custom_metadata: Additional metadata
            
        Returns:
            Embedding result with metadata
        """
        try:
            logger.info(f"🔗 Embedding chord analysis: {source_identifier}")
            
            # Create document text for embedding
            document_text = self._create_analysis_document(analysis_data, source_identifier)
            
            # Create metadata
            metadata = self._create_analysis_metadata(analysis_data, source_identifier, custom_metadata)
            
            # Generate unique ID
            doc_id = f"chord_analysis_{hash(source_identifier)}_{int(datetime.now().timestamp())}"
            
            # Add to collection
            if self.model_name == "openai":
                # ChromaDB will handle OpenAI embeddings
                self.collection.add(
                    documents=[document_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            else:
                # Generate embeddings with SentenceTransformer
                embedding = self.embedding_model.encode([document_text])[0].tolist()
                self.collection.add(
                    documents=[document_text],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                
            logger.info(f"✅ Embedded analysis: {doc_id}")
            
            return {
                "success": True,
                "document_id": doc_id,
                "source": source_identifier,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to embed chord analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": source_identifier
            }
            
    def _create_analysis_document(self, analysis_data: Dict[str, Any], source_identifier: str) -> str:
        """Create rich document text for semantic embedding."""
        try:
            # Extract key information
            summary = analysis_data.get("analysis_summary", {})
            chord_events = analysis_data.get("chord_events", [])
            
            detected_key = summary.get("detected_key", "Unknown")
            chord_progression = summary.get("chord_progression", "Unknown")
            total_chords = summary.get("total_chord_events", 0)
            
            # Build rich document text
            doc_parts = []
            
            # Header
            doc_parts.append(f"Musical Analysis of {Path(source_identifier).stem}")
            
            # Key and progression
            doc_parts.append(f"Detected Key: {detected_key}")
            doc_parts.append(f"Chord Progression: {chord_progression}")
            doc_parts.append(f"Total Chord Events: {total_chords}")
            
            # Detailed chord sequence
            if chord_events:
                doc_parts.append("Chord Sequence with Timing:")
                for event in chord_events:
                    chord = event.get("chord", "Unknown")
                    start_time = event.get("start_time_seconds", 0)
                    duration = event.get("duration_seconds", 0)
                    confidence = event.get("confidence", 0)
                    
                    doc_parts.append(
                        f"  {chord} at {start_time:.1f}s (duration: {duration:.1f}s, confidence: {confidence:.2f})"
                    )
            
            # Musical context
            doc_parts.append(f"Musical Context: This analysis contains chord progressions in {detected_key}")
            doc_parts.append(f"Harmonic Content: Features chords {chord_progression}")
            
            # Add guitar tabs if available
            guitar_tabs = analysis_data.get("guitar_tabs", [])
            if guitar_tabs:
                doc_parts.append("Guitar Chord Fingerings:")
                for tab in guitar_tabs:
                    chord = tab.get("chord", "Unknown")
                    strings = tab.get("strings", [])
                    doc_parts.append(f"  {chord}: {'-'.join(strings)}")
            
            return "\n".join(doc_parts)
            
        except Exception as e:
            logger.error(f"Failed to create analysis document: {e}")
            return f"Chord analysis of {source_identifier}"
            
    def _create_analysis_metadata(self, 
                                analysis_data: Dict[str, Any], 
                                source_identifier: str,
                                custom_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create comprehensive metadata for the analysis."""
        try:
            summary = analysis_data.get("analysis_summary", {})
            chord_events = analysis_data.get("chord_events", [])
            
            # Extract unique chords
            unique_chords = list(set([
                event.get("chord", "Unknown") 
                for event in chord_events 
                if event.get("chord")
            ]))
            
            # Sanitize chord progression (convert list to string if needed)
            chord_prog = summary.get("chord_progression", "Unknown")
            if isinstance(chord_prog, list):
                chord_prog = " - ".join(str(c) for c in chord_prog)
            elif not isinstance(chord_prog, str):
                chord_prog = str(chord_prog)
            
            # Calculate confidence safely
            confidences = [event.get("confidence", 0) for event in chord_events if event.get("confidence") is not None]
            avg_confidence = float(np.mean(confidences)) if confidences else 0.0
            if np.isnan(avg_confidence) or np.isinf(avg_confidence):
                avg_confidence = 0.0
            
            # Calculate total duration safely
            durations = []
            for event in chord_events:
                start = event.get("start_time_seconds", 0) or 0
                duration = event.get("duration_seconds", 0) or 0
                if isinstance(start, (int, float)) and isinstance(duration, (int, float)):
                    durations.append(start + duration)
            total_dur = float(max(durations)) if durations else 0.0
            
            metadata = {
                # Source information (ensure strings)
                "source_type": "chord_analysis",
                "source_file": str(Path(source_identifier).name),
                "source_path": str(source_identifier),
                
                # Musical information (ensure proper types)
                "detected_key": str(summary.get("detected_key", "Unknown")),
                "chord_progression": chord_prog,
                "total_chord_events": int(summary.get("total_chord_events", 0)),
                "unique_chords": ", ".join(unique_chords) if unique_chords else "None",
                "chord_count": int(len(unique_chords)),
                
                # Analysis metadata (ensure proper types)
                "estimated_accuracy": float(summary.get("estimated_accuracy_percent", 0) or 0),
                "analysis_timestamp": str(datetime.now().isoformat()),
                "embedding_model": str(self.model_name),
                
                # Duration and confidence (ensure floats)
                "total_duration": total_dur,
                "average_confidence": avg_confidence
            }
            
            # Add custom metadata if provided
            if custom_metadata:
                metadata.update(custom_metadata)
                
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create metadata: {e}")
            return {
                "source_type": "chord_analysis",
                "source_file": Path(source_identifier).name,
                "error": str(e)
            }
            
    def query(self, 
              question: str, 
              n_results: int = 5,
              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the RAG system with natural language.
        
        Args:
            question: Natural language query
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Formatted query results
        """
        try:
            logger.info(f"🔍 Querying RAG system: {question}")
            
            # Perform semantic search
            if self.model_name == "openai":
                # ChromaDB handles OpenAI embeddings automatically
                results = self.collection.query(
                    query_texts=[question],
                    n_results=n_results,
                    where=filters
                )
            else:
                # Generate query embedding with SentenceTransformer
                query_embedding = self.embedding_model.encode([question])[0].tolist()
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=filters
                )
            
            # Format results
            formatted_results = self._format_query_results(question, results, n_results)
            
            logger.info(f"✅ Found {len(formatted_results.get('results', []))} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {
                "error": str(e),
                "query": question,
                "results": []
            }
            
    def _format_query_results(self, query: str, results: Dict, n_results: int) -> Dict[str, Any]:
        """Format query results for consistent output."""
        try:
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]
            
            formatted_results = []
            
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                result = {
                    "id": ids[i] if i < len(ids) else None,
                    "rank": i + 1,
                    "document": doc,
                    "metadata": metadata,
                    "distance": distance,
                    "similarity_score": 1 - distance,  # Convert distance to similarity
                    "source_file": metadata.get("source_file", "Unknown"),
                    "detected_key": metadata.get("detected_key", "Unknown"),
                    "chord_progression": metadata.get("chord_progression", "Unknown"),
                    "unique_chords": metadata.get("unique_chords", []),
                    "total_duration": metadata.get("total_duration", 0)
                }
                formatted_results.append(result)
                
            return {
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "database_info": {
                    "collection": self.collection_name,
                    "total_documents": self.collection.count(),
                    "model": self.model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            return {
                "query": query,
                "error": str(e),
                "results": []
            }
            
    def search_by_key(self, key: str, mode: Optional[str] = None, n_results: int = 10) -> Dict[str, Any]:
        """Search analyses by musical key."""
        try:
            # Build key filter
            key_filter = {"detected_key": {"$contains": key}}
            if mode:
                key_filter["detected_key"]["$contains"] = f"{key} {mode}"
                
            query_text = f"songs in {key}"
            if mode:
                query_text += f" {mode}"
                
            return self.query(query_text, n_results=n_results, filters=key_filter)
            
        except Exception as e:
            logger.error(f"Key search failed: {e}")
            return {"error": str(e), "results": []}
            
    def search_by_chords(self, chords: List[str], n_results: int = 10) -> Dict[str, Any]:
        """Search analyses containing specific chords."""
        try:
            query_text = f"songs with chords {', '.join(chords)}"
            
            # Build chord filter (contains any of the specified chords)
            chord_filter = {"unique_chords": {"$in": chords}}
            
            return self.query(query_text, n_results=n_results, filters=chord_filter)
            
        except Exception as e:
            logger.error(f"Chord search failed: {e}")
            return {"error": str(e), "results": []}
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the RAG database."""
        try:
            # Get all documents to analyze
            all_results = self.collection.get()
            metadatas = all_results.get("metadatas", [])
            
            if not metadatas:
                return {
                    "total_documents": 0,
                    "message": "No documents in database"
                }
            
            # Analyze keys
            keys = [meta.get("detected_key", "Unknown") for meta in metadatas]
            key_counts = {}
            for key in keys:
                key_counts[key] = key_counts.get(key, 0) + 1
                
            # Analyze chords
            all_chords = []
            for meta in metadatas:
                chords = meta.get("unique_chords", [])
                all_chords.extend(chords)
                
            chord_counts = {}
            for chord in all_chords:
                chord_counts[chord] = chord_counts.get(chord, 0) + 1
                
            # Sort by frequency
            sorted_keys = sorted(key_counts.items(), key=lambda x: x[1], reverse=True)
            sorted_chords = sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "total_documents": len(metadatas),
                "database_path": self.db_path,
                "collection_name": self.collection_name,
                "embedding_model": self.model_name,
                "key_distribution": dict(sorted_keys),
                "most_common_chords": dict(sorted_chords[:20]),  # Top 20 chords
                "total_unique_keys": len(key_counts),
                "total_unique_chords": len(chord_counts),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
            
    def migrate_from_old_systems(self) -> Dict[str, Any]:
        """
        Migrate data from old RAG systems to the unified system.
        
        This method consolidates data from:
        - RAG/chroma_store
        - RAG/enhanced_chroma_store
        - Any other existing ChromaDB instances
        """
        try:
            logger.info("🔄 Starting migration from old RAG systems...")
            
            migration_stats = {
                "migrated_documents": 0,
                "errors": 0,
                "source_databases": []
            }
            
            # List of old database paths to check
            old_db_paths = [
                "RAG/chroma_store",
                "RAG/enhanced_chroma_store",
                "chroma_store",
                "enhanced_chroma_store"
            ]
            
            for old_path in old_db_paths:
                if os.path.exists(old_path):
                    try:
                        logger.info(f"📦 Migrating from {old_path}...")
                        
                        # Connect to old database
                        old_client = chromadb.PersistentClient(path=old_path)
                        collections = old_client.list_collections()
                        
                        for collection_info in collections:
                            old_collection = old_client.get_collection(collection_info.name)
                            
                            # Get all documents from old collection
                            old_data = old_collection.get()
                            
                            if old_data.get("documents"):
                                # Migrate documents
                                for i, (doc, metadata, doc_id) in enumerate(zip(
                                    old_data["documents"],
                                    old_data.get("metadatas", [{}] * len(old_data["documents"])),
                                    old_data.get("ids", [f"migrated_{i}" for i in range(len(old_data["documents"]))])
                                )):
                                    try:
                                        # Add migration metadata
                                        if not isinstance(metadata, dict):
                                            metadata = {}
                                        metadata["migrated_from"] = old_path
                                        metadata["migrated_at"] = datetime.now().isoformat()
                                        metadata["original_collection"] = collection_info.name
                                        
                                        # Add to unified collection
                                        new_id = f"migrated_{hash(doc_id)}_{int(datetime.now().timestamp())}"
                                        
                                        if self.model_name == "openai":
                                            self.collection.add(
                                                documents=[doc],
                                                metadatas=[metadata],
                                                ids=[new_id]
                                            )
                                        else:
                                            # Re-embed with current model
                                            embedding = self.embedding_model.encode([doc])[0].tolist()
                                            self.collection.add(
                                                documents=[doc],
                                                embeddings=[embedding],
                                                metadatas=[metadata],
                                                ids=[new_id]
                                            )
                                            
                                        migration_stats["migrated_documents"] += 1
                                        
                                    except Exception as e:
                                        logger.error(f"Failed to migrate document {doc_id}: {e}")
                                        migration_stats["errors"] += 1
                                        
                        migration_stats["source_databases"].append({
                            "path": old_path,
                            "collections": [c.name for c in collections]
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate from {old_path}: {e}")
                        migration_stats["errors"] += 1
                        
            logger.info(f"✅ Migration complete: {migration_stats['migrated_documents']} documents migrated")
            return migration_stats
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return {"error": str(e)}


# Global instance for easy access
_global_rag_system = None

def get_unified_rag_system(**kwargs) -> UnifiedRAGSystem:
    """Get or create the global unified RAG system instance."""
    global _global_rag_system
    
    if _global_rag_system is None:
        _global_rag_system = UnifiedRAGSystem(**kwargs)
        
    return _global_rag_system

def query_unified_rag(question: str, **kwargs) -> str:
    """
    Simple interface for querying the unified RAG system.
    
    Args:
        question: Natural language question
        **kwargs: Additional arguments for UnifiedRAGSystem
        
    Returns:
        Formatted response string
    """
    try:
        rag_system = get_unified_rag_system(**kwargs)
        results = rag_system.query(question)
        
        if results.get("error"):
            return f"I encountered an error: {results['error']}"
            
        search_results = results.get("results", [])
        
        if not search_results:
            return "I couldn't find relevant information for your question. Try asking about chord progressions, musical keys, or specific songs."
            
        # Format response
        response_parts = [f"Based on my music analysis database, here's what I found:\n"]
        
        for i, result in enumerate(search_results[:3], 1):
            source_file = result.get("source_file", "Unknown")
            detected_key = result.get("detected_key", "Unknown")
            chord_progression = result.get("chord_progression", "Unknown")
            similarity = result.get("similarity_score", 0)
            
            response_parts.append(f"{i}. **{source_file}**")
            response_parts.append(f"   - Key: {detected_key}")
            response_parts.append(f"   - Progression: {chord_progression}")
            response_parts.append(f"   - Relevance: {similarity:.1%}")
            response_parts.append("")
            
        response_parts.append("Would you like me to search for more specific information?")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Unified RAG query failed: {e}")
        return f"I encountered an error processing your question: {str(e)}"

if __name__ == "__main__":
    # Test the unified system
    print("🎸 Testing Unified RAG System")
    print("=" * 50)
    
    try:
        # Initialize system
        rag = UnifiedRAGSystem()
        
        # Show statistics
        stats = rag.get_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"   Total Documents: {stats.get('total_documents', 0)}")
        print(f"   Database Path: {stats.get('database_path', 'Unknown')}")
        print(f"   Embedding Model: {stats.get('embedding_model', 'Unknown')}")
        
        # Test query
        if stats.get('total_documents', 0) > 0:
            print(f"\n🔍 Testing Query:")
            response = query_unified_rag("songs in C major")
            print(response)
        else:
            print(f"\n📝 Database is empty. Run migration or embed some data first.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
