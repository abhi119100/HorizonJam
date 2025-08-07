import React from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { COLORS, FONT_SIZES, SPACING } from '../utils/constants';

const GuitarChord = ({ 
  chordName = 'Em',
  fretPositions = [0, 2, 2, 0, 0, 0], // Standard Em chord
  onPress = null,
  size = 'medium' // small, medium, large
}) => {
  
  const chordDefinitions = {
    'Em': [0, 2, 2, 0, 0, 0],
    'Am': [0, 0, 2, 2, 1, 0],
    'D': [-1, -1, 0, 2, 3, 2],
    'G': [3, 2, 0, 0, 3, 3],
    'C': [-1, 3, 2, 0, 1, 0],
    'E': [0, 2, 2, 1, 0, 0],
    'A': [-1, 0, 2, 2, 2, 0],
    'Dm': [-1, -1, 0, 2, 3, 1],
    'F': [1, 3, 3, 2, 1, 1],
  };

  const positions = chordDefinitions[chordName] || fretPositions;
  
  const sizeConfig = {
    small: { width: 60, height: 80, dotSize: 8, fontSize: FONT_SIZES.XS },
    medium: { width: 80, height: 100, dotSize: 10, fontSize: FONT_SIZES.SM },
    large: { width: 100, height: 120, dotSize: 12, fontSize: FONT_SIZES.MD },
  };

  const config = sizeConfig[size];

  const renderFretboard = () => {
    const frets = 4;
    const strings = 6;
    
    return (
      <View style={[styles.fretboard, { width: config.width, height: config.height }]}>
        {/* Strings */}
        {Array.from({ length: strings }).map((_, stringIndex) => (
          <View
            key={`string-${stringIndex}`}
            style={[
              styles.string,
              {
                left: (stringIndex * (config.width - 20)) / (strings - 1) + 10,
                height: config.height - 20,
                top: 10,
              }
            ]}
          />
        ))}
        
        {/* Frets */}
        {Array.from({ length: frets + 1 }).map((_, fretIndex) => (
          <View
            key={`fret-${fretIndex}`}
            style={[
              styles.fret,
              fretIndex === 0 && styles.nutFret,
              {
                top: (fretIndex * (config.height - 20)) / frets + 10,
                width: config.width - 20,
                left: 10,
              }
            ]}
          />
        ))}
        
        {/* Finger positions */}
        {positions.map((fret, stringIndex) => {
          if (fret === -1) return null; // Muted string
          
          const x = (stringIndex * (config.width - 20)) / (strings - 1) + 10;
          const y = fret === 0 ? 5 : (fret - 0.5) * ((config.height - 20) / frets) + 10;
          
          return (
            <View
              key={`finger-${stringIndex}`}
              style={[
                styles.fingerPosition,
                fret === 0 ? styles.openString : styles.frettedNote,
                {
                  left: x - config.dotSize / 2,
                  top: y - config.dotSize / 2,
                  width: config.dotSize,
                  height: config.dotSize,
                  borderRadius: config.dotSize / 2,
                }
              ]}
            />
          );
        })}
        
        {/* String labels (muted strings) */}
        {positions.map((fret, stringIndex) => {
          if (fret !== -1) return null;
          
          const x = (stringIndex * (config.width - 20)) / (strings - 1) + 10;
          
          return (
            <Text
              key={`muted-${stringIndex}`}
              style={[
                styles.mutedString,
                {
                  left: x - 6,
                  top: -5,
                  fontSize: config.fontSize,
                }
              ]}
            >
              ×
            </Text>
          );
        })}
      </View>
    );
  };

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      activeOpacity={onPress ? 0.7 : 1}
    >
      <Text style={[styles.chordName, { fontSize: config.fontSize + 2 }]}>
        {chordName}
      </Text>
      {renderFretboard()}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: SPACING.SM,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderRadius: 12,
    margin: SPACING.XS,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  chordName: {
    color: COLORS.TEXT_PRIMARY,
    fontWeight: 'bold',
    marginBottom: SPACING.XS,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  fretboard: {
    position: 'relative',
    backgroundColor: 'rgba(139, 69, 19, 0.8)',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  string: {
    position: 'absolute',
    width: 2,
    backgroundColor: COLORS.TEXT_PRIMARY,
    opacity: 0.8,
    shadowColor: 'rgba(0, 0, 0, 0.5)',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.8,
    shadowRadius: 1,
  },
  fret: {
    position: 'absolute',
    height: 2,
    backgroundColor: COLORS.TEXT_SECONDARY,
    opacity: 0.7,
  },
  nutFret: {
    height: 4,
    backgroundColor: COLORS.TEXT_PRIMARY,
  },
  fingerPosition: {
    position: 'absolute',
  },
  openString: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: COLORS.TEXT_PRIMARY,
  },
  frettedNote: {
    backgroundColor: COLORS.TEXT_PRIMARY,
  },
  mutedString: {
    position: 'absolute',
    color: COLORS.ERROR,
    fontWeight: 'bold',
  },
});

export default GuitarChord;