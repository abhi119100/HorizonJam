#!/usr/bin/env python3
"""
RAG-Based Music Tutor System

Complete end-to-end pipeline:
Audio Input (.wav, .mp3) → Chord/Key Extraction → ChromaDB Storage → RAG Retrieval → GPT-4o Guidance

This system IS the music tutor - it processes audio, stores analysis in ChromaDB,
retrieves relevant context, and generates music-specific guidance using GPT-4o.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
horizon_src_path = os.path.join(current_dir, 'HorizonJam-master', 'src')
rag_path = os.path.join(current_dir, 'RAG')

sys.path.insert(0, horizon_src_path)
sys.path.insert(0, rag_path)

# Print paths for debugging
print(f"🔍 Looking for modules in:")
print(f"  - HorizonJam: {horizon_src_path}")
print(f"  - RAG: {rag_path}")

# Fix import path issues by temporarily modifying sys.path
original_path = sys.path.copy()
try:
    # Add the HorizonJam src directory to Python path
    if horizon_src_path not in sys.path:
        sys.path.insert(0, horizon_src_path)
    
    # Import the pipeline class directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("pipeline", os.path.join(horizon_src_path, "pipeline.py"))
    pipeline_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline_module)
    
    AccurateAudioToChordsPipeline = pipeline_module.AccurateAudioToChordsPipeline
    print("✅ HorizonJam pipeline imported successfully")
    
except Exception as e:
    print(f"❌ HorizonJam import failed: {e}")
    print("Available files in HorizonJam src:")
    if os.path.exists(horizon_src_path):
        for f in os.listdir(horizon_src_path):
            if f.endswith('.py'):
                print(f"  - {f}")
    sys.exit(1)
finally:
    # Restore original path
    sys.path = original_path

try:
    from embed_chord_analysis import ChordAnalysisEmbedder
    from query_chord_analysis import ChordAnalysisQuerySystem
    print("✅ RAG modules imported")
except ImportError as e:
    print(f"❌ RAG import failed: {e}")
    print("Available files in RAG:")
    if os.path.exists(rag_path):
        for f in os.listdir(rag_path):
            if f.endswith('.py'):
                print(f"  - {f}")
    sys.exit(1)

try:
    from openai import OpenAI
    print("✅ OpenAI imported")
except ImportError as e:
    print(f"❌ OpenAI import failed: {e}")
    print("Install with: pip install openai")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGMusicTutor:
    """
    Complete RAG-based music tutor system.
    
    Handles the entire pipeline from audio input to GPT-4o guidance:
    1. Audio processing and chord extraction
    2. ChromaDB storage and embedding
    3. RAG retrieval of relevant context
    4. GPT-4o music guidance generation
    """
    
    def __init__(self,
                 openai_api_key: Optional[str] = None,
                 model: str = "gpt-4o",
                 db_path: str = "RAG/enhanced_chroma_store",
                 collection_name: str = "chord_analysis",
                 temp_output_dir: str = "./temp_analysis"):
        """
        Initialize the RAG music tutor system.
        
        Args:
            openai_api_key: OpenAI API key
            model: GPT model to use
            db_path: ChromaDB database path
            collection_name: ChromaDB collection name
            temp_output_dir: Temporary directory for analysis files
        """
        # Initialize OpenAI
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Initialize paths
        self.db_path = db_path
        self.collection_name = collection_name
        self.temp_output_dir = Path(temp_output_dir)
        self.temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline components
        self._initialize_components()
        
        print(f"🎸 RAG Music Tutor initialized with {self.model}")
        
    def _initialize_components(self):
        """Initialize all pipeline components."""
        try:
            # 1. HorizonJam chord detection pipeline
            self.chord_pipeline = AccurateAudioToChordsPipeline(
                confidence_threshold=0.3,
                min_note_duration=0.05,
                max_note_duration=4.0
            )
            
            # 2. ChromaDB embedder
            self.embedder = ChordAnalysisEmbedder(
                db_path=self.db_path,
                collection_name=self.collection_name
            )
            
            # 3. RAG query system
            self.query_system = ChordAnalysisQuerySystem(
                db_path=self.db_path,
                collection_name=self.collection_name
            )
            
            logger.info("✅ All pipeline components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
            
    def process_audio_and_teach(self, audio_path: str, user_question: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete pipeline: Process audio and provide music guidance.
        
        Args:
            audio_path: Path to audio file
            user_question: Optional specific question about the audio
            
        Returns:
            Complete analysis and guidance
        """
        print(f"🎵 Processing audio: {Path(audio_path).name}")
        
        try:
            # Step 1: Extract chords and key using HorizonJam
            print("Step 1: Extracting chords and key...")
            analysis_data = self._extract_chords_and_key(audio_path)
            
            # Step 2: Store in ChromaDB
            print("Step 2: Storing analysis in ChromaDB...")
            self._store_in_chromadb(analysis_data, audio_path)
            
            # Step 3: Retrieve relevant context using RAG
            print("Step 3: Retrieving relevant musical context...")
            context = self._retrieve_musical_context(analysis_data, user_question)
            
            # Step 4: Generate GPT-4o guidance
            print("Step 4: Generating music guidance...")
            guidance = self._generate_music_guidance(analysis_data, context, user_question)
            
            # Compile complete response
            complete_response = {
                "audio_file": Path(audio_path).name,
                "chord_analysis": analysis_data,
                "retrieved_context": context,
                "music_guidance": guidance,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            print("✅ Complete analysis and guidance generated!")
            return complete_response
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"error": str(e), "audio_file": Path(audio_path).name}
            
    def _extract_chords_and_key(self, audio_path: str) -> Dict[str, Any]:
        """Step 1: Extract chords and key using HorizonJam."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run HorizonJam pipeline
            horizon_results = self.chord_pipeline.run_pipeline(str(audio_path), temp_dir)
            
            # Find generated JSON
            json_files = list(Path(temp_dir).glob("*.json"))
            if not json_files:
                raise RuntimeError("HorizonJam did not generate JSON output")
                
            with open(json_files[0], 'r') as f:
                analysis_data = json.load(f)
                
            # Enhance with metadata
            analysis_data['metadata'] = analysis_data.get('metadata', {})
            analysis_data['metadata'].update({
                "source_audio_file": Path(audio_path).name,
                "processing_timestamp": datetime.now().isoformat(),
                "pipeline_version": "rag_tutor_v1.0"
            })
            
            return analysis_data
            
    def _store_in_chromadb(self, analysis_data: Dict[str, Any], audio_path: str):
        """Step 2: Store analysis in ChromaDB."""
        # Save temporary JSON file
        temp_json_path = self.temp_output_dir / f"{Path(audio_path).stem}_analysis.json"
        with open(temp_json_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
            
        # Embed in ChromaDB
        self.embedder.embed_analysis(analysis_data, str(temp_json_path))
        
    def _retrieve_musical_context(self, analysis_data: Dict[str, Any], user_question: Optional[str] = None) -> Dict[str, Any]:
        """Step 3: Retrieve relevant musical context using RAG."""
        summary = analysis_data.get('analysis_summary', {})
        detected_key = summary.get('detected_key', 'Unknown')
        chord_progression = summary.get('chord_progression', [])
        
        # Build search queries
        queries = []
        
        # Primary query based on detected key and progression
        if detected_key != 'Unknown' and chord_progression:
            progression_str = ' - '.join(chord_progression[:6])  # First 6 chords
            queries.append(f"Key of {detected_key} chord progression {progression_str}")
            
        # Secondary query for key-specific content
        if detected_key != 'Unknown':
            queries.append(f"Music theory {detected_key} key signature chords")
            
        # User-specific query if provided
        if user_question:
            queries.append(user_question)
            
        # Default fallback query
        if not queries:
            queries.append("Guitar chord progressions music theory")
            
        # Retrieve context from multiple queries
        all_context = []
        for query in queries:
            try:
                results = self.query_system.search_analysis(query, n_results=3)
                if results.get('results'):
                    all_context.extend(results['results'])
            except Exception as e:
                logger.warning(f"Query failed for '{query}': {e}")
                
        return {
            "queries_used": queries,
            "retrieved_chunks": all_context[:8],  # Limit to top 8 chunks
            "context_count": len(all_context)
        }
        
    def _generate_music_guidance(self, analysis_data: Dict[str, Any], context: Dict[str, Any], user_question: Optional[str] = None) -> str:
        """Step 4: Generate GPT-4o music guidance."""
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Build user prompt with analysis and context
        user_prompt = self._build_user_prompt(analysis_data, context, user_question)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"GPT-4o generation failed: {e}")
            return f"❌ Failed to generate guidance: {str(e)}"
            
    def _build_system_prompt(self) -> str:
        """Build the system prompt for GPT-4o."""
        return """You are an expert music tutor and guitarist with deep knowledge of music theory, chord progressions, and guitar techniques.

