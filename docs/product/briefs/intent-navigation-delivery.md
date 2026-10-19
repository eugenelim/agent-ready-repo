# Brief: see every intent and its artifact-backed outstanding work from the files themselves

- **Slug:** `intent-navigation-delivery`
- **Received:** 2026-10-08
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Executing
- **Ready confirmed:** 2026-10-08 by the repository owner, after a clean independent delivery-brief shaping review of revision `481476b67b4971e4a8161c414f2980339bda90fb`. Review evidence: `.context/reviews/c701093f-3a4c-4acb-9c5b-ea9268ab7ea8/2-shaping-reviewer-raw.md`.
- **Slices confirmed:** 2026-10-08 by the repository owner: slices 1 to 8, materialized as the Spec map's specs. Any material edit before the next Ready re-shapes the affected specs in the same change. Amended 2026-10-12 by the repository owner: slices 9, 10 and 11 added and slice 8 re-fitted, in the order 9, 10, 8, 11, after a clean independent delivery-brief shaping review of revision `bf268a0de309fc72`. Amended 2026-10-16 by the repository owner: slice 11 split into 11a (hand-over prompt) and 11b (readiness bridge), and slices 12 (source parts and refined style) and 13 (tree, roadmap and owners) added, in the order 12, 13, 11a, 11b.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/FEAT-0002-intent-graph-navigation.md`](../intents/FEAT-0002-intent-graph-navigation.md), re-decomposed to this brief by the owner on 2026-10-08.
- **Parent intent:** intent:intent-graph-navigation

## Outcome

A maintainer or agent can see every outstanding intent, brief, and spec that exists as an artifact, placed under its parent intent, walk the intent tree, and see which intents depend on which others. Every graph answer is derived from preamble headers when it is asked, and readiness, when shown, comes only through RFC-0108's read-only bridge, so no registry has to be kept in step and nothing is written into the repository. The views show altitude, parent, related edges, dependencies, delivery mapping, and recorded state. This is the read-only orientation surface that lets `workspace.toml` stop being the place where artifact-backed outstanding work is found. New artifacts record their graph pointers in a form the navigator resolves. A maintainer can also start a session from the offline view. Its first screen answers four questions: what can I work on next, what is open under a capability, what has no parent, and what is broken. It then hands the picked item to the right skill through a prompt the maintainer copies.

## Success metrics (optional)

- Every intent, brief, and spec whose own `Status:` is not terminal appears in the outstanding-work view, and no terminal one or template file does.
- `close-work` reaches the same parents as the navigator, through a parity-checked copy of the same derivation.
- No graph answer depends on `workspace.toml`. Readiness appears only through RFC-0108's read-only bridge, exactly as `workspace-status` reported it, and never as the navigator's own derivation.
- The owner answers the four session-start questions from the view's first screen without searching, and FEAT-0002's 4-of-6-session comparison against repository search passes on the shipped build.
- An intent dependency is shown with its direction and source field, separately from parent and related edges; invalid pointers and cycles are visible rather than omitted.

## Scope / Non-goals

**In scope:**

- The public read-only `navigate-intents` skill in the `core` pack: a header-only derivation of the intent graph, a bounded JSON query, a plain-text tree, and an outstanding-work view.
- Moving `close-work`'s intent and brief parent edges onto that derivation, through a parity-checked copy.
- Making the skills that create intents, briefs, and specs write `Parent intent:` and `Brief:` as typed references, and refusing a malformed one in any new or changed artifact.
- Typed intent-valued `Discovery:` pointers end to end under RFC-0106 D2: the delivery resolver resolves every registered kind, the writers emit the typed form, the forward check covers it, and the untyped legacy values are swept once.
- An optional `Related intents:` intent preamble field, its validation, and its display.
- An on-demand, self-contained offline HTML view written outside the repository.
- Bringing `lint-traceability`'s intent ladder classification to the navigator's preamble-only reading, with a parity check between the two.
- Read-only intent dependency graphs derived from intent-valued `Depends on:` preamble pointers, exposed through the bounded query, plain-text output, and offline HTML view.
- Headings for brief and spec nodes in the derivation, so every row can lead with a name.
- A usability-first redesign of the offline HTML view around the four session-start questions, as RFC-0108's first adopter, with the shared view stylesheet and its byte-parity gate.
- RFC-0108's read-only readiness bridge and fixed-template hand-over prompt in the offline view.

**Non-goals:**

