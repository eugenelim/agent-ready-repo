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
surface that must change sits next to one that must not, and in two cases both
obligations share a sentence. So the inventory comes first and carries its own
method, the edit tasks work from it rather than from a fresh search, and the
sweep lands last because the tracked projections only converge after self-host.

## Constraints

- The out-of-bounds surfaces are the spec's *Never do*.
- `packs/AGENTS.md` owns the export boundary, the version-bump file set, and the
  self-host projection rule.

## Construction tests

Two owning suites, and one registration step that is easy to miss.

- **`packs/core/tests/pack/`** — the pack-local assertions for the three
  `references/` files, the seed, and the authority statements.
- **`tools/test_stasis_retirement_claims.py`** — the repository-level assertions
  for `guides/`, `guides/README.md`, and `web/src/content/`. They cannot live in
  the pack suite: a pack test may not read above its own pack.

**The new `tools/` suite must be added to the `tools/test_*.py` enumeration in
`Makefile`'s repo-test target.** `tools/lint-pack-test-boundary.py` fails any
suite that no runner names and that is not in its `_NO_RUNNER` table, so an
unregistered file both fails the lint and executes nowhere. T4 owns that edit.

**What runs in the always-on PR chain, stated plainly.** `build-check` runs no
pytest, and the full suite is dispatch-only. So AC-0007, AC-0008 and AC-0009 are
**dispatch-only evidence** unless the runner line they join is itself in the
always-run chain — T4's first step is to determine which and record the answer
here. Do not let them read as gate-backed when they are not.

## Surface inventory

### Method, and what it does not prove

The halt is a **concept** — the loop stops when findings repeat — and no single
token finds a concept. Three earlier attempts each missed a different class: one
searched only `packs/core/.apm/`; one searched case-sensitively and missed
`**Stasis.**` in its own target file; one searched the token `stasis` and missed
two halt claims that never use the word, one of them on the public pack page.

Reproduced from the repository root:

```
grep -rinE "stasis|matches_previous_round|repeated finding|same findings|findings[^.]{0,30}repeat|repeat[^.]{0,20}finding" \
  packs/core/.apm packs/core/seeds packs/core/DESIGN.md \
  guides web/src/content docs/CONVENTIONS.md tools/hooks \
  | grep -v __pycache__
```

41 occurrences at the revision this plan was written against.

**Explicit residual.** This is a vocabulary search, not a proof of completeness.
A surface stating the halt in words none of these patterns match is not in this
table and will not be found by re-running the command. The table is a judgement
recorded with its method, and the method's limit is named here rather than
implied away.

### Classes

**halt** instructs stopping, skipping a check, or replanning. **Surface**
instructs reporting to the human. **authority** says stasis does not by itself
complete intent, create follow-on work, or authorise an amendment. **mechanism**
describes how the signal is computed. **claim** is published prose asserting the
behaviour to a reader.

