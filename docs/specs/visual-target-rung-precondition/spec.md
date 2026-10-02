# Spec: visual-target rung precondition

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0132](../../adr/0132-visual-target-confirmation-is-an-explicit-state.md);
  [`visual-target-field`](../visual-target-field/spec.md) must ship first, because
  this contract reads a field that slice writes.
- **Brief:** none
- **Discovery:** [`visual-target-confirmation/notes/carrier-inventory.md`](../visual-target-confirmation/notes/carrier-inventory.md)
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

The `approved-visual-target` rung resolves only when the direction artifact
carries `visual_target: confirmed`. The superseded prose reading — that a
target's presence, or an unrecorded human nod, is enough — is gone from every
carrier, and a mechanism that does not depend on knowing the carrier set in
advance keeps it gone.

## What Changes

- `references/visual-observation.md`'s precedence table states the
  `approved-visual-target` rung's condition as `visual_target: confirmed`.
- Every carrier that states the rung's precondition names the field.
- A new construction test in `tests/roster/` enforces the **positive exclusive
  property** below over a re-run sweep, not over a fixed file list. It lives
  there rather than in a pack suite because the sweep reads above any one pack,
  which `tools/lint-pack-test-boundary.py` refuses; `tests/AGENTS.md` names
  `tests/roster/` as the home for a repository-level assertion. Landing there
  carries that file's registration obligations, which this contract discharges.
- AC-0008's assertion moves to `tests/roster/` for the same reason — it reads a
  path under `docs/` — and, because it names a `docs/specs/<slug>` literal, owes
  a `.workspace-prune-protected.toml` entry that the property test does not.
  Both modules' CI registration is T8's work. **Two of its three obligations
  are gated and one is not**, and the difference is measured rather than
  assumed. `tests/roster/test_two_sided_prune_closure_invariant.py` enforces the
  prune entry unconditionally. `tools/lint-ci-parity.py` enforces the
  `STEP_DISPOSITION` entry only for a step that already exists — it demands "one
  entry per step", so a step and its row deleted together pass in both
  directions, as `tools/test_build_gate_chain.py:283-285` states outright.
  **Nothing in the repository requires the named build-check step to exist at
  all.** T8 therefore carries its own check for that one obligation; see its
  `Done when`. This contract still states no acceptance criterion for the
  registration, because a task with a closure predicate that detects the gap is
  what was missing, not a criterion restating the obligation.
- `converge`, `visualize` and `creative-direction`'s output contract are gated
  on a confirmed target — the three obligations `visual-target-field` retired
  on 2026-09-30 and handed here, because the first of them moves this very
  rung.
- `docs/specs/frontend-visual-authority/spec.md`'s `Status` records that
  ADR-0132 supersedes one of its contract-tier `Always do` rules.
- `test_visual_authority_release.py`'s version pin moves with this delivery's
  own bump.

## The mechanism, and its limit

Three mechanisms were tried on the predecessor contract and rejected, each
because it assumed the author already knew the full extent: a presence check
(leaves the old reading alive beside the new one), a closed retired-phrase set
(cannot enumerate an English reading), and a closed surface set (cannot
enumerate surfaces not yet found). Do not retry them.

This contract uses a **positive exclusive property** instead:

> Within the swept Markdown scope, every sentence that both refers to a visual
> target and states a confirmation or approval condition must also contain the
> literal `visual_target`.

It is closed over paraphrase, because it constrains any sentence that states
the condition however worded rather than matching a retired phrase. It is
closed over undiscovered carriers, because the scope is produced by re-running
the sweep at test time rather than by listing files.

**Five limits, each measured rather than assumed.** Trial runs against this
repository on 2026-09-30 and 2026-10-02 produced all five; they are recorded
here so a review round does not have to rediscover them.

