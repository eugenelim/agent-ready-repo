# Adversarial review — round 2 (spec mode), and the decision to stop

Round 2 was dispatched with an origin-tagging requirement: every finding had to
declare whether it was **(a)** a defect round 1 missed, **(b)** a sustained
round-1 finding still unrepaired, or **(c)** a new defect introduced *by* the
round-1 repairs.

**Result: 3 Blockers, 9 Concerns, 3 Nits. 8 of 15 are origin (c).**

The reviewer's own conclusion: *"The revision is oscillating rather than
converging... I would stop and replan rather than run a round 3."*

That matches this repository's recorded practice — a review whose findings come
predominantly from the previous round's fixes has stopped converging, and
another round calibrates to the last defect rather than the artifact. **The loop
is stopped here. Round 3 was not run.**

## Controller verification of the two decisive claims

Both re-derived independently against the committed 76-topic store before
accepting the stop recommendation.

**Blocker 1 — AC 4's monotonicity is inverted.** Under ancestor-only matching,
narrowing a query *adds* matching ancestors:

```
packs                                  26
packs/core                             26  flat
packs/core/.apm                        26  flat
packs/core/.apm/skills                 27  INCREASES
packs/core/.apm/skills/work-loop       32  INCREASES
```

AC 4 asserts the count is non-**increasing** as the query narrows. Measured, it
is non-**decreasing**. The clause was true under round 1's bidirectional design;
flipping to ancestor-only inverted it and the AC was not updated. T2's
monotonicity test would fail on the real corpus. **Confirmed.**

**Concern 4 — a unit error in the residual argument.** `25` counts scope
*atoms* reducing to an empty base, not topics:

```
atoms reducing to empty base : 25   <- written into the spec as "25 topics"
topics with ANY empty base   : 17
topics with ONLY empty bases : 14
```

This figure is load-bearing: it is the arithmetic used to argue the 7-topic
starvation is a corpus-granularity property rather than a matcher defect.
**Confirmed.**

## Root cause

The reviewer traced Blockers 1 and 2 and Concerns 5 and 12 to a single
unsettled choice: **is AC 1 a match-level or a selection-level contract?**

Round 1 stated it at selection level, which measurement showed is unsatisfiable
(7 topics starved; 20 topics tie at base `tools` against a 12-body envelope).
Round 2 restated it at match level, which:

- hollowed out AC 1's second clause into something unfailable (Blocker 2), and
- removed the exact ground on which the adjudicator had refuted round-1
  finding 4, reviving it (Concern 5).

Neither level is right. Corpus coverage — "every topic is reachable" — is a
**curation** metric, not a **retrieval** contract. A retrieval contract is about
what a given query gets back. Restating it that way dissolves all four findings
rather than moving the defect around, and is the replan this spec needs.

## Findings not yet repaired, carried into the replan

Independent of the AC 1 question:

- **Blocker 3 (a)** — six TDD tasks carry no compilable red stub and three
  goal-based tasks carry no `no stub (mode)` line, required by
  `docs/CONVENTIONS.md:543-552`. This is the mechanism that would have caught
  Blocker 1 at PLAN.
- **Concern 6 (b)** — AC 11 and T7 are before/after comparisons with no
  committed baseline artifact; round 1 raised this and the repair moved the
  wording without adding a record location.
- **Concern 7 (c)** — T4 commits a golden fixture under `tests/` that no listed
  test module reads, while declaring goal-based mode.
- **Concern 8 (c)** — the new `tools/repair-legacy-topic-scopes.py` violates
  this spec's own `Never do: add a new module` Boundary, and `tools/AGENTS.md`
  requires pure-stdlib scripts while the task mandates importing pack runtime
  code. `project_knowledge.py:683` already exposes `--migrate-legacy`.
- **Concern 9 (a)** — T9's `make build-self` refuses on a dirty tree
  (`self_host.py:1283`); `packs/AGENTS.local.md:28` prescribes `FORCE=1`.
- **Concern 10 (a)** — AC 12 has no implementing task and no Testing Strategy
  row.
- **Concern 11 (b)** — figures are still duplicated across spec and plan,
  including the one Concern 4 shows is now wrong in both places at once.
- **Nit 15 (a)** — the competency-facet sort key is constant over the filtered
  set, so specificity is the effective primary key; the plan's description
  implies otherwise.

## Findings the reviewer resolved in the artifact's favour

- **Nit 13** — the reviewer tried to construct a counterexample to the plan's
  claim that ancestor-only eliminates the specificity-vs-distance pathology,
  and could not. Under ancestor-only every matching base is a prefix of the
  query, so depth *is* distance. The claim stands; only its framing as an
  unmitigated risk was wrong.
- The reviewer independently verified a store-independent query set (all 6,880
  git-tracked paths plus parents) also yields 76 of 76, so the intended fix is
  sound — it is the *test's* query derivation that is weak, not the matcher.

## Status

`spec.md` and `plan.md` remain **Draft**. No implementation was started, no
approval gate was fired, and no `loop-engine`/`loop-cohort` state was
initialised. The measured defect this spec addresses is real and unchanged: the
current matcher reaches 21 of 76 topics across 32 candidate concrete queries.
