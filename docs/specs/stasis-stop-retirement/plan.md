# Plan: stasis-stop-retirement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`packs/AGENTS.md`](../../../packs/AGENTS.md),
  [`packs/core/AGENTS.md`](../../../packs/core/AGENTS.md),
  [ADR-0104](../../adr/0104-light-mode-review-stops-on-divergence.md)

## Approach

Delete a halt from the surfaces that state it, in four tasks, then pin it out.

Each task names its own surfaces. An earlier draft kept a numbered inventory that
the criteria, the tasks, the testing strategy and the risks all cited by row
number; two review rounds then spent most of their findings on pointers that had
gone stale rather than on the work. Surfaces live inside the task that edits
them now, and nothing is addressed by number.

## Constraints

- The out-of-bounds surfaces are the spec's *Never do*.
- `packs/AGENTS.md` owns the export boundary, the version-bump file set, and the
  self-host projection rule.
- **Name the interpreter for any `agentbundle` CLI gate.** The editable install
  is shared across worktrees and points at whichever claimed it last; at the time
  of writing that is not this one, so a bare `agentbundle …` returns a verdict
  about another tree. Check before trusting a green:
  `python3 -c "import agentbundle, os; print(os.path.dirname(agentbundle.__file__))"`.
  Repo-local scripts — ruff, mypy, `lint-spec-status.py`, the alignment lint —
  are unaffected.

## How to classify a surface

Four classes, and the distinction is what a clause **obliges**, never whether it
contains the word *stasis*. Pattern-matching on the token is how this change's
surface search went wrong five separate times.

- **halt** — instructs stopping, skipping a check, or replanning. Retire it.
- **Surface** — instructs reporting to the human. Keep it. Two halts share a
  sentence with one.
- **authority** — says stasis does not by itself complete intent, create
  follow-on work, or authorise an amendment. Keep it, unchanged.
- **mechanism** — describes how the signal is computed. Correct it only where it
  claims a repeated fingerprint *detects* stasis, which the measurement refutes.

A code comment, a docstring, a payload key and a print line all describe the
mechanism without instructing anything. None is edited.

## Deliberately untouched

Each with the reason, because an unexplained omission reads the same as an
oversight.

- **`docs/CONVENTIONS.md` and `packs/core/seeds/docs/CONVENTIONS.md`** — both
  state the halt; both are deleted by `dispatch-agent-context`, committed
  `8b286d51a`, verified absent in that worktree. Editing either conflicts with a
  deletion, and the halt goes with the files. The authority half of that sentence
  is not lost with them: `SKILL.md` states it independently, and T1 pins it
  there. **If that branch does not merge**, both copies keep a retired halt and
  nothing here catches it — escalate rather than widening this spec, because the
  clause would then need an owner.
- **`scripts/loop-cohort.py`, `scripts/_loop_guards.py`** — mechanism only. The
  guards' reset message is byte-pinned by a golden-stream fixture.
- **`packs/core/.apm/hooks/pre-pr.py`, `tools/hooks/pre-pr.py`** — already wrong
  before this change; spec *Follow-ons*.
- **`docs/rfc/0093-intent-scoped-completion.md`** — carries a reworded variant of
  the halt. `Status: Accepted`, frozen as filed; a historical record, not a live
  instruction.
- **`docs/product/changelog.md`** — release history, frozen for the same reason.
- **`guides/governance-extras/how-to/new-rfc.md`** — names the work-loop
  iteration cap and stasis-detection data while illustrating how to amend a cap
  through an RFC. It asserts no halt, and the cap it discusses survives this
  change.
- **`evals/evals.json`** — the two cases mentioning stasis assert amendment
  authority. T1 pins them; no case changes. Recorded as a deviation in the spec's
  Durable Outputs, not as compliance.

## Construction tests

Two owning suites, and the registration that decides whether one of them runs.

- **`packs/core/tests/pack/`** — the pack-local assertions for the three
  `references/` files and the authority statements.
- **`tools/test_stasis_retirement_claims.py`** — the assertions over `guides/`
  and `web/src/content/`, **and AC-0006's absence sweep**. All three cannot live
  in the pack suite: a pack test may not read above its own pack, and the sweep's
  corpus spans `guides/`, `web/src/content/` and the tracked projections as well
  as pack content.

**The `tools/` suite needs two registrations, and only one of them makes it
gate-backed.** `tools/lint-pack-test-boundary.py` fails any suite no runner
names, so it must join the `tools/test_*.py` enumeration in the `Makefile`
repo-test target or the lint reds. Separately, `build-check.yml` names
`tools/test_*.py` suites **individually** as their own steps, and that workflow
runs on every PR. So the suite is dispatch-only until it has a `build-check.yml`
step of its own, and always-run once it does. T3 adds both.

