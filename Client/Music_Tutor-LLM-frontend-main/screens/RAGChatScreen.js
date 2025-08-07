import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { queryRAG } from '../services/apiService';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';
import { showErrorAlert } from '../utils/helpers';

const RAGChatScreen = ({ route }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI Music Tutor. I can help you with music theory, chord progressions, practice tips, and answer any questions about your musical journey. What would you like to learn today?",
      isBot: true,
      timestamp: new Date(),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef();
  const { chordData } = route.params || {};

  useEffect(() => {
    // If we have chord data from analysis, add a contextual message
    if (chordData) {
      const contextMessage = {
        id: Date.now(),
        text: `I can see you've analyzed some audio! I detected chords like ${chordData.chords?.slice(0, 3).map(c => c.name).join(', ')}. Feel free to ask me about these chords, the progression, or any music theory questions!`,
        isBot: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, contextMessage]);
    }
  }, [chordData]);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputText.trim(),
      isBot: false,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Prepare context from chord data if available
      const context = chordData ? {
        chords: chordData.chords?.map(c => c.name) || [],
        key: chordData.key,
        confidence: chordData.confidence,
        analysis_metadata: chordData.metadata,
      } : {};

      const response = await queryRAG(userMessage.text, context);
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.response || response.guidance || "I'm sorry, I couldn't process that request. Could you try rephrasing your question?",
        isBot: true,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error getting RAG response:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: "I'm having trouble connecting to my knowledge base right now. Please check your connection and try again.",
        isBot: true,
        timestamp: new Date(),
        isError: true,
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message) => {
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          message.isBot ? styles.botMessage : styles.userMessage,
        ]}
      >
        <View
          style={[
            styles.messageBubble,
            message.isBot ? styles.botBubble : styles.userBubble,
            message.isError && styles.errorBubble,
          ]}
        >
          <Text
            style={[
              styles.messageText,
              message.isBot ? styles.botText : styles.userText,
            ]}
          >
            {message.text}
          </Text>
          <Text style={styles.timestamp}>
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </Text>
        </View>
      </View>
    );
  };

  const renderQuickQuestions = () => {
    const quickQuestions = [
      "What's a chord progression?",
      "How do I practice scales?",
      "Explain music theory basics",
      "What are seventh chords?",
    ];

    return (
      <View style={styles.quickQuestionsContainer}>
        <Text style={styles.quickQuestionsTitle}>Quick Questions:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {quickQuestions.map((question, index) => (
            <TouchableOpacity
              key={index}
              style={styles.quickQuestionButton}
              onPress={() => setInputText(question)}
            >
              <Text style={styles.quickQuestionText}>{question}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.map(renderMessage)}
          
          {isLoading && (
            <View style={[styles.messageContainer, styles.botMessage]}>
              <View style={[styles.messageBubble, styles.botBubble, styles.loadingBubble]}>
                <Text style={styles.loadingText}>Thinking...</Text>
                <View style={styles.loadingDots}>
                  <Text style={styles.loadingDot}>●</Text>
                  <Text style={styles.loadingDot}>●</Text>
                  <Text style={styles.loadingDot}>●</Text>
                </View>
              </View>
            </View>
          )}
        </ScrollView>

        {messages.length <= 2 && renderQuickQuestions()}

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask me about music theory, chords, practice tips..."
            placeholderTextColor={COLORS.TEXT_MUTED}
            multiline
            maxLength={500}
            editable={!isLoading}
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
            ]}
            onPress={sendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: SPACING.MD,
  },
  messagesContent: {
    paddingTop: SPACING.MD,
    paddingBottom: SPACING.LG,
  },
  messageContainer: {
    marginVertical: SPACING.XS,
  },
  botMessage: {
    alignItems: 'flex-start',
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    borderRadius: 20,
  },
  botBubble: {
    backgroundColor: COLORS.SURFACE,
    borderBottomLeftRadius: 5,
  },
  userBubble: {
    backgroundColor: COLORS.PRIMARY,
    borderBottomRightRadius: 5,
  },
  errorBubble: {
    backgroundColor: COLORS.ERROR,
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  messageText: {
    fontSize: FONT_SIZES.MD,
    lineHeight: 20,
  },
  botText: {
    color: COLORS.TEXT_PRIMARY,
  },
  userText: {
    color: COLORS.BACKGROUND,
    fontWeight: '500',
  },
  timestamp: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_MUTED,
    marginTop: SPACING.XS,
    alignSelf: 'flex-end',
  },
  loadingText: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.MD,
    marginRight: SPACING.SM,
  },
  loadingDots: {
    flexDirection: 'row',
  },
  loadingDot: {
    color: COLORS.PRIMARY,
    fontSize: FONT_SIZES.SM,
    marginHorizontal: 1,
  },
  quickQuestionsContainer: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    borderTopWidth: 1,
    borderTopColor: COLORS.PANEL,
  },
  quickQuestionsTitle: {
    color: COLORS.TEXT_SECONDARY,
    fontSize: FONT_SIZES.SM,
    marginBottom: SPACING.SM,
    fontWeight: '600',
  },
  quickQuestionButton: {
    backgroundColor: COLORS.PANEL,
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    borderRadius: 20,
    marginRight: SPACING.SM,
  },
  quickQuestionText: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.SM,
  },
  inputContainer: {
    flexDirection: 'row',
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    backgroundColor: COLORS.SURFACE,
    borderTopWidth: 1,
    borderTopColor: COLORS.PANEL,
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    backgroundColor: COLORS.PANEL,
    borderRadius: 20,
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.MD,
    maxHeight: 100,
    marginRight: SPACING.SM,
  },
  sendButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.SM,
    borderRadius: 20,
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.TEXT_MUTED,
  },
  sendButtonText: {
    color: COLORS.BACKGROUND,
    fontSize: FONT_SIZES.MD,
    fontWeight: '600',
  },
});

export default RAGChatScreen;