# Spec: stasis-stop-retirement

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0104](../../adr/0104-light-mode-review-stops-on-divergence.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Full mode no longer instructs a halt when review findings repeat, and no shipped
surface claims it does.

ADR-0104 decided the retirement and records why: the control was evaluated 302
times across two months of recorded runs and returned false every time, because
its key embeds a line number and an ordinal that every repair moves. Its trigger
condition is destroyed by ordinary editing, so it reads as protection while
providing none. This spec carries that decision out.

The signal itself survives. `matches_previous_round` is still computed, still
emitted, and still **Surfaced** — ADR-0104 requires that. Two shipped surfaces
instruct Surfacing, and on both the instruction shares a sentence with the halt
being removed. Removing the halt without preserving them would leave the
accepted decision with no shipped home, and since ADR-0104 is frozen the repair
for that would be a superseding ADR rather than a spec edit.

After this, full mode's only mechanical bound is its retry cap. That is
ADR-0104's accepted tradeoff, not an oversight.

### Four audiences, not one edit

The disposition is stated in four places that differ in who reads them and what
breaks when they are wrong. Treating them as one prose sweep is how an earlier
attempt at this work went wrong.

| Audience | Surfaces | What a wrong edit costs |
| --- | --- | --- |
| The agent, at runtime | three `references/` files | the loop behaves against its own instructions |
| An adopter repository | one projected seed | other people's repositories carry the stale rule |
| A reader of the published guides | four guide files | documented behaviour does not match shipped behaviour |
| A prospective adopter | the public pack page, and two comparison tables | a capability claim against named competitors becomes false |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the runtime instruction changes | `packs/core/.apm/skills/work-loop/references/` (three files) | Spec owner | Each describes the signal, preserves the Surface, and states no halt | AC-0001, AC-0002, AC-0003 |
| User-facing promise | Applicable — published guides describe the stop as live behaviour | `guides/core/explanation/`, `guides/core/how-to/`, `guides/README.md` | Spec owner | No guide asserts a halt on repeated findings | AC-0007 |
| Current product truth | Applicable — the public pack page and two comparison tables claim the capability | `web/src/content/packs/core.md`, `guides/core/explanation/core-pack.md` comparison tables | Spec owner + the owner of the positioning call | Claims match shipped behaviour, or are withdrawn | AC-0008, AC-0009 |
| Interface compatibility | Applicable — an adopter-projected seed states the rule | `packs/core/seeds/docs/CONVENTIONS.md`, `docs/CONVENTIONS.md` | Spec owner | The clause is split so its authority half survives and its stop half goes, and the twin does not diverge silently | AC-0004, AC-0005 |
| Eval harness | Applicable — `packs/AGENTS.md` requires a non-cosmetic pack update to update the pack's eval harness | `packs/core/.apm/skills/work-loop/evals/evals.json` | Spec owner | The disposition is recorded: the two matching eval cases assert amendment authority, which this change does not alter, so no case changes | Stated in the plan's inventory rows 13 and 14; no edit |
| Decision rationale | Applicable | `docs/adr/0104-...md` | Decision-maker | Accepted, in tree | Satisfied before this plan; no further write |
| Release history | Applicable — core pack content changes | `docs/product/changelog.md` | Spec owner | Entry naming the core bump | Entry present, version matches the manifests |
| Reusable learning | Applicable — a retired control ships on more surfaces than its owning module | `project-knowledge --capture` | Spec owner | A topic recording the four-audience split and the seed's dual-purpose clause | Captured at a semantic gate after ship |
| Operations | Not applicable | — | — | — | No runtime or operator change |

## Boundaries

### Always do

- Preserve a Surface disposition for the signal. ADR-0104 requires it; only the
  halt is retired.
- Keep `matches_previous_round` computed and emitted. Its disposition is
  retired, not its computation.
- Work from the plan's surface inventory, which is reproducible from a stated
  command, rather than from a fresh search. An earlier attempt at this change
  used a case-sensitive search that missed two of its own targets.

### Ask first

- Any change to `scripts/_loop_guards.py`'s reset message, which is byte-pinned
  by a golden-stream fixture.
- Withdrawing a comparison-table row, rather than re-pointing it at the retry
  cap as AC-0009 now requires. Re-pointing is the owner's answer; withdrawing
  would be a different positioning call.

### Never do

- Weaken, reword, or delete any statement that stasis confers no completion or
  amendment authority. Those are not stop routes, they stay true, and a search
  broad enough to find the halts reaches them. This is the single likeliest way
  this change does damage.
- Re-key the stop to the position-free family. ADR-0104 rejects reviving it.
- Change `matches_previous_round`'s computed value, the retry cap, or any
  script under `scripts/`.
- Add a top-level dependency, a new module, or a new script.

## Testing Strategy

- **The runtime instruction (AC-0001, AC-0002, AC-0003)** — Goal-based check.
  One absence and one presence assertion per reference file. Presence matters as
  much as absence: deleting a row outright would leave an emitted field
  undocumented, and on two of these rows it would delete a Surface disposition
  ADR-0104 requires.
- **The projected seed and its twin (AC-0004, AC-0005)** — Goal-based check. The
  clause carries two obligations in one sentence, so the assertion has to see
  both halves. AC-0005 asserts the repository copy is untouched, which reads
  backwards until you know why: that file is being removed by another worktree,
  so the two deliberately diverge for as long as it survives.
- **The authority statements (AC-0006)** — Goal-based check. One normalized
  substring assertion per statement, against literals in the test source. One
  row is covered by an existing suite; five are not, including one previously
  recorded as covered whose existing assertion does not contain the token being
  guarded. The plan's inventory records which is which and the rule used to
  decide.
- **The published guides and public page (AC-0007, AC-0008)** — Goal-based
  check, in a repository-level suite because a pack test may not read above its
  own pack. The plan names the Makefile runner line the suite joins; without
  that registration the boundary lint fails it and nothing executes it.
- **The competitive claims (AC-0009)** — Goal-based check. The owner's answer is
  to re-point the rows at the iteration cap rather than withdraw them, so the
  assertion has a fixed target: both tables and both prose passages claim a cap
  and no detection.
- **The retired phrasing stays retired (AC-0010)** — TDD. A parametrized,
  whitespace-normalized absence sweep over the plan's two literal lists,
  asserting its corpus paths exist before walking them. Same shape as the sweep
  ADR-0104's Confirmation already ships.
- **The refuted mechanism claim (AC-0011)** — Goal-based check. Distinct from
  the halt: several surfaces assert that a repeated fingerprint *detects*
  stasis, which the measurement refutes independently of what detection then
  triggers.

**What is not mechanically protected.** Three things. The comparison tables state
a competitive claim, and no assertion can decide whether the replacement claim is
*honest* — only whether it matches an agreed string. AC-0005 rests on another
worktree removing `docs/CONVENTIONS.md`; if that does not happen, the repository
copy keeps a retired halt and the criterion asserts the opposite. And the
inventory is a
vocabulary search over a concept: a surface stating the halt in words none of
the patterns match is not in the table, and AC-0010 cannot pin the absence of a
paraphrase nobody has written yet. Three earlier attempts at this inventory each
missed a different class, which is why the method and its limit are recorded
rather than the result alone.

## Acceptance Criteria

**Halt, Surface, authority.** A *halt* instructs the loop to stop, skip a check,
or replan. A *Surface* instructs the agent to report to the human. An *authority
statement* says stasis does not by itself complete intent, create follow-on
work, or authorise an amendment. This spec retires halts, preserves Surfaces,
and leaves authority statements untouched.

The plan's *Surface inventory* enumerates every occurrence with its file, line,
class, and action; states the vocabulary command that reproduces it; and names
that command's residual, which is that a vocabulary search cannot prove a
concept absent.

### The runtime instruction

- [ ] **AC-0001.** `references/finding-adjudication.md`'s route-and-record entry
  for the signal instructs no halt and retains a Surface disposition.
- [ ] **AC-0002.** `references/state-schema.md`'s stasis paragraph instructs no
  halt and no skipped check, **retains its Surface disposition**, and still
  describes what the field is. Two shipped surfaces instruct Surfacing, not one;
  this is the second.
- [ ] **AC-0003.** `references/delivery-contract-lifecycle.md`'s numbered stop
  conditions no longer list repeated findings as a condition that stops
  immediately for replanning.

### The adopter-projected seed

- [ ] **AC-0004.** `packs/core/seeds/docs/CONVENTIONS.md`'s clause instructs no
  pause for replanning, and its statement that retry caps and stasis neither
  complete intent nor create backlog work survives intact.
- [ ] **AC-0005.** `docs/CONVENTIONS.md` is unchanged by this work. Its copy of
  the clause is byte-identical to the seed's today, and divergence here is
  deliberate: the `dispatch-agent-context` worktree is removing that file. Both
  of its sessions have been told the clause carries a retired halt and a
  surviving authority statement, so a relocation inherits both halves.

### What must not move

- [ ] **AC-0006.** Every authority statement the plan's inventory marks `keep` is
  present, asserted as a normalized substring against literal text held in the
  test source — not read from the surface under test, which would compare a file
  to itself and could never fail. The plan names which rows an existing suite
  already covers and which need new cases.
- [ ] **AC-0007.** No file under `guides/` asserts that repeated findings stop
  the loop.
- [ ] **AC-0008.** The public pack page states only capabilities the tree has
  after this change.
- [ ] **AC-0009.** The two competitive comparison tables, and the prose beside
  each, claim an iteration cap and not stasis detection. The cap is real,
  survives this change untouched, and is still absent from both compared tools;
  the detection half is what becomes false.

### Staying retired

- [ ] **AC-0010.** A whitespace-normalized absence sweep fails when any phrase in
  the plan's *retired phrases* list reappears on any path in the plan's *sweep
  corpus* list, and asserts every corpus path exists before walking it. Both
  lists are literal in the plan.
- [ ] **AC-0011.** No surface this spec is permitted to edit states that a
  repeated finding fingerprint detects stasis. Code comments, docstrings, and
  the payload key are out of scope by Boundaries and out of scope here.

## Follow-ons

- **Full mode's retry cap remains a round count.** After this lands it is full
  mode's only mechanical bound. ADR-0104 holds that round count tracks nothing
  about the cost the bound exists to contain and names diff size as the quantity
  that does, and leaves the cap deliberately in place. Owner: the work-loop
  maintainer.
- **A hook docstring describes a cap that never existed.**
  `packs/core/.apm/hooks/pre-pr.py` and `tools/hooks/pre-pr.py` call
  `loop-cohort.py check` the work-loop's "iteration/stasis caps", but the signal
  appears only on the inspect and classify paths, never in `check`. Wrong before
  this change and more misleading after it. Excluded here because it is a
  pre-existing defect in a different component. Owner: the work-loop maintainer.
- **The architect pack describes its own convergence loop as "the prose analogue
  of fingerprint stasis".** That analogy points at a mechanism this spec
  retires. Out of scope — a different pack, a different loop — and recorded so
  the reference is not orphaned silently.

## Assumptions

- Technical: the signal is computed in the classifier and emitted on the review
  payloads; no script consumes its value to decide control flow. Nothing in
  `scripts/` changes.
- Technical: `.claude/skills/work-loop/` and `.agents/skills/work-loop/` carry
  the same prose as `.apm/` and are tracked. They are regenerated by self-host
  rather than edited, so they converge only after the projection step — which is
  why AC-0008's corpus is stated explicitly rather than left as "shipped
  surfaces".
- Technical: `docs/CONVENTIONS.md:1093` is byte-identical to the projected seed.
  Whether it moves with the seed is open; see Boundaries.
- Process: ADR-0104 is Accepted and frozen. If this spec cannot preserve the
  Surface disposition it requires, the answer is a superseding ADR, not a
  spec-side deviation.
- Process: a core pack bump and its file set are owned by
  [`packs/AGENTS.md`](../../../packs/AGENTS.md) § *Version bump rule*. The target
  is a patch above whatever the manifests hold at execution time; this branch has
  carried unreleased bumps from concurrent work more than once.
