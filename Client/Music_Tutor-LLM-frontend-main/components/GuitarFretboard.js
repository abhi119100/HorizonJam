import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';

const GuitarFretboard = ({ 
  chordProgression = ['Em', 'Am', 'D', 'G'],
  onChordPress = null,
  highlightedChord = null 
}) => {
  const [selectedFret, setSelectedFret] = useState(null);

  const stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
  const fretCount = 12;

  const chordPositions = {
    'Em': { frets: [0, 2, 2, 0, 0, 0], color: COLORS.SUCCESS },
    'Am': { frets: [0, 0, 2, 2, 1, 0], color: COLORS.PRIMARY },
    'D': { frets: [-1, -1, 0, 2, 3, 2], color: COLORS.ACCENT },
    'G': { frets: [3, 2, 0, 0, 3, 3], color: COLORS.WARNING },
    'C': { frets: [-1, 3, 2, 0, 1, 0], color: COLORS.SECONDARY },
    'Dm': { frets: [-1, -1, 0, 2, 3, 1], color: COLORS.ERROR },
    'F': { frets: [1, 3, 3, 2, 1, 1], color: '#9C27B0' },
    'A': { frets: [-1, 0, 2, 2, 2, 0], color: '#FF5722' },
  };

  const handleFretPress = (stringIndex, fretIndex) => {
    setSelectedFret({ string: stringIndex, fret: fretIndex });
  };

  const handleChordPress = (chord) => {
    if (onChordPress) {
      onChordPress(chord);
    }
  };

  const renderChordProgression = () => {
    return (
      <View style={styles.chordProgressionContainer}>
        {chordProgression.map((chord, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.chordProgressionItem,
              { backgroundColor: chordPositions[chord]?.color || COLORS.PANEL },
              highlightedChord === chord && styles.highlightedChord,
            ]}
            onPress={() => handleChordPress(chord)}
          >
            <Text style={styles.chordProgressionText}>{chord}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderFretboard = () => {
    return (
      <View style={styles.fretboardContainer}>
        {/* String names */}
        <View style={styles.stringNamesContainer}>
          {stringNames.map((name, index) => (
            <Text key={index} style={styles.stringName}>
              {name}
            </Text>
          ))}
        </View>

        {/* Fretboard */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.fretboard}>
            {/* Fret markers */}
            <View style={styles.fretMarkers}>
              {Array.from({ length: fretCount + 1 }).map((_, fretIndex) => (
                <View key={fretIndex} style={styles.fretMarker}>
                  {(fretIndex === 3 || fretIndex === 5 || fretIndex === 7 || fretIndex === 9) && (
                    <View style={styles.fretDot} />
                  )}
                  {fretIndex === 12 && (
                    <View style={styles.doubleFretDot}>
                      <View style={styles.fretDot} />
                      <View style={styles.fretDot} />
                    </View>
                  )}
                </View>
              ))}
            </View>

            {/* Strings and frets */}
            {stringNames.map((_, stringIndex) => (
              <View key={stringIndex} style={styles.stringRow}>
                {/* String line */}
                <View style={styles.stringLine} />
                
                {/* Fret positions */}
                {Array.from({ length: fretCount + 1 }).map((_, fretIndex) => {
                  const isPressed = selectedFret?.string === stringIndex && selectedFret?.fret === fretIndex;
                  
                  // Check if this position is part of any chord in progression
                  let chordColor = null;
                  chordProgression.forEach(chord => {
                    const chordData = chordPositions[chord];
                    if (chordData && chordData.frets[stringIndex] === fretIndex) {
                      chordColor = chordData.color;
                    }
                  });

                  return (
                    <TouchableOpacity
                      key={fretIndex}
                      style={[
                        styles.fretPosition,
                        isPressed && styles.pressedFret,
                      ]}
                      onPress={() => handleFretPress(stringIndex, fretIndex)}
                    >
                      {(chordColor || isPressed) && (
                        <View
                          style={[
                            styles.fingerDot,
                            { backgroundColor: chordColor || COLORS.TEXT_PRIMARY },
                          ]}
                        />
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            ))}

            {/* Fret lines */}
            {Array.from({ length: fretCount + 1 }).map((_, fretIndex) => (
              <View
                key={fretIndex}
                style={[
                  styles.fretLine,
                  fretIndex === 0 && styles.nutLine,
                  { left: fretIndex * 50 },
                ]}
              />
            ))}
          </View>
        </ScrollView>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {renderChordProgression()}
      {renderFretboard()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'transparent',
    borderRadius: 8,
    padding: SPACING.MD,
    flex: 1,
  },
  chordProgressionContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SPACING.MD,
    paddingVertical: SPACING.SM,
  },
  chordProgressionItem: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    borderRadius: 6,
    minWidth: 40,
    alignItems: 'center',
  },
  highlightedChord: {
    borderWidth: 2,
    borderColor: COLORS.TEXT_PRIMARY,
  },
  chordProgressionText: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  fretboardContainer: {
    backgroundColor: COLORS.FRETBOARD,
    borderRadius: 8,
    padding: SPACING.SM,
    flex: 1,
    minHeight: 200,
  },
  stringNamesContainer: {
    paddingLeft: 20,
    marginBottom: SPACING.SM,
  },
  stringName: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.SM,
    fontWeight: 'bold',
    height: 25,
    textAlignVertical: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  fretboard: {
    position: 'relative',
    height: 150,
    minWidth: 600,
  },
  fretMarkers: {
    flexDirection: 'row',
    position: 'absolute',
    top: -20,
    left: 0,
    right: 0,
    height: 15,
  },
  fretMarker: {
    width: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fretDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.TEXT_SECONDARY,
  },
  doubleFretDot: {
    alignItems: 'center',
    gap: 2,
  },
  stringRow: {
    position: 'relative',
    height: 25,
    flexDirection: 'row',
  },
  stringLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 12,
    height: 2,
    backgroundColor: COLORS.TEXT_PRIMARY,
    opacity: 0.8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 1,
  },
  fretPosition: {
    width: 50,
    height: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fingerDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 2,
  },
  pressedFret: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  fretLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 2,
    backgroundColor: COLORS.TEXT_SECONDARY,
    opacity: 0.7,
  },
  nutLine: {
    width: 4,
    backgroundColor: COLORS.TEXT_PRIMARY,
  },
});

export default GuitarFretboard;