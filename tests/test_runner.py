
from sandbox.runner import run_python


def test_successful_execution():
    result = run_python("print(2 + 3)")

    assert result["success"] is True
    assert result["stdout"].strip() == "5"


def test_runtime_error():
    result = run_python("print(1 / 0)")

    assert result["success"] is False
    assert "ZeroDivisionError" in result["stderr"]


def test_empty_code():
    result = run_python("")

    assert result["success"] is False
    assert "No Python code" in result["stderr"]


def test_infinite_loop_times_out():
    result = run_python("while True:\n    pass")

    assert result["success"] is False
    assert result["timed_out"] is True
