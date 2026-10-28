"""Deterministic hook contract tests; no live Claude runtime is simulated."""
import json
import os
from pathlib import Path
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
        self.proof = self.root / "screenshots" / "proof.png"
        self.proof.write_bytes(b"mock evidence")
        self.results = self.root / "test-results.json"
        self.results.write_text('{"passes":false}\n')
        self.log = self.root / ".claude" / ".evidence-reads"
        self.env = {**os.environ, "VERIFY_READ_LOG": str(self.log),
                    "RESULTS_FILE": str(self.results)}

    def hook(self, script, *, tool="Write", event="PreToolUse",
             path=None, session="first", payload=None):
        obj = {"tool_name": tool, "hook_event_name": event,
               "cwd": str(self.root), "session_id": session,
               "tool_input": {"file_path": str(path or self.results)}}
        proc = subprocess.run(
            ["bash", str(HOOKS / script)],
            input=json.dumps(obj) if payload is None else payload,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=self.env, cwd=self.root, check=True)
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def read(self, session="first", path=None, event="PostToolUse"):
        self.hook("track-read.sh", tool="Read", event=event,
                  path=path or self.proof, session=session)

    def blocked(self, verdict):
        self.assertEqual(verdict["hookSpecificOutput"]["hookEventName"],
                         "PreToolUse")
        self.assertEqual(verdict["hookSpecificOutput"]["permissionDecision"],
                         "deny")

    def test_settings_register_read_after_success(self):
        hooks = json.loads(SETTINGS.read_text())["hooks"]
        self.assertFalse(any(x.get("matcher") == "Read" for x in hooks["PreToolUse"]))
        self.assertTrue(any(x.get("matcher") == "Read" for x in hooks["PostToolUse"]))
        self.assertNotIn("Stop", hooks)

    def test_no_evidence_denied(self):
        self.blocked(self.hook("verify-gate.sh"))

    def test_successful_read_unlocks_exactly_once(self):
        self.read()
        self.assertIsNone(self.hook("verify-gate.sh"))
        self.blocked(self.hook("verify-gate.sh"))

    def test_failed_or_pretool_read_does_not_unlock(self):
        self.read(event="PreToolUse")
        self.read(event="PostToolUseFailure")
        self.blocked(self.hook("verify-gate.sh"))

    def test_session_isolation(self):
        self.read(session="first")
        self.blocked(self.hook("verify-gate.sh", session="second"))
        self.assertIsNone(self.hook("verify-gate.sh", session="first"))

    def test_stale_hash_denied(self):
        self.read()
        self.proof.write_bytes(b"changed")
        self.blocked(self.hook("verify-gate.sh"))

    def test_deleted_evidence_denied(self):
        self.read()
        self.proof.unlink()
        self.blocked(self.hook("verify-gate.sh"))

    def test_non_evidence_and_missing_file_denied(self):
        missing = self.root / "screenshots" / "missing.png"
        self.read(path=missing)
        text = self.root / "ordinary.txt"
        text.write_text("ordinary")
        self.read(path=text)
        self.blocked(self.hook("verify-gate.sh"))

    def test_corrupt_log_denied(self):
        self.log.write_text("bad JSON")
        self.blocked(self.hook("verify-gate.sh"))

    def test_unrelated_write_allowed(self):
        self.assertIsNone(self.hook("verify-gate.sh",
                                    path=self.root / "other.json"))

    def test_bad_input_denied(self):
        self.blocked(self.hook("verify-gate.sh", payload="not-json"))

    def test_kill_switch_modern_schema(self):
        (self.root / "AGENT_STOP").touch()
        self.blocked(self.hook("kill-switch.sh"))

    def test_steering_modern_schema(self):
        note = self.root / "STEER.md"
        note.write_text('halt "now"\nand inspect')
        verdict = self.hook("steer.sh")
        self.blocked(verdict)
        self.assertIn('"now"', verdict["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(note.read_text(), "")

    def test_auto_commit_requires_opt_in(self):
        script = (HOOKS / "commit-on-stop.sh").read_text()
        self.assertIn('CWC_AUTO_COMMIT_ON_STOP:-0', script)


if __name__ == "__main__":
    unittest.main()
