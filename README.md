# Skills

This repository publishes standalone AI agent skills.

## Published Skills

- [runtime-observability](./skills/runtime-observability): post-run observability for AI agent sessions, including timeline, token, cost, redundancy, and quality reports.
- [github-issue-agent](./skills/github-issue-agent): safe GitHub issue triage and handling workflow, including verified replies, bug/feature issue implementation, and PR preparation with user-confirmation gates.
- [skill-health-audit](./skills/skill-health-audit): analyze skill usage/effectiveness/redundancy, produce a health report, and generate a reversible cleanup script with confirmation gates.

## Repository Layout

```text
.
├── LICENSE
├── README.md
└── skills/
    ├── github-issue-agent/
    ├── runtime-observability/
    └── skill-health-audit/
```

## Verification

Each skill includes its own README with usage and verification notes:

- `skills/runtime-observability/README.md`
- `skills/github-issue-agent/README.md`
- `skills/skill-health-audit/README.md`

## License

Apache-2.0. See `LICENSE`.
