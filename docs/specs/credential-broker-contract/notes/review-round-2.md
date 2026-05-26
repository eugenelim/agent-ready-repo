# Round 2 adversarial review — credential-broker-contract spec + plan

**Reviewer:** adversarial-reviewer (subagent)
**Date:** 2026-05-26
**Verdict:** Not clean — 5 Blockers, 6 Concerns, 3 Nits.

## Blockers

**1. T5's byte-equivalence allow-list cites a non-existent delta.** `docs/specs/credential-broker-contract/plan.md:163,178`. Helpers contain no `agentbundle:*` literal — namespace is caller-supplied. Fix: rewrite to filename-rename only.

**2. Plan T1 still mandates pack.schema.json edit.** `docs/specs/credential-broker-contract/plan.md:95`. Contradicts round-1 B1. Fix: drop pack.schema.json reference; target lint-agent-artifacts.py only.

**3. Broker Tier-2 byte-equivalence has no AC.** `spec.md:130-138`, `plan.md:163`. Fix: add AC9b under Broker surface.

**4. AC3 enum source contradicts existing inline pattern without justification.** `spec.md:110`. `ALLOWED_PRIMITIVE_CLASSES` is inline at `lint-agent-artifacts.py:127`, not in `scope.py`. Fix: pick inline pattern OR relocate both.

**5. AC45 cites sections of distribution-adapters/spec.md that do not exist.** `spec.md:205-209`. The spec has a Changelog with per-bump bullets, no "version table section" or "conformance suite section". Fix: rewrite to a single Changelog bullet; drop conformance-suite addition.

## Concerns

**6. AC34 same-PR escape weakens separation gate to manual review.** `spec.md:183`. Fix: forbid same-PR; require distinct PRs.

**7. Boundaries § conflates Don't-block prose with stderr-message strings.** `spec.md:38`. Two different surfaces. Fix: split into two clauses.

**8. Loader's `EnvParseError` not addressed in AC6 allow-list.** `spec.md:119-124`, `loader.py:56`. Fix: clarify it carries over by byte-equality.

**9. Assumptions "47 lines" wrong.** `spec.md:223`. `credentials.py` is 26 lines. Fix: correct to 26.

**10. T15 test cleanup ambiguous on which files.** `plan.md:379`. Fix: enumerate per-file disposition.

**11. AC42 "## Shipped band" doesn't exist.** `spec.md:197`. Fix: rephrase to in-place heading-suffix change.

## Nits

**12. AC44 MM-DD lacks substitution command.** `spec.md:201,203`. Fix: pin `git log -1 --format=%cs`.

**13. AC42 cites apm-install-route-parity AC17 shape without inlining row.** `spec.md:197`. Fix: inline row shape.

**14. T9 four-file divergence rationale not in AC27.** `plan.md:259`, `spec.md:167-173`. Fix: add parenthetical to AC27.
