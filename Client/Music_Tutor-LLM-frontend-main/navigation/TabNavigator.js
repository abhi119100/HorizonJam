import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text } from 'react-native';
import HomeScreen from '../screens/HomeScreen';
import ChordAnalysisScreen from '../screens/ChordAnalysisScreen';
import RAGChatScreen from '../screens/RAGChatScreen';
import { COLORS, FONT_SIZES } from '../utils/constants';

const Tab = createBottomTabNavigator();

// Simple icon components (since vector icons might need additional setup)
const HomeIcon = ({ focused }) => (
  <View style={{ alignItems: 'center', justifyContent: 'center' }}>
    <Text style={{ 
      fontSize: 20, 
      color: focused ? COLORS.PRIMARY : COLORS.TEXT_MUTED 
    }}>
      🏠
    </Text>
  </View>
);

const AnalysisIcon = ({ focused }) => (
  <View style={{ alignItems: 'center', justifyContent: 'center' }}>
    <Text style={{ 
      fontSize: 20, 
      color: focused ? COLORS.PRIMARY : COLORS.TEXT_MUTED 
    }}>
      🎵
    </Text>
  </View>
);

const ChatIcon = ({ focused }) => (
  <View style={{ alignItems: 'center', justifyContent: 'center' }}>
    <Text style={{ 
      fontSize: 20, 
      color: focused ? COLORS.PRIMARY : COLORS.TEXT_MUTED 
    }}>
      🤖
    </Text>
  </View>
);

export default function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: COLORS.SURFACE,
          borderTopColor: COLORS.PANEL,
          borderTopWidth: 1,
          height: 70,
          paddingBottom: 10,
          paddingTop: 10,
        },
        tabBarActiveTintColor: COLORS.PRIMARY,
        tabBarInactiveTintColor: COLORS.TEXT_MUTED,
        tabBarLabelStyle: {
          fontSize: FONT_SIZES.SM,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: COLORS.SURFACE,
          borderBottomColor: COLORS.PANEL,
          borderBottomWidth: 1,
        },
        headerTintColor: COLORS.TEXT_PRIMARY,
        headerTitleStyle: {
          fontWeight: 'bold',
          fontSize: FONT_SIZES.LG,
        },
      }}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          title: 'Record',
          tabBarIcon: HomeIcon,
          headerShown: false,
        }}
      />
      <Tab.Screen 
        name="Analysis" 
        component={ChordAnalysisScreen}
        options={{
          title: 'Analysis',
          tabBarIcon: AnalysisIcon,
          headerTitle: 'Chord Analysis',
        }}
      />
      <Tab.Screen 
        name="RAGChat" 
        component={RAGChatScreen}
        options={{
          title: 'Music Tutor',
          tabBarIcon: ChatIcon,
          headerTitle: 'AI Music Tutor',
        }}
      />
    </Tab.Navigator>
  );
}