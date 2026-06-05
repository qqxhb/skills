# Verification Guide

Use this guide to verify that `runtime-observability` is usable for both maintainers and end users.

## 1. Structure Validation

Run:

```bash
python3 skills/skill-creator/scripts/quick_validate.py skills/runtime-observability
```

Expected result:

- The command prints `Skill is valid!`

This confirms the skill metadata and file structure are valid. It does not confirm that the skill is understandable or easy to trigger.

## 2. Script Validation

Run:

```bash
python3 skills/runtime-observability/scripts/normalize_session_log.py \
  --input skills/runtime-observability/examples/sample-session-log.json \
  --output /tmp/runtime-observability-normalized.json

python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-log.json \
  --output /tmp/runtime-observability-sample-report.md \
  --source-label json_file

python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-memory.jsonl \
  --output /tmp/runtime-observability-sample-session-memory-report.md \
  --source-label session_logs
```

Expected result:

- `/tmp/runtime-observability-normalized.json` exists and every event includes the normalized schema fields
- `/tmp/runtime-observability-sample-report.md` exists and contains summary, timeline, token breakdown, quality review, issues, and data gaps
- `/tmp/runtime-observability-sample-session-memory-report.md` exists and explicitly discloses that the source is summary-level session memory

For trigger regression, run:

```bash
python3 skills/runtime-observability/scripts/run_evals.py \
  --evals skills/runtime-observability/evals/evals.json \
  --output-json /tmp/runtime-observability-evals.json \
  --output-md /tmp/runtime-observability-evals.md
```

Expected result:

- `/tmp/runtime-observability-evals.json` exists and summarizes pass/fail per eval
- `/tmp/runtime-observability-evals.md` exists and provides a readable trigger regression report
- All current evals pass

For session-based resolution in the current local environment, run:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id "<real_session_id>" \
  --output /tmp/runtime-observability-session-report.md \
  --source-label session_logs
```

Expected result:

- The command resolves a local `session_memory_<id>.jsonl` artifact when available
- `/tmp/runtime-observability-session-report.md` exists
- The report explicitly discloses when the resolved source is summary-level session memory rather than raw tool/model events

For raw provider resolution, run:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id provider_demo \
  --provider-command 'python3 skills/runtime-observability/examples/mock_session_logs_provider.py --session-id {session_id}' \
  --output /tmp/runtime-observability-provider-report.md \
  --source-label session_logs
```

Expected result:

- `/tmp/runtime-observability-provider-report.md` exists
- The report shows real tool/model events from the provider-backed sample log
- The appendix points to a `provider:` source descriptor rather than a local `session_memory` path

## 3. Content Validation

Read these two files together:

- `skills/runtime-observability/examples/sample-session-log.json`
- `skills/runtime-observability/examples/sample-report.md`

Check that the sample report actually reflects the sample log:

- the large model call is identified as the main token spike
- the second browser call is identified as redundant
- missing fields remain labeled as `unknown`
- inferred statements are not presented as direct facts

Expected result:

- A reviewer can trace every major conclusion in the sample report back to a concrete event or a clearly labeled inference.

## 4. Trigger Validation

Try these requests and confirm the skill should trigger:

- `Use runtime-observability to analyze this session log file and show the execution timeline.`
- `Analyze this session id and tell me why the run was expensive.`
- `Help me review this agent trace for redundant tool calls and token spikes.`
- `用 runtime-observability 分析这个 session log，输出时间线、token 拆解和问题清单。`
- `帮我复盘这次 skill 执行过程，看看哪里浪费了 token。`

Expected result:

- The request is clearly about post-run analysis of an agent or skill execution.
- The expected output includes a structured report rather than telemetry ingestion advice.
- These trigger and non-trigger cases are also captured in `skills/runtime-observability/evals/evals.json` for regression use.

## 5. Negative Trigger Validation

Try these requests and confirm the skill should usually not trigger:

- `Design an OpenTelemetry tracing architecture for my service.`
- `Help me add runtime metrics and APM instrumentation.`
- `给我的服务接入埋点和监控平台。`

Expected result:

- The request is routed toward observability infrastructure or instrumentation work, not post-run trace analysis.

## 6. End-User Validation

### File-based input

Prompt:

```text
用 runtime-observability 分析这个 session log，输出执行时间线、token 拆解、质量评分和问题清单。
```

Expected result:

- The answer contains timeline, token or cost breakdown, quality score, issues, and recommended actions.
- If the log lacks some fields, the answer uses `unknown` or `estimated` rather than inventing precision.

### Session-based input

Prompt:

```text
用 runtime-observability 分析这个 session id，对接 session_logs 读取执行日志，然后给我一份结构化报告。
```

Expected result:

- The skill resolves the session through the available log-reading path first, then produces the same report shape.
- In the current local implementation, if raw `session_logs` data is not directly accessible, the skill may fall back to local `session_memory_<id>.jsonl` artifacts and must disclose that downgrade.

## 7. Ready-for-Use Checklist

Treat the skill as usable when all of these are true:

- `quick_validate.py` passes
- the bundled scripts run successfully on the sample log
- the trigger regression runner passes on `evals/evals.json`
- session-based resolution works for at least one real local session id or fails with an explicit, actionable error
- raw provider resolution works with the documented provider command contract
- `SKILL.md` clearly documents both input modes
- sample input and sample output exist and agree with each other
- `evals/evals.json` captures both positive and negative trigger cases
- trigger examples and negative trigger examples are both documented
- missing-field behavior is explicit and consistent across the skill and the report
