
import subprocess
import tempfile
from pathlib import Path
import uuid


DOCKER_IMAGE = "python:3.12-slim"
TIMEOUT_SECONDS = 10


def run_python(code: str) -> dict:
    """Execute Python code inside a restricted Docker container."""

    if not code or not code.strip():
        return {
            "success": False,
            "stdout": "",
            "stderr": "No Python code provided.",
            "timed_out": False,
        }

    with tempfile.TemporaryDirectory(prefix="coding-agent-") as temp_dir:
        script_path = Path(temp_dir) / "main.py"
        script_path.write_text(code, encoding="utf-8")
        container_name = f"coding-agent-{uuid.uuid4().hex[:12]}"
        command = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--network", "none",
            "--memory", "128m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "--user", "65534:65534",
            "--mount",
            f"type=bind,source={script_path.resolve()},target=/app/main.py,readonly",
            "--workdir", "/app",
            DOCKER_IMAGE,
            "python", "-I", "/app/main.py",
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:10_000],
                "stderr": result.stderr[:10_000],
                "timed_out": False,
            }

        except subprocess.TimeoutExpired:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "Execution timed out; container cleanup requested.",
                "timed_out": True,
            }