| # | File | Line | Class | Action |
| --- | --- | ---: | --- | --- |
| 1 | `references/finding-adjudication.md` | 243 | halt + Surface | rewrite — drop halt, keep Surface |
| 2 | `references/state-schema.md` | 70 | mechanism | rewrite — not a stasis detector |
| 3 | `references/state-schema.md` | 188 | mechanism | rewrite — not a stasis detector |
| 4 | `references/state-schema.md` | 189 | halt + Surface | rewrite — drop halt and skipped check, keep Surface |
| 5 | `references/delivery-contract-lifecycle.md` | 129 | mechanism | rewrite — a repeated fingerprint does not detect it |
| 6 | `references/delivery-contract-lifecycle.md` | 130 | halt | rewrite — drop the immediate replan |
| 7 | `packs/core/seeds/docs/CONVENTIONS.md` | 1093 | halt **and** authority | split — drop the pause, keep the rest |
| 8 | `docs/CONVENTIONS.md` | 1093 | halt **and** authority | byte-identical twin of 7; see spec *Ask first* |
| 9 | `references/delivery-contract-lifecycle.md` | 63 | authority | keep — asserted today |
| 10 | `references/delivery-contract-lifecycle.md` | 136 | authority | keep — **not** asserted today |
| 11 | `SKILL.md` | 759 | authority | keep — **not** asserted today |
| 12 | `SKILL.md` | 780 | authority | keep — **not** asserted today |
| 13 | `evals/evals.json` | 581 | authority | keep — **not** asserted today; see below |
| 14 | `evals/evals.json` | 588 | authority | keep — **not** asserted today |
| 15 | `scripts/loop-cohort.py` | 81 | mechanism | no action — comment |
| 16 | `scripts/loop-cohort.py` | 1730 | mechanism | no action — the `invalid` payload key |
| 17 | `scripts/loop-cohort.py` | 1940 | mechanism | no action — docstring |
| 18 | `scripts/loop-cohort.py` | 1995 | mechanism | no action — comment |
| 19 | `scripts/loop-cohort.py` | 2001 | mechanism | no action — the classified payload key |
| 20 | `scripts/loop-cohort.py` | 2013 | mechanism | no action — the print line |
| 21 | `scripts/_loop_guards.py` | 734 | mechanism | no action — byte-pinned by a golden-stream fixture |
| 22 | `packs/core/.apm/hooks/pre-pr.py` | 18 | wrong before this change | no action — spec *Follow-ons* |
| 23 | `tools/hooks/pre-pr.py` | 18 | wrong before this change | no action — spec *Follow-ons* |
| 24 | `guides/core/explanation/core-pack.md` | 35 | claim — halt, no `stasis` token | rewrite |
| 25 | `guides/core/explanation/core-pack.md` | 66 | claim — capability | rewrite |
| 26 | `guides/core/explanation/core-pack.md` | 121 | claim — halt | rewrite |
| 27 | `guides/core/explanation/core-pack.md` | 135 | claim — halt | rewrite |
| 28 | `guides/core/explanation/core-pack.md` | 154 | competitive claim | owner call |
| 29 | `guides/core/explanation/core-pack.md` | 159 | competitive claim | owner call |
| 30 | `guides/core/explanation/core-pack.md` | 170 | competitive claim | owner call |
| 31 | `guides/core/explanation/core-pack.md` | 175 | competitive claim | owner call |
| 32 | `guides/core/explanation/token-economy.md` | 79 | claim — halt | rewrite |
| 33 | `guides/core/how-to/bug-fix.md` | 107 | claim — capability | rewrite |
| 34 | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 123 | claim — capability | rewrite |
| 35 | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 132 | mechanism | rewrite |
| 36 | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 133 | claim — halt | rewrite |
| 37 | `guides/core/how-to/review-someone-elses-pr.md` | 33 | claim — capability | rewrite |
| 38 | `guides/README.md` | 188 | claim — capability | rewrite |
| 39 | `web/src/content/packs/core.md` | 19 | claim — capability | rewrite |
| 40 | `web/src/content/packs/core.md` | 21 | claim — halt, no `stasis` token | rewrite |
| 41 | `guides/governance-extras/how-to/new-rfc.md` | 131 | unrelated domain | no action — RFC round caps |

**Row 7 is the one to read twice.** Its single sentence says stasis *pauses for
human replanning* (a halt) and that retry caps and stasis *neither complete
intent nor create backlog work* (authority). Deleting the sentence fails AC-0006;
keeping it fails AC-0004.

**Rows 1 and 4 are both Surfaces.** An earlier draft claimed row 1 was the only
one. It is not, and an edit satisfying a halt-only reading of row 4 would delete
a disposition ADR-0104 requires.

### Which `keep` rows an existing suite already covers

Only **row 9**. `packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py`
asserts `"session end, retry cap, stasis, or model judgment never invokes"`,
which contains the distinguishing token.

Row 13 was previously recorded as covered and is not. That same suite asserts
`"stable owner-authority reference"`, `"ordinary plan-locked edge"` and
`"cannot invoke it automatically"` against `evals.json:581` — none contains
`stasis`, so deleting `stasis,` from that enumeration leaves the suite green.

