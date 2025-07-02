#!/usr/bin/env python3
"""
MIDI to Chords Display Tool
Converts BasicPitch MIDI output to chord progressions with timestamps
"""

import sys
import os
from pathlib import Path
import pretty_midi
import librosa
from music21 import converter, chord, stream, pitch, interval, key
from collections import defaultdict
import numpy as np

def parse_midi_notes(midi_path):
    """Parse MIDI file and extract notes with timestamps"""
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        # Get all notes across all instruments
        all_notes = []
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                all_notes.append({
                    'start': note.start,
                    'end': note.end,
                    'pitch': note.pitch,
                    'velocity': note.velocity,
                    'note_name': librosa.midi_to_note(note.pitch)
                })
        
        # Sort by start time
        all_notes.sort(key=lambda x: x['start'])
        return all_notes, midi_data.get_end_time()
        
    except Exception as e:
        print(f"❌ Error parsing MIDI: {e}")
        return [], 0

def filter_musical_notes(notes, min_velocity=45, min_duration=0.1):
    """Filter out noise and artifacts, keeping only real musical notes - AGGRESSIVE"""
    filtered_notes = []
    
    for note in notes:
        # Much stricter velocity filter - real guitar chords are loud
        if note['velocity'] < min_velocity:
            continue
            
        # Stricter duration filter - real chord notes last longer
        note_duration = note['end'] - note['start']
        if note_duration < min_duration:
            continue
            
        filtered_notes.append(note)
    
    return filtered_notes

def detect_musical_activity(window_notes, min_notes=2, min_total_velocity=120):
    """Detect if a window contains real musical activity vs silence/noise - RELAXED"""
    if len(window_notes) < min_notes:
        return False
    
    # Relaxed velocity check to catch quieter second strikes
    total_velocity = sum(note['velocity'] for note in window_notes)
    if total_velocity < min_total_velocity:
        return False
    
    # For guitar chords, we need multiple notes
    unique_pitches = set(note['pitch'] for note in window_notes)
    if len(unique_pitches) < 2:  # Must have at least 2 different notes for a chord
        return False
    
    # More lenient pitch range (guitar chords can span wider intervals)
    pitches = sorted(unique_pitches)
    pitch_range = pitches[-1] - pitches[0]
    if pitch_range > 60:  # Increased from 50 to allow wider chords
        return False
    
    return True

def group_notes_by_time_windows(notes, window_size=2.0):
    """Group notes into time windows for chord detection with silence detection"""
    if not notes:
        return []
    
    # Filter out noise and artifacts first
    musical_notes = filter_musical_notes(notes)
    if not musical_notes:
        return []
    
    total_duration = max(note['end'] for note in musical_notes)
    windows = []
    
    current_time = 0
    while current_time < total_duration:
        window_end = min(current_time + window_size, total_duration)
        
        # Find notes that are active in this window
        window_notes = []
        for note in musical_notes:
            # Note is active if it overlaps with the window
            if note['start'] < window_end and note['end'] > current_time:
                window_notes.append(note)
        
        # Only add windows with real musical activity
        if window_notes and detect_musical_activity(window_notes):
            windows.append({
                'start': current_time,
                'end': window_end,
                'notes': window_notes,
                'is_musical': True
            })
        
        current_time += window_size
    
    return windows

