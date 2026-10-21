import { useEffect, useRef, useState, useMemo, useCallback } from "react";

const MAX_RECORD_SECS = 30;
const MIN_RECORD_SECS = 3;
const TARGET_SR = 44100;

// AudioBuffer -> mono 16-bit PCM WAV (Uint8Array). Pure, no React.
// Bypasses server-side ffmpeg by encoding WAV in the browser directly.
function audioBufferToWav(audioBuffer, targetSampleRate) {
  const numCh = audioBuffer.numberOfChannels;
  let mono;
  if (numCh === 1) {
    mono = audioBuffer.getChannelData(0);
  } else {
    // Average all channels into mono
    const len = audioBuffer.length;
    mono = new Float32Array(len);
    for (let c = 0; c < numCh; c++) {
      const ch = audioBuffer.getChannelData(c);
      for (let i = 0; i < len; i++) mono[i] += ch[i];
    }
    for (let i = 0; i < len; i++) mono[i] /= numCh;
  }

  // Linear-interpolation resample if target rate differs.
  // Good enough for chord detection; not audiophile-grade.
  const srcRate = audioBuffer.sampleRate;
  const outRate = targetSampleRate || srcRate;
  let pcm = mono;
  if (outRate !== srcRate) {
    const ratio = srcRate / outRate;
    const newLen = Math.floor(mono.length / ratio);
    pcm = new Float32Array(newLen);
    for (let i = 0; i < newLen; i++) {
      const idx = i * ratio;
      const i0 = Math.floor(idx);
      const i1 = Math.min(i0 + 1, mono.length - 1);
      const f = idx - i0;
      pcm[i] = mono[i0] * (1 - f) + mono[i1] * f;
    }
  }

  const numSamples = pcm.length;
  const dataBytes = numSamples * 2; // 16-bit
  const buffer = new ArrayBuffer(44 + dataBytes);
  const view = new DataView(buffer);
  const writeStr = (off, s) => {
    for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i));
  };

  // RIFF header
  writeStr(0, "RIFF");
  view.setUint32(4, 36 + dataBytes, true);
  writeStr(8, "WAVE");
  // fmt chunk
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);     // subchunk size
  view.setUint16(20, 1, true);      // PCM format
  view.setUint16(22, 1, true);      // mono
  view.setUint32(24, outRate, true);
  view.setUint32(28, outRate * 2, true); // byte rate (sr * channels * bytes/sample)
  view.setUint16(32, 2, true);      // block align
  view.setUint16(34, 16, true);     // bits per sample
  // data chunk
  writeStr(36, "data");
  view.setUint32(40, dataBytes, true);
  // Samples
  let off = 44;
  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, pcm[i]));
    view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    off += 2;
  }
  return new Uint8Array(buffer);
}