1. *Neither the rung's name nor the artefact's name is a claim about it.*
   `approved-visual-target` is a rung identifier and contains both a target
   reference and the word `approved`, so an unrefined property fires on every
   list of rung names, including tuples inside test files. The spaced noun
   phrase `approved visual target` has the same defect for a different reason:
   `approved` is part of what the artefact is called, not an assertion that
   anything was approved, so every mention of it supplies its own cue.

   **A name is not a cue, but it is still a reference.** The property therefore
   strips both forms **for the cue test only**, and tests the target reference
   against the unstripped sentence. The asymmetry is the whole of this limit.
   Stripping a name is not the same as exempting a file — and stripping it from
   both tests would exempt the carriers that name the rung by its identifier and
   then state its condition, which is most of what this contract exists to
   migrate.

   **Measured 2026-10-02**, against the tree `visual-target-field` left:

   | Cue test | Reference test | Sentences in scope |
   | --- | --- | ---: |
   | identifier stripped | same stripped text | 24 |
   | both names stripped | same stripped text | 7 |
   | both names stripped | **unstripped sentence** | **14** |

   The first row is too wide: 17 of its 24 state no condition at all, and
   `Absence of an approved visual target is not a blocker.` is representative.
   Requiring the literal there would name a field for no reason in instructions
   adopters read. The second row is too narrow by the same measurement: it drops
   both carriers AC-0004 names. In
   `guides/frontend-engineering/how-to/read-the-design-handoff.md` the sentence
   row 3 recovers is the rung bullet at lines 64-66 — ``**`approved-visual-target`**
   — your `direction/<slug>.md` records that a person confirmed the
   composition`` — whose cue `confirmed` survives name stripping. The third row
   is the one this contract uses.

   **One sentence in that file is outside every row, and is named here so no
   round rediscovers it.** The next sentence, `**You are here if** the artifact
   says somewhere that the composition was approved or signed off, rather than
   merely proposed or picked.`, is the most explicit surviving statement of the
   reading ADR-0132 retires — and it carries no `visual[ _-]target` reference at
   all, so the reference test cannot reach it under any row. Widening the cue
   set does not help: measured 2026-10-02, adding `exists` and `present` moves
   the property from 14 sentences to 19 and still does not reach it. Only a
   wider reference test or structural awareness would, and this contract forbids
   both. T3 migrates it by hand, and AC-0005 names it.
2. *Sentence segmentation is meaningless outside prose.* In JSON and Python a
   whole file is one "sentence", so the property would demand the field inside
   eval payloads and module docstrings. The property therefore covers Markdown
   carriers. The non-Markdown carriers are reached by the sweep but excluded
   from the property; those among them that assert the rung's precondition are
   covered by the suite that owns each, over parsed structure rather than over
   sentences — AC-0011 holds them to that. Not every non-Markdown carrier is
   such an assertion, and three of them sit in `tests/roster/` with no owning
   pack, so this limit claims no universal pack-suite coverage.
3. *Segmentation is unreliable inside Markdown too, and the property accepts
   that cost.* A table and an HTML comment block carry no terminal period, so
   whitespace normalization collapses each into one "sentence" that joins
   unrelated rows or bullets. **Five of the fourteen firing loci are this
   class**, measured 2026-10-02:

   - `design-system/SKILL.md` — two, its rung table and its routing table;
   - `token-taxonomy-template.md` — the `**Route:**` comment block;
   - `establish-design-intent.md` — **two**, the same `**Route:**` block, and a
     run-on beginning `confirm the shape against what you get back.*`. That
     line ends `.*` rather than `.`, so the splitter `(?<=[.!?])\s+` does not
     break there and the sentence runs through a heading, an HTML comment and a
     prompt block to `…and any approved visual target.`

   In each the target reference and the cue come from different rows, bullets or
   blocks. The second `establish-design-intent.md` locus is the worst of them:
   its only available migration names the field inside a copy-paste user prompt
   that states no condition. **T3 migrates all five rather than exempting
   them**, because a structural parser is machinery this contract does not need
   for five loci, and because naming the field in a template's
   `**Visual target:**` bullet is correct on its own terms. Do not add table or
   comment awareness to the property to avoid them.
4. *A gated sentence is outside the property, and names the field anyway.*
   AC-0012 to AC-0014 gate three sentences in `converge.md`, `visualize.md` and
   `SKILL.md`. Under limit 1 those sentences strip to nothing that carries a
   cue, so AC-0006 does not reach them: `converge.md`'s `When an approved visual
   target exists, write the selected direction's compositional commitments`
   becomes `When an exists, write ...`. Their `visual_target: confirmed`
   literal is therefore a plain requirement of AC-0012 to AC-0014, **not** a
   consequence of AC-0006, and those criteria state it in their own right.
   **Naming the field is still not reading it.** `visualize` can say that a
   target the human has confirmed is the one `converge` records as
   `visual_target: confirmed` without `visualize` reading anything; the sentence
   cites the disposition, the operation does not consult it.
