import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { apiService } from '../services/apiService';
import ChordDisplay from '../components/ChordDisplay';
import AudioUploader from '../components/AudioUploader';
import PlayerControls from '../components/PlayerControls';
import { COLORS, SPACING, FONT_SIZES, SCREEN_NAMES } from '../utils/constants';
import { getGuidance } from '../services/apiService';
import { showErrorAlert } from '../utils/helpers';

const ChordAnalysisScreen = () => {
  const navigation = useNavigation();
  const [chordData, setChordData] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [selectedChord, setSelectedChord] = useState(null);
  const [isGettingGuidance, setIsGettingGuidance] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasAnalysis, setHasAnalysis] = useState(false);

  const handleAudioUpload = async (audioUri) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiService.uploadAudio(audioUri, 0.7, 0.5);
      setChordData(result);
      setAudioFile({ uri: audioUri });
      setHasAnalysis(true);
    } catch (err) {
      setError('Failed to analyze audio. Please try again.');
      console.error('Audio analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Set up navigation header with actions only if we have analysis
    if (hasAnalysis && navigation.setOptions) {
      navigation.setOptions({
        headerRight: () => (
          <TouchableOpacity
            style={styles.headerButton}
            onPress={handleGetGuidance}
          >
            <Text style={styles.headerButtonText}>Get Guidance</Text>
          </TouchableOpacity>
        ),
      });
    }
  }, [navigation, chordData, hasAnalysis]);

  const handleChordPress = (chord) => {
    setSelectedChord(chord);
    
    Alert.alert(
      `Chord: ${chord.name}`,
      `Confidence: ${chord.confidence}%\n${chord.timestamp ? `Time: ${formatDuration(chord.timestamp * 1000)}` : ''}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Learn About This Chord', 
          onPress: () => handleChordGuidance(chord) 
        },
      ]
    );
  };

  const handleChordGuidance = async (chord) => {
    setIsGettingGuidance(true);
    
    try {
      const guidanceQuery = {
        question: `Tell me about the ${chord.name} chord. How is it constructed, what are its uses in music, and any tips for playing it?`,
        context: {
          detectedChord: chord.name,
          confidence: chord.confidence,
          key: chordData?.key,
          allChords: chordData?.chords?.map(c => c.name),
        },
      };

      const guidanceResult = await getGuidance(guidanceQuery);

      navigation.navigate('Guidance', {
        guidanceText: guidanceResult.guidance,
        audioUrl: guidanceResult.audioUrl,
        chordData: chordData,
        focusChord: chord,
      });
    } catch (error) {
      console.error('Error getting chord guidance:', error);
      showErrorAlert(
        'Guidance Error',
        'Failed to get guidance about this chord. Please try again.'
      );
    } finally {
      setIsGettingGuidance(false);
    }
  };

  const handleGetGuidance = async () => {
    if (!chordData) {
      showErrorAlert('No Data', 'No chord analysis data available for guidance.');
      return;
    }

    setIsGettingGuidance(true);

    try {
      const guidanceQuery = {
        question: 'Analyze my chord progression and provide musical insights and improvement suggestions.',
        context: {
          chords: chordData.chords?.map(c => c.name) || [],
          key: chordData.key,
          confidence: chordData.confidence,
          tempo: chordData.tempo,
          timeSignature: chordData.timeSignature,
        },
      };

      const guidanceResult = await getGuidance(guidanceQuery);

      navigation.navigate('Guidance', {
        guidanceText: guidanceResult.guidance,
        audioUrl: guidanceResult.audioUrl,
        chordData: chordData,
      });
    } catch (error) {
      console.error('Error getting guidance:', error);
      showErrorAlert(
        'Guidance Error',
        'Failed to get musical guidance. Please check your connection and try again.'
      );
    } finally {
      setIsGettingGuidance(false);
    }
  };

  const renderAnalysisSummary = () => {
    if (!chordData) return null;

    const { chords, key, confidence } = chordData;
    const uniqueChords = [...new Set(chords?.map(c => c.name) || [])];

    return (
      <View style={styles.summaryContainer}>
        <Text style={styles.summaryTitle}>Analysis Summary</Text>
        
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Detected Key:</Text>
          <Text style={styles.summaryValue}>{key || 'Unknown'}</Text>
        </View>
        
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Key Confidence:</Text>
          <Text style={[
            styles.summaryValue,
            { color: confidence > 70 ? COLORS.SUCCESS : confidence > 40 ? COLORS.WARNING : COLORS.ERROR }
          ]}>
            {confidence}%
          </Text>
        </View>
        
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Chords:</Text>
          <Text style={styles.summaryValue}>{chords?.length || 0}</Text>
        </View>
        
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Unique Chords:</Text>
          <Text style={styles.summaryValue}>{uniqueChords.length}</Text>
        </View>

        {uniqueChords.length > 0 && (
          <View style={styles.chordsPreview}>
            <Text style={styles.summaryLabel}>Chord Types:</Text>
            <Text style={styles.chordsPreviewText}>
              {uniqueChords.slice(0, 6).join(', ')}
              {uniqueChords.length > 6 && '...'}
            </Text>
          </View>
        )}
      </View>
    );
  };

  const renderActionButtons = () => {
    return (
      <View style={styles.actionButtonsContainer}>
        <TouchableOpacity
          style={[styles.actionButton, styles.primaryActionButton]}
          onPress={handleGetGuidance}
          disabled={isGettingGuidance}
        >
          <Text style={styles.actionButtonText}>
            {isGettingGuidance ? 'Getting Guidance...' : 'Get Musical Guidance'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.secondaryActionButton]}
          onPress={() => navigation.navigate('Home')}
        >
          <Text style={styles.actionButtonText}>Record New Audio</Text>
        </TouchableOpacity>
      </View>
    );
  };

  if (!hasAnalysis) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Chord Analysis</Text>
          <Text style={styles.subtitle}>Upload an audio file to analyze chords</Text>
        </View>
        
        <View style={styles.uploadSection}>
          <AudioUploader onAudioReady={handleAudioUpload} />
        </View>
        
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.PRIMARY} />
            <Text style={styles.loadingText}>Analyzing audio...</Text>
          </View>
        )}
        
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        {renderAnalysisSummary()}

        <ChordDisplay 
          chordData={chordData}
          onChordPress={handleChordPress}
        />

        {audioFile && (
          <PlayerControls 
            localAudioUri={audioFile.uri}
            onPlaybackStatusChange={(status) => {
              // Handle playback status if needed
              console.log('Playback status:', status);
            }}
          />
        )}

        {renderActionButtons()}
      </ScrollView>
    </SafeAreaView>
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
  headerButton: {
    marginRight: SPACING.MD,
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    backgroundColor: COLORS.ACCENT,
    borderRadius: 6,
  },
  headerButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.SM,
    fontWeight: 'bold',
  },
  summaryContainer: {
    backgroundColor: COLORS.SURFACE,
    margin: SPACING.MD,
    padding: SPACING.LG,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.PANEL,
  },
  summaryTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
    textAlign: 'center',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.XS,
    marginBottom: SPACING.SM,
  },
  summaryLabel: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: '500',
  },
  summaryValue: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: 'bold',
  },
  chordsPreview: {
    marginTop: SPACING.SM,
    paddingTop: SPACING.SM,
    borderTopWidth: 1,
    borderTopColor: COLORS.BACKGROUND,
  },
  chordsPreviewText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    marginTop: SPACING.XS,
    flexWrap: 'wrap',
  },
  actionButtonsContainer: {
    margin: SPACING.MD,
    gap: SPACING.MD,
  },
  actionButton: {
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryActionButton: {
    backgroundColor: COLORS.PRIMARY,
  },
  secondaryActionButton: {
    backgroundColor: COLORS.SECONDARY,
  },
  actionButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  header: {
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.PANEL,
  },
  title: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.XS,
  },
  subtitle: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
  },
  uploadSection: {
    padding: SPACING.LG,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: SPACING.MD,
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
  },
  errorContainer: {
    margin: SPACING.LG,
    padding: SPACING.MD,
    backgroundColor: COLORS.ERROR + '20',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.ERROR,
  },
  errorText: {
    color: COLORS.ERROR,
    fontSize: FONT_SIZES.MD,
    textAlign: 'center',
  },
  noDataContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.XL,
  },
  noDataTitle: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
  },
  noDataText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.XL,
  },
  backButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 8,
  },
  backButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
});

export default ChordAnalysisScreen;