# FireXCore fork — evidence gate hardening

Derived from Anthropic's Apache-2.0 educational example. Keep upstream LICENSE
and copyright notices. This is **not** a hardened sandbox or a security boundary.

## Improvements
- Evidence-read accounting is registered under PostToolUse(Read) rather than
  PreToolUse(Read), so an attempted/failed Read cannot unlock a result edit.
- A recorded evidence path must be a qualifying, existing file with the same
  SHA-256 digest, read in the same Claude Code session.
- Gate responses use documented hookSpecificOutput / permissionDecision=deny.
- No Stop auto-commit hook is registered by default. The retained checkpoint
  script requires CWC_AUTO_COMMIT_ON_STOP=1 and explicit registration.
- Mock-event regression tests cover hook registration, isolation, integrity,
  malformed inputs, kill switch and operator steering.

## Known limits
- An agent with Bash access can bypass Write/Edit hooks, alter audit logs, or
  edit result files directly. Hashing does not make the log tamper-proof.
- The shared JSONL audit file has no interprocess locking; simultaneous sessions
  can race when consuming entries. Do not use this as a concurrent trust store.
- Any qualifying evidence can unlock any result row. Test-to-proof binding and
  independent inspection are still required.
- Require Bash, Python 3, and appropriate executable permissions. On Windows
  use Git Bash or replace shell hooks with native Python command hooks.
- Tests mock hook payloads. Live Claude Code integration and real browser
  evaluation are **not** demonstrated by these tests.
- Keep project-specific tenant data, credentials, screenshots, and private
  configuration out of public forks.

## Verification
Run from repository root:
\`\`\`bash
python3 -m unittest discover -s tests -v
\`\`\`

Upstream PR #3 by @reginaldalfret independently addresses the older PreToolUse
decision response schema; this fork preserves credit and does not claim to
have originated that fix. The separate Read lifecycle bug is documented
independently. Anthropic states that its demonstration repository is
unmaintained and not accepting contributions.
