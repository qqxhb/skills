# Provider Contract

Use this reference when you want `runtime-observability` to consume a real raw `session_logs` source instead of falling back to `session_memory_<id>.jsonl`.

## Goal

Provide a command that accepts a session id and prints a raw session log payload to stdout.

## CLI Contract

The bundled scripts support either of these forms:

```bash
provider-cli fetch-session --session-id <session_id>
provider-cli fetch-session {session_id}
```

You can pass the command in one of two ways:

```bash
python3 skills/runtime-observability/scripts/generate_report.py \
  --session-id "<session_id>" \
  --provider-command 'provider-cli fetch-session --session-id {session_id}' \
  --output /tmp/runtime-observability-report.md
```

or:

```bash
export RUNTIME_OBSERVABILITY_SESSION_PROVIDER_CMD='provider-cli fetch-session --session-id {session_id}'
```

## Output Contract

The provider must print one of these shapes to stdout:

1. JSON array of event objects
2. JSON object containing an `events` array
3. JSONL where each line is one event object

Each event object should ideally include:

- `timestamp`
- `event_type`
- `tool_name` or `model`
- `duration_ms`
- `input_tokens`
- `output_tokens`
- `status`
- `input_summary`
- `output_summary`

Different field names are allowed because the normalizer already maps common aliases.

## Error Contract

- Exit non-zero on lookup failure
- Write a useful error to stderr
- Do not print human commentary to stdout before the JSON payload

## Fallback Behavior

If no provider command is configured, the scripts fall back to resolving local `session_memory_<id>.jsonl` artifacts under `~/.trae-cn/memory/projects/`.
