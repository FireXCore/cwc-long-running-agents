#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Advisory only: direct Bash/PowerShell file writes bypass this gate.
source "$(dirname "$0")/python-bin.sh"
if ! cwc_select_python; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Evidence audit unavailable: real Python 3.9+ required"}}'
  exit 0
fi
"$CWC_SELECTED_PYTHON" "$(dirname "$0")/evidence_audit.py" check ||
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Evidence audit helper failed"}}'
