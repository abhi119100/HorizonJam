#!/usr/bin/env python3
"""
ChordAI Test Version - Test HorizonJam + RAG Integration

Tests the core functionality without requiring OpenAI API key
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add RAG system to path
current_dir = Path(__file__).parent
rag_path = current_dir / "RAG"
sys.path.insert(0, str(rag_path))

try:
    from query_chord_analysis import ChordAnalysisQuerySystem
    print("✅ RAG system imported")
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAG system import failed: {e}")
    RAG_AVAILABLE = False

class ChordAITester:
    """
    ChordAI Test System - Tests HorizonJam + RAG integration
    """
    
    def __init__(self, 
                 db_path: str = "RAG/enhanced_chroma_store",
                 collection_name: str = "chord_analysis"):
        """Initialize the ChordAI tester."""
        
        # Initialize RAG system if available
        if RAG_AVAILABLE:
            try:
                self.rag_system = ChordAnalysisQuerySystem(
                    db_path=db_path,
                    collection_name=collection_name
                )
                print("✅ RAG system initialized")
            except Exception as e:
                print(f"⚠️ RAG system initialization failed: {e}")
                self.rag_system = None
        else:
            self.rag_system = None
        
        # Paths
        self.project_root = Path(__file__).parent
        self.horizon_path = self.project_root / "HorizonJam-master"
        self.run_pipeline_path = self.horizon_path / "run_pipeline.py"
        
        # Verify HorizonJam exists
        if not self.run_pipeline_path.exists():
            raise FileNotFoundError(f"HorizonJam pipeline not found at {self.run_pipeline_path}")
            
        print("🎸 ChordAI Tester initialized")
        
    def test_audio_analysis(self, wav_path: str) -> Dict[str, Any]:
        """
        Test the complete workflow: HorizonJam + RAG context retrieval
        
        Args:
            wav_path: Path to WAV audio file
            
        Returns:
            Complete analysis results
        """
        print(f"\n🎵 Testing Analysis: {Path(wav_path).name}")
        print("=" * 50)
        
        try:
            # Step 1: Run HorizonJam chord detection
            print("🔍 Step 1: Testing HorizonJam chord detection...")
            chord_results = self._run_horizon_jam(wav_path)
            
            # Step 2: Display chord detection results
            print("\n🎼 Step 2: Chord Detection Results")
            self._display_chord_results(chord_results)
            
            # Step 3: Test RAG context retrieval
            print("\n🧠 Step 3: Testing RAG context retrieval...")
            rag_context = self._test_rag_context(chord_results)
            
            # Step 4: Show what would be sent to GPT-4o
            print("\n📝 Step 4: GPT-4o Input Preview")
            self._show_gpt_input_preview(chord_results, rag_context)
            
            # Complete response
            response = {
                "audio_file": Path(wav_path).name,
                "chord_analysis": chord_results,
                "rag_context": rag_context,
                "timestamp": datetime.now().isoformat(),
                "test_status": "SUCCESS"
            }
            
            print("\n✅ Test completed successfully!")
            return response
            
        except Exception as e:
            error_msg = f"❌ Test failed: {str(e)}"
            print(error_msg)
            return {"error": error_msg, "audio_file": Path(wav_path).name, "test_status": "FAILED"}
            
    def _run_horizon_jam(self, wav_path: str) -> Dict[str, Any]:
        """Run HorizonJam chord detection on WAV file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Run HorizonJam pipeline
                cmd = [
                    sys.executable, 
                    str(self.run_pipeline_path),
                    wav_path,
                    "-o", temp_dir,
                    "--confidence", "0.3",
                    "--min-duration", "0.05"
                ]
                
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.horizon_path))
                
                if result.returncode != 0:
                    raise RuntimeError(f"HorizonJam failed: {result.stderr}")
                
                # Find generated JSON
                json_files = list(Path(temp_dir).glob("*.json"))
                if not json_files:
                    # Parse terminal output if no JSON
                    return self._parse_terminal_output(result.stdout)
                
                # Load JSON results
                with open(json_files[0], 'r') as f:
                    data = json.load(f)
                    
                # Add terminal output for context
                data['terminal_output'] = result.stdout
                return data
                
            except Exception as e:
                raise RuntimeError(f"HorizonJam execution failed: {str(e)}")
                
    def _parse_terminal_output(self, output: str) -> Dict[str, Any]:
        """Parse HorizonJam terminal output into structured data."""
        import re
        
        # Extract key information from terminal output
        key_match = re.search(r'Detected Key: ([A-G][#b]? (?:major|minor))', output)
        detected_key = key_match.group(1) if key_match else "Unknown"
        
        # Extract chord progression
        prog_match = re.search(r'Progression: ([A-G#b\s-]+)', output)
        progression = prog_match.group(1).strip().split(' - ') if prog_match else []
        
        # Extract chord events
        chord_events = []
        event_pattern = r'(\d+)\. \[(\d{2}:\d{2}) - (\d{2}:\d{2})\] -> ([A-G][#b]?[^\s]*)'
        for match in re.finditer(event_pattern, output):
            chord_events.append({
                "start_time": match.group(2),
                "end_time": match.group(3),
                "chord": match.group(4)
            })
        
        return {
            "analysis_summary": {
                "detected_key": detected_key,
                "chord_progression": progression,
                "total_chords": len(chord_events)
            },
            "chord_events": chord_events,
            "terminal_output": output
        }
        
    def _display_chord_results(self, results: Dict[str, Any]):
        """Display chord detection results to user."""
        summary = results.get('analysis_summary', {})
        events = results.get('chord_events', [])
        
        print(f"🎹 Key: {summary.get('detected_key', 'Unknown')}")
        print(f"🎼 Progression: {' → '.join(summary.get('chord_progression', []))}")
        print(f"📊 Total Chords: {summary.get('total_chords', len(events))}")
        
        if events:
            print("\n⏰ Chord Timeline:")
            for i, event in enumerate(events[:8]):  # Show first 8
                start = event.get('start_time', f'{i*2}s')
                chord = event.get('chord', 'Unknown')
                print(f"  {start}: {chord}")
            if len(events) > 8:
                print(f"  ... and {len(events) - 8} more chords")
                
    def _test_rag_context(self, chord_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test RAG context retrieval."""
        if not self.rag_system:
            print("  ⚠️ RAG system not available - skipping context retrieval")
            return {"error": "RAG system not available", "context_chunks": []}
            
        try:
            summary = chord_results.get('analysis_summary', {})
            detected_key = summary.get('detected_key', 'Unknown')
            chord_progression = summary.get('chord_progression', [])
            
            # Build search queries for RAG system
            queries = []
            
            # Primary query based on detected key and progression
            if detected_key != 'Unknown' and chord_progression:
                progression_str = ' - '.join(chord_progression[:6])  # First 6 chords
                queries.append(f"Key of {detected_key} chord progression {progression_str}")
                
            # Secondary query for key-specific content
            if detected_key != 'Unknown':
                queries.append(f"Music theory {detected_key} key signature chords scales")
                
            # Individual chord queries for fingerings and shapes
            unique_chords = list(set(chord_progression[:8]))  # First 8 unique chords
            for chord in unique_chords:
                if chord and chord != 'Unknown':
                    queries.append(f"{chord} chord guitar fingering shape")
                    
            # Default fallback query
            if not queries:
                queries.append("Guitar chord progressions music theory scales")
                
            # Test context retrieval from multiple queries
            all_context = []
            for query in queries:
                try:
                    results = self.rag_system.search_analysis(query, n_results=3)
                    if results.get('results'):
                        all_context.extend(results['results'])
                        print(f"  📚 Found {len(results['results'])} results for: {query[:50]}...")
                except Exception as e:
                    print(f"  ⚠️ Query failed for '{query[:30]}...': {e}")
                    
            # Remove duplicates and limit results
            seen_ids = set()
            unique_context = []
            for item in all_context:
                item_id = item.get('id', str(item))
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_context.append(item)
                    
            print(f"  ✅ Retrieved {len(unique_context)} unique context chunks")
                    
            return {
                "queries_used": queries,
                "context_chunks": unique_context[:10],  # Limit to top 10 chunks
                "total_found": len(all_context),
                "unique_chunks": len(unique_context)
            }
            
        except Exception as e:
            print(f"  ❌ RAG context retrieval failed: {e}")
            return {"error": str(e), "context_chunks": []}
            
    def _show_gpt_input_preview(self, chord_results: Dict[str, Any], rag_context: Dict[str, Any]):
        """Show what would be sent to GPT-4o."""
        summary = chord_results.get('analysis_summary', {})
        events = chord_results.get('chord_events', [])
        context_chunks = rag_context.get('context_chunks', [])
        
        print("This is what would be sent to GPT-4o for tutoring:")
        print("-" * 50)
        
        print(f"**Detected Key:** {summary.get('detected_key', 'Unknown')}")
        print(f"**Chord Progression:** {' → '.join(summary.get('chord_progression', []))}")
        print(f"**Total Chords:** {len(events)}")
        
        print("\n**Chord Timeline:**")
        for event in events[:6]:  # First 6 chords
            start = event.get('start_time', 'N/A')
            chord = event.get('chord', 'Unknown')
            print(f"- {start}: {chord}")
            
        # Show RAG context preview
        if context_chunks:
            print(f"\n**RAG Context ({len(context_chunks)} chunks):**")
            for i, chunk in enumerate(context_chunks[:3]):  # Top 3 chunks
                chunk_text = chunk.get('text', '').strip()
                if chunk_text:
                    print(f"\nContext {i+1}: {chunk_text[:150]}...")
        else:
            print("\n**No RAG context available**")
            
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG knowledge base."""
        if self.rag_system:
            try:
                return self.rag_system.get_collection_stats()
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"error": "RAG system not available"}


def main():
    """Main function for ChordAI testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChordAI Test System")
    parser.add_argument("--wav", "-w", help="WAV file to test")
    parser.add_argument("--stats", "-s", action="store_true", help="Show RAG knowledge base stats")
    
    args = parser.parse_args()
    
    try:
        tester = ChordAITester()
        
        if args.stats:
            stats = tester.get_rag_stats()
            print("📊 RAG Knowledge Base Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        elif args.wav:
            print(f"🎵 Testing with WAV file: {args.wav}")
            result = tester.test_audio_analysis(args.wav)
            
            if result.get('test_status') == 'SUCCESS':
                print(f"\n🎉 Test completed successfully!")
                print(f"📁 Results saved in memory for analysis")
            else:
                print(f"\n❌ Test failed - check error messages above")
            
        else:
            print("🎸 ChordAI Test System")
            print("Use --help for options")
            print("Example: python chordai_test.py --wav 'HorizonJam-master/tests/test66.wav'")
            
    except Exception as e:
        print(f"❌ Failed to start tester: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
