"""Quick e2e smoke test: upload audio -> WS analyze -> count text/audio chunks."""
import asyncio
import json
import sys
import requests
import websockets

UPLOAD = "http://127.0.0.1:8001/upload-audio"
WS = "ws://127.0.0.1:8001/ws/tutor"
AUDIO = "tests/audio/pop.wav"


async def run():
    # 1. Upload — send just the basename; the relay concatenates filename into a path
    # without sanitizing, so passing "tests/audio/pop.wav" creates broken subpath.
    import os
    basename = os.path.basename(AUDIO)
    with open(AUDIO, "rb") as f:
        r = requests.post(UPLOAD, files={"audio_file": (basename, f, "audio/wav")},
                          data={"question": "What chords are these?"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"[upload] {data}")
    if not data.get("success"):
        print("[upload] FAILED")
        sys.exit(1)

    # 2. WS analyze
    text_chunks = 0
    audio_chunks = 0
    audio_bytes = 0
    text_total = []
    last_status = None

    async with websockets.connect(WS, max_size=None) as ws:
        await ws.send(json.dumps({
            "type": "analyze",
            "file_path": data["file_path"],
            "question": "What chords are these?",
        }))
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                if isinstance(msg, bytes):
                    audio_chunks += 1
                    audio_bytes += len(msg)
                else:
                    try:
                        m = json.loads(msg)
                    except Exception:
                        text_total.append(msg)
                        continue
                    t = m.get("type")
                    if t == "status":
                        last_status = m.get("message")
                        print(f"[status] {last_status}")
                    elif t == "error":
                        print(f"[error] {m.get('message')}")
                        break
                    elif t == "chord_analysis":
                        summary = (m.get("data") or {}).get("analysis_summary", {})
                        print(f"[chord_analysis] key={summary.get('detected_key')} "
                              f"events={summary.get('total_chord_events')} "
                              f"prog={summary.get('chord_progression')}")
                    elif t == "text_chunk":
                        text_chunks += 1
                        text_total.append(m.get("text", ""))
                    elif t == "complete":
                        print("[complete]")
                        break
        except asyncio.TimeoutError:
            print("[timeout] no message for 60s")

    full_text = "".join(text_total)
    print(f"\n--- e2e summary ---")
    print(f"text chunks : {text_chunks}")
    print(f"audio chunks: {audio_chunks}")
    print(f"audio bytes : {audio_bytes}")
    print(f"text length : {len(full_text)} chars")
    if full_text:
        print(f"first 240   : {full_text[:240]!r}")


if __name__ == "__main__":
    asyncio.run(run())
