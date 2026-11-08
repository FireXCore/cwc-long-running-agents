# External sharing kit — technical, not promotional spam

The content below is ready to adapt for developer communities, technical blogs or social media. **Not published by this file.** Follow each platform's self-promotion rules and disclose that you maintain the fork.

## Short developer announcement

**Title:** Windows Claude Code hooks: a real fail-open case, its cause, and a reproducible fix

I found a Windows case where a registered Claude Code `PreToolUse` hook did not stop a Write, even with `AGENT_STOP` present. Git Bash was missing; the `.sh` command was routed through PowerShell, exited 0 without a usable hook decision, and `onFailure: block` never triggered.

I documented the live reproduction and the practical fix (explicit `shell: bash`, `onFailure: block`, and a Windows preflight launcher) in an independent fork of Anthropic's educational long-running agents example. There's also a self-contained Python demo, CI on Windows/Linux, and detailed limitations.

The hooks are advisory, **not a security boundary**; shell access and builder-authored evidence can still bypass local proof gates.

**Case study:** https://github.com/FireXCore/cwc-long-running-agents/blob/main/docs/WINDOWS-HOOK-CASE-STUDY.md

**Repository:** https://github.com/FireXCore/cwc-long-running-agents

## Short social post

A registered Claude Code hook isn't necessarily an effective hook. On one Windows setup, missing Git Bash led to a `.sh` hook exiting successfully under a PowerShell fallback—and `AGENT_STOP` failed to stop a Write.

Repro, fix, Windows/Linux tests and an honest list of bypasses:

https://github.com/FireXCore/cwc-long-running-agents/blob/main/docs/WINDOWS-HOOK-CASE-STUDY.md

Independent Anthropic fork. Not a security sandbox.

## Target audiences

- Claude Code users debugging hooks on Windows
- maintainers of long-running AI coding-agent harnesses
- developers building honest regression tests around `PreToolUse` and `PostToolUse`
- projects that require independent evaluation rather than agent self-certification

## Verification checklist before posting

- Link directly to the publicly available case study and confirmed CI runs.
- Do not imply the fork is merged into, approved by or operated by Anthropic.
- Do not claim proof authenticity or production security.
- Do not claim publication, installs, adoption, or performance numbers without evidence.
- Do not repost into unrelated issues or other maintainers' repositories.
