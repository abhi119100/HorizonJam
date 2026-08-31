---
name: frontend-e2e
description: Verify HorizonJam browser recording, WAV encoding, upload, WebSocket streaming, result rendering, stop/cancellation behavior, and optional TTS across frontend/backend boundaries. Use for nextjs-frontend, relay HTTP/WebSocket changes, microphone workflows, stream events, playback, or user-visible analysis behavior.
---

# Verify the Browser Workflow

1. Read `docs/context/PRODUCT.md#runtime-user-flow`, `docs/context/ARCHITECTURE.md#http-and-websocket-contract`, and `docs/context/SECURITY.md`.
2. Map the changed UI action to frontend symbol, request/message, backend handler, response event, and rendered state.
3. Define expected message order, visible states, failure behavior, and cleanup before editing.
4. Add focused tests at the lowest affected boundary and run the frontend production build.
5. Start TTS on 5000, relay on 8001, and Next.js on 3000 only when live E2E is required.
6. Exercise file upload and microphone flows; inspect console, network, relay logs, JSON events, and binary audio.
7. Test short/silent/invalid audio, disconnected WebSocket, detector/RAG/TTS failure, Stop during work, repeated analysis, and unmount cleanup as relevant.
8. Check desktop/mobile layout, keyboard access, permissions, and text overflow.
9. Record browser/OS, sample, detector, configuration, timings, screenshots/logs, and pass/fail evidence.

`python _e2e_smoke.py` covers service messaging only and does not replace browser verification. TTS success is not required for written tutoring success.
