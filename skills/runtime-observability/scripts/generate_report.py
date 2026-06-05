#!/usr/bin/env python3
"""Generate a markdown runtime observability report from session log JSON."""

from __future__ import annotations

import argparse
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from normalize_session_log import load_events_from_path, resolve_session_events


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or value == "unknown":
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def fmt_duration_ms(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{int(value)} ms"
    return "unknown"


def fmt_tokens(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(int(value))
    return "unknown"


def short_time(value: Any) -> str:
    parsed = parse_timestamp(value)
    return parsed.strftime("%H:%M:%SZ") if parsed else "unknown"


def compute_total_duration(events: list[dict[str, Any]]) -> str:
    timestamps = [parse_timestamp(event["timestamp"]) for event in events]
    timestamps = [ts for ts in timestamps if ts is not None]
    if len(timestamps) < 2:
        return "unknown"
    seconds = int((max(timestamps) - min(timestamps)).total_seconds())
    return f"about {seconds} seconds"


def model_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event["event_type"] == "model_call"]


def tool_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event["event_type"] == "tool_call"]


def summary_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event["event_type"] == "session_summary"]


def provider_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("source_type") == "session_logs_provider"]


def find_token_spike(models: list[dict[str, Any]]) -> dict[str, Any] | None:
    inputs = [event["input_tokens"] for event in models if isinstance(event["input_tokens"], (int, float))]
    if len(inputs) < 2:
        return None
    max_event = max(
        (event for event in models if isinstance(event["input_tokens"], (int, float))),
        key=lambda event: event["input_tokens"],
    )
    baseline = median(inputs)
    if baseline <= 0:
        return None
    if max_event["input_tokens"] >= baseline * 2:
        return max_event
    return None


