# Verified Reply Example

## User Request

```text
Please draft a reply to issue #123. The user asks whether this behavior is expected.
```

## Draft Reply

```markdown
Thanks for the question. This behavior is expected when `strict` mode is enabled.

Evidence:
- `src/config.ts` reads the `strict` option before applying fallback behavior.
- `docs/configuration.md` documents that fallback behavior is disabled in strict mode.

If you are seeing this without `strict` mode enabled, please share your config and a minimal reproduction.
```

## Verification Result

```text
Verdict: PASS
Evidence:
- Confirmed `strict` mode gate in `src/config.ts`.
- Confirmed documentation in `docs/configuration.md`.
Risks:
- Did not run a reproduction because the issue only asked for expected behavior.
Corrections:
- None.
```

## Required User Confirmation

```text
I verified the draft against repository docs and code. Do you want me to post this exact reply?
```
