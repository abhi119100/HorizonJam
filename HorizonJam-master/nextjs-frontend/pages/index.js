import { useEffect, useRef, useState, useMemo } from "react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [analysisData, setAnalysisData] = useState(null);
  const [tutoringText, setTutoringText] = useState("");
  const wsRef = useRef(null);
  const audioQueue = useRef([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const hiddenFileRef = useRef(null);

  // Backend endpoints (configurable via Next.js env)
  const TUTOR_WS_URL = process.env.NEXT_PUBLIC_TUTOR_WS_URL || "ws://localhost:8001/ws/tutor";
  const UPLOAD_URL = process.env.NEXT_PUBLIC_UPLOAD_URL || "http://localhost:8001/upload-audio";
  const TTS_URL = process.env.NEXT_PUBLIC_TTS_URL || "http://localhost:5000/tts";

  // Derived UI data
  const uniqueChords = useMemo(() => {
    if (!analysisData || !analysisData.chord_events) return [];
    const list = analysisData.chord_events
      .map(ev => ev.chord || ev.chord_symbol)
      .filter(Boolean)
      .filter(c => c !== 'N');
    return Array.from(new Set(list)).slice(0, 8);
  }, [analysisData]);

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
        if (audioQueue.current.length > 0) {
          const nextAudio = audioQueue.current.shift();
          playAudioBuffer(nextAudio);
        }
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
    }
  };

  // Connect WebSocket lazily
  const connectWS = () => {
    if (wsRef.current && wsRef.current.readyState === 1) return;
    const ws = new WebSocket(TUTOR_WS_URL);

    ws.onopen = () => setStatus("🔗 Connected");
    ws.onerror = () => setStatus("❌ WebSocket error");
    ws.onclose = () => setStatus("🔌 Disconnected");

    ws.onmessage = (evt) => {
      if (evt.data instanceof Blob) {
        evt.data.arrayBuffer().then(audioData => {
          if (isPlaying) {
            audioQueue.current.push(audioData);
          } else {
            playAudioBuffer(audioData);
          }
        });
        return;
      }

      if (typeof evt.data === 'string') {
        try {
          const msg = JSON.parse(evt.data);
          switch (msg.type) {
            case "status":
              setStatus(msg.message);
              break;
            case "error":
              setStatus("❌ " + msg.message);
              break;
            case "chord_analysis":
              setAnalysis(JSON.stringify(msg.data, null, 2));
              setAnalysisData(msg.data);
              break;
            case "text_chunk":
              setTutoringText((prev) => prev + msg.text);
              break;
            case "complete":
              setStatus("✅ Analysis complete!");
              break;
            default:
              break;
          }
        } catch (error) {
          setTutoringText((prev) => prev + evt.data);
        }
      }
    };

    wsRef.current = ws;
  };

  // Upload audio then trigger analysis via WS
  const handleAnalyze = async () => {
    if (!file) {
      hiddenFileRef.current?.click();
      return;
    }

    setAnalysis("");
    setAnalysisData(null);
    setTutoringText("");
    audioQueue.current = [];
    setIsPlaying(false);

    connectWS();
    const formData = new FormData();
    formData.append("audio_file", file);
    if (question.trim()) formData.append("question", question.trim());
    setStatus("⬆️ Uploading...");

    try {
      const res = await fetch(UPLOAD_URL, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setStatus("📡 Analyzing...");
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
      const res = await fetch(TTS_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`TTS failed (${res.status}): ${errText}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      await audio.play();
    } catch (err) {
      console.error(err);
      setStatus("TTS error: " + err.message);
    }
  };

  const stopAudio = () => {
    audioQueue.current = [];
    setIsPlaying(false);
  };

  useEffect(() => () => wsRef.current?.close(), []);

  // Styles (inline for simplicity)
  const colors = {
    bg: "#0f141a",
    panel: "#141a21",
    border: "#1f2a36",
    text: "#e6edf3",
    subtext: "#9aa7b2",
    accent: "#18a4c9",
    accentSoft: "#0f6e84",
    orange: "#ff9f43",
  };

  const Card = ({ title, children, style }) => (
    <div style={{
      background: colors.panel,
      border: `1px solid ${colors.border}`,
      borderRadius: 16,
      padding: 20,
      color: colors.text,
      ...style
    }}>
      {title && <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>{title}</div>}
      {children}
    </div>
  );

  const Nav = () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, padding: 16, color: colors.text }}>
      <div style={{ display: 'flex', gap: 20, fontWeight: 700 }}>
        <span>Home</span>
        <span style={{ color: colors.subtext }}>Library</span>
        <span style={{ color: colors.subtext }}>Coach</span>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{
        background: colors.panel,
        border: `1px solid ${colors.border}`,
        borderRadius: 24,
        padding: '8px 14px',
        color: colors.subtext,
        minWidth: 280
      }}>
        Upload audio or search songs
      </div>
    </div>
  );

  const StartButton = (
    <button
      onClick={handleAnalyze}
      style={{
        background: colors.accent,
        border: 'none',
        color: 'white',
        padding: '14px 18px',
        borderRadius: 12,
        fontWeight: 700,
        fontSize: 18,
        cursor: 'pointer',
        width: '100%'
      }}
    >
      Start Playing
    </button>
  );

  const ChordPills = (
    <div style={{ display: 'flex', gap: 16, marginTop: 18, flexWrap: 'wrap' }}>
      {uniqueChords.length === 0 ? (
        ["Am", "F", "C", "G"].map((c, i) => (
          <div key={i} style={{ color: colors.text, fontWeight: 700 }}>{c}</div>
        ))
      ) : (
        uniqueChords.map((c, i) => (
          <div key={i} style={{ color: colors.text, fontWeight: 700 }}>{c}</div>
        ))
      )}
    </div>
  );

  const StudioCanvas = (
    <Card title="Studio Canvas" style={{ minHeight: 320 }}>
      <div style={{ marginBottom: 16 }}>{StartButton}</div>
      {ChordPills}
      <div style={{ display: 'flex', gap: 16, marginTop: 18 }}>
        {(uniqueChords.length ? uniqueChords.slice(0,4) : ["Am","F","C","G"]).map((c,i)=> (
          <div key={i} style={{
            width: 72, height: 96, border: `1px solid ${colors.border}`, borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.subtext
          }}>{c}</div>
        ))}
      </div>
    </Card>
  );

  const chordExplain = tutoringText ||
    `Your AI tutor will appear here. Upload audio and press Start Playing to analyze; you'll see live explanations and can play a single spoken summary.`;

  const AICompanion = (
    <Card title="AI Companion Chat" style={{ minHeight: 420 }}>
      <div style={{
        background: colors.accentSoft,
        color: colors.text,
        display: 'inline-block',
        padding: '10px 14px',
        borderRadius: 12,
        marginBottom: 14
      }}>
        Live Tutor
      </div>
      <div style={{ color: colors.subtext, lineHeight: 1.6, whiteSpace: 'pre-wrap', maxHeight: 280, overflowY: 'auto' }}>
        {chordExplain}
      </div>
      <div style={{ marginTop: 12, display:'flex', gap: 10 }}>
        <button onClick={() => handleTTS(chordExplain)} style={{
          background: colors.accent, border: 'none', color: 'white', padding: '10px 12px', borderRadius: 8, cursor: 'pointer'
        }}>🔊 Speak</button>
        <button onClick={stopAudio} style={{
          background: '#4b5563', border: 'none', color: 'white', padding: '10px 12px', borderRadius: 8, cursor: 'pointer'
        }}>⏹️ Stop</button>
      </div>
    </Card>
  );

  // Analysis detail views (progression, timeline, chord tabs)
  const ProgressionCard = (
    <Card title="Chord Progression">
      <div style={{ color: colors.subtext }}>
        {analysisData?.analysis_summary?.chord_progression
          ? analysisData.analysis_summary.chord_progression
          : (uniqueChords.length ? uniqueChords.join(' - ') : 'No progression detected yet')}
      </div>
    </Card>
  );

  const TimelineCard = (
    <Card title="Chord Timeline">
      <div style={{ maxHeight: 220, overflowY: 'auto' }}>
        {(analysisData?.chord_events?.length ? analysisData.chord_events : []).map((ev, idx) => {
          const rawStart = ev.start_time ?? ev.start ?? ev.time ?? 0;
          const rawEnd = ev.end_time ?? ev.end ?? (ev.duration != null ? (Number(rawStart) + Number(ev.duration)) : rawStart);
          const start = Number.isFinite(Number(rawStart)) ? Number(rawStart).toFixed(2) : '0.00';
          const end = Number.isFinite(Number(rawEnd)) ? Number(rawEnd).toFixed(2) : '0.00';
          const name = ev.chord || ev.chord_symbol || 'N';
          if (name === 'N') return null;
          return (
            <div key={idx} style={{
              display: 'flex', alignItems: 'center', padding: '6px 8px',
              borderBottom: `1px solid ${colors.border}`
            }}>
              <div style={{ width: 64, color: colors.subtext }}>
                {String(idx + 1).padStart(2, '0')}.
              </div>
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: 700 }}>{name}</span>
                <span style={{ color: colors.subtext }}>  [{start} - {end}]</span>
              </div>
            </div>
          );
        })}
        {!analysisData?.chord_events?.length && (
          <div style={{ color: colors.subtext }}>No timeline available yet</div>
        )}
      </div>
    </Card>
  );

  const TabsCard = (
    <Card title="Guitar Chord Tabs">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
        {(analysisData?.guitar_tabs?.length ? analysisData.guitar_tabs : (uniqueChords.map(c => ({ chord: c, full_tab: '', difficulty: '', compact_notation: '' })))).map((tab, idx) => (
          <div key={idx} style={{
            background: '#0b1116', border: `1px solid ${colors.border}`, borderRadius: 12, padding: 12
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 800 }}>[GUITAR] {tab.chord} Chord</div>
              <div style={{ color: colors.subtext, fontSize: 12 }}>{tab.compact_notation || ''}</div>
            </div>
            {tab.difficulty && (
              <div style={{ color: colors.subtext, fontSize: 12, marginTop: 6 }}>{tab.difficulty}</div>
            )}
            <pre style={{ whiteSpace: 'pre-wrap', marginTop: 8, color: colors.text }}>
{(tab.full_tab && tab.full_tab.trim()) ? tab.full_tab : `E |-----\nA |-----\nD |-----\nG |-----\nB |-----\nE |-----`}
            </pre>
          </div>
        ))}
      </div>
    </Card>
  );

  const ContentCard = ({ icon, title, subtitle }) => (
    <div style={{
      background: colors.panel,
      border: `1px solid ${colors.border}`,
      borderRadius: 16,
      padding: 18,
      width: 300,
      color: colors.text
    }}>
      <div style={{ fontSize: 28, color: colors.orange }}>{icon}</div>
      <div style={{ fontWeight: 800, marginTop: 10 }}>{title}</div>
      <div style={{ color: colors.subtext, marginTop: 6 }}>{subtitle}</div>
    </div>
  );

  return (
    <div style={{ background: colors.bg, minHeight: '100vh', color: colors.text }}>
      <Nav />

      {/* Hidden file input to keep logic unchanged */}
      <input
        ref={hiddenFileRef}
        type="file"
        accept=".wav,.mp3,.m4a"
        onChange={(e) => {
          const f = e.target.files?.[0] || null;
          setFile(f);
          if (f) handleAnalyze();
        }}
        style={{ display: 'none' }}
      />

      {/* Controls row (search + question) */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '6px 20px 16px' }}>
        <input
          placeholder="Optional question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{
            width: '100%', padding: 12, borderRadius: 10, background: colors.panel,
            border: `1px solid ${colors.border}`, color: colors.text
          }}
        />
        <div style={{ marginTop: 8, color: colors.subtext, fontSize: 12 }}>{status}</div>
      </div>

      {/* Main section: Studio Canvas */}
      <div style={{
        maxWidth: 1100,
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: 20,
        padding: '0 20px'
      }}>
        {StudioCanvas}
      </div>

      {/* Analysis details (above AI Companion) */}
      <div style={{ maxWidth: 1100, margin: '26px auto 20px', padding: '0 20px' }}>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 20 }}>
          {ProgressionCard}
          {TimelineCard}
        </div>
        <div style={{ marginTop: 20 }}>
          {TabsCard}
        </div>
      </div>

      {/* AI Companion Chat at the bottom */}
      <div style={{
        maxWidth: 1100,
        margin: '0 auto 40px',
        padding: '0 20px'
      }}>
        {AICompanion}
      </div>

      {/* Developer info panel (collapsed UI state) */}
      <div style={{ maxWidth: 1100, margin: '0 auto 40px', padding: '0 20px', color: colors.subtext }}>
        <details>
          <summary style={{ cursor: 'pointer' }}>Developer state</summary>
          <pre style={{ whiteSpace: 'pre-wrap', marginTop: 10 }}>{analysis}</pre>
          <div style={{ marginTop: 8, fontSize: 12 }}>Audio Queue: {audioQueue.current.length} | Playing: {isPlaying ? 'Yes' : 'No'}</div>
        </details>
      </div>
    </div>
  );
}