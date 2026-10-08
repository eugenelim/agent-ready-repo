# Brief: see every intent and its artifact-backed outstanding work from the files themselves

- **Slug:** `intent-navigation-delivery`
- **Received:** 2026-10-08
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Draft
- **Slices confirmed:** 2026-10-08 by eugenelim, lifecycle owner: slices 1 to 7, materialized as the Spec map's specs. Any material edit before the next Ready re-shapes the affected specs in the same change.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/FEAT-0002-intent-graph-navigation.md`](../intents/FEAT-0002-intent-graph-navigation.md), re-decomposed to this brief by the owner on 2026-10-08.
- **Parent intent:** intent:intent-graph-navigation

## Outcome

A maintainer or agent can see every outstanding intent, brief, and spec that exists as an artifact, placed under its parent intent, and can walk the intent tree by altitude, parent, related edge, delivery mapping, and recorded state. Every answer is derived from preamble headers when it is asked, so no registry has to be kept in step and nothing is written into the repository. This is the read-only orientation surface that lets `workspace.toml` stop being the place where artifact-backed outstanding work is found. New artifacts record their graph pointers in a form the navigator resolves.

## Success metrics (optional)

- Every intent, brief, and spec whose own `Status:` is not terminal appears in the outstanding-work view, and no terminal one or template file does.
- `close-work` reaches the same parents as the navigator, through a parity-checked copy of the same derivation.
- No answer depends on `workspace.toml`.

## Scope / Non-goals

**In scope:**

- The public read-only `navigate-intents` skill in the `core` pack: a header-only derivation of the intent graph, a bounded JSON query, a plain-text tree, and an outstanding-work view.
- Moving `close-work`'s intent and brief parent edges onto that derivation, through a parity-checked copy.
- Making the skills that create intents, briefs, and specs write `Parent intent:` and `Brief:` as typed references, and refusing a malformed one in any new or changed artifact.
- Typed intent-valued `Discovery:` pointers end to end under RFC-0106 D2: the delivery resolver resolves every registered kind, the writers emit the typed form, the forward check covers it, and the untyped legacy values are swept once.
- An optional `Related intents:` intent preamble field, its validation, and its display.
- An on-demand, self-contained offline HTML view written outside the repository.
- Bringing `lint-traceability`'s intent ladder classification to the navigator's preamble-only reading, with a parity check between the two.

**Non-goals:**

- Retiring `workspace-status` or `workspace.toml`, or changing any registration rule. That belongs to [FEAT-0034](../intents/FEAT-0034-workspace-registry-retirement.md).
- The three registry facts the headers cannot supply: captured items with no artifact of their own, `needs` dependency edges, and queue order. FEAT-0034 decides where they go.
- `navigate-intents` writing to any intent, brief, spec, or coordination record.
- Owning or inferring the typed intent-to-delivery mapping, which stays with FEAT-0003's resolver. Slice 7 only widens the `Discovery:` forms that resolver admits, through its contract's amendment path.
- Changing the typed reference grammar, intent identity, or any status vocabulary. The brief applies an accepted grammar decision; it never makes one.
- Tracker projection.
- A shared renderer with `navigate-decisions`.

## Constraints / Appetite

- Every slice is bound by FEAT-0002's [§ Settled design decisions](../intents/FEAT-0002-intent-graph-navigation.md#settled-design-decisions), the constraints in its [§ De-risk record](../intents/FEAT-0002-intent-graph-navigation.md#de-risk-record--2026-10-07), and the delivery decisions and owner Amendments in its [§ Decomposition](../intents/FEAT-0002-intent-graph-navigation.md#decomposition). RFC-0105 D1 to D5 govern the navigator.
- Publication: no `core` release publishes `navigate-intents` until slices 1, 3, and 4 have merged, because RFC-0105 D1 and D4 require a published navigator to cover related edges and to emit the offline view, and its § Experiment requires those tests to have run. The mechanism, by owner decision on 2026-10-08, is the `feature/intent-navigation` integration branch: slices 1, 3, and 4 merge into it, and the slice 4 spec owns merging it to the default branch. Slices 2 and 6 merge into `feature/intent-navigation` while it is still open, and to the default branch once slice 4 has merged it. Slices 5 and 7 merge to the default branch. Before slice 4 merges the integration branch, that branch is rebased onto the default branch, and the `navigate-intents` copy of the resolver is refreshed to the default branch's resolver version in that rebase, so every pinned copy matches.
- `close-work` verdict changes: the slice 2 spec carries, as its bound on which verdicts may change, the two causes FEAT-0002's 2026-10-07 owner Amendment accepts, measured against a baseline taken after the `[core][2.30.1]` repair.
- Appetite: each slice is sized for one spec and one review loop. A slice that cannot reach a clean spec-mode shaping review in three rounds is cut further, not grown.

