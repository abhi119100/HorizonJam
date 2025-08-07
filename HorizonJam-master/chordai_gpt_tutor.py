#!/usr/bin/env python3
"""
ChordAI + RAG-Enhanced GPT-4o Music Tutor

Real-world scenario: ChordAI-level chord detection + RAG-enhanced intelligent music tutoring
WAV Audio → HorizonJam Chord Detection → Display Results → RAG Context → GPT-4o Explains Chord Shapes & Scales
"""

# --- Silence noise early (before any third-party imports) ---
import os
import sys
import warnings
from pathlib import Path

# Suppress all warnings immediately
warnings.filterwarnings('ignore')

# Import centralized logging configuration
utils_path = Path(__file__).parent / "utils"
sys.path.insert(0, str(utils_path))

try:
    from logging_config import setup_logging, suppress_warnings
    # Set up logging configuration
    setup_logging()
except ImportError:
    pass  # Continue without logging configuration if utils not available

# Remove utils from path to avoid conflicts
if str(utils_path) in sys.path:
    sys.path.remove(str(utils_path))
# ----------------------------------------------------------------

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not found. Install with: pip install python-dotenv")
    print("⚠️ Falling back to system environment variables")

# Add RAG system to path
current_dir = Path(__file__).parent
rag_path = current_dir / "RAG"
sys.path.insert(0, str(rag_path))

try:
    from openai import OpenAI
    print("✅ OpenAI imported")
except ImportError:
    print("❌ OpenAI not found. Install with: pip install openai")
    sys.exit(1)

# Import unified RAG system
try:
    from unified_rag_system import UnifiedRAGSystem
    print("✅ Unified RAG system imported")
except ImportError as e:
    print(f"⚠️ Unified RAG system not available: {e}")
    UnifiedRAGSystem = None
    query_unified_rag = None

