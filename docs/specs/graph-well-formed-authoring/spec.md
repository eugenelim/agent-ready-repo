# Spec: Graph well-formed authoring

- **Status:** Approved
- **Approved:** 2026-10-08 by the repository owner, spec and plan together, after clean shaping and adversarial reviews and a passing final alignment check.
- **Owner:** Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0103 D1–D3 and its 2026-10-08 errata; ADR-0007; ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> `Agent Rules`, `Testing Strategy`, and `Acceptance Criteria` are contract.
> `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`, and `Assumptions`
> are working material.

## Outcome

Authors and agents create intent parents and spec-to-brief pointers that name existing nodes with typed references. A check catches bad pointers in changed artifacts without requiring a cleanup of untouched legacy files.

## What Changes

- One shared forward check, owned by the Core `work-loop` skill, covers `Parent intent:` and `Brief:`.
- Authoring surfaces with a remaining grammar gap emit typed references.
- The seeded brief template and its companion example describe `Parent intent:` as a resolved parent pointer.
- Work-loop completion and repository CI invoke the check against a supplied Git base.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Authoring contract | Authors need field meaning and the forward-only boundary | `guides/core/reference/product-brief-fields.md`; `guides/core/how-to/write-the-contract.md` | Core maintainer | Guide lints and source-form checks | Guides explain typed authoring and legacy reader compatibility |
| Portable procedure | Adopter work-loops need the same check | `packs/core/.apm/skills/work-loop/SKILL.md` and `scripts/lint-graph-pointers.py` | Core maintainer | Changed-artifact CLI fixtures and projected invocation | The shipped skill invokes its bundled check |
| Brief template | New briefs carry a parent pointer | `packs/core/seeds/docs/product/briefs/_template.md`; `author-delivery-brief/examples/shape-a-outcome-brief.md` | Core maintainer | Authoring-surface content pins | Both descriptions agree with the field's parent meaning |
| Verification | Selection, refusal, and authoring evidence remain available | `notes/verification-ledger.md` | Implementer | Targeted suites, local lint gate, slice-PR CI run identifiers | Ledger binds evidence to the reviewed revision |
| Release history | Portable Core content changes | `docs/product/changelog.md`; Core pack and plugin versions | Core maintainer | Catalogue self-host and verify | Release entry names the check and its forward-only scope |

## Agent Rules

### Always do

- Apply RFC-0103's typed-reference grammar to authors; retain existing readers' legacy path fallbacks.
- Derive remaining writer gaps from current source surfaces. Reuse the shipped grammar migration's inventory method; do not redo converted writers.
- Validate every active occurrence of a governed field in a selected artifact's preamble, above its first `## ` heading. Hide HTML comments and remove surrounding backticks before deciding its value.
- Resolve pointers within their field's target collection. Intent identity comes from `Slug:`; the registered kind follows RFC-0103 D2, with `Kind:` taking precedence over `Level:`.
- Use the existing confinement helper for every artifact read. Reference text selects an indexed node and never opens a path.
- Land this slice as one PR to the default branch. Its plan tasks are ordered commits inside that PR.

### Ask first

- Change the grammar, collection boundary, or governed fields after approval.
- Repair a writer gap whose outcome requires changing a reader or another slice.
- Commit or push any part of this work.

### Never do

- Check pointers in untouched legacy artifacts, or sweep their values in this slice.
- Add `Discovery:` enforcement; that belongs to `typed-discovery-pointers`.
- Add reader-parity requirements, change `intent-navigation`, or work on another brief slice.
- Add a dependency, pack, top-level directory, persistent index, or cross-skill import.
- Edit generated adapter projections by hand.

## Testing Strategy

- **TDD — selection and field rules (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011, AC-0012):** disposable Git repositories exercise the real check over committed, staged, unstaged, added, renamed, deleted, and untouched artifacts. Small corpus fixtures distinguish typed targets, absent values, wrong kinds, retired targets, ambiguous identity, and unsafe input.
- **Goal-based authoring checks (AC-0009):** the derived writer inventory and construction pins inspect actual author-facing sources, because these writers are instructions and templates.
- **Goal-based integration (AC-0010):** a projected invocation, skill invocation pins, and repository gate registration prove that the shipped check is reachable.

## Acceptance Criteria

- [ ] **AC-0001.** Against a supplied Git base, the check selects the current versions of artifact files added or modified by the change, including staged and unstaged edits and untracked additions. A renamed artifact is checked at its destination. A deleted artifact is not read. Artifacts are intent and brief files directly under their canonical collections, and `docs/specs/<dir>/spec.md`, with the delivery resolver's admitted file and directory names; templates are excluded.
- [ ] **AC-0002.** An unchanged artifact with an untyped or unresolved governed pointer contributes no field violation, even when another artifact in the same collection changes.
- [ ] **AC-0003.** Outside AC-0005's non-pointer cases, each active `Parent intent:` in a selected artifact passes exactly when its typed reference names one live intent with the referenced registered kind and slug. A bare slug, repository path, markdown link, malformed typed reference, wrong kind, missing target, retired target, or duplicate target identity produces a violation.
- [ ] **AC-0004.** Outside AC-0005's non-pointer cases, each active `Brief:` in a selected artifact passes exactly when it is `brief:<slug>` naming one live brief. An untyped value or a typed reference naming no unique live brief produces a violation.
- [ ] **AC-0005.** For either governed field, an absent, blank, comment-only value, or a value whose first word is `none` in any letter case, produces no field violation. Text after that first word does not change this result.
- [ ] **AC-0006.** Adding or changing body text or commented field-shaped text does not create a pointer value. A selected artifact's active preamble fields are still checked when its edit is only in the body.
- [ ] **AC-0007.** A check with an unavailable Git base or an unsafe, unreadable, or invalid-UTF-8 artifact needed for selection or target resolution exits non-zero. It does not return a clean result from an incomplete inventory. A safe fixture with no selected artifacts exits zero.
- [ ] **AC-0008.** A complete check exits zero only when every selected governed value passes; otherwise it exits non-zero.
- [ ] **AC-0009.** No author-facing source in the bounded writer-candidate universe emits or instructs an untyped populated `Parent intent:` or `Brief:`. The derivation enumerates every candidate and records its instruction, template, example, generated-copy, or excluded role; an unclassified candidate or remaining untyped writer fails verification. Already-converted sources require no form rewrite.
- [ ] **AC-0010.** Installed Core includes the executable shared check, and work-loop completion invokes it against the change's base. The repository's slice-PR gate invokes the same check against its PR base. A fixture introducing an untyped pointer makes each invocation fail.
- [ ] **AC-0011.** Each field violation is identified by stable code, field name, and repository-relative artifact path. Standard output, standard error, and diagnostics surfaced by the skill contain no raw unsafe reference, absolute host path, or traceback.
- [ ] **AC-0012.** Invoking the check leaves repository file bytes unchanged.

## Follow-ons

The brief's slice 7 adds `Discovery:` to this check. No other field rule is part of this delivery.

## Assumptions

None.
