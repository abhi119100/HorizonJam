#!/usr/bin/env python3
"""
Viterbi Sequence Smoothing for Chord Detection
Implements HMM-based sequence smoothing to reduce chord flicker and improve musical consistency
"""

import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class ChordViterbiSmoother:
    """
    Implements Viterbi decoding for chord sequence smoothing
    Uses musical transition probabilities to enforce sequence consistency
    """
    
    def __init__(self):
        self.chord_vocab = [
            'C', 'Dm', 'Em', 'F', 'G', 'Am', 'Bdim',  # C major
            'G', 'Am', 'Bm', 'C', 'D', 'Em', 'F#dim',  # G major
            'D', 'Em', 'F#m', 'G', 'A', 'Bm', 'C#dim',  # D major
            'A', 'Bm', 'C#m', 'D', 'E', 'F#m', 'G#dim',  # A major
            'E', 'F#m', 'G#m', 'A', 'B', 'C#m', 'D#dim',  # E major
            'F', 'Gm', 'Am', 'Bb', 'C', 'Dm', 'Edim',  # F major
            'Bb', 'Cm', 'Dm', 'Eb', 'F', 'Gm', 'Adim',  # Bb major
            # Extended chords
            'C7', 'Dm7', 'Em7', 'Fmaj7', 'G7', 'Am7', 'Bm7b5',
            'Csus2', 'Csus4', 'Dsus2', 'Dsus4', 'Esus2', 'Esus4',
            'Fsus2', 'Fsus4', 'Gsus2', 'Gsus4', 'Asus2', 'Asus4',
            'Bsus2', 'Bsus4'
        ]
        
        # Remove duplicates and sort
        self.chord_vocab = sorted(list(set(self.chord_vocab)))
        self.chord_to_idx = {chord: i for i, chord in enumerate(self.chord_vocab)}
        self.transition_matrix = self._build_default_transition_matrix()
        
    def _build_default_transition_matrix(self) -> np.ndarray:
        """
        Build default chord transition matrix based on music theory
        Higher probabilities for common progressions (V-I, ii-V, IV-I, etc.)
        """
        n_chords = len(self.chord_vocab)
        # Start with uniform low probability
        transitions = np.full((n_chords, n_chords), 0.01)
        
        # Add self-transition probability (chord repetition)
        np.fill_diagonal(transitions, 0.3)
        
        # Define common chord progressions with higher probabilities
        common_progressions = [
            # Major key progressions
            ('C', 'F', 0.15), ('C', 'G', 0.15), ('C', 'Am', 0.12),
            ('F', 'C', 0.18), ('F', 'G', 0.12), ('F', 'Dm', 0.10),
            ('G', 'C', 0.20), ('G', 'Am', 0.12), ('G', 'F', 0.10),
            ('Am', 'F', 0.15), ('Am', 'C', 0.12), ('Am', 'G', 0.10),
            ('Dm', 'G', 0.18), ('Dm', 'Am', 0.12), ('Dm', 'F', 0.10),
            ('Em', 'Am', 0.15), ('Em', 'F', 0.12), ('Em', 'G', 0.10),
            
            # ii-V-I progressions
            ('Dm', 'G', 0.20), ('G', 'C', 0.25),
            ('Em', 'A', 0.20), ('A', 'D', 0.25),
            ('Am', 'D', 0.18), ('D', 'G', 0.25),
            
            # Seventh chord progressions
            ('C7', 'F', 0.22), ('F', 'C7', 0.15),
            ('G7', 'C', 0.25), ('C', 'G7', 0.12),
            ('Am7', 'Dm7', 0.18), ('Dm7', 'G7', 0.20),
            
            # Sus chord resolutions
            ('Csus4', 'C', 0.30), ('Csus2', 'C', 0.25),
            ('Fsus4', 'F', 0.30), ('Fsus2', 'F', 0.25),
            ('Gsus4', 'G', 0.30), ('Gsus2', 'G', 0.25),
        ]
        
        # Apply common progressions
        for from_chord, to_chord, prob in common_progressions:
            if from_chord in self.chord_to_idx and to_chord in self.chord_to_idx:
                from_idx = self.chord_to_idx[from_chord]
                to_idx = self.chord_to_idx[to_chord]
                transitions[from_idx, to_idx] = prob
        
        # Normalize rows to sum to 1
        transitions = transitions / transitions.sum(axis=1, keepdims=True)
        
        return transitions
    
    def update_transition_matrix_from_data(self, chord_sequences: List[List[str]], 
                                         smoothing: float = 0.1) -> None:
        """
        Update transition matrix from observed chord sequences
        Uses Laplace smoothing to handle unseen transitions
        """
        n_chords = len(self.chord_vocab)
        observed_transitions = np.zeros((n_chords, n_chords))
        
        for sequence in chord_sequences:
            for i in range(len(sequence) - 1):
                from_chord = sequence[i]
                to_chord = sequence[i + 1]
                
                if from_chord in self.chord_to_idx and to_chord in self.chord_to_idx:
                    from_idx = self.chord_to_idx[from_chord]
                    to_idx = self.chord_to_idx[to_chord]
                    observed_transitions[from_idx, to_idx] += 1
        
        # Apply Laplace smoothing
        smoothed_transitions = observed_transitions + smoothing
        
        # Normalize
        self.transition_matrix = smoothed_transitions / smoothed_transitions.sum(axis=1, keepdims=True)
        
        print(f"📊 Updated transition matrix from {len(chord_sequences)} sequences")
    
    def viterbi_decode(self, emission_probs: np.ndarray, 
                      chord_labels: List[str]) -> Tuple[List[str], List[float]]:
        """
        Viterbi decoding to find most likely chord sequence
        
        Args:
            emission_probs: (T, N) array of chord probabilities per timestep
            chord_labels: List of chord labels for each timestep
            
        Returns:
            smoothed_sequence: Most likely chord sequence
            path_probabilities: Probability of each chord in the path
        """
        T, N = emission_probs.shape
        
        # Map chord labels to indices
        chord_indices = []
        for chord in chord_labels:
            if chord in self.chord_to_idx:
                chord_indices.append(self.chord_to_idx[chord])
            else:
                # Handle unknown chords - find closest match
                chord_indices.append(0)  # default to first chord
        
        # Initialize Viterbi tables
        viterbi = np.zeros((T, N))
        path = np.zeros((T, N), dtype=int)
        
        # Initialize first timestep
        viterbi[0] = np.log(emission_probs[0] + 1e-10)
        
        # Forward pass
        for t in range(1, T):
            for j in range(N):
                # Find best previous state
                transition_scores = viterbi[t-1] + np.log(self.transition_matrix[:, j] + 1e-10)
                best_prev = np.argmax(transition_scores)
                
                viterbi[t, j] = transition_scores[best_prev] + np.log(emission_probs[t, j] + 1e-10)
                path[t, j] = best_prev
        
        # Backward pass - find best path
        best_path = np.zeros(T, dtype=int)
        best_path[-1] = np.argmax(viterbi[-1])
        
        for t in range(T-2, -1, -1):
            best_path[t] = path[t+1, best_path[t+1]]
        
        # Convert back to chord names and get probabilities
        smoothed_sequence = [self.chord_vocab[idx] for idx in best_path]
        path_probabilities = [np.exp(viterbi[t, best_path[t]]) for t in range(T)]
        
        return smoothed_sequence, path_probabilities
    
    def smooth_chord_sequence(self, chord_detections: List[Dict], 
                            confidence_threshold: float = 0.1) -> List[Dict]:
        """
        Apply Viterbi smoothing to a sequence of chord detections
        
        Args:
            chord_detections: List of chord detection results with probabilities
            confidence_threshold: Minimum confidence to consider
            
        Returns:
            smoothed_detections: Chord detections with smoothed sequence
        """
        if len(chord_detections) < 2:
            return chord_detections
        
        # Extract emission probabilities and labels
        chord_labels = [d['chord'] for d in chord_detections]
        confidences = [d.get('confidence', 1.0) for d in chord_detections]
        
        # Create emission probability matrix
        n_timesteps = len(chord_detections)
        n_chords = len(self.chord_vocab)
        emission_probs = np.zeros((n_timesteps, n_chords))
        
        for t, (chord, conf) in enumerate(zip(chord_labels, confidences)):
            if chord in self.chord_to_idx:
                # High probability for detected chord
                chord_idx = self.chord_to_idx[chord]
                emission_probs[t, chord_idx] = max(conf, confidence_threshold)
                
                # Small probability for other chords
                emission_probs[t] += 0.01
                emission_probs[t, chord_idx] = max(conf, confidence_threshold)
            else:
                # Unknown chord - uniform distribution
                emission_probs[t] = 1.0 / n_chords
        
        # Normalize emission probabilities
        emission_probs = emission_probs / emission_probs.sum(axis=1, keepdims=True)
        
        # Apply Viterbi decoding
        smoothed_chords, smoothed_probs = self.viterbi_decode(emission_probs, chord_labels)
        
        # Update chord detections with smoothed results
        smoothed_detections = []
        for i, detection in enumerate(chord_detections):
            smoothed_detection = detection.copy()
            smoothed_detection['chord'] = smoothed_chords[i]
            smoothed_detection['viterbi_confidence'] = smoothed_probs[i]
            smoothed_detection['original_chord'] = detection['chord']
            smoothed_detection['smoothed'] = (smoothed_chords[i] != detection['chord'])
            smoothed_detections.append(smoothed_detection)
        
        return smoothed_detections
    
    def save_transition_matrix(self, filepath: str) -> None:
        """Save transition matrix to file"""
        data = {
            'chord_vocab': self.chord_vocab,
            'transition_matrix': self.transition_matrix.tolist(),
            'created_at': str(Path().cwd())
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Transition matrix saved to: {filepath}")
    
    def load_transition_matrix(self, filepath: str) -> bool:
        """Load transition matrix from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.chord_vocab = data['chord_vocab']
            self.chord_to_idx = {chord: i for i, chord in enumerate(self.chord_vocab)}
            self.transition_matrix = np.array(data['transition_matrix'])
            
            print(f"📂 Transition matrix loaded from: {filepath}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to load transition matrix: {e}")
            return False


def test_viterbi_smoothing():
    """Test the Viterbi smoothing with a sample chord sequence"""
    
    # Sample chord detections with some noise
    sample_detections = [
        {'chord': 'C', 'confidence': 0.9, 'timestamp': 0.0},
        {'chord': 'Am', 'confidence': 0.6, 'timestamp': 1.0},  # noisy
        {'chord': 'F', 'confidence': 0.8, 'timestamp': 2.0},
        {'chord': 'C', 'confidence': 0.5, 'timestamp': 3.0},   # noisy
        {'chord': 'G', 'confidence': 0.9, 'timestamp': 4.0},
        {'chord': 'Am', 'confidence': 0.7, 'timestamp': 5.0},  # noisy
        {'chord': 'C', 'confidence': 0.95, 'timestamp': 6.0},
    ]
    
    smoother = ChordViterbiSmoother()
    smoothed = smoother.smooth_chord_sequence(sample_detections)
    
    print("🎯 Viterbi Smoothing Test Results:")
    print("=" * 50)
    
    for i, (orig, smooth) in enumerate(zip(sample_detections, smoothed)):
        changed = "✓" if smooth['smoothed'] else " "
        print(f"{i+1}. [{orig['timestamp']:4.1f}s] {orig['chord']:>6} → {smooth['chord']:>6} "
              f"(conf: {smooth['viterbi_confidence']:.3f}) {changed}")
    
    return smoothed


if __name__ == "__main__":
    test_viterbi_smoothing()
