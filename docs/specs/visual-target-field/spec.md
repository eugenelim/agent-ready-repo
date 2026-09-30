# Spec: visual-target field

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0131](../../adr/0131-visual-target-confirmation-is-an-explicit-state.md)
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

A direction artifact records its visual target's disposition in one closed
frontmatter field, `visual_target`, whose values are `none`, `unconfirmed` and
`confirmed`. `creative-direction` writes that field, and writes a target's binding claim and
its compositional commitments only where a human has confirmed the target.

One producer behaviour changes, and it reaches further than an earlier draft of
this section claimed. Today `converge` writes compositional commitments
whenever an approved visual target exists; after this slice it writes them only
for a confirmed one.

**That does move a rung, inside this slice.** No consumer reads the *field* —
that stays the successor's contract — but the live `approved-visual-target`
rung resolves from the recorded composition, not from the field. An artifact
whose target is approved but unconfirmed now has no composition to resolve and
falls to `direction-and-taxonomy`. The earlier claim that nothing downstream
resolves differently was false, and it was false in the direction that made the
change look safer than it is.

**Owner decision, not yet taken:** whether a slice that moves rung resolution
may ship with the field-read half deferred to the successor. This contract does
not start until that is answered.

## What Changes

- The direction template gains the `visual_target` frontmatter key and a
  `**Confirmation record:**` line, and its `## Approved visual target` comment
  names the frontmatter key as the canonical disposition and states the
  absent-field reading.
- `converge` writes the disposition, and writes compositional commitments only
  for a confirmed target.
- `visualize` and `creative-direction`'s own output contract scope their
  binding-boundaries instruction to a target a human has confirmed.
- The `creative-direction` eval harness covers the new field.
- The byte-pinned template excerpt inside `establish-design-intent.md` is
  re-derived so the guidebook lint stays green.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | eugenelim | The template carries the field and its closed set | AC-0001 to AC-0003 and AC-0011 hold |
