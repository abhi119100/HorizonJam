import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';

const GuidanceText = ({ 
  guidanceText, 
  isLoading = false, 
  onRequestGuidance = null,
  showRequestButton = true 
}) => {
  const [expandedSections, setExpandedSections] = useState(new Set());

  const toggleSection = (sectionIndex) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionIndex)) {
      newExpanded.delete(sectionIndex);
    } else {
      newExpanded.add(sectionIndex);
    }
    setExpandedSections(newExpanded);
  };

  const formatGuidanceText = (text) => {
    if (!text) return [];

    // Split text into sections based on common patterns
    const sections = [];
    const lines = text.split('\n').filter(line => line.trim());
    
    let currentSection = { title: '', content: [] };
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Check if line looks like a header (starts with number, bullet, or is in caps)
      const isHeader = /^\d+\./.test(trimmedLine) || 
                      /^[A-Z\s]{3,}:/.test(trimmedLine) ||
                      /^[•\-\*]/.test(trimmedLine);
      
      if (isHeader && currentSection.content.length > 0) {
        sections.push({ ...currentSection });
        currentSection = { title: trimmedLine, content: [] };
      } else if (isHeader) {
        currentSection.title = trimmedLine;
      } else {
        currentSection.content.push(trimmedLine);
      }
    });
    
    if (currentSection.title || currentSection.content.length > 0) {
      sections.push(currentSection);
    }
    
    return sections.length > 0 ? sections : [{ title: 'Music Guidance', content: [text] }];
  };

  const renderSection = (section, index) => {
    const isExpanded = expandedSections.has(index);
    const hasContent = section.content && section.content.length > 0;
    
    return (
      <View key={index} style={styles.sectionContainer}>
        {section.title && (
          <TouchableOpacity
            style={styles.sectionHeader}
            onPress={() => hasContent && toggleSection(index)}
            activeOpacity={hasContent ? 0.7 : 1}
          >
            <Text style={styles.sectionTitle}>
              {section.title}
            </Text>
            {hasContent && (
              <Text style={styles.expandIcon}>
                {isExpanded ? '−' : '+'}
              </Text>
            )}
          </TouchableOpacity>
        )}
        
        {(!section.title || isExpanded) && hasContent && (
          <View style={styles.sectionContent}>
            {section.content.map((paragraph, pIndex) => (
              <Text key={pIndex} style={styles.paragraph}>
                {paragraph}
              </Text>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderLoadingState = () => (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={COLORS.PRIMARY} />
      <Text style={styles.loadingText}>
        Generating personalized music guidance...
      </Text>
    </View>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>No Guidance Available</Text>
      <Text style={styles.emptyText}>
        Upload some audio or ask a music-related question to get personalized guidance from your AI music tutor.
      </Text>
      {showRequestButton && onRequestGuidance && (
        <TouchableOpacity
          style={styles.requestButton}
          onPress={onRequestGuidance}
        >
          <Text style={styles.requestButtonText}>
            Ask for Guidance
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        {renderLoadingState()}
      </View>
    );
  }

  if (!guidanceText || guidanceText.trim() === '') {
    return (
      <View style={styles.container}>
        {renderEmptyState()}
      </View>
    );
  }

  const sections = formatGuidanceText(guidanceText);

  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.headerContainer}>
          <Text style={styles.mainTitle}>Music Guidance</Text>
          <Text style={styles.subtitle}>
            Personalized tips and insights from your AI music tutor
          </Text>
        </View>
        
        {sections.map((section, index) => renderSection(section, index))}
        
        {showRequestButton && onRequestGuidance && (
          <TouchableOpacity
            style={styles.moreGuidanceButton}
            onPress={onRequestGuidance}
          >
            <Text style={styles.moreGuidanceButtonText}>
              Ask Another Question
            </Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
  scrollContainer: {
    flex: 1,
  },
  headerContainer: {
    backgroundColor: COLORS.PRIMARY,
    padding: SPACING.LG,
    marginBottom: SPACING.MD,
  },
  mainTitle: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.SURFACE,
    marginBottom: SPACING.XS,
  },
  subtitle: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.SURFACE,
    opacity: 0.9,
  },
  sectionContainer: {
    backgroundColor: COLORS.SURFACE,
    marginHorizontal: SPACING.MD,
    marginBottom: SPACING.MD,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.LG,
    backgroundColor: COLORS.SURFACE,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.BACKGROUND,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    flex: 1,
    marginRight: SPACING.MD,
  },
  expandIcon: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.PRIMARY,
    width: 20,
    textAlign: 'center',
  },
  sectionContent: {
    padding: SPACING.LG,
  },
  paragraph: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    lineHeight: 24,
    marginBottom: SPACING.MD,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.XL,
  },
  loadingText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    marginTop: SPACING.LG,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.XL,
  },
  emptyTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
  },
  emptyText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.XL,
  },
  requestButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 25,
  },
  requestButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  moreGuidanceButton: {
    backgroundColor: COLORS.SECONDARY,
    marginHorizontal: SPACING.LG,
    marginVertical: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 8,
    alignItems: 'center',
  },
  moreGuidanceButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
});

export default GuidanceText;