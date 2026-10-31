# SPDX-License-Identifier: Apache-2.0
# Start from a disposable project root containing .claude/settings.json.
# No param() block: an advanced script would consume -p, --model, --verbose and
# --debug as PowerShell parameters instead of forwarding them to Claude Code.
$ClaudeArgs = $args
$ErrorActionPreference = 'Stop'
function Fail([string]$Message) {
  # Write-Error would throw under ErrorActionPreference=Stop and skip exit 2.
  [Console]::Error.WriteLine("CWC preflight: $Message")
  exit 2
}
if (-not (Test-Path -LiteralPath '.claude/settings.json' -PathType Leaf)) {
  Fail 'No .claude/settings.json in the working directory.'
}
# The file existing is not enough: every hook must pin shell=bash and every
# PreToolUse hook must fail closed, and nothing may disable hooks.
try { $settings = Get-Content -Raw -LiteralPath '.claude/settings.json' | ConvertFrom-Json }
catch { Fail '.claude/settings.json is not valid JSON.' }
$pre = @($settings.hooks.PreToolUse | ForEach-Object { $_.hooks } | Where-Object { $_ })
$all = @($settings.hooks.PSObject.Properties | ForEach-Object { $_.Value } | ForEach-Object { $_.hooks } | Where-Object { $_ })
if ($pre.Count -eq 0 -or ($pre | Where-Object { $_.onFailure -ne 'block' }) -or
    ($all | Where-Object { $_.shell -ne 'bash' })) {
  Fail 'Hooks must set shell=bash, and PreToolUse hooks onFailure=block.'
}
foreach ($file in @('.claude/settings.json', '.claude/settings.local.json')) {
  if (-not (Test-Path -LiteralPath $file)) { continue }
  # Parsed, so JSON-escaped key spellings are caught too.
  try { $parsed = Get-Content -Raw -LiteralPath $file | ConvertFrom-Json }
  catch { Fail "$file is not valid JSON." }
  if ($parsed.disableAllHooks -eq $true) { Fail "$file sets disableAllHooks." }
}
$candidates = @()
if ($env:CLAUDE_CODE_GIT_BASH_PATH) { $candidates += $env:CLAUDE_CODE_GIT_BASH_PATH }
$candidates += @("$env:ProgramFiles\Git\bin\bash.exe",
                 "$env:ProgramFiles\Git\usr\bin\bash.exe")
# Git for Windows installed elsewhere: bin\bash.exe is in the install root above
# cmd\git.exe or mingw64\bin\git.exe.
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if ($git) {
  $dir = Split-Path $git.Source
  for ($i = 0; $i -lt 3 -and $dir; $i++) {
    $candidates += Join-Path $dir 'bin\bash.exe'
    $dir = Split-Path $dir
  }
}
$bash = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
if (-not $bash) { Fail 'Git Bash missing. Windows Claude Code can silently skip shell hooks.' }
# Windows PowerShell 5.1 drops embedded double quotes from native arguments and,
# under ErrorActionPreference=Stop, aborts on native stderr; probes avoid both.
function Invoke-Probe([string]$Exe, [string[]]$ProbeArgs) {
  $ErrorActionPreference = 'Continue'
  $out = & $Exe @ProbeArgs 2>$null
  if ($LASTEXITCODE -ne 0) { return $null }
  return "$out".Trim()
}
$probe = Invoke-Probe $bash @('-c', 'printf CWC_BASH_OK')
if ($probe -ne 'CWC_BASH_OK') { Fail 'Git Bash execution failed.' }
$pyProbe = 'import sys,sqlite3; print(sys.executable if sys.version_info >= (3,9) else str())'
$python = $null
foreach ($name in @('python.exe','py.exe')) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { continue }
  if ($name -eq 'py.exe') {
    $found = Invoke-Probe $cmd.Source @('-3', '-c', $pyProbe)
  } else {
    $found = Invoke-Probe $cmd.Source @('-c', $pyProbe)
  }
  if ($found -and (Test-Path -LiteralPath $found -PathType Leaf)) {
    $python = $found
    break
  }
}
if (-not $python) { Fail 'Real Python 3.9+ with sqlite3 not found (Store alias rejected).' }
$env:CLAUDE_CODE_GIT_BASH_PATH = $bash
$env:CWC_PYTHON_BIN = $python.Replace('\','/')
$env:CWC_PY_PROBE = 'import sys; print(sys.version_info.major)'
# IFS= and set -f keep the unquoted expansions whole (the path may contain spaces).
$probe = Invoke-Probe $bash @('-c', 'set -f; IFS=; exec $CWC_PYTHON_BIN -c $CWC_PY_PROBE')
if ($probe -ne '3') { Fail 'Selected Python does not run under Git Bash.' }
$claude = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claude) { Fail 'Claude Code executable not found.' }
$versionOutput = Invoke-Probe $claude.Source @('--version')
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
