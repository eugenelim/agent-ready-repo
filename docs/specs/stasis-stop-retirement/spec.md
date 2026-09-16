# Spec: stasis-stop-retirement

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
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

ADR-0104 decided this and records why: the control was evaluated 302 times across
two months of recorded runs and returned false every time, because its key embeds
a line number and an ordinal that every repair moves. Its trigger condition is
destroyed by ordinary editing, so it reads as protection while providing none.

Three things survive, and each is a criterion below rather than a note, because
each is a way the obvious edit does damage.

**The Surface survives.** `matches_previous_round` keeps being computed, emitted,
and reported to the human. ADR-0104 requires that, and two shipped surfaces carry
the instruction — on both, in the same sentence as the halt. ADR-0104 is frozen,
so losing them would need a superseding ADR rather than a spec edit.

**The authority statements survive.** Several surfaces say stasis does not by
itself complete intent, create follow-on work, or authorise an amendment. Those
stay true after the retirement, and a search wide enough to find the halts
reaches them.

**Preserved prose stays unmatched.** The absence sweep that keeps the halt retired
must not fire on text this spec protects. One candidate phrase already collided
with iteration-cap prose, which is why the sweep's own criterion carries that
condition.

After this, full mode's only mechanical bound is its retry cap. That is
ADR-0104's accepted tradeoff, not an oversight.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the runtime instruction changes | the three work-loop `references/` files named in the plan | Spec owner | Each instructs no halt and keeps its Surface | AC-0001 |
| User-facing promise | Applicable — published guides describe the halt as live behaviour | `guides/core/`, `guides/README.md` | Spec owner | No guide asserts a halt on repeated findings | AC-0004 |
| Current product truth | Applicable — the public page and two comparison tables claim the capability | `web/src/content/packs/core.md`, the two tables in `guides/core/explanation/core-pack.md` | Spec owner | Claims match shipped behaviour | AC-0004, AC-0005 |
| Release history | Applicable — core pack content changes | `docs/product/changelog.md` | Spec owner | Entry naming the core bump | Entry present, version matches the manifests |
| Reusable learning | Applicable — a retired control ships on more surfaces than its owning module, in more vocabularies than one search finds | `project-knowledge --capture` | Spec owner | A topic recording the audience split and the five ways this change's own surface search was wrong | Captured at a semantic gate after ship |
| Eval harness | **Deviation, recorded.** `packs/AGENTS.md` § *Security and authoring rules* requires a non-cosmetic pack update to update the pack's eval harness. No eval case exercises the retired route; the two that mention stasis assert amendment authority, which this change does not alter. No case changes. | `packs/core/.apm/skills/work-loop/evals/evals.json` | Spec owner | This row is the record | Reviewed at approval as a deviation, not as compliance |
| Decision rationale | Applicable | `docs/adr/0104-light-mode-review-stops-on-divergence.md` | Decision-maker | Accepted, in tree | Satisfied before this plan |
| Interface compatibility, operations | Not applicable | — | — | — | No schema, runtime, or operator change |

## Boundaries

### Always do

- Keep `matches_previous_round` computed and emitted. Only its disposition is
  retired.
- Work from the surfaces each plan task names, not from a fresh search. This
  change's own surface search has been wrong five times, in five different ways;
  the plan records them.

### Ask first

- Any change to `_loop_guards.py`'s reset message, which is byte-pinned by a
  golden-stream fixture.
- Withdrawing a comparison-table row rather than re-pointing it at the retry cap.
  Re-pointing is the owner's decision, recorded 2026-09-16.

### Never do

- Weaken, reword, or delete any statement that stasis confers no completion or
  amendment authority. This is the likeliest way this change does damage.
- Delete a Surface disposition along with the halt it shares a sentence with.
- Re-key the stop to a position-free identity. ADR-0104 rejects reviving it.
- Change `matches_previous_round`'s computed value, the retry cap, or any script
  under `scripts/`.
- Edit `docs/CONVENTIONS.md` or `packs/core/seeds/docs/CONVENTIONS.md`. Both
  state the halt and both are deleted by `dispatch-agent-context` (committed
  `8b286d51a`). Editing either would conflict with a deletion; the halt goes with
  the files. See the plan's *Deliberately untouched*.
- Add a top-level dependency, a new module, or a new script.

## Testing Strategy

- **The runtime instruction (AC-0001, AC-0002)** — Goal-based check. One absence
  and one presence assertion per reference file. Presence carries as much weight
  as absence: two of these rows would lose a Surface disposition to a careless
  deletion.