| Current product truth | `guides/experience-design/how-to/establish-design-intent.md` | eugenelim | Its excerpt matches the template verbatim and carries the new material | AC-0008 and AC-0012 hold |
| Behavioural coverage | `packs/experience-design/.apm/skills/creative-direction/evals/` | eugenelim | The harness exercises the new field | AC-0013 holds |
| Release history | `packs/experience-design/pack.toml`, its `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | eugenelim | Matching versions above this slice's own baseline, and one release entry this slice authored | AC-0009 and AC-0010 hold |

Retention class: repository-durable.

## Agent Rules

### Always do

- Use the exact field name `visual_target` and the exact values `none`,
  `unconfirmed` and `confirmed`.
- Treat an absent `visual_target` as `unconfirmed`. That is the fail-closed
  default ADR-0131 fixes.
- Re-derive the guide's template excerpt in the same change as any template
  edit.

### Ask first

- Before changing the `status` field's vocabulary or meaning.
- Before adding a `visual_target` value beyond the three named here.

### Never do

- Never make any consumer read the field in this slice; that is the successor's
  contract, and shipping both at once is what four review rounds rejected.
  **Ruling on the carve-out, so an implementer does not have to guess.** The
  carve-out covers an instruction to `converge` — the operation that writes the
  field — conditioning any of its own writes on the disposition it itself
  records. That is one operation's internal ordering, not a second party reading
  a published field. It does not cover any other skill, agent, guide or rung.
  ADR-0131 anticipates exactly this: it states that the `creative-direction`
  contract suite asserts `converge` gates compositional commitments on the
  confirmed reading.
- Never write a sidecar file beside the direction artifact.
- Never add a dependency, module boundary, or top-level directory.
- Never record a person's name, handle, or contact detail in the confirmation
  record.

## Testing Strategy

**The bounded unit, defined once.** Where a criterion below says *paragraph
block*, it means one maximal run of consecutive non-blank source lines in the
named file, taken from the file the criterion names and no other. Where it says
*list item*, it means one `- ` item and its continuation lines. Both are units
the Markdown itself delimits, so a verification can isolate exactly what the
criterion describes. A period-delimited span of whitespace-normalized text is
**not** a bounded unit: adjacent structure that carries no terminal period —
a heading, a table cell, a bullet — joins it silently, which would let an
unscoped instruction pass because a scoped heading sat above it. Each such
criterion also requires its anchor to occur exactly once in the named file, so
the verification cannot silently grade a different occurrence.

- **TDD — the template carries the state and its provenance (AC-0001, AC-0002,
  AC-0003, AC-0011).** The template's bytes parse; asserted from
  `packs/experience-design/tests/skills/creative-direction/test_contract.py`.
- **TDD — the producing surfaces are scoped to a confirmed target (AC-0004,
  AC-0005, AC-0006, AC-0007).** Each asserts an exact literal inside a bounded
  unit as defined above, read from the single file the criterion names.
  Asserting the literal inside that unit, not anywhere in the file, is what
  makes removing the scope red rather than pass on some other occurrence of the
  same word.
- **TDD — the eval harness covers the field (AC-0013).** Asserted over a named
  case's `assertions` entries in the harness, not over a concatenated corpus.
- **Goal-based check — the pinned excerpt still matches and carries the new
  material (AC-0008, AC-0012).**
  `python3 tools/lint-guidebook-steps.py guides/experience-design` is the
  one-liner for AC-0008; AC-0012 is a contract-suite assertion scoped to the
  guide's fenced excerpt block, because the lint proves only that *some*
  contiguous run matches and the guide discusses the template in prose outside
  the fence.
- **Goal-based check — the release surface stays consistent (AC-0009,
  AC-0010).** `tests/conformance/test_pack_metadata.py` covers `pack.toml` to
  `plugin.json` agreement and nothing else — it never compares a marketplace
  version and never opens the changelog. AC-0009's third site and AC-0010 are
  therefore covered by one new construction test at
  `tests/roster/test_visual_target_release_surface.py`, which reads all three
  version sites and the changelog bytes. It lives in `tests/roster/` and not
  `tests/conformance/` because `tools/lint-conformance-portability.py` — which
  also runs on every PR — rejects a conformance test that names a shipped pack
  or reaches `docs/`, and this test must do both. `tests/AGENTS.md` names
  `tests/roster/` as the repository-level home.
  **Run mode, read from the workflow rather than the Make target.** An earlier
  revision claimed a green PR said nothing about these two criteria. That was
  wrong, and the error is worth naming so it is not repeated: `make
  build-check` genuinely does not invoke `make test`, but
  `.github/workflows/build-check.yml` triggers on `pull_request` and its
  carve-out step runs `python -m pytest tests/ -q` directly, which collects
  everything under `tests/`. The PR gate therefore does run this test, and no
  corpus dispatch is needed before approving the release. The start-of-work
  baseline stays a recorded manual check; the post-bump end state is what the
  new test observes.

## Acceptance Criteria

- [ ] **AC-0001.** `creative-direction-template.md`'s frontmatter carries a
  `visual_target` key whose placeholder enumerates exactly `none`,
  `unconfirmed` and `confirmed`.
- [ ] **AC-0002.** That template's `## Approved visual target` section carries
  exactly one `**Confirmation record:**` line, and after whitespace
  normalization that line is exactly:
  `**Confirmation record:** <YYYY-MM-DD> — <where the confirmation was recorded>`
  Equality, not a shape. Two weaker mechanisms were tried and both failed to
  decide the property: a denylist of `who`, `name`, `handle`, `email` passes
  `<approver>` and `<signed off by>`, and a two-slot regex with free text
  around a keyword passes `<who recorded it>` on `record` and
  `<approver name, where recorded>` on `where`. A criterion that claims to
  exclude person-identifying placeholders must actually decide it, and pinning
  the exact placeholder text is the only form here that does. The `Never do`
  rail at the top of this spec still governs what a producer writes *into* the
  record at runtime; that half is review-enforced, and this criterion does not
  claim otherwise.
- [ ] **AC-0003.** That section's comment contains the literal `visual_target`,
  names the `**Target:**`, `**Binding:**` and `**Confirmation record:**` lines,
  and contains the literal `bind nothing on their own`.
- [ ] **AC-0004.** In `references/converge.md`, the paragraph block containing
  the literal `Record the approved visual target disposition` contains all
  three closed values — `visual_target: none`, `visual_target: unconfirmed`
  and `visual_target: confirmed` — and that anchor occurs exactly once in the
  file. All three, because that block today records the no-target case as the
  bare word `none`; leaving it unwritten as a field value would make it read
  as `unconfirmed` under the absent-field rule, which is not what ADR-0131
  fixes. A whole-file containment check does not
  satisfy this criterion: once AC-0005's edit puts `visual_target: confirmed`
  anywhere in `converge.md`, a file-level check can no longer fail.
