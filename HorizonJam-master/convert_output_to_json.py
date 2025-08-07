  #!/usr/bin/env python3
"""
Convert chord detection terminal output to JSON format
"""

import json
import re
from typing import List, Dict, Any

def parse_chord_output_to_json(output_text: str) -> Dict[str, Any]:
    """
    Parse the terminal output and convert to structured JSON
    """
    
    # Extract chord events
    chord_events = []
    event_pattern = r'(\d+)\. \[(\d{2}:\d{2}) - (\d{2}:\d{2})\] -> ([A-G][#b]?[^\s]*) \(play #(\d+)\) \(([\d.]+)s\)'
    
    for match in re.finditer(event_pattern, output_text):
        event = {
            "event_number": int(match.group(1)),
            "start_time": match.group(2),
            "end_time": match.group(3),
            "chord": match.group(4),
            "play_number": int(match.group(5)),
            "duration_seconds": float(match.group(6))
        }
        chord_events.append(event)
    
    # Extract key detection
    key_match = re.search(r'\[KEY\] Detected Key: ([A-G][#b]? (?:major|minor))', output_text)
    detected_key = key_match.group(1) if key_match else None
    
    # Extract total chord events
    total_match = re.search(r'\[TOTAL\] Total chord events: (\d+)', output_text)
    total_events = int(total_match.group(1)) if total_match else len(chord_events)
    
    # Extract progression
    progression_match = re.search(r'Progression: ([A-G#b\s-]+)', output_text)
    progression = progression_match.group(1).strip() if progression_match else None
    
    # Extract accuracy
    accuracy_match = re.search(r'Estimated accuracy: ([\d.]+)%', output_text)
    accuracy = float(accuracy_match.group(1)) if accuracy_match else None
    
    # Extract guitar tabs
    guitar_tabs = []
    
    # Pattern to match guitar tab sections
    tab_pattern = r'\[GUITAR\] ([A-G][#b]?[^\s]*) Chord\s*={40}\s*Guitar Tab\s*-{10}\s*((?:E \|--[x\d]--\s*\n?)+)'
    
    for match in re.finditer(tab_pattern, output_text, re.MULTILINE | re.DOTALL):
        chord_name = match.group(1)
        tab_lines = match.group(2).strip().split('\n')
        
        # Parse individual string positions
        strings = {}
        for line in tab_lines:
            if '|--' in line:
                string_match = re.match(r'([EADGBE]) \|--([x\d])--', line.strip())
                if string_match:
                    strings[string_match.group(1)] = string_match.group(2)
        
        # Extract difficulty and dataset info for this chord
        chord_section_start = output_text.find(f'[GUITAR] {chord_name} Chord')
        if chord_section_start > 0:
            # Look backwards for difficulty and dataset info
            section_before = output_text[:chord_section_start]
            
            difficulty_match = re.search(r'\[DIFFICULTY\] ([^\n]+)', section_before[::-1])
            difficulty = difficulty_match.group(1)[::-1] if difficulty_match else None
            
            dataset_match = re.search(r'\[DATASET\] Found in dataset: (\d+) times', section_before[::-1])
            dataset_count = int(dataset_match.group(1)[::-1]) if dataset_match else None
            
            compact_match = re.search(r'\[COMPACT\] ([x\d]+)', section_before[::-1])
            compact_notation = compact_match.group(1)[::-1] if compact_match else None
        
        tab_info = {
            "chord": chord_name,
            "strings": strings,
            "difficulty": difficulty,
            "dataset_count": dataset_count,
            "compact_notation": compact_notation
        }
        guitar_tabs.append(tab_info)
    
    # Create final JSON structure
    result = {
        "analysis_summary": {
            "detected_key": detected_key,
            "total_chord_events": total_events,
            "chord_progression": progression,
            "estimated_accuracy_percent": accuracy
        },
        "chord_events": chord_events,
        "guitar_tabs": guitar_tabs,
        "metadata": {
            "source": "HorizonJam chord detection",
            "format_version": "1.0"
        }
    }
    
    return result

def main():
    # Sample output from terminal (lines 90-144)
    sample_output = """
==================================================                                  
CHORD EVENT DETECTION (Distinct Plays)                                              
==================================================                                  
1. [00:00 - 00:00] -> B (play #1) (0.7s)                                            
2. [00:00 - 00:05] -> E (play #2) (4.3s)                                            
3. [00:05 - 00:05] -> B (play #3) (0.7s)                                            
4. [00:05 - 00:15] -> E (play #4) (10.1s)                                           
5. [00:15 - 00:16] -> B (play #5) (0.7s)                                            
6. [00:16 - 00:21] -> E (play #6) (4.6s)                                            
                                                                                    
[KEY] Detected Key: E major                                                         
[TOTAL] Total chord events: 6                                                       
                                                                                    
============================================================                        
CHORD PROGRESSION & TABS                                                            
============================================================                        
Progression: B - E - B - E - B - E                                                  
Total chords: 6 | Estimated accuracy: 85.0%                                         
                                                                                    
                                                                                    
Chord Tabs (unique)                                                                 
----------------------------------------                                            
                                                                                    
[DIFFICULTY] Easy (Level 2)                                                         
[DATASET] Found in dataset: 6 times                                                 
[COMPACT] 022454                                                                    
                                                                                    
[GUITAR] E Chord                                                                    
========================================                                            
    Guitar Tab                                                                      
    ----------                                                                      
E |--0--                                                                            
A |--2--                                                                            
D |--2--                                                                            
G |--4--                                                                            
B |--5--                                                                            
E |--4--                                                                            
                                                                                    
[DIFFICULTY] Advanced (Level 4)                                                     
[DATASET] Found in dataset: 50 times                                                
[COMPACT] x24442                                                                    
                                                                                    
[GUITAR] B Chord                                                                    
========================================                                            
    Guitar Tab                                                                      
    ----------                                                                      
E |--x--                                                                            
A |--2--                                                                            
D |--4--                                                                            
G |--4--                                                                            
B |--4--                                                                            
E |--2--
"""
    
    # Convert to JSON
    json_result = parse_chord_output_to_json(sample_output)
    
    # Pretty print JSON
    print(json.dumps(json_result, indent=2))
    
    # Save to file
    with open('chord_analysis_output.json', 'w') as f:
        json.dump(json_result, f, indent=2)
    
    print("\n✅ JSON output saved to 'chord_analysis_output.json'")

if __name__ == "__main__":
    main()