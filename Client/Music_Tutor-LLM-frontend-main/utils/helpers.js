import { Alert, Platform } from 'react-native';
import { MUSIC_CONSTANTS, STATUS_MESSAGES } from './constants';

/**
 * Format duration from milliseconds to MM:SS format
 * @param {number} milliseconds - Duration in milliseconds
 * @returns {string} Formatted duration string
 */
export const formatDuration = (milliseconds) => {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

/**
 * Validate audio file
 * @param {Object} audioFile - Audio file object
 * @returns {Object} Validation result with isValid and error message
 */
export const validateAudioFile = (audioFile) => {
  if (!audioFile) {
    return { isValid: false, error: STATUS_MESSAGES.NO_AUDIO };
  }

  if (!audioFile.uri) {
    return { isValid: false, error: STATUS_MESSAGES.INVALID_FILE };
  }

  // Check file extension
  const validExtensions = ['.wav', '.mp3', '.m4a', '.aac'];
  const fileExtension = audioFile.uri.toLowerCase().substring(audioFile.uri.lastIndexOf('.'));
  
  if (!validExtensions.includes(fileExtension)) {
    return { isValid: false, error: 'Unsupported audio format. Please use WAV, MP3, M4A, or AAC.' };
  }

  return { isValid: true, error: null };
};

/**
 * Show alert with error message
 * @param {string} title - Alert title
 * @param {string} message - Alert message
 * @param {Function} onPress - Callback function for OK button
 */
export const showErrorAlert = (title = 'Error', message = STATUS_MESSAGES.ERROR, onPress = null) => {
  Alert.alert(
    title,
    message,
    [{ text: 'OK', onPress }],
    { cancelable: false }
  );
};

/**
 * Show confirmation alert
 * @param {string} title - Alert title
 * @param {string} message - Alert message
 * @param {Function} onConfirm - Callback for confirm button
 * @param {Function} onCancel - Callback for cancel button
 */
export const showConfirmAlert = (title, message, onConfirm, onCancel = null) => {
  Alert.alert(
    title,
    message,
    [
      { text: 'Cancel', style: 'cancel', onPress: onCancel },
      { text: 'OK', onPress: onConfirm },
    ],
    { cancelable: false }
  );
};

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Get platform-specific styles
 * @param {Object} iosStyle - iOS specific styles
 * @param {Object} androidStyle - Android specific styles
 * @returns {Object} Platform-specific styles
 */
export const getPlatformStyle = (iosStyle, androidStyle) => {
  return Platform.OS === 'ios' ? iosStyle : androidStyle;
};

/**
 * Convert chord data to display format
 * @param {Object} chordData - Raw chord data from API
 * @returns {Object} Formatted chord data for display
 */
export const formatChordData = (chordData) => {
  if (!chordData || !chordData.chords) {
    return { chords: [], key: 'Unknown', confidence: 0 };
  }

  return {
    chords: chordData.chords.map(chord => ({
      name: chord.name || 'Unknown',
      confidence: Math.round((chord.confidence || 0) * 100),
      timestamp: chord.timestamp || 0,
      duration: chord.duration || 0,
    })),
    key: chordData.key || 'Unknown',
    confidence: Math.round((chordData.confidence || 0) * 100),
    tempo: chordData.tempo || null,
    timeSignature: chordData.timeSignature || null,
  };
};

/**
 * Generate random color for chord visualization
 * @param {string} chordName - Name of the chord
 * @returns {string} Hex color code
 */
export const getChordColor = (chordName) => {
  // Generate consistent color based on chord name
  let hash = 0;
  for (let i = 0; i < chordName.length; i++) {
    hash = chordName.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 80%)`;
};

/**
 * Check if a note is in a specific scale
 * @param {string} note - Musical note
 * @param {string} scale - Musical scale
 * @returns {boolean} Whether the note is in the scale
 */
export const isNoteInScale = (note, scale) => {
  // This is a simplified implementation
  // In a real app, you'd have more complex music theory logic
  const majorScales = {
    'C': ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
    'G': ['G', 'A', 'B', 'C', 'D', 'E', 'F#'],
    'D': ['D', 'E', 'F#', 'G', 'A', 'B', 'C#'],
    // Add more scales as needed
  };

  const scaleNotes = majorScales[scale.split(' ')[0]];
  return scaleNotes ? scaleNotes.includes(note) : false;
};

/**
 * Calculate similarity between two chord progressions
 * @param {Array} progression1 - First chord progression
 * @param {Array} progression2 - Second chord progression
 * @returns {number} Similarity score between 0 and 1
 */
export const calculateProgressionSimilarity = (progression1, progression2) => {
  if (!progression1 || !progression2 || progression1.length === 0 || progression2.length === 0) {
    return 0;
  }

  const minLength = Math.min(progression1.length, progression2.length);
  let matches = 0;

  for (let i = 0; i < minLength; i++) {
    if (progression1[i] === progression2[i]) {
      matches++;
    }
  }

  return matches / minLength;
};