"""Mock hook contracts (not live Claude Code or trusted provenance tests)."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "claude-code-config" / ".claude" / "hooks"
SETTINGS = ROOT / "claude-code-config" / ".claude" / "settings.json"

class HookGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / ".claude").mkdir()
        (self.root / "screenshots").mkdir()
        (self.root / "evidence").mkdir()
        self.proof = self.root / "screenshots" / "proof.png"
        self.proof.write_bytes(b"mock evidence")
        self.results = self.root / "test-results.json"
        self.results.write_text('{"passes":false}\n')
        self.db = self.root / ".claude" / ".evidence-reads.sqlite3"
        self.env = {**os.environ, "CWC_AUDIT_DB": str(self.db),
                    "RESULTS_FILE": str(self.results)}

    def hook(self, script, tool="Write", event="PreToolUse",
             path=None, session="first", payload=None, env=None):
        obj = {"tool_name": tool, "hook_event_name": event,
               "cwd": str(self.root), "session_id": session,
               "tool_input": {"file_path": str(path or self.results)}}
        environment = dict(env or self.env)
        if os.name == "nt":
            # Git Bash cannot open Windows backslash paths as script arguments.
            environment["CWC_HOOK_SCRIPT"] = str(HOOKS / script)
            command = ["bash", "-c",
                       'exec bash "$(cygpath -u "$CWC_HOOK_SCRIPT")"']
        else:
            command = ["bash", str(HOOKS / script)]
        proc = subprocess.run(
            command, input=json.dumps(obj) if payload is None else payload,
            text=True, capture_output=True, env=environment, cwd=self.root)
        self.assertEqual(proc.returncode, 0,
                         f"Hook failed: {proc.stderr!r} {proc.stdout!r}")
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def read(self, session="first", path=None, event="PostToolUse"):
        self.hook("track-read.sh", tool="Read", event=event,
                  path=path or self.proof, session=session)

    def denied(self, verdict):
        self.assertEqual(verdict["hookSpecificOutput"]["hookEventName"],
                         "PreToolUse")
        self.assertEqual(verdict["hookSpecificOutput"]["permissionDecision"],
                         "deny")

    def test_settings_post_read_only(self):
        hooks = json.loads(SETTINGS.read_text())["hooks"]
        self.assertFalse(any(x.get("matcher") == "Read" for x in hooks["PreToolUse"]))
        self.assertTrue(any(x.get("matcher") == "Read" for x in hooks["PostToolUse"]))
        self.assertNotIn("Stop", hooks)

    def test_no_evidence_denied(self):
        self.denied(self.hook("verify-gate.sh"))

    def test_read_spent_exactly_once(self):
        self.read()
        self.assertIsNone(self.hook("verify-gate.sh"))
        self.denied(self.hook("verify-gate.sh"))

    def test_failed_read_does_not_unlock(self):
        self.read(event="PreToolUse")
        self.read(event="PostToolUseFailure")
        self.denied(self.hook("verify-gate.sh"))

    def test_session_isolation(self):
        self.read("first")
        self.denied(self.hook("verify-gate.sh", session="second"))
        self.assertIsNone(self.hook("verify-gate.sh", session="first"))

    def test_hash_drift(self):
        self.read()
        self.proof.write_bytes(b"changed")
        self.denied(self.hook("verify-gate.sh"))

    def test_deleted_evidence(self):
        self.read()
        self.proof.unlink()
        self.denied(self.hook("verify-gate.sh"))

    def test_outside_workspace_evidence(self):
        external = self.root.parent / (self.root.name + "-external.png")
        external.write_bytes(b"outside")
        self.addCleanup(lambda: external.unlink(missing_ok=True))
        self.read(path=external)
        self.denied(self.hook("verify-gate.sh"))

    def test_non_evidence_or_missing(self):
        self.read(path=self.root / "evidence" / "missing.png")
        non = self.root / "evidence" / "ordinary.txt"
        non.write_text("not evidence")
        self.read(path=non)
        self.denied(self.hook("verify-gate.sh"))

    def test_hardlink_to_results(self):
        alias = self.root / "results-hardlink"
        os.link(self.results, alias)
        self.denied(self.hook("verify-gate.sh", path=alias))

    def test_ttl_expired(self):
        self.read()
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE reads SET observed=1")
        self.denied(self.hook("verify-gate.sh"))

    def test_ttl_invalid_fails_closed(self):
        self.read()
        env = {**self.env, "CWC_EVIDENCE_TTL_SECONDS": "0"}
        self.denied(self.hook("verify-gate.sh", env=env))

    def test_corrupt_db_denied(self):
        self.db.write_bytes(b"not sqlite")
        self.denied(self.hook("verify-gate.sh"))

    def test_unrelated_write(self):
        self.assertIsNone(self.hook("verify-gate.sh",
                                    path=self.root / "other.json"))

    def test_malformed_input(self):
        self.denied(self.hook("verify-gate.sh", payload="{not json"))

    def test_kill_switch_schema(self):
        (self.root / "AGENT_STOP").touch()
        self.denied(self.hook("kill-switch.sh"))

    def test_operator_steering_schema(self):
        note = self.root / "STEER.md"
        note.write_text('halt "now"')
        self.denied(self.hook("steer.sh"))
        self.assertEqual(note.read_text(), "")

    def test_no_stop_autocommit(self):
        script = (HOOKS / "commit-on-stop.sh").read_text()
        self.assertIn("CWC_AUTO_COMMIT_ON_STOP:-0", script)

    def test_concurrent_consumers_only_one_grant(self):
        self.read()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.hook("verify-gate.sh"), range(20)))
        self.assertEqual(sum(result is None for result in results), 1)
        self.assertEqual(sum(result is not None for result in results), 19)

    def test_parallel_sessions_do_not_lose_evidence(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(self.read, ("first", "second")))
        self.assertIsNone(self.hook("verify-gate.sh", session="first"))
        self.assertIsNone(self.hook("verify-gate.sh", session="second"))

    def test_store_python_stub_fails_closed(self):
        stub = self.root / "fake-python"
        stub.write_text("#!/bin/sh\nexit 0\n")
        stub.chmod(0o755)
        env = {**self.env, "CWC_PYTHON_BIN": str(stub)}
        self.denied(self.hook("verify-gate.sh", env=env))
        note = self.root / "STEER.md"
        note.write_text("operator message")
        self.denied(self.hook("steer.sh", env=env))
        self.assertEqual(note.read_text(), "operator message")

    def test_self_minted_evidence_is_still_untrusted(self):
        # KNOWN LIMITATION: shows this is an advisory gate, not certification.
        file = self.root / "evidence" / "self-console.txt"
        file.write_text("invented PASS")
        self.read(path=file)
        self.assertIsNone(self.hook("verify-gate.sh"))

    def test_forged_sqlite_entry_is_still_untrusted(self):
        # KNOWN LIMITATION: local agent can edit SQLite directly.
        import hashlib
        import time
        self.read()  # initialize database
        with sqlite3.connect(self.db) as db:
            db.execute("DELETE FROM reads")
            db.execute("INSERT INTO reads(session,path,sha,observed) VALUES(?,?,?,?)",
                       ("first", str(self.proof),
                        hashlib.sha256(self.proof.read_bytes()).hexdigest(), time.time()))
        self.assertIsNone(self.hook("verify-gate.sh"))

if __name__ == "__main__":
    unittest.main()
