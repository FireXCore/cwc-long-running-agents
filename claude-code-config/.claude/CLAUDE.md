<!-- Copyright 2026 Anthropic PBC -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Long-running project conventions (fork)

## Start
Read PROGRESS.md when present. Inspect recent commits and smoke-test existing
functionality before editing. Do not create/overwrite files without authorization.

## Scope
Work on one feature at a time; reuse existing code and preserve approved behavior.

## Proof and verification
Run real app/API/browser checks and inspect evidence. Local evidence hooks are
ADVISORY only. The builder cannot certify PASS; use an independent trusted
evaluator for a final verdict. Do not call a mocked test a real integration test.

## Handoff
Keep PROGRESS.md current with IMPLEMENTED, TESTED, VERIFIED and PENDING.

## Commits
No Stop auto-commit hook is registered. Commit, push, merge and publish only
when explicitly authorized for the task.

## Operator controls
Honor AGENT_STOP and STEER.md, but recognize they are not a security boundary.
On Windows use the checked launcher described in FORK-HARDENING.md.
