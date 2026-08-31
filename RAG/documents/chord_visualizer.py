import json
import os
import re
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from pathlib import Path
from typing import Optional
import logging


def fetch_scales_chords_diagram(chord_name, instrument="guitar", output="image", size="100px", save_dir=Path("chord_diagrams")):
    """
    Try fetching a chord diagram from scales-chords.com
    Returns the saved image path or None if it fails
    """
    try:
        base_url = "https://www.scales-chords.com/chordimage.php"
        params = {
            "chord": chord_name,
            "instrument": instrument,
            "output": output,
            "size": size
        }
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code == 200 and response.content.startswith(b'\x89PNG'):
            save_dir.mkdir(parents=True, exist_ok=True)
            safe_name = chord_name.replace('/', '_')
            save_path = save_dir / f"{safe_name}_remote.png"
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return str(save_path)
    except Exception as e:
        print(f"Failed to fetch remote diagram for {chord_name}: {e}")
    
    return None





class ChordVisualizer:
    """Class to create visual representations of guitar chord shapes"""
    
    def __init__(self):
        self.fret_count = 5  # Default frets to show
        self.string_count = 6  # Standard guitar
        self.fret_width = 60
        self.fret_height = 40
        self.margin = 30
        
    def parse_chord_notation(self, chord_string):
        """
        Parse chord notation like 'x32010' or '3-2-0-0-1-0'
        Returns list of fret positions for each string (high E to low E)
        """
        # Remove spaces and convert common separators
        chord_string = chord_string.strip().replace('-', '').replace(' ', '')
        
        # Handle 'x' for muted strings
        fret_positions = []
        for char in chord_string:
            if char.lower() == 'x':
                fret_positions.append(-1)  # -1 represents muted
            elif char.isdigit():
                fret_positions.append(int(char))
            else:
                fret_positions.append(0)  # Default to open
                
        # Ensure we have 6 positions (pad with 0s if needed)
        while len(fret_positions) < 6:
            fret_positions.append(0)
            
        return fret_positions[:6]  # Only take first 6
    
    def create_chord_diagram(self, chord_name, fret_positions, save_path=None):
        """
        Create a chord diagram visualization
        fret_positions: list of 6 integers representing fret positions for each string
                       -1 = muted, 0 = open, 1+ = fret number
        """
        fig, ax = plt.subplots(1, 1, figsize=(4, 5))
        
        # Determine fret range to display
        active_frets = [f for f in fret_positions if f > 0]
        if active_frets:
            min_fret = max(1, min(active_frets) - 1)
            max_fret = min_fret + self.fret_count
        else:
            min_fret = 1
            max_fret = self.fret_count + 1
        
        # Draw fretboard
        self._draw_fretboard(ax, min_fret, max_fret)
        
        # Draw string markers and finger positions
        self._draw_chord_positions(ax, fret_positions, min_fret)
        
        # Add title
        ax.set_title(f'{chord_name}', fontsize=16, fontweight='bold', pad=20)
        
        # Remove axes
        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(-1, self.fret_count + 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            return save_path
        else:
            # Return as base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            return image_base64
    
    def _draw_fretboard(self, ax, min_fret, max_fret):
        """Draw the fretboard grid"""
        # Draw frets (horizontal lines)
        for fret in range(self.fret_count + 1):
            line_width = 3 if fret == 0 else 1  # Nut is thicker
            ax.axhline(y=fret, color='black', linewidth=line_width, xmin=0, xmax=1)
        
        # Draw strings (vertical lines)
        for string in range(6):
            ax.axvline(x=string, color='black', linewidth=1)
        
        # Add fret numbers if not starting from 1st fret
        if min_fret > 1:
            ax.text(-0.8, self.fret_count/2, f'{min_fret}fr', 
                   rotation=90, va='center', ha='center', fontsize=10)
    
    def _draw_chord_positions(self, ax, fret_positions, min_fret):
        """Draw finger positions and open/muted string indicators"""
        for string_idx, fret_pos in enumerate(fret_positions):
            if fret_pos == -1:  # Muted string
                ax.text(string_idx, -0.5, 'X', ha='center', va='center', 
                       fontsize=14, fontweight='bold', color='red')
            elif fret_pos == 0:  # Open string
                circle = Circle((string_idx, -0.5), 0.15, 
                              fill=False, color='black', linewidth=2)
                ax.add_patch(circle)
            else:  # Fretted note
                # Calculate position relative to displayed frets
                relative_fret = fret_pos - min_fret + 1
                if 0 <= relative_fret <= self.fret_count:
                    circle = Circle((string_idx, relative_fret - 0.5), 0.2, 
                                  fill=True, color='black')
                    ax.add_patch(circle)
                    # Add fret number inside circle
                    ax.text(string_idx, relative_fret - 0.5, str(fret_pos), 
                           ha='center', va='center', color='white', 
                           fontsize=8, fontweight='bold')

class MusicWebScraper:
    """Enhanced web scraper with chord visualization capabilities"""
    
    def __init__(self, output_dir="music_rag_data"):
        self.output_dir = output_dir
        self.chord_visualizer = ChordVisualizer()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'chord_diagrams'), exist_ok=True)
        
        # Common chord patterns database
        self.common_chords = {
            'C': '032010',
            'G': '320003',
            'Am': '002210',
            'F': '133211',
            'D': 'xx0232',
            'Em': '022000',
            'A': 'x02220',
            'E': '022100',
            'Dm': 'xx0231',
            'B7': 'x21202',
            'C7': '032310',
            'G7': '320001'
        }
    
    def extract_chord_from_text(self, text):
        """Extract chord information from text content"""
        chords_found = []
        
        # Pattern to match chord names with optional notation
        chord_pattern = r'\b([A-G][#b]?(?:maj|min|m|M|dim|aug|sus[24]?|add[0-9]|[0-9]+)?)\s*:?\s*([x0-9\-\s]{6,})?'
        
        matches = re.finditer(chord_pattern, text, re.IGNORECASE)
        
        for match in matches:
            chord_name = match.group(1)
            fret_notation = match.group(2)
            
            if fret_notation:
                # Clean up the notation
                fret_notation = re.sub(r'[^\dx\-]', '', fret_notation.strip())
                if len(fret_notation) >= 6:
                    chords_found.append({
                        'name': chord_name,
                        'notation': fret_notation[:6],
                        'source': 'extracted'
                    })
            elif chord_name.upper() in [c.upper() for c in self.common_chords.keys()]:
                # Use common chord pattern
                matching_chord = next(c for c in self.common_chords.keys() 
                                    if c.upper() == chord_name.upper())
                chords_found.append({
                    'name': chord_name,
                    'notation': self.common_chords[matching_chord],
                    'source': 'database'
                })
        
        return chords_found
    

    
    def create_chord_visuals(self, chords_data):
        """Create visual diagrams for extracted chords"""
        visual_data = []
        
        for chord in chords_data:
            try:
                chord_name = chord['name']
                notation = chord['notation']
                
                # Try remote diagram first
                diagram_path = fetch_scales_chords_diagram(
                chord_name,
                instrument="guitar",
                output="image",
                size="100px",
                save_dir=Path(self.output_dir) / "chord_diagrams"
                )

                if not diagram_path:
                
                    fret_positions = self.chord_visualizer.parse_chord_notation(notation)
                    diagram_path = os.path.join(
                    self.output_dir, 'chord_diagrams', 
                    f"{chord_name.replace('/', '_')}.png"
                    )
                    self.chord_visualizer.create_chord_diagram(
                    chord_name, fret_positions, diagram_path
                    )

                
                visual_data.append({
                    'chord_name': chord_name,
                    'notation': notation,
                    'fret_positions': fret_positions,
                    'diagram_path': diagram_path,
                    'source': chord['source']
                })
                
            except Exception as e:
                print(f"Error creating visual for chord {chord.get('name', 'unknown')}: {e}")
        
        return visual_data
    
    def scrape_chord_websites(self):
        """Scrape websites for chord information"""
        chord_websites = [
            'https://www.guitar-chords.org.uk/',
            'https://www.justinguitar.com/categories/guitar-chord-library',
            'https://www.chordie.com/chord.pere/www.guitaretab.com/j/jeremy-riddle/345366.html',
            'https://www.fender.com/articles/play/guitar-chord-library'
        ]
        
        all_chords = []
        
        for url in chord_websites:
            try:
                print(f"Scraping chords from: {url}")
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract text content
                text_content = soup.get_text()
                
                # Extract chord information
                chords = self.extract_chord_from_text(text_content)
                all_chords.extend(chords)
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
        
        return all_chords
    
    def process_ultimate_guitar_tabs(self, search_terms=None):
        """Enhanced Ultimate Guitar scraping with chord extraction"""
        if search_terms is None:
            search_terms = ['beginner chords', 'basic guitar chords', 'chord charts']
        
        tab_data = []
        
        for term in search_terms:
            try:
                # This is a simplified example - Ultimate Guitar has anti-scraping measures
                search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={term}"
                
                response = self.session.get(search_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract chord information from the page
                text_content = soup.get_text()
                chords = self.extract_chord_from_text(text_content)
                
                if chords:
                    tab_data.append({
                        'search_term': term,
                        'chords': chords,
                        'url': search_url
                    })
                
                time.sleep(2)  # Be respectful with rate limiting
                
            except Exception as e:
                print(f"Error processing Ultimate Guitar search for '{term}': {e}")
        
        return tab_data
    
    def save_enhanced_data(self, data, filename):
        """Save data with chord visuals to JSON"""
        output_path = os.path.join(self.output_dir, filename)
        
        # Convert any non-serializable data
        serializable_data = []
        for item in data:
            if isinstance(item, dict):
                # Convert numpy arrays to lists
                clean_item = {}
                for key, value in item.items():
                    if isinstance(value, np.ndarray):
                        clean_item[key] = value.tolist()
                    else:
                        clean_item[key] = value
                serializable_data.append(clean_item)
            else:
                serializable_data.append(item)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        print(f"Saved enhanced data to {output_path}")
    
    def run_enhanced_scraping(self):
        """Main method to run enhanced scraping with chord visualization"""
        print("Starting enhanced music scraping with chord visualization...")
        
        # 1. Scrape chord websites
        print("\n1. Scraping chord websites...")
        web_chords = self.scrape_chord_websites()
        
        # 2. Add common chords from database
        print("\n2. Adding common chord database...")
        db_chords = []
        for name, notation in self.common_chords.items():
            db_chords.append({
                'name': name,
                'notation': notation,
                'source': 'database'
            })
        
        # 3. Combine all chord data
        all_chords = web_chords + db_chords
        
        # 4. Create visual diagrams
        print(f"\n3. Creating visual diagrams for {len(all_chords)} chords...")
        chord_visuals = self.create_chord_visuals(all_chords)
        
        # 5. Process Ultimate Guitar (optional)
        print("\n4. Processing Ultimate Guitar tabs...")
        ug_data = self.process_ultimate_guitar_tabs()
        
        # 6. Save all data
        print("\n5. Saving enhanced dataset...")
        
        enhanced_dataset = {
            'chord_visuals': chord_visuals,
            'web_scraped_chords': web_chords,
            'database_chords': db_chords,
            'ultimate_guitar_data': ug_data,
            'total_chords': len(all_chords),
            'diagrams_created': len(chord_visuals)
        }
        
        self.save_enhanced_data([enhanced_dataset], 'enhanced_chord_dataset.json')
        
        # Save chord visuals separately for easy access
        self.save_enhanced_data(chord_visuals, 'chord_visual_library.json')
        
        print(f"\n✅ Enhanced scraping complete!")
        print(f"   - Total chords processed: {len(all_chords)}")
        print(f"   - Visual diagrams created: {len(chord_visuals)}")
        print(f"   - Chord diagrams saved to: {os.path.join(self.output_dir, 'chord_diagrams')}")
        
        return enhanced_dataset
    

def main():
    """Example usage"""
    scraper = MusicWebScraper()
    
    # Run enhanced scraping
    results = scraper.run_enhanced_scraping()
    
    # Example: Create a specific chord diagram
    print("\nCreating example chord diagram...")
    chord_viz = ChordVisualizer()
    
    # Create a C major chord diagram
    c_major_frets = chord_viz.parse_chord_notation('032010')
    chord_viz.create_chord_diagram('C Major', c_major_frets, 
                                 'example_c_major.png')
    print("Created example_c_major.png")

if __name__ == "__main__":
    main()