#!/usr/bin/env python3
"""Normalize agent/session logs into the runtime-observability schema."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from session_logs_provider import fetch_provider_payload, resolve_memory_path


NORMALIZED_FIELDS = [
    "step",
    "timestamp",
    "event_type",
    "actor",
    "tool_name",
    "model",
    "input_tokens",
    "output_tokens",
    "duration_ms",
    "status",
    "input_summary",
    "output_summary",
    "source_type",
    "session_id",
    "raw",
]


def first_present(event: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in event and event[key] not in (None, ""):
            return event[key]
    return "unknown"


def normalize_event(event: dict[str, Any], step: int) -> dict[str, Any]:
    normalized = {
        "step": step,
        "timestamp": first_present(event, ["timestamp", "time", "created_at", "ts"]),
        "event_type": first_present(event, ["event_type", "type", "kind"]),
        "actor": first_present(event, ["actor", "role", "source"]),
        "tool_name": first_present(event, ["tool_name", "tool", "toolName"]),
        "model": first_present(event, ["model", "model_name", "modelName"]),
        "input_tokens": first_present(event, ["input_tokens", "prompt_tokens", "inputTokenCount"]),
        "output_tokens": first_present(event, ["output_tokens", "completion_tokens", "outputTokenCount"]),
        "duration_ms": first_present(event, ["duration_ms", "latency_ms", "elapsed_ms"]),
        "status": first_present(event, ["status", "result", "state"]),
        "input_summary": first_present(
            event,
            ["input_summary", "request_summary", "input", "prompt", "message"],
        ),
        "output_summary": first_present(
            event,
            ["output_summary", "response_summary", "output", "result_summary", "response"],
        ),
        "source_type": first_present(event, ["source_type"]),
        "session_id": first_present(event, ["session_id"]),
        "raw": event,
    }

    if normalized["event_type"] == "unknown":
        if normalized["tool_name"] != "unknown":
            normalized["event_type"] = "tool_call"
        elif normalized["model"] != "unknown":
            normalized["event_type"] = "model_call"

    if normalized["actor"] == "unknown":
        normalized["actor"] = "agent"

    return normalized


def enrich_normalized_event(
    normalized: dict[str, Any],
    session_id: str | None = None,
    default_source_type: str | None = None,
) -> dict[str, Any]:
    if default_source_type and normalized["source_type"] == "unknown":
        normalized["source_type"] = default_source_type
    if session_id and normalized["session_id"] == "unknown":
        normalized["session_id"] = session_id
    return normalized


def normalize_session_memory_event(event: dict[str, Any], step: int, session_id: str) -> dict[str, Any]:
    actions = event.get("actions", [])
    learned = event.get("learned", [])
    action_summary = "; ".join(actions[:3]) if isinstance(actions, list) else "unknown"
    if isinstance(actions, list) and len(actions) > 3:
        action_summary += f"; ... (+{len(actions) - 3} more)"
    learned_summary = "; ".join(learned[:2]) if isinstance(learned, list) else "unknown"

    return {
        "step": step,
        "timestamp": event.get("message_summary_time", "unknown"),
        "event_type": "session_summary",
        "actor": "agent",
        "tool_name": "unknown",
        "model": "unknown",
        "input_tokens": "unknown",
        "output_tokens": "unknown",
        "duration_ms": "unknown",
        "status": "success",
        "input_summary": event.get("intent", "unknown"),
        "output_summary": event.get("outcome", "unknown"),
        "source_type": "session_memory",
        "session_id": session_id,
        "raw": {
            **event,
            "actions_summary": action_summary,
            "learned_summary": learned_summary,
        },
    }


def load_json_payload(
    payload: Any,
    session_id: str | None = None,
    default_source_type: str | None = None,
) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        events = payload.get("events", [])
    else:
        raise ValueError("Unsupported log payload")

    if not isinstance(events, list):
        raise ValueError("Expected a JSON array or an object with an 'events' array")

    normalized_events = []
    for idx, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValueError(f"Event #{idx} is not an object")
        normalized_events.append(
            enrich_normalized_event(
                normalize_event(event, idx),
                session_id=session_id,
                default_source_type=default_source_type,
            )
        )
    return normalized_events


def load_jsonl_payload(
    path: Path,
    session_id: str | None = None,
    default_source_type: str | None = None,
) -> list[dict[str, Any]]:
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]
    inferred_session_id = session_id or infer_session_id_from_path(path)
    if all(isinstance(event, dict) and "intent" in event for event in events):
        return [
            normalize_session_memory_event(event, idx, inferred_session_id)
            for idx, event in enumerate(events, start=1)
        ]
    return [
        enrich_normalized_event(
            normalize_event(event, idx),
            session_id=inferred_session_id,
            default_source_type=default_source_type,
        )
        for idx, event in enumerate(events, start=1)
        if isinstance(event, dict)
    ]


def infer_session_id_from_path(path: Path) -> str:
    name = path.name
    prefix = "session_memory_"
    suffix = ".jsonl"
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix):-len(suffix)]
    return "unknown"


def load_events_from_path(path: Path, session_id: str | None = None) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return load_jsonl_payload(path, session_id=session_id)
    return load_json_payload(json.loads(path.read_text()), session_id=session_id)


def load_events_from_provider_payload(
    payload: Any,
    session_id: str,
) -> list[dict[str, Any]]:
    if isinstance(payload, list) and payload and all(isinstance(event, dict) for event in payload):
        return load_json_payload(
            payload,
            session_id=session_id,
            default_source_type="session_logs_provider",
        )
    if isinstance(payload, dict):
        return load_json_payload(
            payload,
            session_id=session_id,
            default_source_type="session_logs_provider",
        )
    raise ValueError("session_logs provider returned an unsupported payload")


def resolve_session_events(
    session_id: str,
    memory_root: Path,
    provider_command: str | None = None,
    provider_timeout_sec: int = 30,
) -> tuple[list[dict[str, Any]], str]:
    if provider_command:
        payload, source_descriptor = fetch_provider_payload(
            session_id=session_id,
            provider_command=provider_command,
            timeout_sec=provider_timeout_sec,
        )
        return load_events_from_provider_payload(payload, session_id), source_descriptor

    memory_path = resolve_memory_path(session_id, memory_root)
    return load_events_from_path(memory_path, session_id=session_id), str(memory_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize session log JSON into a stable schema")
    parser.add_argument("--input", help="Path to the raw session log JSON or JSONL")
    parser.add_argument("--session-id", help="Session id to resolve from local session artifacts")
    parser.add_argument("--output", required=True, help="Path to the normalized JSON output")
    parser.add_argument(
        "--memory-root",
        default=os.path.expanduser("~/.trae-cn/memory/projects"),
        help="Root directory used to resolve session_memory_<id>.jsonl files",
    )
    parser.add_argument(
        "--provider-command",
        default=os.environ.get("RUNTIME_OBSERVABILITY_SESSION_PROVIDER_CMD"),
        help="Command template used to fetch raw session logs. Use {session_id} or allow automatic --session-id appending.",
    )
    parser.add_argument(
        "--provider-timeout-sec",
        type=int,
        default=30,
        help="Timeout in seconds for the external session_logs provider command",
    )
    args = parser.parse_args()

    if not args.input and not args.session_id:
        raise SystemExit("One of --input or --session-id is required")

    memory_root = Path(args.memory_root)
    output_path = Path(args.output)
    if args.input:
        normalized_events = load_events_from_path(Path(args.input), session_id=args.session_id)
    else:
        normalized_events, _ = resolve_session_events(
            session_id=args.session_id,
            memory_root=memory_root,
            provider_command=args.provider_command,
            provider_timeout_sec=args.provider_timeout_sec,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(normalized_events, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