## Design (LLD)

### Design decisions

**The Surface survives the halt.** Two surfaces state both in one sentence. Each
rewrite splits the sentence; neither deletes the row. ADR-0104 is Accepted and
frozen, so losing a Surface would need a superseding ADR.

**The refuted mechanism is a separate claim from the halt.** Several surfaces say
a repeated fingerprint *detects* stasis. That is false independently of what
detection triggers — the fingerprint carries position — so AC-0002 is its own
criterion rather than riding along with the halt removal.

**Authority assertions read the file, not a union.** The existing precedent in
`test_contract_amendment_wave4.py` asserts its phrase against `SKILL.md`
concatenated with `delivery-contract-lifecycle.md`. That proves the statement
exists somewhere in the union — an over-broad edit deleting it from one file
while it survives in the other leaves the suite green. T1's assertions read each
file separately.

**Comparison claims re-point at the cap.** The tables mark "iteration cap and
stasis detection" present here and absent for two named tools. The cap half is
true and survives untouched; the detection half becomes false. Keeping the row
and dropping the stasis clause is the owner's decision of 2026-09-16. Note what
is being dropped: the detection was never observed to work, so this corrects a
claim rather than conceding a capability.

**No script changes.** Nothing branches on the disposition, so retiring it moves
no runtime behaviour.

### Retired phrases — AC-0006's list

Whitespace-normalized, case-insensitive:

- `do not start another round`
- `stops immediately for human replanning`
- `surface immediately; do not run`
- `same findings twice = stop`
- `the loop stops and surfaces`
- `stops a third pass`
- `refuses to self-certify past a red gate or a repeated finding`
- `it stops at plan approval, unresolved boundaries, repeated findings`

`pause for human replanning` was a candidate and is excluded. It matches
iteration-cap prose the spec preserves, in a file the spec does not edit — the
collision AC-0006's third clause exists to catch. Adding a phrase means checking
it against preserved text first.

### Sweep corpus — AC-0006's path list

Each asserted to exist before it is walked. No path here is one another branch
deletes.

- `packs/core/.apm/skills/work-loop/SKILL.md`
- `packs/core/.apm/skills/work-loop/references/*.md`
- `packs/core/.apm/skills/work-loop/evals/evals.json`
- `packs/core/DESIGN.md`
- `.claude/skills/work-loop/`, `.agents/skills/work-loop/` — tracked projections
  carrying the old prose until self-host runs, which is why T4 projects before it
  sweeps
- `guides/core/`, `guides/README.md`
- `web/src/content/packs/core.md`

### Failure, edge cases & resilience

The likeliest failure is an over-broad edit reaching an authority statement. T1
captures their literals before any edit task runs, so the failure reds rather
than passing silently.

The second is a sweep that fires on the tracked projections before self-host. T4
sequences around it.

## Tasks

### T1: Pin what must not move

**Depends on:** none

**Tests:**
- AC-0003 — one normalized-substring assertion per authority statement, each read
  from its own file, not a concatenation.

**Surfaces, all `keep`:**
- `references/delivery-contract-lifecycle.md` — the transition-scope statement
  and the completion statement.
- `SKILL.md` — the termination statement and the finish-checklist statement.
- `evals/evals.json` — the amendment expectation and the amendment rejection.

Only the first has any existing coverage, and that coverage reads a
concatenation, so treat all six as needing their own case.

**Approach:**
- Capture the literals from the current tree before any edit task runs.

**Done when:** all six assertions are green against the unedited tree, so they
can fail in T2 and T3 if an edit reaches too far.

### T2: Retire the halt in the runtime references

**Depends on:** T1

**Tests:**
- AC-0001 — one absence and one presence assertion per file. The presence half is
  the Surface.
- AC-0002 — the refuted detection claim is gone from every surface below.

**Surfaces:**
- `references/finding-adjudication.md` — the route-and-record entry: halt +
  Surface. Drop the halt, keep the Surface.
- `references/state-schema.md` — the stasis paragraph: halt + Surface, same
  treatment. Its `finding_fingerprints` row and the paragraph's first sentence
  both claim the field detects stasis; correct both.
- `references/delivery-contract-lifecycle.md` — the numbered stop conditions:
  drop repeated findings as a condition that stops immediately for replanning,
  and drop the claim that a repeated fingerprint identifies it.

