# Two-minute local demo: evidence-read gate

This demo uses only Python's standard library. It does **not** install Claude Code, change global settings, contact external services, or use real screenshots.

```bash
git clone https://github.com/FireXCore/cwc-long-running-agents.git
cd cwc-long-running-agents
python3 examples/demo_evidence_gate.py
```

On Windows, run `py -3 examples\demo_evidence_gate.py` when `python3` resolves to the Microsoft Store stub.

Expected:

```text
1. Without Read: DENIED
2. Synthetic PostToolUse(Read): RECORDED
3. First results write after Read: ALLOWED
4. Second results write, no new Read: DENIED
PASS: Local hook-accounting demonstration only. No real application was tested.
```

The demo creates a temporary directory, records a synthetic PostToolUse(Read) event, checks two PreToolUse(Write) events, verifies that the result file was **not** changed, and deletes its own files. It demonstrates SQLite consumption, **not** Claude Code hook registration, evidence authenticity, sandboxing, or software correctness.

For actual Claude Code acceptance on a disposable Windows project, read [WINDOWS-LIVE-QA.md](../scripts/WINDOWS-LIVE-QA.md). For architectural boundaries, read [FORK-HARDENING.md](../FORK-HARDENING.md).
