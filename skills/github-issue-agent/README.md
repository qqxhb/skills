# GitHub Issue Agent

`github-issue-agent` is a workflow skill for handling GitHub issues safely and repeatably.

It helps an agent:

- inspect GitHub issue context
- classify issues into question, bug, feature, duplicate, already-fixed, or needs-info
- verify claims against repository evidence
- draft issue replies
- implement fixes or features when explicitly requested
- prepare PRs only after user confirmation

## Safety Model

The skill is intentionally conservative:

- no issue comment is posted without user-confirmed text
- no commit or PR is created unless the user requests or approves it
- every factual reply must pass a verification gate
- repository evidence is preferred over assumptions
- authentication secrets are never requested or printed in chat

## Repository Layout

```text
github-issue-agent/
├── README.md
├── SKILL.md
├── evals/
│   └── evals.json
├── examples/
│   └── verified-reply-example.md
└── references/
    ├── issue-workflow.md
    ├── reply-template.md
    └── verification.md
```

## When It Should Trigger

Use this skill when the user asks to:

- view or analyze GitHub issues
- triage open issues
- answer a GitHub issue
- verify whether an issue is already fixed
- implement a bug fix or feature from an issue
- create a PR for issue work
- draft or post an issue comment

Do not use it for generic code review unless the review is tied to a GitHub issue or PR that claims to resolve one.

## Typical Prompts

```text
Analyze issue #123 and tell me if it is still valid.
```

```text
Draft a reply for this GitHub issue, but do not post it yet.
```

```text
Fix GitHub issue #42 and open a PR after I approve the change.
```

```text
Check whether this PR really fixes the linked issue.
```

## Verification

From a full skills workspace that includes `skill-creator`, validate the skill structure:

```bash
python3 skills/skill-creator/scripts/quick_validate.py skills/github-issue-agent
```

Expected result:

```text
Skill is valid!
```

Manual acceptance checklist:

- `SKILL.md` has valid YAML frontmatter with `name` and `description`.
- The description includes both capability and trigger conditions.
- The workflow requires user confirmation before posting comments.
- The workflow requires user confirmation before commits or PRs.
- The reply verification gate is explicit.
- Reference files are discoverable from `SKILL.md`.

## Publishing

This skill is safe to publish as a standalone directory under:

```text
skills/github-issue-agent/
```

For a multi-skill repository, list it in the root README next to other published skills.

## Known Limits

- The skill does not include a GitHub API client by itself.
- It depends on the runtime's available GitHub, shell, or MCP tools.
- It cannot post comments or create PRs without authenticated tool access.
- Verification quality depends on repository test coverage and available reproduction steps.