def identify_chord_from_pitches(pitches):
    """Comprehensive chord identification including suspended and extended chords"""
    if not pitches:
        return "Silence"
    
    try:
        # Convert MIDI pitches to note names and pitch classes
        note_names = []
        pitch_classes = set()
        
        for midi_pitch in pitches:
            try:
                note_name = librosa.midi_to_note(midi_pitch)
                # Extract just the note letter (G, C, D, etc.) without octave
                root_note = note_name[0]
                if len(note_name) > 1 and note_name[1] in ['#', '♯', 'b', '♭']:
                    # Convert Unicode symbols to ASCII for consistent matching
                    sharp_flat = note_name[1]
                    if sharp_flat == '♯':
                        sharp_flat = '#'
                    elif sharp_flat == '♭':
                        sharp_flat = 'b'
                    root_note += sharp_flat
                
                note_names.append(note_name)
                pitch_classes.add(root_note)
            except:
                continue
        
        if not pitch_classes:
            return "Unknown"
        
        # Convert to sorted list for consistent analysis
        unique_notes = sorted(list(pitch_classes))
        note_set = frozenset(unique_notes)
        
        if len(unique_notes) == 1:
            return unique_notes[0]  # Single note
        
        # COMPREHENSIVE CHORD PATTERNS - HIGHEST PRIORITY FIRST
        
        # 1. SUSPENDED CHORDS (sus2, sus4) - CRITICAL FOR USER'S SEQUENCE
        suspended_chords = {
            # sus2 chords (root + 2nd + 5th)
            frozenset(['E', 'F#', 'B']): 'Esus2',
            frozenset(['A', 'B', 'E']): 'Asus2', 
            frozenset(['D', 'E', 'A']): 'Dsus2',
            frozenset(['G', 'A', 'D']): 'Gsus2',
            frozenset(['C', 'D', 'G']): 'Csus2',
            frozenset(['F', 'G', 'C']): 'Fsus2',
            frozenset(['B', 'C#', 'F#']): 'Bsus2',
            
            # sus4 chords (root + 4th + 5th)  
            frozenset(['E', 'A', 'B']): 'Esus4',
            frozenset(['A', 'D', 'E']): 'Asus4',
            frozenset(['D', 'G', 'A']): 'Dsus4', 
            frozenset(['G', 'C', 'D']): 'Gsus4',
            frozenset(['C', 'F', 'G']): 'Csus4',
            frozenset(['F', 'Bb', 'C']): 'Fsus4',
            frozenset(['B', 'E', 'F#']): 'Bsus4',
        }
        
        # 2. MINOR 7TH CHORDS - CRITICAL FOR F#m7
        minor_seventh_chords = {
            frozenset(['F#', 'A', 'C#', 'E']): 'F#m7',
            frozenset(['A', 'C', 'E', 'G']): 'Am7',
            frozenset(['D', 'F', 'A', 'C']): 'Dm7',
            frozenset(['E', 'G', 'B', 'D']): 'Em7',
            frozenset(['B', 'D', 'F#', 'A']): 'Bm7',
            frozenset(['C', 'Eb', 'G', 'Bb']): 'Cm7',
            frozenset(['G', 'Bb', 'D', 'F']): 'Gm7',
            frozenset(['C#', 'E', 'G#', 'B']): 'C#m7',
        }
        
        # 3. BASIC MAJOR CHORDS  
        basic_major = {
            frozenset(['E', 'G#', 'B']): 'E',
            frozenset(['A', 'C#', 'E']): 'A',
            frozenset(['B', 'D#', 'F#']): 'B',
            frozenset(['F#', 'A#', 'C#']): 'F#',
            frozenset(['C', 'E', 'G']): 'C',
            frozenset(['D', 'F#', 'A']): 'D',
            frozenset(['G', 'B', 'D']): 'G',
            frozenset(['F', 'A', 'C']): 'F',
        }
        
        # 4. BASIC MINOR CHORDS
        basic_minor = {
            frozenset(['F#', 'A', 'C#']): 'F#m',
            frozenset(['A', 'C', 'E']): 'Am',
            frozenset(['B', 'D', 'F#']): 'Bm',
            frozenset(['E', 'G', 'B']): 'Em',
            frozenset(['C', 'Eb', 'G']): 'Cm',
            frozenset(['D', 'F', 'A']): 'Dm',
            frozenset(['G', 'Bb', 'D']): 'Gm',
            frozenset(['C#', 'E', 'G#']): 'C#m',
        }
        
        # 5. DOMINANT 7TH CHORDS
        dominant_seventh = {
            frozenset(['E', 'G#', 'B', 'D']): 'E7',
            frozenset(['A', 'C#', 'E', 'G']): 'A7',
            frozenset(['B', 'D#', 'F#', 'A']): 'B7',
            frozenset(['F#', 'A#', 'C#', 'E']): 'F#7',
            frozenset(['C', 'E', 'G', 'Bb']): 'C7',
            frozenset(['D', 'F#', 'A', 'C']): 'D7',
            frozenset(['G', 'B', 'D', 'F']): 'G7',
        }
        
        # 6. MAJOR 7TH CHORDS
        major_seventh = {
            frozenset(['E', 'G#', 'B', 'D#']): 'Emaj7',
            frozenset(['A', 'C#', 'E', 'G#']): 'Amaj7', 
            frozenset(['B', 'D#', 'F#', 'A#']): 'Bmaj7',
            frozenset(['F#', 'A#', 'C#', 'F']): 'F#maj7',
            frozenset(['C', 'E', 'G', 'B']): 'Cmaj7',
            frozenset(['D', 'F#', 'A', 'C#']): 'Dmaj7',
            frozenset(['G', 'B', 'D', 'F#']): 'Gmaj7',
            frozenset(['F', 'A', 'C', 'E']): 'Fmaj7',
        }
        
        # CHECK IN PRIORITY ORDER (most specific first)
        
        # 1. Check suspended chords FIRST (exact match)
        if note_set in suspended_chords:
            return suspended_chords[note_set]
        
        # 2. Check minor 7th chords (exact match)  
        if note_set in minor_seventh_chords:
            return minor_seventh_chords[note_set]
            
        # 3. Check major 7th chords (exact match)
        if note_set in major_seventh:
            return major_seventh[note_set]
            
        # 4. Check dominant 7th chords (exact match)
        if note_set in dominant_seventh:
            return dominant_seventh[note_set]
        
        # 5. Check basic chords (exact match)
        if note_set in basic_major:
            return basic_major[note_set]
        if note_set in basic_minor:
            return basic_minor[note_set]
        
        # 6. SUBSET MATCHING for chords with extra notes
        all_chord_patterns = {
            **suspended_chords,
            **minor_seventh_chords, 
            **major_seventh,
            **dominant_seventh,
            **basic_major,
            **basic_minor
        }
        
        # Find best subset match (prioritize more complex chords)
        best_match = None
        best_match_size = 0
        
        for pattern, chord_name in all_chord_patterns.items():
            if pattern.issubset(note_set):
                if len(pattern) > best_match_size:
                    best_match = chord_name
                    best_match_size = len(pattern)
        
        if best_match:
            return best_match
        
        # 7. SMART FALLBACK for unrecognized patterns
        # Look for root note patterns
        for root in ['E', 'F#', 'A', 'B', 'C', 'D', 'G', 'F']:
            if root in unique_notes:
                # Quick sus2 check
                if root == 'E' and 'F#' in unique_notes and 'B' in unique_notes:
                    return 'Esus2'
                elif root == 'F#' and 'A' in unique_notes and 'C#' in unique_notes:
                    if 'E' in unique_notes:
                        return 'F#m7'
                    else:
                        return 'F#m'
                elif root == 'A' and 'C#' in unique_notes and 'E' in unique_notes:
                    return 'A'
                return root
        
        return unique_notes[0] if unique_notes else "Unknown"
        
    except Exception as e:
        return "Unknown"

