#!/usr/bin/env python3
"""
Complete Audio-to-RAG Pipeline Integration

This script implements the complete flow:
Audio Input (.wav, .mp3) → Chord/Key Extraction → JSON → ChromaDB Embeddings → RAG

Integrates HorizonJam chord detection with the ChromaDB RAG system for semantic
search and retrieval of musical content analysis.

Features:
- End-to-end audio processing pipeline
- Automatic chord/key extraction using HorizonJam
- JSON output generation and validation
- ChromaDB embedding and storage
- RAG integration for semantic search
- Batch processing capabilities
- Comprehensive error handling and logging

Usage:
    # Single audio file
    python audio_to_rag_pipeline.py --input song.wav
    
    # Batch processing
    python audio_to_rag_pipeline.py --batch-dir /path/to/audio/files/
    
    # Custom output and database paths
    python audio_to_rag_pipeline.py --input song.wav --output-dir ./analysis --db-path ./my_rag_db
"""

import os
import sys
import json
import logging
import argparse
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add HorizonJam to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'HorizonJam-master', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RAG'))

try:
    from pipeline import AccurateAudioToChordsPipeline
    from embed_chord_analysis import ChordAnalysisEmbedder
    from query_chord_analysis import ChordAnalysisQuerySystem
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the singleguitar directory")
    print("and that all required dependencies are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_to_rag_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AudioToRAGPipeline:
    """
    Complete pipeline for processing audio files into searchable RAG embeddings.
    
    Handles the entire flow from audio input to ChromaDB storage and enables
    semantic search of musical content.
    """
    
    def __init__(self,
                 output_dir: str = "./audio_analysis_output",
                 db_path: str = "RAG/enhanced_chroma_store",
                 collection_name: str = "chord_analysis",
                 model_name: str = "all-MiniLM-L6-v2",
                 horizon_jam_path: str = "HorizonJam-master"):
        """
        Initialize the audio-to-RAG pipeline.
        
        Args:
            output_dir: Directory for intermediate JSON outputs
            db_path: ChromaDB database path
            collection_name: ChromaDB collection name
            model_name: SentenceTransformer model name
            horizon_jam_path: Path to HorizonJam directory
        """
        self.output_dir = Path(output_dir)
        self.db_path = db_path
        self.collection_name = collection_name
        self.model_name = model_name
        self.horizon_jam_path = Path(horizon_jam_path)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.chord_pipeline = None
        self.embedder = None
        self.query_system = None
        
        self._initialize_components()
        
    def _initialize_components(self) -> None:
        """
        Initialize HorizonJam pipeline and RAG components.
        """
        try:
            # Initialize HorizonJam chord detection pipeline
            logger.info("Initializing HorizonJam chord detection pipeline...")
            self.chord_pipeline = AccurateAudioToChordsPipeline(
                confidence_threshold=0.3,
                min_note_duration=0.05,
                max_note_duration=4.0
            )
            
            # Initialize ChromaDB embedder
            logger.info("Initializing ChromaDB embedder...")
            self.embedder = ChordAnalysisEmbedder(
                db_path=self.db_path,
                collection_name=self.collection_name,
                model_name=self.model_name
            )
            
            # Initialize query system
            logger.info("Initializing RAG query system...")
            self.query_system = ChordAnalysisQuerySystem(
                db_path=self.db_path,
                collection_name=self.collection_name,
                model_name=self.model_name
            )
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
            
    def process_audio_file(self, audio_path: str, custom_output_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single audio file through the complete pipeline.
        
        Args:
            audio_path: Path to the audio file
            custom_output_name: Optional custom name for output files
            
        Returns:
            Processing results and metadata
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        logger.info(f"🎵 Processing audio file: {audio_path.name}")
        
        try:
            # Step 1: Extract chords and key using HorizonJam
            logger.info("Step 1: Extracting chords and key...")
            
            # Create temporary output directory for HorizonJam
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run HorizonJam pipeline
                horizon_results = self.chord_pipeline.run_pipeline(
                    str(audio_path), 
                    temp_dir
                )
                
                # Find the generated JSON file
                json_files = list(Path(temp_dir).glob("*.json"))
                if not json_files:
                    raise RuntimeError("HorizonJam did not generate JSON output")
                    
                horizon_json_path = json_files[0]
                
                # Load the analysis results
                with open(horizon_json_path, 'r') as f:
                    analysis_data = json.load(f)
                    
            # Step 2: Save formatted JSON output
            logger.info("Step 2: Saving formatted JSON output...")
            
            output_name = custom_output_name or f"{audio_path.stem}_analysis"
            json_output_path = self.output_dir / f"{output_name}.json"
            
            # Enhance the analysis data with additional metadata
            enhanced_analysis = self._enhance_analysis_data(analysis_data, audio_path)
            
            with open(json_output_path, 'w') as f:
                json.dump(enhanced_analysis, f, indent=2)
                
            logger.info(f"📄 JSON saved to: {json_output_path}")
            
            # Step 3: Create embeddings and store in ChromaDB
            logger.info("Step 3: Creating embeddings and storing in ChromaDB...")
            
            self.embedder.embed_analysis(enhanced_analysis, str(json_output_path))
            
            # Step 4: Verify storage and generate summary
            logger.info("Step 4: Generating processing summary...")
            
            processing_summary = {
                "audio_file": str(audio_path),
                "json_output": str(json_output_path),
                "analysis_summary": enhanced_analysis.get('analysis_summary', {}),
                "processing_timestamp": datetime.now().isoformat(),
                "database_path": self.db_path,
                "collection_name": self.collection_name,
                "status": "success"
            }
            
            logger.info(f"✅ Successfully processed: {audio_path.name}")
            return processing_summary
            
        except Exception as e:
            logger.error(f"Failed to process {audio_path.name}: {e}")
            error_summary = {
                "audio_file": str(audio_path),
                "error": str(e),
                "processing_timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            return error_summary
            
    def _enhance_analysis_data(self, analysis_data: Dict[str, Any], audio_path: Path) -> Dict[str, Any]:
        """
        Enhance analysis data with additional metadata for better RAG integration.
        
        Args:
            analysis_data: Original HorizonJam analysis data
            audio_path: Path to the source audio file
            
        Returns:
            Enhanced analysis data
        """
        # Add file metadata
        enhanced_data = analysis_data.copy()
        
        # Enhance metadata section
        if 'metadata' not in enhanced_data:
            enhanced_data['metadata'] = {}
            
        enhanced_data['metadata'].update({
            "source_audio_file": audio_path.name,
            "source_audio_path": str(audio_path),
            "file_size_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
            "processing_timestamp": datetime.now().isoformat(),
            "pipeline_version": "audio_to_rag_v1.0",
            "rag_integration": True
        })
        
        # Enhance analysis summary with additional insights
        if 'analysis_summary' in enhanced_data:
            summary = enhanced_data['analysis_summary']
            
            # Add musical insights
            chord_events = enhanced_data.get('chord_events', [])
            unique_chords = list(set(event['chord'] for event in chord_events))
            
            summary.update({
                "unique_chords": unique_chords,
                "unique_chord_count": len(unique_chords),
                "total_duration_seconds": max(
                    (event.get('duration_seconds', 0) for event in chord_events), 
                    default=0
                ),
                "average_chord_duration": (
                    sum(event.get('duration_seconds', 0) for event in chord_events) / 
                    len(chord_events) if chord_events else 0
                )
            })
            
        return enhanced_data
        
    def batch_process_directory(self, directory_path: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Process all audio files in a directory.
        
        Args:
            directory_path: Path to directory containing audio files
            file_extensions: List of file extensions to process (default: ['.wav', '.mp3', '.flac'])
            
        Returns:
            Batch processing results
        """
        if file_extensions is None:
            file_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.aac']
            
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
            
        # Find audio files
        audio_files = []
        for ext in file_extensions:
            audio_files.extend(directory_path.glob(f"*{ext}"))
            audio_files.extend(directory_path.glob(f"*{ext.upper()}"))
            
        if not audio_files:
            logger.warning(f"No audio files found in {directory_path}")
            return {"processed": 0, "errors": 0, "files": []}
            
        logger.info(f"Found {len(audio_files)} audio files to process")
        
        # Process files
        processed = 0
        errors = 0
        results = []
        
        for audio_file in audio_files:
            try:
                logger.info(f"Processing: {audio_file.name}")
                result = self.process_audio_file(str(audio_file))
                
                if result.get('status') == 'success':
                    processed += 1
                else:
                    errors += 1
                    
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {audio_file.name}: {e}")
                errors += 1
                results.append({
                    "audio_file": str(audio_file),
                    "error": str(e),
                    "status": "error"
                })
                
        batch_summary = {
            "directory": str(directory_path),
            "total_files": len(audio_files),
            "processed": processed,
            "errors": errors,
            "results": results,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Batch processing complete: {processed} processed, {errors} errors")
        return batch_summary
        
    def search_processed_content(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search the processed audio content using semantic similarity.
        
        Args:
            query: Natural language search query
            n_results: Number of results to return
            
        Returns:
            Search results
        """
        try:
            logger.info(f"Searching for: '{query}'")
            results = self.query_system.search_analysis(query, n_results)
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e), "results": []}
            
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the processed audio database.
        
        Returns:
            Database statistics
        """
        try:
            return self.query_system.get_analysis_statistics()
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return {"error": str(e)}

def main():
    """
    Main CLI interface for the audio-to-RAG pipeline.
    """
    parser = argparse.ArgumentParser(description="Complete Audio-to-RAG Pipeline")
    parser.add_argument("--input", "-i", help="Input audio file path")
    parser.add_argument("--batch-dir", "-b", help="Directory containing audio files for batch processing")
    parser.add_argument("--output-dir", "-o", default="./audio_analysis_output", help="Output directory for JSON files")
    parser.add_argument("--db-path", default="RAG/enhanced_chroma_store", help="ChromaDB database path")
    parser.add_argument("--collection", default="chord_analysis", help="ChromaDB collection name")
    parser.add_argument("--search", "-s", help="Search query for processed content")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    if not any([args.input, args.batch_dir, args.search, args.stats]):
        parser.print_help()
        return 1
        
    print("🎸 Complete Audio-to-RAG Pipeline")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        pipeline = AudioToRAGPipeline(
            output_dir=args.output_dir,
            db_path=args.db_path,
            collection_name=args.collection
        )
        
        # Process single file
        if args.input:
            print(f"\n📁 Processing single file: {args.input}")
            result = pipeline.process_audio_file(args.input)
            
            if result.get('status') == 'success':
                print(f"✅ Success!")
                print(f"📄 JSON output: {result['json_output']}")
                print(f"🎵 Key: {result['analysis_summary'].get('detected_key', 'Unknown')}")
                print(f"🎶 Progression: {result['analysis_summary'].get('chord_progression', 'Unknown')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        # Process batch directory
        if args.batch_dir:
            print(f"\n📁 Processing directory: {args.batch_dir}")
            batch_result = pipeline.batch_process_directory(args.batch_dir)
            
            print(f"📊 Batch Results:")
            print(f"  Total files: {batch_result['total_files']}")
            print(f"  Processed: {batch_result['processed']}")
            print(f"  Errors: {batch_result['errors']}")
            
        # Search processed content
        if args.search:
            print(f"\n🔍 Searching for: '{args.search}'")
            search_results = pipeline.search_processed_content(args.search)
            
            if search_results.get('error'):
                print(f"❌ Search error: {search_results['error']}")
            else:
                print(f"Found {search_results['total_results']} results:")
                for result in search_results['results'][:3]:
                    print(f"\n  📁 {result['source_file']}")
                    print(f"  🎵 Key: {result['detected_key']}")
                    print(f"  🎶 Progression: {result['chord_progression']}")
                    print(f"  📊 Similarity: {result['similarity_score']:.3f}")
                    
        # Show statistics
        if args.stats:
            print(f"\n📊 Database Statistics:")
            stats = pipeline.get_database_statistics()
            
            if stats.get('error'):
                print(f"❌ Error: {stats['error']}")
            else:
                print(f"Total analyses: {stats['total_analyses']}")
                print(f"\nTop keys:")
                for key, count in list(stats['key_distribution'].items())[:5]:
                    print(f"  {key}: {count}")
                print(f"\nMost common chords:")
                for chord, count in list(stats['most_common_chords'].items())[:8]:
                    print(f"  {chord}: {count}")
                    
        print(f"\n✅ Pipeline execution completed!")
        print(f"🗄️ Database: {args.db_path}")
        print(f"📁 Output directory: {args.output_dir}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        logger.error(f"Pipeline execution failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
