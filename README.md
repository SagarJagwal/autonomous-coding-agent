# Autonomous AI Coding Agent

An LLM-powered Python coding agent that generates code from natural-language tasks, executes it in a Docker sandbox, evaluates the result, and attempts automated repairs when execution or verification fails.

## Features

- **Code generation:** Uses Groq-hosted LLMs to generate Python scripts from natural-language instructions.
- **Workflow orchestration:** Uses LangGraph to coordinate generation, execution, verification, and repair.
- **Sandboxed execution:** Runs generated code in Docker with network access disabled, resource limits, a read-only filesystem, and a non-root user.
- **Automated error recovery:** Uses execution errors and verification feedback to generate corrected code.
- **Bounded retries:** Limits execution attempts to prevent unbounded repair loops.
- **Verification:** Uses an LLM-based reviewer to assess whether generated code and its output satisfy the requested task.
- **Testing:** Includes automated tests for sandbox execution and agent workflow behavior.
- **Logging:** Records key workflow events for easier debugging.

## Tech Stack

Python, LangGraph, LangChain, Groq API, Docker, pytest, python-dotenv.

## Architecture

1. Receive a task in natural language.
2. Generate a Python script using the LLM.
3. Execute the script inside a constrained Docker container.
4. Evaluate execution results and task requirements.
5. Repair failed or incorrectly verified solutions.
6. Stop after success or the configured attempt limit.

## Project Structure

```text
autonomous-coding-agent/
├── agent/
│   └── graph.py
├── sandbox/
│   └── runner.py
├── tests/
│   ├── test_agent.py
│   └── test_runner.py
├── main.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Setup

Requirements: Python, Docker Desktop, and a Groq API key.

1. Clone the repository and navigate into the project directory.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Use your own API key and never commit `.env` to version control.

5. Ensure Docker Desktop is running.
6. Start the agent:

```bash
python main.py
```

7. Run the test suite:

```bash
python -m pytest -v
```

## Example

Input:

```text
Write a Python script that prints the sum of 15 and 27.
```

Output:

```text
Success: True
Attempts: 1

Output:
42
```

## Validation Results

- 8 automated tests passed in the current local test run.
- Tested normal execution, runtime exceptions, empty code, timeout handling, incorrect-result retries, and maximum-attempt behavior.
- Manually checked that the timeout path requested container cleanup and left no matching containers in the Docker container listing.

## Limitations and Future Improvements

- LLM-based verification can approve incorrect answers; deterministic assertions should be added for tasks with known expected outputs.
- Docker isolation reduces risk but does not guarantee complete protection against malicious code.
- Additional improvements include structured task specifications, stronger output validation, execution tracing, and broader integration tests.
- The project is a prototype and is not intended to execute untrusted code as a production service without further security review.

## Security

Keep API keys in environment variables. Do not commit credentials, `.env`, or virtual-environment files. Review the sandbox configuration before executing untrusted programs.