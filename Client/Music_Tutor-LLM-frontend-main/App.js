import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import AppNavigator from './navigation/AppNavigator';
import ErrorBoundary from './components/common/ErrorBoundary';
import { COLORS } from './utils/constants';

export default function App() {
  return (
    <ErrorBoundary>
      <View style={styles.container}>
        <StatusBar style="light" backgroundColor={COLORS.BACKGROUND} />
        <AppNavigator />
      </View>
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
});