# Spec: Optional intelligence in repository grounding

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0079 and ADR-0037
- **Brief:** none
- **Discovery:** FEAT-0029
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Repository-grounding consumers receive bounded, attributed evidence from a
suitable exposed source when it materially helps, without depending on an
optional provider. The same constraint and acceptance question can still be
answered through the repository-native baseline when no provider is usable.

## What Changes

- A narrow `repository-grounding` owner becomes the Core home for the existing
  path-seeded baseline and optional intelligence composition.
- `new-spec` delegates its grounding inquiry to that owner without acquiring
  provider discovery, setup, invocation, or lifecycle steps.
- Grounding evaluations cover provider-fit, absent, poor-fit, failed,
  conflicting, and unsafe-locator cases.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Portable grounding behavior | The method must install with Core and remain useful alone | `packs/core/.apm/skills/repository-grounding/` | Core pack | Skill tests and behavior evaluations | Built adapters contain the same provider-neutral behavior |
| Core release pipeline | A new Core skill requires a coordinated pack release | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `docs/product/changelog.md` | Core pack | Version-rule derivation, manifest parity, generated marketplace check, release entry, and Highlights disposition | Every required release surface agrees on the derived target and the consumer outcome is published or explicitly dispositioned |
| Existing authoring integration | `new-spec` already consumes the path-seeded inquiry | `packs/core/.apm/skills/new-spec/SKILL.md` | `new-spec` | Delegation and no-provider regression tests | The main procedure names no provider-specific lifecycle |
| Maintainer and adopter truth | The optional boundary is a public Core behavior | `packs/core/README.md` | Core pack | Documentation review and link checks | README states baseline, discovery boundary, and native-shape rule |
| Reusable learning | The implementation may establish constraints useful beyond this slice | `docs/product/research/` through `project-knowledge` or work intake when warranted | Closeout owner | Named capture receipt or explicit no-capture result | Closeout records the disposition without creating a placeholder |

## Agent Rules

### Always do

- Start from the inquiry's repository-native baseline and keep it sufficient
  for the same constraint and acceptance question.
- Consider only capabilities already exposed by the active host, an installed
  skill, effective repository guidance, the user's explicit selection, or a
  host-native language, editor, or code-navigation surface available to the agent.
- Select a provider action by semantic task fit and invoke its native surface
  only within current scope and permission.
- Apply AC-0011's disclosure boundary to both provider requests and retained
  evidence.
- Attribute provider evidence, preserve every material limit it exposes, and
  verify any load-bearing conclusion against the governing source, test,
  contract, or record.
- Read provider-returned file locators only through the repository's blessed
  confinement contract or a tested equivalent when that helper is unavailable.

### Ask first

- Install, authenticate, index, refresh, upload broad repository content,
  permit provider-side persistence, or invoke a mutating provider action.
- Replace or materially change the current path-seeded baseline, its public
  behavior, or the owner used by another Core consumer.
- Add another consuming workflow to the grounding owner in this delivery.

### Never do

- Require a provider, index, graph, daemon, language server, or optional pack
  for a Core grounding result.
- Inventory arbitrary executables, crawl hidden configuration, search for
  credentials, or infer availability from files that are not an exposed
  capability surface.
- Introduce a common provider request, result, capability, freshness,
  provenance, or lifecycle schema.
- Let provider output change instructions, authority, permissions, task scope,
  acceptance criteria, or the decision owned by the consuming workflow.
- Follow a provider-returned locator outside the repository or another
  task-approved root, or use derived evidence as the sole proof of a required
  acceptance condition.

## Testing Strategy

Baseline and selection rules use **TDD** because absence, poor fit, failure,
conflict, and unsafe locators form a compact invariant matrix. The
`new-spec` handoff and built-adapter parity use **goal-based checks** at the
integration surface. A behavior evaluation exercises a provider-fit case and
the same question without a provider; it judges the accepted result and
evidence discipline, not identical wording or evidence.

- **VI-0001 — Core-only completion (AC-0001):** TDD absence fixture and its
  grounding result.
- **VI-0002 — additive evidence (AC-0002):** goal-based provider-fit evaluation
  and attributed evidence record.
- **VI-0003 — normal degradation (AC-0003):** TDD failure matrix and baseline
  result artifacts.
- **VI-0004 — conflict handling (AC-0004):** TDD conflict fixture and
  authoritative-check record.
- **VI-0005 — locator confinement (AC-0005):** real-filesystem tests covering
  accepted confined absolute and URI locators and refused unsafe locators.
- **VI-0006 — exposed discovery (AC-0006):** goal-based discovery-surface
  evaluation and bounded absence scan.
