#!/usr/bin/env python3
"""
Accurate Audio-to-Chords Pipeline Runner
Usage: python run_pipeline.py input.wav [options]
"""

# --- Silence noise early (before any third-party imports) ---
import os
import sys
from pathlib import Path

# Add utils to path for log silencer (sibling directory after flattening)
utils_path = Path(__file__).parent / "utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    try:
        import log_silencer  # This automatically sets up noise filtering
    except ImportError:
        pass  # Continue without noise filtering if utils not available
    finally:
        if str(utils_path) in sys.path:
            sys.path.remove(str(utils_path))
# ----------------------------------------------------------------

import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline import AccurateAudioToChordsPipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <input_audio> [options]")
        print("Options:")
        print("  -o, --output DIR     Output directory (default: ./output)")
        print("  --confidence FLOAT   Librosa confidence threshold (default: 0.3)")
        print("  --min-duration FLOAT Minimum note duration in seconds (default: 0.05)")
        print("  --max-duration FLOAT Maximum note duration in seconds (default: 4.0)")
        print("  --onset-threshold FLOAT BasicPitch onset threshold (default: 0.5)")
        print("  --frame-threshold FLOAT BasicPitch frame threshold (default: 0.3)")
        print("  --min-freq FLOAT     Minimum frequency in Hz (default: 80.0)")
        print("  --max-freq FLOAT     Maximum frequency in Hz (default: 1200.0)")
        print("  --window-size FLOAT  Chord detection window size in seconds")
        sys.exit(1)
    
    # Parse arguments
    input_file = sys.argv[1]
    output_dir = "./output"
    
    # Parse options
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "-o" or sys.argv[i] == "--output":
            if i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            else:
                print("Error: --output requires a directory")
                sys.exit(1)
        elif sys.argv[i].startswith("--"):
            key = sys.argv[i][2:].replace('-', '_')
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                try:
                    args[key] = float(sys.argv[i + 1])
                except ValueError:
                    args[key] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        
        # Map command line arguments to pipeline parameters
        pipeline_args = {}
        arg_mapping = {
            'confidence_threshold': 'confidence_threshold',
            'min_duration': 'min_note_duration',
            'max_duration': 'max_note_duration', 
            'chord_window_size': 'chord_window_size',
            'window_size': 'chord_window_size',
            'onset_threshold': 'basicpitch_onset_threshold',
            'frame_threshold': 'basicpitch_frame_threshold',
            'min_freq': 'min_frequency',
            'max_freq': 'max_frequency',
            # Handle legacy parameter names
            'min_note_len': 'min_note_duration',
            'confidence': 'confidence_threshold'
        }
        
        # Parameters that should NOT be passed to the pipeline constructor
        excluded_params = {'output_dir', 'verbose', 'output'}
        
        for key, value in args.items():
            if key in excluded_params:
                continue  # Skip parameters that aren't for the pipeline
            elif key in arg_mapping:
                pipeline_args[arg_mapping[key]] = value
            else:
                # Only pass through arguments that are valid pipeline parameters
                valid_pipeline_params = {
                    'confidence_threshold', 'min_note_duration', 'max_note_duration',
                    'chord_window_size', 'basicpitch_onset_threshold', 'basicpitch_frame_threshold',
                    'min_frequency', 'max_frequency'
                }
                if key in valid_pipeline_params:
                    pipeline_args[key] = value
        
        pipeline = AccurateAudioToChordsPipeline(**pipeline_args)
        
        # Run the pipeline
        results = pipeline.run_pipeline(input_file, output_dir)
        
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()