Your role is to analyze chord progressions and provide educational, practical guidance to help musicians understand and improve their playing.

Key capabilities:
- Analyze chord progressions and identify patterns
- Explain music theory concepts clearly
- Suggest practice techniques and exercises
- Provide context about musical styles and genres
- Offer constructive feedback on harmonic choices
- Recommend next steps for learning and improvement

Always be:
- Educational and encouraging
- Specific and actionable in your advice
- Clear in explaining complex concepts
- Supportive of the musician's learning journey

Format your responses with clear sections and practical takeaways."""

    def _build_user_prompt(self, analysis_data: Dict[str, Any], context: Dict[str, Any], user_question: Optional[str] = None) -> str:
        """Build the user prompt with analysis data and retrieved context."""
        summary = analysis_data.get('analysis_summary', {})
        chord_events = analysis_data.get('chord_events', [])
        
        prompt_parts = []
        
        # Analysis summary
        prompt_parts.append("## Chord Analysis Results")
        prompt_parts.append(f"**Detected Key:** {summary.get('detected_key', 'Unknown')}")
        prompt_parts.append(f"**Chord Progression:** {' - '.join(summary.get('chord_progression', []))}")
        prompt_parts.append(f"**Confidence:** {summary.get('confidence', 'N/A')}")
        
        # Chord events (first 10)
        if chord_events:
            prompt_parts.append("\n**Chord Timeline:**")
            for i, event in enumerate(chord_events[:10]):
                time_str = f"{event.get('start_time', 0):.1f}s"
                chord = event.get('chord', 'Unknown')
                prompt_parts.append(f"- {time_str}: {chord}")
            if len(chord_events) > 10:
                prompt_parts.append(f"... and {len(chord_events) - 10} more chords")
                
        # Retrieved context
        if context.get('retrieved_chunks'):
            prompt_parts.append("\n## Relevant Musical Context")
            for i, chunk in enumerate(context['retrieved_chunks'][:5]):
                chunk_text = chunk.get('text', '').strip()
                if chunk_text:
                    prompt_parts.append(f"**Context {i+1}:** {chunk_text[:200]}...")
                    
        # User question
        if user_question:
            prompt_parts.append(f"\n## Specific Question")
            prompt_parts.append(f"The user asks: {user_question}")
            
        # Request for guidance
        prompt_parts.append("\n## Request")
        if user_question:
            prompt_parts.append("Please analyze this chord progression and answer the user's specific question. Provide educational insights, practical advice, and suggestions for improvement.")
        else:
            prompt_parts.append("Please analyze this chord progression and provide educational insights, practical advice, and suggestions for improvement. Include music theory explanations and practice recommendations.")
            
        return "\n".join(prompt_parts)
        
    def ask_question(self, question: str, audio_path: Optional[str] = None) -> str:
        """Ask a music-related question, optionally with audio context."""
        if audio_path:
            # Process audio and include in context
            result = self.process_audio_and_teach(audio_path, question)
            return result.get('music_guidance', 'No guidance generated')
        else:
            # Query existing knowledge base
            try:
                context_results = self.query_system.search_analysis(question, n_results=5)
                context = {
                    "queries_used": [question],
                    "retrieved_chunks": context_results.get('results', []),
                    "context_count": len(context_results.get('results', []))
                }
                
                # Generate response without audio analysis
                return self._generate_music_guidance({}, context, question)
                
            except Exception as e:
                return f"❌ Failed to process question: {str(e)}"
                
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            return self.query_system.get_collection_stats()
        except Exception as e:
            return {"error": str(e)}
            
    def interactive_session(self):
        """Start an interactive music tutoring session."""
        print("\n🎸 RAG Music Tutor - Interactive Session")
        print("Commands:")
        print("  - Type a question to get music guidance")
        print("  - 'analyze <audio_file>' to process audio")
        print("  - 'stats' to see knowledge base statistics")
        print("  - 'quit' to exit")
        print("\n" + "="*50)
        
        while True:
            try:
                user_input = input("\n🎵 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Keep practicing!")
                    break
                    
                elif user_input.lower() == 'stats':
                    stats = self.get_stats()
                    print(f"\n📊 Knowledge Base Stats:")
                    for key, value in stats.items():
                        print(f"  - {key}: {value}")
                        
                elif user_input.lower().startswith('analyze '):
                    audio_path = user_input[8:].strip()
                    if os.path.exists(audio_path):
                        print(f"\n🎵 Analyzing {Path(audio_path).name}...")
                        result = self.process_audio_and_teach(audio_path)
                        print(f"\n🎸 Music Tutor: {result.get('music_guidance', 'No guidance generated')}")
                    else:
                        print(f"❌ Audio file not found: {audio_path}")
                        
                elif user_input:
                    print("\n🤔 Thinking...")
                    response = self.ask_question(user_input)
                    print(f"\n🎸 Music Tutor: {response}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye! Keep practicing!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main function to run the RAG Music Tutor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG-based Music Tutor System")
    parser.add_argument("--audio", "-a", help="Audio file to analyze")
    parser.add_argument("--question", "-q", help="Question to ask about the audio")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive session")
    parser.add_argument("--stats", "-s", action="store_true", help="Show knowledge base stats")
    
    args = parser.parse_args()
    
    try:
        # Initialize tutor
        tutor = RAGMusicTutor()
        
        if args.stats:
            stats = tutor.get_stats()
            print("📊 Knowledge Base Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        elif args.audio:
            print(f"🎵 Processing audio: {args.audio}")
            result = tutor.process_audio_and_teach(args.audio, args.question)
            
            print("\n" + "="*60)
            print("🎸 MUSIC TUTOR ANALYSIS & GUIDANCE")
            print("="*60)
            print(result.get('music_guidance', 'No guidance generated'))
            
        elif args.question:
            print(f"🤔 Answering: {args.question}")
            response = tutor.ask_question(args.question)
            print(f"\n🎸 Music Tutor: {response}")
            
        elif args.interactive:
            tutor.interactive_session()
            
        else:
            print("🎸 RAG Music Tutor System")
            print("Use --help to see available options")
            print("Quick start: python rag_music_tutor.py --interactive")
            
    except Exception as e:
        print(f"❌ Failed to initialize tutor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
