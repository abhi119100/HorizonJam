import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from chordai_gpt_tutor import ChordAIRAGTutor
from detection import normalize_and_validate
from tutor_evidence import (
    assemble_tutor_context,
    assess_tutor_request,
    build_performance_evidence,
    build_retrieval_query,
    select_retrieved_evidence,
    verify_and_repair_response,
)
from tutor_ws_relay import TutorWebSocketManager


def chord_results(confidence=0.9, warnings=None, legacy=False, guitar=True):
    events = [
        {
            "start_time" if legacy else "start": 0.0,
            "end_time" if legacy else "end": 1.5,
            "chord_symbol" if legacy else "chord": "G",
            "confidence": confidence,
            "source_detector": "hybrid",
        },
        {
            "start_time" if legacy else "start": 1.5,
            "end_time" if legacy else "end": 3.0,
            "chord_symbol" if legacy else "chord": "C",
            "confidence": confidence,
            "source_detector": "hybrid",
        },
    ]
    result = {
        "analysis_summary": {
            "detected_key": "G Major",
            "chord_progression": "G - C",
            "total_chord_events": 2,
        },
        "chord_events": events,
        "detector_used": "hybrid",
        "warnings": warnings or [],
    }
    if guitar:
        result["chord_tabs"] = [{"chord": "G", "frets": "320003"}]
    return result


def search_results(include_irrelevant=False):
    results = []
    if include_irrelevant:
        results.append({
            "id": "noise-1",
            "rank": 1,
            "document": "A recipe for tomato soup and kitchen storage.",
            "source_file": "cooking.txt",
            "similarity_score": 0.95,
            "metadata": {"topic": "cooking"},
        })
    results.append({
        "id": "voice-leading-1",
        "rank": 2 if include_irrelevant else 1,
        "document": "G and C share the note G; keeping common tones can make guitar chord transitions smoother.",
        "source_file": "voice-leading.md",
        "similarity_score": 0.82,
        "metadata": {"topic": "guitar voice leading", "detected_key": "G Major"},
    })
    return {"total_results": len(results), "results": results}


class FakeRag:
    def __init__(self, result=None):
        self.result = result if result is not None else search_results()
        self.queries = []

    def query(self, query, n_results=5):
        self.queries.append((query, n_results))
        return self.result


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            midpoint = max(1, len(self.content) // 2)
            return [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=self.content[:midpoint]))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=self.content[midpoint:]))]),
            ]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def bare_tutor(content="G moves to C and creates a clear harmonic change."):
    tutor = object.__new__(ChordAIRAGTutor)
    tutor.client = FakeClient(content)
    tutor.rag_system = FakeRag()
    return tutor


