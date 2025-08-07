import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  SafeAreaView,
} from 'react-native';
import AudioUploader from '../components/AudioUploader';
import SongStructure from '../components/SongStructure';
import GuitarChord from '../components/GuitarChord';
import GuitarFretboard from '../components/GuitarFretboard';
import InstructorPanel from '../components/InstructorPanel';
import { COLORS, SPACING, FONT_SIZES, STATUS_MESSAGES } from '../utils/constants';
import { uploadAudio, healthCheck } from '../services/apiService';
import { showErrorAlert, formatChordData } from '../utils/helpers';

const HomeScreen = ({ navigation }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [serverStatus, setServerStatus] = useState('unknown');
  const [lastUploadResult, setLastUploadResult] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedChord, setSelectedChord] = useState('Em');
  const [currentChordProgression, setCurrentChordProgression] = useState(['Em', 'Am', 'D', 'G']);

  useEffect(() => {
    checkServerHealth();
  }, []);

  const checkServerHealth = async () => {
    try {
      await healthCheck();
      setServerStatus('online');
    } catch (error) {
      console.error('Server health check failed:', error);
      setServerStatus('offline');
    }
  };

  const handleMicrophonePress = () => {
    setIsRecording(!isRecording);
    // Handle actual recording logic here
    console.log('Microphone pressed, recording:', !isRecording);
  };

  const handleChordSelection = (chord) => {
    setSelectedChord(chord);
    console.log('Selected chord:', chord);
  };

  const handleSectionPress = (section) => {
    console.log('Selected section:', section);
  };

  const handleAudioRecorded = async (audioFile) => {
    if (!audioFile) {
      showErrorAlert('No Audio', 'Please record some audio first.');
      return;
    }

    setIsUploading(true);
    
    try {
      console.log('Uploading audio file:', audioFile.name);
      
      const result = await uploadAudio(audioFile);
      
      if (result && result.success) {
        const formattedData = formatChordData(result.data);
        setLastUploadResult(formattedData);
        
        // In tabbed interface, show success message
        Alert.alert(
          'Analysis Complete',
          'Your audio has been analyzed! Switch to the Analysis tab to view results.',
          [{ text: 'OK' }]
        );
      } else {
        throw new Error(result.message || 'Analysis failed');
      }
    } catch (error) {
      console.error('Error uploading audio:', error);
      
      let errorMessage = 'Failed to analyze audio. ';
      
      if (error.message.includes('Network')) {
        errorMessage += 'Please check your internet connection.';
      } else if (error.message.includes('timeout')) {
        errorMessage += 'The request timed out. Please try again.';
      } else {
        errorMessage += error.message || 'Please try again.';
      }
      
      showErrorAlert('Upload Failed', errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const navigateToGuidance = () => {
    navigation.navigate('Guidance', {
      chordData: lastUploadResult,
    });
  };

  const renderServerStatus = () => {
    const statusColor = serverStatus === 'online' ? COLORS.SUCCESS : 
                       serverStatus === 'offline' ? COLORS.ERROR : 
                       COLORS.WARNING;
    
    const statusText = serverStatus === 'online' ? 'Server Online' :
                      serverStatus === 'offline' ? 'Server Offline' :
                      'Checking Server...';

    return (
      <View style={styles.statusContainer}>
        <View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />
        <Text style={styles.statusText}>{statusText}</Text>
        <TouchableOpacity 
          style={styles.refreshButton} 
          onPress={checkServerHealth}
        >
          <Text style={styles.refreshButtonText}>↻</Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderQuickActions = () => {
    return (
      <View style={styles.quickActionsContainer}>
        <Text style={styles.quickActionsTitle}>Quick Actions</Text>
        
        <TouchableOpacity
          style={[styles.quickActionButton, styles.primaryAction]}
          onPress={() => navigation.navigate('Guidance')}
        >
          <Text style={styles.quickActionButtonText}>
            Ask Music Question
          </Text>
        </TouchableOpacity>



        {lastUploadResult && (
          <TouchableOpacity
            style={[styles.quickActionButton, styles.tertiaryAction]}
            onPress={navigateToGuidance}
          >
            <Text style={styles.quickActionButtonText}>
              Get Guidance on Last Analysis
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderWelcomeSection = () => {
    return (
      <View style={styles.welcomeContainer}>
        <Text style={styles.welcomeTitle}>
          Welcome to HorizonJam Music Tutor
        </Text>
        <Text style={styles.welcomeText}>
          Your AI-powered music learning companion. Record your playing, 
          get real-time chord analysis, and receive personalized guidance 
          to improve your musical skills.
        </Text>
      </View>
    );
  };

  const renderFeatures = () => {
    const features = [
      {
        title: '🎵 Chord Analysis',
        description: 'Upload audio to detect chords, key signatures, and progressions'
      },
      {
        title: '🎯 Music Guidance',
        description: 'Get personalized tips and theory explanations from AI tutor'
      },
      {
        title: '🔊 Audio Playback',
        description: 'Listen to text-to-speech guidance and your recordings'
      },
    ];

    return (
      <View style={styles.featuresContainer}>
        <Text style={styles.featuresTitle}>Features</Text>
        {features.map((feature, index) => (
          <View key={index} style={styles.featureItem}>
            <Text style={styles.featureTitle}>{feature.title}</Text>
            <Text style={styles.featureDescription}>{feature.description}</Text>
          </View>
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Glass Morphism Overlay */}
      <View style={styles.glassOverlay} />
      
      {/* Modern Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoIcon}>🎵</Text>
            <Text style={styles.logoText}>HorizonJam</Text>
          </View>
        </View>
        
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>Music Learning Studio</Text>
        </View>
        
        <View style={styles.headerRight}>
          {renderServerStatus()}
        </View>
      </View>

      {/* Main Dashboard Layout */}
      <View style={styles.dashboard}>
        {/* Left Sidebar */}
        <View style={styles.sidebar}>
          <View style={styles.sidebarSection}>
            <Text style={styles.sidebarTitle}>Audio Controls</Text>
            <TouchableOpacity 
              style={[styles.recordButton, isRecording && styles.recordButtonActive]}
              onPress={handleMicrophonePress}
            >
              <Text style={styles.recordIcon}>🎤</Text>
              <Text style={styles.recordText}>{isRecording ? 'Stop Recording' : 'Start Recording'}</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.uploadButton}>
              <Text style={styles.uploadIcon}>📁</Text>
              <Text style={styles.uploadText}>Upload Audio</Text>
            </TouchableOpacity>
            
            {lastUploadResult && (
              <TouchableOpacity style={styles.playbackButton}>
                <Text style={styles.playbackIcon}>▶️</Text>
                <Text style={styles.playbackText}>Play Analysis</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Main Content Area */}
        <ScrollView style={styles.mainArea} showsVerticalScrollIndicator={false}>
          {/* Top Row */}
          <View style={styles.topRow}>
            {/* Instructor Panel */}
            <View style={styles.instructorCard}>
              <View style={styles.glassShine} />
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>AI Instructor</Text>
                <View style={styles.statusDot} />
              </View>
              <View style={styles.instructorContent}>
                <View style={styles.avatarContainer}>
                  <Text style={styles.avatarEmoji}>🎓</Text>
                </View>
                <View style={styles.messageContainer}>
                  <Text style={styles.instructorMessage}>
                    Welcome! Ready to analyze your music? Upload an audio file or record directly.
                  </Text>
                </View>
              </View>
              <View style={styles.instructorActions}>
                <TouchableOpacity 
                  style={[styles.micButton, isRecording && styles.micButtonActive]}
                  onPress={handleMicrophonePress}
                >
                  <Text style={styles.micIcon}>🎤</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Current Chord Display */}
            <View style={styles.chordCard}>
              <View style={styles.glassShine} />
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Current Chord</Text>
              </View>
              <View style={styles.chordDisplay}>
                <Text style={styles.chordName}>{selectedChord}</Text>
                <View style={styles.chordDiagram}>
                  <GuitarChord 
                    chordName={selectedChord}
                    size="medium"
                    onPress={() => console.log('Chord pressed')}
                  />
                </View>
              </View>
            </View>
          </View>

          {/* Middle Row - Music Tutor Workspace */}
           <View style={styles.middleRow}>
             <View style={styles.musicTutorCard}>
               <View style={styles.glassShine} />
               <View style={styles.cardHeader}>
                 <Text style={styles.cardTitle}>Music Tutor & Analysis</Text>
                 <View style={styles.tutorControls}>
                   <TouchableOpacity style={styles.analyzeButton}>
                     <Text style={styles.analyzeButtonText}>🎵 Analyze</Text>
                   </TouchableOpacity>
                   <TouchableOpacity style={styles.chatButton}>
                     <Text style={styles.chatButtonText}>💬 Chat</Text>
                   </TouchableOpacity>
                 </View>
               </View>
               <View style={styles.tutorWorkspace}>
                 <View style={styles.analysisSection}>
                   <View style={styles.analysisHeader}>
                     <Text style={styles.analysisTitle}>Audio Analysis Results</Text>
                     <View style={styles.analysisStatus}>
                       <View style={[styles.statusDot, { backgroundColor: lastUploadResult ? COLORS.SUCCESS : COLORS.WARNING }]} />
                       <Text style={styles.analysisStatusText}>
                         {lastUploadResult ? 'Analysis Complete' : 'No Analysis Yet'}
                       </Text>
                     </View>
                   </View>
                   {lastUploadResult ? (
                     <View style={styles.analysisResults}>
                       <View style={styles.resultItem}>
                         <Text style={styles.resultLabel}>Key Signature:</Text>
                         <Text style={styles.resultValue}>{lastUploadResult.keySignature || 'Unknown'}</Text>
                       </View>
                       <View style={styles.resultItem}>
                         <Text style={styles.resultLabel}>Tempo:</Text>
                         <Text style={styles.resultValue}>{lastUploadResult.tempo || 'Unknown'} BPM</Text>
                       </View>
                       <View style={styles.resultItem}>
                         <Text style={styles.resultLabel}>Chord Progression:</Text>
                         <View style={styles.chordProgressionList}>
                           {currentChordProgression.map((chord, index) => (
                             <View key={index} style={styles.chordTag}>
                               <Text style={styles.chordTagText}>{chord}</Text>
                             </View>
                           ))}
                         </View>
                       </View>
                     </View>
                   ) : (
                     <View style={styles.noAnalysisState}>
                       <Text style={styles.noAnalysisIcon}>🎼</Text>
                       <Text style={styles.noAnalysisText}>Upload or record audio to see analysis results</Text>
                       <TouchableOpacity style={styles.uploadPromptButton}>
                         <Text style={styles.uploadPromptText}>📁 Upload Audio File</Text>
                       </TouchableOpacity>
                     </View>
                   )}
                 </View>
                 
                 <View style={styles.tutorSection}>
                   <View style={styles.tutorHeader}>
                     <Text style={styles.tutorTitle}>AI Music Tutor</Text>
                     <View style={styles.tutorAvatar}>
                       <Text style={styles.tutorAvatarText}>🎓</Text>
                     </View>
                   </View>
                   <View style={styles.tutorContent}>
                     <View style={styles.tutorMessages}>
                       <View style={styles.tutorMessage}>
                         <Text style={styles.tutorMessageText}>
                           {lastUploadResult 
                             ? `Great! I can see you're working with a ${lastUploadResult.keySignature || 'unknown key'} progression. The chords ${currentChordProgression.join(', ')} create a beautiful harmonic movement. Would you like me to explain the theory behind this progression or suggest practice exercises?`
                             : 'Hello! I\'m your AI music tutor. Upload an audio file or record yourself playing, and I\'ll provide detailed analysis and personalized guidance to help improve your musical skills.'}
                         </Text>
                       </View>
                     </View>
                     <View style={styles.tutorInput}>
                       <TouchableOpacity style={styles.tutorInputField}>
                         <Text style={styles.tutorInputPlaceholder}>Ask me anything about music theory, chords, or techniques...</Text>
                       </TouchableOpacity>
                       <TouchableOpacity style={styles.sendButton}>
                         <Text style={styles.sendButtonText}>→</Text>
                       </TouchableOpacity>
                     </View>
                   </View>
                 </View>
               </View>
             </View>
           </View>

          {/* Bottom Row - Fretboard */}
          <View style={styles.bottomRow}>
            <View style={styles.fretboardCard}>
              <View style={styles.glassShine} />
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Guitar Fretboard</Text>
                <View style={styles.chordProgressionDisplay}>
                  {currentChordProgression.map((chord, index) => (
                    <View key={index} style={styles.progressionChord}>
                      <Text style={styles.progressionChordText}>{chord}</Text>
                    </View>
                  ))}
                </View>
              </View>
              <View style={styles.fretboardContent}>
                <GuitarFretboard 
                  chordProgression={currentChordProgression}
                  onChordPress={handleChordSelection}
                  highlightedChord={selectedChord}
                />
              </View>
            </View>
          </View>
        </ScrollView>


      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
    position: 'relative',
  },
  
  // Glass Morphism Overlay
  glassOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: COLORS.GRADIENT_GLASS,
    pointerEvents: 'none',
    zIndex: -1,
  },
  
  // Glass Shine Effect
  glassShine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '50%',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    pointerEvents: 'none',
    zIndex: 1,
  },
  
  // Header Styles with Glass Effect
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.2)',
    elevation: 8,
    shadowColor: 'rgba(0, 0, 0, 0.1)',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  headerLeft: {
    flex: 1,
  },
  headerCenter: {
    flex: 2,
    alignItems: 'center',
  },
  headerRight: {
    flex: 1,
    alignItems: 'flex-end',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoIcon: {
    fontSize: 24,
    marginRight: SPACING.XS,
  },
  logoText: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.PRIMARY,
  },
  headerTitle: {
    fontSize: FONT_SIZES.LG,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: '500',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  // Dashboard Layout
  dashboard: {
    flex: 1,
    flexDirection: 'row',
    padding: SPACING.MD,
    gap: SPACING.MD,
    minHeight: 0, // Prevent overflow issues
  },
  
  // Sidebar Styles with Glass Effect
  sidebar: {
    width: 220,
    backgroundColor: COLORS.SURFACE,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    padding: SPACING.LG,
    gap: SPACING.LG,
    elevation: 8,
    shadowColor: COLORS.SHADOW_GLASS,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    position: 'relative',
    overflow: 'hidden',
  },
  sidebarSection: {
    gap: SPACING.SM,
  },
  sidebarTitle: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.XS,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  // Main Area Styles
  mainArea: {
    flex: 1,
    gap: SPACING.MD,
    minHeight: 0, // Prevent overflow
    overflow: 'hidden', // Ensure proper clipping
  },
  
  // Card Base Styles
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.MD,
    paddingBottom: SPACING.SM,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.PANEL,
  },
  cardTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  // Top Row Styles
  topRow: {
    flexDirection: 'row',
    gap: SPACING.MD,
    height: 220,
    alignItems: 'stretch',
  },
  instructorCard: {
    flex: 2,
    backgroundColor: COLORS.CARD,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    elevation: 6,
    shadowColor: COLORS.SHADOW_GLASS,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  instructorContent: {
    flexDirection: 'row',
    flex: 1,
    gap: SPACING.MD,
    alignItems: 'center',
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.PRIMARY,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarEmoji: {
    fontSize: 24,
  },
  messageContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  instructorMessage: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    lineHeight: 20,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 1,
  },
  instructorActions: {
    alignItems: 'center',
    marginTop: SPACING.SM,
  },
  micButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.ACCENT,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 6,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
  },
  micButtonActive: {
    backgroundColor: COLORS.ERROR,
  },
  micIcon: {
    fontSize: 20,
  },
  chordCard: {
    flex: 1,
    backgroundColor: COLORS.CARD,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    elevation: 6,
    shadowColor: COLORS.SHADOW_GLASS,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  chordDisplay: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: SPACING.MD,
  },
  chordName: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
    display: 'none', // Hide duplicate chord name
  },
  chordDiagram: {
    flex: 1,
    justifyContent: 'center',
  },
  
  // Middle Row Styles - Music Tutor Workspace
  middleRow: {
    height: 420,
    alignItems: 'stretch',
  },
  musicTutorCard: {
    flex: 1,
    backgroundColor: COLORS.CARD,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    elevation: 6,
    shadowColor: COLORS.SHADOW_GLASS,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  tutorControls: {
    flexDirection: 'row',
    gap: SPACING.SM,
  },
  analyzeButton: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    backgroundColor: COLORS.GRADIENT_PRIMARY,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 4,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  analyzeButtonText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  chatButton: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    backgroundColor: COLORS.GRADIENT_SECONDARY,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 4,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  chatButtonText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  tutorWorkspace: {
    flex: 1,
    flexDirection: 'row',
    gap: SPACING.MD,
  },
  analysisSection: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
    borderRadius: 12,
    padding: SPACING.MD,
  },
  analysisHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.MD,
  },
  analysisTitle: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 1,
  },
  analysisStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.XS,
  },
  analysisStatusText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 1,
  },
  analysisResults: {
    gap: SPACING.MD,
  },
  resultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.SM,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.PANEL,
  },
  resultLabel: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: '500',
  },
  resultValue: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: '600',
  },
  chordProgressionList: {
    flexDirection: 'row',
    gap: SPACING.XS,
  },
  chordTag: {
    paddingHorizontal: SPACING.SM,
    paddingVertical: SPACING.XS,
    backgroundColor: COLORS.PRIMARY,
    borderRadius: 6,
  },
  chordTagText: {
    fontSize: FONT_SIZES.XS,
    fontWeight: '600',
    color: COLORS.SURFACE,
  },
  noAnalysisState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: SPACING.MD,
  },
  noAnalysisIcon: {
    fontSize: 48,
    opacity: 0.5,
  },
  noAnalysisText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  uploadPromptButton: {
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    backgroundColor: COLORS.ACCENT,
    borderRadius: 8,
  },
  uploadPromptText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  tutorSection: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
    borderRadius: 12,
    padding: SPACING.MD,
  },
  tutorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.MD,
  },
  tutorTitle: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  tutorAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.PRIMARY,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tutorAvatarText: {
    fontSize: 16,
  },
  tutorContent: {
    flex: 1,
    gap: SPACING.MD,
  },
  tutorMessages: {
    flex: 1,
  },
  tutorMessage: {
    backgroundColor: COLORS.PANEL,
    borderRadius: 12,
    padding: SPACING.MD,
  },
  tutorMessageText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    lineHeight: 18,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 1,
  },
  tutorInput: {
    flexDirection: 'row',
    gap: SPACING.SM,
  },
  tutorInputField: {
    flex: 1,
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    backgroundColor: COLORS.PANEL,
    borderRadius: 8,
    justifyContent: 'center',
  },
  tutorInputPlaceholder: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    opacity: 0.7,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.PRIMARY,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonText: {
    fontSize: 18,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: 'bold',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  // Bottom Row Styles
  bottomRow: {
    height: 320,
    alignItems: 'stretch',
  },
  fretboardCard: {
    flex: 1,
    backgroundColor: COLORS.CARD,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    elevation: 6,
    shadowColor: COLORS.SHADOW_GLASS,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  fretboardContent: {
    flex: 1,
  },
  chordProgressionDisplay: {
    flexDirection: 'row',
    gap: SPACING.XS,
  },
  progressionChord: {
    paddingHorizontal: SPACING.SM,
    paddingVertical: SPACING.XS,
    backgroundColor: COLORS.PRIMARY,
    borderRadius: 6,
  },
  progressionChordText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.TEXT_PRIMARY,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  // Audio Controls in Sidebar
  recordButton: {
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    backgroundColor: COLORS.ERROR,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: SPACING.SM,
    borderWidth: 1,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 4,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  recordButtonActive: {
    backgroundColor: COLORS.ERROR,
    opacity: 0.8,
  },
  recordIcon: {
    fontSize: 18,
  },
  recordText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
    marginTop: SPACING.XS,
  },
  uploadButton: {
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    backgroundColor: COLORS.PRIMARY,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: SPACING.SM,
    borderWidth: 1,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 4,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  uploadIcon: {
    fontSize: 18,
  },
  uploadText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
    marginTop: SPACING.XS,
  },
  playbackButton: {
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    backgroundColor: COLORS.SUCCESS,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: SPACING.SM,
    borderWidth: 1,
    borderColor: COLORS.BORDER_LIGHT,
    elevation: 4,
    shadowColor: COLORS.SHADOW_MEDIUM,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  playbackIcon: {
    fontSize: 18,
  },
  playbackText: {
    fontSize: FONT_SIZES.SM,
    fontWeight: '600',
    color: COLORS.SURFACE,
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
    marginTop: SPACING.XS,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.SM,
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 1,
  },
  refreshButton: {
    padding: SPACING.XS,
    marginLeft: SPACING.SM,
  },
  refreshButtonText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: 'bold',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.SUCCESS,
  },
  welcomeContainer: {
    backgroundColor: COLORS.PRIMARY,
    padding: SPACING.LG,
    marginHorizontal: SPACING.MD,
    marginBottom: SPACING.MD,
    borderRadius: 12,
  },
  welcomeTitle: {
    fontSize: FONT_SIZES.XL,
    fontWeight: 'bold',
    color: COLORS.SURFACE,
    marginBottom: SPACING.MD,
    textAlign: 'center',
  },
  welcomeText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.SURFACE,
    lineHeight: 22,
    textAlign: 'center',
    opacity: 0.9,
  },
  quickActionsContainer: {
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
  quickActionsTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
    textAlign: 'center',
  },
  quickActionButton: {
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    borderRadius: 8,
    marginBottom: SPACING.SM,
    alignItems: 'center',
  },
  primaryAction: {
    backgroundColor: COLORS.PRIMARY,
  },
  secondaryAction: {
    backgroundColor: COLORS.SECONDARY,
  },
  tertiaryAction: {
    backgroundColor: COLORS.ACCENT,
  },
  quickActionButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  featuresContainer: {
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
  featuresTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
    textAlign: 'center',
  },
  featureItem: {
    marginBottom: SPACING.MD,
    paddingBottom: SPACING.MD,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.BACKGROUND,
  },
  featureTitle: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.XS,
  },
  featureDescription: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
    lineHeight: 18,
  },
});

export default HomeScreen;