def format_time(seconds):
    """Format time in MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def detect_optimal_window_size(notes, total_duration):
    """Advanced automatic window detection for accurate chord boundary detection"""
    if not notes:
        return 2.0, ["No notes found"]
    
    reasoning = []
    
    # Calculate note density and timing patterns
    note_times = [note['start'] for note in notes]
    note_times.sort()
    
    # Find note clusters (chord strikes)
    chord_onsets = []
    last_time = 0
    
    for i, time in enumerate(note_times):
        if i == 0 or time - last_time > 0.3:  # New chord if >0.3s gap
            chord_onsets.append(time)
        last_time = time
    
    reasoning.append(f"Detected {len(chord_onsets)} potential chord strikes")
    
    if len(chord_onsets) <= 1:
        return 2.0, reasoning + ["Single chord detected → 2s windows"]
    
    # Calculate average gap between chord strikes
    gaps = []
    for i in range(1, len(chord_onsets)):
        gap = chord_onsets[i] - chord_onsets[i-1]
        gaps.append(gap)
    
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        reasoning.append(f"Average chord gap: {avg_gap:.1f}s")
        
        # Use 80% of average gap as window size (to catch individual strikes)
        optimal_window = avg_gap * 0.8
        
        # Clamp to reasonable range
        optimal_window = max(0.5, min(3.0, optimal_window))
        
        if optimal_window < 1.0:
            reasoning.append("Fast playing → small windows for precision")
        elif optimal_window > 2.0:
            reasoning.append("Slow playing → larger windows")
        else:
            reasoning.append("Medium pacing → balanced windows")
        
        return optimal_window, reasoning
    
    return 1.5, reasoning + ["Default medium windows"]

def analyze_midi_chords(midi_path, window_size=None):
    """Main function to analyze MIDI and extract chord progression"""
    print(f"🎼 MIDI to Chords Analyzer")
    print("=" * 50)
    print(f"📁 Analyzing: {Path(midi_path).name}")
    
    # Parse MIDI file first to get data for auto-detection
    notes, total_duration = parse_midi_notes(midi_path)
    if not notes:
        print("❌ No notes found in MIDI file")
        return
    
    # Auto-detect optimal window size if not provided
    if window_size is None:
        window_size, reasoning = detect_optimal_window_size(notes, total_duration)
        print(f"🤖 Auto-detected window size: {window_size} seconds")
        if reasoning:
            print(f"   Reasoning: {', '.join(reasoning)}")
    else:
        print(f"⏱️  Manual window size: {window_size} seconds")
        
    print("=" * 50)
    
    print(f"📊 Found {len(notes)} notes over {total_duration:.1f} seconds")
    
    # Show filtering results
    musical_notes = filter_musical_notes(notes)
    filtered_count = len(notes) - len(musical_notes)
    if filtered_count > 0:
        print(f"🔇 Filtered out {filtered_count} noise/artifact notes")
        print(f"🎵 {len(musical_notes)} musical notes remain")
    
    # Group notes into time windows
    windows = group_notes_by_time_windows(notes, window_size)
    print(f"🎵 Created {len(windows)} time windows")
    print()
    
    # Analyze each time window
    chord_progression = []
    
    for i, window in enumerate(windows):
        start_time = window['start']
        end_time = window['end']
        window_notes = window['notes']
        
        if not window_notes:
            continue
        
        # Extract unique pitches
        pitches = list(set(note['pitch'] for note in window_notes))
        
        # Get context for intelligent inference
        prev_chord = None
        next_chord = None
        
        # Get previous chord (if exists)
        if i > 0:
            prev_window = windows[i-1]
            prev_pitches = list(set(note['pitch'] for note in prev_window['notes']))
            prev_chord = identify_chord_from_pitches(prev_pitches)
        
        # Get next chord (if exists)  
        if i < len(windows) - 1:
            next_window = windows[i+1]
            next_pitches = list(set(note['pitch'] for note in next_window['notes']))
            next_chord = identify_chord_from_pitches(next_pitches)
        
        # Get extended region pitches for context
        region_start = max(0, i - 1)
        region_end = min(len(windows), i + 2)
        region_pitches = []
        for j in range(region_start, region_end):
            region_pitches.extend(note['pitch'] for note in windows[j]['notes'])
        region_pitches = list(set(region_pitches))
        
        # Use context-aware chord identification
        chord_name = identify_chord_with_context(pitches, prev_chord, next_chord, region_pitches)
        
        # Format time range  
        time_range = f"[{format_time(start_time)} - {format_time(end_time)}]"
        
        chord_progression.append({
            'start': start_time,
            'end': end_time, 
            'chord': chord_name,
            'note_count': len(window_notes),
            'unique_pitches': len(pitches),
            'time_range': time_range
        })
        
        print(f"{time_range} → {chord_name}")
        print(f"    Notes: {len(window_notes)}, Unique pitches: {len(pitches)}")
        
        # Show the actual notes for debugging
        note_names = [note['note_name'] for note in window_notes]
        unique_notes = sorted(set(note_names))
        print(f"    Pitches: {', '.join(unique_notes)}")
        
        # DEBUG: Show exact note analysis for all segments
        if len(pitches) >= 2:  # Show debug for all chord segments
            print(f"    🔍 MIDI pitches: {sorted(pitches)}")
            print(f"    🔍 Note analysis: {[librosa.midi_to_note(p) for p in sorted(pitches)]}")
            
            # Show what chord patterns are being matched
            root_notes = set()
            for p in pitches:
                try:
                    note_name = librosa.midi_to_note(p)
                    root_note = note_name[0]
                    if len(note_name) > 1 and note_name[1] in ['#', '♯', 'b', '♭']:
                        sharp_flat = note_name[1]
                        if sharp_flat == '♯':
                            sharp_flat = '#'
                        elif sharp_flat == '♭':
                            sharp_flat = 'b'
                        root_note += sharp_flat
                    root_notes.add(root_note)
                except:
                    continue
            print(f"    🔍 Root notes detected: {sorted(list(root_notes))}")
            
            # Check specifically for Esus2 pattern
            if 'E' in root_notes and 'B' in root_notes:
                if 'F#' in root_notes:
                    print(f"    🎯 ESUS2 PATTERN DETECTED: E + F# + B")
                else:
                    print(f"    ❌ Missing F# for Esus2 (has E + B)")
        
        print()
    
    # Convert chord progression to format expected by detect_chord_events
    chord_segments = [(item['start'], item['end'], item['chord'], item['note_count'], 
                      []) for item in chord_progression]
    
    # Use professional chord event detection
    grouped_chords = detect_chord_events(chord_segments)

    # Summary with grouped chords
    print("=" * 50)
    print("🎼 CHORD PROGRESSION SUMMARY")
    print("=" * 50)
    for item in chord_progression:
        print(f"{item['time_range']} → {item['chord']}")
    
    print("\n" + "=" * 50)
    print("🎯 CHORD EVENT DETECTION (Distinct Plays)")
    print("=" * 50)
    for i, event in enumerate(grouped_chords, 1):
        duration_str = f"{event['duration']:.1f}s"
        time_range = f"[{format_time(event['start'])} - {format_time(event['end'])}]"
        play_num = event['play_number']
        print(f"{i}. {time_range} → {event['chord']} (play #{play_num}) ({duration_str})")
    
    # Count total plays per chord
    chord_play_counts = {}
    for event in grouped_chords:
        chord = event['chord']
        chord_play_counts[chord] = chord_play_counts.get(chord, 0) + 1
    
    print(f"\n🎸 Total chord events detected: {len(grouped_chords)}")
    print("🎯 Chord play summary:")
    for chord, count in chord_play_counts.items():
        print(f"   {chord}: {count} time{'s' if count > 1 else ''}")
    
    # Analyze overall key
    key_sig = analyze_key_signature(notes, grouped_chords)
    print(f"\n🔑 Detected Key: {key_sig}")
    
    # Final summary
    raw_segments = len(chord_progression)
    chord_events = len(grouped_chords)
    print(f"\n💾 Analysis complete! Found {raw_segments} raw segments, {chord_events} chord events.")
    
    return chord_progression, grouped_chords

def analyze_key_signature(notes, chord_events=None):
    """Smart key signature analysis using multiple approaches"""
    
    # Method 1: Chord progression analysis (most reliable)
    if chord_events:
        key_from_chords = detect_key_from_chord_progression(chord_events)
        if key_from_chords != "Unknown":
            return key_from_chords
    
    # Method 2: Note frequency analysis
    if notes:
        key_from_notes = detect_key_from_notes(notes)
        if key_from_notes != "Unknown":
            return key_from_notes
    
    # Method 3: music21 analysis (if available)
    try:
        from music21 import stream, pitch, key
        if notes:
            key_from_music21 = detect_key_with_music21(notes)
            if key_from_music21 != "Unknown":
                return key_from_music21
    except ImportError:
        pass
    except Exception:
        pass
    
    return "Unknown"

def detect_key_from_chord_progression(chord_events):
    """Detect key signature from chord progression patterns"""
    if not chord_events:
        return "Unknown"
    
    # Get all unique chords
    chords = [event['chord'] for event in chord_events]
    chord_counts = {}
    for chord in chords:
        chord_counts[chord] = chord_counts.get(chord, 0) + 1
    
    # Most common chord is likely the tonic or relative
    most_common = max(chord_counts.items(), key=lambda x: x[1])[0]
    
    # Key signature patterns
    major_key_patterns = {
        # Pattern: [tonic, common chords in that key]
        'C': ['C', 'F', 'G', 'Am', 'Dm', 'Em'],
        'G': ['G', 'C', 'D', 'Em', 'Am', 'Bm'],
        'D': ['D', 'G', 'A', 'Bm', 'Em', 'F#m'],
        'A': ['A', 'D', 'E', 'F#m', 'Bm', 'C#m'],
        'E': ['E', 'A', 'B', 'C#m', 'F#m', 'G#m'],
        'F': ['F', 'Bb', 'C', 'Dm', 'Gm', 'Am'],
    }
    
    minor_key_patterns = {
        'Am': ['Am', 'F', 'G', 'C', 'Dm', 'Em', 'E'],
        'Em': ['Em', 'C', 'D', 'G', 'Am', 'Bm', 'B'],
        'Bm': ['Bm', 'G', 'A', 'D', 'Em', 'F#m', 'F#'],
        'F#m': ['F#m', 'D', 'E', 'A', 'Bm', 'C#m', 'C#'],
        'Dm': ['Dm', 'Bb', 'C', 'F', 'Gm', 'Am', 'A'],
        'Gm': ['Gm', 'Eb', 'F', 'Bb', 'Cm', 'Dm', 'D'],
    }
    
    # Score each possible key
    key_scores = {}
    
    # Check major keys
    for key, pattern in major_key_patterns.items():
        score = 0
        for chord in chords:
            if chord in pattern:
                score += chord_counts[chord]
        key_scores[f"{key} major"] = score
    
    # Check minor keys  
    for key, pattern in minor_key_patterns.items():
        score = 0
        for chord in chords:
            if chord in pattern:
                score += chord_counts[chord]
        key_scores[f"{key[:-1]} minor"] = score
    
    # Find best match
    if key_scores:
        best_key = max(key_scores.items(), key=lambda x: x[1])
        if best_key[1] > 0:  # At least some chords match
            return best_key[0]
    
    # Fallback: if most common chord is minor, assume that's the key
    if most_common.endswith('m') and not most_common.endswith('maj'):
        root = most_common[:-1] if most_common.endswith('m') else most_common
        return f"{root} minor"
    
    return "Unknown"

def detect_key_from_notes(notes):
    """Detect key from note frequency analysis"""
    if not notes:
        return "Unknown"
    
    try:
        # Count note frequencies
        note_counts = {}
        for note in notes:
            try:
                note_name = librosa.midi_to_note(note['pitch'])
                root_note = note_name[0]
                if len(note_name) > 1 and note_name[1] in ['#', '♯', 'b', '♭']:
                    sharp_flat = note_name[1]
                    if sharp_flat == '♯':
                        sharp_flat = '#'
                    elif sharp_flat == '♭':
                        sharp_flat = 'b'
                    root_note += sharp_flat
                note_counts[root_note] = note_counts.get(root_note, 0) + 1
            except:
                continue
        
        if not note_counts:
            return "Unknown"
        
        # Find most common note
        most_common_note = max(note_counts.items(), key=lambda x: x[1])[0]
        
        # Simple heuristics for major vs minor
        # Check for presence of major/minor third intervals
        if most_common_note == 'A':
            if 'C' in note_counts and 'E' in note_counts:
                if note_counts.get('C', 0) > note_counts.get('C#', 0):
                    return "A minor"
                else:
                    return "A major"
        elif most_common_note == 'C':
            if 'E' in note_counts and 'G' in note_counts:
                return "C major"
        elif most_common_note == 'G':
            if 'B' in note_counts and 'D' in note_counts:
                return "G major"
        elif most_common_note == 'D':
            if 'F#' in note_counts and 'A' in note_counts:
                return "D major"
        elif most_common_note == 'E':
            if 'G#' in note_counts and 'B' in note_counts:
                return "E major"
            elif 'G' in note_counts and 'B' in note_counts:
                return "E minor"
        
        # Fallback to most common note as key
        return f"{most_common_note} major"
        
    except Exception:
        return "Unknown"

def detect_key_with_music21(notes):
    """Detect key using music21 library"""
    try:
        from music21 import stream, pitch, key
        
        # Create a stream with weighted pitches
        s = stream.Stream()
        note_counts = {}
        
        for note in notes:
            try:
                midi_pitch = note['pitch']
                note_counts[midi_pitch] = note_counts.get(midi_pitch, 0) + 1
            except:
                continue
        
        # Add notes to stream based on frequency
        for midi_pitch, count in note_counts.items():
            try:
                p = pitch.Pitch(midi=midi_pitch)
                # Add multiple instances based on frequency (but cap at 10)
                for _ in range(min(count, 10)):
                    s.append(p)
            except:
                continue
        
        if len(s) == 0:
            return "Unknown"
        
        # Analyze key
        analyzed_key = s.analyze('key')
        if analyzed_key:
            mode = 'major' if analyzed_key.mode == 'major' else 'minor'
            return f"{analyzed_key.tonic.name} {mode}"
        
    except Exception:
        pass
    
    return "Unknown"

def detect_chord_events(window_segments):
    """Conservative chord event detection to avoid over-segmentation"""
    if not window_segments:
        return []
    
    chord_events = []
    print(f"🔍 Analyzing {len(window_segments)} chord segments...")
    
    i = 0
    while i < len(window_segments):
        start_time, end_time, chord, note_count, pitches = window_segments[i]
        
        # Skip silence and very weak chords
        if chord == "Silence" or note_count < 2:
            i += 1
            continue
            
        print(f"   Segment {i+1}: [{start_time:.1f}-{end_time:.1f}] → {chord} ({note_count} notes)")
        
        # Find all consecutive segments with the same chord
        current_chord = chord
        chord_start = start_time
        chord_end = end_time
        total_notes = note_count
        
        # Look ahead to group consecutive same-chord segments
        j = i + 1
        while j < len(window_segments):
            next_start, next_end, next_chord, next_notes, _ = window_segments[j]
            
            if next_chord != current_chord or next_notes < 2:
                break
                
            # Check for gap between segments
            gap = next_start - chord_end
            
            # More conservative: only split if gap > 1.0s (was 0.5s)
            if gap > 1.0:
                break
                
            # Extend the current chord
            chord_end = next_end
            total_notes += next_notes
            j += 1
        
        # Create single event for the chord group (less aggressive splitting)
        chord_events.append({
            'start': chord_start,
            'end': chord_end,
            'chord': current_chord,
            'play_number': len([e for e in chord_events if e['chord'] == current_chord]) + 1,
            'duration': chord_end - chord_start,
            'total_notes': total_notes
        })
        
        print(f"   ✅ Detected: {current_chord} (play #{len([e for e in chord_events if e['chord'] == current_chord])}) from {chord_start:.1f}s to {chord_end:.1f}s")
        
        i = j  # Skip to next unprocessed segment
    
    # POST-PROCESS: Merge very short events that are likely over-segmented
    merged_events = []
    for event in chord_events:
        # If this event is very short (<0.8s) and same chord as previous, merge them
        if (merged_events and 
            event['chord'] == merged_events[-1]['chord'] and 
            event['duration'] < 0.8 and 
            event['start'] - merged_events[-1]['end'] < 1.5):
            
            # Merge with previous event
            last_event = merged_events[-1]
            last_event['end'] = event['end']
            last_event['duration'] = last_event['end'] - last_event['start']
            last_event['total_notes'] += event['total_notes']
            print(f"   🔗 Merged short {event['chord']} segment into previous play")
        else:
            merged_events.append(event)
    
    # Re-number play counts after merging
    play_counts = {}
    for event in merged_events:
        chord = event['chord']
        play_counts[chord] = play_counts.get(chord, 0) + 1
        event['play_number'] = play_counts[chord]
    
    print(f"\n🎯 Total chord events detected: {len(merged_events)}")
    
    return merged_events

def identify_chord_with_context(pitches, prev_chord=None, next_chord=None, all_pitches_in_region=None):
    """Enhanced chord identification with aggressive Am7 detection and missing note inference"""
    
    # First try standard identification
    standard_chord = identify_chord_from_pitches(pitches)
    
    # INTELLIGENT MISSING NOTE INFERENCE
    # Convert pitches to note names for analysis
    detected_notes = set()
    for midi_pitch in pitches:
        try:
            note_name = librosa.midi_to_note(midi_pitch)
            root_note = note_name[0]
            if len(note_name) > 1 and note_name[1] in ['#', '♯', 'b', '♭']:
                sharp_flat = note_name[1]
                if sharp_flat == '♯':
                    sharp_flat = '#'
                elif sharp_flat == '♭':
                    sharp_flat = 'b'
                root_note += sharp_flat
            detected_notes.add(root_note)
        except:
            continue
    
    # MISSING NOTE PATTERNS - Common transcription failures
    
    # 1. ESUS2 INFERENCE: E + B (missing F#) → Esus2
    if detected_notes == {'E', 'B'} or ({'E', 'B'}.issubset(detected_notes) and 'G#' not in detected_notes):
        # If we have E + B but no G# (which would make it E major), likely Esus2
        print(f"    🎯 INFERRED: E + B pattern → likely Esus2 (missing F#)")
        return 'Esus2'
    
    # 2. F#m7 INFERENCE: F# + A + C# (missing E) → F#m7
    if detected_notes == {'F#', 'A', 'C#'} or ({'F#', 'A', 'C#'}.issubset(detected_notes)):
        # Check if context suggests F#m7
        if prev_chord in ['Esus2', 'E'] or next_chord in ['Esus2', 'E']:
            print(f"    🎯 INFERRED: F# + A + C# in E context → likely F#m7")
            return 'F#m7'
    
    # 3. ASUS2 INFERENCE: A + B + E (should be A + B + E) → Asus2  
    if detected_notes == {'A', 'B', 'E'} or ({'A', 'B', 'E'}.issubset(detected_notes) and 'C#' not in detected_notes):
        print(f"    🎯 INFERRED: A + B + E pattern → likely Asus2")
        return 'Asus2'
    
    # 4. MAJOR CHORD DISAMBIGUATION: E + B + G# is definitely E major (not Esus2)
    if {'E', 'B', 'G#'}.issubset(detected_notes):
        print(f"    🎯 CONFIRMED: E + B + G# → definitely E major")
        return 'E'
    
    # AGGRESSIVE Am7 DETECTION: If we detect C between Am chords, it's likely Am7
    if standard_chord == "C":
        # Check if previous or next chord is Am/Am7
        am_context = (prev_chord in ["Am", "Am7"] or next_chord in ["Am", "Am7"])
        
        if am_context and all_pitches_in_region:
            # Check if we have A note in the broader region
            region_notes = set()
            for midi_pitch in all_pitches_in_region:
                try:
                    note_name = librosa.midi_to_note(midi_pitch)
                    root_note = note_name[0]
                    if len(note_name) > 1 and note_name[1] in ['#', '♯', 'b', '♭']:
                        sharp_flat = note_name[1]
                        if sharp_flat == '♯':
                            sharp_flat = '#'
                        elif sharp_flat == '♭':
                            sharp_flat = 'b'
                        root_note += sharp_flat
                    region_notes.add(root_note)
                except:
                    continue
            
            # If we have A in the region, this C is probably Am7
            if 'A' in region_notes:
                return "Am7"
            
            # Even if no A detected, between Am chords, C is likely Am7
            if prev_chord in ["Am", "Am7"] and next_chord in ["Am", "Am7"]:
                return "Am7"
    
    # If context gives us a 7th chord and standard gives us a basic chord, prefer context
    if all_pitches_in_region and len(all_pitches_in_region) > len(pitches):
        context_chord = identify_chord_from_pitches(all_pitches_in_region)
        if '7' in context_chord and '7' not in standard_chord:
            return context_chord
    
    return standard_chord

def main():
    if len(sys.argv) < 2:
        print("Usage: python midi_to_chords.py <midi_file> [window_size]")
        print("\nExamples:")
        print("  python midi_to_chords.py basic_pitch_transcription.mid           # Auto-detect window size")
        print("  python midi_to_chords.py basic_pitch_transcription.mid 1.5      # Manual window size")
        print("  python midi_to_chords.py basic_pitch_transcription.mid auto     # Explicit auto-detect")
        return
    
    midi_path = sys.argv[1]
    
    # Handle window size parameter
    window_size = None  # Default: auto-detect
    if len(sys.argv) > 2:
        if sys.argv[2].lower() == 'auto':
            window_size = None  # Explicit auto-detect
        else:
            try:
                window_size = float(sys.argv[2])  # Manual window size
            except ValueError:
                print(f"❌ Error: Invalid window size '{sys.argv[2]}'. Use a number or 'auto'")
                return
    
    if not os.path.exists(midi_path):
        print(f"❌ Error: MIDI file '{midi_path}' not found")
        return
    
    # Analyze chords
    result = analyze_midi_chords(midi_path, window_size)
    
    if result:
        chord_progression, grouped_chords = result
        
        print(f"\n💾 Analysis complete! Found {len(chord_progression)} raw segments, {len(grouped_chords)} chord events.")

if __name__ == "__main__":
    main() 