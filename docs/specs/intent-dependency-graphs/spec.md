# Spec: Intent dependency graphs

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-08 by the repository owner, spec and plan together, after a clean shaping review and a clean adjudicated adversarial review. Re-fitted to the session-start view before its build started, and re-approved on 2026-10-14 by eugenelim, spec and plan together, after clean adjudicated shaping (round 6), adversarial (round 6) and security spec-stage (round 3) reviews; reports under `.context/reviews/3f9e2ddc-66e7-4d49-9e83-decaf02878e2/`.
- **Owner:** Platform Core maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 D3; RFC-0105 D1–D5; RFC-0103 D2; RFC-0108 D1; ADR-0074
- **Amended in part by:** [intent-view-handover-prompt](../intent-view-handover-prompt/spec.md) — the Never-do "Show readiness or a copyable prompt…", narrowed for the prompt only, as that spec's `Amends:` line states. [intent-view-readiness-handover](../intent-view-readiness-handover/spec.md) — its reading of export criterion 0001 and its Never-do rules "Read workspace `needs` entries, decide scheduling/readiness/closure…" and "Show readiness or a copyable prompt…", as that spec's `Amends:` line states.
- **Amends:** [intent-navigation](../intent-navigation/spec.md) criteria 0003 and 0013; [intent-navigation-export](../intent-navigation-export/spec.md) criterion 0001; [intent-view-session-start](../intent-view-session-start/spec.md) its broken-entry term and criteria 0006, 0013, 0014, 0017, 0019, 0022, 0030, 0038 and 0042. § *Amended predecessor criteria* states each change. The shipped specs are historical records and are not edited; this spec is where the amendments live.
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none — the navigator's versioned query envelope is contracted here and in the inherited navigator spec.
- **Shape:** mixed

> **Spec contract:** Agent Rules, Testing Strategy, and Acceptance Criteria define this delivery's obligations. Outcome, What Changes, Durable Outputs, Follow-ons, and Assumptions orient the work. The plan owns construction strategy.

## Outcome

A maintainer or agent can follow an intent's prerequisites and dependents through bounded JSON, readable text, or the offline intent view. In the view, a picked intent's detail shows what it waits for and what waits for it, one plain sentence per dependency, on the session-start page's layout, marks and Key. Every surface keeps recorded dependency pointers apart from parentage, related edges, and any decision about whether work can start.

## What Changes

- Intent `Depends on:` pointers gain a read-only dependency view in `navigate-intents`.
- Typed pointers and legacy repository paths resolve to the same intent identity.
- The bounded query gains a `dependencies` operation with JSON and text output.
- The view payload gains one additive `dependencies` member. The view's intent detail gains a "Dependencies" part and two record-detail groups. Broken dependency pointers and cycles join "What is broken?". The Key explains the new labels.
- Faults and cycles remain visible alongside usable dependency edges.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence and closeout |
| --- | --- | --- | --- |
| Current user procedure | `guides/core/how-to/navigate-intents.md` | Core maintainer | A dependency task covering the query, the text output and the view's "Dependencies" part, the "waits for" direction, legacy path acceptance and the header-only scope; the `--from` text says a scoped export also carries the dependency records of intents linked to the scope; the guide checks pass and the examples match executable fixtures. |
| Navigation architecture | `packs/core/DESIGN.md` | Core maintainer | Describes the dependency reading inside the navigator and the distinction between dependency display and enforcement; no new shared registry or renderer. |
| Contract extension | This spec's `Amends:` line and § *Amended predecessor criteria* | Core maintainer | Each amended criterion is named with its new wording. |
| Executable proof | The Core navigator's existing test, browser and evaluation surfaces plus the new dependency cases | Implementer | Targeted contract, rendered-view, safety, and activation results cover the criteria below. |
| Release and distribution | Core pack/plugin manifests, a changelog fragment under `docs/product/changelog.d/`, supported self-host projections | Core maintainer | Matching version bump, outcome-led Highlights, catalogue verification, and projected dependency fixture. |
| Verification record | `notes/verification-ledger.md` and `notes/screens/` in this spec directory | Implementer | Records corpus characterization, task evidence, browser, width and scale evidence, screenshots with SHA-256, reviews, and slice PR gate runs. |
| Coordination | `workspace.toml` `["ini-010".work]` | Implementer | Entry moves from `queue` to `active` when the build starts and to `shipped` when this spec ships. |

