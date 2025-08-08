import os
from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import aiohttp
import asyncio

load_dotenv()
KYUTAI_API_KEY = os.getenv("KYUTAI_API_KEY")

router = APIRouter()

@router.websocket("/ws/kyutai-tts")
async def websocket_kyutai_tts(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            async for chunk in kyutai_stream_tts(text):
                await websocket.send_bytes(chunk)
            await websocket.send_text("[END]")
    except WebSocketDisconnect:
        print("Client disconnected")

async def kyutai_stream_tts(text: str):
    # Use local TTS server instead of external API
    payload = {"text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:5000/tts", json=payload) as resp:
            async for chunk in resp.content.iter_chunked(2048):
                yield chunk