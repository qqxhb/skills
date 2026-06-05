# Runtime Observability Skill

This repository publishes the `runtime-observability` skill as a standalone open-source package.

`runtime-observability` is a post-run observability skill for AI agents. It turns black-box runs into structured reports with:

- execution timeline
- tool and model usage
- token and cost breakdown
- redundant call detection
- quality scoring
- explicit data-gap disclosure

## Repository Layout

```text
.
├── LICENSE
├── README.md
└── skills/
    └── runtime-observability/
        ├── README.md
        ├── SKILL.md
        ├── evals/
        ├── examples/
        ├── references/
        └── scripts/
```

## Quick Start

Generate a report from the bundled sample log:

```bash
python3 skills/runtime-observability/scripts/generate_report.py   --input skills/runtime-observability/examples/sample-session-log.json   --output /tmp/runtime-observability-sample-report.md   --source-label json_file
```

Run the raw provider demo:

```bash
python3 skills/runtime-observability/scripts/generate_report.py   --session-id provider_demo   --provider-command 'python3 skills/runtime-observability/examples/mock_session_logs_provider.py --session-id {session_id}'   --output /tmp/runtime-observability-provider-report.md   --source-label session_logs
```

Validate the repository by running the sample report commands above and checking that the generated Markdown files exist and contain execution summary, timeline, and cost sections.

## More Information

See:

- `skills/runtime-observability/README.md` for user-facing usage and verification
- `skills/runtime-observability/SKILL.md` for agent/runtime instructions
- `skills/runtime-observability/references/provider-contract.md` for external raw provider integration
