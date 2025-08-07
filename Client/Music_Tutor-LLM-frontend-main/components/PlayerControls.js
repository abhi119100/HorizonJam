import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Slider,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../utils/constants';
import { formatDuration } from '../utils/helpers';
import { 
  playAudioFromUrl, 
  playLocalAudio, 
  stopAudio, 
  pauseAudio, 
  resumeAudio 
} from '../services/ttsService';

const PlayerControls = ({ 
  audioUrl = null, 
  localAudioUri = null, 
  autoPlay = false,
  onPlaybackStatusChange = null 
}) => {
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (autoPlay && (audioUrl || localAudioUri)) {
      handlePlay();
    }

    return () => {
      if (sound) {
        stopAudio(sound);
      }
    };
  }, [audioUrl, localAudioUri]);

  useEffect(() => {
    if (onPlaybackStatusChange) {
      onPlaybackStatusChange({
        isPlaying,
        position,
        duration,
        error,
      });
    }
  }, [isPlaying, position, duration, error]);

  const setupSound = async () => {
    try {
      setIsLoading(true);
      setError(null);

      let newSound;
      if (audioUrl) {
        newSound = await playAudioFromUrl(audioUrl);
      } else if (localAudioUri) {
        newSound = await playLocalAudio(localAudioUri);
      } else {
        throw new Error('No audio source provided');
      }

      // Set up status update listener
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded) {
          setPosition(status.positionMillis || 0);
          setDuration(status.durationMillis || 0);
          setIsPlaying(status.isPlaying || false);

          // Handle playback completion
          if (status.didJustFinish) {
            setIsPlaying(false);
            setPosition(0);
          }
        } else if (status.error) {
          setError(status.error);
          setIsPlaying(false);
        }
      });

      setSound(newSound);
      setIsPlaying(true);
    } catch (err) {
      console.error('Error setting up sound:', err);
      setError(err.message);
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlay = async () => {
    if (!sound) {
      await setupSound();
    } else {
      try {
        await resumeAudio(sound);
        setIsPlaying(true);
        setError(null);
      } catch (err) {
        console.error('Error resuming audio:', err);
        setError(err.message);
      }
    }
  };

  const handlePause = async () => {
    if (sound) {
      try {
        await pauseAudio(sound);
        setIsPlaying(false);
        setError(null);
      } catch (err) {
        console.error('Error pausing audio:', err);
        setError(err.message);
      }
    }
  };

  const handleStop = async () => {
    if (sound) {
      try {
        await stopAudio(sound);
        setSound(null);
        setIsPlaying(false);
        setPosition(0);
        setError(null);
      } catch (err) {
        console.error('Error stopping audio:', err);
        setError(err.message);
      }
    }
  };

  const handleSeek = async (value) => {
    if (sound && duration > 0) {
      try {
        const seekPosition = (value / 100) * duration;
        await sound.setPositionAsync(seekPosition);
        setPosition(seekPosition);
        setError(null);
      } catch (err) {
        console.error('Error seeking audio:', err);
        setError(err.message);
      }
    }
  };

  if (!audioUrl && !localAudioUri) {
    return (
      <View style={styles.container}>
        <Text style={styles.noAudioText}>
          No audio available for playback
        </Text>
      </View>
    );
  }

  const sliderValue = duration > 0 ? (position / duration) * 100 : 0;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Audio Playback</Text>
      
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Playback Error: {error}</Text>
        </View>
      )}

      {/* Progress Slider */}
      <View style={styles.progressContainer}>
        <Text style={styles.timeText}>{formatDuration(position)}</Text>
        <Slider
          style={styles.slider}
          minimumValue={0}
          maximumValue={100}
          value={sliderValue}
          onSlidingComplete={handleSeek}
          minimumTrackTintColor={COLORS.PRIMARY}
          maximumTrackTintColor={COLORS.TEXT_SECONDARY}
          thumbStyle={styles.sliderThumb}
          disabled={!sound || duration === 0}
        />
        <Text style={styles.timeText}>{formatDuration(duration)}</Text>
      </View>

      {/* Control Buttons */}
      <View style={styles.controlsContainer}>
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.PRIMARY} />
            <Text style={styles.loadingText}>Loading audio...</Text>
          </View>
        ) : (
          <View style={styles.buttonRow}>
            {!isPlaying ? (
              <TouchableOpacity
                style={[styles.controlButton, styles.playButton]}
                onPress={handlePlay}
                disabled={isLoading}
              >
                <Text style={styles.controlButtonText}>▶</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[styles.controlButton, styles.pauseButton]}
                onPress={handlePause}
              >
                <Text style={styles.controlButtonText}>⏸</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[styles.controlButton, styles.stopButton]}
              onPress={handleStop}
              disabled={!sound}
            >
              <Text style={styles.controlButtonText}>⏹</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Status Display */}
      <View style={styles.statusContainer}>
        <Text style={styles.statusText}>
          {isLoading ? 'Loading...' : 
           isPlaying ? 'Playing' : 
           sound ? 'Paused' : 'Ready'}
        </Text>
        {audioUrl && (
          <Text style={styles.sourceText}>Remote Audio</Text>
        )}
        {localAudioUri && (
          <Text style={styles.sourceText}>Local Recording</Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.SURFACE,
    padding: SPACING.LG,
    margin: SPACING.MD,
    borderRadius: 12,
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
  noAudioText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_SECONDARY,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorContainer: {
    backgroundColor: COLORS.ERROR,
    padding: SPACING.SM,
    borderRadius: 6,
    marginBottom: SPACING.MD,
  },
  errorText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.SM,
    textAlign: 'center',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: SPACING.MD,
  },
  timeText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
    fontFamily: 'monospace',
    minWidth: 50,
  },
  slider: {
    flex: 1,
    height: 40,
    marginHorizontal: SPACING.SM,
  },
  sliderThumb: {
    backgroundColor: COLORS.PRIMARY,
    width: 20,
    height: 20,
  },
  controlsContainer: {
    alignItems: 'center',
    marginVertical: SPACING.MD,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: SPACING.MD,
  },
  loadingText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
    marginTop: SPACING.SM,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: SPACING.LG,
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  playButton: {
    backgroundColor: COLORS.SUCCESS,
  },
  pauseButton: {
    backgroundColor: COLORS.WARNING,
  },
  stopButton: {
    backgroundColor: COLORS.ERROR,
  },
  controlButtonText: {
    color: COLORS.SURFACE,
    fontSize: FONT_SIZES.LG,
    fontWeight: 'bold',
  },
  statusContainer: {
    alignItems: 'center',
    marginTop: SPACING.MD,
    paddingTop: SPACING.MD,
    borderTopWidth: 1,
    borderTopColor: COLORS.BACKGROUND,
  },
  statusText: {
    fontSize: FONT_SIZES.MD,
    color: COLORS.TEXT_PRIMARY,
    fontWeight: '500',
    marginBottom: SPACING.XS,
  },
  sourceText: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.TEXT_SECONDARY,
  },
});

export default PlayerControls;