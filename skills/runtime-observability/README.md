# Runtime Observability

`runtime-observability` is a post-run analysis skill for AI agents.

It turns a black-box run into a structured report:

- execution timeline
- tool and model usage
- token and cost breakdown
- redundant call detection
- quality scoring
- data-gap disclosure

This skill directory contains two layers:

- `SKILL.md`: instructions for the agent runtime
- `README.md`: instructions for human readers and GitHub users

## What It Solves

After an agent run, users often only see the final answer. They cannot easily tell:

- which tools were called
- what happened in the middle
- where time and tokens were spent
- whether the run looped or wasted work
- whether the output stayed in scope

This skill reconstructs the run from available logs and produces a readable diagnosis.

## Current Input Modes

The skill currently supports three practical input paths:

1. Raw JSON session log file
2. Session-based fallback through local `session_memory_<id>.jsonl`
3. External raw `session_logs` provider command

Priority order for `--session-id`:

1. external provider via `--provider-command` or `RUNTIME_OBSERVABILITY_SESSION_PROVIDER_CMD`
2. local fallback under `~/.trae-cn/memory/projects/**/session_memory_<id>.jsonl`

## Quick Start

### Analyze a JSON log file

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-log.json \
  --output /tmp/runtime-observability-sample-report.md \
  --source-label json_file
```

### Analyze a local session id

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id 6a2225e91139d4bef41095fb \
  --output /tmp/runtime-observability-session-report.md \
  --source-label session_logs
```

### Analyze through an external raw provider

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id provider_demo \
  --provider-command 'python3 skills/runtime-observability/examples/mock_session_logs_provider.py --session-id {session_id}' \
  --output /tmp/runtime-observability-provider-report.md \
  --source-label session_logs
```

## How To Verify

Treat validation as passed when all of the following succeed.

### 1. Skill structure

```bash
python3 skills/skill-creator/scripts/quick_validate.py skills/runtime-observability
```

Expected result:

- output contains `Skill is valid!`

### 2. File-based path

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-log.json \
  --output /tmp/runtime-observability-sample-report.md \
  --source-label json_file
```

Expected result:

- `/tmp/runtime-observability-sample-report.md` exists
- report contains `Execution Summary`
- report contains `Execution Timeline`
- report contains `Token And Cost Breakdown`

### 3. Session-memory fallback path

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --input skills/runtime-observability/examples/sample-session-memory.jsonl \
  --output /tmp/runtime-observability-sample-session-memory-report.md \
  --source-label session_logs
```

Expected result:

- report exists
- report shows `Confidence: low`
- report explicitly says the source is summary-level session memory

### 4. Raw provider path

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id provider_demo \
  --provider-command 'python3 skills/runtime-observability/examples/mock_session_logs_provider.py --session-id {session_id}' \
  --output /tmp/runtime-observability-provider-report.md \
  --source-label session_logs
```

Expected result:

- report exists
- report shows tool and model events
- appendix contains a `provider:` source descriptor

### 5. Trigger regression

```bash
python3 skills/runtime-observability/scripts/run_evals.py \
  --evals skills/runtime-observability/evals/evals.json \
  --output-json /tmp/runtime-observability-evals.json \
  --output-md /tmp/runtime-observability-evals.md
```

Expected result:

- JSON and Markdown reports both exist
- current eval set passes

## Repository Layout

```text
runtime-observability/
├── README.md
├── SKILL.md
├── evals/
├── examples/
├── references/
└── scripts/
```

Key files:

- `scripts/normalize_session_log.py`: normalizes raw payloads into one schema
- `scripts/generate_report.py`: generates the markdown report
- `scripts/session_logs_provider.py`: provider interface for raw session log resolution
- `references/provider-contract.md`: contract for external providers
- `references/verification.md`: detailed verification checklist

## External Provider Contract

If you want to connect a real upstream `session_logs` source, read:

- `references/provider-contract.md`

The provider must print one of these to stdout:

- JSON array of events
- JSON object with an `events` array
- JSONL stream of event objects

## Package

Build the distributable skill package with:

```bash
PYTHONPATH=. python3 skills/skill-creator/scripts/package_skill.py skills/runtime-observability .
```

The packaged artifact is:

- `runtime-observability.skill`

## Known Limits

- If only `session_memory_<id>.jsonl` is available, the report is summary-level rather than raw trace-level.
- Per-tool token attribution depends on upstream payload fidelity.
- The current trigger eval runner is heuristic and is not a live LLM trigger test.

## License And Publishing

Before publishing to GitHub, confirm:

- the example session ids and sample logs are safe to disclose
- no local-only paths or private provider commands are committed unintentionally
- any real provider integration hides credentials and private endpoints
