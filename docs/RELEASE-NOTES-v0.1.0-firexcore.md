# Draft release notes — v0.1.0-firexcore (NOT PUBLISHED)

**Status: DRAFT.** This is material for a possible first GitHub *pre-release*. No tag or GitHub Release is created by this file.

## What is included

- Corrected `PreToolUse` JSON response schema.
- `PostToolUse(Read)` evidence accounting, SHA-256, TTL and session separation.
- SQLite transactional single-use evidence tracking.
- Windows PowerShell launcher with Git Bash and real Python verification.
- Operator steering and kill switch examples.
- Windows and Ubuntu hook CI across Python 3.9 and 3.12.
- Quick simulation demo, setup docs, and the original upstream documentation.

## Why it matters

In Windows live acceptance reported by PR #1, shell-hook startup could silently fail open without Git Bash. Hook configuration now pins Bash and `onFailure: block` on supported Claude Code. The results gate is **advisory** and can still be bypassed by agent-written artifacts, direct shell writes and a forged local SQLite database.

## Before publication

- Verify the exact tagged SHA and all CI results.
- Repeat live Claude Code acceptance for the release candidate on a disposable Windows project.
- Confirm documentation links and requirements.
- Publish with a **pre-release** label, not as production security tooling.

### Provenance

Independent FireXCore fork. Based on Anthropic's educational demo under Apache-2.0. See [PR #1](https://github.com/FireXCore/cwc-long-running-agents/pull/1) and [PR #2](https://github.com/FireXCore/cwc-long-running-agents/pull/2).
