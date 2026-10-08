# Spec: Typed discovery pointers

- **Status:** Approved
- **Approved:** 2026-10-08 by the repository owner, spec and plan together, after adjudicated shaping findings were refuted, a clean adversarial review, and a passing final alignment check.
- **Owner:** Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 D2 and its errata; RFC-0103 D1–D3 and its 2026-10-08 errata; ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> `Agent Rules`, `Testing Strategy`, and `Acceptance Criteria` are contract.
> `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`, and `Assumptions`
> are working material.

## Outcome

Authors name an intent-valued spec `Discovery:` with the intent's registered kind and slug, without losing its delivery relation or closure parent. Research and notes references remain repository-path provenance, while changed specs cannot introduce an untyped or unresolved intent pointer.

## What Changes

- The delivery resolver admits `outcome:`, `opportunity:`, and `capability:` Discovery targets alongside its existing `intent:` and intents-path forms.
- Discovery writers emit typed intent targets and repository paths for non-intent provenance.
- The shared forward check gains its `Discovery:` field rule.
- A one-time, derived sweep converts legacy intent-valued Discovery headers.
- The shipped delivery contract's status annotations identify the supersession of AC-0001, AC-0007, and AC-0010 by RFC-0106 D2; this spec owns the changed behavior.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current resolver contract | Additional admitted intent forms affect both consumers | Resolver source/docstrings and Core construction tests | Core maintainer | Resolver fixtures, closure-parent integration, copy pins | All pinned copies support the new forms |
| Historical contract pointer | Readers of the frozen delivery record need the accepted decision | Status lines in `docs/specs/intent-delivery-traceability/spec.md` and `plan.md` | Core maintainer | Status-only diff review | Both point to RFC-0106 D2 and name the three affected criteria; frozen bodies remain unchanged |
| Authoring procedure | The template and guides instruct new Discovery values | `packs/core/.apm/skills/new-spec/`; `guides/core/how-to/write-the-contract.md`; applicable inventory-proven writer surfaces | Owning pack maintainers | Source-form pins and guide lints | Typed intent authoring and path provenance are explicit |
| Current architecture | Resolver admission is an existing runtime boundary | `docs/architecture/work-intake-and-artifact-routing.md` | Architecture maintainer | Whole-page comparison with source | The living resolver description admits the registered intent kinds |
| Migration and verification | The sweep and consumer observations need stable evidence | `notes/verification-ledger.md` | Implementer | Derived manifest, before/after relations, zero-diff repeat, gates | Ledger binds evidence to the slice revision |
| Release history | Core runtime and writer behavior change | `docs/product/changelog.md`; touched pack/plugin versions | Owning pack maintainers | Catalogue verify and release checks | Outcome-led release entry names typed Discovery support |

## Agent Rules

### Always do

- Use the target's `Slug:` and RFC-0103 D2 registered kind when writing an intent-valued Discovery pointer; `Kind:` takes precedence over `Level:`.
- Change the canonical resolver source at `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`, then synchronize every copy the copy-pinning test requires at landing time.
- Reuse the single `work-loop` forward check at `scripts/lint-graph-pointers.py`; add only this field's rule when it already exists.
- Derive the migration cohort from current spec preambles. Rewrite only resolvable, untyped intent-valued Discovery headers, preserving their target identity.
- Preserve the resolver's relation schema, canonical endpoint identifiers, feature-delivery policy, confinement, and diagnostics outside the admitted-form change.
- Land one slice PR straight to the default branch. Resolve support precedes typed writer and corpus changes inside that PR.

### Ask first

- A migration candidate has a missing, retired, or ambiguous intent target, or no determinable registered kind.
- A required resolver repair changes relation semantics beyond admitting the registered intent-reference prefixes.
- Commit or push any part of this work.

### Never do

- Type research or notes provenance as a graph node, or sweep non-intent Discovery values.
- Change `Contract:`, registry registration, navigator trust labels, or another slice's contract.
- Add parity checks against other readers or edit `docs/specs/intent-navigation/spec.md`.
- Rewrite the frozen delivery spec or plan bodies. Their status lines alone carry the agreed supersession pointer.
- Add a dependency, pack, top-level directory, relation type, diagnostic code, or cross-skill import.
- Edit generated adapter projections by hand.

## Testing Strategy

