# Plan: stasis-stop-retirement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`packs/AGENTS.md`](../../../packs/AGENTS.md),
  [`packs/core/AGENTS.md`](../../../packs/core/AGENTS.md),
  [`docs/CONVENTIONS.md`](../../CONVENTIONS.md),
  [ADR-0104](../../adr/0104-light-mode-review-stops-on-divergence.md)

## Approach

Edit prose on four audiences, in dependency order, then pin the result.

The work is small per surface and the risk is entirely in scope selection: every
surface that must change sits next to one that must not, and in one case both
obligations are in the same sentence. So the inventory comes first and is
reproducible, the four edit tasks work from it rather than from a fresh search,
and the sweep task lands last because the tracked projections only converge
after self-host runs.

## Constraints

- The out-of-bounds surfaces are the spec's *Never do*.
- `packs/AGENTS.md` owns the export boundary, the version-bump file set, and the
  self-host projection rule.

## Construction tests

Two owning suites, not one.

- `packs/core/tests/pack/` — the pack-local prose assertions for the three
  `references/` files and the seed. A pack test may not read above its own pack,
  which is why the guide and web assertions cannot live here.
- `tools/` — the repository-level assertions for `guides/` and
  `web/src/content/`, alongside the existing guide linters.

Two authority statements are **already** asserted by
`packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py`
(`references/delivery-contract-lifecycle.md`'s transition-scope statement and
one `evals/evals.json` statement). AC-0005 adds cases for the others and reuses
those two rather than duplicating them.

## Surface inventory

Reproduced by, from the repository root:

```
grep -rin "stasis" \
  packs/core/.apm packs/core/seeds packs/core/DESIGN.md \
  guides web/src/content docs/CONVENTIONS.md \
  | grep -v __pycache__
```

Case-insensitive matters: a case-sensitive search misses `**Stasis.**` in
`state-schema.md` and `Stasis detection` in `loop-cohort.py`, and the first of
those is an edit target.

`.claude/skills/work-loop/` and `.agents/skills/work-loop/` mirror `.apm/` and
are excluded above because self-host regenerates them. They are in AC-0008's
sweep corpus, not in any edit task.

| # | Surface | Class | Action |
| --- | --- | --- | --- |
| 1 | `references/finding-adjudication.md` route entry | halt + Surface | rewrite — drop halt, keep Surface |
| 2 | `references/state-schema.md` stasis paragraph | halt | rewrite — drop halt and the skipped check |
| 3 | `references/delivery-contract-lifecycle.md` stop conditions | halt + refuted mechanism | rewrite — both |
| 4 | `references/state-schema.md` `finding_fingerprints` row | refuted mechanism | rewrite — the field is not a stasis detector |
| 5 | `packs/core/seeds/docs/CONVENTIONS.md` | halt **and** authority, one sentence | split — drop the pause, keep the rest |
| 6 | `docs/CONVENTIONS.md` | byte-identical twin of 5 | open — see spec *Ask first* |
| 7 | `references/delivery-contract-lifecycle.md` transition scope | authority | keep — already asserted |
| 8 | `references/delivery-contract-lifecycle.md` completion | authority | keep |
| 9 | `SKILL.md` termination | authority | keep |
| 10 | `SKILL.md` finish checklist | authority | keep |
| 11 | `evals/evals.json` amendment expectation | authority | keep — already asserted |
| 12 | `evals/evals.json` amendment rejection | authority | keep |
| 13 | `scripts/loop-cohort.py` module comment | mechanism description | no action — comment, not instruction |
| 14 | `scripts/loop-cohort.py` empty-vs-empty comment | mechanism description | no action |
| 15 | `scripts/_loop_guards.py` reset message | mechanism description | no action — byte-pinned by a golden-stream fixture |
| 16 | `hooks/pre-pr.py` docstring | wrong before this change | no action — spec *Follow-ons* |
| 17 | `guides/core/explanation/core-pack.md` loop description | published claim | rewrite |
| 18 | `guides/core/explanation/core-pack.md` numbered stasis item | published claim | rewrite |
| 19 | `guides/core/explanation/core-pack.md` failure-mode row | published claim | rewrite |
| 20 | `guides/core/explanation/core-pack.md` comparison rows and prose (four) | competitive claim | owner call — see below |
| 21 | `guides/core/explanation/token-economy.md` | published claim | rewrite |
| 22 | `guides/core/how-to/bug-fix.md` | published claim | rewrite |
| 23 | `guides/core/how-to/review-someone-elses-pr.md` | published claim | rewrite |
| 24 | `guides/README.md` flagship description | published claim | rewrite |
| 25 | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | published claim | rewrite |
| 26 | `web/src/content/packs/core.md` | public claim | rewrite |
| 27 | `guides/governance-extras/how-to/new-rfc.md` | unrelated domain | no action — RFC round caps, not this loop |

Row 5 is the one to read twice. Its single sentence says stasis *pauses for
human replanning* (a halt) and that stasis *neither completes intent nor creates
backlog work* (authority). An edit that removes the sentence violates AC-0005;
one that keeps it violates AC-0004.

## Design (LLD)

### Design decisions

**The Surface survives the halt.** ADR-0104 is Accepted and requires the signal
to be reported and Surfaced. Row 1 is the only shipped instruction to Surface
it, and the halt is in the same clause. The rewrite splits the clause rather
than deleting the row.

