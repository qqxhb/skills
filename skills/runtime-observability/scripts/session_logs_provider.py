#!/usr/bin/env python3
"""Helpers for resolving raw session logs from pluggable providers."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any


def resolve_memory_path(session_id: str, memory_root: Path) -> Path:
    direct_matches = list(memory_root.glob(f"**/session_memory_{session_id}.jsonl"))
    if direct_matches:
        return direct_matches[0]
    raise FileNotFoundError(
        f"Could not resolve session id {session_id} under {memory_root}"
    )


def build_provider_command(provider_command: str, session_id: str) -> list[str]:
    rendered = provider_command.format(session_id=session_id)
    if "{session_id}" in provider_command:
        return shlex.split(rendered)
    return shlex.split(rendered) + ["--session-id", session_id]


def parse_provider_stdout(stdout: str) -> Any:
    stripped = stdout.strip()
    if not stripped:
        raise ValueError("session_logs provider returned empty output")

    if stripped[0] in "[{":
        return json.loads(stripped)

    lines = [line for line in stripped.splitlines() if line.strip()]
    parsed_lines = [json.loads(line) for line in lines]
    return parsed_lines


def fetch_provider_payload(
    session_id: str,
    provider_command: str,
    timeout_sec: int = 30,
) -> tuple[Any, str]:
    command = build_provider_command(provider_command, session_id)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "unknown provider error"
        raise RuntimeError(
            f"session_logs provider failed for session {session_id}: {stderr}"
        )
    payload = parse_provider_stdout(completed.stdout)
    return payload, "provider:" + " ".join(command)
