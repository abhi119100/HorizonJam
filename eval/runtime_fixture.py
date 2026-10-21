"""Evaluation-only backend: real relay/transport, deterministic provider substitutes."""
import time
import tutor_ws_relay as relay
from eval.browser_evidence_ux_check import ANALYSIS


class FixtureTutor:
    def _run_horizon_jam(self, path):
        return ANALYSIS

    def _retrieve_rag_context(self, result, question):
        if question == "slow":
            time.sleep(2)
        if question == "fail":
            raise RuntimeError("Fixture provider unavailable")
        return {}

    def stream_rag_tutoring(self, **kwargs):
        text = "The detected harmony is uncertain. Practice the transition slowly."
        kwargs["websocket_callback"](text)
        return text


relay.manager.tutor = FixtureTutor()
app = relay.app


@app.get("/__test/state")
def state():
    return {"sessions": len(relay.uploads.sessions), "uploads": sum(len(s.uploads) for s in relay.uploads.sessions.values()), "jobs": len(relay.manager.tasks)}
