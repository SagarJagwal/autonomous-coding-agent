
import os
import re
import logging
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from sandbox.runner import run_python

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0,
)


class AgentState(TypedDict):
    task: str
    code: str
    output: str
    error: str
    attempts: int
    success: bool
    execution_success: bool
    verified: bool
    verification_feedback: str


def extract_code(response: str) -> str:
    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        response,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else response.strip()


def generate_code(state: AgentState) -> dict:
    prompt = f"""
Write a complete Python script for this task:

{state['task']}

Requirements:
- Return only executable Python code.
- Print the requested result.
- Do not use network access, secrets, or external files.
- Do not catch or suppress exceptions unless the task requires it.
- If the task is impossible under its constraints, print a concise,
  truthful explanation rather than pretending it was completed.
- Return code inside a Python code fence.
"""
    logger.info("Generating code for task")
    response = llm.invoke(prompt)
    return {"code": extract_code(response.content)}


def execute_code(state: AgentState) -> dict:
    logger.info("Executing code: attempt %s", state["attempts"] + 1)
    result = run_python(state["code"])

    return {
        "output": result["stdout"],
        "error": result["stderr"],
        "execution_success": result["success"],
        "success": False,
        "verified": False,
        "attempts": state["attempts"] + 1,
    }


def verify_result(state: AgentState) -> dict:
    prompt = f"""
You are a strict software test reviewer.

User's task:
{state['task']}

Python code:
```python
{state['code']}
```

Actual program output:
{state['output']}

Execution error:
{state['error'] or "None"}

Decide whether the code and output satisfy the user's task.

Rules:
- Do not treat a successful process exit as proof of correctness.
- Check whether the output matches the requested result.
- If the task is impossible under its own constraints, a clear,
  truthful explanation of the contradiction is acceptable.
- If the result is incorrect, incomplete, or misleading, return FAIL.
- Do not assume that unshown behavior works.

Return exactly one of these formats:

PASS
Reason: brief explanation

or

FAIL
Reason: brief explanation
"""
    response = llm.invoke(prompt)
    verdict = response.content.strip()

    verified = verdict.upper().startswith("PASS")
    logger.info("Verification result: %s", "PASS" if verified else "FAIL")

    return {
        "verified": verified,
        "success": verified,
        "verification_feedback": verdict,
    }


def repair_code(state: AgentState) -> dict:
    prompt = f"""
Fix the Python script below.

User's task:
{state['task']}

Previous code:
```python
{state['code']}
```

Execution error:
{state['error'] or "None"}

Verification feedback:
{state['verification_feedback'] or "Execution failed."}

Previous output:
{state['output']}

Requirements:
- Fix the actual problem identified by the error or reviewer.
- Preserve the user's original requirements.
- Do not repeat the same failed solution.
- If the task is impossible as written, produce a truthful
  explanation of the contradiction.
- Return only the complete Python script inside a code fence.
"""
    logger.info("Requesting code repair")
    response = llm.invoke(prompt)
    return {"code": extract_code(response.content)}


def after_execution(state: AgentState) -> str:
    if state["execution_success"]:
        return "verify"

    if state["attempts"] >= MAX_ATTEMPTS:
        return "finish"

    return "repair"


def after_verification(state: AgentState) -> str:
    if state["verified"] or state["attempts"] >= MAX_ATTEMPTS:
        return "finish"

    return "repair"


builder = StateGraph(AgentState)

builder.add_node("generate", generate_code)
builder.add_node("execute", execute_code)
builder.add_node("verify", verify_result)
builder.add_node("repair", repair_code)

builder.add_edge(START, "generate")
builder.add_edge("generate", "execute")

builder.add_conditional_edges(
    "execute",
    after_execution,
    {
        "verify": "verify",
        "repair": "repair",
        "finish": END,
    },
)

builder.add_conditional_edges(
    "verify",
    after_verification,
    {
        "repair": "repair",
        "finish": END,
    },
)

builder.add_edge("repair", "execute")

graph = builder.compile()


def run_agent(task: str) -> dict:
    return graph.invoke(
        {
            "task": task,
            "code": "",
            "output": "",
            "error": "",
            "attempts": 0,
            "success": False,
            "execution_success": False,
            "verified": False,
            "verification_feedback": "",
        }
    )