## Agent Rules

### Always do

- Extend the navigator's existing derivation, query and export surfaces. Inherit [intent-navigation](../intent-navigation/spec.md)'s node admission, preamble boundary, identity, integrity refusals, envelope, and confinement rules; [intent-navigation-export](../intent-navigation-export/spec.md)'s publication and offline-safety rules; and [intent-view-session-start](../intent-view-session-start/spec.md)'s page structure, state marks, Key, routing, width zones and access floor.
- Treat dependency values as untrusted data. Show the header-only coverage boundary and each pointer's basis.
- Use RFC-0106 D3 as the canonical authoring form. Legacy path acceptance is this reader's compatibility rule.
- Keep every glyph decorative and hidden from assistive technology, with a word as the read text, and insert record text only as text.
- This spec owns the extension of the navigator's admitted-field and operation contracts and the view criteria it amends.

### Ask first

- Changes to admitted artifact populations, dependency enforcement, or migration ownership require an owner decision.
- Any change to `close-work/scripts/intent_graph.py` or to `intent_graph.py`'s derivation output.
- Adding a question or destination to the view's navigation, or any ordering not named in these criteria.
- Commit or push only with explicit permission.

### Never do

- Read workspace `needs` entries, decide scheduling/readiness/closure, or infer a dependency from parentage, relatedness, status, or prose.
- Show readiness or a copyable prompt, launch anything, reach the network, or change the shipped content-security policy string.
- Add a new skill, renderer, persistence layer, runtime dependency, JavaScript library, or cross-skill import.
- Rewrite dependency headers or migrate legacy records. FEAT-0034 owns enforcement and migration.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0012, AC-0013, AC-0016):** Fixture-driven query, text and payload tests prove the dependency interpretation and bounded outputs. Fixtures carry independently written node, edge, and diagnostic expectations. A recorded real-input corpus characterizes typed and path references before refusal rules are finalized.
- **Scripted browser check (AC-0009, AC-0010, AC-0011, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024):** the Playwright suite `view_browser_checks.py` drives exported fixture files in headless Chromium at true viewport sizes. It is not collected by CI, so its pass at the final code commit, with the commit id, the SHA-256 of the three view assets and the count of tests run with none skipped, is recorded in the ledger.
- **Goal-based integration and activation checks (AC-0014, AC-0015, AC-0025, AC-0026):** the pack's evaluation, projection, guide and catalogue checks, the scale benchmark, the real export and the screenshots, recorded in the ledger.
- **Visual / manual QA (AC-0027):** an `experience-reviewer` pass over the rendered real export decides the design-intent outcome no script can.

## Acceptance Criteria

Terms used below:

