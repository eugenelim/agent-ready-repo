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
emitted, and still **Surfaced** — ADR-0104 requires that, and today the only
shipped instruction to Surface it sits in the same sentence as the halt being
removed. Removing the halt without preserving the Surface would leave the
accepted decision with no shipped home.

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
| User-facing promise | Applicable — published guides describe the stop as live behaviour | `guides/core/explanation/`, `guides/core/how-to/` | Spec owner | No guide asserts a halt on repeated findings | AC-0006 |
| Current product truth | Applicable — the public pack page and two comparison tables claim the capability | `web/src/content/packs/core.md`, `guides/core/explanation/core-pack.md` comparison tables | Spec owner + the owner of the positioning call | Claims match shipped behaviour, or are withdrawn | AC-0007 |
| Interface compatibility | Applicable — an adopter-projected seed states the rule | `packs/core/seeds/docs/CONVENTIONS.md` | Spec owner | The clause is split so its authority half survives and its stop half goes | AC-0004 |
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

- Withdrawing a comparison-table row rather than re-pointing it at the retry
  cap. That is a positioning call, not a documentation fix.
- Editing `docs/CONVENTIONS.md`, whose line 1093 is byte-identical to the
  projected seed. Whether the repository copy moves with the seed is a
  convention-ownership question.
- Any change to `scripts/_loop_guards.py`'s reset message, which is byte-pinned
  by a golden-stream fixture.

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
  undocumented, which is a different defect from the one being fixed.
- **The projected seed (AC-0004)** — Goal-based check. The clause carries two
  obligations in one sentence, so the assertion has to see both halves: the stop
  gone, the authority statement intact.
- **The authority statements (AC-0005)** — Goal-based check. One positive
  assertion per surviving statement. Two are already asserted by
  `test_contract_amendment_wave4.py`; the plan names which, so this criterion
  adds cases rather than duplicating them.
- **The published guides and public claims (AC-0006, AC-0007)** — Goal-based
  check. Absence assertions over the guide corpus, and for the comparison tables
  an assertion that matches whichever resolution the owner picks.
- **The retired phrasing stays retired (AC-0008)** — TDD. A parametrized,
  whitespace-normalized absence sweep with an explicit corpus path list and an
  explicit retired-phrase list, asserting its corpus paths exist before walking
  them. Same shape as the sweep ADR-0104's Confirmation already ships.
- **The refuted mechanism claim (AC-0009)** — Goal-based check. Distinct from
  the halt: one surface asserts that a repeated fingerprint *detects* stasis,
  which the measurement refutes independently of what the detection then does.

**What is not mechanically protected.** The comparison tables state a
competitive claim. No assertion can decide whether the replacement claim is
*honest*, only whether it matches an agreed string. That judgement is the
owner's, recorded once in the plan.

## Acceptance Criteria

**Halt, Surface, authority.** A *halt* instructs the loop to stop, skip a check,
or replan. A *Surface* instructs the agent to report to the human. An *authority
statement* says stasis does not by itself complete intent, create follow-on
work, or authorise an amendment. This spec retires halts, preserves Surfaces,
and leaves authority statements untouched.

The plan's *Surface inventory* enumerates every occurrence with its file, line,
class, and action, and states the command that reproduces it.

### The runtime instruction

- [ ] **AC-0001.** `references/finding-adjudication.md`'s route-and-record entry
  for the signal instructs no halt and retains a Surface disposition.
- [ ] **AC-0002.** `references/state-schema.md`'s stasis paragraph instructs no
  halt and no skipped check, and still describes what the field is.
- [ ] **AC-0003.** `references/delivery-contract-lifecycle.md`'s numbered stop
  conditions no longer list repeated findings as a condition that stops
  immediately for replanning.

### The adopter-projected seed

- [ ] **AC-0004.** `packs/core/seeds/docs/CONVENTIONS.md`'s clause instructs no
  pause for replanning, and its statement that retry caps and stasis neither
  complete intent nor create backlog work survives intact.

### What must not move

- [ ] **AC-0005.** Every authority statement the plan's inventory marks `keep`
  is unchanged, compared against its pre-change text under whitespace
  normalization.
- [ ] **AC-0006.** No file under `guides/` asserts that repeated findings stop
  the loop.
- [ ] **AC-0007.** The public pack page and the two comparison tables state only
  capabilities the tree has after this change.

### Staying retired

- [ ] **AC-0008.** A whitespace-normalized absence sweep fails when any retired
  phrasing named in the plan's inventory reappears on any path in the plan's
  sweep corpus, and asserts every corpus path exists before walking it.
- [ ] **AC-0009.** No shipped surface states that a repeated finding fingerprint
  detects stasis.

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
