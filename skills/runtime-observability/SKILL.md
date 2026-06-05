---
name: runtime-observability
description: Analyze agent or skill execution logs and turn black-box runs into trace, token, cost, and quality reports. Invoke whenever the user asks what happened during a run, wants session-log analysis, token breakdown, redundant tool-call diagnosis, execution scoring, or a post-run observability report.
---

# Runtime Observability

Use this skill to explain what happened inside an agent or skill run after execution finishes.

This skill does not collect telemetry itself. Treat it as a post-run analysis layer over existing logs, especially session logs exposed by a `session_logs`-style skill or any equivalent exported event stream.

## What This Skill Solves

Users often only see the final answer. They cannot tell:

- which tools were called and in what order
- where time was spent
- whether token usage was reasonable
- which decisions changed the execution path
- whether the output quality was acceptable

This skill opens that black box by converting raw execution logs into a structured diagnosis.

## When To Use

Use this skill aggressively when the user asks any variant of:

- "What happened during this run?"
- "Analyze this session log"
- "Why did this skill cost so many tokens?"
- "Generate an execution report / trace / timeline"
- "Find redundant tool calls or loops"
- "Score the quality of this run"
- "Debug a black-box agent execution"

Also use it when a user provides a session id, a session log export, a transcript of tool calls, or asks for a postmortem of a skill run.

Do not use this skill for live tracing infrastructure, telemetry ingestion pipelines, or application APM setup. This skill analyzes an already recorded run.

## Required Inputs

You need one of the following:

1. A session identifier that can be resolved through a log-reading skill such as `session_logs`
2. A raw session log export
3. A structured event stream containing tool calls, model calls, timestamps, and outputs

If none of these exist, stop and say observability cannot be reconstructed reliably.

## Input Modes

Support both of these entry modes.

### Mode A: Session-Based Input

Use this mode when the user provides:

- a session id
- a link or handle that can be resolved by a `session_logs`-style skill
- a request such as "analyze this run" where the logs are retrievable from the environment

Workflow:

1. Resolve the session through the available log-reading skill or tool
2. Extract the raw event stream
3. Normalize the events before diagnosing anything

For a local session id, use:

```bash
python3 skills/runtime-observability/scripts/normalize_session_log.py \
  --session-id "<session_id>" \
  --output "<out_dir>/normalized-session-log.json"

python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id "<session_id>" \
  --output "<out_dir>/runtime-observability-report.md" \
  --source-label session_logs
```

Current implementation detail:

- If a real `session_logs` provider is directly available, prefer that upstream source.
- In the current local environment, the bundled scripts resolve `session_id` through accessible `session_memory_<id>.jsonl` artifacts under `~/.trae-cn/memory/projects/`.
- Treat that path as a degraded but real session-based source: it preserves session chronology at the summary layer, but not raw tool/model telemetry.
- For the raw provider contract, read `references/provider-contract.md`.

To force an external raw provider, use:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id "<session_id>" \
  --provider-command 'provider-cli fetch-session --session-id {session_id}' \
  --output "<out_dir>/runtime-observability-report.md" \
  --source-label session_logs
```

or:

```bash
export RUNTIME_OBSERVABILITY_SESSION_PROVIDER_CMD='provider-cli fetch-session --session-id {session_id}'
```

### Mode B: File-Based Input

Use this mode when the user provides:

- a JSON log file
- a pasted event transcript
- a structured export from another agent platform

Workflow:

1. Read the provided file or payload
2. Map source fields into the normalized timeline schema
3. Preserve unknown fields rather than dropping them

For a local JSON file, use the bundled scripts:

```bash
python3 skills/runtime-observability/scripts/normalize_session_log.py \
  --input "<raw_log.json>" \
  --output "<out_dir>/normalized-session-log.json"

python3 skills/runtime-observability/scripts/generate_report.py \
  --input "<raw_log.json>" \
  --output "<out_dir>/runtime-observability-report.md" \
  --source-label json_file
```

## What Good Input Looks Like

The best input contains at least:

- event ordering information such as `timestamp` or step index
- event type such as `model_call`, `tool_call`, `tool_result`, or `final_output`
- names for tools or models when available
- a status field such as `success`, `error`, or `unknown`

Helpful but optional fields:

- `duration_ms`
- `input_tokens`
- `output_tokens`
- prompt or payload summaries
- retry markers
- branch ids
- final output content

If the source uses different names, map them into the normalized schema instead of forcing the original naming.

## Operating Principles

- Prefer evidence over inference. Quote log fields or snippets for every important claim.
- Never invent missing telemetry. If a field is unavailable, label it as `unknown`.
- Distinguish exact values from estimates. Use `estimated` whenever attribution is reconstructed heuristically.
- Separate data collection from analysis. First normalize the run, then diagnose it.
- Keep the final report readable by humans first, exhaustive second.

## Missing Data Behavior

When important fields are missing, degrade gracefully:

- missing `duration_ms`: still produce ordering and issue analysis, but mark timing totals as `unknown`
- missing per-call token fields: still produce session-level token analysis if available; otherwise report token analysis as `unknown`
- missing `model`: keep the event and label the model as `unknown`
- missing tool input or output bodies: summarize only what is directly visible and lower confidence if the gap affects conclusions
- missing final output artifact: skip output compliance scoring details that depend on the artifact and explain the gap explicitly

Do not block the whole analysis just because one dimension is missing. Only refuse when the log is too incomplete to reconstruct even a basic execution trace.

## Workflow

Follow this sequence.

### 1. Acquire And Normalize The Run

Obtain the session log through the appropriate log-reading skill or from user-provided files.

If the user gave you a local JSON log file, prefer running:

```bash
python3 skills/runtime-observability/scripts/normalize_session_log.py \
  --input "<raw_log.json>" \
  --output "<out_dir>/normalized-session-log.json"
