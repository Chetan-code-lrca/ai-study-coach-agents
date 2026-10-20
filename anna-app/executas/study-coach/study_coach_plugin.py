"""AI Study Coach Executa: use Anna host sampling for study actions."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from executa_sdk import PROTOCOL_VERSION_V2, SamplingClient, SamplingError

from study_logic import build_request


MANIFEST = {
    "display_name": "AI Study Coach Engine",
    "version": "0.1.0",
    "description": (
        "Generates study plans, explains supplied study material, answers "
        "source-grounded questions, and creates quizzes using Anna host sampling."
    ),
    "author": "AI Study Coach",
    "host_capabilities": ["llm.sample"],
    "tools": [
        {
            "name": "study_coach",
            "description": (
                "Perform one AI Study Coach action. Supported actions are "
                "generate_study_plan, summarize_material, explain_concepts, "
                "answer_question, and generate_quiz. Uses the Anna host LLM; "
                "no model-provider API key is required by the app."
            ),
            "parameters": [
                {
                    "name": "action",
                    "type": "string",
                    "description": (
                        "Action name: generate_study_plan, summarize_material, "
                        "explain_concepts, answer_question, or generate_quiz."
                    ),
                    "required": True,
                },
                {"name": "subject", "type": "string", "description": "Study-plan subject.", "required": False, "default": "Computer Science"},
                {"name": "level", "type": "string", "description": "Study level: Beginner, Intermediate, or Advanced.", "required": False, "default": "Intermediate"},
                {"name": "weeks", "type": "integer", "description": "Study-plan duration from 1 to 12 weeks.", "required": False, "default": 4},
                {"name": "hours_per_day", "type": "number", "description": "Available study hours per day, from 0.5 to 8.", "required": False, "default": 2},
                {"name": "goals", "type": "string", "description": "Optional learning goals.", "required": False, "default": ""},
                {"name": "material", "type": "string", "description": "Study material for summarization, explanation, or grounded Q&A; up to 30000 characters.", "required": False, "default": ""},
                {"name": "question", "type": "string", "description": "Question to answer using supplied material.", "required": False, "default": ""},
                {"name": "topic", "type": "string", "description": "Topic for a practice quiz.", "required": False, "default": ""},
                {"name": "difficulty", "type": "string", "description": "Quiz difficulty: Easy, Medium, or Hard.", "required": False, "default": "Medium"},
                {"name": "count", "type": "integer", "description": "Quiz question count from 3 to 10.", "required": False, "default": 5},
                {"name": "source_material", "type": "string", "description": "Optional source material for a quiz; up to 30000 characters.", "required": False, "default": ""},
            ],
        }
    ],
    "runtime": {"type": "uv", "min_version": "0.1.0"},
}


_stdout_lock = threading.Lock()


def _write_frame(message: dict[str, Any]) -> None:
    """Write one JSON-RPC frame to stdout; diagnostics must use stderr."""
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    with _stdout_lock:
        sys.stdout.write(payload + "\n")
        sys.stdout.flush()


sampling = SamplingClient(write_frame=_write_frame)


async def _run_study_coach(args: dict[str, Any], *, invoke_id: str) -> dict[str, Any]:
    action = args.get("action", "")
    request = build_request(action, args)
    result = await sampling.create_message(
        messages=[
            {
                "role": "user",
                "content": {"type": "text", "text": request["prompt"]},
            }
        ],
        max_tokens=request["max_tokens"],
        system_prompt=request["system_prompt"],
        metadata={
            "executa_invoke_id": invoke_id,
            "tool": "study_coach",
            "action": action,
        },
        timeout=90.0,
    )
    content = result.get("content") or {}
    output_text = ""
    if isinstance(content, dict) and content.get("type") == "text":
        output_text = str(content.get("text") or "").strip()
    if not output_text:
        raise RuntimeError("Anna's model returned an empty response. Please try again.")
    return {
        "action": action,
        "text": output_text,
        "model": result.get("model"),
        "usage": result.get("usage"),
        "stopReason": result.get("stopReason"),
    }


def _response(request_id: Any, *, result: Any = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    frame: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        frame["error"] = error
    else:
        frame["result"] = result
    return frame


def _handle_initialize(request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    protocol = (params or {}).get("protocolVersion") or "1.1"
    if protocol != PROTOCOL_VERSION_V2:
        sampling.disable(
            f"Host offered protocolVersion={protocol!r}; "
            "Anna LLM sampling requires Executa protocol 2.0."
        )
    accepted = protocol if protocol in ("1.1", "2.0") else "2.0"
    return _response(
        request_id,
        result={
            "protocolVersion": accepted,
            "serverInfo": {
                "name": MANIFEST["display_name"],
                "version": MANIFEST["version"],
            },
            "client_capabilities": {"sampling": {}} if accepted == PROTOCOL_VERSION_V2 else {},
            "capabilities": {},
        },
    )


def _handle_invoke(request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    tool = params.get("tool")
    if tool != "study_coach":
        return _response(request_id, result={"success": False, "error": f"Unknown tool: {tool}"})

    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        return _response(request_id, result={"success": False, "error": "Action arguments must be an object."})

    invoke_id = str(params.get("invoke_id") or "")
    future = asyncio.run_coroutine_threadsafe(
        _run_study_coach(args, invoke_id=invoke_id),
        _loop,
    )
    try:
        data = future.result(timeout=110.0)
        return _response(request_id, result={"success": True, "data": data})
    except (ValueError, TypeError) as exc:
        return _response(request_id, result={"success": False, "error": str(exc)})
    except SamplingError as exc:
        message = getattr(exc, "message", str(exc))
        return _response(
            request_id,
            result={"success": False, "error": f"Anna LLM request failed: {message}"},
        )
    except Exception as exc:  # noqa: BLE001 - turn runtime failures into a readable app error
        print(f"study_coach invoke failed: {exc}", file=sys.stderr, flush=True)
        return _response(
            request_id,
            result={
                "success": False,
                "error": "The study request failed. Check Anna sampling permission and try again.",
            },
        )


def _handle_message(raw: str) -> None:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        _write_frame(_response(None, error={"code": -32700, "message": "Parse error"}))
        return

    # Sampling replies share stdin with ordinary requests and must be dispatched
    # while an invoke coroutine is waiting for the host response.
    if "method" not in message:
        if not sampling.dispatch_response(message):
            print(f"Unmatched host response id={message.get('id')!r}", file=sys.stderr)
        return

    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        response = _handle_initialize(request_id, params)
    elif method == "describe":
        response = _response(request_id, result=MANIFEST)
    elif method == "health":
        response = _response(
            request_id,
            result={"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": MANIFEST["version"]},
        )
    elif method == "invoke":
        response = _handle_invoke(request_id, params)
    elif method == "shutdown":
        response = _response(request_id, result={"ok": True})
    else:
        response = _response(
            request_id,
            error={"code": -32601, "message": f"Method not found: {method}"},
        )

    if request_id is not None:
        _write_frame(response)


_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, name="anna-sampling-loop", daemon=True)
_loop_thread.start()


def main() -> None:
    """Serve JSON-RPC messages on stdio for the lifetime of the Executa."""
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="study-coach-invoke") as pool:
        try:
            for raw in sys.stdin:
                line = raw.strip()
                if line:
                    pool.submit(_handle_message, line)
        finally:
            _loop.call_soon_threadsafe(_loop.stop)


if __name__ == "__main__":
    main()
