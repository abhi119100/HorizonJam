"""
Hybrid Chord Detection System
Combines rule-based advanced detection with ML predictions for maximum accuracy
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.calibration import CalibratedClassifierCV
from src.chord_detector import analyze_midi_chords
from src.ml_chord_trainer import ChordMLTrainer
from src.training_data_collector import ChordTrainingDataCollector
from src.viterbi_smoothing import ChordViterbiSmoother
from src.gp_dataset_integration import GPDatasetIntegration
from src.guitar_tab_generator import GuitarTabGenerator

class HybridChordDetector:
    """Combines rule-based and ML approaches for superior chord detection"""
    
    def detect_chords(self, audio_file: str) -> Dict:
        """Main interface method for chord detection"""
        try:
            chords, metadata = self.detect_chords_hybrid(audio_file)
            
            # Convert to expected format
            result = {
                'chords': chords,
                'scale': metadata.get('estimated_key', 'Unknown'),
                'metadata': metadata,
                'total_chords': len(chords),
                'chord_progression': ' - '.join([c['chord'] for c in chords])
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Hybrid detection failed: {e}")
            return None
    
    def __init__(self, use_viterbi: bool = True):
        """Initialize hybrid detector with ML trainer, collector, Viterbi smoother, and GP dataset"""
        self.ml_trainer = ChordMLTrainer()
        self.collector = ChordTrainingDataCollector()
        self.viterbi_smoother = ChordViterbiSmoother() if use_viterbi else None
        self.gp_dataset = GPDatasetIntegration()
        # Initialize guitar tab generator for visual tab output
        self.tab_generator = GuitarTabGenerator()
        self.ml_available = False
        self.use_viterbi = use_viterbi
        
        # Check if ML model is available
        models_dir = Path("models")
        if models_dir.exists():
            model_files = list(models_dir.glob("*.joblib"))
            if model_files:
                try:
                    self.ml_trainer.load_model(str(model_files[0]))
                    self.ml_available = True
                    # ML model loaded silently
                except Exception as e:
                    # Could not load ML model
                    self.ml_available = False
            else:
                # No trained ML models found - using rule-based detection only
                pass
        
        # Try to load existing transition matrix
        if self.use_viterbi:
            transition_path = Path("models/chord_transitions.json")
            if transition_path.exists():
                self.viterbi_smoother.load_transition_matrix(str(transition_path))
        
        # Ensemble weights
        self.weights = {
            'rule_based': 0.7,  # Your advanced algorithm gets higher weight
            'ml_model': 0.3     # ML model provides refinement
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'high_confidence': 0.85,
            'medium_confidence': 0.65,
            'low_confidence': 0.45
        }
    
    def detect_chords_hybrid(self, midi_path: str, **kwargs) -> Tuple[List[Dict], Dict]:
        """
        Hybrid chord detection combining rule-based + ML approaches
        
        Returns:
            chords: List of detected chords with enhanced confidence
            metadata: Detection metadata and ensemble info
        """
        
        # Run hybrid chord detection silently
        analysis_result = analyze_midi_chords(midi_path, **kwargs)
        
        # Extract components from the new return format
        rule_based_result = analysis_result['chord_progression']
        rule_based_events = analysis_result['chord_events']
        detected_key = analysis_result['detected_key']
        
        # Step 2: Run ML prediction (if available)
        ml_predictions = None
        if self.ml_available:
            print("🤖 Running ML predictions...")
            try:
                ml_predictions = self.get_ml_predictions(midi_path)
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
                ml_predictions = None
        
        # Step 3: Ensemble decision making with GP dataset enhancement
        print("🎯 Combining predictions with GP dataset knowledge...")
        enhanced_chords = self.ensemble_predictions(
            rule_based_result, ml_predictions, rule_based_events
        )
        
        # Step 3.5: Enhance with GP dataset knowledge
        enhanced_chords = self.enhance_with_gp_dataset(enhanced_chords)
        
        # Step 4: Generate metadata
        metadata = self.generate_detection_metadata(
            rule_based_result, ml_predictions, enhanced_chords
        )
        
        # Step 5: Enhance scale detection with GP dataset
        chord_names = [c.get('chord', '') for c in enhanced_chords]
        scale_enhancement = self.gp_dataset.enhance_scale_detection(chord_names)
        
        # Use GP-enhanced scale if more confident
        if scale_enhancement.get('confidence', 0) > 0.7:
            detected_key = scale_enhancement['detected_scale']
        
        # Add the detected key to metadata
        metadata['detected_key'] = detected_key
        metadata['estimated_key'] = detected_key  # For compatibility
        metadata['scale_enhancement'] = scale_enhancement
        
        return enhanced_chords, metadata
    
    def get_ml_predictions(self, midi_path: str) -> List[Dict]:
        """Get ML model predictions"""
        
        if not self.ml_available:
            return None
        
        # Extract features for ML model
        features = self.collector.extract_comprehensive_features(midi_path)
        
        # For each time segment, get ML prediction
        ml_predictions = []
        
        # This is a simplified approach - in practice you'd segment the audio
        # and run predictions on each segment
        try:
            chord_name, confidence = self.ml_trainer.predict_chord(features)
            
            ml_predictions.append({
                'chord': chord_name,
                'confidence': confidence,
                'source': 'ml_model',
                'timestamp': 0.0,
                'end_time': features.get('midi_stats', {}).get('total_duration', 10.0)
            })
            
        except Exception as e:
            print(f"⚠️ ML prediction error: {e}")
            return None
        
        return ml_predictions
    
    def ensemble_predictions(self, 
                           rule_based: List[Dict], 
                           ml_predictions: Optional[List[Dict]],
                           rule_based_events: List[Dict]) -> List[Dict]:
        """Combine rule-based and ML predictions using ensemble logic"""
        
        enhanced_chords = []
        
        for i, chord_data in enumerate(rule_based):
            rule_chord = chord_data['chord']
            rule_confidence = 0.8  # Default confidence for rule-based
            
            # Start with rule-based prediction
            final_chord = rule_chord
            final_confidence = rule_confidence
            ensemble_info = {'source': 'rule_based_only'}
            
            # If ML predictions available, combine them
            if ml_predictions and len(ml_predictions) > 0:
                # Find matching ML prediction (simplified - match by time or index)
                ml_chord = ml_predictions[0]['chord']  # Simplified
                ml_confidence = ml_predictions[0]['confidence']
                
                # Ensemble decision logic
                if ml_confidence > self.confidence_thresholds['high_confidence']:
                    if ml_chord == rule_chord:
                        # Both agree with high ML confidence - boost confidence
                        final_chord = rule_chord
                        final_confidence = min(0.95, rule_confidence + 0.15)
                        ensemble_info = {'source': 'both_agree_high_conf', 'ml_chord': ml_chord}
                    else:
                        # High ML confidence but disagree - weighted average
                        if ml_confidence > 0.9:
                            final_chord = ml_chord
                            final_confidence = ml_confidence * 0.9
                            ensemble_info = {'source': 'ml_override', 'rule_chord': rule_chord}
                        else:
                            final_chord = rule_chord
                            final_confidence = rule_confidence * 0.9
                            ensemble_info = {'source': 'rule_preferred', 'ml_chord': ml_chord}
                
                elif ml_confidence > self.confidence_thresholds['medium_confidence']:
                    if ml_chord == rule_chord:
                        # Both agree with medium ML confidence
                        final_chord = rule_chord
                        final_confidence = min(0.9, rule_confidence + 0.1)
                        ensemble_info = {'source': 'both_agree_med_conf', 'ml_chord': ml_chord}
                    else:
                        # Medium ML confidence, prefer rule-based
                        final_chord = rule_chord
                        final_confidence = rule_confidence * 0.95
                        ensemble_info = {'source': 'rule_preferred_med', 'ml_chord': ml_chord}
                
                else:
                    # Low ML confidence - stick with rule-based
                    final_chord = rule_chord
                    final_confidence = rule_confidence
                    ensemble_info = {'source': 'rule_only_low_ml', 'ml_chord': ml_chord}
            
            # Create enhanced chord data
            enhanced_chord = chord_data.copy()
            enhanced_chord.update({
                'chord': final_chord,
                'confidence': final_confidence,
                'ensemble_info': ensemble_info,
                'original_rule_chord': rule_chord
            })
            
            enhanced_chords.append(enhanced_chord)
        
        return enhanced_chords
    
    def enhance_with_gp_dataset(self, chords: List[Dict]) -> List[Dict]:
        """Enhance chord detection using Guitar Pro dataset knowledge"""
        
        enhanced_chords = []
        
        for chord_data in chords:
            chord_name = chord_data.get('chord', '')
            
            # Get GP dataset enhancement
            gp_enhancement = self.gp_dataset.enhance_chord_detection(chord_name)
            
            # Apply confidence boost from GP dataset
            original_confidence = chord_data.get('confidence', 0.5)
            confidence_boost = gp_enhancement.get('confidence_boost', 0.0)
            enhanced_confidence = min(original_confidence + confidence_boost, 1.0)
            
            # Create enhanced chord data
            enhanced_chord = chord_data.copy()
            enhanced_chord.update({
                'confidence': enhanced_confidence,
                'gp_enhanced': gp_enhancement.get('gp_support', False),
                'gp_occurrences': gp_enhancement.get('occurrences_in_dataset', 0),
                'original_confidence': original_confidence,
                'confidence_boost': confidence_boost
            })
            
            # Add ensemble info if not present
            if 'ensemble_info' not in enhanced_chord:
                enhanced_chord['ensemble_info'] = {
                    'source': 'gp_enhanced',
                    'original_source': 'rule_based',
                    'gp_support': gp_enhancement.get('gp_support', False)
                }
            else:
                enhanced_chord['ensemble_info']['gp_enhanced'] = True
                enhanced_chord['ensemble_info']['gp_support'] = gp_enhancement.get('gp_support', False)
            
            enhanced_chords.append(enhanced_chord)
        
        return enhanced_chords
    
    def generate_detection_metadata(self, 
                                  rule_based: List[Dict],
                                  ml_predictions: Optional[List[Dict]],
                                  enhanced: List[Dict]) -> Dict:
        """Generate comprehensive metadata about the detection process"""
        
        metadata = {
            'detection_method': 'hybrid',
            'ml_available': self.ml_available,
            'ensemble_weights': self.weights,
            'statistics': {
                'total_chords': len(enhanced),
                'rule_based_count': len(rule_based),
                'ml_predictions_count': len(ml_predictions) if ml_predictions else 0
            }
        }
        
        # Analyze ensemble decisions
        ensemble_sources = [c['ensemble_info']['source'] for c in enhanced]
        source_counts = {}
        for source in ensemble_sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        metadata['ensemble_analysis'] = {
            'decision_sources': source_counts,
            'agreement_rate': self.calculate_agreement_rate(rule_based, ml_predictions),
            'confidence_distribution': self.analyze_confidence_distribution(enhanced)
        }
        
        # Performance estimates
        estimated_accuracy = self.estimate_accuracy(enhanced)
        metadata['performance_estimate'] = {
            'estimated_accuracy': estimated_accuracy,
            'confidence_level': self.get_confidence_level(estimated_accuracy)
        }
        
        return metadata
    
    def calculate_agreement_rate(self, rule_based: List[Dict], ml_predictions: Optional[List[Dict]]) -> float:
        """Calculate agreement rate between rule-based and ML predictions"""
        
        if not ml_predictions or len(ml_predictions) == 0:
            return 0.0
        
        # Simplified agreement calculation
        agreements = 0
        total_comparisons = min(len(rule_based), len(ml_predictions))
        
        for i in range(total_comparisons):
            if i < len(rule_based) and rule_based[i]['chord'] == ml_predictions[0]['chord']:
                agreements += 1
        
        return agreements / total_comparisons if total_comparisons > 0 else 0.0
    
    def analyze_confidence_distribution(self, enhanced_chords: List[Dict]) -> Dict:
        """Analyze the distribution of confidence scores"""
        
        confidences = [c['confidence'] for c in enhanced_chords]
        
        if not confidences:
            return {}
        
        import numpy as np
        
        return {
            'mean_confidence': float(np.mean(confidences)),
            'std_confidence': float(np.std(confidences)),
            'min_confidence': float(min(confidences)),
            'max_confidence': float(max(confidences)),
            'high_confidence_count': sum(1 for c in confidences if c > self.confidence_thresholds['high_confidence']),
            'medium_confidence_count': sum(1 for c in confidences if self.confidence_thresholds['medium_confidence'] < c <= self.confidence_thresholds['high_confidence']),
            'low_confidence_count': sum(1 for c in confidences if c <= self.confidence_thresholds['medium_confidence'])
        }
    
    def estimate_accuracy(self, enhanced_chords: List[Dict]) -> float:
        """Estimate overall accuracy based on confidence scores and ensemble decisions"""
        
        if not enhanced_chords:
            return 0.0
        
        # Weight accuracy estimate based on confidence and ensemble source
        total_weight = 0
        weighted_accuracy = 0
        
        for chord in enhanced_chords:
            confidence = chord['confidence']
            source = chord['ensemble_info']['source']
            
            # Base accuracy estimates for different sources
            base_accuracy = {
                'rule_based_only': 0.80,
                'both_agree_high_conf': 0.95,
                'both_agree_med_conf': 0.88,
                'ml_override': 0.85,
                'rule_preferred': 0.82,
                'rule_preferred_med': 0.81,
                'rule_only_low_ml': 0.79
            }
            
            source_accuracy = base_accuracy.get(source, 0.75)
            
            # Adjust based on confidence
            adjusted_accuracy = source_accuracy * (0.5 + 0.5 * confidence)
            
            weighted_accuracy += adjusted_accuracy * confidence
            total_weight += confidence
        
        return weighted_accuracy / total_weight if total_weight > 0 else 0.75
    
    def get_confidence_level(self, accuracy: float) -> str:
        """Get human-readable confidence level"""
        
        if accuracy >= 0.9:
            return "Very High"
        elif accuracy >= 0.8:
            return "High"
        elif accuracy >= 0.7:
            return "Medium"
        elif accuracy >= 0.6:
            return "Low"
        else:
            return "Very Low"
    
    def save_detection_results(self, chords: List[Dict], metadata: Dict, output_path: str):
        """Save hybrid detection results"""
        
        results = {
            'detection_metadata': metadata,
            'chords': chords,
            'summary': {
                'total_chords': len(chords),
                'estimated_accuracy': metadata['performance_estimate']['estimated_accuracy'],
                'confidence_level': metadata['performance_estimate']['confidence_level'],
                'detection_method': 'hybrid_advanced_ml'
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Hybrid detection results saved to: {output_path}")
    
    def print_detection_summary(self, chords: List[Dict], metadata: Dict):
        """Print concise chord progression summary with guitar tabs"""

        progression = [c['chord'] for c in chords]

        print("\n" + "="*60)
        print("🎸 CHORD PROGRESSION & TABS")
        print("="*60)
        print("Progression: " + " - ".join(progression))
        print(f"Total chords: {len(progression)} | Estimated accuracy: {metadata['performance_estimate']['estimated_accuracy']:.1%}\n")

        # Display guitar tabs once per unique chord
        unique_chords = list(dict.fromkeys(progression))  # Preserve order, remove duplicates
        print("\n🎸 Chord Tabs (unique)")
        print("-" * 40)
        for chord in unique_chords:
            try:
                self.tab_generator.print_chord_tab(chord)
            except Exception as e:
                print(f"⚠️ Could not generate tab for {chord}: {e}")



def main():
    """Command line interface for hybrid chord detection"""
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hybrid_chord_detector.py <midi_file> [output_file]")
        return
    
    midi_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(midi_file):
        print(f"❌ File not found: {midi_file}")
        return
    
    # Create hybrid detector
    detector = HybridChordDetector()
    
    # Run detection
    chords, metadata = detector.detect_chords_hybrid(midi_file)
    
    # Print summary
    detector.print_detection_summary(chords, metadata)
    
    # Save results if output file specified
    if output_file:
        detector.save_detection_results(chords, metadata, output_file)


if __name__ == "__main__":
    main()