class EvidenceGroundedTutorTests(unittest.TestCase):
    def test_detector_normalizer_repairs_and_preserves_confidence(self):
        events, warnings = normalize_and_validate([
            {"start": 1.0, "end": 2.0, "chord": "C", "confidence": 0.7},
            {"start": -0.5, "end": 1.5, "chord": "G", "confidence": 0.4},
            {"start": 2.0, "end": 3.0, "chord": "C", "confidence": 0.6},
        ])

        self.assertEqual([(e["start"], e["end"], e["chord"]) for e in events], [
            (0.0, 1.0, "G"),
            (1.0, 3.0, "C"),
        ])
        self.assertEqual([event["confidence"] for event in events], [0.4, 0.7])
        self.assertTrue(any("negative start" in warning for warning in warnings))
        self.assertTrue(any("overlapping" in warning for warning in warnings))
        self.assertTrue(any("merged" in warning for warning in warnings))

    def test_performance_evidence_preserves_detector_fields(self):
        result = chord_results(0.42, warnings=["clamped 1 overlapping interval"])
        evidence = build_performance_evidence(result, audio_id="fixture.wav")
        self.assertEqual(evidence.audio_id, "fixture.wav")
        self.assertEqual(evidence.detector, "hybrid")
        self.assertEqual(evidence.estimated_key, "G Major")
        self.assertEqual(evidence.warnings, ["clamped 1 overlapping interval"])
        self.assertEqual(evidence.chord_events[0].start, 0.0)
        self.assertEqual(evidence.chord_events[0].end, 1.5)
        self.assertEqual(evidence.chord_events[0].confidence, 0.42)
        self.assertEqual(evidence.chord_events[0].source_detector, "hybrid")
        self.assertEqual(evidence.chord_events[0].alternatives, [])
        self.assertEqual(evidence.instrument_context["instrument"], "guitar")

    def test_backward_compatible_event_shape(self):
        evidence = build_performance_evidence(chord_results(legacy=True))
        self.assertEqual([event.chord for event in evidence.chord_events], ["G", "C"])
        self.assertEqual(evidence.progression_summary, "G - C")

    def test_invalid_event_is_not_silently_accepted(self):
        result = chord_results()
        result["chord_events"][0]["end"] = 0.0
        with self.assertRaises(ValueError):
            build_performance_evidence(result)

    def test_retrieval_preserves_actual_content_and_provenance(self):
        selected = select_retrieved_evidence(search_results(), "guitar G C voice leading")
        self.assertEqual(selected["status"], "available")
        self.assertEqual(selected["evidence"][0]["evidence_id"], "voice-leading-1")
        self.assertEqual(selected["evidence"][0]["source"], "voice-leading.md")
        self.assertIn("common tones", selected["evidence"][0]["content"])

    def test_irrelevant_retrieval_candidate_is_not_selected(self):
        selected = select_retrieved_evidence(
            search_results(include_irrelevant=True), "guitar G C voice leading"
        )
        sources = [item["source"] for item in selected["evidence"]]
        self.assertEqual(sources, ["voice-leading.md"])
        noise = next(item for item in selected["candidates"] if item["source"] == "cooking.txt")
        self.assertFalse(noise["selected"])

    def test_no_result_retrieval_is_honest(self):
        selected = select_retrieved_evidence({"results": []}, "G C")
        self.assertEqual(selected["status"], "no_results")
        self.assertEqual(selected["evidence"], [])

    def test_context_sections_appear_once_and_include_document(self):
        performance = build_performance_evidence(chord_results())
        assessment = assess_tutor_request(performance, "Why does this progression work?")
        query = build_retrieval_query(performance, assessment, "Why does this progression work?")
        retrieval = select_retrieved_evidence(search_results(), query)
        context = assemble_tutor_context(performance, retrieval, "Why does this progression work?")
        user_message = context["messages"][1]["content"]
        for heading in (
            "USER QUESTION", "PERFORMANCE EVIDENCE", "RETRIEVED KNOWLEDGE",
            "UNCERTAINTIES / WARNINGS", "OUTPUT EXPECTATIONS",
        ):
            self.assertEqual(user_message.count(heading), 1)
        self.assertIn("common tones", user_message)
        self.assertIn('"confidence": 0.9', user_message)

    def test_low_confidence_response_is_repaired_before_delivery(self):
        performance = build_performance_evidence(chord_results(0.25))
        context = assemble_tutor_context(
            performance, select_retrieved_evidence({"results": []}, "G C"),
            "What chord am I playing?",
        )
        result = verify_and_repair_response("You are playing G, then C.", context)
        self.assertIn("added_uncertainty_caveat", result["repairs"])
        self.assertIn("uncertain", result["final_response"].lower())
        self.assertTrue(result["passed"])

    def test_false_retrieval_claim_is_removed_when_no_result(self):
        performance = build_performance_evidence(chord_results())
        context = assemble_tutor_context(
            performance, select_retrieved_evidence({"results": []}, "G C"), None
        )
        result = verify_and_repair_response(
            "According to the retrieved source, this is a cadence. Practice slowly.",
            context,
        )
        self.assertNotIn("retrieved source", result["final_response"].lower())
        self.assertIn("Practice slowly", result["final_response"])

    def test_real_retrieval_method_returns_selected_document(self):
        tutor = bare_tutor()
        context = tutor._retrieve_rag_context(
            chord_results(), "How can I make these transitions smoother?"
        )
        self.assertEqual(context["status"], "available")
        self.assertIn("common tones", context["evidence"][0]["content"])
        self.assertTrue(tutor.rag_system.queries)

    def test_nonstreaming_model_receives_grounded_context(self):
        tutor = bare_tutor("This likely moves from G to C; use the shared G tone.")
        rag = tutor._retrieve_rag_context(chord_results(), "Why does this work?")
        response = tutor._generate_rag_tutoring(chord_results(), rag, "Why does this work?")
        call = tutor.client.chat.completions.calls[0]
        self.assertIn("common tones", call["messages"][1]["content"])
        self.assertIn("0.9", call["messages"][1]["content"])
        self.assertIn("likely", response.lower())

    def test_streaming_delivers_only_verified_uncertainty_text(self):
        tutor = bare_tutor("You are definitely playing G and C. Practice slowly.")
        rag = tutor._retrieve_rag_context(chord_results(0.2), "What am I playing?")
        delivered = []
        traces = []
        response = tutor.stream_rag_tutoring(
            chord_results(0.2), rag, delivered.append, "What am I playing?", traces.append
        )
        self.assertTrue(delivered)
        self.assertIn("uncertain", delivered[0].lower())
        self.assertEqual(" ".join(delivered), response)
        self.assertIn("added_uncertainty_caveat", traces[0]["verification"]["repairs"])

    def test_developer_trace_contains_exact_model_input(self):
        tutor = bare_tutor()
        rag = tutor._retrieve_rag_context(chord_results(), "Why does this work?")
        trace = tutor.inspect_tutor_evidence(chord_results(), rag, "Why does this work?")
        self.assertEqual(trace["performance_evidence"]["detector"], "hybrid")
        self.assertEqual(trace["retrieval"]["evidence"][0]["evidence_id"], "voice-leading-1")
        self.assertIn("common tones", json.dumps(trace["model_messages"]))

    def test_user_contradiction_remains_question_not_observation(self):
        performance = build_performance_evidence(chord_results())
        context = assemble_tutor_context(
            performance, select_retrieved_evidence({"results": []}, "D major"),
            "I know I am playing D major. Why does it sound wrong?",
        )
        self.assertEqual(context["performance_evidence"]["progression_summary"], "G - C")
        self.assertIn("D major", context["user_question"])
        self.assertIn("not unquestionable ground truth", context["messages"][0]["content"])


