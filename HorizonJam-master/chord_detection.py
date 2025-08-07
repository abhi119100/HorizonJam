#!/usr/bin/env python3
"""
HorizonJam Chord Detection System
Unified interface for audio→MIDI→chords pipeline with ML training
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pipeline import AccurateAudioToChordsPipeline
from training_data_collector import ChordTrainingDataCollector
from ml_chord_trainer import ChordMLTrainer
from hybrid_chord_detector import HybridChordDetector

def run_chord_detection(audio_file: str, use_hybrid: bool = True, save_training: bool = False):
    """
    Run chord detection on audio/MIDI file
    
    Args:
        audio_file: Path to audio or MIDI file
        use_hybrid: Use hybrid ML+rule detection (default: True)
        save_training: Save results for training data collection
    """
    
    print(f"🎵 Processing: {audio_file}")
    
    if use_hybrid:
        # Use hybrid detection (ML + rules + Viterbi smoothing)
        detector = HybridChordDetector()
        result = detector.detect_chords(audio_file)
        
        if result:
            print(f"🎯 Chord Progression: {' - '.join([c['chord'] for c in result['chords']])}")
            print(f"🎼 Scale: {result.get('scale', 'Unknown')}")
            print(f"📊 Total Chords: {len(result['chords'])}")
            
            if save_training:
                # Save for potential training data collection
                output_file = Path("output") / f"{Path(audio_file).stem}_hybrid_result.json"
                output_file.parent.mkdir(exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"💾 Results saved: {output_file}")
        else:
            print("❌ No chords detected")
    
    else:
        # Use original pipeline (rule-based only)
        pipeline = AccurateAudioToChordsPipeline(
            confidence_threshold=0.7,
            min_note_duration=0.1,
            chord_window_size=1.0,
            basicpitch_onset_threshold=0.3,
            basicpitch_frame_threshold=0.3,
            min_frequency=80,
            max_frequency=2000
        )
        
        result = pipeline.process(audio_file)
        
        if result and 'chord_progression' in result:
            print(f"🎯 Chord Progression: {result['chord_progression']}")
            print(f"🎼 Scale: {result.get('scale', 'Unknown')}")
            print(f"📊 Total Chords: {result.get('total_chords', 0)}")
            
            if save_training:
                output_file = Path("output") / f"{Path(audio_file).stem}_pipeline_result.json"
                output_file.parent.mkdir(exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"💾 Results saved: {output_file}")
        else:
            print("❌ No chords detected")

def train_model():
    """Train ML model on collected training data"""
    
    print("🤖 Training ML Model...")
    
    trainer = ChordMLTrainer()
    
    # Load training data
    db_file = Path("training_data/chord_training_database.json")
    if not db_file.exists():
        print("❌ No training data found. Please collect some training samples first.")
        return
    
    with open(db_file, 'r') as f:
        training_data = json.load(f)
    
    if len(training_data) < 2:
        print(f"⚠️ Only {len(training_data)} training samples found. Need at least 2 for training.")
        return
    
    print(f"📊 Training on {len(training_data)} samples...")
    
    # Train model
    report = trainer.train_model(training_data)
    
    if report:
        print("✅ Model training complete!")
        print(f"🎯 Accuracy: {report.get('accuracy', 'N/A')}")
        print(f"📈 Best Model: {report.get('best_model', 'N/A')}")
        print(f"💾 Model saved to: models/")
    else:
        print("❌ Model training failed")

def collect_training_data(audio_file: str):
    """Collect training data by comparing detections"""
    
    print(f"📝 Collecting training data for: {audio_file}")
    
    # Run both detections
    pipeline = AccurateAudioToChordsPipeline()
    rule_result = pipeline.process(audio_file)
    
    detector = HybridChordDetector()
    hybrid_result = detector.detect_chords(audio_file)
    
    if rule_result and hybrid_result:
        collector = ChordTrainingDataCollector()
        
        # Convert results to training format
        detected_chords = []
        if 'chord_events' in rule_result:
            detected_chords = rule_result['chord_events']
        
        corrected_chords = hybrid_result.get('chords', [])
        
        # Collect training sample
        sample_id = collector.collect_user_correction(
            audio_file=audio_file,
            detected_chords=detected_chords,
            corrected_chords=corrected_chords,
            metadata={'source': 'auto_collection', 'method': 'rule_vs_hybrid'}
        )
        
        print(f"✅ Training sample collected: {sample_id}")
    else:
        print("❌ Could not collect training data - detection failed")

def show_status():
    """Show current system status"""
    
    print("🎸" + "="*50)
    print("🎯 HORIZONJAM CHORD DETECTION STATUS")
    print("="*50)
    
    # Check training data
    db_file = Path("training_data/chord_training_database.json")
    if db_file.exists():
        with open(db_file, 'r') as f:
            training_data = json.load(f)
        print(f"📊 Training samples: {len(training_data)}")
        
        sources = {}
        for sample in training_data:
            source = sample.get('metadata', {}).get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            print(f"   • {source}: {count}")
    else:
        print("📊 Training samples: 0")
    
    # Check models
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.joblib"))
        print(f"🤖 Trained models: {len(model_files)}")
        for model in model_files:
            print(f"   • {model.name}")
    else:
        print("🤖 Trained models: 0")
    
    print()
    print("🎯 Next Steps for 88-92% Accuracy:")
    print("1. Collect more training data: python chord_detection.py --collect <audio_file>")
    print("2. Train ML model: python chord_detection.py --train")
    print("3. Use hybrid detection: python chord_detection.py <audio_file>")

def main():
    """Main interface"""
    
    parser = argparse.ArgumentParser(description="HorizonJam Chord Detection System")
    parser.add_argument('audio_file', nargs='?', help='Audio or MIDI file to process')
    parser.add_argument('--hybrid', action='store_true', default=True, help='Use hybrid detection (default)')
    parser.add_argument('--rule-only', action='store_true', help='Use rule-based detection only')
    parser.add_argument('--train', action='store_true', help='Train ML model')
    parser.add_argument('--collect', metavar='FILE', help='Collect training data from file')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--save', action='store_true', help='Save results for training')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.train:
        train_model()
    elif args.collect:
        collect_training_data(args.collect)
    elif args.audio_file:
        use_hybrid = not args.rule_only
        run_chord_detection(args.audio_file, use_hybrid=use_hybrid, save_training=args.save)
    else:
        print("🎸 HorizonJam Chord Detection System")
        print()
        print("Usage:")
        print("  python chord_detection.py <audio_file>     # Detect chords (hybrid)")
        print("  python chord_detection.py --rule-only <file>  # Rule-based only")
        print("  python chord_detection.py --train          # Train ML model")
        print("  python chord_detection.py --collect <file> # Collect training data")
        print("  python chord_detection.py --status         # Show system status")
        print()
        print("Examples:")
        print("  python chord_detection.py tests/test11.mid")
        print("  python chord_detection.py --status")
        print("  python chord_detection.py --train")

if __name__ == "__main__":
    main()
