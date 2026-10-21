import asyncio
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import tutor_ws_relay as relay
from upload_store import UploadStore, RequestSizeLimit

ORIGIN = {"origin": "http://localhost:3000"}


def wav(seconds=0.6, silent=False):
    data = np.zeros(int(8000 * seconds)) if silent else 0.1 * np.sin(2 * np.pi * 220 * np.arange(int(8000 * seconds)) / 8000)
    buffer = io.BytesIO()
    sf.write(buffer, data, 8000, format="WAV")
    return buffer.getvalue()


class FakeTutor:
    def _run_horizon_jam(self, path):
        assert Path(path).is_file()
        return {"chord_events": [{"start": 0, "end": 0.6, "chord": "A"}]}

    def _retrieve_rag_context(self, result, question):
        return {}

    def stream_rag_tutoring(self, **kwargs):
        kwargs["websocket_callback"]("Try a slow transition.")
        return "Try a slow transition."


class UploadBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = UploadStore(Path(self.temp.name))
        self.manager = relay.TutorWebSocketManager()
        self.manager.tutor = FakeTutor()
        self.patch_store = patch.object(relay, "uploads", self.store)
        self.patch_manager = patch.object(relay, "manager", self.manager)
        self.patch_store.start()
        self.patch_manager.start()
        self.client = TestClient(relay.app).__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.patch_manager.stop()
        self.patch_store.stop()
        self.temp.cleanup()

    def upload(self, token, content=None, name="same.wav"):
        return self.client.post("/upload-audio", headers={"authorization": f"Bearer {token}"},
                                files={"audio_file": (name, content if content is not None else wav(), "audio/wav")})

    def test_repository_and_dotfiles_are_not_served(self):
        for path in ("/static/STATUS.md", "/static/.env", "/static/.env.production"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_untrusted_and_missing_websocket_origins_are_denied(self):
        for headers in ({}, {"origin": "https://evil.example"}):
            with self.assertRaises(WebSocketDisconnect):
                with self.client.websocket_connect("/ws/tutor", headers=headers):
                    pass

    def test_upload_requires_live_session(self):
        self.assertEqual(self.upload("unknown").status_code, 401)
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
        self.assertEqual(self.upload(token).status_code, 401)

    def test_upload_returns_owned_id_never_paths_or_filenames(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            response = self.upload(token, name="../../private.wav")
            self.assertEqual(response.status_code, 200, response.text)
            data = response.json()
            self.assertNotIn("file_path", data)
            self.assertNotIn("filename", data)
            item = self.store.get(token, data["upload_id"])
            self.assertEqual(sf.info(item.wav).samplerate, 44100)
            self.assertEqual(self.upload(token).status_code, 409)
        async def disconnected():
            async with asyncio.timeout(2):
                while token in self.store.sessions:
                    await asyncio.sleep(0.001)
        self.client.portal.call(disconnected)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_cross_session_analysis_and_deletion_are_denied(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as first:
            token = first.receive_json()["token"]
            uid = self.upload(token).json()["upload_id"]
            with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as second:
                other = second.receive_json()["token"]
                response = self.client.delete(f"/uploads/{uid}", headers={"authorization": f"Bearer {other}"})
                self.assertEqual(response.status_code, 404)
                second.send_json({"type": "analyze", "upload_id": uid})
                self.assertEqual(second.receive_json()["type"], "error")
                self.assertTrue(self.store.get(token, uid).wav.exists())

    def test_arbitrary_server_path_and_malformed_messages_are_rejected(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            ws.receive_json()
            for message in ({"type": "analyze", "file_path": "STATUS.md"}, [], {"type": "analyze", "upload_id": "../anything"}):
                ws.send_json(message)
                self.assertEqual(ws.receive_json()["type"], "error")

    def test_wav_silence_short_long_and_invalid_content_rejected_and_cleaned(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            for content in (wav(silent=True), wav(0.1), wav(30.2), b"not audio", b"#EXTM3U\nfile:///private.wav"):
                response = self.upload(token, content)
                self.assertIn(response.status_code, (415, 422), response.text)
                self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_same_filename_in_different_sessions_has_isolated_storage(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as first:
            one = first.receive_json()["token"]
            uid = self.upload(one).json()["upload_id"]
            with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as second:
                two = second.receive_json()["token"]
                other = self.upload(two).json()["upload_id"]
                self.assertNotEqual(self.store.get(one, uid).wav, self.store.get(two, other).wav)

    def test_ready_upload_can_be_deleted_and_not_replayed(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            uid = self.upload(token).json()["upload_id"]
            self.assertEqual(self.client.delete(f"/uploads/{uid}", headers={"authorization": f"Bearer {token}"}).status_code, 200)
            ws.send_json({"type": "analyze", "upload_id": uid})
            self.assertEqual(ws.receive_json()["type"], "error")
            self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_real_handlers_deliver_job_scoped_text_and_cleanup(self):
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            uid = self.upload(token).json()["upload_id"]
            ws.send_json({"type": "analyze", "upload_id": uid, "speech": False})
            messages = []
            while not messages or messages[-1]["type"] != "complete":
                messages.append(ws.receive_json())
            self.assertIn("text_chunk", [m["type"] for m in messages])
            self.assertTrue(all(m["job_id"] == uid for m in messages))
            async def finished():
                await asyncio.gather(*self.manager.tasks)
            self.client.portal.call(finished)
            self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_written_completion_precedes_speech_and_survives_its_failure(self):
        speech_started, finish_speech = threading.Event(), threading.Event()
        async def slow_speech(*args):
            speech_started.set()
            await asyncio.to_thread(finish_speech.wait, 5)
            raise RuntimeError("speech unavailable")
        self.manager.send_text_chunk = slow_speech
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            uid = self.upload(token).json()["upload_id"]
            ws.send_json({"type": "analyze", "upload_id": uid, "speech": True})
            messages = []
            while not messages or messages[-1]["type"] != "complete":
                messages.append(ws.receive_json())
            self.assertTrue(speech_started.wait(2))
            self.assertFalse(finish_speech.is_set())
            self.assertIn("Try a slow transition", messages[-1]["full_response"])
            finish_speech.set()
            async def finished():
                await asyncio.gather(*self.manager.tasks)
            self.client.portal.call(finished)
            self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_cancel_during_detection_keeps_input_until_worker_finishes(self):
        started, finish = threading.Event(), threading.Event()
        paths = []
        def detection(path):
            paths.append(Path(path))
            started.set()
            finish.wait(5)
            self.assertTrue(Path(path).exists())
            return {"chord_events": []}
        self.manager.tutor._run_horizon_jam = detection
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            uid = self.upload(token).json()["upload_id"]
            ws.send_json({"type": "analyze", "upload_id": uid})
            self.assertTrue(started.wait(5))
            ws.send_json({"type": "cancel", "upload_id": uid})
            while ws.receive_json()["type"] != "cancelled":
                pass
            self.assertTrue(paths[0].exists())
            finish.set()
            async def finished():
                await asyncio.gather(*self.manager.tasks)
            self.client.portal.call(finished)
            self.assertFalse(paths[0].exists())
            self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_upload_expiry(self):
        clock = [0]
        self.store.clock = lambda: clock[0]
        with self.client.websocket_connect("/ws/tutor", headers=ORIGIN) as ws:
            token = ws.receive_json()["token"]
            self.upload(token)
            clock[0] = 301
            self.store.prune()
            self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_body_limit_applies_before_multipart_and_to_chunked_bodies(self):
        client = TestClient(RequestSizeLimit(relay.app, limit=100))
        response = client.post("/upload-audio", content=b"x" * 101)
        self.assertEqual(response.status_code, 413)
        response = client.post("/upload-audio", content=iter([b"x" * 60, b"x" * 60]))
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
