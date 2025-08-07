import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { COLORS, SPACING, FONT_SIZES, AUDIO_CONFIG, STATUS_MESSAGES } from '../utils/constants';
import { formatDuration, showErrorAlert, validateAudioFile } from '../utils/helpers';
import { getAudioPermissions } from '../services/ttsService';

const AudioUploader = ({ onAudioRecorded, isLoading = false }) => {
  const [recording, setRecording] = useState(null);
  const [recordingStatus, setRecordingStatus] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [hasPermission, setHasPermission] = useState(false);

  useEffect(() => {
    checkPermissions();
    return () => {
      if (recording) {
        recording.stopAndUnloadAsync();
      }
    };
  }, []);

  const checkPermissions = async () => {
    const permission = await getAudioPermissions();
    setHasPermission(permission);
    
    if (!permission) {
      showErrorAlert(
        'Permission Required',
        'Microphone access is required to record audio. Please enable it in your device settings.'
      );
    }
  };

  const startRecording = async () => {
    if (!hasPermission) {
      await checkPermissions();
      return;
    }

    try {
      console.log('Starting recording...');
      
      // Configure audio session
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      const recordingOptions = Platform.select({
        ios: AUDIO_CONFIG.RECORDING_OPTIONS.ios,
        android: AUDIO_CONFIG.RECORDING_OPTIONS.android,
      });

      const { recording: newRecording } = await Audio.Recording.createAsync(recordingOptions);
      
      newRecording.setOnRecordingStatusUpdate((status) => {
        setRecordingStatus(status);
        if (status.isRecording) {
          setRecordingDuration(status.durationMillis || 0);
        }
      });

      setRecording(newRecording);
      setIsRecording(true);
      console.log('Recording started successfully');
    } catch (error) {
      console.error('Failed to start recording:', error);
      showErrorAlert('Recording Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      console.log('Stopping recording...');
      setIsRecording(false);
      
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      
      if (uri) {
        const fileInfo = await FileSystem.getInfoAsync(uri);
        
        const audioFile = {
          uri: uri,
          name: `recording_${Date.now()}.wav`,
          type: 'audio/wav',
          size: fileInfo.size,
        };

        const validation = validateAudioFile(audioFile);
        
        if (validation.isValid) {
          onAudioRecorded(audioFile);
        } else {
          showErrorAlert('Invalid Audio', validation.error);
        }
      }

      setRecording(null);
      setRecordingStatus(null);
      setRecordingDuration(0);
    } catch (error) {
      console.error('Failed to stop recording:', error);
      showErrorAlert('Recording Error', 'Failed to stop recording. Please try again.');
    }
  };

  const cancelRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      setRecording(null);
      setRecordingStatus(null);
      setRecordingDuration(0);
    } catch (error) {
      console.error('Failed to cancel recording:', error);
    }
  };

  if (!hasPermission) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionText}>
            Microphone permission is required to record audio
          </Text>
          <TouchableOpacity 
            style={styles.permissionButton} 
            onPress={checkPermissions}
          >
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Record Your Audio</Text>
      
      {isRecording && (
        <View style={styles.recordingInfo}>
          <Text style={styles.recordingText}>
            {STATUS_MESSAGES.RECORDING}
          </Text>
          <Text style={styles.durationText}>
            {formatDuration(recordingDuration)}
          </Text>
        </View>
      )}

      <View style={styles.buttonContainer}>
        {!isRecording ? (
          <TouchableOpacity
            style={[styles.recordButton, isLoading && styles.disabledButton]}
            onPress={startRecording}
            disabled={isLoading}
          >
            <Text style={styles.recordButtonText}>
              {isLoading ? 'Processing...' : 'Start Recording'}
            </Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.recordingControls}>
            <TouchableOpacity
              style={styles.stopButton}
              onPress={stopRecording}
            >
              <Text style={styles.stopButtonText}>Stop</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={cancelRecording}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <Text style={styles.helpText}>
        Tap "Start Recording" and play your instrument or sing. 
        The audio will be analyzed for chord progressions and key detection.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: SPACING.LG,
    backgroundColor: COLORS.SURFACE,
    borderRadius: 12,
    margin: SPACING.MD,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  title: {
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
    color: COLORS.TEXT_PRIMARY,
    textAlign: 'center',
    marginBottom: SPACING.MD,
  },
  permissionContainer: {
    alignItems: 'center',
    padding: SPACING.LG,
  },
  permissionText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    marginBottom: SPACING.MD,
  },
  permissionButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  recordingInfo: {
    alignItems: 'center',
    marginBottom: SPACING.LG,
  },
  recordingText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.ERROR,
    fontWeight: 'bold',
    marginBottom: SPACING.SM,
  },
  durationText: {
    fontSize: FONT_SIZES.XL,
    color: COLORS.TEXT_PRIMARY,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  buttonContainer: {
    alignItems: 'center',
    marginVertical: SPACING.LG,
  },
  recordButton: {
    backgroundColor: COLORS.PRIMARY,
    paddingHorizontal: SPACING.XL,
    paddingVertical: SPACING.LG,
    borderRadius: 50,
    minWidth: 150,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: COLORS.TEXT_SECONDARY,
  },
  recordButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
  },
  recordingControls: {
    flexDirection: 'row',
    gap: SPACING.MD,
  },
  stopButton: {
    backgroundColor: COLORS.ERROR,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 25,
    minWidth: 80,
    alignItems: 'center',
  },
  stopButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: COLORS.TEXT_SECONDARY,
    paddingHorizontal: SPACING.LG,
    paddingVertical: SPACING.MD,
    borderRadius: 25,
    minWidth: 80,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.MD,
    fontWeight: 'bold',
  },
  helpText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    marginTop: SPACING.MD,
    lineHeight: 20,
  },
});

export default AudioUploader;