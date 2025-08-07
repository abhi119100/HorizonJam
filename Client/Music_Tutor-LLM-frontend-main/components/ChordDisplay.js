import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';
import { formatDuration, getChordColor } from '../utils/helpers';

const ChordDisplay = ({ chordData, onChordPress = null }) => {
  if (!chordData || !chordData.chords || chordData.chords.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.noDataText}>
          No chord data available. Record some audio to see chord analysis.
        </Text>
      </View>
    );
  }

  const { chords, key, confidence, tempo, timeSignature } = chordData;

  const renderChordItem = (chord, index) => {
    const chordColor = getChordColor(chord.name);
    
    return (
      <TouchableOpacity
        key={index}
        style={[
          styles.chordItem,
          { backgroundColor: chordColor },
          onChordPress && styles.pressableChord
        ]}
        onPress={() => onChordPress && onChordPress(chord)}
        activeOpacity={onChordPress ? 0.7 : 1}
      >
        <Text style={styles.chordName}>{chord.name}</Text>
        <Text style={styles.chordConfidence}>{chord.confidence}%</Text>
        {chord.timestamp !== undefined && (
          <Text style={styles.chordTime}>
            {formatDuration(chord.timestamp * 1000)}
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  const renderProgressionView = () => {
    return (
      <View style={styles.progressionContainer}>
        <Text style={styles.sectionTitle}>Chord Progression</Text>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.progressionScroll}
        >
          <View style={styles.progressionRow}>
            {chords.map((chord, index) => renderChordItem(chord, index))}
          </View>
        </ScrollView>
      </View>
    );
  };

  const renderKeyInfo = () => {
    return (
      <View style={styles.keyInfoContainer}>
        <Text style={styles.sectionTitle}>Key Analysis</Text>
        <View style={styles.keyDetails}>
          <View style={styles.keyItem}>
            <Text style={styles.keyLabel}>Detected Key:</Text>
            <Text style={styles.keyValue}>{key}</Text>
          </View>
          <View style={styles.keyItem}>
            <Text style={styles.keyLabel}>Confidence:</Text>
            <Text style={[
              styles.keyValue,
              { color: confidence > 70 ? COLORS.SUCCESS : confidence > 40 ? COLORS.WARNING : COLORS.ERROR }
            ]}>
              {confidence}%
            </Text>
          </View>
          {tempo && (
            <View style={styles.keyItem}>
              <Text style={styles.keyLabel}>Tempo:</Text>
              <Text style={styles.keyValue}>{Math.round(tempo)} BPM</Text>
            </View>
          )}
          {timeSignature && (
            <View style={styles.keyItem}>
              <Text style={styles.keyLabel}>Time Signature:</Text>
              <Text style={styles.keyValue}>{timeSignature}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  const renderChordGrid = () => {
    return (
      <View style={styles.gridContainer}>
        <Text style={styles.sectionTitle}>Detected Chords</Text>
        <View style={styles.chordGrid}>
          {chords.map((chord, index) => renderChordItem(chord, index))}
        </View>
      </View>
    );
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {renderKeyInfo()}
      {renderProgressionView()}
      {renderChordGrid()}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
  noDataText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    padding: SPACING.XL,
    fontStyle: 'italic',
  },
  sectionTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
  },
  keyInfoContainer: {
    backgroundColor: COLORS.SURFACE,
    margin: SPACING.MD,
    padding: SPACING.LG,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  keyDetails: {
    gap: SPACING.SM,
  },
  keyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.XS,
  },
  keyLabel: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: '500',
  },
  keyValue: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: 'bold',
  },
  progressionContainer: {
    backgroundColor: COLORS.SURFACE,
    margin: SPACING.MD,
    padding: SPACING.LG,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  progressionScroll: {
    maxHeight: 100,
  },
  progressionRow: {
    flexDirection: 'row',
    gap: SPACING.SM,
    paddingVertical: SPACING.SM,
  },
  gridContainer: {
    backgroundColor: COLORS.SURFACE,
    margin: SPACING.MD,
    padding: SPACING.LG,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  chordGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.SM,
    justifyContent: 'flex-start',
  },
  chordItem: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 80,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
  pressableChord: {
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  chordName: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.XS,
  },
  chordConfidence: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: '500',
  },
  chordTime: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_SECONDARY,
    marginTop: SPACING.XS,
    fontFamily: 'monospace',
  },
});

export default ChordDisplay;