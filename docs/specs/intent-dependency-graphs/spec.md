# Spec: Intent dependency graphs

- **Status:** Approved
- **Approved:** 2026-10-08 by the repository owner, spec and plan together, after a clean shaping review and a clean adjudicated adversarial review.
- **Owner:** Platform Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 D3; RFC-0105 D1–D5; RFC-0103 D2; ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none — the navigator's versioned query envelope is contracted here and in the inherited navigator spec.
- **Shape:** mixed

> **Spec contract:** Agent Rules, Testing Strategy, and Acceptance Criteria define this delivery's obligations. Outcome, What Changes, Durable Outputs, Follow-ons, and Assumptions orient the work. The plan owns construction strategy.

## Outcome

A maintainer or agent can follow an intent's prerequisites and dependents in a directed graph, through bounded JSON, readable text, or the offline intent navigator. Each view distinguishes recorded dependency pointers from parentage, related edges, and an enforcing workflow's readiness decision.

## What Changes

- Intent `Depends on:` pointers gain a read-only dependency view in `navigate-intents`.
- Typed pointers and legacy repository paths resolve to the same intent identity.
- The bounded query gains a `dependencies` operation; the offline view gains dependency selection and traversal.
- Faults and cycles remain visible alongside usable dependency edges.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence and closeout |
| --- | --- | --- | --- |
| Current user procedure | `guides/core/how-to/navigate-intents.md`, supplied by slice 1 | Core maintainer | Dependency examples, direction legend, legacy support, and coverage boundary pass the guide checks and match executable fixtures. |
| Navigation architecture | `packs/core/DESIGN.md` | Core maintainer | Describes one navigator derivation and the distinction between dependency display and enforcement; no new shared registry or renderer. |
| Contract extension | This spec and plan; inherited navigator/export status pointers when applicable | Core maintainer | Explicit extension references resolve without rewriting frozen bodies. |
| Executable proof | The Core navigator's existing test/evaluation surfaces plus the new dependency cases | Implementer | Targeted contract, rendered-view, safety, and activation results cover the criteria below. |
| Release and distribution | Core pack/plugin manifests, `docs/product/changelog.md`, supported self-host projections | Core maintainer | Matching version bump, outcome-led Highlights, catalogue verification, and projected dependency fixture. |
| Verification record | `notes/verification-ledger.md` in this spec directory | Implementer | Records corpus characterization, task evidence, browser evidence, and slice PR gate runs. |

## Agent Rules

### Always do

- Extend the navigator's existing derivation and export surfaces. Inherit [intent-navigation](../intent-navigation/spec.md)'s node admission, preamble boundary, identity, integrity refusals, envelope, and confinement rules, and [intent-navigation-export](../intent-navigation-export/spec.md)'s publication and offline-safety rules.
- Treat dependency values as untrusted data. Show the header-only coverage boundary and each pointer's basis.
- Use RFC-0106 D3 as the canonical authoring form. Legacy path acceptance is this reader's compatibility rule.
- Apply this extension after slices 1 and 4. This spec owns the extension of the navigator's admitted-field and operation contracts; it does not retroactively edit an approved or frozen predecessor body.

### Ask first

- Changes to admitted artifact populations, dependency enforcement, or migration ownership require an owner decision.
- Commit or push only with explicit permission.

### Never do

- Read workspace `needs` entries, decide scheduling/readiness/closure, or infer a dependency from parentage, relatedness, status, or prose.
- Add a new skill, renderer, persistence layer, runtime dependency, or cross-skill import.
- Rewrite dependency headers or migrate legacy records. FEAT-0034 owns enforcement and migration.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0012, AC-0013):** Fixture-driven query and text tests prove the dependency interpretation and bounded outputs. Fixtures carry independently written node, edge, and diagnostic expectations. A recorded real-input corpus characterizes typed and path references before refusal rules are finalized.
- **Rendered and browser checks (AC-0009, AC-0010, AC-0011):** Use the offline export, including keyboard-only operation and hostile dependency text. The established export harness is reused after its prerequisite lands.
- **Goal-based integration and activation checks (AC-0014, AC-0015):** Use the pack's existing evaluation, projection, guide, and catalogue checks. Per-task checks are separate from the final slice PR gates.

## Acceptance Criteria