5. *The cue set is narrower than English, and limit 1 narrows it further.* A
   carrier phrased with neither `confirm` nor `approved` — "a target the team
   has signed off", say — is outside the property. So, now, is a condition
   whose only cue was the artefact's own name: `when an approved visual target
   exists` is no longer caught. Both narrow the gap; neither closes it. This
   cost was accepted deliberately on 2026-10-02 against requiring the literal in
   17 sentences that state no condition. AC-0007 keeps the cue set in one named
   constant so widening it is deliberate.

Against the current tree the property identifies **14 sentences across 12
Markdown files**. That is the migration T2, T3 and T7 owe between them: two of
the fourteen are the authoritative statements T2 owns, in
`visual-observation.md`'s precedence row and `frontend-engineering`'s
`SKILL.md`; one is in `visualize.md`, which T7 owns outright; the rest are T3's.
Two more are the same sentence in `packs/frontend-engineering/JOURNEY.md` and
its projection at `web/src/content/journeys/frontend-engineering.md`, so the
distinct texts number thirteen.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md` | eugenelim | The rung condition names the field | AC-0001 holds |
| Behavioural invariant | `tests/roster/` | eugenelim | The exclusive property is enforced over a re-run sweep | AC-0006, AC-0007 hold |
| Producer instruction | `packs/experience-design/.apm/skills/creative-direction/references/converge.md`, `references/visualize.md`, `SKILL.md` | eugenelim | Each gated sentence names the confirmation condition and the field | AC-0012, AC-0013, AC-0014 hold |
| Governance record | `docs/specs/frontend-visual-authority/spec.md`, asserted from `tests/roster/` | eugenelim | Its `Status` names the superseded rule | AC-0008 holds |
| Release history | both packs' `pack.toml`, their `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | eugenelim | Matching versions and release entries | AC-0009, AC-0010 hold |

Retention class: repository-durable.

## Agent Rules

### Always do

- Re-run the carrier sweep as part of the change, and again at test time. The
  extent measured on 2026-10-02, against the tree `visual-target-field` left,
  is 27 files and 105 loci — 15 Markdown and 12 non-Markdown carriers. It was
  25 files and 59 loci at authoring on 2026-09-30; that slice is what moved it.
  Treat any further difference as a discovery, not a failure.
- Normalize whitespace before sweeping. A raw line-oriented grep misses
  `frontend-reviewer.md`, where the phrase wraps mid-line.
- Keep `visual-observation.md` free of the literals `experience-design`,
  `creative-direction` and `design-system`; `test_visual_authority_precedence.py`
  reds on any of them. The field name `visual_target` is not one of them.

### Ask first

- Before raising `BODY_BUDGET` in `test_visual_authority_entrypoint.py`. The
  budget is owned by the Shipped `design-to-build-value-handoff` spec, and the
  body stands at **964 of 968** lines — four lines of headroom, measured
  2026-10-02 by running `skill_body_lines()`. The 963 carried from authoring was
  wrong in the unsafe direction.
- Before widening or narrowing the confirmation-cue set in AC-0007.
- Before changing the `visual_target` value vocabulary, which
  `visual-target-field` owns.
- Before gating a producing surface this contract does not already name. The
  three it names are gated together deliberately: gating one without the others
  has a producer forming a binding claim the writer then records.

### Never do

- Never retry a presence check, a closed retired-phrase set, or a closed
  surface set as the enforcing mechanism.
- Never key the property on a file list embedded in the test.
- Never add a dependency, module boundary, or top-level directory.

## Testing Strategy

- **TDD — the rung condition names the field (AC-0001, AC-0002, AC-0003).**
  Literal assertions over shipped bytes, from the owning pack's test
  directories.
- **TDD — the restating carriers name it too (AC-0004).** Verified by
  the AC-0006 property rather than per-file, because a per-file assertion is
  the closed surface set this contract may not retry.
- **Recorded manual observation — the two loci outside the property (AC-0005).**
  AC-0006 cannot decide them and no other test in this contract does, so each is
  a named observation in the verification ledger rather than an assertion. The
  criterion names both and covers nothing else; naming two loci a measurement
  found is not the closed surface set this contract may not retry, because the
  property still computes its own scope and these are its measured complement.
- **TDD — the producing surfaces are gated (AC-0012, AC-0013, AC-0014).** Each
  asserts an exact literal inside a bounded unit — one blank-line-delimited
  paragraph block, or one list item — read from the single file the criterion
  names, with the anchor's uniqueness in that file asserted rather than
  assumed. A period-delimited span of normalized text is not a bounded unit:
  adjacent structure carrying no terminal period joins it silently.