- [ ] **AC-0005.** In `references/converge.md`, the paragraph block containing
  the literal `write the selected direction's compositional commitments` also
  contains the literal `visual_target: confirmed`, and that anchor occurs
  exactly once in the file. T2 splits that instruction into its own
  blank-line-delimited block: today it sits inside a five-sentence paragraph
  covering the target path, the template copy, the `visualize` handoff and the
  fill list, so the literal could satisfy the criterion from a sentence with
  nothing to do with the gated write.
  The field-literal form is correct here and not a rail crossing: `converge` is
  the operation that writes the field, so this is its own internal ordering,
  per the ruling in `Never do`.
- [ ] **AC-0006.** In `references/visualize.md`, the paragraph block containing
  the literal `record its identity and three boundaries` also contains the
  literal `the human has confirmed`, and that anchor occurs exactly once in the
  file. The condition is the confirmation determination that operation already
  holds — `visualize` runs before `converge` writes the field, so it has no
  field to read and the field-literal form would be a rail crossing here.
- [ ] **AC-0007.** In `creative-direction`'s `SKILL.md` — that file read
  directly, not a concatenation of the skill's files — the list item beginning
  `- **Approved visual target**` contains the literal `the human has confirmed`,
  and that item occurs exactly once in that file.
- [ ] **AC-0008.** `python3 tools/lint-guidebook-steps.py guides/experience-design`
  exits zero.
- [ ] **AC-0009.** `packs/experience-design/pack.toml`, its
  `.claude-plugin/plugin.json`, and its entry in `.claude-plugin/marketplace.json`
  carry the same version, strictly greater than the recorded slice-start
  baseline in the plan's `Version baseline and target`. Comparing against
  `origin/main` would pass on the sibling slice's bump and let this slice ship
  no bump at all. All three sites are observed after the bump by the new
  conformance test, because `test_pack_metadata.py` never compares a
  marketplace version.
- [ ] **AC-0010.** `docs/product/changelog.md` carries a release entry for that
  version whose heading begins at the start of a line at exactly `## ` — a
  substring test cannot tell that from a `### ` entry nested under
  `[Unreleased]`, which the release pipeline records as never publishing — with
  a `### Highlights` subsection in which a `-` bullet names the `visual_target`
  field. The bullet form is load-bearing: the `/now/` projection extracts only
  bullets, so a paragraph is dropped silently. Asserted by the new roster test
  reading the changelog bytes. The existing `4.1.1` entry does not satisfy
  this: its Highlights describe the `frame`/`inherit` scoping fix.
- [ ] **AC-0011.** That section's comment states that an absent `visual_target`
  reads `unconfirmed`.
- [ ] **AC-0012.** Within one fenced block of
  `guides/experience-design/how-to/establish-design-intent.md` — selected as
  the single ` ```markdown ` fence whose body contains the line
  `type: creative-direction`, and asserted to be the only such fence — both the
  `visual_target` frontmatter key and the `**Confirmation record:**` line are
  present. Selecting by that property rather than by fence ordinal is the
  point: the guide carries three ` ```markdown ` fences, and the first is a
  design-principles block that no edit in this slice ever makes carry the
  field. Scoping to the fence at all is what a whole-file check cannot do,
  since the guide discusses the template in prose outside it.
- [ ] **AC-0013.** In `packs/experience-design/.apm/skills/creative-direction/evals/evals.json`,
  at least one case carries an entry in its own `assertions` list naming one of
  the three `visual_target` values as the disposition the run must write. A
  substring check over the concatenated harness does not satisfy this: it passes
  when the field name lands in a trigger query or a prose `expected_output`
  while no case asserts anything.

## Follow-ons

- eugenelim: [`visual-target-rung-precondition`](../visual-target-rung-precondition/spec.md)
  — makes the `approved-visual-target` rung require the field and removes the
  superseded prose reading from every carrier. Authored, Draft, and registered
  under `workspace.toml [backlog].open` so the pointer resolves outside this
  document. That successor is the whole justification for shipping a field no
  consumer reads, so it may not rest on this spec's prose alone.

## Assumptions

none
