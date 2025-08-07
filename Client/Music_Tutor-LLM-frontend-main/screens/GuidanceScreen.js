import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import GuidanceText from '../components/GuidanceText';
import PlayerControls from '../components/PlayerControls';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';
import { getGuidance } from '../services/apiService';
import { showErrorAlert } from '../utils/helpers';

const GuidanceScreen = ({ route, navigation }) => {
  const { 
    guidanceText: initialGuidanceText,
    audioUrl: initialAudioUrl,
    chordData,
    focusChord 
  } = route.params || {};

  const [question, setQuestion] = useState('');
  const [guidanceText, setGuidanceText] = useState(initialGuidanceText || '');
  const [audioUrl, setAudioUrl] = useState(initialAudioUrl || null);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  useEffect(() => {
    // If we received initial guidance, add it to history
    if (initialGuidanceText) {
      const initialEntry = {
        question: focusChord ? 
          `Tell me about the ${focusChord.name} chord` : 
          'Analyze my chord progression',
        answer: initialGuidanceText,
        audioUrl: initialAudioUrl,
        timestamp: Date.now(),
      };
      setConversationHistory([initialEntry]);
    }
  }, [initialGuidanceText, initialAudioUrl, focusChord]);

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      showErrorAlert('No Question', 'Please enter a music-related question.');
      return;
    }

    setIsLoading(true);
    
    try {
      const guidanceQuery = {
        question: question.trim(),
        context: {
          chordData: chordData,
          conversationHistory: conversationHistory.slice(-3), // Last 3 interactions for context
          focusChord: focusChord,
        },
      };

      const result = await getGuidance(guidanceQuery);
      
      if (result && result.guidance) {
        const newGuidance = result.guidance;
        const newAudioUrl = result.audioUrl;
        
        // Add to conversation history
        const newEntry = {
          question: question.trim(),
          answer: newGuidance,
          audioUrl: newAudioUrl,
          timestamp: Date.now(),
        };
        
        setConversationHistory(prev => [...prev, newEntry]);
        setGuidanceText(newGuidance);
        setAudioUrl(newAudioUrl);
        setQuestion(''); // Clear the input
      } else {
        throw new Error('No guidance received from server');
      }
    } catch (error) {
      console.error('Error getting guidance:', error);
      
      let errorMessage = 'Failed to get guidance. ';
      
      if (error.message.includes('Network')) {
        errorMessage += 'Please check your internet connection.';
      } else if (error.message.includes('timeout')) {
        errorMessage += 'The request timed out. Please try again.';
      } else {
        errorMessage += 'Please try again later.';
      }
      
      showErrorAlert('Guidance Error', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestGuidance = () => {
    // Focus on the text input when user wants to ask a question
    textInputRef?.current?.focus();
  };

  const renderQuestionInput = () => {
    return (
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Ask Your Music Tutor</Text>
        <View style={styles.inputRow}>
          <TextInput
            ref={textInputRef}
            style={styles.textInput}
            value={question}
            onChangeText={setQuestion}
            placeholder="Ask about chords, scales, theory, techniques..."
            placeholderTextColor={COLORS.TEXT_SECONDARY}
            multiline
            maxLength={500}
            editable={!isLoading}
          />
          <TouchableOpacity
            style={[styles.askButton, isLoading && styles.disabledButton]}
            onPress={handleAskQuestion}
            disabled={isLoading || !question.trim()}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color={COLORS.SURFACE} />
            ) : (
              <Text style={styles.askButtonText}>Ask</Text>
            )}
          </TouchableOpacity>
        </View>
        <Text style={styles.characterCount}>
          {question.length}/500 characters
        </Text>
      </View>
    );
  };

  const renderSuggestedQuestions = () => {
    const suggestions = [
      "How can I improve my chord transitions?",
      "What scales work with this key?",
      "Explain the theory behind this progression",
      "What are some practice exercises for these chords?",
      "How do I make my playing more expressive?",
    ];

    // Add context-specific suggestions
    if (chordData?.key) {
      suggestions.unshift(`What songs are in the key of ${chordData.key}?`);
    }
    
    if (focusChord) {
      suggestions.unshift(`What are variations of the ${focusChord.name} chord?`);
    }

    return (
      <View style={styles.suggestionsContainer}>
        <Text style={styles.suggestionsTitle}>Suggested Questions</Text>
        {suggestions.slice(0, 4).map((suggestion, index) => (
          <TouchableOpacity
            key={index}
            style={styles.suggestionButton}
            onPress={() => setQuestion(suggestion)}
            disabled={isLoading}
          >
            <Text style={styles.suggestionText}>{suggestion}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderConversationHistory = () => {
    if (conversationHistory.length === 0) return null;

    return (
      <View style={styles.historyContainer}>
        <Text style={styles.historyTitle}>Conversation History</Text>
        {conversationHistory.slice(-3).reverse().map((entry, index) => (
          <TouchableOpacity
            key={entry.timestamp}
            style={styles.historyItem}
            onPress={() => {
              setGuidanceText(entry.answer);
              setAudioUrl(entry.audioUrl);
            }}
          >
            <Text style={styles.historyQuestion} numberOfLines={2}>
              Q: {entry.question}
            </Text>
            <Text style={styles.historyPreview} numberOfLines={2}>
              {entry.answer.substring(0, 100)}...
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  let textInputRef = React.useRef();

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.content}>
          <GuidanceText 
            guidanceText={guidanceText}
            isLoading={isLoading}
            onRequestGuidance={handleRequestGuidance}
            showRequestButton={!guidanceText && !isLoading}
          />

          {audioUrl && (
            <PlayerControls 
              audioUrl={audioUrl}
              autoPlay={false}
            />
          )}

          {!guidanceText && !isLoading && renderSuggestedQuestions()}
          {conversationHistory.length > 1 && renderConversationHistory()}
        </View>

        {renderQuestionInput()}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
  keyboardContainer: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  inputContainer: {
    backgroundColor: COLORS.SURFACE,
    padding: SPACING.LG,
    borderTopWidth: 1,
    borderTopColor: COLORS.BACKGROUND,
  },
  inputLabel: {
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.SM,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: SPACING.SM,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: COLORS.TEXT_SECONDARY,
    borderRadius: 8,
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    maxHeight: 80,
    minHeight: 40,
  },
  askButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 8,
    minWidth: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabledButton: {
    backgroundColor: COLORS.TEXT_SECONDARY,
  },
  askButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  characterCount: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'right',
    marginTop: SPACING.XS,
  },
  suggestionsContainer: {
    backgroundColor: COLORS.SURFACE,
    margin: SPACING.MD,
    padding: SPACING.LG,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.PANEL,
  },
  suggestionsTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
  },
  suggestionButton: {
    backgroundColor: COLORS.BACKGROUND,
    padding: SPACING.MD,
    borderRadius: 8,
    marginBottom: SPACING.SM,
  },
  suggestionText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_PRIMARY,
  },
  historyContainer: {
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
  historyTitle: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.MD,
  },
  historyItem: {
    backgroundColor: COLORS.BACKGROUND,
    padding: SPACING.MD,
    borderRadius: 8,
    marginBottom: SPACING.SM,
  },
  historyQuestion: {
    fontSize: FONT_SIZES.SM,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    marginBottom: SPACING.XS,
  },
  historyPreview: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_SECONDARY,
  },
});

export default GuidanceScreen;