- **TDD — resolver admission (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005):** existing resolver suites exercise all four intent prefixes, legacy paths, non-feature targets, provenance, malformed/unsafe/missing values, and actual closure-parent lookup. This is an admitted-form extension, not reader parity work.
- **TDD — forward check (AC-0006, AC-0007, AC-0008):** changed-spec fixtures exercise the shared check's Discovery rule and its inherited changed-artifact selection and read-only envelope.
- **Goal-based authoring and migration (AC-0009, AC-0010, AC-0011):** inventory-derived source checks and a current-corpus manifest prove writer form and a target-preserving, repeatable sweep.
- **Goal-based integration (AC-0012):** projected resolver/check invocation and catalogue verification prove delivery of the changed artifacts.

## Acceptance Criteria

- [ ] **AC-0001.** For each registered intent prefix (`intent`, `outcome`, `opportunity`, `capability`) and the legacy repository-relative intents-path form, a Discovery value naming a unique live feature intent with `Decomposed: <date> spec` produces the same direct-delivery relation as the legacy path to that intent. Relation identifiers and basis retain the delivered resolver schema. This is the superseding behavior for `intent-delivery-traceability` AC-0001.
- [ ] **AC-0002.** A Discovery value with any admitted intent prefix that resolves to a live non-feature intent returns contextual provenance carrying the resolved intent's canonical identifier; it produces no feature-delivery relation. Non-intent provenance, including repository paths to research and notes files, retains contextual-provenance treatment. This is the superseding behavior for that contract's AC-0007.
- [ ] **AC-0003.** Every admitted intent prefix is intent-shaped for the delivery resolver's malformed, unsafe, ambiguous, and missing-target handling. Those cases retain the existing diagnostic and closure-refusal policies. A non-intent Discovery value remains provenance; an unsafe non-intent value is emitted without its target. This is the superseding behavior for that contract's AC-0010.
- [ ] **AC-0004.** After replacing a valid path-valued Discovery with its registered typed form, `close-work` retains the same resolved intent parent. Fixtures include the two feature-level outcome targets of `finding-response-receptacle` and `finding-response-scoring`, and a non-feature intent target.
- [ ] **AC-0005.** Every resolver copy named by the current copy-pinning test is byte-identical to the canonical source. The required set is derived at the slice's landing revision and includes a navigator copy if that copy exists then.
- [ ] **AC-0006.** Outside AC-0007's non-pointer cases, the shared check refuses a selected spec's intent-valued Discovery unless it is a typed reference naming one live intent with that intent's registered kind and slug. Intent-valued forms include the four intent prefixes, repository paths under `docs/product/intents/`, markdown links resolving there relative to the spec, and a bare slug matching a live intent. Untouched legacy specs produce no Discovery field violation.
- [ ] **AC-0007.** An absent, blank, comment-only Discovery, or one whose first word is `none` in any letter case, produces no field violation. A non-intent Discovery value contributes no field violation under this rule and produces no forward-check graph edge.
- [ ] **AC-0008.** The Discovery rule follows the shared check's selection and result contract in `graph-well-formed-authoring` AC-0001, AC-0002, AC-0006–AC-0008, AC-0011, and AC-0012, including when this slice creates the shared machinery first. This is an implementation obligation for the shared check, not a prerequisite on the sibling slice's delivery.
- [ ] **AC-0009.** Every source surface the current writer inventory identifies as emitting or instructing a populated Discovery value emits the target's registered typed form for an intent and a repository-relative path for non-intent provenance. Instruction, template, example, and generated-copy roles are recorded separately.
- [ ] **AC-0010.** For every resolvable untyped intent-valued Discovery in the derived current cohort, the sweep changes only that header value to the registered typed reference for the same live intent. No such untyped value remains after the sweep. Non-intent provenance and spec bodies are byte-unchanged.
- [ ] **AC-0011.** Running the sweep again against its completed cohort produces no file changes. An unresolved candidate stops migration for that candidate and is reported to the owner rather than being guessed or silently counted as complete.
- [ ] **AC-0012.** The self-hosted resolver and shared forward check support the new typed Discovery fixture after projection. Catalogue verification reports no projection drift.

## Follow-ons

None within RFC-0106 D2. Discovery edges remain `pointer_unchecked` under the unchanged navigator contract.

## Assumptions

None.
