"""Offline tests for the Care Copilot response parser.

The payload shape mirrors what the Agent Bricks Multi-Agent Supervisor actually
returns (verified against the partner test notebook): interleaved text chunks
with `<name>sub-agent</name>` routing markers, final synthesized answer last.
"""

from care_harness.care_copilot import _extract_answer


def _payload(*texts: str) -> dict:
    return {
        "output": [
            {"content": [{"type": "output_text", "text": t} for t in texts]},
        ]
    }


def test_final_answer_after_routing_markers():
    payload = _payload(
        "I'll query the Knowledge Assistant.",
        "<name>knowledge-assistant-better2gether</name>",
        "**BATT-CRIT** means the battery is below 8%.",
        "<name>supervisor-agent-better2gether</name>",
        "A BATT-CRIT alert means the battery dropped below 8%. Tell the member to charge now.",
    )
    answer = _extract_answer(payload)
    assert answer.startswith("A BATT-CRIT alert means")
    assert "knowledge-assistant-better2gether" in answer  # routing footer
    assert "supervisor-agent-better2gether" in answer


def test_no_markers_returns_last_text():
    payload = _payload("first chunk", "the actual answer")
    assert _extract_answer(payload) == "the actual answer"


def test_empty_payload():
    assert "no text" in _extract_answer({"output": []})


def test_multiple_output_items():
    payload = {
        "output": [
            {"content": [{"type": "output_text", "text": "<name>genie-space</name>"}]},
            {"content": "not-a-list-ignored"},
            {"content": [{"type": "output_text", "text": "42 alerts in region West."}]},
        ]
    }
    answer = _extract_answer(payload)
    assert answer.startswith("42 alerts in region West.")
    assert "genie-space" in answer
