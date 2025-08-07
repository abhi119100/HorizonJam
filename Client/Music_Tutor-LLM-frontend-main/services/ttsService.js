import { Audio } from 'expo-av';
import { Platform } from 'react-native';

// Initialize audio mode for better playback (only on native platforms)
if (Platform.OS !== 'web') {
  Audio.setAudioModeAsync({
    allowsRecordingIOS: false,
    staysActiveInBackground: false,
    interruptionModeIOS: Audio.InterruptionModeIOS?.DoNotMix || 0,
    playsInSilentModeIOS: true,
    shouldDuckAndroid: true,
    interruptionModeAndroid: Audio.InterruptionModeAndroid?.DoNotMix || 0,
    playThroughEarpieceAndroid: false,
  }).catch(error => {
    console.warn('Audio mode setup failed:', error);
  });
}

/**
 * Play audio from URL (TTS generated audio)
 * @param {string} url - URL of the audio file to play
 * @returns {Promise<Object>} Sound object for controlling playback
 */
export const playAudioFromUrl = async (url) => {
  try {
    console.log('Loading audio from URL:', url);
    
    const { sound } = await Audio.Sound.createAsync(
      { uri: url },
      { shouldPlay: false, isLooping: false }
    );

    // Add status update listener
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded) {
        console.log('Audio status:', {
          isPlaying: status.isPlaying,
          positionMillis: status.positionMillis,
          durationMillis: status.durationMillis,
        });
      }
    });

    await sound.playAsync();
    return sound;
  } catch (error) {
    console.error('Error playing audio from URL:', error);
    throw new Error(`Failed to play audio: ${error.message}`);
  }
};

/**
 * Play audio from local file
 * @param {string} localUri - Local URI of the audio file
 * @returns {Promise<Object>} Sound object for controlling playback
 */
export const playLocalAudio = async (localUri) => {
  try {
    console.log('Loading local audio:', localUri);
    
    const { sound } = await Audio.Sound.createAsync(
      { uri: localUri },
      { shouldPlay: false, isLooping: false }
    );

    await sound.playAsync();
    return sound;
  } catch (error) {
    console.error('Error playing local audio:', error);
    throw new Error(`Failed to play local audio: ${error.message}`);
  }
};

/**
 * Stop audio playback
 * @param {Object} sound - Sound object to stop
 */
export const stopAudio = async (sound) => {
  try {
    if (sound) {
      await sound.stopAsync();
      await sound.unloadAsync();
    }
  } catch (error) {
    console.error('Error stopping audio:', error);
  }
};

/**
 * Pause audio playback
 * @param {Object} sound - Sound object to pause
 */
export const pauseAudio = async (sound) => {
  try {
    if (sound) {
      await sound.pauseAsync();
    }
  } catch (error) {
    console.error('Error pausing audio:', error);
  }
};

/**
 * Resume audio playback
 * @param {Object} sound - Sound object to resume
 */
export const resumeAudio = async (sound) => {
  try {
    if (sound) {
      await sound.playAsync();
    }
  } catch (error) {
    console.error('Error resuming audio:', error);
  }
};

/**
 * Get audio recording permissions
 * @returns {Promise<boolean>} Whether permission was granted
 */
export const getAudioPermissions = async () => {
  try {
    const { status } = await Audio.requestPermissionsAsync();
    return status === 'granted';
  } catch (error) {
    console.error('Error requesting audio permissions:', error);
    return false;
  }
};