"""Playwright check for the Phase 7 evidence disclosure and local feedback."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = "http://localhost:3000"
SCREENSHOTS = ROOT / "eval" / "screenshots"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


ANALYSIS = {
    "analysis_summary": {
        "detected_key": "D Major",
        "chord_progression": "D7",
        "total_chord_events": 1,
    },
    "chord_events": [{
        "start": 0.0, "end": 2.0, "duration_seconds": 2.0,
        "chord": "D7", "source_detector": "rule_jaccard",
    }],
    "detector_used": "rule_jaccard",
    "evidence_summaries": [{
        "start": 0.0, "end": 2.0, "chord": "D7",
        "strength": "MIXED_EVIDENCE", "agreement": "SYMBOLIC_DSP_DISAGREE",
        "observed_notes": ["C", "D", "F#", "A"], "harmonic_candidate": "G",
        "supporting_sources": ["rule_jaccard", "basic_pitch", "librosa_chroma"],
        "warnings": [],
        "short_explanation": "Detected notes favor D7, while the harmonic spectrum favors G.",
    }],
    "guitar_tabs": [],
}


def _run_view(page, screenshot: Path) -> dict:
    def websocket_handler(websocket):
        websocket.send(json.dumps({"type": "session", "token": "mock-capability", "protocol": 1}))
        def receive(message):
            job_id = json.loads(message)["upload_id"]
            websocket.send(json.dumps({"type": "chord_analysis", "job_id": job_id, "data": ANALYSIS}))
            websocket.send(json.dumps({"type": "complete", "job_id": job_id, "full_response": "Done"}))
        websocket.on_message(receive)

    page.route_web_socket("ws://localhost:8001/ws/tutor", websocket_handler)
    page.route(
        "http://localhost:8001/upload-audio",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"success": True, "upload_id": "mock-upload-id"}),
        ),
    )
    page.goto(URL, wait_until="networkidle")
    page.locator('input[type="file"]').set_input_files(ROOT / "tests" / "audio" / "pop.wav")
    page.get_by_text("Why this chord?").wait_for()
    page.get_by_text("Why this chord?").click()
    page.get_by_text("Mixed evidence").wait_for()
    assert page.get_by_text("Notes heard: C D F# A").is_visible()
    page.get_by_role("button", name="Wrong chord").click()
    feedback = page.evaluate(
        "JSON.parse(localStorage.getItem('horizonjam_evidence_feedback_v1'))"
    )
    record = feedback[-1]
    serialized = json.dumps(record).lower()
    assert record["user_feedback"] == "wrong"
    assert record["audio_identifier"].startswith("session:")
    assert all(token not in serialized for token in ("mock-session.wav", "pop.wav", "file_path", "audio_bytes"))
    assert page.get_by_role("button", name="Wrong chord").get_attribute("aria-pressed") == "true"
    page.screenshot(path=screenshot, full_page=True)
    return {
        "viewport": page.viewport_size,
        "feedback_records": len(feedback),
        "body_scroll_width": page.evaluate("document.body.scrollWidth"),
        "viewport_width": page.evaluate("window.innerWidth"),
    }


def main() -> int:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE))
        desktop = browser.new_page(viewport={"width": 1440, "height": 1000})
        desktop_result = _run_view(desktop, SCREENSHOTS / "evidence_ux_desktop.png")
        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_result = _run_view(mobile, SCREENSHOTS / "evidence_ux_mobile.png")
        browser.close()
    assert desktop_result["body_scroll_width"] <= desktop_result["viewport_width"]
    assert mobile_result["body_scroll_width"] <= mobile_result["viewport_width"]
    print(json.dumps({"desktop": desktop_result, "mobile": mobile_result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
