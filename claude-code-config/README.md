# Claude Code config: long-running primitives

Example implementations of the long-running primitives as native Claude Code hooks. Copy `.claude/` into your project as a starting point and adapt the file paths and matching rules to fit.

**Requires:** `bash`, `git`, `python3` (the hooks parse JSON via python3; without it they silently no-op).

```bash
cp -r .claude/ /path/to/your/project/
chmod +x /path/to/your/project/.claude/hooks/*.sh
cd /path/to/your/project && claude
```

| File | Primitive |
|---|---|
| `.claude/hooks/kill-switch.sh` | Halt every tool call while `./AGENT_STOP` exists |
| `.claude/hooks/steer.sh` | Surface `./STEER.md` content to the agent once, then clear it |
| `.claude/hooks/track-read.sh` + `verify-gate.sh` | Deny marking a test passing until evidence (screenshot/console log) has been Read |
| `.claude/hooks/commit-on-stop.sh` | Optional session checkpoint; disabled by default in this fork |
| `.claude/CLAUDE.md` | Progress-file convention, one-feature-at-a-time, proof-before-passing |

The verify gate guards a results file you create in your project (default name `test-results.json`; override with `RESULTS_FILE`). Shape it however you like; the hook only cares that the file exists and that the agent opened evidence before touching it. A minimal starting point:

```json
{ "feature-1": { "passes": false }, "feature-2": { "passes": false } }
```

In this fork the gate records successful Read calls only, uses session identifiers and SHA-256 to detect stale evidence, and consumes a record on the next permitted results edit. It remains advisory and can be bypassed via Bash or by modifying local files. The gate tracks evidence at the session level (any screenshot opened unlocks one write). For per-test evidence tracking, extend `track-read.sh` to record which test ID each screenshot belongs to and have `verify-gate.sh` match on that.

For unattended multi-session runs, pair this config with the [`ralph-loop`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop) plugin or a wrapper script that calls `claude -p "continue from PROGRESS.md"` in a loop.

## FireXCore fork notes

This fork removes the default Stop/auto-commit registration. The optional
`commit-on-stop.sh` script requires both an explicit Stop hook registration
and `CWC_AUTO_COMMIT_ON_STOP=1`. Do not enable it in sensitive repositories.
See [FORK-HARDENING.md](../FORK-HARDENING.md) and run
`python3 -m unittest discover -s tests -v` before use.
