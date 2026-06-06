---
name: github-issue-agent
description: Triage and handle GitHub issues for the current repository. Use when asked to view, analyze, reply to, resolve, implement, or create PRs for GitHub issues. Always confirm issue reply text before posting.
---

# GitHub Issue Agent

Use this skill to handle GitHub issues end-to-end for the current repository:

- inspect issue context and repository state
- classify question, bug, feature, duplicate, or already-fixed cases
- draft verified issue replies
- implement fixes or features when requested
- prepare commits and PRs only after explicit user confirmation

## Operating Rules

- Never post an issue comment without showing the exact reply text to the user and receiving confirmation.
- Never create commits, branches, PRs, or issue state changes unless the user explicitly requests or approves that action.
- Verify factual claims against repository evidence before presenting them as facts.
- Treat the current repository as the source of truth. Prefer code, tests, docs, and executed reproduction steps over assumptions.
- If GitHub authentication is missing, ask the user to configure it through their normal secure channel. Do not request or print secrets in chat.
- If there is an existing dirty worktree, avoid touching unrelated files and do not revert user changes.

## Core Workflow

1. Identify the target repository and issue scope.
2. Fetch issue title, body, labels, status, linked PRs, and relevant comments.
3. Sync or inspect the latest default branch before making behavioral claims.
4. Classify the issue.
5. Choose the matching workflow below.
6. Verify evidence.
7. Ask the user before posting, committing, or opening a PR.

## Repository And Issue Discovery

- Derive the GitHub repository from git remotes when the user does not provide one.
- Prefer `origin` for the user's fork or working repo, but inspect `upstream` when the repo is a fork.
- Resolve the target issue from:
  - explicit issue number or URL
  - label filter
  - assignee or milestone filter
  - "open issues" or "recent issues" request
- Load issue body and comments before deciding.
- Check whether the issue is still open and whether linked PRs or commits already resolve it.

## Classification

Use these categories:

- **Question**: asks for explanation, usage, setup, or expected behavior.
- **Bug**: reports incorrect behavior, regression, crash, failing test, or broken workflow.
- **Feature**: asks for a new capability or enhancement.
- **Duplicate**: substantially overlaps an existing issue.
- **Already fixed**: latest default branch or released version already contains the fix.
- **Needs info**: cannot proceed without missing reproduction steps, environment, logs, or expected behavior.

If classification is ambiguous, state the ambiguity and ask the user before doing engineering work.

## Question Workflow

1. Locate the relevant code, docs, or tests.
2. Draft a concise reply with citations to evidence where possible.
3. Run the reply verification gate.
4. Show the verified reply to the user.
5. Post only after user confirmation.

## Bug Or Feature Workflow

1. Confirm the issue is still valid on the latest default branch.
2. Reproduce the bug or define an acceptance case.
3. Make the smallest focused change that addresses the issue.
4. Add or update tests when they materially reduce regression risk.
5. Run the smallest useful verification command for the touched path.
6. Summarize the change, tests, and residual risks.
7. Commit or open a PR only after user confirmation.

## Already-Fixed Workflow

1. Find the commit, PR, release note, test, or code path that proves the fix.
2. Verify the reported scenario no longer reproduces if feasible.
3. Draft a reply that names the evidence and version or commit when known.
4. Run the reply verification gate.
5. Ask the user to confirm before posting.

## Reply Verification Gate

Before posting any issue reply, run an independent verification pass that tries to disprove the draft.

The verifier must check:

- every factual claim in the reply
- code references and line ranges
- reproduction or test evidence when behavior is discussed
- whether the reply over-promises a fix, timeline, release, or support commitment

If verification fails, revise the reply and verify again.

Use this output format for the verification result:

```text
Verdict: PASS|FAIL
Evidence:
- ...
Risks:
- ...
Corrections:
- ...
```

## PR And Commit Rules

- Use a branch name that includes the issue number when available, such as `fix/issue-123-short-title`.
- Keep commits atomic and scoped to the issue.
- Include issue references in commit messages or PR body when useful.
- PR body should include:
  - summary
  - linked issue
  - tests run
  - known risks or follow-ups
- Do not submit a PR if the user only asked for triage or a draft reply.

## When To Read References

- Read `references/issue-workflow.md` when doing a full triage, bug fix, feature implementation, or PR flow.
- Read `references/verification.md` before validating a draft reply or a proposed issue resolution.
- Read `references/reply-template.md` when drafting a user-facing GitHub issue comment.
