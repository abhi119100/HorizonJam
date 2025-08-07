import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';

const InstructorPanel = ({ 
  message = "Hello! Do you want to play a song?",
  onMicrophonePress = null,
  showMicrophone = true,
  avatar = 'instructor', // 'instructor' or 'tutor'
  isListening = false 
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const handleMicrophonePress = () => {
    if (onMicrophonePress) {
      onMicrophonePress();
    }
  };

  const renderAvatar = () => {
    // Simple avatar using emoji/text since we don't have image assets
    const avatarContent = avatar === 'tutor' ? '🎓' : '🎵';
    const avatarBg = avatar === 'tutor' ? COLORS.SUCCESS : COLORS.PRIMARY;

    return (
      <View style={[styles.avatar, { backgroundColor: avatarBg }]}>
        <Text style={styles.avatarEmoji}>{avatarContent}</Text>
      </View>
    );
  };

  const renderMicrophoneButton = () => {
    if (!showMicrophone) return null;

    return (
      <TouchableOpacity
        style={[
          styles.microphoneButton,
          isListening && styles.microphoneListening,
          isPressed && styles.microphonePressed,
        ]}
        onPress={handleMicrophonePress}
        onPressIn={() => setIsPressed(true)}
        onPressOut={() => setIsPressed(false)}
        activeOpacity={0.8}
      >
        <Text style={styles.microphoneIcon}>🎤</Text>
        {isListening && (
          <View style={styles.listeningIndicator}>
            <View style={[styles.listeningDot, styles.dot1]} />
            <View style={[styles.listeningDot, styles.dot2]} />
            <View style={[styles.listeningDot, styles.dot3]} />
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>
          {avatar === 'tutor' ? 'Tutor' : 'Instructor'}
        </Text>
      </View>
      
      <View style={styles.content}>
        <View style={styles.messageContainer}>
          <Text style={styles.message}>{message}</Text>
          {avatar === 'tutor' && renderAvatar()}
        </View>
        
        {showMicrophone && (
          <View style={styles.microphoneContainer}>
            {renderMicrophoneButton()}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.PANEL,
    borderRadius: 8,
    padding: SPACING.MD,
    minHeight: 150,
  },
  header: {
    marginBottom: SPACING.MD,
  },
  title: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    justifyContent: 'space-between',
  },
  messageContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  message: {
    color: COLORS.TEXT_PRIMARY,
    fontSize: FONT_SIZES.MD,
    lineHeight: 22,
    flex: 1,
    marginRight: SPACING.MD,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'flex-end',
  },
  avatarEmoji: {
    fontSize: 24,
  },
  microphoneContainer: {
    alignItems: 'center',
    marginTop: SPACING.MD,
  },
  microphoneButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#3B82F6', // Blue
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    position: 'relative',
  },
  microphonePressed: {
    transform: [{ scale: 0.95 }],
    elevation: 2,
  },
  microphoneListening: {
    backgroundColor: '#EF4444', // Red when listening
  },
  microphoneIcon: {
    fontSize: 24,
  },
  listeningIndicator: {
    position: 'absolute',
    bottom: -30,
    flexDirection: 'row',
    gap: 4,
  },
  listeningDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.ERROR,
  },
  dot1: {
    animationDelay: '0ms',
  },
  dot2: {
    animationDelay: '200ms',
  },
  dot3: {
    animationDelay: '400ms',
  },
});

export default InstructorPanel;