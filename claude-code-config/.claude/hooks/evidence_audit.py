#!/usr/bin/env python3
# Copyright 2026 FireXCore contributors
# SPDX-License-Identifier: Apache-2.0
"""Advisory evidence gate only. Agent-owned files and Bash bypass it."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

def input_event():
    try:
        e = json.load(sys.stdin)
        return e if isinstance(e, dict) else None
    except (ValueError, TypeError):
        return None

def deny(msg):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))

def root(e):
    value = e.get("cwd")
    if value is not None and not isinstance(value, str):
        raise ValueError("invalid cwd")
    return Path(value or os.getcwd()).resolve()

def resolve(value, cwd):
    if not isinstance(value, str) or not value:
        return None
    try:
        p = Path(value)
        return (p if p.is_absolute() else cwd / p).resolve()
    except (ValueError, OSError, RuntimeError):
        return None

def is_evidence(path, cwd):
    if path is None or not path.is_file():
        return False
    if not any(path != d and d in path.parents
               for d in ((cwd / "screenshots").resolve(),
                         (cwd / "evidence").resolve())):
        return False
    return path.suffix.lower() == ".png" or path.name.endswith(("-console.txt", "-result.txt"))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def ttl():
    value = int(os.environ.get("CWC_EVIDENCE_TTL_SECONDS", "900"))
    if not 1 <= value <= 86400:
        raise ValueError("invalid TTL")
    return value

def db(cwd):
    name = resolve(os.environ.get("CWC_AUDIT_DB",
                                 ".claude/.evidence-reads.sqlite3"), cwd)
    name.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(name, timeout=15, isolation_level=None)
    c.execute("PRAGMA busy_timeout=15000")
    c.execute("""CREATE TABLE IF NOT EXISTS reads (
        id INTEGER PRIMARY KEY, session TEXT NOT NULL, path TEXT NOT NULL,
        sha TEXT NOT NULL, observed REAL NOT NULL)""")
    return c

def record(e):
    if not e or e.get("hook_event_name") != "PostToolUse" or e.get("tool_name") != "Read":
        return
    obj = e.get("tool_input")
    session = e.get("session_id")
    if not isinstance(obj, dict) or not isinstance(session, str) or not session:
        return
    try:
        cwd = root(e)
        path = resolve(obj.get("file_path"), cwd)
        if not is_evidence(path, cwd):
            return
        digest = sha256(path)
        c = db(cwd)
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("INSERT INTO reads(session,path,sha,observed) VALUES(?,?,?,?)",
                      (session, str(path), digest, time.time()))
            c.commit()
        finally:
            c.close()
    except (OSError, ValueError, sqlite3.Error):
        pass

def win_key(p):
    # Win32 names that open the same file even before it exists: \\?\ and \\.\
    # prefixes, a ::$DATA stream suffix, trailing dots/spaces (abspath strips).
    s = str(p)
    if s.startswith("\\\\?\\UNC\\"):
        s = "\\\\" + s[8:]
    elif s.startswith(("\\\\?\\", "\\\\.\\")):
        s = s[4:]
    if s.lower().endswith("::$data"):
        s = s[:-7]
    return os.path.normcase(os.path.abspath(s))

def same_file(a, b):
    if a == b or (os.name == "nt" and win_key(a) == win_key(b)):
        return True
    try:
        return a.is_file() and b.is_file() and os.path.samefile(a, b)
    except OSError:
        return False

def check(e):
    if not e or e.get("hook_event_name") != "PreToolUse" or \
       e.get("tool_name") not in ("Write", "Edit") or \
       not isinstance(e.get("tool_input"), dict):
        deny("Malformed hook event")
        return
    try:
        cwd = root(e)
        target = resolve(e["tool_input"].get("file_path"), cwd)
        result = resolve(os.environ.get("RESULTS_FILE", "test-results.json"), cwd)
        if target is None or result is None:
            deny("Missing file path")
            return
        if not same_file(target, result):
            return
        session = e.get("session_id")
        if not isinstance(session, str) or not session:
            deny("Missing session")
            return
        now = time.time()
        lifetime = ttl()
        c = db(cwd)
        try:
            c.execute("BEGIN IMMEDIATE")
            rows = c.execute("SELECT path,sha,observed FROM reads WHERE session=?",
                             (session,)).fetchall()
            valid = any(0 <= now - stamp <= lifetime and
                        is_evidence(p := resolve(name, cwd), cwd) and
                        sha256(p) == digest for name, digest, stamp in rows)
            if valid:
                c.execute("DELETE FROM reads WHERE session=?", (session,))
                c.commit()
                return
            c.rollback()
        finally:
            c.close()
        deny("No fresh unchanged evidence in this session")
    except (OSError, ValueError, TypeError, sqlite3.Error):
        deny("Evidence audit failed")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode == "record":
        record(input_event())
    elif mode == "check":
        check(input_event())
    else:
        sys.exit(2)
