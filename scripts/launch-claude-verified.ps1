# SPDX-License-Identifier: Apache-2.0
# Start from a disposable project root containing .claude/settings.json.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$ClaudeArgs)
$ErrorActionPreference = 'Stop'
function Fail([string]$Message) {
  Write-Error "CWC preflight: $Message"
  exit 2
}
if (-not (Test-Path -LiteralPath '.claude/settings.json' -PathType Leaf)) {
  Fail 'No .claude/settings.json in the working directory.'
}
$candidates = @()
if ($env:CLAUDE_CODE_GIT_BASH_PATH) { $candidates += $env:CLAUDE_CODE_GIT_BASH_PATH }
$candidates += @("$env:ProgramFiles\Git\bin\bash.exe",
                 "$env:ProgramFiles\Git\usr\bin\bash.exe")
$bash = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
if (-not $bash) { Fail 'Git Bash missing. Windows Claude Code can silently skip shell hooks.' }
$probe = & $bash -lc 'printf CWC_BASH_OK' 2>$null
if ($LASTEXITCODE -ne 0 -or "$probe" -ne 'CWC_BASH_OK') { Fail 'Git Bash execution failed.' }
$python = $null
foreach ($name in @('python.exe','py.exe')) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { continue }
  if ($name -eq 'py.exe') {
    $found = & $cmd.Source -3 -c 'import sys,sqlite3; print(sys.executable if sys.version_info >= (3,9) else "")' 2>$null
  } else {
    $found = & $cmd.Source -c 'import sys,sqlite3; print(sys.executable if sys.version_info >= (3,9) else "")' 2>$null
  }
  if ($LASTEXITCODE -eq 0 -and $found -and (Test-Path -LiteralPath $found -PathType Leaf)) {
    $python = $found
    break
  }
}
if (-not $python) { Fail 'Real Python 3.9+ with sqlite3 not found (Store alias rejected).' }
$env:CLAUDE_CODE_GIT_BASH_PATH = $bash
$env:CWC_PYTHON_BIN = $python.Replace('\','/')
$probe = & $bash -lc '"$CWC_PYTHON_BIN" -c "import sys; print(sys.version_info.major)"' 2>$null
if ($LASTEXITCODE -ne 0 -or "$probe" -ne '3') { Fail 'Selected Python does not run under Git Bash.' }
$claude = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claude) { Fail 'Claude Code executable not found.' }
$versionOutput = & $claude.Source --version 2>$null
if ("$versionOutput" -notmatch '(\d+)\.(\d+)\.(\d+)') {
  Fail 'Unable to parse Claude Code version for onFailure:block support.'
}
$detectedVersion = [Version]::new([int]$Matches[1], [int]$Matches[2], [int]$Matches[3])
if ($detectedVersion -lt [Version]'2.1.295') {
  Fail 'Claude Code 2.1.295+ is required for fail-closed onFailure:block hook handling.'
}
Write-Host 'CWC preflight PASS. Hooks are advisory and can be bypassed with Bash.'
& $claude.Source @ClaudeArgs
exit $LASTEXITCODE