```

Normalize events into a timeline with these fields whenever available:

- `timestamp`
- `event_type`
- `actor`
- `tool_name`
- `model`
- `input_tokens`
- `output_tokens`
- `duration_ms`
- `status`
- `input_summary`
- `output_summary`

If the source data lacks a field, keep the field and set it to `unknown` rather than dropping it.

### 2. Build The Execution Trace

Reconstruct:

- tool invocation order
- model invocation order
- major branches or retries
- waiting gaps and expensive spans
- decision points where the agent chose one path over another

Important: a "decision point" requires evidence. Use it only when the logs show an explicit comparison, branch, retry, fallback, refusal, or tool-selection rationale. Do not pretend to know private reasoning that is not present in the logs.

### 3. Analyze Time And Token Cost

Produce totals and breakdowns by:

- full session
- skill
- tool
- model
- time segment or execution stage

If per-tool token data is unavailable, estimate only when you have enough evidence, and label the result as `estimated from neighboring model calls` or similar.

Check for anomalies:

- sudden token spikes
- repeated large prompts with near-identical intent
- retry storms
- tool loops without new information
- long idle spans between dependent steps

Read `references/scoring-rubric.md` for the anomaly heuristics before concluding that a run is abnormal.

### 4. Score Result Quality

Evaluate the final run on three axes:

- output compliance: did the run produce the format the user or skill expected
- factual grounding: did the answer cite or imply things not supported by logs or accessible sources
- scope discipline: did the run stay inside the skill's intended capability boundary

Use the weighted rubric in `references/scoring-rubric.md`.

Important: hallucination claims need evidence. Mark them as:

- `confirmed` when the log or accessible source disproves the claim
- `suspected` when support is missing but not fully disproven

### 5. Identify Waste And Improvement Opportunities

Call out:

- redundant tool calls
- avoidable retries
- oversized prompts
- missing caching or summarization opportunities
- weak branching logic
- poor output validation

Each issue should include:

- severity
- evidence
- why it matters
- the smallest plausible fix

### 6. Produce The Report

Read `references/report-template.md` and follow its structure.

If you are working from a local JSON file, you can generate a first-pass markdown report with:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --input "<raw_log.json>" \
  --output "<out_dir>/runtime-observability-report.md" \
  --source-label json_file
```

Then refine the report in conversation if the user wants more nuance, stricter scoring, or a Mermaid diagram.

The report must contain:

- a one-screen summary
- an execution timeline
- token and cost breakdown
- quality score
- issue list with severity
- concrete next actions

If the user asks for a diagram, additionally emit a Mermaid sequence diagram or timeline based on the normalized trace.

## User-Facing Trigger Examples

These are good examples of requests that should trigger this skill:

- `Use runtime-observability to analyze this session log file and show the execution timeline.`
- `Analyze this session id and tell me why the run was expensive.`
- `Help me review this agent trace for redundant tool calls and token spikes.`
- `用 runtime-observability 分析这个 session log，输出时间线、token 拆解和问题清单。`
- `帮我复盘这次 skill 执行过程，看看哪里浪费了 token。`
- `分析这个 session id 的执行链路，判断输出质量有没有越界或幻觉。`

These requests should usually not trigger this skill:

- `Design an OpenTelemetry tracing architecture for my service.`
- `Help me add runtime metrics and APM instrumentation.`
- `给我的服务接入埋点和监控平台。`

## Reporting Rules

Always include the confidence of your analysis:

- `high`: mostly direct log evidence
- `medium`: some derived attribution, but the path is still clear
- `low`: major fields missing; conclusions are directional only

Always separate:

- `observed`: direct from logs
- `inferred`: reconstructed from multiple signals
- `unknown`: data not available

## Output Checklist

Before sending the report, verify:

- every issue points to evidence
- every score has a rubric-backed reason
- missing telemetry is disclosed
- estimated token attribution is labeled
- the summary can be understood without reading the full trace

## Example Triggers

**Example 1**
Input: Analyze why yesterday's skill run was expensive and whether it got stuck in a loop.

Output: A post-run report with timeline, token anomaly analysis, redundant-call findings, and fix suggestions.

**Example 2**
Input: I have a session log. Tell me what tools it used, how long each step took, and whether the output quality was acceptable.

Output: A structured execution report with tool chronology, timing table, quality score, and issue annotations.

**Example 3**
Input: Use runtime-observability on this JSON log export and tell me which steps are `unknown` versus `estimated`.

Output: A report that preserves incomplete fields, explicitly labels unknown or estimated attribution, and still provides a usable diagnosis.

## Recommended Verification

After editing this skill, run:

```bash
python3 skills/skill-creator/scripts/quick_validate.py skills/runtime-observability
```

Then read `references/verification.md` and validate the sample input/output pair before treating the skill as ready to use.

For an end-to-end local check, run:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-log.json \
  --output /tmp/runtime-observability-sample-report.md \
  --source-label json_file
```

For a real local session-based check, run:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id "<real_session_id>" \
  --output /tmp/runtime-observability-session-report.md \
  --source-label session_logs
```

For a raw-provider contract check, run:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id provider_demo \
  --provider-command 'python3 skills/runtime-observability/examples/mock_session_logs_provider.py --session-id {session_id}' \
  --output /tmp/runtime-observability-provider-report.md \
  --source-label session_logs
```

For trigger regression checks, run:

```bash
python3 skills/runtime-observability/scripts/run_evals.py \
  --evals skills/runtime-observability/evals/evals.json \
  --output-json /tmp/runtime-observability-evals.json \
  --output-md /tmp/runtime-observability-evals.md
```