def find_redundant_tool_calls(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    redundant = []
    for current, previous in zip(tools[1:], tools[:-1]):
        if (
            current["tool_name"] == previous["tool_name"]
            and current["input_summary"] == previous["input_summary"]
            and current["tool_name"] != "unknown"
        ):
            redundant.append(current)
    return redundant


def quality_scores(events: list[dict[str, Any]], spike: dict[str, Any] | None, redundant: list[dict[str, Any]]) -> tuple[int, int, int]:
    output_compliance = 35
    factual_grounding = 40
    scope_discipline = 25
    summaries_only = (
        any(event["event_type"] == "session_summary" for event in events)
        and not any(event["event_type"] == "tool_call" for event in events)
        and not any(event["event_type"] == "model_call" for event in events)
    )

    missing_duration = any(
        event["event_type"] == "model_call" and event["duration_ms"] == "unknown" for event in events
    )
    if missing_duration:
        output_compliance -= 4
    if summaries_only:
        output_compliance -= 7
        factual_grounding -= 12
        scope_discipline -= 5

    if spike is not None:
        factual_grounding -= 3
    if redundant:
        scope_discipline -= min(7, 3 + len(redundant) * 2)

    return output_compliance, factual_grounding, scope_discipline


def build_issue_lines(events: list[dict[str, Any]], spike: dict[str, Any] | None, redundant: list[dict[str, Any]]) -> list[str]:
    issues = []
    if redundant:
        for event in redundant:
            issues.append(
                "- Severity: medium; Issue: "
                f"{event['tool_name']} call #{event['step']} appears redundant; Evidence: it repeats the same tool and input summary "
                "as the previous call; Fix: stop after the first successful lookup unless a new branch appears."
            )
    if spike is not None:
        issues.append(
            "- Severity: high; Issue: model call "
            f"#{spike['step']} has a token spike; Evidence: it uses {spike['input_tokens']} input tokens, far above neighboring calls; "
            "Fix: summarize or chunk the fetched log before replaying it to the model."
        )

    missing_duration = [
        event for event in events if event["event_type"] == "model_call" and event["duration_ms"] == "unknown"
    ]
    if missing_duration:
        issues.append(
            "- Severity: low; Issue: exact timing totals are incomplete; Evidence: at least one model call lacks `duration_ms`; "
            "Fix: preserve timing as `unknown` rather than pretending the totals are exact."
        )
    return issues


def build_markdown(events: list[dict[str, Any]], source_label: str, source_path: str) -> str:
    models = model_events(events)
    tools = tool_events(events)
    summaries = summary_events(events)
    provider_backed = bool(provider_events(events))
    summaries_only = bool(summaries and not tools and not models)
    spike = find_token_spike(models)
    redundant = find_redundant_tool_calls(tools)
    output_compliance, factual_grounding, scope_discipline = quality_scores(events, spike, redundant)
    total_score = output_compliance + factual_grounding + scope_discipline

    total_tokens = sum(
        int(event["input_tokens"]) + int(event["output_tokens"])
        for event in models
        if isinstance(event["input_tokens"], (int, float)) and isinstance(event["output_tokens"], (int, float))
    )

    session_label = "unknown"
    for event in tools:
        summary = event["input_summary"]
        if isinstance(summary, str) and "sess_" in summary:
            session_label = summary.split()[-1]
            break
    if session_label == "unknown":
        for event in events:
            if event.get("session_id") not in (None, "", "unknown"):
                session_label = str(event["session_id"])
                break

    tool_counts = Counter(event["tool_name"] for event in tools)
    model_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0})
    for event in models:
        model = str(event["model"])
        model_totals[model]["calls"] += 1
        if isinstance(event["input_tokens"], (int, float)):
            model_totals[model]["input"] += int(event["input_tokens"])
        if isinstance(event["output_tokens"], (int, float)):
            model_totals[model]["output"] += int(event["output_tokens"])

    headline = []
    if spike is not None:
        headline.append(
            "- Observed: model call "
            f"#{spike['step']} dominates token usage and is the main cost center."
        )
    else:
        headline.append("- Observed: no clear token spike appears in the provided log.")

    if redundant:
        first = redundant[0]
        headline.append(
            "- Observed: "
            f"{first['tool_name']} call #{first['step']} repeats the previous call with materially the same input."
        )
    else:
        headline.append("- Observed: no obviously redundant consecutive tool call appears in the provided log.")

    if any(event["duration_ms"] == "unknown" for event in models):
        headline.append("- Unknown: some model calls lack `duration_ms`, so exact timing totals are partial.")
    elif models:
        headline.append("- Observed: timing data is present for all model calls.")
    else:
        headline.append("- Unknown: no raw model-level timing data is available in the resolved source.")
    if summaries and not tools and not models:
        headline.append("- Observed: this session-based input was resolved from summarized session memory, so tool-level telemetry is unavailable.")
    if provider_backed:
        headline.append("- Observed: the session id was resolved through an external raw session_logs provider before normalization.")

    lines = [
        "# Runtime Observability Report",
        "",
        "## Execution Summary",
        f"- Session: `{session_label}`",
        f"- Input source: {source_label}",
        f"- Confidence: {'low' if summaries and not tools and not models else 'medium' if any(event['duration_ms'] == 'unknown' for event in models) else 'high'}",
        f"- Total duration: {compute_total_duration(events)}",
        f"- Total tool calls: {len(tools)}",
        f"- Total model calls: {len(models)}",
        f"- Total summary events: {len(summaries)}",
        f"- Total tokens: {total_tokens if total_tokens else 'unknown'} observed",
        f"- Overall quality score: {total_score}/100",
        "",
        "## Headline Findings",
        *headline,
        "",
        "## Execution Timeline",
        "| Step | Time | Type | Name | Duration | Tokens | Notes |",
        "|------|------|------|------|----------|--------|-------|",
    ]

    for event in events:
        name = (
            event["tool_name"]
            if event["tool_name"] != "unknown"
            else event["model"]
            if event["model"] != "unknown"
            else "request" if event["event_type"] == "user_request" else "response" if event["event_type"] == "final_output" else "unknown"
        )
        note = event["output_summary"] if event["output_summary"] != "unknown" else event["input_summary"]
        tokens = "unknown"
        if isinstance(event["input_tokens"], (int, float)) and isinstance(event["output_tokens"], (int, float)):
            tokens = str(int(event["input_tokens"]) + int(event["output_tokens"]))
        lines.append(
            f"| {event['step']} | {short_time(event['timestamp'])} | {event['event_type']} | {name} | "
            f"{fmt_duration_ms(event['duration_ms'])} | {tokens} | {note} |"
        )

    lines.extend(
        [
            "",
            "## Token And Cost Breakdown",
            "",
            "### By tool",
            "| Tool | Calls | Tokens | Share | Notes |",
            "|------|-------|--------|-------|-------|",
        ]
    )
    for tool_name, calls in sorted(tool_counts.items()):
        note = "Consecutive duplicate detected" if any(event["tool_name"] == tool_name for event in redundant) else "Observed in trace"
        lines.append(f"| {tool_name} | {calls} | unknown | unknown | {note} |")
    if not tool_counts:
        lines.append("| none | 0 | unknown | unknown | No tool-level events available in the resolved source |")

    lines.extend(
        [
            "",
            "### By model",
            "| Model | Calls | Input tokens | Output tokens | Notes |",
            "|-------|-------|--------------|---------------|-------|",
        ]
    )
    for model_name, totals in sorted(model_totals.items()):
        note = "Dominant cost center" if spike is not None and model_name == spike["model"] else "Observed in trace"
        lines.append(
            f"| {model_name} | {totals['calls']} | {totals['input']} | {totals['output']} | {note} |"
        )
    if not model_totals:
        lines.append("| none | 0 | unknown | unknown | No model-level events available in the resolved source |")

    lines.extend(["", "### Anomalies"])
    if spike is not None:
        lines.append(
            f"- Observed: model call #{spike['step']} consumes {spike['input_tokens']} input tokens, far above the session median."
        )
        lines.append(
            "- Inferred: the spike likely comes from replaying too much raw context instead of a compact summary."
        )
    if redundant:
        for event in redundant:
            lines.append(
                f"- Observed: {event['tool_name']} call #{event['step']} duplicates the immediately preceding lookup."
            )
    if spike is None and not redundant:
        lines.append("- None: no major anomaly was detected with the current heuristic.")
    if summaries and not tools and not models:
        lines.append("- Unknown: the resolved session source is summary-level memory, so token spikes and redundancy can only be inferred at a coarse level.")

    lines.extend(
        [
            "",
            "## Decision Points",
            "- Observed: the available source preserves chronological session milestones in timestamp order.",
            "- Inferred: if only summary-level memory is available, conclusions should focus on progression and outcomes rather than raw tool-level causality."
            if summaries_only
            else "- Inferred: the clearest decision points are where the run switches from model reasoning to tool usage, retries, or final output assembly.",
            "",
            "## Quality Review",
            "",
            "### Output compliance",
            f"- Score: {output_compliance}/35",
            "- Notes: The report structure can still be produced even with missing fields, but missing timing data or summary-only sources reduce completeness."
            if summaries_only
            else "- Notes: The report structure is grounded in raw event ordering; completeness mainly depends on whether duration and token fields are present.",
            "",
            "### Factual grounding",
            f"- Score: {factual_grounding}/40",
            "- Notes: Claims are based on visible log fields; heuristic explanations remain labeled as inferred, especially when only summary memory is available."
            if summaries_only
            else "- Notes: Claims are based on visible raw log fields and any heuristic explanation remains labeled as inferred.",
            "",
            "### Scope discipline",
            f"- Score: {scope_discipline}/25",
            "- Notes: Redundant or generic lookups lower discipline because they drift away from direct post-run diagnosis; summary-only sources also limit how confidently scope can be judged."
            if summaries_only
            else "- Notes: Redundant or generic lookups lower discipline because they drift away from direct post-run diagnosis.",
            "",
            "## Issues",
        ]
    )

    issue_lines = build_issue_lines(events, spike, redundant)
    lines.extend(issue_lines or ["- Severity: low; Issue: no major issue detected; Evidence: the current heuristics found no spike or redundancy; Fix: none."])

    lines.extend(
        [
            "",
            "## Recommended Actions",
            "1. Normalize the raw log before deeper analysis so missing fields become explicit.",
            "2. Summarize large traces before replaying them to the model.",
            "3. Stop repeated tool calls unless a new branch or validation need is visible.",
            "",
            "## Data Gaps",
        ]
    )

    gap_lines = []
    if any(event["duration_ms"] == "unknown" for event in events):
        gap_lines.append("- Unknown: at least one event lacks `duration_ms`.")
    if any(event["model"] == "unknown" for event in models):
        gap_lines.append("- Unknown: at least one model event lacks `model`.")
    if any(event["tool_name"] == "unknown" for event in tools):
        gap_lines.append("- Unknown: at least one tool event lacks `tool_name`.")
    gap_lines.append("- Unknown: per-tool token attribution is not available unless the source log records it explicitly.")
    if summaries and not tools and not models:
        gap_lines.append("- Unknown: the resolved session id currently maps to session memory summaries rather than raw tool/model event logs.")
    if provider_backed:
        gap_lines.append("- Observed: raw session logs came from an external provider command, so upstream payload fidelity depends on that provider.")
    lines.extend(gap_lines)

    lines.extend(
        [
            "",
            "## Appendix",
            f"- Source logs: `{source_path}`",
            "- Estimation notes: the report uses direct counts when present and heuristic anomaly detection for redundancy and token spikes.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a runtime observability markdown report")
    parser.add_argument("--input", help="Path to the raw or normalized session log JSON/JSONL")
    parser.add_argument("--session-id", help="Session id to resolve from local session artifacts")
    parser.add_argument("--output", required=True, help="Path to the markdown report output")
    parser.add_argument(
        "--source-label",
        default="json_file",
        help="Input source label to write into the report summary",
    )
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
    inferred_source_label = args.source_label
    if args.session_id and args.source_label == "json_file":
        inferred_source_label = "session_logs"
    if args.input:
        input_path = Path(args.input)
        events = load_events_from_path(input_path, session_id=args.session_id)
        source_path = str(input_path)
    else:
        events, source_path = resolve_session_events(
            session_id=args.session_id,
            memory_root=memory_root,
            provider_command=args.provider_command,
            provider_timeout_sec=args.provider_timeout_sec,
        )
    markdown = build_markdown(events, inferred_source_label, source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
