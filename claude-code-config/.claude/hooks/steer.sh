#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Advisory operator steering; preserves notes if Python is unavailable.
f="$AGENT_STEER_FILE"
if [ -z "$f" ]; then f="./STEER.md"; fi
if [ -s "$f" ]; then
  source "$(dirname "$0")/python-bin.sh"
  if ! cwc_select_python; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Steering pending: real Python 3.9+ required; STEER.md preserved"}}'
    exit 0
  fi
  note=$(cat "$f")
  reason=$("$CWC_SELECTED_PYTHON" -c 'import json,sys; print(json.dumps("OPERATOR STEERING: "+sys.argv[1]+"\\n\\nPause, incorporate this guidance, then continue."))' "$note")
  if [ $? -ne 0 ] || [ -z "$reason" ]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Steering helper failed; STEER.md preserved"}}'
    exit 0
  fi
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' "$reason"
  : > "$f"
fi
