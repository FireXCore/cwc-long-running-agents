#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
cwc_select_python() {
  local candidate answer
  if [ -n "$CWC_PYTHON_BIN" ]; then
    candidates=("$CWC_PYTHON_BIN")
  else
    candidates=(python3 python)
  fi
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      answer=$("$candidate" -c 'import sys,sqlite3; print("CWC_OK" if sys.version_info >= (3,9) else "CWC_OLD")' 2>/dev/null)
      if [ "$answer" = "CWC_OK" ]; then
        CWC_SELECTED_PYTHON="$candidate"
        return 0
      fi
    fi
  done
  return 1
}