- Retiring `workspace-status` or `workspace.toml`, or changing any registration rule. That belongs to [FEAT-0034](../intents/FEAT-0034-workspace-registry-retirement.md).
- Captured items with no artifact of their own, queue order (except slice 11's display of `work-loop`'s own dispatch mark under RFC-0108 D3, which states dispatch behaviour, not priority, and ends with first-in-list selection), dependency enforcement, and migration of workspace `needs` edges. FEAT-0034 owns their disposition under RFC-0106 D3. Slice 8 displays recorded intent dependencies without deciding dispatch readiness or replacing the blocking reader.
- `navigate-intents` writing to any intent, brief, spec, or coordination record.
- Owning or inferring the typed intent-to-delivery mapping, which stays with FEAT-0003's resolver. Slice 7 only widens the `Discovery:` forms that resolver admits, through its contract's amendment path.
- Changing the typed reference grammar, intent identity, or any status vocabulary. The brief applies an accepted grammar decision; it never makes one.
- Tracker projection.
- A shared renderer with `navigate-decisions`. RFC-0108 shares one stylesheet, not a renderer.
- Moving `work-loop` Step 0 or the session-start activation boundary to the view. FEAT-0034 owns that move, after parity.
- Any page authority to launch, write, or reach the network, under RFC-0108 D4.

## Constraints / Appetite

- Every slice is bound by FEAT-0002's [§ Settled design decisions](../intents/FEAT-0002-intent-graph-navigation.md#settled-design-decisions), the constraints in its [§ De-risk record](../intents/FEAT-0002-intent-graph-navigation.md#de-risk-record--2026-10-07), and the delivery decisions and owner Amendments in its [§ Decomposition](../intents/FEAT-0002-intent-graph-navigation.md#decomposition). RFC-0105 D1 to D5 govern the navigator.
- Publication: no `core` release publishes `navigate-intents` until slices 1, 3, and 4 have merged, because RFC-0105 D1 and D4 require a published navigator to cover related edges and to emit the offline view, and its § Experiment requires those tests to have run. The mechanism, by owner decision on 2026-10-08, is the `feature/intent-navigation` integration branch: slices 1, 3, and 4 merge into it, and the slice 4 spec owns merging it to the default branch. Slices 2 and 6 merge into `feature/intent-navigation` while it is still open, and to the default branch once slice 4 has merged it. Slices 5 and 7 merge to the default branch. Before slice 4 merges the integration branch, that branch is brought up to date by merging the default branch, and the `navigate-intents` copy of the resolver is refreshed to the default branch's resolver version in that merge, so every pinned copy matches.
- `close-work` verdict changes: the slice 2 spec carries, as its bound on which verdicts may change, the causes FEAT-0002's 2026-10-07 and 2026-10-10 owner Amendments accept, measured against a baseline taken after the `[core][2.30.1]` repair.
- Appetite: each slice is sized for one spec and one review loop. A slice that cannot reach a clean spec-mode shaping review in three rounds is cut further, not grown.
- Slices 10 and 11 are governed by [RFC-0108](../../rfc/0108-skill-html-view-standard.md) D1 to D4 and follow the advisory design in [`session-start-orientation-ia.md`](../../design/screens/session-start-orientation-ia.md), [`skill-html-views` direction](../../design/direction/skill-html-views.md) and [tokens](../../design/tokens/skill-html-views.md). They merge straight to the default branch. By owner decision on 2026-10-11, the order is: slice 9, then slice 10, then slice 8 re-fitted, then slice 11. Slice 9 merges straight to the default branch too.
- Slice 8 follows slices 1 and 4 and merges straight to the default branch after the initial navigator release. It does not add a publication prerequisite to slices 1, 3, and 4. Its spec owns the explicit amendments needed to extend the navigator's admitted fields, query contract, and export coverage; the existing slice specs are not silently broadened.

## Assumptions / Risks

