# ADR-0118: `architect-design` authors from three scope-routed model-first templates, not one generic design doc

- **Status:** Proposed
- **Date:** 2026-09-18
- **Areas:** architecture, documentation
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0035 (the grounding discipline this authoring model keeps); ADR-0032 (the workload-class overlay axis the conditional overlays route on)

## Decision summary

- **Decision:** `architect-design` will author from three scope-routed, model-first templates, and this record fixes every shared name the four delivery slices use.
- **Because:** the slices land separately, so a name invented twice diverges silently and no gate catches it.
- **Applies to:** `packs/architect/.apm/skills/architect-design/` — its assets, its routing, and the document-architecture gates that read its output. Nothing outside the skill.
- **Tradeoff accepted:** the names are fixed before the templates that use them exist, so a name that reads badly in slice 1 costs an amendment here rather than a local rename.
- **Revisit if:** a slice cannot implement a named element as named, or a fourth architectural scope appears that none of the three templates fits.

## Context

`architect-design` today offers one generic design-doc template. The move to a
model-first authoring model — where a document leads with the model and the
rationale follows — is being delivered in four slices by separate sessions:

- **Slice 0** (this record's own change) removes the test brittleness that
  blocks slice 1 and fixes the shared names.
- **Slice 1** replaces the single template with three scope templates.
- **Slice 2** adds the document-architecture gates.
- **Slice 3** routes the conditional overlays.

Two constraints shape what this record has to carry.

The slices do not share a session, so every name one slice writes and another
reads has to be settled in one place first. Nothing mechanical reconciles them:
a template section renamed in slice 1 and a gate written against the old name in
slice 2 both pass their own suites.

The corpus ontology is pinned by exact equality in
`packs/architect/tests/pack/test_architecture_lenses_corpus.py` —
`EXPECTED_CONCEPTS` near lines 17 and 156, and `EXPECTED_INDEXES` with the
manifest counts near lines 79 and 211. A new concept file or category fails that
equality and drags the generated indexes and `.okf-generated.json` along with it.
So the scope routing has to live inside the skill or it cannot ship at all.

## Decision

We will author `architect-design` output from three scope-routed, model-first
templates, and the names below are binding on every slice.

- **D1:** Three template assets live under
  `packs/architect/.apm/skills/architect-design/assets/`:
  `application-system-design.md`, `subsystem-design.md`, and
  `architecture-change-design.md`.
- **D2:** `design-doc.md` is retained as a non-routed compatibility pointer. It
  is never deleted and never renamed, because adopters may reference it.
- **D3:** The subsystem template's section spine is, in order: 1 Scope and
  Context, 2 Structural Model, 3 Runtime Model, 4 Contracts and Invariants,
  5 Data and State, 6 Deployment and Operations, 7 Quality Scenarios and
  Verification, 8 Implementation Mapping, 9 Decisions, Alternatives, and Risks,
  10 Rollout, Migration, and Reversal, 11 Open Questions. Section 11 is
  conditional: omit it when there are no open questions. Two shape rules bind
  every section: it opens with the question it answers, and any model it
  carries precedes that model's rationale. The **section names** above are the
  fixed shared vocabulary; the **wording of each opening question** is not
  fixed here and is slice 1's to author, because only the template it lives in
  determines how the question is phrased.
- **D4:** The decomposition criteria are named `D1` through `D6`. A child
  subsystem earns its own document when it meets `D1` plus at least one other
  criterion:

  | ID | Criterion |
  | --- | --- |
  | `D1` | A live architectural decision of its own. Mandatory, and also the recursion's stopping rule. |
  | `D2` | Crosses a trust, identity, data-ownership, or deployment boundary that differs from the parent's. |
  | `D3` | An independent release or failure unit. |
  | `D4` | A different system shape or workload class, so a different overlay applies. |
  | `D5` | Different owners or reviewers. |
  | `D6` | Its own quality scenarios, rather than inherited ones. |

  These six IDs belong to the skill. They are unrelated to the **D1**–**D6**
  constraint addresses of this record, which exist only here; the criteria are
  written in backticks throughout this file to keep the two apart.

  Three cases are refusals: `D1` is unmet; the split would give one contract two
  homes; or the child is only large, not distinct. **Size alone never justifies
  a split.**
- **D5:** The document-architecture gates are `DA1` through `DA10`, and their
  mechanizability is fixed here because it decides how slice 2 may phrase each
  one:

  | ID | Gate | Mechanizability |
  | --- | --- | --- |
  | DA1 | Present-tense body | Hybrid |
  | DA2 | Semantic references | Hybrid |
  | DA3 | Paragraph budget | Mechanizable |
  | DA4 | Model before explanation | Hybrid |
  | DA5 | One concern, one home | Judgment-only |
  | DA6 | Settled decisions removed | Hybrid |
  | DA7 | Diagram states one question at one zoom | Hybrid |
  | DA8 | Build mapping complete | Hybrid |
  | DA9 | Evidence separated, not accumulated | Hybrid |
  | DA10 | Size trigger invokes the decomposition rubric | Mechanizable |

  A hybrid gate admits a structural precheck, but the pass/fail call is a
  reviewer's, so slice 2 phrases it as a reviewer check rather than a lint.
  DA5 is judgment-only: text similarity must not decide it. DA10 is a trigger
  that invokes the `D1`–`D6` rubric; it is not itself a split authority.
- **D6:** Architectural **scope** is skill-level routing inside
  `architect-design`. It is not a new OKF concept, and it is not a new OKF
  category. No concept file and no category is added.

## Decision drivers

- **Cross-slice name stability.** Three later changes read these names from
  three separate sessions; nothing reconciles a divergence.
- **Mechanizability honesty.** A gate phrased as a lint that no lint can decide
  either ships a check that never fires or a check that fires on the wrong
  signal. Classifying DA1–DA10 now stops slice 2 from having to guess.
- **Adopter continuity.** An adopter's existing reference to `design-doc.md`
  keeps resolving.
- **Corpus cost.** Routing inside the skill avoids the exact-equality corpus
  pins entirely; a new concept or category would fail them and pull the
  generated indexes and `.okf-generated.json` into scope.

## Consequences

**Positive:**

- Slices 1–3 can proceed independently, each citing a single fixed set of names.
- Slice 2 knows, before it starts, which of its ten gates may be a lint (DA3 and
  DA10) and which must read as a reviewer check (the other eight).
- The corpus ontology and its generated projections stay untouched.

**Negative:**

- The names are fixed before the templates exist, so slice 1 cannot rename a
  section locally; a name that reads badly needs an erratum here first.
- Retaining `design-doc.md` leaves an unrouted asset in the directory that a
  reader may mistake for a fourth scope. Slice 1 owns saying, in the asset
  itself, that it is a pointer.
- Eleven section names, six decomposition criteria, and ten gate IDs are more
  vocabulary than the skill carries today.

**Revisit if:** a slice cannot implement a named element as named, or a fourth
architectural scope appears that none of the three templates fits.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** each of slices 1–3 uses these names exactly, and its reviewer
  compares the slice's artifacts against this record. Slice 2 additionally
  implements DA3 and DA10 as mechanical checks and the remaining eight as
  reviewer checks. `packs/AGENTS.md` forbids shipped pack content from citing
  this catalogue's internal records, so a slice states the rule directly in
  `packs/` and cites `ADR-0118` only in repository-level material.
- **Owner:** the `architect` pack maintainer.

## Alternatives considered

- **Keep one generic template and add scope as a routing note inside it:**
  rejected against *cross-slice name stability* and the model-first goal. One
  template cannot lead with a structural model for a subsystem and a change
  narrative for an architecture change; the routing note would restate, not
  resolve, the difference.
- **Introduce scope as a new OKF concept or category:** rejected against
  *corpus cost*. `test_architecture_lenses_corpus.py` pins `EXPECTED_CONCEPTS`,
  `EXPECTED_INDEXES`, and the manifest counts by exact equality, so this adds
  the generated indexes and `.okf-generated.json` to every slice that touches it
  for no routing benefit — the routing is skill-level either way.
- **Rename or delete `design-doc.md` once the three templates land:** rejected
  against *adopter continuity*. The rename is invisible to an adopter's existing
  reference until it breaks.
- **Let each slice name its own elements and reconcile at the end:** rejected
  against *cross-slice name stability*. Reconciliation is a fourth change with
  no gate behind it, and the divergence is silent until a reader hits it.
- **Declare all ten document-architecture gates mechanizable:** rejected against
  *mechanizability honesty*. DA5 in particular would fall to a text-similarity
  proxy, which decides a different question from the one the gate asks.

## References

- `packs/architect/tests/pack/test_architecture_lenses_corpus.py` — the
  exact-equality corpus pins that D6 avoids.
- `packs/AGENTS.md`, *Shipped pack content carries no internal-governance
  citations* — why a slice states the rule in `packs/` rather than citing this
  record there.
