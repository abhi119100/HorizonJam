# ws_relay.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import aiohttp
import os

app = FastAPI()

# Serve the test client HTML file
@app.get("/test_client.html")
async def get_test_client():
    return FileResponse("test_client.html")

# Serve static files from current directory
app.mount("/static", StaticFiles(directory="."), name="static")

@app.websocket("/ws/tts")
async def ws_tts(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        while True:
            text = await websocket.receive_text()
            print(f"Received text: {text}")
            async with aiohttp.ClientSession() as sess:
                async with sess.post(
                    "http://localhost:5000/tts",
                    json={"text": text},
                    headers={"accept": "audio/wav"}
                ) as resp:
                    # Forward audio chunks to the client as they arrive
                    total = 0
                    async for chunk in resp.content.iter_chunked(2048):
                        total += len(chunk)
                        await websocket.send_bytes(chunk)
                    print(f"Streamed audio data: {total} bytes")
            await websocket.send_text("[END]")
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")