import json
from typing import List, Dict

def calculate_experience_gain(chord: Dict) -> int:
    """Calculate experience gain based on chord complexity."""
    chord_name = chord.get('chord', '').lower()
    
    # Simple scoring based on chord complexity
    if 'major' in chord_name or 'minor' in chord_name:
        return 10
    elif '7' in chord_name or 'dim' in chord_name:
        return 20
    elif '9' in chord_name or '11' in chord_name or '13' in chord_name:
        return 30
    elif 'sus' in chord_name or 'add' in chord_name:
        return 25
    else:
        return 15

def export_to_json(chords: List[Dict], output_path: str, source: str = "guitar_audio") -> None:
    """Export chords to JSON with metadata for LLM tutor."""
    
    # Enhance chords with experience gain
    enhanced_chords = []
    for chord in chords:
        enhanced_chord = chord.copy()
        enhanced_chord['experience_gain'] = calculate_experience_gain(chord)
        enhanced_chords.append(enhanced_chord)
    
    # Calculate summary statistics
    unique_chords = len(set(c['chord'] for c in chords))
    total_duration = max(c.get('end_time', 0) for c in chords) if chords else 0
    
    json_data = {
        'chords': enhanced_chords,
        'summary': {
            'total_chords': len(chords),
            'unique_chords': unique_chords,
            'total_duration': total_duration,
            'average_experience_per_chord': sum(c['experience_gain'] for c in enhanced_chords) / len(enhanced_chords) if enhanced_chords else 0
        },
        'metadata': {
            'source': source,
            'version': '1.0',
            'format': 'guitar_chord_analysis'
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Chord analysis exported to: {output_path}")