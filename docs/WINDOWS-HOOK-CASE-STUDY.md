# Case study: Claude Code shell hooks silently fail open on Windows

**Audience:** developers using Claude Code `PreToolUse` hooks or debugging long-running coding agents on Windows.

**Scope:** one tested Windows host, Claude Code 2.1.312. This is a technical reproduction of an **operational hook integration failure**, not a claim that Claude Code or these hooks provide a security sandbox.

## The incident

While auditing the long-running agent example, a Windows run showed that placing an `AGENT_STOP` file did **not** block a Write tool call. The Claude Code hook configuration still registered the Bash hook.

The critical distinction: if Git Bash was unavailable, a `.sh` hook could be sent through the host's PowerShell fallback. That command could exit **0**, emit no usable JSON decision, and permit the tool call. Setting `"onFailure": "block"` *alone* was insufficient in this case because the hook process did not fail.

See the [full FireXCore live acceptance and review in PR #1](https://github.com/FireXCore/cwc-long-running-agents/pull/1). The underlying historical `PreToolUse` decision-schema issue was already reported independently in [Anthropic issue #2](https://github.com/anthropics/cwc-long-running-agents/issues/2) and addressed in [upstream PR #3](https://github.com/anthropics/cwc-long-running-agents/pull/3), authored by another contributor.

## How the failure was reproduced

On the tested Windows environment, without usable Git Bash configuration:

1. Copy the demo's `.claude` hook configuration into an **isolated scratch project**.
2. Create an `AGENT_STOP` file in the scratch project's root.
3. Launch Claude Code; request one harmless Write (a disposable canary file).
4. Inspect the actual tool event and the resulting file, not the model's verbal summary.

**Observed before fix:** the canary Write succeeded while the stop file existed. This contradicts the intended kill-switch behavior.

**After the fix:** explicitly pinning `"shell": "bash"` and `"onFailure": "block"` caused tool execution to be denied when Git Bash could not launch. When Bash was available, the kill-switch's `hookSpecificOutput.permissionDecision = deny` was respected.

The documented observation comes from one Windows 10 host with Claude Code 2.1.312. The configuration must be revalidated if Claude Code changes its shell or failure-handling behavior.

### Relevant configuration

```json
{
  "type": "command",
  "command": ".claude/hooks/kill-switch.sh",
  "shell": "bash",
  "onFailure": "block"
}
```

This is the critical part of the **existing** `PreToolUse` hook settings in this fork; it is *not* a general sandbox policy. Use the full [settings.json](../claude-code-config/.claude/settings.json) when inspecting behavior.

## What else changed in the FireXCore fork?

- A PowerShell preflight launcher detects a working Git Bash and Python interpreter and checks selected hook settings.
- Read evidence is recorded after `PostToolUse(Read)`, with a session identifier, path scope, SHA-256 checksum and short expiry.
- SQLite transactions prevent a single recorded read from being consumed by two concurrent gated Writes in the **hook-level** test harness.
- A small standalone demo reproduces **DENY → RECORD → ALLOW ONCE → DENY** without needing a Claude Code subscription.
- Regression tests run on Windows and Ubuntu across Python 3.9 and 3.12.

**Evidence:** [original live QA PR](https://github.com/FireXCore/cwc-long-running-agents/pull/1), [current CI](https://github.com/FireXCore/cwc-long-running-agents/actions/workflows/hook-contract-tests.yml), [two-minute local demo](DEMO.md).

## Boundaries and non-goals

- A builder with shell access can still write to the results file without triggering `Write|Edit` hooks.
- The builder can create fake evidence, read it, or forge the local SQLite database.
- A successful hook-level unit test is not the same as a live Claude Code acceptance test.
- The launcher is a convenience preflight; it does not authenticate evidence or certify all configuration sources.
- No production security guarantee or independent application-level PASS is claimed.

**The engineering lesson:** a hook can be registered yet ineffective. Test the host's actual tool-call behavior, startup errors and on-disk state; do not infer safety from a syntactically valid configuration or a zero exit code.

## Try a safe local demonstration

```bash
git clone https://github.com/FireXCore/cwc-long-running-agents.git
cd cwc-long-running-agents
python3 examples/demo_evidence_gate.py
```

On Windows, use `py -3 examples\demo_evidence_gate.py` if `python3` is only a Store alias. The demo is synthetic and intentionally does not modify real application results.

## Credit

FireXCore is an independent fork of Anthropic's original educational example and preserves Apache-2.0 attribution. The earlier decision-schema finding was reported by a separate community member and upstream PR #3 belongs to its author. No affiliation with or endorsement by Anthropic is implied.
