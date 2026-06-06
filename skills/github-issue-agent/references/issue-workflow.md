# Issue Workflow

Use this reference for full GitHub issue triage, implementation, or PR workflows.

## Discovery

Collect enough context before acting:

- repository owner and name
- default branch
- issue number or issue filter
- issue title and body
- labels, milestone, assignees, and state
- relevant comments
- linked PRs or commits
- current working tree status

If the repository is a fork, distinguish:

- `origin`: usually the user's fork or working remote
- `upstream`: usually the canonical project

Do not assume that `origin` is the upstream project.

## Triage Decision Tree

Classify the issue as one of:

- Question
- Bug
- Feature
- Duplicate
- Already fixed
- Needs info

Choose the narrowest classification that fits the evidence.

## Question Handling

For a question:

1. Find the relevant docs, code, or tests.
2. Draft a direct answer.
3. Include caveats when behavior depends on version, config, or environment.
4. Run the verification gate.
5. Ask the user before posting.

## Bug Handling

For a bug:

1. Sync or inspect the latest default branch.
2. Try to reproduce the issue with the smallest command or test.
3. If reproduced, write or update a focused failing test when valuable.
4. Make the smallest fix.
5. Run the smallest useful verification command.
6. Summarize behavior before and after the fix.
7. Ask before committing or opening a PR.

If the issue cannot be reproduced, report:

- attempted reproduction steps
- observed behavior
- missing information
- proposed clarifying question

## Feature Handling

For a feature:

1. Restate the requested capability and acceptance criteria.
2. Identify the smallest compatible implementation path.
3. Check existing architecture and conventions.
4. Implement only after the user confirms the scope if the request is broad.
5. Add tests or examples that protect the new behavior.
6. Ask before committing or opening a PR.

## Duplicate Handling

For a duplicate:

1. Find the existing issue.
2. Compare symptoms, environment, and requested behavior.
3. Draft a reply that links the duplicate and explains the overlap.
4. Ask the user before posting or closing.

## Already-Fixed Handling

For an already-fixed issue:

1. Identify the exact evidence:
   - commit
   - PR
   - release note
   - test
   - code path
2. Avoid saying "fixed in version X" unless that version is confirmed.
3. Draft a concise reply with evidence.
4. Run the verification gate.
5. Ask before posting.

## PR Preparation

When the user approves PR creation, include:

- problem summary
- linked issue
- implementation summary
- tests run
- risks and follow-ups

Never open a PR for pure triage unless the user asks for it.