**The refuted mechanism is a separate claim from the halt.** Rows 3 and 4 assert
that a repeated fingerprint *detects* stasis. That is false independently of
what detection then triggers — the fingerprint carries position — so it gets its
own criterion rather than riding along with the halt removal.

**The comparison tables need an owner decision, not a default.** Two tables mark
"iteration cap and stasis detection" present for this pack and absent for two
named competitors. Retiring the stop makes half that claim false. Re-pointing it
at the retry cap keeps a true claim; withdrawing the row concedes a
differentiator. The plan does not pick; the spec's *Ask first* routes it.

**No script changes.** The signal keeps computing. Rows 13 to 15 are comments
and messages describing the mechanism, and row 15 is byte-pinned by a fixture,
so touching it breaks a golden stream for no gain.

### Failure, edge cases & resilience

The likeliest failure is an over-broad edit reaching rows 7 to 12. AC-0005 is
the guard, and it compares against pre-change text — so the baseline must be
captured before T1 edits anything, or the assertion ratifies whatever landed.

The second likeliest is a sweep that reds on the tracked projections before
self-host runs. T5 lands after T4 for that reason.

## Tasks

### T1: Capture the baseline and pin what must not move

**Depends on:** none

**Tests:**
- AC-0005 — one positive assertion per `keep` row in the inventory, against text
  captured from the current tree, reusing the two cases
  `test_contract_amendment_wave4.py` already owns rather than duplicating them.

**Approach:**
- Record the `keep` rows' current text before any edit task runs. An assertion
  written after the edits pins whatever survived rather than what should have.

**Done when:** the authority assertions are green against the unedited tree, so
they can fail in T2 and T3 if an edit reaches too far.

### T2: Retire the halt in the runtime references

**Depends on:** T1

**Tests:**
- AC-0001, AC-0002, AC-0003 — one absence and one presence assertion per file.
- AC-0009 — the refuted mechanism claim is absent from rows 3 and 4.

**Approach:**
- Work from inventory rows 1 to 4.
- Row 1 keeps its Surface. Rows 2 and 3 drop the halt and the skipped check.
  Row 4 stops calling the fingerprint a stasis detector.

**Done when:** the three reference files instruct no halt, row 1 still instructs
a Surface, and T1's authority assertions are still green.

### T3: Split the projected seed

**Depends on:** T1

**Tests:**
- AC-0004 — the pause is gone and the authority half is intact, asserted as two
  separate conditions on one sentence.

**Approach:**
- Inventory row 5. Decide row 6 (`docs/CONVENTIONS.md`) per the spec's *Ask
  first* before editing either, since they are byte-identical today and a
  one-sided edit makes them diverge silently.

**Done when:** the seed carries the authority statement and no pause, and row 6
is either edited in step or recorded as deliberately divergent.

### T4: Correct the published guides and public claims

**Depends on:** T2

**Tests:**
- AC-0006 — an absence assertion over the guide corpus, in `tools/`, because a
  pack test cannot read above its pack.
- AC-0007 — the public page and the comparison tables match the resolution the
  owner picked.

**Approach:**
- Inventory rows 17 to 26. Row 20 needs the owner's answer first.
- Depends on T2 so the guides describe what the references actually say.

**Done when:** no guide asserts a halt, and the comparison tables carry a claim
the tree supports.

### T5: Pin the retirement, then version and project

**Depends on:** T3, T4

**Tests:**
- AC-0008 — the parametrized sweep, one case per retired phrasing, over an
  explicit corpus path list that includes the tracked projections, asserting
  each path exists before walking it.

**Approach:**
- State the retired-phrase list and the corpus path list here in the plan; the
  criterion cites this list rather than naming phrases itself.
- Bump both pack manifests by one patch above whatever they hold at execution
  time and add the changelog entry in the same commit.
- Run `FORCE=1 make build-self` before the sweep, not after: the projections
  carry the old prose until it does.

**Done when:** the sweep is green after self-host, `make lint-ruff lint-mypy` is
clean, and `agentbundle catalogue verify --root .` returns ok.

## Rollout

- **Delivery:** prose only; no runtime behaviour changes because nothing branched
  on the disposition. Reversible by reverting the commit.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** self-host runs after the version bump and before
  the sweep.

## Risks

- **An over-broad edit deletes a true statement.** Six authority statements sit
  adjacent to the halts, and one shares a sentence with one. T1 exists to make
  that failure red rather than silent.
- **The seed and its repository twin diverge.** They are byte-identical today
  and nothing asserts that they stay so. T3 forces the decision rather than
  letting a one-sided edit make it.
- **The competitive claim is resolved by default.** If nobody answers row 20,
  the likeliest outcome is that the rows are left alone and the published
  comparison becomes false. The spec routes it to *Ask first* so silence blocks
  rather than defaults.

## Changelog

- 2026-09-15 — Drafted. Cut out of `review-recurrence-family-key` after a third
  adversarial round, where every blocker sat in the retirement half rather than
  in the key derivation. Carries that review's findings forward: the corrected
  inventory (27 rows, not 8), the seed's dual-purpose clause, the corrected
  authority-statement population, the Surface disposition ADR-0104 requires, and
  the projection ordering the sweep depends on.
