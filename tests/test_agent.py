
from types import SimpleNamespace

import agent.graph as agent_graph


class FakeLLM:
    """Return predefined responses without calling the real API."""

    def __init__(self, responses):
        self.responses = iter(responses)

    def invoke(self, prompt):
        return SimpleNamespace(content=next(self.responses))


def fake_runner(code):
    """Simulate execution results for deterministic tests."""
    if "print(1 / 0)" in code:
        return {
            "success": False,
            "stdout": "",
            "stderr": "ZeroDivisionError: division by zero",
            "timed_out": False,
        }

    if "print(42)" in code:
        return {
            "success": True,
            "stdout": "42\n",
            "stderr": "",
            "timed_out": False,
        }

    if "print(0)" in code:
        return {
            "success": True,
            "stdout": "0\n",
            "stderr": "",
            "timed_out": False,
        }

    return {
        "success": True,
        "stdout": "Other output\n",
        "stderr": "",
        "timed_out": False,
    }


def test_correct_result_is_verified(monkeypatch):
    monkeypatch.setattr(
        agent_graph,
        "llm",
        FakeLLM([
            "```python\nprint(42)\n```",
            "PASS\nReason: The output matches the task.",
        ]),
    )
    monkeypatch.setattr(agent_graph, "run_python", fake_runner)

    result = agent_graph.run_agent(
        "Write a script that prints the sum of 15 and 27."
    )

    assert result["success"] is True
    assert result["verified"] is True
    assert result["attempts"] == 1
    assert result["output"].strip() == "42"


def test_incorrect_result_triggers_repair(monkeypatch):
    monkeypatch.setattr(
        agent_graph,
        "llm",
        FakeLLM([
            "```python\nprint(0)\n```",
            "FAIL\nReason: Expected 42, but received 0.",
            "```python\nprint(42)\n```",
            "PASS\nReason: The output matches the task.",
        ]),
    )
    monkeypatch.setattr(agent_graph, "run_python", fake_runner)

    result = agent_graph.run_agent(
        "Write a script that prints the sum of 15 and 27."
    )

    assert result["success"] is True
    assert result["verified"] is True
    assert result["attempts"] == 2
    assert result["output"].strip() == "42"


def test_runtime_error_triggers_repair(monkeypatch):
    monkeypatch.setattr(
        agent_graph,
        "llm",
        FakeLLM([
            "```python\nprint(1 / 0)\n```",
            "```python\nprint(42)\n```",
            "PASS\nReason: The output matches the task.",
        ]),
    )
    monkeypatch.setattr(agent_graph, "run_python", fake_runner)

    result = agent_graph.run_agent("Print 42.")

    assert result["success"] is True
    assert result["attempts"] == 2
    assert result["output"].strip() == "42"


def test_agent_stops_after_max_attempts(monkeypatch):
    monkeypatch.setattr(
        agent_graph,
        "llm",
        FakeLLM([
            "```python\nprint(0)\n```",
            "FAIL\nReason: Expected 42, but received 0.",
            "```python\nprint(0)\n```",
            "FAIL\nReason: The output is still incorrect.",
            "```python\nprint(0)\n```",
            "FAIL\nReason: The output remains incorrect.",
        ]),
    )
    monkeypatch.setattr(agent_graph, "run_python", fake_runner)

    result = agent_graph.run_agent("Print 42.")

    assert result["attempts"] == agent_graph.MAX_ATTEMPTS
    assert result["success"] is False
    assert result["verified"] is False