## Assumptions / Risks

- **Pre-work repairs are done.** They landed before any slice, in the `[core][2.30.1]` changelog entry and its corpus edits: the terminality reading below, and 16 spec status lines that now use the standard header. Empty brief parents now read `none`, and parent values with prose after `none` now carry the prose in a comment.
- **Status is read by its leading word.** Many status lines carry text after the status word, such as `Shipped (2026-09-11)`. `close-work`'s `closure_terminality` reads the leading word as `lint-spec-status.py` does. Slices 1 and 2, the ones that decide terminality, apply the same rule and terminal sets, never an exact string match.
- **The delivery resolver has hard limits.** Past 1,000,000 bytes per file, 64 MiB in total, or 10,000 files under the three collections, it returns `complete: false`. Its file count includes every file under `docs/specs/`, not only `spec.md`. On 2026-10-08 that was 1,688 files, so delivery mappings stop at about six times that corpus.
- **The resolver reads a brief's `Parent intent:` by its own rules.** It records a parent only when the target is a feature intent, merges values by slug, skips any value starting `none`, and does not hide multi-line comment regions. A navigator that shows brief parents must state where it matches those rules and where it does not.
- **The resolver neither lists every spec nor carries its `Status:`.** It names only specs that a relation, provenance record, or diagnostic touches.
- **The seeded brief template ships to adopters.** `packs/core/seeds/docs/product/briefs/_template.md` carries `Status: Draft` and placeholder values, and must not be counted as outstanding work.

## Rabbit holes (optional)

- One combined spec covering all four parts reached 69 acceptance criteria and did not converge in four spec-mode shaping rounds, because each part reconciles with a different shipped component. Keep each slice to one shipped component's reconciliation.

## Delivery slices

1. **`intent-navigation` — navigator core.**
   - The derivation, the bounded query, the plain-text tree, the outstanding-work view, and the skill's activation evaluations.
   - It places a spec under an intent by the spec's own `Brief:` and intent-valued `Discovery:` pointers, resolved field-scoped and shown as pointer edges. These stay separate from the resolver's typed delivery mapping, which it displays and never re-derives.
   - It decides outstanding work through its own parity-checked copy of the leading-word rule and terminal sets. The copy is pinned to the same upstreams as `closure_terminality`, and to `closure_terminality` itself only for the spec terminal subset, which has no other home. Cross-skill imports are banned.
   - `Parent intent:`, `Brief:`, and intent-valued `Discovery:` have an accepted canonical form, under RFC-0103 and its 2026-10-08 errata entry, but no form check until it ships: slice 5 checks `Parent intent:` and `Brief:`, and slice 7 checks `Discovery:`. All three pass through the same resolution refusals. RFC-0105 D1 requires every relationship to keep its basis and trust class, so the slice 1 spec decides the trust label it shows for `Parent intent:` and `Brief:` before and after slice 5's check ships. `Discovery:` edges stay `pointer_unchecked` on purpose, after slice 7 too, because the navigator resolves them by slug without a kind check.
   - It goes first, because slices 2, 3, 4, and 6 need it.
2. **`close-work-intent-graph-convergence`.**
   - `close-work` takes intent and brief parent edges from the shared derivation.
   - It needs slice 1, and may ship in a later release.
3. **`related-intents-field`.**
   - The `Related intents:` field: its shape and corpus validation, the template and reference-guide rows, and its display in the query and the tree.
   - It needs slice 1.