Rows 10, 11, 12, 13 and 14 need new cases. **The rule:** a reuse claim holds only
when the existing assertion's literal text contains the token whose deletion the
criterion is guarding against. Check each claim against the assertion's text,
not against the file it reads.

### Retired phrases — AC-0010's literal list

Whitespace-normalized, case-insensitive:

- `do not start another round`
- `stops immediately for human replanning`
- `pause for human replanning`
- `surface immediately; do not run`
- `same findings twice = stop`
- `the loop stops and surfaces`
- `stops a third pass`
- `refuses to self-certify past a red gate or a repeated finding`
- `it stops at plan approval, unresolved boundaries, repeated findings`

### Sweep corpus — AC-0010's literal path list

Each asserted to exist before it is walked:

- `packs/core/.apm/skills/work-loop/SKILL.md`
- `packs/core/.apm/skills/work-loop/references/*.md`
- `packs/core/.apm/skills/work-loop/evals/evals.json`
- `packs/core/seeds/docs/CONVENTIONS.md`
- `packs/core/DESIGN.md`
- `.claude/skills/work-loop/` and `.agents/skills/work-loop/` — tracked
  projections carrying the old prose until self-host runs, which is why T5
  projects before it sweeps
- `guides/core/`, `guides/README.md`
- `web/src/content/packs/core.md`

## Design (LLD)

### Design decisions

**Two Surfaces survive the halt.** ADR-0104 is Accepted and requires the signal
to be reported and Surfaced. Rows 1 and 4 each state a Surface in the same
sentence as a halt. Both rewrites split the sentence rather than deleting it.

**The refuted mechanism is a separate claim from the halt.** Rows 2, 3, 5 and 35
assert that a repeated fingerprint *detects* stasis. That is false independently
of what detection then triggers, so it gets its own criterion rather than riding
along with the halt removal.

**The baseline for AC-0006 lives in the test source.** An assertion that reads
the `keep` rows from the tree at run time compares a file to itself and can
never fail. The existing precedent in `test_contract_amendment_wave4.py` holds
literal phrases and compares them as normalized substrings; AC-0006 follows that
form rather than whole-statement equality, which is not assertable across the
line break in row 9.

**The comparison tables need an owner decision, not a default.** Rows 28 to 31
mark "iteration cap and stasis detection" present for this pack and absent for
two named competitors. Retiring the stop makes half that claim false.
Re-pointing it at the retry cap keeps a true claim; withdrawing the rows concedes
a differentiator. The plan does not pick; the spec's *Ask first* routes it, so
silence blocks rather than shipping a false comparison.

**No script changes.** Rows 15 to 21 are comments, docstrings, payload keys and
a message. Row 21 is byte-pinned by a golden-stream fixture, so touching it
breaks a stream for no gain.

### Failure, edge cases & resilience

The likeliest failure is an over-broad edit reaching rows 9 to 14. AC-0006 is the
guard, and its literals must be captured before T2 and T3 edit anything.

The second is a sweep that reds on the tracked projections before self-host runs.
T5 sequences around it.

The third is the new `tools/` suite never executing. T4 registers it and records
which chain runs it.

## Tasks

### T1: Pin what must not move

**Depends on:** none

**Tests:**
- AC-0006 — one normalized-substring assertion per `keep` row, against literals
  held in the test source. Reuse row 9's existing case; add cases for rows 10,
  11, 12, 13 and 14. Verify each reuse claim against the existing assertion's
  text before relying on it.

**Approach:**
- Capture the literals from the current tree before any edit task runs.

**Done when:** the authority assertions are green against the unedited tree, so
they can fail in T2 and T3 if an edit reaches too far.

### T2: Retire the halt in the runtime references

**Depends on:** T1

**Tests:**
- AC-0001, AC-0002, AC-0003 — one absence and one presence assertion per file.
  The presence half on rows 1 and 4 is the Surface.
- AC-0011 — the refuted mechanism claim is absent from rows 2, 3 and 5.

