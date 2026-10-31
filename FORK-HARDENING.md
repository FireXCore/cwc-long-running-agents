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
  Claude Code 2.1.295+). A crashing command, invalid output, or timeout
  blocks the tool call rather than silently allowing it.
- Every hook also pins `"shell": "bash"`. Without it, Windows Claude Code
  with no Git Bash runs the `.sh` command through PowerShell, which exits 0
  with no JSON, so `onFailure` never triggers and every tool call is allowed
  (reproduced live on 2.1.312). With `shell: bash` the hook fails to start and
  `onFailure: "block"` blocks the call. Without Git Bash all tools are then
  blocked: fail closed, not usable.
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
- Live Windows acceptance was run on one host (Windows 10 19045, Claude Code
  2.1.312, Windows PowerShell 5.1, Git for Windows outside Program Files);
  see PR #1. CI uses mock events only. `shell: bash` failing closed without
  Git Bash was verified on 2.1.312. The docs give no minimum version for
  `shell`, so older builds are unverified.
- Windows PowerShell 5.1 strips embedded double quotes from arguments the
  launcher forwards to `claude`. Pass prompts on stdin, not as arguments.
- With the results file absent, Win32 aliases (trailing dot/space, `\\?\`,
  `::$DATA`) are now gated. Other spellings that only the OS resolves (for
  example admin shares) are caught only once the file exists.
- Do not deploy these examples as security isolation for RMS or tenants.

## Tests
Run: python -m unittest discover -s tests -v
The old JSONL audit log (.claude/.evidence-reads) is no longer used.
The SQLite file is .claude/.evidence-reads.sqlite3 unless CWC_AUDIT_DB is set.

## Upstream attribution
The PreToolUse schema change overlaps upstream PR #3 by @reginaldalfret.
The PostToolUse(Read) lifecycle issue is distinct. Anthropic identifies the
original demo as unmaintained and not accepting contributions.
