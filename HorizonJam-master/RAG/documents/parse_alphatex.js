#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Simple AlphaTex parser for extracting musical information
 * This is a basic implementation - for full AlphaTab functionality,
 * you would need the official @alphatab/alphatab package
 */

function parseAlphaTex(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        const fileName = path.basename(filePath, path.extname(filePath));
        
        // Parse basic AlphaTex structure
        const lines = content.split('\n').filter(line => line.trim());
        const result = {
            title: fileName,
            sections: [],
            metadata: {}
        };
        
        let currentSection = null;
        let measureNumber = 1;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Skip empty lines and comments
            if (!line || line.startsWith('//')) continue;
            
            // Parse metadata (title, artist, etc.)
            if (line.startsWith('\\title')) {
                result.title = line.replace('\\title', '').trim().replace(/"/g, '');
                continue;
            }
            
            if (line.startsWith('\\artist')) {
                result.metadata.artist = line.replace('\\artist', '').trim().replace(/"/g, '');
                continue;
            }
            
            if (line.startsWith('\\album')) {
                result.metadata.album = line.replace('\\album', '').trim().replace(/"/g, '');
                continue;
            }
            
            if (line.startsWith('\\tempo')) {
                result.metadata.tempo = parseInt(line.replace('\\tempo', '').trim());
                continue;
            }
            
            // Parse track/section headers
            if (line.startsWith('\\track') || line.startsWith('.')) {
                if (currentSection) {
                    result.sections.push(currentSection);
                }
                
                currentSection = {
                    name: line.startsWith('\\track') ? line.replace('\\track', '').trim().replace(/"/g, '') : 'Section',
                    measures: [],
                    instrument: 'guitar'
                };
                measureNumber = 1;
                continue;
            }
            
            // Parse musical content (simplified)
            if (currentSection && (line.includes('.') || line.match(/[\d\-\+]/))) {
                // This is likely a measure with notes
                const measure = {
                    number: measureNumber++,
                    content: line,
                    notes: parseNotes(line),
                    chords: parseChords(line)
                };
                
                currentSection.measures.push(measure);
            }
        }
        
        // Add the last section
        if (currentSection) {
            result.sections.push(currentSection);
        }
        
        return [result]; // Return as array to match expected format
        
    } catch (error) {
        console.error(`Error parsing AlphaTex file: ${error.message}`);
        return [];
    }
}

function parseNotes(line) {
    // Extract fret numbers and note positions
    // This is a simplified parser - real AlphaTex is more complex
    const notes = [];
    const notePattern = /(\d+)\.(\d+)/g;
    let match;
    
    while ((match = notePattern.exec(line)) !== null) {
        notes.push({
            string: parseInt(match[1]),
            fret: parseInt(match[2])
        });
    }
    
    return notes;
}

function parseChords(line) {
    // Extract chord symbols (simplified)
    const chordPattern = /\b([A-G][#b]?(?:maj|min|dim|aug|sus|add)?\d*)\b/g;
    const chords = [];
    let match;
    
    while ((match = chordPattern.exec(line)) !== null) {
        chords.push(match[1]);
    }
    
    return chords;
}

// Main execution
if (require.main === module) {
    const filePath = process.argv[2];
    
    if (!filePath) {
        console.error('Usage: node parse_alphatex.js <file.atx>');
        process.exit(1);
    }
    
    if (!fs.existsSync(filePath)) {
        console.error(`File not found: ${filePath}`);
        process.exit(1);
    }
    
    const result = parseAlphaTex(filePath);
    console.log(JSON.stringify(result, null, 2));
}

module.exports = { parseAlphaTex };