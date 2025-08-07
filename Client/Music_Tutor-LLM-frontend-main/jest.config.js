module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: [
    '@testing-library/jest-native/extend-expect'
  ],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)'
  ],
  collectCoverageFrom: [
    'components/**/*.{js,jsx}',
    'screens/**/*.{js,jsx}',
    'services/**/*.{js,jsx}',
    'utils/**/*.{js,jsx}',
    'navigation/**/*.{js,jsx}',
    '!**/*.test.{js,jsx}',
    '!**/node_modules/**',
  ],
  testMatch: [
    '**/__tests__/**/*.{js,jsx}',
    '**/*.test.{js,jsx}',
  ],
};