4. **`intent-navigation-export`.**
   - The offline HTML view, with its confinement, inert content, source links, scale evidence, and accessibility.
   - It renders every edge type the query returns, and owns the test for related edges in the view.
   - It needs slices 1 and 3.
5. **`graph-well-formed-authoring`.**
   - The skills that create intents, briefs, and specs write `Parent intent:` and `Brief:` as typed references. Readers keep the path fallback for adopter and legacy files the check does not touch.
   - A forward-only check refuses, in any artifact a change adds or modifies, a `Parent intent:` or `Brief:` value that is not a typed reference or that names no node of its field's target type. A value whose first word is `none`, and an absent field, are not pointers and pass. It leaves untouched legacy files alone. No shipped check does this today: `intent_shape.py` treats `Parent intent:` as unconstrained. Any writer gap left after the grammar's own spec is a discovery condition for this slice's spec.
   - It updates the seeded brief template's `Parent intent:` comment, which calls the field "provenance; never interpreted", to match its reading as a parent pointer.
   - It needs no other slice.
6. **`lint-traceability-intent-parity`.**
   - `lint-traceability.py` classifies an intent's ladder kind from its preamble only, by slice 1's AC-0004 rule, instead of the first matching line anywhere in the file.
   - A parity check compares the lint's classification with the navigator's derivation over the real corpus, and fails on any difference. The spec decides the comparison unit, because the lint gives a ladder intent both an `intent:` node and a ladder node; the slug source; and how tombstones are excluded on both sides.
   - It needs slice 1.
7. **`typed-discovery-pointers`.**
   - Under [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) D2, intent-valued spec `Discovery:` pointers name the kind the traceability graph registers for their target (RFC-0103 D2). A value naming a research or notes file stays a repository path, as provenance.
   - FEAT-0003's delivery resolver resolves such a value with every registered kind, in every copy the copies test pins when it merges, kept byte-identical. Today it accepts only `intent:` or a path, so a typed `outcome:` or `opportunity:` value naming a feature intent would lose its direct-delivery relation, and `close-work` its parent, and any ladder-kind value its resolved intent. This amends the shipped `intent-delivery-traceability` contract's AC-0001, AC-0007, and AC-0010 through that contract's own amendment path.
   - The skills that write `Discovery:` emit the typed form; the forward check refuses an untyped intent-valued `Discovery:`, or one naming no live intent, in a new or changed spec; and the untyped legacy values are swept once. Slices 5 and 7 share one forward check with a rule per field: whichever lands first creates it, and the other adds its field's rule.
   - It reconciles two components, the resolver and the writers, as one outcome. That is a deliberate exception to the one-component rule in Rabbit holes: the resolver change is a single classifier branch that exists only to serve these writers.
   - It needs no other slice.

## Spec map

The Status column is derived from each spec; it is not hand-edited.

| Spec | Status |
| --- | --- |
| `intent-navigation` | <auto> |
| `close-work-intent-graph-convergence` | <auto> |
| `related-intents-field` | <auto> |
| `intent-navigation-export` | <auto> |
| `graph-well-formed-authoring` | <auto> |
| `lint-traceability-intent-parity` | <auto> |
| `typed-discovery-pointers` | <auto> |

## Governance references (optional)

- [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md) — artifact-derived navigation and gated workspace retirement.
- [RFC-0103](../../rfc/0103-cross-artifact-reference-grammar.md) — the typed reference grammar that slices 5 and 7 enforce: `Parent intent:` and `Brief:` in slice 5, and intent-valued `Discovery:` in slice 7, through its 2026-10-08 errata entry.
- [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) — types intent-valued `Discovery:` (D2) and retires registration per responsibility (D1).
- [The intent-delivery-traceability contract](../../specs/intent-delivery-traceability/spec.md) — the delivery resolver whose mapping slice 1 displays, and whose admitted `Discovery:` forms slice 7 widens.
- [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) — an index is generated or absent.
- [ADR-0007](../../adr/0007-ship-doc-drift-lint-as-work-loop-skill-script.md) — agent-invoked skill scripts.
- [ADR-0074](../../adr/0074-the-work-loop-owns-its-state-lock.md) — skill scripts are standard-library-only.