- **TDD — the non-Markdown carriers are covered (AC-0011).** The suite that
  owns each carrier asserts over parsed structure, for those carriers that
  assert the rung's precondition. The criterion states no count and the reason
  is in it. One construction test guards the
  **non-Markdown** count against silent shrinkage. It must count that subset
  rather than the whole swept set — an aggregate floor stays green while every
  non-Markdown carrier disappears and Markdown ones replace it.
- **TDD — the exclusive property holds (AC-0006, AC-0007).** One new test in
  `tests/roster/` — not a pack suite, because the sweep reads above any one pack
  and `tools/lint-pack-test-boundary.py` refuses that — walks the swept scope,
  normalizes whitespace, splits sentences, and asserts the property. It must red when a carrier states the condition without the field:
  the plan carries a mutation check that proves it does, because a sweep test
  that finds nothing passes for both the right and the wrong reason.
- **Goal-based check — governance (AC-0008).** A literal assertion over the
  superseded spec's `Status`, from `tests/roster/` for the same boundary reason:
  it reads a path under `docs/`, which no pack test may reach.
- **Goal-based check — the release surface (AC-0009, AC-0010).**
  `tests/conformance/test_pack_metadata.py`, the moved version pin, and a
  recorded baseline reading for each pack taken before the bump.

## Acceptance Criteria

- [ ] **AC-0001.** In `references/visual-observation.md`, the precedence-table
  row whose first cell is `approved-visual-target` contains the literal
  `visual_target: confirmed` in its condition cell.
- [ ] **AC-0002.** That file contains none of the literals `experience-design`,
  `creative-direction`, `design-system`.
- [ ] **AC-0003.** In `frontend-engineering`'s `SKILL.md`, the sentence naming
  what the `approved-visual-target` rung requires contains the literal
  `visual_target: confirmed`.
- [ ] **AC-0004.** `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`
  and `guides/frontend-engineering/how-to/read-the-design-handoff.md` each
  contain the literal `visual_target` wherever they state the rung's
  precondition, verified by the AC-0006 property rather than by a per-file
  assertion.
- [ ] **AC-0005.** **Two loci state the superseded presence reading and lie
  outside every mechanism in this contract. Both are migrated by hand under T3,
  named here so the criterion is decidable rather than open-ended:**
  `guides/frontend-engineering/how-to/read-the-design-handoff.md`'s
  `**You are here if** the artifact says somewhere that the composition was
  approved or signed off` (no target reference, so no row reaches it), and
  `packs/experience-design/.apm/skills/design-system/SKILL.md`'s
  `the visual target when one exists` (its only cue is `exists`, outside the
  confirmation-cue set). Both are checked as recorded manual observations in the
  verification ledger, because no test in this contract decides them.
  **This criterion was narrowed twice on 2026-10-02, and never widened.** It
  first asserted over the whole swept scope on the literals `exists` and
  `present`, which nothing in this contract checks — AC-0006's cue set is
  `confirm` and `approved`. Adding those two literals to the cue set was
  measured and declined: it moves the property from 14 sentences to 19, three of
  the five additions state no condition, and it still does not reach the
  sign-off sentence. It then carried a second clause asserting that no sentence
  *within* AC-0006's reach states presence as sufficient. That clause had no
  artifact either — AC-0006 requires the literal `visual_target` in a firing
  sentence and settles nothing about what that sentence claims — so it was
  dropped rather than given new machinery. AC-0005 is now exactly the two loci
  above. See § The mechanism, and its limit, limit 1.
- [ ] **AC-0006.** A construction test enforces the positive exclusive property:
  over a whitespace-normalized sweep of the Markdown files under `packs/`,
  `guides/`, `web/src/content/`, `tests/` and `docs/design/`, every sentence
  matching `visual[ _-]target` **in its unstripped text** that also contains a
  confirmation cue **after both the rung identifier `approved-visual-target`
  and the spaced noun phrase `approved visual target` are stripped** contains
  the literal `visual_target`. The two tests read different text, deliberately:
  see § The mechanism, and its limit, limit 1. The scope is computed by the test
  at run time from those roots; no file list is embedded.
- [ ] **AC-0007.** That test names its confirmation-cue set and its stripped
  name forms explicitly in module-level constants, and its docstring records
  both exclusions: a carrier stating the condition with no cue from that set is
  outside the property, and so is one whose only cue came from a stripped name.
