# FireXCore discovery and launch copy

These are **suggested public metadata values** and shareable copy, not claims that repository settings or social accounts have already been updated.

## GitHub About metadata

- **Description:** `Claude Code hooks for long-running AI agents: tested Windows fail-closed setup, session-aware evidence gating, SQLite audit and cross-platform CI. Independent Anthropic fork.`
- **Homepage:** leave blank until there is a working public demo; the repository itself is the landing page.
- **Topics:** `claude-code`, `claude-code-hooks`, `ai-agents`, `agent-harness`, `long-running-agents`, `developer-tools`, `python`, `powershell`, `sqlite`, `testing`

These values must be set in GitHub repository **About → Edit repository metadata** (the connected repository editing tools cannot change Topics or About fields). Relevant names should match the actual code; avoid unrelated trending topics. GitHub allows up to 20 topics.

## Short announcement for developer communities

**Title:** I hardened a Claude Code long-running-agent hook demo after reproducing a Windows fail-open case

I forked Anthropic's educational `cwc-long-running-agents` example to investigate a concrete failure: without Git Bash, some Windows Claude Code setups could run `.sh` hook commands through PowerShell, exit successfully without valid hook decisions, and allow a tool call despite `AGENT_STOP`.

The FireXCore fork adds explicit Bash selection, fail-closed configuration on supported Claude Code versions, a Windows preflight launcher, a session-scoped SQLite evidence gate, and regression tests on Windows/Linux across two Python versions.

There is also a self-contained local demo: `python examples/demo_evidence_gate.py`.

**Important limitation:** this is not an agent sandbox or independently trustworthy PASS/FAIL mechanism. The agent can forge local evidence and bypass Write/Edit hooks using shell access. I documented the bypasses instead of claiming otherwise.

Repo: https://github.com/FireXCore/cwc-long-running-agents

This is an independent fork. Anthropic's original educational demo and the other contributor's schema fix retain their own attribution.

## One-paragraph technical introduction

FireXCore/cwc-long-running-agents is an experimental fork with reproducible tests for Claude Code hook lifecycle, Windows Git Bash execution, session-scoped evidence accounting and operator intervention. It preserves the original Apache-2.0 upstream credits. The project deliberately treats hooks as advisory tooling and points to external evaluation for trusted verification.

## Suggested publishing sequence

1. Set truthful GitHub Topics and About description.
2. Link the actual README and local demo, not screenshots that imply unsupported production behavior.
3. Publish the short technical summary in communities where Claude Code hooks are relevant, following each community's promotion rules.
4. Share new concrete findings, reproducible tests or releases; do not repeatedly repost the same link.
5. Review GitHub **Insights → Traffic** and Stars/Issues over a 14-day window, rather than manufacturing popularity metrics.