- **Dependency fixture:** a fixture corpus holding typed and path pointers to the same intent, repeated and comma-separated fields, null and comment-only values, body and other-field decoys, a non-intent target, each fault state, a chain, a diamond, a self-dependency, a multi-intent cycle, one cycle member that also writes two faulty values, and a parent hierarchy under which a `--from` scope has a linked set holding an intent outside that scope while the corpus holds at least one edge and one diagnostic outside the linked set.
- **Step:** one hop along a resolved dependency edge.
- **All steps:** the depth equal to the number of live intents, which reaches every intent the chosen direction can reach.
- **Dependency edge record:** `{"from", "to", "field": "Depends on", "trust_class": "pointer_unchecked", "basis": {"field": "Depends on", "values": [{"value", "form", "position"}, ...]}}`, where `from` is the waiting intent, `to` its prerequisite, and `values` every distinct contributing value in first-written order. A value's `position` is the 0-based index of its first occurrence in the intent's *item list*: every non-empty comma item of every `Depends on:` occurrence that AC-0001 keeps, in file order, repeats included. Dropped fields and empty items take no index.
- **Value form:** the form the navigator's inherited classifier gives a value: one of `typed`, `path`, `bare_slug`, `markdown_link` and `unrecognized`.
- **Dependency diagnostic:** one entry of a `dependencies` result's diagnostics, in one of two shapes. A *pointer diagnostic* is `{"from", "field": "Depends on", "value", "form", "position", "state", "trust_class": "pointer_unchecked"}`, plus `reissued_as` when the state is `retired_target` and the tombstone names a reissue; its state is a fault state or `outside_scope`, and the same value written more than once by one intent is one diagnostic. A *cycle diagnostic* is `{"state": "cycle", "members": [...]}`.
- **Record order:** edge records by `from`, then `to`; pointer diagnostics by `from`, then `position`; then cycle diagnostics by their first member. Query JSON, text and the payload use this order.
- **Cycle group:** a set of live intents in which each reaches every other along resolved dependency edges, taken as large as it can be, with more than one member or one member that depends on itself. One cycle group gives exactly one cycle diagnostic, whose `members` are its node ids in node-id order.
- **Step count:** for an intent, the fewest steps from the picked or start intent along any traversal the chosen direction includes; the start is 0. For an edge, the larger of its two ends' step counts.
- **Named intent:** in the view, an intent in the payload's `nodes` is named by its display name as a link with its state mark. Any other intent is named by its node id as plain text marked "outside this export", and its node id is its name for name order.
- **Width and theme matrix:** true viewport widths of 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme.

### Reading and query

- [x] **AC-0001.** Only an intent's active preamble `Depends on:` field produces dependency pointers. Every repeated occurrence is read as a comma-separated list with preamble comments hidden. Empty fields, comment-only fields, and a field whose first word is `none` produce no pointer, and an item left empty after the comma split, as in `a, , b`, is dropped with no diagnostic. Body text and other pointer fields produce no dependency edge.
- [x] **AC-0002.** A value of form `typed` is an RFC-0103 typed reference under the navigator's inherited grammar: a registered intent kind, `brief` or `spec`, a colon, and a slug or spec directory name that passes its grammar. One with an intent kind resolves only to a live intent with that exact kind and slug, using the navigator's inherited node identity; the resulting edge runs from the waiting intent to its prerequisite. One with `brief:` or `spec:` produces an `outside_scope` pointer diagnostic, not an edge, whether or not its target exists: this view does not resolve non-intent targets. Any other prefix, a misspelled kind, or a slug failing the grammar is not typed: its form is whatever the classifier gives, and AC-0003 or AC-0004 decides its state.
- [x] **AC-0003.** A legacy repository-relative path beneath `docs/product/intents/` resolves by exact string match against the intent files the inherited confined walk admitted, and opens no file. A path naming a live intent's file gives an edge; one naming a tombstone's file gives `retired_target`; any other path beneath that directory gives `dangling`. A path beneath `docs/product/briefs/` or `docs/specs/` gives `outside_scope`. Paths with an empty, `.` or `..` segment, and paths at any other location, such as `C:/x` or `featre:a/b`, are `unparseable`. A value with a leading `/`, a backslash or a URL scheme is never of form `path`.
- [x] **AC-0004.** A value of form `bare_slug`, `markdown_link` or `unrecognized` returns `unparseable`; a typed prefix differing from a live intent's registered kind returns `kind_mismatch`; a value naming only a tombstone returns `retired_target`; and one naming no intent returns `dangling`. These are the navigator's existing state labels. Each faulty value is one pointer diagnostic for its source intent and removes no other usable edge. Inherited corpus-integrity failures still fail the whole operation. If the intent files read for dependencies differ from the derivation's live intents, because a file changed between reads, `dependencies` and export fail with `unsafe_input`, the inherited code for a file swapped during reading.
- [x] **AC-0005.** Each distinct waiting-intent/prerequisite pair appears once, even when repeated or expressed in both accepted forms. It is one dependency edge record. Every edge of a cycle group, including a self-dependency, remains an edge, and the group gives one cycle diagnostic; an acyclic chain produces none. A chain and a cycle group each longer than 2,000 intents never crash: queried from the chain's first waiting intent and from one cycle member, with `both` and all steps, the query returns a result or `result_too_large`, and the export writes its file or refuses with `export_too_large`.
- [x] **AC-0006.** `dependencies` accepts the inherited intent identity forms through `id`, `direction` of `prerequisites`, `dependents`, or `both`, and a non-negative integer `depth`. Defaults are `prerequisites` and depth 1. It returns the selected intent and the intents within that many hops along the chosen direction; `both` is the union of the prerequisite and dependent traversals from that intent. Returned edges are all resolved dependency edges whose endpoints are in the returned set, preserving waiting-to-prerequisite direction. Its diagnostics are every pointer diagnostic whose `from` is a returned intent, and the cycle diagnostic of every cycle group with at least one returned member. The result states its start, direction, depth, and header-only scope. Invalid direction or missing id returns `invalid_query`; invalid depth and unresolved identities use the inherited errors. Results use the inherited query envelope, returned intents in node-id order, and record order.
- [x] **AC-0007.** Dependency JSON applies [intent-navigation](../intent-navigation/spec.md)'s JSON result-size rule for `tree`, `ancestors`, and `search` — its count, byte, serialization, and precedence rules — to its returned intents and dependency records; both resolved edges and diagnostics count toward the edge limit. An exceeded limit returns `result_too_large` with no partial graph and names `depth` as the bounded route. Dependency text uses that spec's byte limit for `tree` text output. Limit-boundary fixtures prove both an admitted result and a refusal.
- [x] **AC-0008.** `dependencies` supports `--format text`. Each returned intent is identified, including an isolated start; each edge is printed as waiting-intent `->` prerequisite; each pointer diagnostic is printed with its source intent, state and value, and each cycle diagnostic with its members. After a header stating its scope, it lists returned intents, then edges, then diagnostics, each in the JSON order. The output states direction, depth, and header-only coverage and escapes display controls using the inherited text policy.
- [x] **AC-0012.** Existing query operations retain their contracted node, relation, placement, and error results when dependency headers are added, changed, or faulty; comparisons exclude only inherited nondeterministic provenance. This extends the navigator's admitted fields and operation set for the dependency view, without turning dependency faults into failures of unrelated operations.
- [x] **AC-0013.** Dependency queries and the dependency-bearing export leave repository bytes unchanged. Export writes only its explicitly selected scratch output through the inherited publication path. Neither operation rewrites `Depends on:`.

