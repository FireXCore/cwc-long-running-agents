# Contributing to the FireXCore fork

This is an **independent experimental fork** of Anthropic's educational long-running agents demo. It is **not** operated by Anthropic. Read the [upstream original](UPSTREAM-README.md) and the [threat model](FORK-HARDENING.md) before contributing.

## Useful contributions

- Reproducible Claude Code hook-lifecycle bugs on Windows, macOS, and Linux.
- Verified compatibility fixes across supported Claude Code versions.
- Test cases for path aliases, concurrent evidence reads, failure handling and correct hook schemas.
- Documentation improvements that help users run the demo without overstating security guarantees.

## Report a bug

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml). Include the OS, Claude Code version, Git Bash/Python versions, a minimal disposable fixture, expected and observed behavior, and redacted logs. **Never submit API keys, private customer data, credentials or RMS tenant information.** In particular, do not treat evidence written by the builder as independently verified.

## Changes and review

1. Create a feature branch based on `main`; keep the change tightly scoped.
2. Preserve upstream copyright and Apache-2.0 notices.
3. Run `python -m unittest discover -s tests -v` and `bash -n claude-code-config/.claude/hooks/*.sh`.
4. Include a failing regression test for bug fixes and identify any behavior that is only hook-level versus **live Claude Code**.
5. Open a PR, link to a reproducer and CI evidence. Never claim a local hook is a security boundary.

No contribution implies a guaranteed response time, merge or upstream Anthropic acceptance.