- [ ] **AC-0001.** Only an intent's active preamble `Depends on:` field produces dependency pointers. Every repeated occurrence is read as a comma-separated list with preamble comments hidden. Empty fields, comment-only fields, and a field whose first word is `none` produce no pointer. Body text and other pointer fields produce no dependency edge.
- [ ] **AC-0002.** An RFC-0103 typed reference resolves only to a live intent with that exact registered kind and slug, using the navigator's inherited node identity. The resulting edge runs from the waiting intent to its prerequisite. References to a live non-intent artifact produce an `outside_scope` diagnostic, not an intent edge.
- [ ] **AC-0003.** A legacy repository-relative path beneath `docs/product/intents/` resolves to the live intent in that file, through inherited confined reads. Paths with absolute roots, traversal segments, backslashes, or a target outside that collection are refused as `unparseable`. Bare slugs, filename ordinals alone, and markdown links are not accepted dependency values.
- [ ] **AC-0004.** Within the admitted intent prefixes, malformed values return `unparseable`; a typed prefix differing from a live intent's registered kind returns `wrong_kind`; a value naming only a tombstone returns `retired`; and one naming no intent returns `dangling`. Each faulty value is reported for its source intent without removing other usable edges. Inherited corpus-integrity failures still fail the whole operation.
- [ ] **AC-0005.** Each distinct waiting-intent/prerequisite pair appears once, even when repeated or expressed in both accepted forms. Its basis identifies `Depends on:` and every distinct contributing value with form `typed` or `path`; it carries `pointer_unchecked` trust. A self-dependency or a directed cycle among returned edges remains visible, with a `cycle` diagnostic naming that cycle's member intents; an acyclic chain produces no cycle diagnostic.
- [ ] **AC-0006.** `dependencies` accepts the inherited intent identity forms through `id`, `direction` of `prerequisites`, `dependents`, or `both`, and a non-negative integer `depth`. Defaults are `prerequisites` and depth 1. It returns the selected intent and the intents within that many hops along the chosen direction; `both` is the union of the prerequisite and dependent traversals from that intent. Returned edges are all resolved dependency edges whose endpoints are in the returned set, preserving waiting-to-prerequisite direction. Fault diagnostics authored by returned intents are included. The result states its start, direction, depth, and header-only scope. Invalid direction or missing id returns `invalid_query`; invalid depth and unresolved identities use the inherited errors. Results use the inherited query envelope and deterministic node-id ordering.
- [ ] **AC-0007.** Dependency JSON applies [intent-navigation](../intent-navigation/spec.md)'s JSON result-size rule for `tree`, `ancestors`, and `search` — its count, byte, serialization, and precedence rules — to its returned intents and dependency records; both resolved edges and diagnostics count toward the edge limit. An exceeded limit returns `result_too_large` with no partial graph and names `depth` as the bounded route. Dependency text uses that spec's byte limit for `tree` text output. Limit-boundary fixtures prove both an admitted result and a refusal.
- [ ] **AC-0008.** `dependencies` supports `--format text`. Each returned intent is identified, including an isolated start; each edge is printed as waiting-intent `->` prerequisite, and each diagnostic is printed with its source intent and state. The output states direction, depth, and header-only coverage and escapes display controls using the inherited text policy.
- [ ] **AC-0009.** The offline HTML view lets a reader select an intent, choose prerequisites, dependents, or both, and change depth. The visible dependency nodes, edges, and diagnostics equal the dependency query for the same selection and depth. The graph has a waiting-to-prerequisite arrow legend; parent and related edges are distinguishable by labels or line styles as well as color. Cycles and refused pointers are visible.
- [ ] **AC-0010.** A keyboard-only reader can select an intent, change dependency direction and depth, follow a listed prerequisite or dependent, and return to the selected intent without a focus trap. Every visible dependency edge and diagnostic has a text equivalent with the same identities, direction, and state. Controls have accessible names and a visible focus indicator.
- [ ] **AC-0011.** Dependency metadata obeys [intent-navigation-export](../intent-navigation-export/spec.md)'s offline publication and inert-content contract and RFC-0105 D4. Hostile titles or dependency values cannot execute script, supply active URLs, spoof generated trust labels, or trigger automatic network requests. Unsafe reads produce the inherited refusal instead of a successful query or export.
- [ ] **AC-0012.** Existing query operations retain their contracted node, relation, placement, and error results when dependency headers are added, changed, or faulty; comparisons exclude only inherited nondeterministic provenance. This extends the navigator's admitted fields and operation set for the dependency view, without turning dependency faults into failures of unrelated operations.
- [ ] **AC-0013.** Dependency queries leave repository bytes unchanged and have the same result with `workspace.toml` absent, present, or unreadable, except inherited nondeterministic provenance. Export writes only its explicitly selected scratch output through the inherited publication path. Neither operation rewrites `Depends on:`.
- [ ] **AC-0014.** Navigator activation evaluations accept intent dependency, prerequisite, dependent, and dependency-graph requests. Requests to enforce blocking, reorder the queue, migrate workspace dependencies, or edit an intent do not activate this read-only capability.
- [ ] **AC-0015.** The supported self-host projection answers a typed/path dependency fixture through the installed navigator and renders its offline dependency view. Core's pack/plugin versions match and increase, its changelog describes the dependency view, and catalogue verification passes. Shipped instructions and guides explain the header-only scope, legacy path acceptance, and enforcement boundary without internal governance citations.

## Follow-ons

None. FEAT-0034's already-owned enforcement and migration remain outside this delivery.

## Assumptions

- Technical: slices 1 and 4 supply the implementation and export harness this extension consumes — exact code seams and visual conventions are not available in this authoring worktree. The plan's discovery conditions stop implementation when those prerequisites are absent.