**Approach:**
- Work inventory rows 1 to 6.

**Done when:** the three reference files instruct no halt, both Surfaces remain,
and T1's assertions are still green.

### T3: Split the projected seed and settle its twin

**Depends on:** T1

**Tests:**
- AC-0004 — the pause is gone and the authority half is intact, asserted as two
  conditions on one sentence.
- AC-0005 — the twin carries the same split, or a divergence record exists.

**Approach:**
- Inventory rows 7 and 8. Get the *Ask first* answer before editing either; they
  are byte-identical today and a one-sided edit makes them diverge silently.
- If they diverge deliberately, the record goes in `docs/CONVENTIONS.md` beside
  the clause, since that is the surface a reader lands on.

**Done when:** the seed carries the authority statement and no pause, and the
twin is either edited in step or carries the divergence record.

### T4: Correct the published guides and public claims

**Depends on:** T2

**Tests:**
- AC-0007, AC-0008 — absence and content assertions in
  `tools/test_stasis_retirement_claims.py`.
- AC-0009 — the comparison tables match the owner's resolution.

**Approach:**
- Determine which Makefile runner line the new suite joins and whether that line
  runs in the always-on PR chain. Record the answer in *Construction tests*
  above, replacing the open question there.
- Register the suite in that line. Without it the boundary lint fails and
  nothing executes the file.
- Work inventory rows 24 to 27 and 32 to 40. Rows 28 to 31 need the owner's
  answer first.

**Done when:** no guide asserts a halt, the public page matches the tree, the
comparison tables carry a supported claim, and the new suite is registered and
observed to run.

### T5: Pin the retirement, then version and project

**Depends on:** T3, T4

**Tests:**
- AC-0010 — the parametrized sweep over the two literal lists above, one case per
  retired phrase, asserting each corpus path exists before walking it.

**Approach:**
- Bump both pack manifests by one patch above whatever they hold at execution
  time and add the changelog entry in the same commit.
- Run `FORCE=1 make build-self` **before** the sweep. The projections carry the
  old prose until it does.

**Done when:** the sweep is green after self-host, `make lint-ruff lint-mypy` is
clean, and `agentbundle catalogue verify --root .` returns ok.

## Rollout

- **Delivery:** prose only; no runtime behaviour changes because nothing branched
  on the disposition. Reversible by reverting the commit.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** self-host runs after the version bump and before the
  sweep.

## Risks

- **An over-broad edit deletes a true statement.** Six authority statements sit
  adjacent to the halts and one shares a sentence with one. Five of the six are
  unasserted today. T1 exists to make that failure red rather than silent.
- **A Surface disposition is deleted with its halt.** Two rows carry both in one
  sentence, and ADR-0104 is frozen, so the repair for losing them is a
  superseding ADR rather than a spec edit.
- **The seed and its twin diverge silently.** Byte-identical today with nothing
  asserting it. AC-0005 forces the decision either way.
- **The competitive claim resolves by default.** If nobody answers rows 28 to 31,
  the likeliest outcome is that they are left alone and the published comparison
  becomes false.
- **The inventory is incomplete in a way no re-run finds.** Named in *Method*
  above. Three attempts have each missed a different class; a fourth class is
  possible and no command in this plan would surface it.

## Changelog

- 2026-09-15 — Drafted, cut out of `review-recurrence-family-key` after a third
  adversarial round put every blocker in the retirement half.
- 2026-09-15 — Repaired after this spec's own first round. The inventory moved
  from a token search to a vocabulary search and from 27 rows to 41, after the
  token search was shown to miss two halt claims that never use the word
  including one on the public pack page; a second Surface disposition was found
  and the "only shipped Surface instruction" claim corrected in two places; one
  "already asserted" reuse claim was refuted against the assertion's own text;
  the retired-phrase and sweep-corpus lists became literal; the `tools/` suite
  gained a registration step and an honest statement that it may be dispatch-only
  evidence; and the eval-harness obligation got a recorded disposition.
