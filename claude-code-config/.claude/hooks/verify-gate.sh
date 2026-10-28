#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Advisory PreToolUse gate: does not cover Bash or external writes.
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Cannot validate evidence: python3 unavailable"}}'
  exit 0
fi
python3 "$(dirname "$0")/evidence_audit.py" check || printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Cannot validate evidence: audit helper error"}}'