class ChordAIRAGTutor:
    """
    ChordAI + RAG-Enhanced GPT-4o Music Tutor System
    
    Processes WAV files → Detects chords → Retrieves RAG context → Provides intelligent tutoring
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 db_path: Optional[str] = None,
                 collection_name: Optional[str] = None):
        """Initialize the ChordAI + RAG-enhanced tutor."""
        # Initialize OpenAI with .env support
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Add OPENAI_API_KEY to .env file or set environment variable.")
        
        # Use .env file values or defaults for unified RAG system
        self.db_path = db_path or os.getenv("RAG_DB_PATH", "RAG/unified_chroma_store")
        self.collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", "music_theory")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize Unified RAG system
        try:
            if UnifiedRAGSystem:
                self.rag_system = UnifiedRAGSystem(
                    db_path=self.db_path,
                    collection_name=self.collection_name,
                    model_name="openai",
                    openai_api_key=self.api_key
                )
                print("✅ Unified RAG system initialized")
            else:
                raise ImportError("UnifiedRAGSystem not available")
        except Exception as e:
            print(f"⚠️ Unified RAG system initialization failed: {e}")
            print("Falling back to direct GPT-4o mode")
            self.rag_system = None
        
        # Paths
        self.project_root = Path(__file__).parent
        self.horizon_path = self.project_root  # We're already in HorizonJam-master
        self.run_pipeline_path = self.horizon_path / "run_pipeline.py"
        
        # Verify HorizonJam exists
        if not self.run_pipeline_path.exists():
            raise FileNotFoundError(f"HorizonJam pipeline not found at {self.run_pipeline_path}")
            
        print("🎸 ChordAI + RAG-Enhanced Music Tutor initialized")
        
    def analyze_audio(self, wav_path: str, user_question: Optional[str] = None, confidence: float = 0.3, min_duration: float = 0.05, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete ChordAI workflow: Analyze audio and provide RAG-enhanced tutoring.
        
        Args:
            wav_path: Path to WAV audio file
            user_question: Optional specific question about the music
            confidence: Chord detection confidence threshold (default: 0.3)
            min_duration: Minimum chord duration in seconds (default: 0.05)
            output_dir: Optional output directory for JSON results
            
        Returns:
            Complete analysis and tutoring response
        """
        print(f"\n🎵 Analyzing: {Path(wav_path).name}")
        print("=" * 50)
        
        try:
            # Step 1: Run HorizonJam chord detection
            print("🔍 Step 1: Detecting chords with HorizonJam...")
            chord_results = self._run_horizon_jam(wav_path, confidence, min_duration)
            
            # Step 2: Display chord detection results and generate chord tabs
            print("\n🎼 Step 2: Chord Detection Results")
            self._display_chord_results(chord_results)
            
            # Step 3: Retrieve RAG context
            print("\n🧠 Step 3: Retrieving musical context from knowledge base...")
            rag_context = self._retrieve_rag_context(chord_results, user_question)
            
            # Step 4: Embed analysis into RAG system for future learning
            print("\n🧠 Step 4: Embedding analysis into knowledge base...")
            embedding_result = self._embed_analysis_to_rag(chord_results, Path(wav_path).name)
            
            # Step 5: Generate RAG-enhanced GPT-4o tutoring
            print("\n🎸 Step 5: Generating RAG-enhanced music tutoring...")
            tutoring = self._generate_rag_tutoring(chord_results, rag_context, user_question)
            
            # Complete response with properly formatted chord tabs
            response = {
                "audio_file": Path(wav_path).name,
                "chord_analysis": chord_results,
                "chord_tabs": chord_results.get("chord_tabs", []),
                "rag_context": rag_context,
                "embedding_result": embedding_result,
                "tutoring": tutoring,
                "timestamp": datetime.now().isoformat()
            }
            
            print("\n🎸 RAG-Enhanced Music Tutor Response:")
            print("-" * 40)
            print(tutoring)
            
            # Save JSON output if output directory is specified
            if output_dir:
                self._save_json_output(response, output_dir)
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Analysis failed: {str(e)}"
            print(error_msg)
            return {"error": error_msg, "audio_file": Path(wav_path).name}
            
    def _run_horizon_jam(self, wav_path: str, confidence: float = 0.3, min_duration: float = 0.05) -> Dict[str, Any]:
        """Run HorizonJam chord detection on WAV file."""
        import tempfile
        import subprocess
        import json
        from pathlib import Path
        
        # Use the existing temp_output directory that HorizonJam uses
        output_dir = self.horizon_path / "temp_output"
        output_dir.mkdir(exist_ok=True)
        
        # Clean any existing files
        for file in output_dir.glob("*"):
            file.unlink()
        
        try:
            # Handle WAV path correctly for HorizonJam
            wav_path_obj = Path(wav_path)
            
            # If it's an absolute path, use it directly
            if wav_path_obj.is_absolute():
                if wav_path_obj.exists():
                    wav_rel_path = wav_path_obj
                else:
                    raise FileNotFoundError(f"WAV file not found: {wav_path_obj}")
            else:
                # For relative paths, try different base directories
                possible_paths = [
                    self.project_root / wav_path_obj,  # Relative to project root (same as HorizonJam directory)
                    self.project_root / "tests" / wav_path_obj,  # Check tests directory
                    Path(wav_path_obj)  # Current working directory
                ]
                
                wav_rel_path = None
                for possible_path in possible_paths:
                    if possible_path.exists():
                        wav_rel_path = possible_path
                        break
                
                if wav_rel_path is None:
                    raise FileNotFoundError(f"WAV file not found in any of these locations: {[str(p) for p in possible_paths]}")
            
            # Determine the correct path to pass to HorizonJam pipeline
            # If the WAV file is under the HorizonJam directory, use relative path
            # Otherwise, use absolute path
            try:
                wav_for_cmd = wav_rel_path.relative_to(self.horizon_path)
            except ValueError:
                # WAV file is not under HorizonJam directory, use absolute path
                wav_for_cmd = wav_rel_path.resolve()
            
            # Run HorizonJam pipeline from the HorizonJam directory
            # Use relative output path since we're running from HorizonJam directory
            output_rel_path = output_dir.name  # Just use the directory name since we're in the right location
            
            cmd = [
                sys.executable, 
                "run_pipeline.py",  # Use relative path since we're in HorizonJam directory
                str(wav_for_cmd),
                "-o", output_rel_path,  # Just the directory name
                "--confidence", str(confidence),
                "--min-duration", str(min_duration)
            ]
            
            # Run the pipeline command
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=str(self.horizon_path))
            
            # Filter and display only relevant output
            if not os.getenv("CHORDAI_DEBUG"):
                # Import filter function from log silencer
                try:
                    sys.path.insert(0, str(Path(__file__).parent / "utils"))
                    from log_silencer import filter_subprocess_output
                    
                    # Filter stdout to show only relevant lines
                    stdout_lines = result.stdout.splitlines()
                    filtered_lines = filter_subprocess_output(stdout_lines)
                    
                    if filtered_lines:
                        print("\n".join(filtered_lines))
                    
                    # Only show stderr if there are actual errors (not warnings)
                    if result.stderr.strip():
                        stderr_lines = result.stderr.splitlines()
                    # Filter out common warnings that are not actual errors
                    try:
                        from logging_config import filter_output_lines
                        error_lines = filter_output_lines(stderr_lines)
                    except ImportError:
                        error_lines = [line for line in stderr_lines if not any(ignore in line.lower() for ignore in [
                            'pkg_resources', 'userwarning', 'deprecated', 'setuptools', 'coremltools',
                            'langchaindeprecationwarning', 'unicodeencodeerror', 'charmap'
                        ])]
                    if error_lines:
                        print("\n".join(error_lines))
                    
                    sys.path.remove(str(Path(__file__).parent / "utils"))
                except ImportError:
                    # Fallback to original output if filter not available
                    if result.stdout.strip():
                        print(f"  STDOUT (first 500 chars): {result.stdout[:500]}")
            else:
                # Debug mode: show full output
                print(f"🔍 Subprocess results:")
                print(f"  Return code: {result.returncode}")
                print(f"  STDOUT length: {len(result.stdout)} chars")
                print(f"  STDERR length: {len(result.stderr)} chars")
                
                if result.stdout.strip():
                    print(f"  STDOUT (first 500 chars): {result.stdout[:500]}")
                if result.stderr.strip():
                    print(f"  STDERR (first 500 chars): {result.stderr[:500]}")
            
            # Check for actual errors (ignore deprecation warnings)
            if result.returncode != 0:
                # Filter out pkg_resources warnings which are not actual errors
                stderr_lines = result.stderr.strip().split('\n')
                actual_errors = [line for line in stderr_lines if not (
                    'pkg_resources' in line or 
                    'UserWarning' in line or 
                    'deprecated' in line or
                    'setuptools' in line
                )]
                
                if actual_errors:
                    raise RuntimeError(f"HorizonJam failed: {' '.join(actual_errors)}")
                else:
                    print("  ⚠️ Ignoring deprecation warnings from dependencies")
            
            # Find and read generated JSON file directly
            # Look for common HorizonJam output files
            possible_files = [
                "chord_analysis_structured.json",
                "chord_analysis_output.json", 
                "chords.json",
                "analysis.json"
            ]
            
            json_file = None
            
            # Check for known JSON file names first
            for filename in possible_files:
                candidate = output_dir / filename
                if candidate.exists():
                    json_file = candidate
                    break
            
            # Fallback to any JSON file in the directory
            if not json_file:
                json_files = list(output_dir.glob("*.json"))
                if json_files:
                    json_file = json_files[0]
            
            if not json_file:
                # List directory contents for debugging
                files = list(output_dir.iterdir())
                file_list = [f.name for f in files]
                raise RuntimeError(f"No JSON output file generated by HorizonJam. Found files: {file_list}")
            
            print(f"📄 Reading chord analysis from: {json_file.name}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                chord_data = json.load(f)
            
            # Validate JSON structure - check for required fields
            if not isinstance(chord_data, dict):
                raise RuntimeError("Invalid JSON structure from HorizonJam - not a dictionary")
            
            if 'analysis_summary' not in chord_data:
                raise RuntimeError("Invalid JSON structure from HorizonJam - missing analysis_summary")
            
            # Ensure analysis_summary has required fields
            summary = chord_data.get('analysis_summary', {})
            if not summary.get('detected_key'):
                summary['detected_key'] = 'Unknown'
            if not summary.get('chord_progression'):
                summary['chord_progression'] = []
            if not summary.get('total_chord_events'):
                summary['total_chord_events'] = len(chord_data.get('chord_events', []))
            
            # Parse terminal output to get complete progression and accuracy
            terminal_data = self._parse_terminal_output(result.stdout)
            
            # Merge terminal data with JSON data for complete information
            terminal_summary = terminal_data.get('analysis_summary', {})
            json_summary = chord_data.get('analysis_summary', {})
            
            # Update chord progression from terminal (more complete)
            if terminal_summary.get('chord_progression'):
                json_summary['chord_progression'] = terminal_summary['chord_progression']
            
            # Update accuracy from terminal
            if terminal_summary.get('accuracy'):
                json_summary['accuracy'] = terminal_summary['accuracy']
            
            # Update total chords from terminal
            if terminal_summary.get('total_chords'):
                json_summary['total_chords'] = terminal_summary['total_chords']
            
            # Update BPM from terminal
            if terminal_summary.get('bpm'):
                json_summary['bpm'] = terminal_summary['bpm']
            
            # Ensure chord_events from terminal are included
            if terminal_data.get('chord_events'):
                chord_data['chord_events'] = terminal_data['chord_events']
            
            print("✅ Successfully loaded chord analysis from JSON and terminal output")
            return chord_data
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            return {
                "analysis_summary": {
                    "detected_key": "Unknown",
                    "chord_progression": [],
                    "total_chord_events": 0,
                    "estimated_accuracy_percent": 0.0
                },
                "chord_events": [],
                "error": str(e)
            }
        finally:
            # Clean up output directory
            try:
                for file in output_dir.glob("*"):
                    file.unlink()
                output_dir.rmdir()
            except:
                pass  # Ignore cleanup errors
        
    def _parse_terminal_output(self, output: str) -> Dict[str, Any]:
        """Parse HorizonJam terminal output into structured data."""
        import re
        
        # Extract key information from terminal output
        key_match = re.search(r'\[KEY\] Detected Key: ([A-G][#b]? (?:major|minor))', output)
        detected_key = key_match.group(1) if key_match else "Unknown"
        
        # Extract chord progression - improved regex to capture all chord types
        prog_match = re.search(r'Progression: ([^\n]+)', output)
        progression = prog_match.group(1).strip().split(' - ') if prog_match else []
        
        # Extract total chord events
        total_match = re.search(r'\[TOTAL\] Total chord events: (\d+)', output)
        total_chords = int(total_match.group(1)) if total_match else 0
        
        # Extract chord events with correct pattern including duration
        chord_events = []
        event_pattern = r'(\d+)\. \[(\d{2}:\d{2}) - (\d{2}:\d{2})\] -> ([A-G][#b]?[^\s]*) \(play #\d+\) \(([\d.]+)s\)'
        for match in re.finditer(event_pattern, output):
            chord_events.append({
                "event_number": int(match.group(1)),
                "start_time": match.group(2),
                "end_time": match.group(3),
                "chord": match.group(4),
                "duration_seconds": float(match.group(5))
            })
        
        # Extract BPM if available
        bpm_match = re.search(r'\[BPM\] Tempo: ([\d.]+) BPM', output)
        bpm = float(bpm_match.group(1)) if bpm_match else None
        
        # Extract accuracy if available
        accuracy_match = re.search(r'Estimated accuracy: ([\d.]+)%', output)
        accuracy = float(accuracy_match.group(1)) if accuracy_match else None
        
        return {
            "analysis_summary": {
                "detected_key": detected_key,
                "chord_progression": progression,
                "total_chords": total_chords,
                "bpm": bpm,
                "accuracy": accuracy
            },
            "chord_events": chord_events,
            "terminal_output": output
        }
        
    def _display_chord_results(self, results: Dict[str, Any]):
        """Display concise chord detection results."""
        summary = results.get('analysis_summary', {})
        detected_key = summary.get('detected_key', 'Unknown')
        accuracy = summary.get('accuracy', 'Unknown')
        bpm = summary.get('bpm', 'Unknown')
        
        print("\n🎼 Step 2: Chord Detection Results")
        print(f"🎹 Key: {detected_key} | 🎯 Accuracy: {accuracy}% | ⏱️ Tempo: {bpm} BPM")
            
        # Display progression
        progression = summary.get('chord_progression', [])
        if isinstance(progression, str):
            print(f"🎼 Progression: {progression}")
        elif isinstance(progression, list) and progression:
            print(f"🎼 Progression: {' - '.join(progression)}")
        else:
            print("🎼 Progression: No progression detected")
            
        # Display chord count and timeline
        chord_events = results.get('chord_events', [])
        if chord_events:
            unique_chords = list(set(event.get('chord', '') for event in chord_events if event.get('chord')))
            print(f"📊 {len(chord_events)} chord events | 🎸 Unique chords: {', '.join(unique_chords)}")
            
            # Display chord events timeline
            print("\n⏰ Chord Timeline:")
            for event in chord_events:
                start_time = event.get('start_time', '00:00')
                end_time = event.get('end_time', '00:00')
                chord = event.get('chord', 'Unknown')
                duration = event.get('duration_seconds', 0)
                print(f"   {event.get('event_number', '?'):2d}. [{start_time}-{end_time}] {chord} ({duration:.1f}s)")
                
        # Display guitar tabs for detected chords
        self._display_chord_tabs(results)
        
    def _display_chord_tabs(self, results: Dict[str, Any]):
        """Display guitar tabs for detected chords."""
        try:
            from src.guitar_tab_generator import GuitarTabGenerator
            
            # Get unique chords from the chord events
            chord_events = results.get('chord_events', [])
            if not chord_events:
                return
                
            unique_chords = list(set(event.get('chord', '') for event in chord_events if event.get('chord')))
            
            if not unique_chords:
                return
                
            tab_generator = GuitarTabGenerator()
            
            print("\n\nChord Tabs (unique)")
            print("-" * 40)
            
            # Store tab data for JSON output
            chord_tabs = []
            
            for chord in unique_chords:
                try:
                    tab_result = tab_generator.generate_chord_tab(chord)
                    
                    if tab_result['found']:
                        print(f"\n[DIFFICULTY] {tab_result['difficulty_text']} (Level {tab_result['difficulty']})")
                        print(f"[DATASET] Found in dataset: {tab_result['occurrences']} times")
                        print(f"[COMPACT] {tab_generator.format_compact_tab(tab_result['fingering'])}")
                        print(f"\n[GUITAR] {tab_result['chord']} Chord")
                        print("=" * 40)
                        print(tab_result['primary_tab'])
                        
                        # Add to chord_tabs for JSON output
                        chord_tabs.append({
                            "chord": tab_result['chord'],
                            "difficulty": tab_result['difficulty'],
                            "difficulty_text": tab_result['difficulty_text'],
                            "occurrences": tab_result['occurrences'],
                            "compact_tab": tab_generator.format_compact_tab(tab_result['fingering']),
                            "guitar_tab": tab_result['primary_tab'],
                            "fingering": tab_result['fingering']
                        })
                    else:
                        print(f"\n[ERROR] {tab_result['message']}")
                        if tab_result.get('suggestion'):
                            print(f"[SUGGESTION] Try: {tab_result['suggestion']}")
                        
                        # Add error info to chord_tabs
                        chord_tabs.append({
                            "chord": chord,
                            "error": tab_result['message'],
                            "suggestion": tab_result.get('suggestion')
                        })
                except Exception as e:
                    print(f"\n[ERROR] Failed to generate tab for {chord}: {str(e)}")
                    chord_tabs.append({
                        "chord": chord,
                        "error": f"Failed to generate tab: {str(e)}"
                    })
            
            # Store chord tabs in results for JSON output
            results['chord_tabs'] = chord_tabs
                    
        except ImportError:
            print("\n⚠️ Guitar tab generator not available")
            results['chord_tabs'] = []
        except Exception as e:
            print(f"\n❌ Error displaying chord tabs: {str(e)}")
            results['chord_tabs'] = []
                
    def _retrieve_rag_context(self, chord_results: Dict[str, Any], user_question: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve relevant context from unified RAG system."""
        try:
            if not self.rag_system:
                return {
                    "error": "RAG system not available",
                    "context": "Using direct GPT-4o mode without RAG context"
                }
            
            # Extract key information for RAG query
            summary = chord_results.get("analysis_summary", {})
            detected_key = summary.get("detected_key", "Unknown")
            chord_progression = summary.get("chord_progression", "Unknown")
            chord_events = chord_results.get("chord_events", [])
            
            # Get unique chords
            unique_chords = list(set([
                event.get("chord", "Unknown") 
                for event in chord_events 
                if event.get("chord")
            ]))
            
            # Build enhanced RAG query for comprehensive dataset
            if user_question:
                # User has specific question - create detailed query
                rag_query = f"{user_question} guitar chords {' '.join(unique_chords)} key {detected_key} progression {chord_progression} fingering theory"
            else:
                # General query leveraging comprehensive music dataset
                rag_query = f"guitar chord {' '.join(unique_chords[:3])} key {detected_key} progression fingering theory practice tips"
            
            print(f"🔍 RAG Query: {rag_query}")
            
            # Search unified RAG system with more results for comprehensive dataset
            search_results = self.rag_system.query(rag_query, n_results=5)
            
            if search_results.get("error"):
                return {
                    "error": search_results["error"],
                    "context": "RAG search failed, using analysis data only"
                }
            
            # Format RAG context
            rag_context = {
                "query": rag_query,
                "results_found": search_results.get("total_results", 0),
                "relevant_analyses": [],
                "musical_context": []
            }
            
            # Process search results - use more results from large dataset
            for result in search_results.get("results", [])[:3]:  # Top 3 results
                result_info = {
                    "source": result.get("source_file", "Unknown"),
                    "key": result.get("detected_key", "Unknown"),
                    "progression": result.get("chord_progression", "Unknown"),
                    "similarity": result.get("similarity_score", 0),
                    "context_snippet": result.get("document", "")[:200] + "..."
                }
                rag_context["relevant_analyses"].append(result_info)
                
                # Extract musical insights
                if result.get("detected_key") == detected_key:
                    rag_context["musical_context"].append(f"Similar key analysis found: {result.get('source_file')}")
                
                common_chords = set(unique_chords) & set(result.get("unique_chords", []))
                if common_chords:
                    rag_context["musical_context"].append(f"Common chords with {result.get('source_file')}: {', '.join(common_chords)}")
            
            print(f"✅ RAG Context: {rag_context['results_found']} results, {len(rag_context['musical_context'])} insights")
            return rag_context
            
        except Exception as e:
            print(f"❌ RAG retrieval error: {e}")
            return {
                "error": str(e),
                "context": "RAG system error, using analysis data only"
            }
            
    def _embed_analysis_to_rag(self, chord_results: Dict[str, Any], audio_filename: str) -> Dict[str, Any]:
        """
        Embed the current chord analysis into the unified RAG system for future learning.
        
        Args:
            chord_results: Chord analysis results from HorizonJam
            audio_filename: Name of the source audio file
            
        Returns:
            Embedding result status
        """
        try:
            if not self.rag_system:
                return {"success": False, "error": "RAG system not available"}
            
            print(f"🔗 Embedding analysis into unified RAG system: {audio_filename}")
            
            # Use the unified RAG system's embed method
            result = self.rag_system.embed_chord_analysis(chord_results, audio_filename)
            
            if result.get("success"):
                print(f"✅ Successfully embedded analysis: {result.get('document_id')}")
            else:
                print(f"❌ Failed to embed analysis: {result.get('error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return {"success": False, "error": str(e)}
            
    def _generate_rag_tutoring(self, chord_results: Dict[str, Any], rag_context: Dict[str, Any], user_question: Optional[str] = None) -> str:
        """Generate detailed chord progression tutoring explanation using unified RAG context."""
        try:
            # Extract actual analysis data
            summary = chord_results.get("analysis_summary", {})
            detected_key = summary.get("detected_key", "Unknown")
            chord_progression = summary.get("chord_progression", "Unknown")
            chord_events = chord_results.get("chord_events", [])
            
            # Get unique chords from the progression
            unique_chords = list(set([
                event.get("chord", "Unknown") 
                for event in chord_events 
                if event.get("chord")
            ]))
            
            # Build context from unified RAG system
            rag_content = ""
            if rag_context and not rag_context.get("error"):
                relevant_analyses = rag_context.get("relevant_analyses", [])
                musical_context = rag_context.get("musical_context", [])
                
                if relevant_analyses:
                    rag_content += "\n\nRelevant musical analyses from database:\n"
                    for analysis in relevant_analyses[:2]:
                        source = analysis.get("source", "Unknown")
                        key = analysis.get("key", "Unknown")
                        progression = analysis.get("progression", "Unknown")
                        similarity = analysis.get("similarity", 0)
                        
                        rag_content += f"- {source}: {key} key, {progression} ({similarity:.1%} similar)\n"
                        
                if musical_context:
                    rag_content += "\nMusical insights:\n"
                    for insight in musical_context[:3]:
                        rag_content += f"- {insight}\n"
            
            # Create conversational tutoring prompt
            system_prompt = f"""You are a friendly, experienced guitar instructor having a conversation with a student. 
            
Your student just played this chord progression and wants to understand it better:
            - Key: {detected_key}
            - Progression: {chord_progression} 
            - Chords: {', '.join(unique_chords) if unique_chords else 'None detected'}
            
Respond in a natural, conversational teaching style as if you're sitting next to them with a guitar. Explain the music theory in an approachable way, give practical playing tips, and share insights about the musical style. 
            
Avoid formal headings, bullet points, or academic formatting. Instead, write as if you're having a friendly conversation about music. Keep the theory content but make it sound like natural speech from an encouraging teacher.
            
Focus on helping them understand what makes this progression work musically and how to play it better."""
            
            user_prompt = f"""Please analyze this chord progression in detail:
            
Key: {detected_key}
Progression: {chord_progression}
Chords found: {', '.join(unique_chords) if unique_chords else 'None detected'}
            
{user_question if user_question else 'Provide a comprehensive guitar lesson for this progression.'}
            
{rag_content}"""
            
            # Generate response using GPT-4o
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                
                return response.choices[0].message.content
            else:
                # Fallback response
                return f"""## Analysis of Your Chord Progression
                
**Detected Key:** {detected_key}
**Chord Progression:** {chord_progression}
**Chords Found:** {', '.join(unique_chords) if unique_chords else 'None detected'}
                
This analysis is based on your actual audio file with {len(chord_events)} chord events detected.
                
{rag_content if rag_content else ''}
                
*Note: For detailed analysis, please ensure OpenAI API is configured.*"""
                
        except Exception as e:
            return f"❌ Error generating tutoring explanation: {str(e)}\n\nRaw analysis data available - please check chord_analysis_output.json for details."
            
    def ask_question(self, question: str, wav_path: Optional[str] = None) -> str:
        """Ask a specific question, optionally with audio context."""
        try:
            if wav_path:
                # Analyze audio first, then ask question with context
                print(f"🎵 Analyzing audio for context: {wav_path}")
                analysis_result = self.analyze_audio(wav_path, user_question=question)
                return analysis_result.get("tutoring_response", "Analysis completed but no tutoring response generated.")
            else:
                # Direct question without audio context
                if self.rag_system:
                    try:
                        # Use unified RAG system for enhanced response
                        search_results = self.rag_system.query(question, n_results=3)
                        
                        if search_results.get("error"):
                            # Fallback to direct GPT-4o
                            return self._generate_direct_response(question)
                        
                        # Generate response with RAG context
                        return self._generate_rag_response(question, search_results)
                        
                    except Exception as e:
                        print(f"⚠️ RAG query failed: {e}")
                        return self._generate_direct_response(question)
                else:
                    # Direct GPT-4o response
                    return self._generate_direct_response(question)
                    
        except Exception as e:
            return f"❌ Error processing question: {str(e)}"
                
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get statistics about the unified RAG knowledge base."""
        try:
            if self.rag_system:
                return self.rag_system.get_statistics()
            else:
                return {"error": "RAG system not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def _save_json_output(self, response: Dict[str, Any], output_dir: str):
        """Save analysis results to JSON file in specified output directory."""
        try:
            output_path = Path(output_dir)

            
            # Get chord analysis data
            chord_analysis = response.get("chord_analysis", {})
            
            # Include detailed chord tabs if available
            chord_tabs = response.get("chord_tabs", [])
            if chord_tabs:
                # Replace the simplified guitar_tabs with detailed chord tabs
                chord_analysis["guitar_tabs"] = chord_tabs
            
            # Create structured output for API compatibility
            structured_output = {
                "metadata": {
                    "audio_file": response.get("audio_file"),
                    "timestamp": response.get("timestamp"),
                    "analysis_type": "chord_detection_with_rag_tutoring",
                },
                "chord_analysis": chord_analysis,
                "rag_context": response.get("rag_context", {}),
                "tutoring_response": response.get("tutoring", ""),
                "full_response": response
            }
            
            # Save to chord_analysis_structured.json (expected by API server)
            json_file = output_path / "chord_analysis_structured.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(structured_output, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {json_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save JSON output: {e}")
            
    def interactive_session(self):
        """Start interactive ChordAI + RAG-enhanced tutoring session."""
        print("\n🎸 ChordAI + RAG-Enhanced Music Tutor")
        print("=" * 45)
        print("Commands:")
        print("  - 'analyze <wav_file>' - Analyze audio and get RAG-enhanced tutoring")
        print("  - 'ask <question>' - Ask music theory questions with RAG context")
        print("  - 'stats' - Show RAG knowledge base statistics")
        print("  - 'quit' - Exit")
        print("\n" + "🎵" * 45)
        
        # Show RAG system status
        if self.rag_system:
            try:
                stats = self.get_rag_stats()
                print(f"\n📚 Knowledge Base: {stats.get('total_documents', 'N/A')} documents loaded")
            except:
                pass
        
        while True:
            try:
                user_input = input("\n🎸 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Keep practicing! See you next time!")
                    break
                    
                elif user_input.lower() == 'stats':
                    stats = self.get_rag_stats()
                    print(f"\n📊 RAG Knowledge Base Statistics:")
                    for key, value in stats.items():
                        print(f"  - {key}: {value}")
                        
                elif user_input.lower().startswith('analyze '):
                    wav_path = user_input[8:].strip()
                    if os.path.exists(wav_path):
                        self.analyze_audio(wav_path)
                    else:
                        print(f"❌ Audio file not found: {wav_path}")
                        
                elif user_input.lower().startswith('ask '):
                    question = user_input[4:].strip()
                    if question:
                        print("\n🧠 RAG-Enhanced Music Tutor:")
                        print("-" * 35)
                        response = self.ask_question(question)
                        print(response)
                        
                elif user_input:
                    # Treat as general question
                    print("\n🧠 RAG-Enhanced Music Tutor:")
                    print("-" * 35)
                    response = self.ask_question(user_input)
                    print(response)
                    
            except KeyboardInterrupt:
                print("\n👋 Keep practicing! See you next time!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main function for ChordAI + RAG-Enhanced Music Tutor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChordAI + RAG-Enhanced GPT-4o Music Tutor")
    parser.add_argument("--wav", "-w", help="WAV file to analyze")
    parser.add_argument("--question", "-q", help="Specific question about the music")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive session")
    parser.add_argument("--ask", "-a", help="Ask a general music question")
    parser.add_argument("--stats", "-s", action="store_true", help="Show RAG knowledge base stats")
    parser.add_argument("--confidence", type=float, default=0.3, help="Chord detection confidence threshold (default: 0.3)")
    parser.add_argument("--min-duration", type=float, default=0.05, help="Minimum chord duration in seconds (default: 0.05)")
    parser.add_argument("--out", help="Output directory for JSON results")
    
    args = parser.parse_args()
    
    try:
        tutor = ChordAIRAGTutor()
        
        if args.stats:
            stats = tutor.get_rag_stats()
            print("📊 RAG Knowledge Base Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        elif args.wav:
            print(f"🎵 Analyzing WAV file: {args.wav}")
            tutor.analyze_audio(
                wav_path=args.wav, 
                user_question=args.question,
                confidence=args.confidence,
                min_duration=args.min_duration,
                output_dir=args.out
            )
            
        elif args.ask:
            print("🧠 RAG-Enhanced Music Tutor Response:")
            print("-" * 40)
            response = tutor.ask_question(args.ask)
            print(response)
            
        elif args.interactive:
            tutor.interactive_session()
            
        else:
            print("🎸 ChordAI + RAG-Enhanced Music Tutor")
            print("Use --help for options")
            print("Quick start: python chordai_gpt_tutor.py --interactive")
            
    except Exception as e:
        print(f"❌ Failed to start tutor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