class FakeWebSocket:
    def __init__(self):
        self.text_messages = []

    async def send_text(self, value):
        self.text_messages.append(json.loads(value))


class RelayEvidenceIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_active_relay_path_streams_verified_grounded_response(self):
        tutor = bare_tutor("You are definitely playing G then C. Use the shared G tone.")
        tutor._run_horizon_jam = lambda _path: chord_results(
            0.2, warnings=["clamped 1 overlapping interval"]
        )

        manager = TutorWebSocketManager()
        manager.tutor = tutor
        websocket = FakeWebSocket()
        manager.active_connections["client"] = websocket
        manager.send_text_chunk = AsyncMock()

        await manager.analyze_audio_streaming(
            "client", "fixture.wav", "Why does this progression work?"
        )

        types = [message["type"] for message in websocket.text_messages]
        self.assertIn("chord_analysis", types)
        self.assertIn("text_chunk", types)
        self.assertEqual(types[-1], "complete")
        complete = websocket.text_messages[-1]["full_response"]
        self.assertIn("uncertain", complete.lower())
        model_input = tutor.client.chat.completions.calls[0]["messages"][1]["content"]
        self.assertIn("clamped 1 overlapping interval", model_input)
        self.assertIn("common tones", model_input)
        self.assertGreaterEqual(manager.send_text_chunk.await_count, 1)


if __name__ == "__main__":
    unittest.main()
