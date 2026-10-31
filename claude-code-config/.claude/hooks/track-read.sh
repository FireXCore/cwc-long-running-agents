#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Records only successful PostToolUse(Read) evidence.
source "$(dirname "$0")/python-bin.sh"
if cwc_select_python; then
  "$CWC_SELECTED_PYTHON" "$(dirname "$0")/evidence_audit.py" record
fi
