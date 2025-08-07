import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../../utils/constants';

const LoadingSpinner = ({ 
  size = 'large', 
  color = COLORS.PRIMARY, 
  text = 'Loading...',
  showText = true 
}) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color={color} />
      {showText && (
        <Text style={[styles.text, { color }]}>{text}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.LG,
  },
  text: {
    fontSize: FONT_SIZES.MD,
    marginTop: SPACING.SM,
    textAlign: 'center',
  },
});

export default LoadingSpinner;