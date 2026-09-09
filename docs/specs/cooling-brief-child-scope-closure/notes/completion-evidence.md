# Completion evidence

Every claim here was measured, not recalled. The scripts behind the counts live
in the session scratchpad and re-run from the repository root.

## Contract

| | |
| --- | --- |
| Criteria | 27, contiguous |
| Evidenced | **27/27** — 19 named by a suite case docstring, 12 checked by a mechanical audit, 4 both ways, none uncovered |
| Suite | `tests/roster/test_cooling_brief_child_scope_closure.py`, 22 cases |
| Mutations | 12 across three passes, **12 killed** |
| Durable outputs | **6/6** closeout conditions met |

## What the delivery does

A cooled spec entry's `source.parent` answers three ways instead of two. A value
resolving to a registered brief attributes the child; a declared empty value
attributes nothing and releases every dependant; an absent key or a value naming
no registered brief is unestablished scope, which names the entry in a
`cooled_child_scope_unknown` finding and refuses local `kind = "brief"`
dependencies until someone declares an answer.

Resolution is by entry **kind**, over canonical and legacy memberships, in
whichever collection the brief is registered. That is AC27, and it exists
because three independent reviewers each found the original collection-keyed
predicate wrong from a different direction.

## Verification

| Gate | Result | Commit |
| --- | --- | --- |
| `build-check` (CI) | success | `8a5611ffb` |
| `test-roster` (CI) | success | `8a5611ffb` |
| `test-corpus` (CI) | dispatched | `8a5611ffb` |
| ruff, mypy, spec-status, 8 further lints | pass | local |
| Projections | 9/9 byte-equal | local |

## Residuals, all recorded

Three open follow-ons in `notes/follow-ons.md`: the closeout-time writer for the
trusted-not-verified declaration, the two AC17-pinned test names that now
contradict their bodies, and an interrupted suite's collectable residue. One
follow-on was closed inside this delivery at the owner's direction.

## What this delivery got wrong, and what caught it

Ten review rounds. The counts that matter:

- **Five review blockers on the implementation**, three of them the same
  predicate seen from three directions. One kind-based line closed all three.
- **Adjudication rejected three proposed fixes as harmful**, including one that
  would have made a fail-open reachable in valid workspace state, and refuted a
  finding whose "defect" was the contract's required behaviour.
- **Three CI gates failed after the plan's own Done-when passed locally** —
  ruff, the web reprojection, mypy. None is named in the plan; the plan named a
  `make` target without recording that its chain includes eleven lint steps a
  targeted pytest never reaches.
- **Four claims the delivery made about itself were false**, and a later round
  found three more inside the corrections written for the first four. The worst
  was a fabricated measurement — "disagree on 2 of 15 briefs" — where the real
  answer is zero disagreements across 16 briefs.

The through-line is not carelessness in any single edit. It is that a count is
only as good as the pattern that produced it, and a gate set is only as good as
the enumeration behind it. Both are now derived rather than recalled: the
citation claim carries its denominator, and the gate list was read out of the
workflow file.