- **Pre-work repairs are done.** They landed before any slice, in the `[core][2.30.1]` changelog entry and its corpus edits: the terminality reading below, and 16 spec status lines that now use the standard header. Empty brief parents now read `none`, and parent values with prose after `none` now carry the prose in a comment.
- **Status is read by its leading word.** Many status lines carry text after the status word, such as `Shipped (2026-09-11)`. `close-work`'s `closure_terminality` reads the leading word as `lint-spec-status.py` does. Slices 1 and 2, the ones that decide terminality, apply the same rule and terminal sets, never an exact string match.
- **The delivery resolver has hard limits.** Past 1,000,000 bytes per file, 64 MiB in total, or 10,000 files under the three collections, it returns `complete: false`. Its file count includes every file under `docs/specs/`, not only `spec.md`. On 2026-10-08 that was 1,688 files, so delivery mappings stop at about six times that corpus.
- **The resolver reads a brief's `Parent intent:` by its own rules.** It records a parent only when the target is a feature intent, merges values by slug, skips any value starting `none`, and does not hide multi-line comment regions. A navigator that shows brief parents must state where it matches those rules and where it does not.
- **The resolver neither lists every spec nor carries its `Status:`.** It names only specs that a relation, provenance record, or diagnostic touches.
- **The seeded brief template ships to adopters.** `packs/core/seeds/docs/product/briefs/_template.md` carries `Status: Draft` and placeholder values, and must not be counted as outstanding work.
- **The payload gives briefs and specs no heading.** On 2026-10-12 all 558 spec nodes and all 24 brief nodes carried no heading, so the redesigned rows cannot lead with a name until slice 9 adds one. Some brief titles read as sentences, for example this brief's own title.
- **A 320px check needs a true 320px viewport.** Headless Chrome on macOS enforces a wider minimum window and crops the page instead of reflowing it, so a screenshot taken that way proves nothing about 320px.
- **Header coverage differs from workspace coverage.** RFC-0106 D3 gives dependencies a typed `Depends on:` preamble home, but its migration belongs to FEAT-0034. Slice 8 reports only dependencies recorded in those headers and states that scope; it cannot claim to show every workspace dependency before migration.

## Rabbit holes (optional)

- Ordering open work by anything but recorded stage, or by `workspace-status`'s own sets, invents a priority the records do not hold (RFC-0108 D1 rule 7).
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
8. **`intent-dependency-graphs`.**
   - A maintainer or agent can see which intents a selected intent depends on, and which intents depend on it, as a directed graph in the bounded JSON query, a readable dependency listing in plain text, and the self-contained offline HTML view.
   - Read `Depends on:` only from intent preambles, with RFC-0106 D3's comma-separated RFC-0103 typed references as the canonical form. The read-only view also accepts legacy repository paths to intents, as confirmed by the owner at slice 8's assumption checkpoint. An intent-to-intent edge points from the waiting intent to its prerequisite. Parent edges and `Related intents:` remain distinct and never imply dependencies.
   - Resolve intent targets by their registered kind and slug. Show each edge's source field and pointer trust. Malformed, missing, retired, or wrong-kind intent targets, self-dependencies, and dependency cycles are visible diagnostics, not silently dropped or reported as a complete acyclic graph. Non-intent dependencies are identified as outside this view's scope, not converted into intent edges.
   - The slice's spec defines the dependency query and traversal bounds, cycle diagnostics, and compatible amendments to the navigator and export contracts. The view supports selecting an intent and following prerequisites or dependents, distinguishes dependency arrows from other relationships, and provides keyboard-accessible text equivalents in the offline view. It retains the navigator's confinement, inert-content, read-only, and no-network boundaries.
   - It reads no workspace `needs` entries, migrates no dependency records, and decides no scheduling, readiness, or closure outcome. FEAT-0034 retains the enforcing reader and migration; this slice owns the read-only presentation.
   - It needs slices 1, 4 and 10, ships as a later navigator enhancement, and merges straight to the default branch. It does not change slices 5 or 7.
   - It is re-fitted to slice 10's layout before it is built: its spec amends its view criteria to slice 10's zones, state marks and key, in the same change that starts its build.
9. **`intent-node-headings` — names for briefs and specs.**
   - The derivation gives brief and spec nodes a heading from each file's title line, within the existing bounded, confined read, as it already does for intents. The bounded query and the export carry it through their existing node shape.
   - It amends the `intent-navigation` spec's node fields, and keeps `close-work`'s byte-identical copy of the derivation in step.
   - It needs no new slice, and goes first.
10. **`intent-view-session-start` — the usability-first view.**
   - The offline view is reorganised around the four session-start questions:
     - "What can I work on next?" shows open work in a startable stage, by stage then name, and says readiness was not checked;
     - "Open under a capability" lists capabilities with the open work beneath them;
     - "No parent" lists open items with no resolved parent, by type;
     - "Broken" lists broken pointers and delivery diagnostics.
   - Rows lead with the human name and show state as a word plus a shape. The key opens on demand. The detail pane leads with state, the next step, what is open beneath, what is broken and where the item sits, with record fields last and collapsed.
   - The layout adapts by width and is checked at 320, 1280, 1680 and 2560 CSS px in light and dark, using a true 320px viewport.
   - The next step is named in plain words (which skill, and why) with no prompt; slice 11 adds the copyable prompt.
   - It ships the shared `view-base.css` and the byte-parity gate RFC-0108 D2 names, joined with the view's own layout rules into the one hashed style element. The gate is a deliberate exception to the one-component rule in Rabbit holes, as slice 7's resolver change is: it exists only to keep this stylesheet's copies identical.
   - It amends the shipped `intent-navigation-export` spec's view criteria, including AC-0035 (closed label set), AC-0037 to AC-0044 (summary, views, detail and legend) and AC-0056 to AC-0061 (keyboard, viewports and landmarks). Its confinement, inert-content, publication and no-network criteria carry over unchanged.
   - It needs slices 4 and 9, and goes before slice 8 is built.
