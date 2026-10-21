"""Real HTTP/WS browser regression check with synthetic mic and stubbed providers."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def get_state():
    with urllib.request.urlopen("http://127.0.0.1:8001/__test/state", timeout=2) as response:
        return json.load(response)


def wait_for(predicate, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except Exception:
            pass
        time.sleep(0.1)
    raise TimeoutError("Expected condition did not become true")


def run():
    # Fail if a user's service owns either port; never stop unrelated processes.
    import socket
    for port in (3000, 8001):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    processes = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with tempfile.TemporaryDirectory(prefix="horizonjam-browser-") as tmp:
        tmp = Path(tmp)
        capture = tmp / "microphone.wav"
        sf.write(capture, 0.1 * np.sin(2 * np.pi * 220 * np.arange(44100 * 10) / 44100), 44100, subtype="PCM_16")
        with (tmp / "services.log").open("w", encoding="utf-8") as log:
            try:
                for command in (
                    [sys.executable, "-m", "uvicorn", "eval.runtime_fixture:app", "--host", "127.0.0.1", "--port", "8001", "--no-access-log"],
                    ["node", "node_modules/next/dist/bin/next", "dev", "./nextjs-frontend", "--hostname", "127.0.0.1", "--port", "3000"],
                ):
                    processes.append(subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log, creationflags=flags))
                wait_for(get_state)
                wait_for(lambda: urllib.request.urlopen("http://localhost:3000", timeout=3).status == 200)
                print("Fixture services ready; exercising real browser transport.", flush=True)
                with sync_playwright() as playwright:
                    options = {"headless": True, "args": ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", f"--use-file-for-fake-audio-capture={capture}"]}
                    if EDGE.exists():
                        options["executable_path"] = str(EDGE)
                    browser = playwright.chromium.launch(**options)
                    context = browser.new_context(permissions=["microphone"], viewport={"width": 1440, "height": 1000})
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto("http://localhost:3000", wait_until="networkidle")
                    upload = page.locator('input[type="file"]')
                    question = page.get_by_placeholder("Optional question...")
                    upload.set_input_files(capture)
                    expect(page.get_by_text("Analysis complete!", exact=True)).to_be_visible(timeout=20000)
                    page.get_by_text("Why this chord?", exact=True).click()
                    expect(page.get_by_text("Mixed evidence", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Wrong chord", exact=True).click()
                    assert page.evaluate("JSON.parse(localStorage.getItem('horizonjam_evidence_feedback_v1')).length") == 1
                    wait_for(lambda: get_state()["uploads"] == 0)
                    print("Upload, evidence, feedback and success cleanup passed.", flush=True)
                    page.get_by_role("button", name="Clear session", exact=True).click()
                    assert page.evaluate("localStorage.getItem('horizonjam_evidence_feedback_v1')") is None
                    question.fill("slow")
                    upload.set_input_files(capture)
                    expect(page.get_by_text("Retrieving musical context...", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Cancel analysis", exact=True).click()
                    question.fill("")
                    upload.set_input_files([])
                    upload.set_input_files(capture)
                    expect(page.get_by_text("Analysis complete!", exact=True)).to_be_visible(timeout=20000)
                    wait_for(lambda: get_state()["jobs"] == 0)
                    expect(page.get_by_text("Analysis complete!", exact=True)).to_be_visible()
                    print("Cancellation and subsequent analysis passed.", flush=True)
                    page.get_by_role("button", name="Clear session", exact=True).click()
                    upload.set_input_files({"name": "invalid.wav", "mimeType": "audio/wav", "buffer": b"not audio"})
                    expect(page.get_by_text("Error: Unsupported audio container.", exact=True)).to_be_visible()
                    wait_for(lambda: get_state()["uploads"] == 0)
                    question.fill("fail")
                    upload.set_input_files(capture)
                    expect(page.get_by_text("Analysis error: Analysis failed; retry with a supported recording.", exact=True)).to_be_visible(timeout=20000)
                    wait_for(lambda: get_state()["uploads"] == 0)
                    page.get_by_role("button", name="Clear session", exact=True).click()
                    print("Invalid input and provider failure passed; checking microphone.", flush=True)
                    page.get_by_role("button", name="Start Recording").click()
                    expect(page.get_by_text(re.compile(r"Recording.*0?0:03 / 0?0:30"))).to_be_visible(timeout=10000)
                    page.get_by_role("button", name=re.compile(r"Stop$")).first.click()
                    expect(page.get_by_role("button", name="Analyze Recording")).to_be_enabled(timeout=10000)
                    page.get_by_role("button", name="Analyze Recording").click()
                    expect(page.get_by_text("Analysis complete!", exact=True)).to_be_visible(timeout=20000)
                    wait_for(lambda: get_state()["uploads"] == 0)
                    widths = []
                    for viewport in ({"width": 1440, "height": 1000}, {"width": 390, "height": 844}):
                        page.set_viewport_size(viewport)
                        width = page.evaluate("document.body.scrollWidth")
                        assert width <= viewport["width"]
                        widths.append({**viewport, "scroll_width": width})
                    page.get_by_role("button", name="Clear session", exact=True).click()
                    wait_for(lambda: get_state()["sessions"] == 0 and get_state()["uploads"] == 0)
                    page.get_by_role("button", name="Start Recording").click()
                    expect(page.get_by_text(re.compile(r"Recording.*0?0:01 / 0?0:30"))).to_be_visible(timeout=10000)
                    page.get_by_role("button", name="Clear session", exact=True).click()
                    expect(page.get_by_role("button", name="Start Recording")).to_be_visible()
                    expect(page.get_by_role("button", name="Analyze Recording")).to_have_count(0)
                    assert not errors, errors
                    version = browser.version
                    browser.close()
                    return {"scope": "real frontend/HTTP/WebSocket, deterministic detector/provider stubs, synthetic browser microphone; not live-model or musical accuracy", "browser": version, "passed": ["upload", "evidence", "feedback", "success_cleanup", "cancellation", "repeat_analysis", "invalid_audio", "provider_failure", "microphone_wav", "clear_session", "clear_during_recording", "no_page_errors", "responsive_width"], "viewports": widths}
            except Exception:
                log.flush()
                if 'page' in locals() and not page.is_closed():
                    print(page.locator('body').inner_text()[:2000], file=sys.stderr)
                print((tmp / "services.log").read_text(encoding="utf-8", errors="replace")[-4000:], file=sys.stderr)
                raise
            finally:
                for process in processes:
                    process.terminate()
                for process in processes:
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve earlier evidence; use a new report path")
    try:
        report = {"status": "passed", **run()}
    except Exception as exc:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump({"status": "failed", "error": str(exc), "scope": "browser integration; failed runs are not acceptance evidence"}, handle, indent=2)
            handle.write("\n")
        raise
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report, indent=2))
