"""Mock hook contracts (not live Claude Code or trusted provenance tests)."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "claude-code-config" / ".claude" / "hooks"
SETTINGS = ROOT / "claude-code-config" / ".claude" / "settings.json"
LAUNCHER = ROOT / "scripts" / "launch-claude-verified.ps1"

def git_bash():
    """Git Bash on Windows; 'bash' on PATH may resolve to WSL's stub."""
    if os.environ.get("CWC_TEST_GIT_BASH"):
        return os.environ["CWC_TEST_GIT_BASH"]
    git = shutil.which("git")
    if git:  # install root above cmd\git.exe or mingw64\bin\git.exe
        for parent in list(Path(git).resolve().parents)[:3]:  # 3.9: no slicing
            if (parent / "bin" / "bash.exe").is_file():
                return str(parent / "bin" / "bash.exe")
    return r"C:\Program Files\Git\bin\bash.exe"

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
            environment["CWC_HOOK_SCRIPT"] = str(HOOKS / script)
            command = [git_bash(), "-c",
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

    def test_critical_pretool_hooks_fail_closed(self):
        hooks = json.loads(SETTINGS.read_text())["hooks"]["PreToolUse"]
        critical = [hook for group in hooks for hook in group["hooks"]]
        self.assertEqual(len(critical), 3)
        self.assertTrue(all(hook.get("onFailure") == "block"
                            for hook in critical))

    def test_hooks_pin_bash_shell(self):
        # Without Git Bash, Windows Claude Code otherwise runs .sh commands via
        # PowerShell, which exits 0 without output and allows the tool call
        # even with onFailure=block. shell=bash makes the hook fail to start.
        hooks = json.loads(SETTINGS.read_text())["hooks"]
        every = [h for groups in hooks.values() for g in groups for h in g["hooks"]]
        self.assertTrue(every)
        self.assertTrue(all(h.get("shell") == "bash" for h in every))

    def launcher(self, version="2.1.312 (Claude Code)", settings=None, args=()):
        fake = self.root / "fakebin"
        fake.mkdir(exist_ok=True)
        shown =version.replace("(", "^(").replace(")", "^)")  # cmd block syntax
        (fake / "claude.cmd").write_text(
            f'@if "%1"=="--version" (echo {shown}) else (echo ARGS: %*)\r\n')
        if settings != "absent":
            (self.root / ".claude" / "settings.json").write_text(
                settings if settings is not None else SETTINGS.read_text())
        env = {**os.environ, "PATH": str(fake) + os.pathsep + os.environ["PATH"]}
        env.pop("CLAUDE_CODE_GIT_BASH_PATH", None)
        # Windows PowerShell 5.1, the default shell, not pwsh.
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-File", str(LAUNCHER), *args],
            capture_output=True, text=True,
            env=env, cwd=self.root, timeout=120)

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_preflight_passes_on_powershell_51(self):
        proc = self.launcher()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("CWC preflight PASS", proc.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_forwards_claude_flags(self):
        flags = ["-p", "--model", "sonnet", "--verbose", "--debug", "hooks"]
        proc = self.launcher(args=flags)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ARGS: " + " ".join(flags), proc.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_refuses_old_claude_with_exit_2(self):
        proc = self.launcher(version="2.1.200 (Claude Code)")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("2.1.295+", proc.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_refuses_without_settings(self):
        proc = self.launcher(settings="absent")
        self.assertEqual(proc.returncode, 2, proc.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_refuses_unguarded_settings(self):
        unpinned = SETTINGS.read_text().replace('"shell": "bash",', "")
        for text in ("{}", unpinned):
            with self.subTest(settings=text[:20]):
                proc = self.launcher(settings=text)
                self.assertEqual(proc.returncode, 2, proc.stderr)
        (self.root / ".claude" / "settings.local.json").write_text(
            '{"disableAllHooks": true}')
        proc = self.launcher()
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("disableAllHooks", proc.stderr)

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

    @unittest.skipUnless(os.name == "nt", "Win32 path aliases")
    def test_win32_aliases_before_results_exist(self):
        # samefile() cannot help while the results file does not exist yet.
        self.results.unlink()
        name = str(self.results)
        for alias in (name + ".", name + " ", name + ". ", "\\\\?\\" + name,
                      "\\\\.\\" + name, name + "::$DATA", name.upper()):
            with self.subTest(alias=alias):
                self.denied(self.hook("verify-gate.sh", path=alias))

    def test_ttl_expired(self):
        self.read()
        with closing(sqlite3.connect(self.db)) as db, db:
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
        verdict = self.hook("steer.sh")
        self.denied(verdict)
        reason = verdict["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn('halt "now"\n\nPause', reason)  # real newlines, not "\\n"
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
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("DELETE FROM reads")
            db.execute("INSERT INTO reads(session,path,sha,observed) VALUES(?,?,?,?)",
                       ("first", str(self.proof),
                        hashlib.sha256(self.proof.read_bytes()).hexdigest(), time.time()))
        self.assertIsNone(self.hook("verify-gate.sh"))

if __name__ == "__main__":
    unittest.main()
