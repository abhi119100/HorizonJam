"""Process-local, session-owned temporary uploads. Not account authentication."""
from __future__ import annotations

import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import HTTPException
from scipy.signal import resample_poly
from math import gcd
import asyncio

MAX_UPLOAD_BYTES = 16 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024
MAX_DURATION = 30.0
UPLOAD_TTL = 300
SESSION_TTL = 1200
MAX_SESSIONS = 16


@dataclass
class Upload:
    id: str
    directory: Path
    created: float
    state: str = "receiving"
    cancelled: threading.Event = field(default_factory=threading.Event)

    @property
    def wav(self) -> Path:
        return self.directory / "audio.wav"


@dataclass
class Session:
    touched: float
    uploads: dict[str, Upload] = field(default_factory=dict)
    analyses: int = 0


class UploadStore:
    def __init__(self, root: Path | None = None, clock=time.monotonic):
        self.root = root
        self.clock = clock
        self.sessions: dict[str, Session] = {}
        self.lock = threading.RLock()

    def create_session(self) -> str:
        with self.lock:
            self.prune()
            if len(self.sessions) >= MAX_SESSIONS:
                raise HTTPException(503, "Session capacity reached; retry later.")
            token = secrets.token_urlsafe(32)
            self.sessions[token] = Session(self.clock())
            return token

    def session(self, token: str) -> Session:
        session = self.sessions.get(token)
        if session is None or self.clock() - session.touched >= SESSION_TTL:
            self.close_session(token)
            raise HTTPException(401, "Session expired; reconnect before uploading.")
        session.touched = self.clock()
        return session

    def reserve(self, token: str) -> Upload:
        with self.lock:
            self.prune()
            session = self.session(token)
            if session.uploads:
                raise HTTPException(409, "Finish or delete the current recording first.")
            if session.analyses >= 3:
                raise HTTPException(429, "Local session analysis limit reached.")
            if self.root is None:
                self.root = Path(tempfile.mkdtemp(prefix="horizonjam-uploads-"))
            self.root.mkdir(parents=True, exist_ok=True)
            upload_id = secrets.token_urlsafe(24)
            directory = self.root / upload_id
            directory.mkdir()
            item = Upload(upload_id, directory, self.clock())
            session.uploads[upload_id] = item
            return item

    def get(self, token: str, upload_id: str) -> Upload:
        with self.lock:
            session = self.session(token)
            item = session.uploads.get(upload_id)
            if item is None:
                raise HTTPException(404, "Recording unavailable.")
            if item.state == "ready" and self.clock() - item.created >= UPLOAD_TTL:
                self.release(token, item)
                raise HTTPException(404, "Recording expired.")
            return item

    def ready(self, token: str, item: Upload):
        with self.lock:
            if item.cancelled.is_set() or self.get(token, item.id) is not item:
                raise HTTPException(409, "Upload cancelled.")
            item.state = "ready"

    def claim(self, token: str, upload_id: str) -> Upload:
        with self.lock:
            item = self.get(token, upload_id)
            if item.state != "ready" or item.cancelled.is_set():
                raise HTTPException(409, "Recording is not ready or was already used.")
            self.session(token).analyses += 1
            item.state = "analyzing"
            return item

    def release(self, token: str, item: Upload):
        with self.lock:
            # Paths are generated here, never derived from client input.
            if self.root is None or item.directory.resolve().parent != self.root.resolve():
                raise RuntimeError("Upload directory escaped its storage root")
            shutil.rmtree(item.directory, ignore_errors=False) if item.directory.exists() else None
            session = self.sessions.get(token)
            if session:
                session.uploads.pop(item.id, None)

    def delete(self, token: str, upload_id: str):
        with self.lock:
            item = self.get(token, upload_id)
            item.cancelled.set()
            if item.state == "ready":
                self.release(token, item)
            # Active writers/readers own cleanup in finally, including on Windows.

    def close_session(self, token: str):
        with self.lock:
            session = self.sessions.get(token)
            if session:
                for item in list(session.uploads.values()):
                    self._expire(token, item)
                self.sessions.pop(token, None)

    def _expire(self, token: str, item: Upload):
        item.cancelled.set()
        if item.state == "ready":
            self.release(token, item)

    def prune(self):
        with self.lock:
            for token, session in list(self.sessions.items()):
                if self.clock() - session.touched >= SESSION_TTL:
                    self.close_session(token)
                    continue
                for item in list(session.uploads.values()):
                    if item.state == "ready" and self.clock() - item.created >= UPLOAD_TTL:
                        self.release(token, item)


