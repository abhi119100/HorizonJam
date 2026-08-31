#!/usr/bin/env python3
"""
Analyze potential tie scenarios in key detection
"""

import json
import os
from collections import defaultdict
from itertools import combinations

def load_key_signatures():
    """Load key signatures from JSON file"""
    try:
        library_path = os.path.join('datasets', 'full_key_signature_library.json')
        with open(library_path, 'r') as f:
            key_data = json.load(f)
        
        key_signatures = {}
        for key_info in key_data:
            key_name = key_info['key']
            chord_names_list = [chord['name'] for chord in key_info['chords']]
            key_signatures[key_name] = chord_names_list
            
        return key_signatures
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading key signatures: {e}")
        return {}

def analyze_chord_overlaps(key_signatures):
    """Analyze chord overlaps between different keys"""
    print("=== CHORD OVERLAP ANALYSIS ===")
    print()
    
    # Find keys that share the most chords
    overlap_matrix = {}
    
    for key1, key2 in combinations(key_signatures.keys(), 2):
        chords1 = set(key_signatures[key1])
        chords2 = set(key_signatures[key2])
        
        overlap = chords1.intersection(chords2)
        overlap_count = len(overlap)
        
        if overlap_count >= 4:  # High overlap threshold
            overlap_matrix[(key1, key2)] = {
                'count': overlap_count,
                'chords': list(overlap),
                'key1_unique': list(chords1 - chords2),
                'key2_unique': list(chords2 - chords1)
            }
    
    # Sort by overlap count
    sorted_overlaps = sorted(overlap_matrix.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"Found {len(sorted_overlaps)} key pairs with 4+ shared chords:")
    print()
    
    for (key1, key2), data in sorted_overlaps[:15]:  # Show top 15
        print(f"{key1} vs {key2}: {data['count']} shared chords")
        print(f"  Shared: {data['chords']}")
        print(f"  {key1} unique: {data['key1_unique']}")
        print(f"  {key2} unique: {data['key2_unique']}")
        print()
    
    return overlap_matrix

def simulate_tie_scenarios(key_signatures, overlap_matrix):
    """Simulate potential tie scenarios"""
    print("=== POTENTIAL TIE SCENARIOS ===")
    print()
    
    tie_scenarios = []
    
    for (key1, key2), data in overlap_matrix.items():
        shared_chords = data['chords']
        
        # Simulate scoring with different chord combinations
        for num_shared in range(2, min(len(shared_chords) + 1, 6)):
            for chord_combo in combinations(shared_chords, num_shared):
                chord_set = list(chord_combo)
                
                # Calculate scores for both keys
                score1 = calculate_key_score(key1, chord_set, key_signatures)
                score2 = calculate_key_score(key2, chord_set, key_signatures)
                
                if score1 == score2 and score1 > 0:
                    tie_scenarios.append({
                        'keys': [key1, key2],
                        'score': score1,
                        'chords': chord_set,
                        'tonic1': key1.split()[0],
                        'tonic2': key2.split()[0]
                    })
    
    # Remove duplicates and sort
    unique_scenarios = []
    seen = set()
    
    for scenario in tie_scenarios:
        key_tuple = tuple(sorted(scenario['keys']))
        chord_tuple = tuple(sorted(scenario['chords']))
        signature = (key_tuple, chord_tuple)
        
        if signature not in seen:
            seen.add(signature)
            unique_scenarios.append(scenario)
    
    unique_scenarios.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Found {len(unique_scenarios)} potential tie scenarios:")
    print()
    
    for i, scenario in enumerate(unique_scenarios[:20]):  # Show top 20
        print(f"{i+1}. {scenario['keys'][0]} vs {scenario['keys'][1]} (Score: {scenario['score']})")
        print(f"   Chords: {scenario['chords']}")
        print(f"   Tonics: {scenario['tonic1']} vs {scenario['tonic2']}")
        
        # Check if tonics are in the chord set
        tonic1_present = scenario['tonic1'] in scenario['chords'] or scenario['tonic1'] + 'm' in scenario['chords']
        tonic2_present = scenario['tonic2'] in scenario['chords'] or scenario['tonic2'] + 'm' in scenario['chords']
        
        print(f"   Tonic presence: {scenario['tonic1']}={tonic1_present}, {scenario['tonic2']}={tonic2_present}")
        print()
    
    return unique_scenarios

def calculate_key_score(key, chord_list, key_signatures):
    """Calculate traditional key detection score"""
    if key not in key_signatures:
        return 0
    
    key_chords = key_signatures[key]
    score = 0
    
    # Count chord matches
    for chord in chord_list:
        if chord in key_chords:
            score += 1
    
    # Bonus for tonic chord presence
    tonic = key.split()[0]
    if tonic in chord_list:
        score += 2
    
    return score

def analyze_relative_keys(key_signatures):
    """Analyze relative major/minor key relationships"""
    print("=== RELATIVE KEY ANALYSIS ===")
    print()
    
    relative_pairs = []
    
    for key in key_signatures.keys():
        if 'major' in key:
            tonic = key.split()[0]
            # Find relative minor (6th degree)
            relative_minor_candidates = []
            
            for other_key in key_signatures.keys():
                if 'minor' in other_key:
                    other_tonic = other_key.split()[0]
                    # Check if they share most chords
                    major_chords = set(key_signatures[key])
                    minor_chords = set(key_signatures[other_key])
                    overlap = len(major_chords.intersection(minor_chords))
                    
                    if overlap >= 6:  # Should share 6 out of 7 chords
                        relative_minor_candidates.append((other_key, overlap))
            
            if relative_minor_candidates:
                # Find the best match
                best_match = max(relative_minor_candidates, key=lambda x: x[1])
                relative_pairs.append((key, best_match[0], best_match[1]))
    
    print("Relative major/minor pairs with high chord overlap:")
    for major, minor, overlap in relative_pairs:
        print(f"{major} <-> {minor}: {overlap} shared chords")
        
        # Show the shared and different chords
        major_chords = set(key_signatures[major])
        minor_chords = set(key_signatures[minor])
        shared = major_chords.intersection(minor_chords)
        major_unique = major_chords - minor_chords
        minor_unique = minor_chords - major_chords
        
        print(f"  Shared: {sorted(list(shared))}")
        print(f"  {major} unique: {sorted(list(major_unique))}")
        print(f"  {minor} unique: {sorted(list(minor_unique))}")
        print()
    
    return relative_pairs

def main():
    print("Key Detection Tie Analysis")
    print("=" * 50)
    print()
    
    key_signatures = load_key_signatures()
    if not key_signatures:
        print("Failed to load key signatures")
        return
    
    print(f"Loaded {len(key_signatures)} keys")
    print()
    
    # Analyze chord overlaps
    overlap_matrix = analyze_chord_overlaps(key_signatures)
    
    # Simulate tie scenarios
    tie_scenarios = simulate_tie_scenarios(key_signatures, overlap_matrix)
    
    # Analyze relative keys
    relative_pairs = analyze_relative_keys(key_signatures)
    
    print("=== SUMMARY ===")
    print(f"Total keys analyzed: {len(key_signatures)}")
    print(f"High-overlap key pairs: {len(overlap_matrix)}")
    print(f"Potential tie scenarios: {len(tie_scenarios)}")
    print(f"Relative major/minor pairs: {len(relative_pairs)}")
    print()
    print("Most problematic tie scenarios (highest scores):")
    for scenario in tie_scenarios[:5]:
        print(f"  {scenario['keys'][0]} vs {scenario['keys'][1]} (Score: {scenario['score']})")

if __name__ == "__main__":
    main()