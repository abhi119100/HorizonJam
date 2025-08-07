import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';

const SongStructure = ({ 
  songData = null, 
  onSectionPress = null,
  currentMeasure = 0 
}) => {
  const [selectedSection, setSelectedSection] = useState(null);

  // Default song structure if no data provided
  const defaultStructure = [
    { measure: 1, section: 'Verse', color: COLORS.VERSE },
    { measure: 2, section: 'Chorus', color: COLORS.CHORUS },
    { measure: 3, section: 'Chorus', color: COLORS.VERSE },
    { measure: 4, section: 'Chorus', color: COLORS.CHORUS },
    { measure: 5, section: 'Chorus', color: COLORS.CHORUS },
    { measure: 6, section: '', color: 'transparent' },
    { measure: 7, section: '', color: 'transparent' },
    { measure: 8, section: '', color: 'transparent' },
    { measure: 9, section: '', color: 'transparent' },
  ];

  const structure = songData || defaultStructure;

  const handleSectionPress = (section) => {
    setSelectedSection(section);
    if (onSectionPress) {
      onSectionPress(section);
    }
  };

  const renderMeasureNumbers = () => {
    return (
      <View style={styles.measureNumbers}>
        {Array.from({ length: 9 }, (_, i) => (
          <View key={i + 1} style={styles.measureNumber}>
            <Text style={styles.measureText}>{i + 1}</Text>
          </View>
        ))}
      </View>
    );
  };

  const renderSongGrid = () => {
    const rows = [];
    
    // Create rows for the song structure
    for (let row = 0; row < 5; row++) {
      const rowSections = [];
      
      for (let col = 0; col < 9; col++) {
        const measure = col + 1;
        const section = structure.find(s => s.measure === measure && Math.floor((s.measure - 1) / 9) === row);
        
        if (section && section.section) {
          // Calculate width based on section length
          let width = 1;
          let nextIndex = structure.findIndex(s => s.measure === measure);
          
          // Find consecutive sections of the same type
          while (
            nextIndex + width < structure.length &&
            structure[nextIndex + width] &&
            structure[nextIndex + width].section === section.section &&
            structure[nextIndex + width].measure === measure + width
          ) {
            width++;
          }

          rowSections.push({
            ...section,
            width,
            startMeasure: measure,
            endMeasure: measure + width - 1,
          });
          
          // Skip the measures we've covered
          col += width - 1;
        }
      }
      
      if (rowSections.length > 0) {
        rows.push(
          <View key={row} style={styles.structureRow}>
            {rowSections.map((section, index) => (
              <TouchableOpacity
                key={`${row}-${index}`}
                style={[
                  styles.sectionBlock,
                  {
                    backgroundColor: section.color,
                    width: (section.width * 100) + '%',
                    maxWidth: section.width * 90,
                  },
                  selectedSection?.measure === section.measure && styles.selectedSection,
                ]}
                onPress={() => handleSectionPress(section)}
                activeOpacity={0.8}
              >
                <Text style={styles.sectionText}>{section.section}</Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      }
    }
    
    return rows;
  };

  return (
    <View style={styles.container}>
      {renderMeasureNumbers()}
      <ScrollView 
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.structureGrid}>
          {renderSongGrid()}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
  measureNumbers: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: SPACING.SM,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.PANEL,
  },
  measureNumber: {
    width: 30,
    alignItems: 'center',
  },
  measureText: {
    color: COLORS.TEXT_SECONDARY,
    fontSize: FONT_SIZES.SM,
    fontWeight: 'bold',
  },
  scrollContainer: {
    flex: 1,
  },
  structureGrid: {
    padding: SPACING.MD,
    minHeight: 300,
  },
  structureRow: {
    flexDirection: 'row',
    marginBottom: SPACING.SM,
    height: 50,
    alignItems: 'center',
  },
  sectionBlock: {
    height: 40,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.SM,
    minWidth: 60,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  selectedSection: {
    borderWidth: 2,
    borderColor: COLORS.TEXT_PRIMARY,
  },
  sectionText: {
    color: COLORS.BACKGROUND,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default SongStructure;