### View payload

- [x] **AC-0016.** The export's view payload gains one member, `dependencies`, holding `edges` and `diagnostics` in record order. A whole-corpus export holds every dependency edge record and every dependency diagnostic of the corpus. An export with `--from` holds them for the *linked set*: the in-scope intents and every intent reachable from one along prerequisites or along dependents. It holds the edges with both ends in that set, the pointer diagnostics written by its intents, and the cycle diagnostics with a member in it. Every other payload member, and the schema identifier, is unchanged for the same corpus.

### Dependencies in the intent detail

- [x] **AC-0009.** Picking an intent shows a "Dependencies" part in the detail zone, after "Where it sits" and before "Open the file"; the other parts keep their order. Picking a brief or spec shows no such part. Its lead line reads "From Depends on: headers only. This does not check whether work can start."
- [x] **AC-0017.** The part holds two labelled controls. "Show" offers "What it waits for", "What waits for it" and "Both", which select the directions `prerequisites`, `dependents` and `both`. "Steps" offers 1, 2, 3 and "All". The defaults are "What it waits for" and 1.
- [x] **AC-0018.** The part lists one line per dependency edge, reading "<waiting intent> waits for <prerequisite>". Each intent is a named intent. Lines are in ascending step count, then in name order of the waiting intent and then the prerequisite, and the part names that sort key as "Nearest first, then by name". With no edge and no diagnostic to list it reads "It waits for nothing in its Depends on: header.", "No intent's Depends on: header names it." or "No dependencies recorded." for the three choices of "Show". With no edge but at least one diagnostic it reads "No line to show. Its Depends on: values are listed below."
- [x] **AC-0019.** Below the lines, every dependency diagnostic the part's query returns is listed: pointer diagnostics in name order of their source intent, then in written order, then cycle diagnostics in name order of the member that comes first by name. A fault shows the ✕ mark with "Broken", its state label, the source as a named intent and the value written. A `cycle` shows the ✕ mark with "Broken", the label `cycle` and its members as named intents in name order. An `outside_scope` entry shows the value written and "not an intent, outside this view", with no ✕ mark. Every value written renders in its own `code` element, as the existing pointer values do, apart from every generated mark and label.
- [x] **AC-0020.** Over a whole-corpus export of the dependency fixture, for every intent, every choice of "Show" and every choice of "Steps", the part's set of waiting/prerequisite pairs, the picked intent with every intent on an edge line, and its diagnostics equal the query's edges, returned intents and diagnostics for the same id and direction, with the chosen steps as `depth` and "All" as all steps. The same holds for every in-scope intent of an export of that fixture with a `--from` scope chosen so that its linked set holds at least one intent outside `nodes`, and the whole-corpus payload holds at least one edge and one diagnostic that this export's does not.

