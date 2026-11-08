# FireXCore — Long-Running Claude Code Hooks

**An independent, experimental fork of [Anthropic's cwc-long-running-agents](https://github.com/anthropics/cwc-long-running-agents).** Maintains the educational harness examples while addressing specific lifecycle, Windows, and evidence-accounting defects. This is **not** an official Anthropic distribution, a sandbox, or a security enforcement system.

[![Hook contract tests](https://github.com/FireXCore/cwc-long-running-agents/actions/workflows/hook-contract-tests.yml/badge.svg?branch=main)](https://github.com/FireXCore/cwc-long-running-agents/actions/workflows/hook-contract-tests.yml)

## Why this fork exists

The original Anthropic demo is a useful educational starting point, but its previous hook format and Windows execution path could silently bypass intended controls. **FireXCore documents and tests those failure modes** and adds a more observable, session-aware example. It is a maintained *fork experiment*, not an Anthropic product or a production security tool.

| In the original demo | In this FireXCore fork |
| --- | --- |
| Deprecated `PreToolUse` decision JSON | Updated hook response schema and fail-closed startup configuration |
| Evidence recorded before a successful file read | Records only `PostToolUse(Read)` events |
| Simple mutable text log | SHA-256 + session ID + expiry + SQLite transaction |
| Git Bash/Windows runtime ambiguity | PowerShell preflight launcher and Windows-specific tests |
| Limited test matrix | Windows and Ubuntu CI across Python 3.9 and 3.12 |

**Try the behavior without installing Claude Code:** run `python examples/demo_evidence_gate.py`. It uses a disposable folder to demonstrate **deny → record Read → allow once → deny again**. This is a local simulation, **not** verification that a real Claude session or an application test passed.

**Start here:** [2-minute demo](docs/DEMO.md) · [Windows setup](#windows-quick-start-isolated-example) · [Known bypasses](#threat-model-and-known-bypasses) · [Contributing](CONTRIBUTING.md) · [Release notes draft](docs/RELEASE-NOTES-v0.1.0-firexcore.md)

## What is included

| Component | Behavior |
| --- | --- |
| Kill switch | A `PreToolUse` hook denies tool calls while `AGENT_STOP` exists. |
| Operator steering | `STEER.md` is delivered as a one-time operator instruction, then cleared. |
| Evidence accounting | A successful `PostToolUse(Read)` of an in-project proof file creates a session-scoped SHA-256 observation. |
| Results gate | A `PreToolUse(Write|Edit)` checks evidence before modifying `test-results.json` (configurable via `RESULTS_FILE`). |
| Atomic consumption | SQLite transactions consume a session's evidence once; records expire after 15 minutes by default. |
| Windows preflight | A PowerShell launcher checks Git Bash, real Python, Claude Code version, and selected hook settings. |
| Handoff and evaluator | Example `CLAUDE.md` and a second-opinion evaluator agent. |
| CI | Deterministic hook tests on Windows and Linux. |

All policy `PreToolUse` commands specify `"shell": "bash"` and `"onFailure": "block"` to avoid silently allowing operations after hook startup errors on supported Claude Code versions.

## Requirements

- Claude Code **2.1.295+**, for `onFailure: "block"` support. This is a minimum preflight requirement, **not** a guarantee that all behavior was live-tested on that version.
- Python **3.9+** with `sqlite3`.
- Bash; on Windows use **Git for Windows / Git Bash**.
- Git for the example repository workflow.

The live Windows acceptance reported in [PR #1](https://github.com/FireXCore/cwc-long-running-agents/pull/1) used Claude Code 2.1.312, Windows PowerShell 5.1, and Python 3.12. CI tests simulate hook events and are not live Claude Code tests.

## Windows quick start (isolated example)

Run from PowerShell in a scratch directory, not an existing business project:

```powershell
git clone https://github.com/FireXCore/cwc-long-running-agents.git
$fork = (Resolve-Path .\cwc-long-running-agents).Path
$fixture = Join-Path $env:TEMP ("cwc-example-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $fixture | Out-Null
Copy-Item -Path "$fork\claude-code-config\.claude" -Destination "$fixture\.claude" -Recurse
Set-Location $fixture
& "$fork\scripts\launch-claude-verified.ps1"
```

The launcher refuses startup if required tooling or selected settings are invalid. It does **not** certify all user, managed, or dynamically supplied settings. Use a disposable fixture. Do not assume a successful preflight is a security guarantee.

## Linux/macOS quick start

```bash
git clone https://github.com/FireXCore/cwc-long-running-agents.git
fixture="$(mktemp -d)"
cp -R cwc-long-running-agents/claude-code-config/.claude "$fixture/.claude"
cd "$fixture"
python3 --version
claude
```

Launch Claude Code from the fixture root containing `.claude/`. Adjust results filename and evidence patterns for an application only after understanding the limitations below.

## Run tests

```bash
python3 -m unittest discover -s tests -v
bash -n claude-code-config/.claude/hooks/*.sh
```

See [Windows live QA instructions](scripts/WINDOWS-LIVE-QA.md) and [security/implementation notes](FORK-HARDENING.md). CI checks run automatically for PRs and changes to `main`; CI itself does not verify a live Claude Code session.

## Threat model and known bypasses

**This harness does not provide proof authenticity or enforce tenant isolation.**

- A builder can create its own screenshot or log, read it, and unlock the local results gate.
- A process with file access can forge or modify the SQLite evidence database.
- Direct shell writes, external editors, and unhooked tools bypass `Write|Edit` hook checks.
- The local evaluator example has optional Bash and is **not a guaranteed read-only boundary**.
- Launcher checks are best-effort operational preflight; other Claude Code settings sources can change behavior.

For trustworthy PASS/FAIL, use a **separate evaluator or CI environment outside the builder's writable workspace**, with independently obtained browser/API evidence. Never copy these hooks into RMS as a security boundary.

## Use cases and participation

This fork is useful for **Claude Code hook authors**, maintainers of **long-running AI coding agents**, and developers debugging **Windows Git Bash execution** or **session-scoped test evidence**. It offers examples and regression tests, not automatic end-to-end agent verification.

Bug reports with minimal reproduction steps and confirmed tool/OS versions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [live QA checklist](scripts/WINDOWS-LIVE-QA.md). The original Anthropic upstream README is preserved for comparison.

## Documentation, history and attribution

- [FireXCore hardening notes](FORK-HARDENING.md)
- [Windows live acceptance procedure](scripts/WINDOWS-LIVE-QA.md)
- [Release readiness checklist](docs/RELEASE-CHECKLIST.md)
- [Repository discoverability metadata and launch copy](docs/DISCOVERY.md)
- [Original Anthropic README, preserved](UPSTREAM-README.md)
- [Upstream Anthropic repository](https://github.com/anthropics/cwc-long-running-agents)
- [Historical FireXCore PR #1](https://github.com/FireXCore/cwc-long-running-agents/pull/1)
- [Upstream related PR #3](https://github.com/anthropics/cwc-long-running-agents/pull/3), authored independently by another contributor

This work preserves upstream copyright notices and the original [Apache-2.0 license](LICENSE). Anthropic describes its example as unmaintained and not accepting contributions. Do not imply Anthropic endorsement.
