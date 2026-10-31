# FireXCore fork: hook hardening after Windows QA

Derived from Anthropic's Apache-2.0 educational example. Keep the
upstream LICENSE and attribution. **Not a security boundary.**

## Corrected behavior
- Successful PostToolUse(Read) only; failed or attempted reads do not unlock a write.
- SHA-256, session-scoped evidence records within local screenshots/ or evidence/.
- SQLite BEGIN IMMEDIATE serializes evidence consumption across sessions.
- One Read permits at most one Write/Edit to the configured results file.
- Aliases/hardlinks to an existing results file are checked via samefile.
- Evidence expires after 900 seconds by default (CWC_EVIDENCE_TTL_SECONDS).
- Probe an actually working Python 3.9+ interpreter; Windows Store stubs fail.
- Steering notes are not removed when the Python runtime is unavailable.
- Stop auto-commit is disabled by default. No Stop hook is registered.

- PreToolUse command hooks now specify `onFailure: "block"` (requires
  Claude Code 2.1.295+). A missing Git Bash, crashing command, invalid output,
  or timeout blocks the tool call rather than silently allowing it.
  This is still NOT a security boundary; Bash can bypass Write/Edit events.

## Windows: verified launcher required for safe startup
1. Copy claude-code-config/.claude to a *disposable project* root.
2. Open PowerShell in that project root.
3. Run the absolute path to scripts/launch-claude-verified.ps1
   located in this fork (PowerShell call operator &).
4. The launcher must print CWC preflight PASS. It sets
   CLAUDE_CODE_GIT_BASH_PATH and CWC_PYTHON_BIN for the child process.
5. Do not assume raw 'claude' starts the Bash hooks on Windows.

## Remaining risks: NOT FIXED by these hooks
- An agent can write its own screenshot/log and read it; this is NOT proof.
- The agent can forge/alter its local SQLite audit database or invoke shell
  commands to edit test-results.json without passing Write/Edit hooks.
- SQLite prevents the observed double-spend race but provides no evidence
  authenticity, tamper-proofing, or authorization boundary.
- A trusted *external* evaluator must inspect actual browser/API results
  and determine PASS/FAIL outside the builder's writable workspace.
- Live Windows retesting of this revision is pending. CI uses mock events.
- Do not deploy these examples as security isolation for RMS or tenants.

## Tests
Run: python -m unittest discover -s tests -v
The old JSONL audit log (.claude/.evidence-reads) is no longer used.
The SQLite file is .claude/.evidence-reads.sqlite3 unless CWC_AUDIT_DB is set.

## Upstream attribution
The PreToolUse schema change overlaps upstream PR #3 by @reginaldalfret.
The PostToolUse(Read) lifecycle issue is distinct. Anthropic identifies the
original demo as unmaintained and not accepting contributions.