### Broken entries and the Key

- [x] **AC-0021.** A dependency diagnostic other than `outside_scope` is a broken entry: a fault is one entry held by its source intent, and a cycle diagnostic is one entry held by each of its members. In an export with `--from`, only in-scope intents hold entries. "What is broken?" lists each such entry as a row whose context shows "Depends on:" and its state label. Within one holder, dependency entries follow its inherited entries: faults by `position`, then its cycle diagnostic. The holding intent's "What is broken" part lists it as "Depends on:" with the Key's meaning of its state, followed by the value written in its own `code` element for a fault, or the other members as named intents for a cycle. Its state line's broken count includes it. This holds whether or not `outstanding` is available, since these entries come from intent headers, not from delivery mapping. Over the `mixed` fixture, which has no `Depends on:` field, the four question counts stay 3, 2, 6 and 0.
- [x] **AC-0022.** Opening "Record details" for an intent adds two groups after the related-intents groups. "Depends on, written here" lists each distinct value the intent writes in `Depends on:` once, by `position`, with its value form, its trust class and its resolved target as a named intent or its state label, the value in its own `code` element. "Depends on, written elsewhere" lists, as named intents in name order, each intent whose resolved dependency edge names this one, with its trust class.
- [x] **AC-0023.** The Key adds the two groups of AC-0022, the state label `outside_scope`, each of the five value forms with its plain-words meaning, and a line explaining "waits for": the first intent's `Depends on:` header names the second, and the view does not decide whether either can start. Its `cycle` meaning covers both a parent loop and a dependency loop. The ✕ mark's meaning and the "What is broken?" lead line also name dependency loops, which are made of resolved pointers. Over the hostile fixture with hostile `Depends on:` values, every group, state, trust-class and value-form label the page renders is in the intent-view-session-start closed set plus those additions and the five value forms, and every state-mark glyph is one of ● ◆ ◇ ✕ △ ✓.

### Routing, keyboard, layout and safety

- [x] **AC-0024.** The URL fragment holds the "Show" and "Steps" choices only when they differ from the defaults, and reloading restores them with the picked intent. Changing either adds no history entry. A fragment value outside the offered choices, such as a negative, huge or non-numeric step count or an unknown direction, is read as the default, is never shown as text, and is dropped from the next fragment the page writes. Following a link in the part picks that intent, adds a history entry and keeps the current choices; browser back returns to the previous intent and its choices.
- [x] **AC-0010.** Using the keyboard alone, a reader can pick an intent, reach and change "Show" and "Steps", follow a listed prerequisite and a listed dependent, and return to the first intent with browser back, without a focus trap. Across the width and theme matrix, over the dependency fixture with an intent picked whose part shows a cycle: no horizontal scrolling at 320 CSS px, no focused element entirely hidden, every interactive target at least 24 by 24 CSS px, every text node at least 4.5:1 contrast, and every focus indicator at least 3:1.
- [x] **AC-0011.** Dependency metadata obeys [intent-navigation-export](../intent-navigation-export/spec.md)'s offline publication and inert-content contract and RFC-0105 D4. Over the hostile fixture with hostile `Depends on:` values, including values that copy a state-mark glyph, a state label and the phrase "waits for", rendered dependency text holds no code point the text output escapes, record text never becomes markup or an attribute other than text, no link targets anything but an in-page fragment or an existing source link, no network request is made, and the content-security policy string is unchanged. Unsafe reads produce the inherited refusal instead of a successful query or export.