def normalize_upload(item: Upload) -> dict:
    """Validate actual decoded content; bounded duration even for native WAV."""
    source = item.directory / "input"
    decoded = source
    try:
        info = sf.info(source)
    except (RuntimeError, sf.LibsndfileError):
        # Do not pass playlists/manifests to ffmpeg: they can reference other files.
        with source.open("rb") as handle:
            header = handle.read(16)
        if not (header.startswith((b"ID3", b"OggS", b"\x1aE\xdf\xa3")) or header[4:8] == b"ftyp" or (len(header) >= 2 and header[0] == 255 and header[1] & 224 == 224)):
            raise HTTPException(415, "Unsupported audio container.")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise HTTPException(415, "Unsupported audio; upload WAV or enable ffmpeg.")
        decoded = item.directory / "decoded.wav"
        try:
            subprocess.run(
                [ffmpeg, "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe",
                 "-threads", "1", "-i", str(source), "-t", "30.1", "-vn", "-ac", "2",
                 "-ar", "44100", "-c:a", "pcm_s16le", str(decoded)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=True,
            )
            info = sf.info(decoded)
        except (subprocess.SubprocessError, RuntimeError, sf.LibsndfileError):
            raise HTTPException(415, "Audio could not be decoded within the supported limits.")
    if not 8000 <= info.samplerate <= 96000 or not 1 <= info.channels <= 2:
        raise HTTPException(422, "Use mono/stereo audio at 8–96 kHz.")
    if not 0.5 <= info.duration <= MAX_DURATION:
        raise HTTPException(422, "Recording must be between 0.5 and 30 seconds.")
    samples, rate = sf.read(decoded, dtype="float32", always_2d=True, frames=int(MAX_DURATION * info.samplerate) + 1)
    if item.cancelled.is_set():
        raise HTTPException(409, "Upload cancelled.")
    if len(samples) != info.frames or not np.isfinite(samples).all():
        raise HTTPException(422, "Audio is truncated or contains invalid samples.")
    mono = samples.mean(axis=1)
    if float(np.sqrt(np.mean(mono.astype("float64") ** 2))) < 1e-3:
        raise HTTPException(422, "Recording is silent; check your microphone.")
    if rate != 44100:
        divisor = gcd(rate, 44100)
        mono = resample_poly(mono, 44100 // divisor, rate // divisor)
    sf.write(item.wav, mono, 44100, subtype="PCM_16")
    source.unlink()
    if decoded != source:
        decoded.unlink()
    return {"duration_seconds": len(mono) / 44100, "sample_rate": 44100}


class RequestSizeLimit:
    """Bound request bytes before multipart parsing/spooling, including chunked bodies."""
    def __init__(self, app, limit=MAX_REQUEST_BYTES):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        from starlette.responses import JSONResponse
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length."}, 400)(scope, receive, send)
        if length > self.limit or length < 0:
            return await JSONResponse({"detail": "Request too large."}, 413)(scope, receive, send)
        # Spool with a small RAM threshold before multipart creates its own files.
        # Oversized/chunked requests never reach the parser; all spools close.
        with tempfile.SpooledTemporaryFile(max_size=65536) as spool:
            received = 0
            try:
                async with asyncio.timeout(30):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        chunk = message.get("body", b"")
                        received += len(chunk)
                        if received > self.limit:
                            return await JSONResponse({"detail": "Request too large."}, 413)(scope, receive, send)
                        spool.write(chunk)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await JSONResponse({"detail": "Upload timed out."}, 408)(scope, receive, send)
            spool.seek(0)

            async def replay():
                chunk = spool.read(65536)
                return {"type": "http.request", "body": chunk, "more_body": spool.tell() < received}

            await self.app(scope, replay, send)