- **The authority statements (AC-0003)** — Goal-based check. A normalized
  substring assertion per statement, against literals in the test source and
  read from the file that statement must survive in. Reading a concatenation of
  several files proves the statement exists somewhere in the union, which is not
  the property.
- **The published claims (AC-0004, AC-0005)** — Goal-based check, in a
  repository-level suite: a pack test may not read above its own pack. The plan
  names both registrations the suite needs and which one makes it gate-backed.
- **The retirement stays retired (AC-0006)** — TDD. A parametrized,
  whitespace-normalized absence sweep, the shape ADR-0104's Confirmation already
  ships. Its third clause is the interesting one: a phrase list that matches
  preserved prose fails the criterion rather than surprising the implementer.

**What is not mechanically protected.** Two things, and the first is the reason
this spec keeps a *Deliberately untouched* list instead of a complete inventory.

No search proves a concept absent. The halt is an idea — *the loop stops when
findings repeat* — and this change's own search for it has been wrong five times:
by path scope, by case sensitivity, by token vocabulary, by omitting two
directories, and then by including so many that the command no longer produced
the list it claimed to. AC-0006 pins the phrases this change retires. It cannot
pin the absence of a paraphrase nobody has written.

And no assertion decides whether the replacement comparison claim is *honest*,
only whether it matches an agreed string.

## Acceptance Criteria

A **halt** instructs the loop to stop, skip a check, or replan. A **Surface**
instructs the agent to report to the human. An **authority statement** says
stasis does not by itself complete intent, create follow-on work, or authorise an
amendment. This spec retires halts, preserves Surfaces, and leaves authority
statements untouched. Classify by what a clause obliges, never by whether it
contains the word.

- [ ] **AC-0001.** Each of the three runtime reference surfaces the plan names
  instructs no halt on `matches_previous_round`, and each retains every Surface
  disposition it carries today.
- [ ] **AC-0002.** No surface this spec edits states that a repeated finding
  fingerprint detects stasis.
- [ ] **AC-0003.** Each authority statement the plan names is present in the file
  the plan names it in.
- [ ] **AC-0004.** No file under `guides/` and no page under `web/src/content/`
  asserts that repeated findings stop the loop.
- [ ] **AC-0005.** The two comparison tables in
  `guides/core/explanation/core-pack.md`, and the prose beside each, claim an
  iteration cap and not stasis detection.
- [ ] **AC-0006.** A whitespace-normalized absence sweep fails when any phrase in
  the plan's retired-phrase list appears on any path in the plan's sweep corpus;
  asserts each corpus path exists before walking it; and its phrase list matches
  no text this spec preserves.

## Follow-ons

- **Full mode's retry cap remains a round count.** After this it is the only
  mechanical bound. ADR-0104 holds that round count tracks nothing about the cost
  the bound exists to contain, names diff size as the quantity that does, and
  leaves the cap deliberately in place. Owner: the work-loop maintainer.
- **A hook docstring describes a cap that never existed.**
  `packs/core/.apm/hooks/pre-pr.py` and `tools/hooks/pre-pr.py` call
  `loop-cohort.py check` the work-loop's "iteration/stasis caps", but the signal
  appears only on the inspect and classify paths, never in `check`. Wrong before
  this change and more misleading after. Owner: the work-loop maintainer.
- **The architect pack calls its convergence loop "the prose analogue of
  fingerprint stasis".** That analogy points at a mechanism this spec retires.
  A different pack and a different loop, recorded so the reference is not
  orphaned silently.

## Assumptions

- Technical: the signal is computed in the classifier and emitted on the review
  payloads. No script consumes its value to decide control flow, so nothing under
  `scripts/` changes and no runtime behaviour moves.
- Technical: `.claude/skills/work-loop/` and `.agents/skills/work-loop/` carry the
  same prose as `.apm/` and are tracked. Self-host regenerates them, so they
  converge only after the projection step — which is why AC-0006's corpus is an
  explicit path list and the plan sequences the projection before the sweep.
- Technical: an `agentbundle` CLI gate run from this worktree executes whichever
  worktree currently holds the shared editable install. The plan names the
  interpreter for every CLI gate; repo-local scripts are unaffected.
- Process: ADR-0104 is Accepted and frozen. If this spec cannot preserve the
  Surface disposition it requires, the answer is a superseding ADR, not a
  spec-side deviation.
- Process: both `CONVENTIONS.md` copies are deleted on another branch, committed
  but not merged. The plan records what to do if that merge does not happen.
- Process: a core pack bump and its file set are owned by
  [`packs/AGENTS.md`](../../../packs/AGENTS.md) § *Version bump rule*. The target
  is a patch above whatever the manifests hold at execution time; this branch has
  carried unreleased bumps from concurrent work more than once.
