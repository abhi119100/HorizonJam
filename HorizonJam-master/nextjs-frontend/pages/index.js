import { useEffect, useRef, useState } from "react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [tutoringText, setTutoringText] = useState("");
  const wsRef = useRef(null);
  const audioQueue = useRef([]);
  const [isPlaying, setIsPlaying] = useState(false);

  // Play audio from buffer
  const playAudioBuffer = async (audioData) => {
    try {
      setIsPlaying(true);
      const blob = new Blob([audioData], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setIsPlaying(false);
        // Play next audio in queue
        if (audioQueue.current.length > 0) {
          const nextAudio = audioQueue.current.shift();
          playAudioBuffer(nextAudio);
        }
      };
      
      await audio.play();
      console.log('🔊 Playing TTS audio');
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
    }
  };

  // Connect WebSocket lazily
  const connectWS = () => {
    if (wsRef.current && wsRef.current.readyState === 1) return;
    const ws = new WebSocket("ws://localhost:8001/ws/tutor");
    
    ws.onopen = () => setStatus("🔗 WebSocket connected");
    ws.onerror = () => setStatus("❌ WebSocket error");
    ws.onclose = () => setStatus("🔌 WebSocket closed");
    
    ws.onmessage = (evt) => {
      // Handle binary audio data (Blob)
      if (evt.data instanceof Blob) {
        console.log('📦 Received audio blob:', evt.data.size, 'bytes');
        evt.data.arrayBuffer().then(audioData => {
          if (isPlaying) {
            // Queue audio if currently playing
            audioQueue.current.push(audioData);
            console.log('🎵 Queued audio, queue length:', audioQueue.current.length);
          } else {
            // Play immediately
            playAudioBuffer(audioData);
          }
        });
        return;
      }
      
      // Handle text messages (JSON)
      if (typeof evt.data === 'string') {
        try {
          const msg = JSON.parse(evt.data);
          console.log('📨 Received message:', msg.type);
          
          switch (msg.type) {
            case "status":
              setStatus(msg.message);
              break;
            case "error":
              setStatus("❌ " + msg.message);
              break;
            case "chord_analysis":
              setAnalysis(JSON.stringify(msg.data, null, 2));
              break;
            case "rag_context":
              console.log("📚 RAG Context received:", msg.data.total_docs, "documents");
              break;
            case "text_chunk":
              console.log('📝 Text chunk:', msg.text);
              setTutoringText((prev) => prev + msg.text);
              break;
            case "complete":
              setStatus("✅ Analysis complete!");
              console.log('🎉 Analysis completed');
              break;
            default:
              console.log("❓ Unknown message type:", msg.type);
          }
        } catch (error) {
          // If JSON parsing fails, treat as plain text
          console.log('📄 Received plain text:', evt.data);
          setTutoringText((prev) => prev + evt.data);
        }
      }
    };
    
    wsRef.current = ws;
  };

  // Upload audio then trigger analysis via WS
  const handleAnalyze = async () => {
    if (!file) {
      setStatus("Please choose a file");
      return;
    }
    
    // Clear previous results
    setAnalysis("");
    setTutoringText("");
    audioQueue.current = [];
    setIsPlaying(false);
    
    connectWS();
    const formData = new FormData();
    formData.append("audio_file", file);
    if (question.trim()) formData.append("question", question.trim());
    setStatus("⬆️ Uploading...");
    
    try {
      const res = await fetch("http://localhost:8001/upload-audio", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setStatus("📡 Sending analyze request...");
        wsRef.current?.send(
          JSON.stringify({
            type: "analyze",
            file_path: data.file_path,
            question: question.trim() || null,
          })
        );
      } else {
        setStatus("Upload failed: " + data.error);
      }
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  // Call TTS endpoint (returns wav) and play
  const handleTTS = async (text) => {
    try {
      const res = await fetch("http://localhost:5000/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();
    } catch (err) {
      console.error(err);
      setStatus("TTS error: " + err.message);
    }
  };

  const stopAudio = () => {
    audioQueue.current = [];
    setIsPlaying(false);
    console.log('⏹️ Audio stopped');
  };

  useEffect(() => () => wsRef.current?.close(), []);

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h1>🎸 ChordAI Tutor (Next.js Frontend)</h1>
      <input
        type="file"
        accept=".wav,.mp3,.m4a"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <br />
      <input
        style={{ width: "100%", marginTop: 10 }}
        placeholder="Optional question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <br />
      <button onClick={handleAnalyze} style={{ marginTop: 10 }}>
        🎵 Analyze & Stream
      </button>
      <button
        onClick={() => handleTTS(tutoringText || "Hello from ChordAI")}
        style={{ marginLeft: 10 }}
      >
        🔊 Speak
      </button>
      <button onClick={stopAudio} style={{ marginLeft: 10 }}>
        ⏹️ Stop Audio
      </button>
      <p>{status}</p>
      <h3>Chord Analysis</h3>
      <pre style={{ whiteSpace: "pre-wrap" }}>{analysis}</pre>
      <h3>Tutoring Explanation {isPlaying && "🔊"}</h3>
      <p>{tutoringText}</p>
      <div style={{ marginTop: 20, fontSize: 12, color: '#666' }}>
        Audio Queue: {audioQueue.current.length} | Playing: {isPlaying ? 'Yes' : 'No'}
      </div>
    </div>
  );
}