# HorizonJam Music Tutor Frontend

An AI-powered music learning companion built with React Native and Expo. Upload audio recordings to get real-time chord analysis and receive personalized guidance from your AI music tutor.

## Features

- 🎵 **Real-time Chord Analysis**: Upload audio to detect chords, key signatures, and progressions
- 🎯 **AI Music Guidance**: Get personalized tips and theory explanations from AI tutor
- 🔊 **Audio Playback**: Listen to text-to-speech guidance and your recordings
- 📱 **Cross-platform**: Works on iOS, Android, and Web
- 🎨 **Beautiful UI**: Clean, intuitive interface designed for musicians

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator (for iOS development)
- Android Studio/Emulator (for Android development)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HorizonJamFrontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure Backend URL**
   - Edit `services/apiService.js`
   - Update `API_BASE_URL` to point to your FastAPI backend
   ```javascript
   const API_BASE_URL = "http://your-backend-url.com";
   ```

## Running the App

### Development Mode

```bash
# Start Expo development server
expo start

# Or run directly on specific platform
expo start --web      # Web browser
expo start --ios      # iOS Simulator
expo start --android  # Android Emulator
```

### Platform-specific Commands

```bash
# iOS
npm run ios

# Android
npm run android

# Web
npm run web
```

## Project Structure

```
HorizonJamFrontend/
├── assets/                 # Images, audio, and other static assets
│   ├── images/
│   └── audio/
├── components/             # Reusable UI components
│   ├── common/            # Common utility components
│   ├── AudioUploader.js   # Audio recording/upload interface
│   ├── ChordDisplay.js    # Visual chord representation
│   ├── GuidanceText.js    # Display LLM guidance
│   └── PlayerControls.js  # Audio playback controls
├── screens/               # Main app screens
│   ├── HomeScreen.js      # Audio upload and main interface
│   ├── ChordAnalysisScreen.js  # Chord analysis results
│   └── GuidanceScreen.js  # Music guidance interface
├── services/              # API and external service integrations
│   ├── apiService.js      # Backend API communication
│   └── ttsService.js      # Text-to-speech functionality
├── utils/                 # Utility functions and constants
│   ├── helpers.js         # Helper functions
│   └── constants.js       # App constants and configuration
├── navigation/            # App navigation setup
│   └── AppNavigator.js    # Stack navigation configuration
├── App.js                 # Main app component
└── package.json           # Dependencies and scripts
```

## API Integration

The app expects a FastAPI backend with the following endpoints:

- `POST /upload` - Upload audio for chord analysis
- `POST /get-guidance` - Get AI music guidance
- `GET /health` - Health check endpoint

### Audio Upload Format

```javascript
{
  file: FormData, // Audio file (WAV, MP3, M4A, AAC)
}
```

### Guidance Request Format

```javascript
{
  question: string,
  context: {
    chordData?: object,
    conversationHistory?: array,
    focusChord?: object,
  }
}
```

## Configuration

### Environment Variables

Create an `.env` file in the root directory:

```
API_BASE_URL=http://localhost:8000
AUDIO_RECORDING_MAX_DURATION=300000
MAX_FILE_SIZE=52428800
```

### Audio Configuration

Edit `utils/constants.js` to modify audio recording settings:

```javascript
export const AUDIO_CONFIG = {
  RECORDING_OPTIONS: {
    // Platform-specific recording options
  },
  MAX_RECORDING_DURATION: 300000, // 5 minutes
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
};
```

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Building for Production

### Web Build

```bash
expo build:web
```

### iOS Build

```bash
expo build:ios
```

### Android Build

```bash
expo build:android
```

## Deployment

### Web Deployment

The app can be deployed to any static hosting service (Netlify, Vercel, GitHub Pages):

```bash
expo build:web
# Deploy the web-build/ directory
```

### App Store Deployment

1. Build the app using Expo build service
2. Download the generated IPA/APK files
3. Upload to respective app stores

## Troubleshooting

### Common Issues

1. **Audio Recording Permission Denied**
   - Ensure microphone permissions are granted
   - Check device audio settings

2. **Network Connection Errors**
   - Verify backend URL configuration
   - Check if backend server is running
   - Ensure device/emulator has internet access

3. **Audio Playback Issues**
   - Check audio file format compatibility
   - Verify TTS service is working
   - Test with different audio sources

### Debug Mode

```bash
# Enable debug logging
expo start --dev-client
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Open an issue on GitHub
- Check the [Expo documentation](https://docs.expo.dev/)
- Review [React Native documentation](https://reactnative.dev/docs/getting-started)

## Roadmap

- [ ] Offline mode support
- [ ] Advanced music theory features
- [ ] Social sharing capabilities
- [ ] Practice session tracking
- [ ] Custom chord library
- [ ] MIDI input support