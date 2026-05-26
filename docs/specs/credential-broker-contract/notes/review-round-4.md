# Round 4 adversarial review — credential-broker-contract spec + plan

**Reviewer:** adversarial-reviewer (subagent)
**Date:** 2026-05-26
**Verdict:** Not clean — 0 Blockers, 1 Concern, 0 Nits.

## Concerns

**1. Header `Amends` clause contradicts AC45.** `spec.md:6`. Header still says "two new primitive classes `shared-libs/` and `adapter-root-bins/` named in conformance suite" — AC45 round-2 revision pinned the amendment to a single Changelog bullet with no conformance addition. Fix: rephrase header amendment description.