**Done when:** no file instructs a halt, both Surfaces remain, and T1's
assertions are still green.

### T3: Correct the published claims

**Depends on:** T2

**Tests:**
- AC-0004 — absence assertions over the guide corpus and the public page.
- AC-0005 — the two tables and their prose claim a cap.
- AC-0002 — the guide that claims a recorded fingerprint enables detection.

**Surfaces:**
- `guides/core/explanation/core-pack.md` — the loop description; the numbered
  stasis item; the failure-mode row; the two comparison tables and the prose
  beside each. One of these states the halt without using the word *stasis*.
- `guides/core/explanation/token-economy.md` — the third-pass claim.
- `guides/core/how-to/bug-fix.md`, `.../review-someone-elses-pr.md` — capability
  mentions.
- `guides/core/how-to/plan-and-execute-non-trivial-work.md` — a capability
  mention, a detection-mechanism claim, and a halt claim.
- `guides/README.md` — the flagship description.
- `web/src/content/packs/core.md` — a capability claim, and a halt claim that
  does not use the word *stasis*.

**Approach:**
- Register the new suite in the `Makefile` `tools/test_*.py` enumeration, and add
  its own step to `build-check.yml` so the criteria are always-run rather than
  dispatch-only.
- Depends on T2 so the guides describe what the references now say.

**Done when:** no published surface asserts a halt, the tables claim a cap, and
the suite is observed running in a PR check.

### T4: Pin the retirement, then version and project

**Depends on:** T3

**Tests:**
- AC-0006 — the parametrized sweep over the two lists above, one case per retired
  phrase, each corpus path asserted to exist, and a case fixing that no phrase
  matches preserved text.

**Approach:**
- Bump both pack manifests one patch above whatever they hold at execution time,
  and add the changelog entry in the same commit.
- Run `FORCE=1 make build-self` **before** the sweep; the projections carry the
  old prose until it does.

**Done when:** the sweep is green after self-host, `make lint-ruff lint-mypy` is
clean, and catalogue verify returns ok against **this** tree —

```
PYTHONPATH=packages/agentbundle:packages/credbroker \
  python3 -m agentbundle catalogue verify --root .
```

## Rollout

- **Delivery:** prose only; no runtime behaviour changes, because nothing branched
  on the disposition. Reversible by reverting the commit.
- **Infrastructure, external systems:** none.
- **Deployment sequencing:** self-host runs after the version bump and before the
  sweep.

## Risks

- **An over-broad edit deletes an authority statement.** Six of them sit next to
  the halts, and the one with existing coverage is covered by an assertion that
  reads a union of two files and so cannot localise a deletion. T1 is the guard.
- **A Surface is deleted with the halt it shares a sentence with.** Two of them,
  and ADR-0104 is frozen, so the repair would be a superseding ADR.
- **A phrase added to the sweep later collides with preserved prose.** Already
  happened once. AC-0006's third clause makes it a criterion failure rather than
  a discovery.
- **The `CONVENTIONS.md` deletions never merge.** Committed on that branch, not
  merged. *Deliberately untouched* says what to do: escalate, do not widen.
- **A sixth class of surface exists that no search here finds.** Five have been
  found by five different searches. The spec's Testing Strategy states this as an
  unprotected residual rather than implying the list is complete.

## Changelog

- 2026-09-16 — Collapsed. The numbered 43-row inventory is gone; surfaces live in
  the task that edits them, and a *Deliberately untouched* list carries the rest
  with reasons. Criteria went 10 to 6 and tasks 5 to 4. Two review rounds had
  spent most of their findings on stale cross-references between the table, the
  criteria, the tasks and the risks — roughly two thirds of the second round's
  were defects in the first round's repairs. The substance did not change; the
  addressing did.
  Fixed in the same pass: a retired phrase matching preserved iteration-cap
  prose; a sweep corpus containing a path another branch deletes; an instruction
  to edit the approved plan in flight, which the loop refuses; and a false claim
  that `build-check` runs no pytest, which turned the registration question from
  a deferral into an answer.
- 2026-09-15 — Two review rounds, two owner decisions, and a cross-branch
  collision with `dispatch-agent-context`, which deletes both `CONVENTIONS.md`
  copies including the seed this plan had recorded as its own. The surface search
  moved from a token to a vocabulary; a second Surface disposition was found; one
  "already asserted" reuse claim was refuted against the assertion's own text.
- 2026-09-15 — Drafted, cut out of `review-recurrence-family-key` after a third
  adversarial round there put every blocker in this half.
