import React, { useState } from 'react';
import './App.css';
import SongStructure from './components/SongStructure';
import GuitarChord from './components/GuitarChord';
import GuitarFretboard from './components/GuitarFretboard';
import InstructorPanel from './components/InstructorPanel';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [selectedChord, setSelectedChord] = useState('Em');
  const [currentChordProgression] = useState(['Em', 'Am', 'D', 'G']);

  const handleMicrophonePress = () => {
    setIsRecording(!isRecording);
    console.log('Microphone pressed, recording:', !isRecording);
  };

  const handleChordSelection = (chord: string) => {
    setSelectedChord(chord);
    console.log('Selected chord:', chord);
  };

  const handleSectionPress = (section: any) => {
    console.log('Selected section:', section);
  };

  return (
    <div className="app">
      {/* App Bar */}
      <div className="app-bar">
        <h1 className="app-title">Horizon Jam</h1>
        <div className="status-container">
          <div className="status-indicator online"></div>
          <span className="status-text">Server Online</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Left Panel - Instructor */}
        <div className="left-panel">
          <InstructorPanel 
            message="Hello! Do you want to play a song?"
            onMicrophonePress={handleMicrophonePress}
            isListening={isRecording}
          />
        </div>

        {/* Center Panel - Song Structure */}
        <div className="center-panel">
          <SongStructure onSectionPress={handleSectionPress} />
        </div>

        {/* Right Panel - Chord & Tutor */}
        <div className="right-panel">
          <div className="chord-section">
            <h3 className="section-title">Chord</h3>
            <GuitarChord 
              chordName={selectedChord}
              size="large"
              onPress={() => console.log('Chord pressed')}
            />
          </div>
          
          <div className="tutor-section">
            <InstructorPanel 
              avatar="tutor"
              message={`Tell the user to play the peace of the ${currentChordProgression.join(', ')} shapes`}
              showMicrophone={false}
            />
          </div>
        </div>
      </div>

      {/* Bottom Panel - Guitar Fretboard */}
      <div className="bottom-panel">
        <GuitarFretboard 
          chordProgression={currentChordProgression}
          onChordPress={handleChordSelection}
          highlightedChord={selectedChord}
        />
      </div>
    </div>
  );
}

export default App;