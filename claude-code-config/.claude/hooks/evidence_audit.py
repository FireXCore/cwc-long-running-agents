#!/usr/bin/env python3
# Copyright 2026 FireXCore contributors
# SPDX-License-Identifier: Apache-2.0
"""Best-effort, session-scoped evidence audit. NOT a security boundary.

Only a separate trusted evaluator/CI may certify results. An agent with
shell access can forge this log, skip the hook, or edit results via Bash.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def _payload():
    try:
        value = json.load(sys.stdin)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def _root(event):
    cwd = event.get("cwd")
    if cwd is not None and not isinstance(cwd, str):
        raise ValueError("invalid cwd")
    return Path(cwd or os.getcwd()).resolve()


def _path(value, cwd):
    if not isinstance(value, str) or not value:
        return None
    try:
        candidate = Path(value)
        return (candidate if candidate.is_absolute() else cwd / candidate).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _log(cwd):
    return _path(os.environ.get("VERIFY_READ_LOG", ".claude/.evidence-reads"), cwd)


def _evidence(path):
    name = path.name
    return "/screenshots/" in path.as_posix().replace("\\", "/") or name.endswith(
        ("-console.txt", "-result.txt", ".png")
    )


def _digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))


def _record(event):
    if (not event or event.get("hook_event_name") != "PostToolUse"
            or event.get("tool_name") != "Read"):
        return
    payload = event.get("tool_input")
    if not isinstance(payload, dict):
        return
    cwd = _root(event)
    path = _path(payload.get("file_path"), cwd)
    session = event.get("session_id")
    if not isinstance(session, str) or not session or not path or not _evidence(path):
        return
    if not path.is_file():
        return
    try:
        row = {"session": session, "path": str(path), "sha256": _digest(path)}
        log = _log(cwd)
        log.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(log), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        try:
            os.write(fd, (json.dumps(row, separators=(",", ":")) + "\n").encode())
        finally:
            os.close(fd)
    except OSError:
        return  # Absence of evidence denies the next guarded write.


def _entries(log):
    if not log.is_file():
        return []
    rows = []
    for line in log.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if not isinstance(row, dict) or not all(
                isinstance(row.get(key), str) and row[key]
                for key in ("session", "path", "sha256")):
            raise ValueError("invalid evidence record")
        rows.append(row)
    return rows


def _save(log, rows):
    log.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=log.parent,
                prefix=".evidence-", delete=False) as stream:
            temp = Path(stream.name)
            for row in rows:
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")
        os.replace(temp, log)
    finally:
        if temp and temp.exists():
            temp.unlink()


def _check(event):
    if (not event or event.get("hook_event_name") != "PreToolUse"
            or event.get("tool_name") not in ("Write", "Edit")
            or not isinstance(event.get("tool_input"), dict)):
        _deny("Malformed results-edit hook event")
        return
    cwd = _root(event)
    target = _path(event["tool_input"].get("file_path"), cwd)
    results = _path(os.environ.get("RESULTS_FILE", "test-results.json"), cwd)
    if target is None or results is None:
        _deny("Missing results-edit file path")
        return
    if target != results:
        return
    session = event.get("session_id")
    if not isinstance(session, str) or not session:
        _deny("Missing session identifier")
        return
    try:
        log = _log(cwd)
        rows = _entries(log)
        valid = any(
            row["session"] == session
            and (p := _path(row["path"], cwd)) is not None
            and p.is_file() and _evidence(p)
            and _digest(p) == row["sha256"]
            for row in rows
        )
        if not valid:
            _deny("No fresh, unchanged evidence read in this session")
            return
        _save(log, [row for row in rows if row["session"] != session])
    except (OSError, ValueError, TypeError):
        _deny("Evidence audit log missing, corrupt, or unwritable")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    data = _payload()
    if action == "record":
        _record(data)
    elif action == "check":
        _check(data)
    else:
        sys.exit(2)
