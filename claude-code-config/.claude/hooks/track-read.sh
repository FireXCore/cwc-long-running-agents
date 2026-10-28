#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Record evidence after successful Read, scoped by Claude session and file digest.
# Teaching aid only; an agent with shell access can bypass local hooks.
python3 "$(dirname "$0")/evidence_audit.py" record
