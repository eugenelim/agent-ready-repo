# Spec: Frame-intent experience handoff

- **Status:** Shipped
- **Owner:** Product Engineering maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`, and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons`, and `Assumptions` are working
> material.

## Outcome

Product teams framing capability- and feature-level work can pass relevant product facts to downstream experience work when a change materially affects a human-facing digital surface. The same framing path remains usable for non-surface work and installations without Experience Design.

## What Changes

- A situational activation rule joins the `frame-intent` procedure in `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`.
- An optional Product-to-experience handoff block joins the intent prompt sheet in `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`.
- Product Engineering contract tests and frame-intent evals cover activation, exclusion, altitude, decision boundaries, and downstream-pack absence.
- Product Engineering release metadata, user guidance, and release history describe the added capability without changing any Experience Design skill.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Published behavior | The skill decides when and how the handoff appears | `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` | Product Engineering maintainers | Targeted contract tests and one consumer invocation | Activation and exclusion paths match this spec |
| Intent prompt | The optional block must be discoverable without becoming a schema | `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` | Product Engineering maintainers | Template-shape assertions | The prompt exposes the five product-fact groups and remains optional |
| Evaluation contract | The published skill needs portable behavioral examples | `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json` and `packs/product-engineering/tests/pack/` | Product Engineering maintainers | Targeted pytest and eval JSON validation | Positive, negative, altitude, and absent-pack cases are represented |
| User guidance | Adopters need to know when the handoff appears and where design starts | `guides/product-engineering/how-to/shape-a-feature-intent.md` | Product Engineering documentation maintainers | Guide contract checks and link validation in repository gates | The guide names the optional handoff without prescribing design choices |
| Release identity and history | Pack consumers receive a traceable patch release | `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, and `docs/product/changelog.md` | Catalogue maintainers | Version equality checks and catalogue verification | Matching versions and an outcome-led Product Engineering release entry exist |

## Agent Rules

### Always do

- Derive handoff facts from the current intent and, when present, the Digital Experience Contract rather than creating a second product schema.
- Apply both the altitude gate and the material-surface-effect gate before offering or emitting the handoff.
- Keep Product Engineering fields under Product Engineering ownership while allowing downstream Experience Design work to read them.
- Treat the `.apm/` change as a Product Engineering patch release: update the eval harness and keep `pack.toml` and `.claude-plugin/plugin.json` on the same new patch version.

### Ask first

- Ask before adding a handoff fact that is not already owned by the intent or Digital Experience Contract.
- Ask before changing any Experience Design, Frontend Engineering, or reviewer-agent artifact.
- Ask before widening the handoff beyond capability and feature intents.

### Never do

- Never add a new top-level product document, mandatory schema, runtime, dependency, or automatic cross-skill invocation.
- Never choose engagement mode, visual direction, typography, color, layout, motion, first-viewport composition, a signature interaction, or an implementation approach.
- Never create or amend an RFC; no file under `docs/rfc/` changes in this delivery.
- Never add identifying details or attribution from non-repository sources to tracked files, generated artifacts, branch names, commit messages, or pull-request text.

## Testing Strategy

- **Activation and exclusion behavior (AC-0001, AC-0002, AC-0003): TDD.** Pack-level contract tests read only the bounded handoff section and prove positive material-surface triggers, explicit non-surface skips, and the product-altitude exclusion.
- **Handoff content and decision boundary (AC-0004, AC-0005): TDD.** Template and skill-section assertions require the five product-fact groups and reject transfer of downstream design decisions.
- **Graceful absence and ownership (AC-0006, AC-0007): TDD plus goal-based pack wiring checks.** Tests parse `pack.toml` to prove that no Experience Design dependency or automatic integration is introduced, while eval cases exercise the degradation contract.
- **Published artifact (AC-0008): goal-based checks plus manual QA.** Targeted Product Engineering suites, catalogue verification, and one recorded frame-intent invocation establish that the shipped skill exposes the optional block on a qualifying feature request without invoking a downstream skill.
- **Governance boundaries (AC-0009, AC-0010): goal-based checks.** A confined diff check proves `docs/rfc/` is untouched; metadata and eval assertions prove matching patch versions and the required frame-intent eval additions.

## Acceptance Criteria

- [x] **AC-0001.** For a `capability` or `feature` intent, each of these independently activates the Product-to-experience handoff: creating a human-facing digital surface; materially changing a user journey, interaction, content hierarchy, or visible state; changing what a surface must prove, explain, or let a person do.
- [x] **AC-0002.** For a `capability` or `feature` intent, backend-only work, infrastructure, internal refactors, dependency changes, build work, and other changes without material surface effect skip the handoff.
- [x] **AC-0003.** A `product-vision` or `product-strategy` intent does not offer or emit the handoff, including when its subject mentions a digital surface.
- [x] **AC-0004.** The optional handoff exposes these product-fact groups: affected journey or surface; user outcome and relevant first-success behavior; product-specific mechanism or proof the interface may expose; evidence available for user-visible claims; constraints, prohibited claims, and material unknowns.
- [x] **AC-0005.** The handoff selects none of these downstream decisions: engagement mode; visual direction; typography, color, layout, or motion; first-viewport composition; a signature interaction; an implementation approach.
- [x] **AC-0006.** `frame-intent` completes the same intent-authoring flow when Experience Design is absent, without installing, invoking, or requiring an Experience Design skill.
- [x] **AC-0007.** An installed Experience Design pack can read the optional handoff without gaining authority to rewrite the intent, the Digital Experience Contract's Product Engineering fields, or any other Product Engineering-owned field.
- [x] **AC-0008.** The published change adds no top-level product document, mandatory schema, runtime, dependency, automatic cross-skill invocation, or change to visual-direction behavior.
- [x] **AC-0009.** The delivery creates or amends no RFC, and the final diff contains no path under `docs/rfc/`.
- [x] **AC-0010.** `pack.toml` and `.claude-plugin/plugin.json` carry the same new patch version, and the frame-intent eval harness contains the qualifying-feature, non-surface, product-altitude, and Experience-Design-absent cases.

## Follow-ons

none

## Assumptions

- Technical: base freshness was not established because the remote probe failed; the owner explicitly authorized work from the current local base.
- Technical: knowledge provider unavailable — the optional skill-authoring reference capability was not installed.
