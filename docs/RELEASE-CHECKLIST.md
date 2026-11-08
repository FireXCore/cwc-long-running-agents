# Release readiness checklist (FireXCore fork)

This file is a **checklist**, not a published release or a production-security certification.

- [ ] Main branch includes the reviewed README, up-to-date QA procedure, and original upstream attribution.
- [ ] CI passes on Windows and Linux, including Python 3.9 and 3.12.
- [ ] Run fresh live Claude Code tests on a **disposable** Windows workspace, recording version and exact commit SHA.
- [ ] Confirm the kill switch, steering, evidence lifecycle, TTL and concurrent consumption behavior on the release commit.
- [ ] Validate deliberate negative cases: missing Git Bash, fake Python, absent scripts, broken settings and unsupported Claude versions.
- [ ] Confirm builder-authored evidence, forged database rows, and Bash writes remain explicitly documented as bypasses.
- [ ] Do not claim a trusted PASS without an independent evaluator outside the builder's writable workspace.
- [ ] Preserve Apache-2.0 upstream attribution and check links.
- [ ] Choose a fresh version tag; never overwrite an existing tag or Release.
- [ ] Publish **pre-release** notes with platform requirements, limits, test SHA and CI links; never label as a production security product.

Historical implementation and live acceptance: [PR #1](https://github.com/FireXCore/cwc-long-running-agents/pull/1).
