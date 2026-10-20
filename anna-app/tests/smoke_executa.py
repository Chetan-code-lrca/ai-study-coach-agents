"""Exercise the real Executa process with a mocked Anna Sampling response.

This is an integration smoke test for CI. It does not contact Anna or a model:
it starts the same console script Anna uses, performs the JSON-RPC handshake,
answers the reverse sampling request, and checks the app-tool response.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "executas" / "study-coach"
COMMAND = ["uv", "run", "--project", str(PROJECT), "tool-dev-ai-study-coach"]


def _reader(stream: Any, target: queue.Queue[str | None]) -> None:
    try:
        for line in stream:
            target.put(line)
    finally:
        target.put(None)


def _wait_for_frame(
    frames: queue.Queue[str | None],
    predicate: Callable[[dict[str, Any]], bool],
    process: subprocess.Popen[str],
    stderr_lines: list[str],
    timeout: float = 45.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    skipped: list[str] = []
    while time.monotonic() < deadline:
        remaining = max(0.1, deadline - time.monotonic())
        try:
            line = frames.get(timeout=remaining)
        except queue.Empty:
            break
        if line is None:
            raise AssertionError(
                "Executa closed stdout before returning the expected frame. "
                f"returncode={process.poll()}, stderr={''.join(stderr_lines)}"
            )
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            skipped.append(line)
            continue
        if predicate(frame):
            return frame
        skipped.append(line)
    raise AssertionError(
        "Timed out waiting for an Executa JSON-RPC frame. "
        f"Skipped={skipped!r}; returncode={process.poll()}; stderr={''.join(stderr_lines)}"
    )


def _send(process: subprocess.Popen[str], frame: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(frame, separators=(",", ":")) + "\n")
    process.stdin.flush()


def main() -> None:
    stdout_queue: queue.Queue[str | None] = queue.Queue()
    stderr_lines: list[str] = []
    process = subprocess.Popen(
        COMMAND,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    assert process.stdout is not None and process.stderr is not None
    threading.Thread(
        target=_reader, args=(process.stdout, stdout_queue), daemon=True
    ).start()

    def read_stderr() -> None:
        for line in process.stderr:
            stderr_lines.append(line)

    threading.Thread(target=read_stderr, daemon=True).start()

    try:
        _send(process, {"jsonrpc": "2.0", "method": "describe", "id": 1})
        described = _wait_for_frame(stdout_queue, lambda item: item.get("id") == 1, process, stderr_lines)
        manifest = described.get("result") or {}
        assert manifest.get("host_capabilities") == ["llm.sample"], manifest
        assert manifest.get("tools", [{}])[0].get("name") == "study_coach", manifest

        _send(process, {"jsonrpc": "2.0", "method": "health", "id": 2})
        healthy = _wait_for_frame(stdout_queue, lambda item: item.get("id") == 2, process, stderr_lines)
        assert (healthy.get("result") or {}).get("status") == "healthy", healthy

        _send(
            process,
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {"protocolVersion": "2.0"},
                "id": 3,
            },
        )
        initialized = _wait_for_frame(stdout_queue, lambda item: item.get("id") == 3, process, stderr_lines)
        assert (initialized.get("result") or {}).get("protocolVersion") == "2.0", initialized
        assert (initialized.get("result") or {}).get("client_capabilities") == {"sampling": {}}, initialized

        _send(
            process,
            {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "tool": "study_coach",
                    "arguments": {
                        "action": "generate_study_plan",
                        "subject": "Operating Systems",
                        "level": "Intermediate",
                        "weeks": 2,
                        "hours_per_day": 1,
                    },
                    "invoke_id": "ci-smoke",
                },
                "id": 4,
            },
        )

        sampling_request = _wait_for_frame(
            stdout_queue,
            lambda item: item.get("method") == "sampling/createMessage",
            process,
            stderr_lines,
        )
        params = sampling_request.get("params") or {}
        assert params.get("maxTokens") == 3000, sampling_request
        assert params.get("messages"), sampling_request

        # Stub Anna's host-side model response to exercise the complete tool
        # request/response path without credentials, network calls, or billing.
        _send(
            process,
            {
                "jsonrpc": "2.0",
                "id": sampling_request["id"],
                "result": {
                    "content": {"type": "text", "text": "Mock study plan from CI."},
                    "model": "ci-mock-model",
                    "usage": {"inputTokens": 12, "outputTokens": 8},
                    "stopReason": "endTurn",
                },
            },
        )
        invoked = _wait_for_frame(stdout_queue, lambda item: item.get("id") == 4, process, stderr_lines)
        result = invoked.get("result") or {}
        assert result.get("success") is True, invoked
        assert result.get("tool") == "study_coach", invoked
        assert (result.get("data") or {}).get("text") == "Mock study plan from CI.", invoked
        assert (result.get("data") or {}).get("model") == "ci-mock-model", invoked

        _send(process, {"jsonrpc": "2.0", "method": "shutdown", "id": 5})
        _wait_for_frame(stdout_queue, lambda item: item.get("id") == 5, process, stderr_lines)
        if process.stdin:
            process.stdin.close()
        process.wait(timeout=15)
        assert process.returncode == 0, f"Unexpected exit: {process.returncode}; stderr={''.join(stderr_lines)}"
        print("Executa startup, health, initialize, reverse-sampling dispatch, and invoke response passed.")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
