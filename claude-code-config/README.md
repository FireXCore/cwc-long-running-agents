# Long-running Claude Code hook examples — FireXCore fork

Derived from Anthropic's Apache-2.0 educational demo.
**These hooks are advisory, not a security boundary.**

Requires Git Bash and real Python 3.9+ with sqlite3. On Windows the Store
'python3' stub is insufficient. Use the repository's
scripts/launch-claude-verified.ps1 after copying .claude into a disposable
project root. The launcher checks prerequisites and sets environment values
before calling Claude Code. Every hook pins `"shell": "bash"`, so raw
`claude` without Git Bash blocks every tool call instead of silently
skipping the hooks. Do not remove that field.

Hooks:
- kill-switch.sh: block tools while AGENT_STOP exists (when hooks run)
- steer.sh: deliver steering once, preserving the message on runtime failure
- track-read.sh: record successful Read of in-project evidence
- verify-gate.sh: advisory Write/Edit check for results files
- evidence_audit.py: SQLite atomic evidence accounting and 15-minute expiry
- commit-on-stop.sh: optional and disabled; not registered in settings.json

Evidence must be in screenshots/ or evidence/ and match an evidence filename.
A file Read only unlocks a single results edit; it does not prove test success.
Agent-created evidence and modified SQLite records are still forgeable.
Direct Bash/PowerShell writes bypass this gate. Use a separate trusted
evaluator to certify results. See ../FORK-HARDENING.md for full limitations.
