"""
Machine Learning Training System for Chord Detection
Trains models on collected user correction data
"""

import json
import numpy as np
import joblib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from src.training_data_collector import ChordTrainingDataCollector
import sys
import codecs

# Set UTF-8 encoding for Windows console compatibility
if sys.platform.startswith('win'):
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    except (AttributeError, OSError):
        pass  # Fallback for environments where this doesn't work

def safe_print(text):
    """Safely print text with Unicode character handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            # Try encoding to UTF-8 with error replacement
            safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except Exception:
            # Final fallback: convert to ASCII
            ascii_text = text.encode('ascii', errors='replace').decode('ascii')
            print(f"[Unicode Error] {ascii_text}")
            print("[Warning] Some special characters could not be displayed")

class ChordMLTrainer:
    """Machine Learning trainer for chord detection"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.collector = ChordTrainingDataCollector()
        
        # Models
        self.chord_classifier = None
        self.confidence_regressor = None
        self.label_encoder = LabelEncoder()
        self.feature_scaler = StandardScaler()
        
        # Model paths
        self.model_paths = {
            'classifier': self.model_dir / 'chord_classifier.pkl',
            'confidence': self.model_dir / 'confidence_regressor.pkl',
            'encoder': self.model_dir / 'label_encoder.pkl',
            'scaler': self.model_dir / 'feature_scaler.pkl'
        }
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare training data from collected samples"""
        
        training_db = self.collector.training_db
        
        if len(training_db) < 5:
            raise ValueError(f"Need at least 5 training samples, got {len(training_db)}")
        
        safe_print(f"📊 Preparing training data from {len(training_db)} samples...")
        
        X_samples = []
        y_samples = []
        sample_info = []
        
        for sample in training_db:
            try:
                # Extract features
                features = self.extract_ml_features(sample)
                
                # Extract ground truth chords
                ground_truth = sample.get('ground_truth_chords', [])
                
                for chord_data in ground_truth:
                    chord_name = chord_data.get('chord', 'Unknown')
                    if chord_name and chord_name != 'Unknown':
                        X_samples.append(features)
                        y_samples.append(chord_name)
                        sample_info.append({
                            'sample_id': sample['sample_id'],
                            'chord': chord_name,
                            'timestamp': chord_data.get('timestamp', 0)
                        })
                        
            except Exception as e:
                safe_print(f"⚠️ Error processing sample {sample.get('sample_id', 'unknown')}: {e}")
                continue
        
        if len(X_samples) == 0:
            raise ValueError("No valid training samples found")
        
        safe_print(f"✅ Prepared {len(X_samples)} chord samples for training")
        
        return np.array(X_samples), np.array(y_samples), sample_info
    
    def extract_ml_features(self, sample: Dict) -> List[float]:
        """Extract numerical features for ML training"""
        
        features = []
        sample_features = sample.get('features', {})
        
        # MIDI statistics features
        midi_stats = sample_features.get('midi_stats', {})
        features.extend([
            midi_stats.get('total_duration', 0),
            midi_stats.get('num_instruments', 1),
            midi_stats.get('total_notes', 0)
        ])
        
        # Timing features
        timing_features = sample_features.get('timing_features', {})
        features.extend([
            timing_features.get('avg_note_duration', 0.5),
            timing_features.get('std_note_duration', 0.1),
            timing_features.get('note_density', 1.0),
            timing_features.get('avg_velocity', 64),
            timing_features.get('std_velocity', 10)
        ])
        
        # Pitch features
        pitch_features = sample_features.get('pitch_features', {})
        features.extend([
            pitch_features.get('pitch_range', 12),
            pitch_features.get('avg_pitch', 60),
            pitch_features.get('std_pitch', 5),
            pitch_features.get('unique_pitches', 3)
        ])
        
        # Harmonic features
        harmonic_features = sample_features.get('harmonic_features', {})
        features.extend([
            harmonic_features.get('num_time_windows', 1),
            harmonic_features.get('avg_notes_per_window', 3),
            harmonic_features.get('avg_chord_complexity', 3),
            harmonic_features.get('std_chord_complexity', 1)
        ])
        
        # Audio features (if available)
        audio_stats = sample_features.get('audio_stats', {})
        features.extend([
            audio_stats.get('duration', 0),
            audio_stats.get('rms_energy', 0.1)
        ])
        
        spectral_features = sample_features.get('spectral_features', {})
        features.extend([
            spectral_features.get('spectral_centroid', 1000),
            spectral_features.get('spectral_bandwidth', 1000),
            spectral_features.get('spectral_rolloff', 2000),
            spectral_features.get('zero_crossing_rate', 0.1)
        ])
        
        # Chroma features (if available)
        chroma_features = sample_features.get('chroma_features', {})
        chroma_mean = chroma_features.get('chroma_mean', [0] * 12)
        features.extend(chroma_mean[:12])  # Ensure exactly 12 features
        
        # Pad or truncate to fixed size
        target_size = 50
        if len(features) < target_size:
            features.extend([0] * (target_size - len(features)))
        else:
            features = features[:target_size]
        
        return features
    
    def train_models(self, test_size: float = 0.2) -> Dict:
        """Train chord classification models"""
        
        safe_print("🎯 Starting ML model training...")
        
        # Prepare data
        X, y, sample_info = self.prepare_training_data()
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
        )
        
        safe_print(f"📊 Training set: {len(X_train)} samples")
        safe_print(f"📊 Test set: {len(X_test)} samples")
        safe_print(f"📊 Unique chords: {len(np.unique(y_encoded))}")
        
        # Train chord classifier
        safe_print("\n🤖 Training chord classifier...")
        self.chord_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.chord_classifier.fit(X_train, y_train)
        
        # Evaluate classifier
        train_score = self.chord_classifier.score(X_train, y_train)
        test_score = self.chord_classifier.score(X_test, y_test)
        
        safe_print(f"✅ Classifier training accuracy: {train_score:.3f}")
        safe_print(f"✅ Classifier test accuracy: {test_score:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.chord_classifier, X_scaled, y_encoded, cv=5)
        safe_print(f"✅ Cross-validation accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Train confidence regressor (optional)
        print("\n🎯 Training confidence regressor...")
        confidence_targets = self.extract_confidence_targets(sample_info)
        
        if len(confidence_targets) > 0:
            self.confidence_regressor = GradientBoostingClassifier(
                n_estimators=50,
                max_depth=5,
                random_state=42
            )
            
            # Convert confidence to categories (low, medium, high)
            confidence_categories = self.categorize_confidence(confidence_targets)
            self.confidence_regressor.fit(X_scaled, confidence_categories)
            
            conf_score = self.confidence_regressor.score(X_scaled, confidence_categories)
            print(f"✅ Confidence regressor accuracy: {conf_score:.3f}")
        
        # Save models
        self.save_models()
        
        # Generate detailed report
        report = self.generate_training_report(X_test, y_test, y)
        
        return report
    
    def extract_confidence_targets(self, sample_info: List[Dict]) -> List[float]:
        """Extract confidence targets from sample info"""
        
        confidences = []
        for info in sample_info:
            # Use accuracy as proxy for confidence
            # In real implementation, you'd use actual confidence scores
            confidences.append(0.8)  # Placeholder
        
        return confidences
    
    def categorize_confidence(self, confidences: List[float]) -> List[int]:
        """Convert confidence scores to categories"""
        
        categories = []
        for conf in confidences:
            if conf < 0.6:
                categories.append(0)  # Low confidence
            elif conf < 0.8:
                categories.append(1)  # Medium confidence
            else:
                categories.append(2)  # High confidence
        
        return categories
    
    def generate_training_report(self, X_test: np.ndarray, y_test: np.ndarray, y_original: np.ndarray) -> Dict:
        """Generate comprehensive training report"""
        
        # Predictions
        y_pred = self.chord_classifier.predict(X_test)
        
        # Convert back to chord names
        y_test_names = self.label_encoder.inverse_transform(y_test)
        y_pred_names = self.label_encoder.inverse_transform(y_pred)
        
        # Classification report
        class_report = classification_report(y_test_names, y_pred_names, output_dict=True)
        
        # Feature importance
        feature_importance = self.chord_classifier.feature_importances_
        
        report = {
            'model_performance': {
                'test_accuracy': float(self.chord_classifier.score(X_test, y_test)),
                'precision': class_report['macro avg']['precision'],
                'recall': class_report['macro avg']['recall'],
                'f1_score': class_report['macro avg']['f1-score']
            },
            'training_data': {
                'total_samples': len(y_original),
                'unique_chords': len(np.unique(y_original)),
                'chord_distribution': dict(zip(*np.unique(y_original, return_counts=True)))
            },
            'feature_importance': {
                'top_features': self.get_top_features(feature_importance),
                'all_importance': feature_importance.tolist()
            },
            'recommendations': self.generate_recommendations(class_report, len(y_original))
        }
        
        return report
    
    def get_top_features(self, importance: np.ndarray, top_n: int = 10) -> List[Dict]:
        """Get top N most important features"""
        
        feature_names = [
            'duration', 'num_instruments', 'total_notes',
            'avg_note_duration', 'std_note_duration', 'note_density', 'avg_velocity', 'std_velocity',
            'pitch_range', 'avg_pitch', 'std_pitch', 'unique_pitches',
            'num_windows', 'avg_notes_per_window', 'avg_chord_complexity', 'std_chord_complexity',
            'audio_duration', 'rms_energy',
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff', 'zero_crossing_rate'
        ] + [f'chroma_{i}' for i in range(12)] + [f'feature_{i}' for i in range(50)]
        
        # Ensure we have enough feature names
        while len(feature_names) < len(importance):
            feature_names.append(f'feature_{len(feature_names)}')
        
        # Get top features
        top_indices = np.argsort(importance)[-top_n:][::-1]
        
        top_features = []
        for idx in top_indices:
            if idx < len(feature_names):
                top_features.append({
                    'feature': feature_names[idx],
                    'importance': float(importance[idx])
                })
        
        return top_features
    
    def generate_recommendations(self, class_report: Dict, total_samples: int) -> List[str]:
        """Generate recommendations for improving the model"""
        
        recommendations = []
        
        # Sample size recommendations
        if total_samples < 50:
            recommendations.append(f"Collect more training data. Current: {total_samples}, Recommended: 100+")
        
        # Accuracy recommendations
        macro_f1 = class_report['macro avg']['f1-score']
        if macro_f1 < 0.7:
            recommendations.append("Model accuracy is low. Focus on collecting high-quality corrections.")
        elif macro_f1 > 0.9:
            recommendations.append("Excellent model performance! Consider advanced techniques.")
        
        # Class imbalance recommendations
        chord_counts = [class_report[chord]['support'] for chord in class_report if chord not in ['accuracy', 'macro avg', 'weighted avg']]
        if len(chord_counts) > 0:
            max_count = max(chord_counts)
            min_count = min(chord_counts)
            if max_count > 3 * min_count:
                recommendations.append("Class imbalance detected. Collect more samples for underrepresented chords.")
        
        return recommendations
    
    def save_models(self):
        """Save trained models to disk"""
        
        print("\n💾 Saving models...")
        
        if self.chord_classifier:
            joblib.dump(self.chord_classifier, self.model_paths['classifier'])
            print(f"✅ Chord classifier saved to: {self.model_paths['classifier']}")
        
        if self.confidence_regressor:
            joblib.dump(self.confidence_regressor, self.model_paths['confidence'])
            print(f"✅ Confidence regressor saved to: {self.model_paths['confidence']}")
        
        joblib.dump(self.label_encoder, self.model_paths['encoder'])
        joblib.dump(self.feature_scaler, self.model_paths['scaler'])
        
        print(f"✅ Encoders saved")
    
    def load_models(self) -> bool:
        """Load trained models from disk"""
        
        try:
            if self.model_paths['classifier'].exists():
                self.chord_classifier = joblib.load(self.model_paths['classifier'])
                print(f"✅ Loaded chord classifier")
            
            if self.model_paths['confidence'].exists():
                self.confidence_regressor = joblib.load(self.model_paths['confidence'])
                print(f"✅ Loaded confidence regressor")
            
            if self.model_paths['encoder'].exists():
                self.label_encoder = joblib.load(self.model_paths['encoder'])
                print(f"✅ Loaded label encoder")
            
            if self.model_paths['scaler'].exists():
                self.feature_scaler = joblib.load(self.model_paths['scaler'])
                print(f"✅ Loaded feature scaler")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def predict_chord(self, features: Dict) -> Tuple[str, float]:
        """Predict chord using trained model"""
        
        if not self.chord_classifier:
            raise ValueError("No trained model available. Train first or load existing model.")
        
        # Extract ML features
        ml_features = self.extract_ml_features({'features': features})
        
        # Scale features
        X = self.feature_scaler.transform([ml_features])
        
        # Predict
        prediction = self.chord_classifier.predict(X)[0]
        probabilities = self.chord_classifier.predict_proba(X)[0]
        
        # Convert back to chord name
        chord_name = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(max(probabilities))
        
        return chord_name, confidence


def main():
    """Command line interface for model training"""
    
    import sys
    
    trainer = ChordMLTrainer()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--load':
        # Load existing models
        success = trainer.load_models()
        if success:
            print("✅ Models loaded successfully!")
        else:
            print("❌ Failed to load models")
        return
    
    try:
        # Train new models
        report = trainer.train_models()
        
        print("\n" + "="*60)
        print("🎯 TRAINING COMPLETE!")
        print("="*60)
        
        print(f"📊 Test Accuracy: {report['model_performance']['test_accuracy']:.1%}")
        print(f"📊 Precision: {report['model_performance']['precision']:.1%}")
        print(f"📊 Recall: {report['model_performance']['recall']:.1%}")
        print(f"📊 F1-Score: {report['model_performance']['f1_score']:.1%}")
        
        print(f"\n🔍 Top Important Features:")
        for feature in report['feature_importance']['top_features'][:5]:
            print(f"  • {feature['feature']}: {feature['importance']:.3f}")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        # Save report
        report_path = Path("models/training_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Full report saved to: {report_path}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
