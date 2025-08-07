// API Configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
};

// Audio Configuration
export const AUDIO_CONFIG = {
  RECORDING_OPTIONS: {
    android: {
      extension: '.wav',
      outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_DEFAULT,
      audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_DEFAULT,
      sampleRate: 44100,
      numberOfChannels: 2,
      bitRate: 128000,
    },
    ios: {
      extension: '.wav',
      outputFormat: Audio.RECORDING_OPTION_IOS_OUTPUT_FORMAT_LINEARPCM,
      audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH,
      sampleRate: 44100,
      numberOfChannels: 2,
      bitRate: 128000,
      linearPCMBitDepth: 16,
      linearPCMIsBigEndian: false,
      linearPCMIsFloat: false,
    },
  },
  MAX_RECORDING_DURATION: 300000, // 5 minutes in milliseconds
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
};

// Glass Morphism Theme - iOS 26 & Windows Vista Inspired
export const COLORS = {
  // Primary glass colors with transparency
  PRIMARY: '#4f46e5',        // Indigo with glass effect
  SECONDARY: '#7c3aed',      // Violet with glass effect
  ACCENT: '#06b6d4',         // Cyan accent
  
  // Glass background layers
  BACKGROUND: '#1a1a2e',                     // Dark gradient-like background
  SURFACE: 'rgba(255, 255, 255, 0.08)',     // Glass surface
  PANEL: 'rgba(255, 255, 255, 0.12)',       // Glass panel
  CARD: 'rgba(255, 255, 255, 0.1)',         // Glass card
  
  // Glass borders and overlays
  BORDER: 'rgba(255, 255, 255, 0.18)',      // Glass border
  BORDER_LIGHT: 'rgba(255, 255, 255, 0.25)', // Light glass border
  GLASS_OVERLAY: 'rgba(255, 255, 255, 0.05)', // Subtle overlay
  
  // Text colors optimized for glass
  TEXT_PRIMARY: '#ffffff',    // Pure white for contrast
  TEXT_SECONDARY: 'rgba(255, 255, 255, 0.9)', // Semi-transparent white
  TEXT_MUTED: 'rgba(255, 255, 255, 0.7)',     // Muted white
  TEXT_GLASS: 'rgba(255, 255, 255, 0.95)',    // Glass text
  
  // Status colors with glass effect
  SUCCESS: '#10b981',       // Emerald
  WARNING: '#f59e0b',       // Amber
  ERROR: '#ef4444',         // Red
  INFO: '#3b82f6',          // Blue
  
  // Music-specific glass colors
  CHORD: 'rgba(139, 92, 246, 0.8)',    // Purple with transparency
  NOTE: 'rgba(6, 182, 212, 0.8)',      // Cyan with transparency
  FRET: 'rgba(16, 185, 129, 0.8)',     // Emerald with transparency
  STRING: 'rgba(245, 158, 11, 0.8)',   // Amber with transparency
  FRETBOARD: 'rgba(45, 55, 72, 0.6)',  // Dark glass fretboard
  STRINGS: 'rgba(226, 232, 240, 0.9)', // Light glass strings
  
  // Advanced glass effects
  GLASS_LIGHT: 'rgba(255, 255, 255, 0.15)',
  GLASS_DARK: 'rgba(0, 0, 0, 0.1)',
  GLASS_BLUR: 'rgba(255, 255, 255, 0.08)',
  GLASS_SHINE: 'rgba(255, 255, 255, 0.3)',
  
  // Shadow effects for depth
  SHADOW_LIGHT: 'rgba(0, 0, 0, 0.1)',
  SHADOW_MEDIUM: 'rgba(0, 0, 0, 0.15)',
  SHADOW_STRONG: 'rgba(0, 0, 0, 0.25)',
  SHADOW_GLASS: 'rgba(0, 0, 0, 0.08)',
  
  // Glass overlays (React Native compatible)
  GRADIENT_PRIMARY: 'rgba(79, 70, 229, 0.8)',
  GRADIENT_SECONDARY: 'rgba(6, 182, 212, 0.6)',
  GRADIENT_GLASS: 'rgba(255, 255, 255, 0.08)',
};

export const SPACING = {
  XS: 4,
  SM: 8,
  MD: 16,
  LG: 24,
  XL: 32,
  XXL: 48,
};

export const FONT_SIZES = {
  XS: 12,
  SM: 14,
  MD: 16,
  LG: 18,
  XL: 24,
  XXL: 32,
};

// Music Theory Constants
export const MUSIC_CONSTANTS = {
  NOTES: ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'],
  CHORD_TYPES: [
    'Major', 'Minor', 'Diminished', 'Augmented', 
    'Major 7th', 'Minor 7th', 'Dominant 7th', 'Half-diminished 7th'
  ],
  KEYS: [
    'C Major', 'G Major', 'D Major', 'A Major', 'E Major', 'B Major',
    'F# Major', 'C# Major', 'F Major', 'Bb Major', 'Eb Major', 'Ab Major',
    'Db Major', 'Gb Major', 'Cb Major', 'A Minor', 'E Minor', 'B Minor',
    'F# Minor', 'C# Minor', 'G# Minor', 'D# Minor', 'A# Minor', 'D Minor',
    'G Minor', 'C Minor', 'F Minor', 'Bb Minor', 'Eb Minor', 'Ab Minor'
  ],
};

// Screen Names for Navigation
export const SCREENS = {
  HOME: 'Home',
  CHORD_ANALYSIS: 'ChordAnalysis',
  GUIDANCE: 'Guidance',
};

// Status Messages
export const STATUS_MESSAGES = {
  LOADING: 'Loading...',
  RECORDING: 'Recording...',
  PROCESSING: 'Processing audio...',
  ANALYZING: 'Analyzing chords...',
  GENERATING_GUIDANCE: 'Generating guidance...',
  READY: 'Ready',
  ERROR: 'An error occurred',
  SUCCESS: 'Success!',
  NO_AUDIO: 'No audio detected',
  INVALID_FILE: 'Invalid audio file',
  NETWORK_ERROR: 'Network connection error',
  PERMISSION_DENIED: 'Microphone permission denied',
};