- [ ] **AC-0011.** Every non-Markdown carrier **that asserts the rung's
  precondition** names the field where it does so, verified by the suite that
  owns it over parsed structure rather than by the sentence property.
  **This criterion states no count, deliberately.** Three successive drafts
  enumerated the subject set by hand and each was wrong: first all twelve
  carriers the sweep reaches, then nine, and the nine included two modules
  carrying only a rung-name tuple — the same shape the draft used to exclude
  three others. A carrier that merely names a rung is not asserting the
  precondition, limit 1 already says so, and no hand count of that distinction
  has survived a review round. The property is what holds; T3 walks the
  measured carrier set and applies it. A carrier with no owning suite is not
  thereby unowned — it is not a subject.
  A second construction test asserts that the count of non-Markdown carriers
  the sweep reaches has not silently fallen. That count is mechanical and is
  the only number this criterion relies on.
- [ ] **AC-0012.** In `packs/experience-design/.apm/skills/creative-direction/references/converge.md`,
  the paragraph block containing the literal `write the selected direction's
  compositional commitments` also contains the literal `visual_target:
  confirmed`, and that anchor occurs exactly once in the file. T7 splits that
  instruction into its own blank-line-delimited block first: today it sits
  inside a five-sentence paragraph, so the literal could satisfy the criterion
  from a sentence unrelated to the gated write.
- [ ] **AC-0013.** In `references/visualize.md`, the paragraph block containing
  the literal `record its identity and three boundaries` also contains the
  literals `the human has confirmed` **and** `visual_target: confirmed`, and
  that anchor occurs exactly once in the file. Both, and they are not in
  tension: the condition `visualize` acts on is the human confirmation it
  already holds — it runs before `converge` writes the field, so it must not be
  written as a field read — while naming the disposition `converge` will record
  is a citation, not a read. This criterion requires that literal in its own
  right; AC-0006 does not reach this sentence. See § The mechanism, and its
  limit, limit 4.
- [ ] **AC-0014.** In `creative-direction`'s `SKILL.md` — that file read
  directly, not a concatenation of the skill's files — the list item beginning
  `- **Approved visual target**` contains the literals `the human has
  confirmed` **and** `visual_target: confirmed`, and that item occurs exactly
  once in that file. The second literal is this criterion's own requirement,
  not AC-0006's and not a gate on a field read; see limit 4.
- [ ] **AC-0008.** `docs/specs/frontend-visual-authority/spec.md`'s `Status`
  line carries a **second, appended** supersession clause in the documented
  form — `(superseded in part by ADR-0132 — <what changed>; everything else
  stands)` — naming **both** parts this contract supersedes: the `Always do`
  rule at that spec's line 80 about stating rung conditions as properties the
  pack defines, and its **AC-0003a**, which pins the Requires cell to
  `recorded-human-confirmation` and which T2's edit falsifies. **The existing
  ADR-0130 clause is left exactly as it stands, trailing phrase included.**
  `everything else stands` is scoped per clause, not globally:
  `.claude/skills/new-spec/references/spec-and-plan-contract.md:328` ends every
  clause with it, and `docs/specs/sast-sca-tooling/spec.md:3` carries two
  parentheticals that each do — the only doubled record in the repository, and
  the maximum any `Status` line carries. An earlier draft of this criterion
  required the phrase's removal; that
  would have edited the annotation of a decision this contract has nothing to do
  with. **The criterion covers that one `Status` line and nothing else**:
  annotating the governance record is this contract's business, editing another
  spec's criteria list is not.
- [ ] **AC-0009.** `packs/frontend-engineering` and `packs/experience-design`
  each carry matching versions across `pack.toml`,
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, each
  strictly greater than the version its branch carried when this slice began,
  and `test_visual_authority_release.py`'s pin equals the new
  `frontend-engineering` version.
- [ ] **AC-0010.** `docs/product/changelog.md` carries a free-standing `##`
  release entry for each new version, each with a `### Highlights` subsection
  naming the rung precondition.

## Follow-ons

none

## Inherited obligations

AC-0012, AC-0013 and AC-0014 arrived here on 2026-09-30 from
[`visual-target-field`](../visual-target-field/spec.md), which retired them as
AC-0005, AC-0006 and AC-0007. The reason is this contract's own subject: gating
`converge`'s compositional-commitments write drops an approved-but-unconfirmed
target off the `approved-visual-target` rung, because that rung resolves from
the recorded composition rather than from the field. Landing that in a slice
whose stated outcome was that nothing downstream changes would have moved a rung
with nothing shipped to explain it. Here the rung change, the gating and the
carrier migration land together.

## Assumptions

- `visual-target-field` ships first. If it does not, AC-0001 states a condition
  on a field no template produces, and this contract cannot start.
