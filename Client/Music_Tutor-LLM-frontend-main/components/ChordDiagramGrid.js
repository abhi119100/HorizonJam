import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from 'react-native';
import GuitarChord from './GuitarChord';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';

const ChordDiagramGrid = ({ 
  chords = ['E', 'Am', 'Am', 'G'], 
  onChordPress = null,
  selectedChord = null 
}) => {
  
  const chordPositions = [
    { name: 'E', row: 0, col: 0 },
    { name: 'Am', row: 0, col: 1 },
    { name: 'Am', row: 1, col: 0 },
    { name: 'G', row: 1, col: 1 },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ChordDram</Text>
      <View style={styles.grid}>
        {chordPositions.map((chord, index) => (
          <View key={index} style={styles.chordPosition}>
            <GuitarChord 
              chordName={chord.name}
              size="small"
              onPress={() => onChordPress && onChordPress(chord.name)}
            />
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: 8,
    padding: SPACING.MD,
  },
  title: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
    textAlign: 'center',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    gap: SPACING.SM,
  },
  chordPosition: {
    width: '45%',
    alignItems: 'center',
  },
});

export default ChordDiagramGrid;