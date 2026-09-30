# Spec: visual-target rung precondition

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0131](../../adr/0131-visual-target-confirmation-is-an-explicit-state.md);
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
- A new construction test enforces the **positive exclusive property** below
  over a re-run sweep, not over a fixed file list.
- `converge`, `visualize` and `creative-direction`'s output contract are gated
  on a confirmed target — the three obligations `visual-target-field` retired
  on 2026-09-30 and handed here, because the first of them moves this very
  rung.
- `docs/specs/frontend-visual-authority/spec.md`'s `Status` records that
  ADR-0131 supersedes one of its contract-tier `Always do` rules.
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

**Three limits, each measured rather than assumed.** A trial run of the
property against this repository on 2026-09-30 produced all three; they are
recorded here so a review round does not have to rediscover them.

1. *The rung's own name is not a claim about it.* `approved-visual-target` is a
   rung identifier and contains both a target reference and the word
   `approved`, so an unrefined property fires on every list of rung names,
   including tuples inside test files. The property strips that identifier
   before testing for a cue. Stripping a name is not the same as exempting a
   file.
2. *Sentence segmentation is meaningless outside prose.* In JSON and Python a
   whole file is one "sentence", so the property would demand the field inside
   eval payloads and module docstrings. The property therefore covers Markdown
   carriers. The ten non-Markdown carriers are covered by their own packs'
   suites, which assert over parsed structure rather than over sentences —
   AC-0011 holds them to that.
3. *A gated sentence must still name the field.* AC-0012 to AC-0014 gate three
   sentences in `converge.md`, `visualize.md` and `SKILL.md`, and every one of
   them refers to a visual target and carries a confirmation cue — so the
   property applies to them like any other carrier, and each must contain the
   literal `visual_target`. **Naming the field is not reading it.** `visualize`
   can say that a target the human has confirmed is the one `converge` records
   as `visual_target: confirmed` without `visualize` reading anything; the
   sentence cites the disposition, the operation does not consult it. This is
   the same distinction that makes the rung identifier a name rather than a
   claim, in limit 1. Without this statement an implementer following
   AC-0013's "not a field read" wording would write a sentence that reds
   AC-0006 and discover the conflict only when T4 runs.
4. *The cue set is narrower than English.* A carrier phrased with neither
   `confirm` nor `approved` — "a target the team has signed off", say — is
   outside the property. It narrows the gap; it does not close it. AC-0007
   keeps the cue set in one named constant so widening it is deliberate.

Against the current tree the property identifies **29 sentences across 15
Markdown files**. That is the migration T3 owes.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md` | eugenelim | The rung condition names the field | AC-0001 holds |
| Behavioural invariant | `packs/frontend-engineering/tests/skills/frontend-engineering/` | eugenelim | The exclusive property is enforced over a re-run sweep | AC-0006, AC-0007 hold |
| Producer instruction | `packs/experience-design/.apm/skills/creative-direction/references/converge.md`, `references/visualize.md`, `SKILL.md` | eugenelim | Each gated sentence names the confirmation condition and the field | AC-0012, AC-0013, AC-0014 hold |
| Governance record | `docs/specs/frontend-visual-authority/spec.md` | eugenelim | Its `Status` names the superseded rule | AC-0008 holds |
| Release history | both packs' `pack.toml`, their `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | eugenelim | Matching versions and release entries | AC-0009, AC-0010 hold |

Retention class: repository-durable.

## Agent Rules

### Always do

- Re-run the carrier sweep as part of the change, and again at test time. The
  measured extent at authoring is 25 files and 59 loci; treat any difference as
  a discovery, not a failure.
- Normalize whitespace before sweeping. A raw line-oriented grep misses
  `frontend-reviewer.md`, where the phrase wraps mid-line.
- Keep `visual-observation.md` free of the literals `experience-design`,
  `creative-direction` and `design-system`; `test_visual_authority_precedence.py`
  reds on any of them. The field name `visual_target` is not one of them.

### Ask first

- Before raising `BODY_BUDGET` in `test_visual_authority_entrypoint.py`. The
  budget is owned by the Shipped `design-to-build-value-handoff` spec, and the
  body stands at 963 of 968 lines.
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
- **TDD — the restating carriers name it too (AC-0004, AC-0005).** Verified by
  the AC-0006 property rather than per-file, because a per-file assertion is
  the closed surface set this contract may not retry.
- **TDD — the producing surfaces are gated (AC-0012, AC-0013, AC-0014).** Each
  asserts an exact literal inside a bounded unit — one blank-line-delimited
  paragraph block, or one list item — read from the single file the criterion
  names, with the anchor's uniqueness in that file asserted rather than
  assumed. A period-delimited span of normalized text is not a bounded unit:
  adjacent structure carrying no terminal period joins it silently.
- **TDD — the non-Markdown carriers are covered (AC-0011).** Each pack's own
  suite asserts over parsed structure; one construction test guards the reached
  count against silent shrinkage.
- **TDD — the exclusive property holds (AC-0006, AC-0007).** One new test walks
  the swept scope, normalizes whitespace, splits sentences, and asserts the
  property. It must red when a carrier states the condition without the field:
  the plan carries a mutation check that proves it does, because a sweep test
  that finds nothing passes for both the right and the wrong reason.
- **Goal-based check — governance (AC-0008).** A literal assertion over the
  superseded spec's `Status`.
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
- [ ] **AC-0005.** No carrier states that a visual target's *presence* alone
  resolves the rung: within the swept scope, no sentence contains a
  visual-target reference together with the literal `exists` or `present` as
  the stated sufficient condition, unless it also contains `visual_target`.
- [ ] **AC-0006.** A construction test enforces the positive exclusive property:
  over a whitespace-normalized sweep of the Markdown files under `packs/`,
  `guides/`, `web/src/content/`, `tests/` and `docs/design/`, every sentence
  matching `visual[ _-]target` that also contains a confirmation cue — after
  the rung identifier `approved-visual-target` is stripped from the sentence —
  contains the literal `visual_target`. The scope is computed by the test at
  run time from those roots; no file list is embedded.
- [ ] **AC-0007.** That test names its confirmation-cue set explicitly in one
  module-level constant, and its docstring records that a carrier stating the
  condition with no cue from that set is outside the property.
- [ ] **AC-0011.** The ten non-Markdown carriers — the four eval payloads and
  six test modules the sweep reports — name the field where they assert the
  rung's precondition, each verified by its own pack's suite over parsed
  structure rather than by the sentence property, and a second construction
  test asserts that the count of non-Markdown carriers the sweep reaches has
  not silently fallen.
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
  satisfies AC-0006, which requires the literal and not a read. See
  § The mechanism, and its limits, limit 3.
- [ ] **AC-0014.** In `creative-direction`'s `SKILL.md` — that file read
  directly, not a concatenation of the skill's files — the list item beginning
  `- **Approved visual target**` contains the literals `the human has
  confirmed` **and** `visual_target: confirmed`, and that item occurs exactly
  once in that file. The second literal is AC-0006's requirement, not a gate on
  a field read; see limit 3.
- [ ] **AC-0008.** `docs/specs/frontend-visual-authority/spec.md`'s `Status`
  line names ADR-0131 and the superseded `Always do` rule about stating rung
  conditions as properties the pack defines.
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