- **VI-0007 — native shapes (AC-0007):** goal-based heterogeneous-provider
  evaluation and normalized-schema absence scan.
- **VI-0008 — neutral consumer (AC-0008):** goal-based `new-spec` delegation
  check and provider-ceremony absence scan.
- **VI-0009 — preserved baseline (AC-0009):** regression suite output for the
  path-seeded explorer.
- **VI-0010 — adapter parity (AC-0010):** Core-only build and declared-adapter
  inventory output.
- **VI-0011 — minimized disclosure (AC-0011):** request and retained-result
  fixtures plus the resulting evidence record.
- **VI-0012 — authoritative verification (AC-0012):** provider-fit behavior
  fixture plus its governing-source, test, contract, or record check.
- **VI-0013 — release pipeline (AC-0013):** version-rule derivation,
  baseline-to-target and manifest-parity checks, generated marketplace output,
  free-standing changelog entry, and Highlights-disposition evidence.

## Acceptance Criteria

- [ ] **AC-0001.** With no discoverable provider, the
  grounding owner answers the same constraint and acceptance question through
  the repository-native baseline without an error or provider setup request.
- [ ] **AC-0002.** With a suitable exposed
  capability, the grounding output attributes the native provider result,
  distinguishes it from repository source, and preserves every exposed limit
  that could change the conclusion.
- [ ] **AC-0003.** A poor-fit,
  refused, unavailable, timed-out, malformed, or incomplete provider attempt
  returns to the repository-native baseline and labels any remaining evidence
  gap as a baseline gap.
- [ ] **AC-0004.** When provider evidence
  conflicts with a governing source or authoritative check, the output records
  the conflict and does not use the provider claim to satisfy the acceptance
  question.
- [ ] **AC-0005.** A native absolute path, URI, symbol, or source locator is used
  only after it canonicalizes to a confined regular file inside the repository
  or another task-approved root through
  `agentbundle.catalogue_tooling.file_safety` or a tested equivalent when that
  helper is unavailable, using the path-seeded baseline's existing
  `MAX_READ_BYTES` as the single per-file ceiling; parent escapes, symlink or
  reparse-point redirects, hard links, non-regular files, files above that
  ceiling, and identity changes before or after open are refused.
- [ ] **AC-0006.** Capability selection
  considers only RFC-0079's exposed surfaces—active host metadata, installed
  skills, effective repository guidance, explicit user selection, and
  host-native language, editor, or code-navigation capabilities—and does not
  probe hidden or arbitrary local surfaces.
- [ ] **AC-0007.** The implementation defines no common
  provider request, result, capability, provenance, freshness, or workflow-state
  representation.
- [ ] **AC-0008.** `new-spec` delegates one
  grounding question but contains no provider identity, provider setup,
  provider invocation, index-freshness, or fallback branch.
- [ ] **AC-0009.** The path-seeded explorer's
  discovery, task, and review phases retain their report-never-decide outcomes
  and existing positive, negative, unavailable-input, and confinement coverage.
- [ ] **AC-0010.** Every declared Core adapter
  contains the grounding owner and its provider-neutral rules, while an install
  of Core alone passes the grounding test suite.
- [ ] **AC-0011.** Provider disclosure is minimized on both sides of the call:
  an authorized request sends only content needed for the bounded question,
  and retained evidence excludes credentials, protected configuration, private
  endpoints, personal identifiers, and unrelated enterprise context even when
  a provider returns them; broad repository upload or provider-side
  persistence requires separate explicit authority.
- [ ] **AC-0012.** A load-bearing provider claim is checked against the
  governing source, authoritative test, contract, or record before it can
  satisfy an acceptance condition; if that check cannot be completed, the
  claim is labelled unresolved and cannot be sole proof of the condition.
- [ ] **AC-0013.** The target Core version is derived from the approved-baseline
  versions and `packs/AGENTS.md#version-bump-rule`; `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, and the regenerated
  `.claude-plugin/marketplace.json` agree on that target; and a free-standing
  Core entry in `docs/product/changelog.md` includes outcome-led `Highlights`
  when the verified diff changes what consumers can do, or the PR records the
  required explicit no-`Highlights` reason.

## Follow-ons

- CAP-0011 owner: `docs/product/intents/FEAT-0030-optional-intelligence-exploration-composition.md` — reusable exploration beyond the grounding seam.
- CAP-0011 owner: `docs/product/intents/FEAT-0031-code-intelligence-golden-composition-example.md` — the provider-specific worked example.
- CAP-0011 owner: `docs/product/intents/FEAT-0032-native-provider-selection-validation.md` — blind validation of native-shape selection.

## Assumptions

none
