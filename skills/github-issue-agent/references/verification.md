# Verification

Use this reference before approving a GitHub issue reply, resolution claim, or PR summary.

## Reply Verification Gate

A reply is ready to show to the user only when every material claim has evidence.

Check:

- Does the reply describe actual repository behavior?
- Does the reply cite code, docs, tests, commands, or issue history?
- Does it avoid unsupported release, timeline, or support commitments?
- Does it avoid claiming a bug is fixed without proof?
- Does it avoid claiming a workaround is safe without evidence?

## Evidence Types

Prefer stronger evidence:

- executed reproduction command or test
- code path with file and line references
- existing test that covers the behavior
- official repository documentation
- linked commit or PR
- issue maintainer comment

Weak evidence:

- assumptions from similar code
- memory of behavior
- generic framework knowledge
- unverified user claims

Weak evidence can inform a hypothesis, but should not be presented as confirmed fact.

## Verification Output

Use this format:

```text
Verdict: PASS|FAIL
Evidence:
- ...
Risks:
- ...
Corrections:
- ...
```

## PASS Criteria

Return `PASS` only when:

- all factual claims are supported
- uncertainty is explicitly labeled
- commands or tests are named when behavior was verified
- reply does not promise unapproved action
- user confirmation is still required before posting

## FAIL Criteria

Return `FAIL` when:

- any factual claim is unsupported
- issue state is assumed instead of checked
- the reply overstates confidence
- the reply implies a comment has been posted when it has not
- the reply proposes closing or labeling an issue without user approval

## Minimum Verification Commands

Use project-specific commands when available. If unknown, choose the smallest relevant command:

```bash
git status --short
git branch --show-current
git log --oneline -n 5
```

For code behavior, prefer targeted tests over full suites when possible.

## User Confirmation

Before posting, show:

- final reply text
- verification verdict
- evidence summary
- risks or caveats

Ask the user to confirm the exact text.
