import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import TabNavigator from './TabNavigator';
import GuidanceScreen from '../screens/GuidanceScreen';
import { COLORS } from '../utils/constants';

const Stack = createStackNavigator();

// Dark theme for navigation
const DarkTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: COLORS.PRIMARY,
    backgroundColor: COLORS.BACKGROUND,
    card: COLORS.SURFACE,
    text: COLORS.TEXT_PRIMARY,
    border: COLORS.PANEL,
    notification: COLORS.ACCENT,
  },
};

export default function AppNavigator() {
  return (
    <NavigationContainer theme={DarkTheme}>
      <Stack.Navigator
        initialRouteName="MainTabs"
        screenOptions={{
          headerStyle: {
            backgroundColor: COLORS.SURFACE,
            borderBottomWidth: 1,
            borderBottomColor: COLORS.PANEL,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTintColor: COLORS.TEXT_PRIMARY,
          headerTitleStyle: {
            fontWeight: 'bold',
            fontSize: 18,
          },
          headerBackTitleVisible: false,
          headerLeftContainerStyle: {
            paddingLeft: 16,
          },
          headerRightContainerStyle: {
            paddingRight: 16,
          },
        }}
      >
        <Stack.Screen 
          name="MainTabs" 
          component={TabNavigator}
          options={{ 
            headerShown: false // Hide header for tab navigator
          }}
        />
        <Stack.Screen 
          name="Guidance" 
          component={GuidanceScreen}
          options={{ 
            title: 'Music Guidance',
            headerStyle: {
              backgroundColor: COLORS.SURFACE,
              borderBottomWidth: 1,
              borderBottomColor: COLORS.PANEL,
            },
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}