11. **Slice 11 is split into 11a and 11b**, so the hand-over prompt does not wait for the readiness bridge.
   - **11a. `intent-view-handover-prompt` — the copyable next-step prompt.** A picked item's "Next step" shows a copy block holding a prompt from RFC-0108 D4's closed template set, with one path checked against its per-segment grammar. A Copy control copies exactly the shown prompt; when copying fails, the prompt is selected for manual copy. A record that fails the grammar gets no prompt and a plain reason. A hostile fixture covers the prompt. It needs slice 12.
   - **11b. `intent-view-readiness-handover` — the readiness bridge.** With `workspace-status` output piped to `export --readiness -`, "What can I work on next?" shows the canonical active, ready and blocked sets, and marks the item an argless `work-loop` starts, following `work-loop`'s own order. "Broken" marks each loaded record with its workspace finding `code`; a finding for a record the navigator did not load is dropped. The export treats the piped input as untrusted and follows RFC-0108 D3: a size cap, schema check, allowlisted projection and dropped locators. Bridge data only marks records the navigator loaded, and any failed check leaves readiness unchecked while the export still succeeds. It amends the export spec's agent rule "Never let the export or view code read `workspace.toml`" to admit the piped projection; the navigator still never reads that file. It needs slices 8, 10 and 11a.
12. **`intent-view-source-and-style` — source parts and the refined style.**
   - The view's script is authored as named source parts that the export joins into its one hashed script, with no library, framework or bundler.
   - The shared style takes the owner's 2026-10-16 refinement: soft zones, tinted state pills, a clearer detail card, and short fades under RFC-0108's corrected rule 9.
   - It needs slice 10, and goes before 13 and 11a.
13. **Tree, roadmap and owners.**
   - "Browse all intents" becomes an expandable tree with expand-all and collapse-all, Show (All, Open, Done) and Group (full hierarchy or by capability), with filtered-out ancestors shown dimmed as context.
   - A sixth question, "How far along is each capability?", shows top-level capabilities with child capabilities nested and progress over all work beneath: delivered, in progress and not started, with withdrawn and archived apart. It shows no health judgement.
   - The rail is grouped by job: Work, Progress, Tidy, Browse.
   - Each record's `Owner:` header joins the derivation, with owner shown on rows and an owner filter; this changes the derivation and query contract and is shaped as its own spec within the slice.
   - It needs slice 12.

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
| `intent-dependency-graphs` | <auto> |
| `intent-node-headings` | <auto> |
| `intent-view-session-start` | <auto> |
| `intent-view-source-and-style` | <auto> |
| `intent-view-tree-and-roadmap` | <auto> |
| `intent-view-handover-prompt` | <auto> |

## Governance references (optional)

- [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md) — artifact-derived navigation and gated workspace retirement; its 2026-10-12 errata entry admits RFC-0108's bridge and prompt.
- [RFC-0108](../../rfc/0108-skill-html-view-standard.md) — the usability-first standard, shared view style, readiness bridge and hand-over prompt that slices 10 and 11 adopt and slice 8 is re-fitted to. RFC-0108 adoption for this view completes with slice 11.
- [RFC-0103](../../rfc/0103-cross-artifact-reference-grammar.md) — the typed reference grammar that slices 5 and 7 enforce: `Parent intent:` and `Brief:` in slice 5, and intent-valued `Discovery:` in slice 7, through its 2026-10-08 errata entry.
- [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) — types intent-valued `Discovery:` (D2), retires registration per responsibility (D1), and gives dependencies the typed `Depends on:` preamble home consumed by slice 8 (D3).
- [The intent-delivery-traceability contract](../../specs/intent-delivery-traceability/spec.md) — the delivery resolver whose mapping slice 1 displays, and whose admitted `Discovery:` forms slice 7 widens.
- [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) — an index is generated or absent.
- [ADR-0007](../../adr/0007-ship-doc-drift-lint-as-work-loop-skill-script.md) — agent-invoked skill scripts.
- [ADR-0074](../../adr/0074-the-work-loop-owns-its-state-lock.md) — skill scripts are standard-library-only.
