#!/usr/bin/env python3
"""Local educational demo of FireXCore's advisory evidence gate.

Executes evidence_audit.py directly with synthetic hook events.
Does NOT invoke Claude Code or certify any application test.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HOOK = Path(__file__).resolve().parents[1] / "claude-code-config" / ".claude" / "hooks" / "evidence_audit.py"


def call(mode, event, env):
    proc = subprocess.run(
        [sys.executable, str(HOOK), mode],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def main():
    with tempfile.TemporaryDirectory(prefix="cwc-demo-") as directory:
        root = Path(directory)
        (root / ".claude").mkdir()
        (root / "evidence").mkdir()
        proof = root / "evidence" / "demo-console.txt"
        proof.write_text("Synthetic demo evidence, not verified test output.\n", encoding="utf-8")
        result = root / "test-results.json"
        result.write_text('{"passes": false}\n', encoding="utf-8")
        session = "educational-demo-session"
        env = dict(os.environ)
        env["CWC_AUDIT_DB"] = str(root / ".claude" / "demo-evidence.sqlite3")
        env["RESULTS_FILE"] = str(result)
        write = {
            "cwd": str(root),
            "session_id": session,
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(result), "content": '{"passes": true}'},
        }
        read = {
            "cwd": str(root),
            "session_id": session,
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": str(proof)},
        }
        first = call("check", write, env)
        if not first or first.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
            raise RuntimeError("Initial write was not denied")
        print("1. Without Read: DENIED")

        call("record", read, env)
        print("2. Synthetic PostToolUse(Read): RECORDED")

        granted = call("check", write, env)
        if granted is not None:
            raise RuntimeError("Expected one advisory grant after evidence Read")
        print("3. First results write after Read: ALLOWED")

        later = call("check", write, env)
        if not later or later.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
            raise RuntimeError("Second results write was not denied")
        print("4. Second results write, no new Read: DENIED")
        if result.read_text(encoding="utf-8") != '{"passes": false}\n':
            raise RuntimeError("Demo touched the results file unexpectedly")

    print("PASS: Local hook-accounting demonstration only. No real application was tested.")


if __name__ == "__main__":
    main()