export default function Home() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [analysisData, setAnalysisData] = useState(null);
  const [tutoringText, setTutoringText] = useState("");
  const [feedbackChoice, setFeedbackChoice] = useState(null);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const wsRef = useRef(null);
  const sessionTokenRef = useRef(null);
  const activeJobRef = useRef(null);
  const runGenerationRef = useRef(0);
  const uploadAbortRef = useRef(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const currentAnalysisIdRef = useRef(null);
  const audioQueue = useRef([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const isPlayingRef = useRef(false);
  const hiddenFileRef = useRef(null);
  // Single shared handle for whatever audio is currently playing — used by
  // both the streaming WS chunk player and the static "Speak" button so
  // stopAudio() can actually stop it and Speak doesn't start a parallel one.
  const currentAudioRef = useRef(null);
  const currentUrlRef = useRef(null);
  // Bumped on stopAudio() so an in-flight TTS fetch can detect it was
  // superseded and discard its result instead of starting playback.
  const ttsGenRef = useRef(0);
  // Sticky stop flag — set by stopAudio(), cleared when a fresh analysis
  // starts or the user explicitly clicks Speak. Prevents WS audio chunks
  // arriving after Stop from auto-resuming playback.
  const playbackStoppedRef = useRef(false);

  // Recording state
  const [recState, setRecState] = useState("idle"); // idle | recording | recorded
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordedUrl, setRecordedUrl] = useState(null);
  const [recordSecs, setRecordSecs] = useState(0);
  const [micLevel, setMicLevel] = useState(0); // 0..1
  const mediaRecorderRef = useRef(null);
  const recordChunksRef = useRef([]);
  const recordingMimeRef = useRef("");
  const recordingFinalizedRef = useRef(false);
  const recordingStartedAtRef = useRef(0);
  const finalizeRecordingTimerRef = useRef(null);
  const micStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const vuRafRef = useRef(null);
  const recTimerRef = useRef(null);

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

  // Play audio from buffer (uses ref to prevent overlapping).
  // Tracks the playing Audio element in currentAudioRef so stopAudio can pause it.
  const playAudioBuffer = async (audioData) => {
    try {
      isPlayingRef.current = true;
      setIsPlaying(true);
      const blob = new Blob([audioData], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudioRef.current = audio;
      currentUrlRef.current = url;

      audio.onended = () => {
        URL.revokeObjectURL(url);
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
          currentUrlRef.current = null;
        }
        if (audioQueue.current.length > 0) {
          const nextAudio = audioQueue.current.shift();
          playAudioBuffer(nextAudio);
        } else {
          isPlayingRef.current = false;
          setIsPlaying(false);
        }
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      isPlayingRef.current = false;
      setIsPlaying(false);
    }
  };

  // A fresh connection owns each analysis. Wait for the server capability,
  // and ignore every event belonging to an earlier connection/job.
  const connectWS = (generation) => new Promise((resolve, reject) => {
    const ws = new WebSocket(TUTOR_WS_URL);
    wsRef.current = ws;
    const current = () => generation === runGenerationRef.current && wsRef.current === ws;
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error("Connection timed out. Please retry."));
    }, 10000);
    ws.onerror = () => {
      clearTimeout(timer);
      reject(new Error("Could not connect to the tutor."));
      if (current()) { setIsAnalyzing(false); setStatus("Connection failed. Please retry."); }
    };
    ws.onclose = () => {
      clearTimeout(timer);
      reject(new Error("Connection closed before the session was ready."));
      if (current()) { setIsAnalyzing(false); setStatus("Disconnected. Please retry."); }
    };
    ws.onmessage = (evt) => {
      if (!current()) return;
      if (evt.data instanceof Blob) {
        evt.data.arrayBuffer().then(audioData => {
          if (!current() || playbackStoppedRef.current) return;
          if (isPlayingRef.current) audioQueue.current.push(audioData);
          else playAudioBuffer(audioData);
        });
        return;
      }
      let msg;
      try { msg = JSON.parse(evt.data); } catch (_) { return; }
      if (msg.type === "session") {
        clearTimeout(timer);
        sessionTokenRef.current = msg.token;
        resolve({ ws, token: msg.token });
        return;
      }
      if (msg.job_id && msg.job_id !== activeJobRef.current) return;
      switch (msg.type) {
        case "status": setStatus(msg.message); break;
        case "error":
          setStatus("Analysis error: " + msg.message);
          setIsAnalyzing(false);
          break;
        case "cancelled":
          setStatus("Analysis cancelled."); setIsAnalyzing(false); break;
        case "chord_analysis":
          setAnalysis(JSON.stringify(msg.data, null, 2)); setAnalysisData(msg.data); break;
        case "text_chunk": setTutoringText(prev => prev + msg.text + " "); break;
        case "complete":
          setTutoringText(msg.full_response || "");
          setStatus("Analysis complete!"); setIsAnalyzing(false); break;
        default: break;
      }
    };
  });

  const stopAudio = () => {
    // Invalidate any in-flight TTS fetch so it doesn't start playing after
    // we just told it to stop.
    ttsGenRef.current += 1;
    // Sticky: also block any WS chunks that arrive AFTER this Stop.
    playbackStoppedRef.current = true;
    // Drop any pending WS audio chunks.
    audioQueue.current = [];
    // Actually pause whatever audio is currently playing (TTS or WS chunk).
    const audio = currentAudioRef.current;
    if (audio) {
      try { audio.pause(); audio.currentTime = 0; } catch (_) {}
      try { audio.src = ""; } catch (_) {}
    }
    const url = currentUrlRef.current;
    if (url) {
      try { URL.revokeObjectURL(url); } catch (_) {}
    }
    currentAudioRef.current = null;
    currentUrlRef.current = null;
    isPlayingRef.current = false;
    setIsPlaying(false);
  };

  const cancelAnalysis = () => {
    runGenerationRef.current += 1;
    uploadAbortRef.current?.abort();
    wsRef.current?.close();
    wsRef.current = null;
    sessionTokenRef.current = null;
    activeJobRef.current = null;
    stopAudio();
    setIsAnalyzing(false);
    setStatus("Cancelled. Any processing already underway will finish cleanup; no further guidance will be delivered.");
  };

  const clearSession = () => {
    cancelAnalysis();
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.onstop = null;
      recorder.ondataavailable = null;
      recorder.stop();
    }
    mediaRecorderRef.current = null;
    recordingFinalizedRef.current = true;
    teardownRecorder();
    discardRecording();
    setAnalysis(""); setAnalysisData(null); setTutoringText("");
    setFile(null); setFeedbackChoice(null); setQuestion("");
    if (hiddenFileRef.current) hiddenFileRef.current.value = "";
    localStorage.removeItem("horizonjam_evidence_feedback_v1");
    setStatus("Session cleared. Server recordings are removed after active processing releases them.");
  };

  // Both browser-recorded WAV and uploaded files use the same owned-ID contract.
  const runAnalysis = async (audioFile) => {
    if (!audioFile) { setStatus("No audio to analyze."); return; }
    cancelAnalysis();
    const generation = runGenerationRef.current;
    const current = () => generation === runGenerationRef.current;
    const controller = new AbortController();
    uploadAbortRef.current = controller;
    setIsAnalyzing(true);
    setAnalysis(""); setAnalysisData(null); setTutoringText("");
    setFeedbackChoice(null); setEvidenceOpen(false);
    currentAnalysisIdRef.current = typeof crypto !== "undefined" && crypto.randomUUID
      ? `session:${crypto.randomUUID()}` : `session:${Date.now()}-${Math.random().toString(16).slice(2)}`;
    playbackStoppedRef.current = false;
    setStatus("Connecting...");
    let timer;
    try {
      const { ws, token } = await connectWS(generation);
      if (!current()) return;
      const formData = new FormData();
      formData.append("audio_file", audioFile);
      setStatus("Uploading and validating recording...");
      timer = setTimeout(() => controller.abort(), 30000);
      const res = await fetch(UPLOAD_URL, {
        method: "POST", body: formData, signal: controller.signal,
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!current()) return;
      if (!res.ok || !data.success) throw new Error(data.detail || data.error || "Upload failed.");
      if (ws.readyState !== WebSocket.OPEN) throw new Error("Connection closed. Please retry.");
      activeJobRef.current = data.upload_id;
      setStatus("Analyzing...");
      ws.send(JSON.stringify({type: "analyze", upload_id: data.upload_id, question: question.trim() || null, speech: false}));
    } catch (err) {
      if (current()) {
        cancelAnalysis();
        setStatus(err.name === "AbortError" ? "Upload timed out. Please retry." : "Error: " + err.message);
      }
    } finally {
      clearTimeout(timer);
    }
  };

  // File-upload entry point
  const handleAnalyze = () => {
    if (!file) {
      hiddenFileRef.current?.click();
      return;
    }
    runAnalysis(file);
  };

  // Call TTS endpoint (returns wav) and play.
  // - Stops any currently-playing audio first so Speak doesn't stack instances.
  // - Uses a generation counter so a slow fetch can't start playback after the
  //   user has clicked Stop or Speak again in the meantime.
  const handleTTS = async (text) => {
    stopAudio();                       // pause current + clear queue + bump gen
    playbackStoppedRef.current = false; // Speak is an explicit user request; unstick
    const gen = ++ttsGenRef.current;   // claim this request's slot
    isPlayingRef.current = true;       // hold ground so WS chunks queue, not race
    setIsPlaying(true);
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
      // If the user clicked Stop or Speak again while we were fetching, drop this.
      if (gen !== ttsGenRef.current) return;

      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudioRef.current = audio;
      currentUrlRef.current = url;

      audio.onended = () => {
        try { URL.revokeObjectURL(url); } catch (_) {}
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
          currentUrlRef.current = null;
        }
        if (audioQueue.current.length > 0) {
          // Drain any WS chunks that piled up while TTS was playing.
          const next = audioQueue.current.shift();
          playAudioBuffer(next);
        } else {
          isPlayingRef.current = false;
          setIsPlaying(false);
        }
      };

      await audio.play();
    } catch (err) {
      console.error(err);
      setStatus("TTS error: " + err.message);
      if (gen === ttsGenRef.current) {
        isPlayingRef.current = false;
        setIsPlaying(false);
      }
    }
  };

  // -------------------- Mic recording --------------------

  const teardownRecorder = useCallback(() => {
    if (vuRafRef.current) {
      cancelAnimationFrame(vuRafRef.current);
      vuRafRef.current = null;
    }
    if (recTimerRef.current) {
      clearInterval(recTimerRef.current);
      recTimerRef.current = null;
    }
    if (finalizeRecordingTimerRef.current) {
      clearTimeout(finalizeRecordingTimerRef.current);
      finalizeRecordingTimerRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(t => t.stop());
      micStreamRef.current = null;
    }
    if (audioCtxRef.current) {
      try { audioCtxRef.current.close(); } catch (_) {}
      audioCtxRef.current = null;
    }
    analyserRef.current = null;
    setMicLevel(0);
  }, []);

  const finishRecording = useCallback(() => {
    if (recordingFinalizedRef.current) return;
    recordingFinalizedRef.current = true;

    const elapsed = recordingStartedAtRef.current
      ? Math.max(0, Math.round((Date.now() - recordingStartedAtRef.current) / 1000))
      : 0;
    const mime = recordingMimeRef.current || "audio/webm";
    const blob = new Blob(recordChunksRef.current, { type: mime });
    const url = URL.createObjectURL(blob);

    mediaRecorderRef.current = null;
    setRecordSecs(prev => Math.max(prev, elapsed));
    setRecordedBlob(blob);
    setRecordedUrl(url);
    setRecState("recorded");
    setStatus("");
    teardownRecorder();
  }, [teardownRecorder]);

  const startRecording = async () => {
    if (recState === "recording") return;

    // Drop any prior recording
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedBlob(null);
    setRecordedUrl(null);
    setRecordSecs(0);
    recordChunksRef.current = [];
    recordingMimeRef.current = "";
    recordingFinalizedRef.current = false;
    recordingStartedAtRef.current = 0;
    if (finalizeRecordingTimerRef.current) {
      clearTimeout(finalizeRecordingTimerRef.current);
      finalizeRecordingTimerRef.current = null;
    }

    // Pause TTS playback so it doesn't bleed into the recording
    stopAudio();

    try {
      // Disable typical voice-call processing — destroys music quality
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
      micStreamRef.current = stream;

      // VU meter via AudioContext analyser
      const Ctx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new Ctx();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      analyserRef.current = analyser;
      const buf = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteTimeDomainData(buf);
        let peak = 0;
        for (let i = 0; i < buf.length; i++) {
          const v = Math.abs(buf[i] - 128) / 128;
          if (v > peak) peak = v;
        }
        setMicLevel(peak);
        vuRafRef.current = requestAnimationFrame(tick);
      };
      tick();

      // Pin the MIME type so we know what we're producing
      const preferred = "audio/webm;codecs=opus";
      const fallback = "audio/mp4";
      const mime = (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(preferred))
        ? preferred
        : fallback;
      recordingMimeRef.current = mime;

      const mr = new MediaRecorder(stream, { mimeType: mime });
      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) recordChunksRef.current.push(e.data);
      };
      mr.onstop = finishRecording;
      mediaRecorderRef.current = mr;
      mr.start(250);
      recordingStartedAtRef.current = Date.now();
      setRecState("recording");

      // Tick the timer + auto-stop at the cap
      recTimerRef.current = setInterval(() => {
        setRecordSecs(prev => {
          const next = prev + 1;
          if (next >= MAX_RECORD_SECS) {
            stopRecording();
          }
          return next;
        });
      }, 1000);

      setStatus("🎤 Recording...");
    } catch (err) {
      const msg = err && err.message ? err.message : String(err);
      setStatus(`Mic error: ${msg}. If you blocked the prompt, click the lock icon in the address bar to allow microphone access.`);
      teardownRecorder();
      setRecState("idle");
    }
  };

  const stopRecording = () => {
    if (recordingFinalizedRef.current) return;

    const mr = mediaRecorderRef.current;
    if (recTimerRef.current) {
      clearInterval(recTimerRef.current);
      recTimerRef.current = null;
    }

    const elapsed = recordingStartedAtRef.current
      ? Math.max(0, Math.round((Date.now() - recordingStartedAtRef.current) / 1000))
      : recordSecs;
    setRecordSecs(elapsed);
    setMicLevel(0);
    setRecState("recorded");
    setStatus("Stopping recording...");

    if (vuRafRef.current) {
      cancelAnimationFrame(vuRafRef.current);
      vuRafRef.current = null;
    }
    if (mr && mr.state !== "inactive") {
      // Flush any pending data so the final dataavailable carries everything.
      try { mr.requestData(); } catch (_) {}
      try {
        mr.stop();
      } catch (_) {
        // mr.stop() can throw if already stopped — finalize directly.
        finishRecording();
        return;
      }
      // IMPORTANT: do NOT stop the mic stream tracks here. MediaRecorder
      // needs the underlying tracks live while it processes the final
      // chunk and fires `onstop`. Killing the tracks first can suppress
      // `onstop` on Chromium and leave both the mic indicator and the
      // recording state stuck. Track stop happens in teardownRecorder()
      // which `finishRecording` calls.
      finalizeRecordingTimerRef.current = setTimeout(() => {
        finalizeRecordingTimerRef.current = null;
        if (!recordingFinalizedRef.current && mediaRecorderRef.current === mr) {
          // onstop didn't fire — force finalize so the UI doesn't hang.
          console.warn("[mic] MediaRecorder.onstop watchdog fired — forcing finishRecording()");
          finishRecording();
        }
      }, 800);
      return;
    }

    // mr was already inactive (or never started) — finalize directly.
    finishRecording();
  };

  const discardRecording = () => {
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedBlob(null);
    setRecordedUrl(null);
    setRecordSecs(0);
    setRecState("idle");
    setStatus("");
  };

  // Decode WebM/MP4-Opus blob client-side, encode WAV in browser, upload as WAV.
  // This bypasses server-side ffmpeg conversion (which is unreasonably slow on
  // some Windows setups) and keeps the analysis hot path fast.
  const analyzeRecording = async () => {
    if (!recordedBlob) return;
    if (recordSecs < MIN_RECORD_SECS) {
      setStatus(`Recording is too short — at least ${MIN_RECORD_SECS}s required.`);
      return;
    }
    setStatus("🔄 Encoding recording to WAV...");
    let tempCtx = null;
    try {
      const arrayBuffer = await recordedBlob.arrayBuffer();
      const Ctx = window.AudioContext || window.webkitAudioContext;
      tempCtx = new Ctx();
      // decodeAudioData accepts the encoded blob (WebM/Opus or MP4/AAC) and
      // returns PCM samples — independent of how the browser captured them.
      const audioBuffer = await tempCtx.decodeAudioData(arrayBuffer);
      const wavBytes = audioBufferToWav(audioBuffer, TARGET_SR);
      const wavBlob = new Blob([wavBytes], { type: "audio/wav" });
      const filename = `recording_${Date.now()}.wav`;
      const f = new File([wavBlob], filename, { type: "audio/wav" });
      setStatus(`📦 WAV ready (${Math.round(wavBlob.size / 1024)} KB) — uploading...`);
      await runAnalysis(f);
    } catch (e) {
      const msg = e && e.message ? e.message : String(e);
      setStatus(`Failed to encode WAV: ${msg}`);
    } finally {
      if (tempCtx) {
        try { await tempCtx.close(); } catch (_) {}
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => () => {
    runGenerationRef.current += 1;
    uploadAbortRef.current?.abort();
    teardownRecorder();
    wsRef.current?.close();
  }, [teardownRecorder]);

  useEffect(() => () => {
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
  }, [recordedUrl]);

  // -------------------- Styles --------------------
  const colors = {
    bg: "#0f141a",
    panel: "#141a21",
    border: "#1f2a36",
    text: "#e6edf3",
    subtext: "#9aa7b2",
    accent: "#18a4c9",
    accentSoft: "#0f6e84",
    orange: "#ff9f43",
    rec: "#e74c3c",
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
        minWidth: 0,
        width: 'min(280px, 100%)'
      }}>
        Upload audio or record from your mic
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
      Choose Audio File
    </button>
  );

  // -------------------- Recording UI --------------------
  const VuBar = () => (
    <div style={{
      width: '100%',
      height: 10,
      background: '#0b1116',
      border: `1px solid ${colors.border}`,
      borderRadius: 6,
      overflow: 'hidden',
      marginTop: 8,
    }}>
      <div style={{
        width: `${Math.min(100, Math.round(micLevel * 140))}%`,
        height: '100%',
        background: micLevel > 0.85 ? colors.rec : (micLevel > 0.4 ? colors.orange : '#3ddc84'),
        transition: 'width 60ms linear',
      }} />
    </div>
  );

  const fmtTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const RecordPanel = (
    <Card title="Record from Microphone">
      {recState === "idle" && (
        <>
          <button onClick={startRecording} style={{
            background: colors.rec, border: 'none', color: 'white',
            padding: '14px 18px', borderRadius: 12, fontWeight: 700, fontSize: 18,
            cursor: 'pointer', width: '100%'
          }}>
            🎤 Start Recording
          </button>
          <div style={{ color: colors.subtext, fontSize: 12, marginTop: 10 }}>
            Tip: use headphones to keep tutor speech out of your recording. Works best with a clean instrument and a quiet room.
          </div>
        </>
      )}

      {recState === "recording" && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{
              width: 10, height: 10, borderRadius: '50%', background: colors.rec,
              animation: 'pulse 1s infinite',
            }} />
            <span style={{ fontWeight: 700 }}>Recording — {fmtTime(recordSecs)} / {fmtTime(MAX_RECORD_SECS)}</span>
          </div>
          <div style={{ color: colors.subtext, fontSize: 12, marginTop: 6 }}>Mic level</div>
          <VuBar />
          <button onClick={stopRecording} style={{
            background: '#4b5563', border: 'none', color: 'white',
            padding: '12px 16px', borderRadius: 10, fontWeight: 700, fontSize: 16,
            cursor: 'pointer', width: '100%', marginTop: 14
          }}>
            ⏹ Stop
          </button>
        </>
      )}

      {recState === "recorded" && (
        <>
          <div style={{ marginBottom: 10 }}>
            <span style={{
              background: colors.accentSoft, color: colors.text,
              padding: '4px 10px', borderRadius: 8, fontSize: 13, fontWeight: 700,
            }}>
              {recordedBlob ? 'Ready' : 'Finalizing...'}
            </span>
            <span style={{ color: colors.subtext, marginLeft: 10, fontSize: 13 }}>
              {recordSecs}s captured · {recordedBlob ? Math.round(recordedBlob.size / 1024) : 0} KB
            </span>
          </div>
          {recordedUrl && (
            <audio src={recordedUrl} controls style={{ width: '100%', marginBottom: 10 }} />
          )}
          {recordSecs < MIN_RECORD_SECS && (
            <div style={{ color: colors.orange, fontSize: 12, marginBottom: 8 }}>
              Recording is shorter than {MIN_RECORD_SECS}s — re-record for a more reliable analysis.
            </div>
          )}
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={analyzeRecording} disabled={!recordedBlob || recordSecs < MIN_RECORD_SECS} style={{
              flex: 1,
              background: (!recordedBlob || recordSecs < MIN_RECORD_SECS) ? '#3a4a59' : colors.accent,
              border: 'none', color: 'white',
              padding: '12px 16px', borderRadius: 10, fontWeight: 700,
              cursor: (!recordedBlob || recordSecs < MIN_RECORD_SECS) ? 'not-allowed' : 'pointer',
            }}>
              🎵 Analyze Recording
            </button>
            <button onClick={discardRecording} style={{
              background: '#4b5563', border: 'none', color: 'white',
              padding: '12px 16px', borderRadius: 10, fontWeight: 700, cursor: 'pointer',
            }}>
              🔄 Re-record
            </button>
          </div>
        </>
      )}
    </Card>
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
      <div style={{ display: 'flex', gap: 16, marginTop: 18, flexWrap: 'wrap' }}>
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
    `Your AI tutor will appear here. Upload audio or record from your mic, then start analysis.`;

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
  const fullProgression = useMemo(() => {
    if (!analysisData?.chord_events?.length) return null;
    return analysisData.chord_events
      .map(ev => ev.chord || ev.chord_symbol)
      .filter(Boolean)
      .filter(c => c !== 'N');
  }, [analysisData]);

  const evidenceStrengthLabel = (value) => ({
    STRONG_AGREEMENT: 'Strong agreement',
    PARTIAL_AGREEMENT: 'Partial agreement',
    MIXED_EVIDENCE: 'Mixed evidence',
    LIMITED_EVIDENCE: 'Limited evidence',
  }[value] || 'Evidence unavailable');

  const recordFeedback = (choice) => {
    if (!analysisData) return;
    setFeedbackChoice(choice);
    const summaries = (analysisData.evidence_summaries || []).map((item) => ({
      chord: item.chord,
      strength: item.strength,
      agreement: item.agreement,
    }));
    const record = {
      schema_version: 'horizonjam-local-feedback-v1',
      audio_identifier: currentAnalysisIdRef.current,
      predicted_chords: fullProgression || [],
      evidence_summaries: summaries,
      user_feedback: choice,
      user_correction: null,
      detector: analysisData.detector_used || null,
      timestamp: new Date().toISOString(),
    };
    try {
      const key = 'horizonjam_evidence_feedback_v1';
      const existing = JSON.parse(localStorage.getItem(key) || '[]');
      const bounded = Array.isArray(existing) ? existing.slice(-49) : [];
      localStorage.setItem(key, JSON.stringify([...bounded, record]));
    } catch (_) {
      setStatus('Feedback could not be saved in this browser.');
    }
  };

  const EvidenceDetails = analysisData?.evidence_summaries?.length ? (
    <div style={{ marginTop: 16, borderTop: `1px solid ${colors.border}`, paddingTop: 12 }}>
      <details open={evidenceOpen} onToggle={(event) => setEvidenceOpen(event.currentTarget.open)}>
        <summary style={{ cursor: 'pointer', fontWeight: 700 }}>Why this chord?</summary>
        <div style={{ marginTop: 12, display: 'grid', gap: 12 }}>
          {analysisData.evidence_summaries.map((item, index) => (
            <div key={`${item.start}-${item.chord}-${index}`} style={{ borderBottom: `1px solid ${colors.border}`, paddingBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                <strong>{item.chord}</strong>
                <span style={{ color: colors.subtext }}>{evidenceStrengthLabel(item.strength)}</span>
              </div>
              <div style={{ color: colors.subtext, marginTop: 6, lineHeight: 1.5 }}>
                {item.short_explanation}
              </div>
              {!!item.observed_notes?.length && (
                <div style={{ marginTop: 6 }}>Notes heard: {item.observed_notes.join(' ')}</div>
              )}
            </div>
          ))}
        </div>
      </details>
      <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: colors.subtext, marginRight: 4 }}>Was this detection right?</span>
        {[
          ['correct', 'Correct chord'],
          ['wrong', 'Wrong chord'],
          ['not_sure', 'Not sure'],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            aria-pressed={feedbackChoice === value}
            onClick={() => recordFeedback(value)}
            style={{
              background: feedbackChoice === value ? colors.accentSoft : '#0b1116',
              border: `1px solid ${feedbackChoice === value ? colors.accent : colors.border}`,
              color: colors.text,
              padding: '7px 10px',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  ) : null;

  const ProgressionCard = (
    <Card title="Chord Progression">
      <div style={{ color: colors.subtext, marginBottom: 8 }}>
        <strong>Key: </strong>{analysisData?.analysis_summary?.detected_key || 'Unknown'}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {(fullProgression || []).map((chord, i) => (
          <span key={i} style={{
            background: colors.accentSoft, color: colors.text,
            padding: '4px 12px', borderRadius: 8, fontWeight: 700, fontSize: 16
          }}>
            {chord}
          </span>
        ))}
        {!fullProgression && (
          <div style={{ color: colors.subtext }}>No progression detected yet</div>
        )}
      </div>
      {analysisData?.analysis_summary?.chord_progression && (
        <div style={{ color: colors.subtext, marginTop: 8, fontSize: 13 }}>
          Summary: {analysisData.analysis_summary.chord_progression}
        </div>
      )}
      {EvidenceDetails}
    </Card>
  );

  const parseTime = (val) => {
    if (val == null) return 0;
    if (typeof val === 'number') return val;
    const str = String(val);
    const mmss = str.match(/^(\d+):(\d+)$/);
    if (mmss) return parseInt(mmss[1]) * 60 + parseInt(mmss[2]);
    const num = Number(str);
    return Number.isFinite(num) ? num : 0;
  };

  const TimelineCard = (
    <Card title="Chord Timeline">
      <div style={{ maxHeight: 220, overflowY: 'auto' }}>
        {(analysisData?.chord_events?.length ? analysisData.chord_events : []).map((ev, idx) => {
          const startSec = parseTime(ev.start_time ?? ev.start ?? ev.time);
          const endSec = ev.end_time != null || ev.end != null
            ? parseTime(ev.end_time ?? ev.end)
            : startSec + (ev.duration_seconds ?? ev.duration ?? 0);
          const dur = ev.duration_seconds ?? ev.duration ?? (endSec - startSec);
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
                <span style={{ color: colors.subtext }}>
                  {' '}[{startSec.toFixed(1)}s - {endSec.toFixed(1)}s] ({dur.toFixed(1)}s)
                </span>
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

  return (
    <div style={{ background: colors.bg, minHeight: '100vh', color: colors.text }}>
      <style jsx global>{`
        @keyframes pulse {
          0%   { opacity: 1; transform: scale(1); }
          50%  { opacity: 0.4; transform: scale(1.4); }
          100% { opacity: 1; transform: scale(1); }
        }
        @media (max-width: 760px) {
          .hj-two-column {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>

      <Nav />

      {/* Hidden file input for Choose-File flow */}
      <input
        ref={hiddenFileRef}
        type="file"
        accept=".wav,.mp3,.m4a,.webm,.ogg,.flac"
        onChange={(e) => {
          const f = e.target.files?.[0] || null;
          setFile(f);
          if (f) runAnalysis(f);
        }}
        style={{ display: 'none' }}
      />

      <div style={{maxWidth: 1100, margin: '0 auto', padding: '8px 20px', display: 'flex', gap: 12}}>
        {isAnalyzing && <button onClick={cancelAnalysis}>Cancel analysis</button>}
        <button onClick={clearSession}>Clear session</button>
      </div>
      {/* Controls row (question + status) */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '6px 20px 16px' }}>
        <input
          maxLength={2000}
          placeholder="Optional question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{
            width: '100%', boxSizing: 'border-box', padding: 12, borderRadius: 10, background: colors.panel,
            border: `1px solid ${colors.border}`, color: colors.text
          }}
        />
        <div style={{ marginTop: 8, color: colors.subtext, fontSize: 12 }}>{status}</div>
      </div>

      {/* Studio + Recording side by side */}
      <div className="hj-two-column" style={{
        maxWidth: 1100,
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 20,
        padding: '0 20px'
      }}>
        {StudioCanvas}
        {RecordPanel}
      </div>

      {/* Analysis details */}
      <div style={{ maxWidth: 1100, margin: '26px auto 20px', padding: '0 20px' }}>
        <div className="hj-two-column" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 20 }}>
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

      {/* Developer info panel */}
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