### Release, measurement and review

- [x] **AC-0014.** Navigator activation evaluations accept intent dependency, prerequisite, dependent, and dependency-graph requests. Requests to enforce blocking, reorder the queue, migrate workspace dependencies, or edit an intent do not activate this read-only capability.
- [x] **AC-0015.** The supported self-host projection answers a typed/path dependency fixture through the installed navigator and renders its offline dependency view. Core's pack/plugin versions match and increase, its changelog fragment describes the dependency view, and catalogue verification passes. Shipped instructions and guides explain the header-only scope, legacy path acceptance, the enforcement boundary, and that a scoped export also carries the dependency records of intents linked to the scope, without internal governance citations.
- [x] **AC-0025.** The export spec's scale benchmark, re-run on this view, meets its thresholds at 1, 10, 25 and 50 times this repository's corpus, and the ledger records each result.
- [x] **AC-0026.** An export over this repository at the final code commit, opened in headless Chromium, shows for each intent that writes `Depends on:` the edges and diagnostics `query --operation dependencies` returns with `both` and all steps, and the ledger records the command, those intents and the result. Eight screenshots of that export with such an intent picked and "Both" chosen, at the width and theme matrix, taken at true viewport sizes, are committed under `notes/screens/` and listed in the ledger with their SHA-256.
- [x] **AC-0027.** An `experience-reviewer` pass over the rendered real export against RFC-0108 D1 rules 1 to 10 and the `skill-html-views` direction's ranked goals leaves no Major or Blocker finding after adjudication, recorded in the ledger.

### Amended predecessor criteria

Each row states the predecessor criterion's new reading. Every criterion not listed carries over unchanged, with its checks kept.

| Predecessor criterion | New reading |
| --- | --- |
| intent-navigation 0003, admitted edge fields | Unchanged for the graph's `edges`. An intent's `Depends on:` also produces dependency edges and diagnostics, which appear only in `dependencies` results and the export payload's `dependencies` member (AC-0001 to AC-0005, AC-0016). |
| intent-navigation 0013, operation set | The query operations are exactly `summary`, `record`, `tree`, `ancestors`, `search`, `outstanding` and `dependencies`. Any other operation returns `unknown_operation`. |
| intent-navigation-export 0001, payload keys | The payload's keys are exactly `schema`, `scope`, `provenance`, `summary`, `records`, `outstanding`, `nodes`, `edges`, `source_links` and `dependencies`; `schema` stays `intent-navigation.view.v1` (AC-0016). |
| intent-view-session-start, broken-entry term | Also each dependency broken entry of AC-0021. |
| intent-view-session-start 0006, "What is broken?" | Also lists the dependency broken entries of AC-0021. |
| intent-view-session-start 0013, detail part order | For an intent, "Dependencies" sits between "Where it sits" and "Open the file" (AC-0009). |
| intent-view-session-start 0014 and 0017, a record's broken count and "What is broken" part | Both branches also count and list the record's dependency broken entries, shown as AC-0021 states. |
| intent-view-session-start 0042, the page while `outstanding` is unavailable | "What is broken?" lists the edges carrying a `state` and every dependency broken entry, and says delivery diagnostics were unavailable (AC-0021). |
| intent-view-session-start 0019, "Record details" groups | Adds the two groups of AC-0022 for an intent. |
| intent-view-session-start 0022, Key and closed label set | Extended by AC-0023. |
| intent-view-session-start 0030, fragment | Also holds "Show" and "Steps" as AC-0024 states. |
| intent-view-session-start 0038, keyboard | Also covers the "Dependencies" part, as AC-0010 states. |

## Follow-ons

None. FEAT-0034's already-owned enforcement and migration remain outside this delivery, and slice 11 owns readiness and the hand-over prompt.

## Assumptions

- Technical: three live intents write `Depends on:`, all as legacy paths with a trailing preamble comment. The path compatibility rule exists for them.
