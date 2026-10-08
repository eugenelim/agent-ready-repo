# RFC-0106: Stop registering derivable work, and give the remaining facts per-item homes

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** Platform Core maintainer
- **Date opened:** 2026-10-08
- **Date closed:**
- **Decision weight:** standard
- **Related:** [RFC-0105](0105-artifact-derived-navigation-and-workspace-retirement.md), [RFC-0103](0103-cross-artifact-reference-grammar.md), [RFC-0064](0064-ini-001-ai-native-ecosystem.md), [ADR-0119](../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), [Workspace registry retirement](../product/intents/FEAT-0034-workspace-registry-retirement.md), [Intent graph navigation](../product/intents/FEAT-0002-intent-graph-navigation.md), [Intent navigation delivery brief](../product/briefs/intent-navigation-delivery.md)

## Reviewer brief

- **Decision:** Retire registration in `workspace.toml` one responsibility at a time, each in the release that ships its header-derived replacement; type the intent pointers in `Discovery:`; and give every fact the headers cannot yet supply a per-item home.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Registration for each artifact type stops in the release in which the last responsibility its entries feed — orientation, dispatch and resume, dependency blocking, ready-spec selection, suggestions, brief coverage — ships its replacement. Until then its writers keep working unchanged.
  - An intent-valued `Discovery:` pointer names its target in the kind the traceability graph registers for it. A research or notes target stays a repository path.
  - Dependencies move to a typed `Depends on:` header on the item that waits. A captured item gets its own file with a `Status:` line. The registry's first-in-list suggestion may be removed.
  - The `unregistered_work` refusal is retired, so a spec that meets D1's readiness rule is dispatchable without a registry entry.
- **Affected surface:** every skill that writes or moves registry entries, including `work-intake`, `author-delivery-brief`, `close-work`, `work-loop`, `receive-brief`, `run-okr-cascade`, intent rename, and the tracker brief-intake skills; `workspace-status`'s canonical reconciliation and suggestions; the new-spec template's `Discovery:` guidance; and the five accepted contracts named under D1.
- **Stakes:** Costly to reverse once adopters stop registering, so each step is gated on its replacement. Legacy entries stay readable, and RFC-0105's retirement gates still guard deleting the file.
- **Review focus:** whether the replacement named for each responsibility is complete; whether dispatching an Approved spec that nobody queued is acceptable; whether `Depends on:` can carry what `needs` carries; whether removing the first-in-list suggestion loses a real human choice.
- **Not in scope:** deleting `workspace.toml` or `workspace-status`; migrating legacy entries; typing `Contract:`.

## The ask

**Recommendation: accept D1 to D3.** Every responsibility the registry carries for new work has a header-derived replacement or a named removal, and every remaining fact has a per-item home. The registry stops growing as each replacement ships. Two behaviours are removed rather than replaced: `work-loop` no longer refuses a spec for having no registry entry, so a spec that meets D1's readiness rule becomes dispatchable without being queued; and the first-in-list `next_queue` and `next_shape` suggestions go, unless a FEAT-0034 specification gives them a stated rule.

**Why now.** `workspace.toml` is 2,494 lines and 388 entries, and 197 of the 939 commits since 2026-09-07 edited it. It is also the less complete list. On 2026-10-08, intent, brief, and spec headers held 195 outstanding artifacts, and 52 of them were not registered. All 143 registry entries in non-terminal collections that point at an artifact agreed with that artifact's own `Status:`. `navigate-intents`, the read-only intent navigator [RFC-0105](0105-artifact-derived-navigation-and-workspace-retirement.md) committed and the intent navigation delivery brief now plans, is specified to read those headers directly. Until registration retires, every new piece of work pays to keep a second, weaker copy current.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | How does registration stop for new work? | One responsibility at a time, each in the release that ships its named replacement | Removes the copy without losing dispatch, blocking, or lifecycle behaviour | 2026-10-15 | Accept, or name a responsibility without a replacement |
| D2 | How is an intent-valued `Discovery:` written? | The target's registered kind and slug; research and notes targets stay paths | Types every graph edge without inventing a research kind | 2026-10-15 | Accept, or name a target this breaks |
| D3 | Where do the facts headers cannot supply go? | `Depends on:` header; one file per captured item; no stored order, suggestion removable | Each fact is about one item, so one item can hold it | 2026-10-15 | Accept, or name a fact that needs a shared file |

## Problem & goals

### Problem

`workspace.toml` was introduced by [RFC-0064](0064-ini-001-ai-native-ecosystem.md) as the coordination index. Most of what it now holds repeats what each artifact already records. An entry's path, kind, and summary are the artifact's own location, type, and title, and its collection repeats the artifact's `Status:`. The registry's reconciler already flags a collection that disagrees with the status. The cost of the copy is a file that conflicts across worktrees, has reached 2,494 lines, and still misses work.

The registry also carries real behaviour that a reader must not lose. `work-loop` starts or resumes a spec only when `workspace-status`'s canonical reconciliation lists it as ready or active, and that reconciliation is built only from registered entries. An unregistered spec is refused with `unregistered_work`. Its `needs` edges decide which work is blocked. Its list order decides which ready spec an argless `work-loop` start takes, because that start selects the first `canonical.ready` item, and it feeds the `next_queue` and `next_shape` suggestions.

Five accepted contracts require registration:

- [RFC-0064](0064-ini-001-ai-native-ecosystem.md) D4 has each spec pull request update `workspace.toml` in the same diff, and its milestone rows have writers move entries between collections.
- [`docs/product/AGENTS.md`](../product/AGENTS.md) treats a spec's registered membership as the evidence behind a brief's coverage map, although every brief-derived spec names its brief in its own `Brief:` header.
- [FEAT-0005](../product/intents/FEAT-0005-lifecycle-and-closure.md) assigns `close-work` the move of an entry into a terminal collection when work closes. That authority is not yet exercisable, because no collection admits a closed intent.
- [FEAT-0001](../product/intents/FEAT-0001-intent-identity-and-registration.md) renames an intent and its registry path together.
- [ADR-0119](../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md) D4 says an intent "registers in `workspace.toml` directly" and that "its lifecycle state comes from the workspace record".

RFC-0105 D3 makes the registry's retirement a gated target. A deliberate removal of accepted behaviour must cite an accepted RFC, ADR, or errata entry with authority over that behaviour, and each responsibility needs "a named replacement or an accepted removal decision". This RFC is that authority for registration, for the first-in-list suggestion, and for retiring the `unregistered_work` refusal, which `workspace-status`'s spec selector emits and `work-loop` relays. It is not authority for deleting the file.

[RFC-0103](0103-cross-artifact-reference-grammar.md) typed `Parent intent:` and `Brief:` and held `Discovery:` back, ruling that a pointer field adopts the typed form "only once every artifact it can name has a kind and a slug rule". Some `Discovery:` values name intents, and others name research documents that have no node kind. On 2026-10-08, 31 spec `Discovery:` values named an intent by path or markdown link, and 5 used the typed form.

### Terms used by this RFC

- **Registry, entry, collection.** `workspace.toml` is the registry. Each entry points at one artifact or names one captured item, and sits in a named list called a collection, such as a queue, a draft list, `[backlog].open`, or `shipped`. A *terminal* collection holds finished work; the others hold outstanding work.
- **`needs`.** An entry's list of dependencies. The entry is blocked until each named item is settled.
- **Dependency cases the reconciler settles today.** A *coordination receipt* is a record in a brief's body showing that work in another repository was accepted. A *completion receipt* is a record kept on a `needs` edge so the edge stays settled after its target file is pruned. A *cooled* dependency is settled by its per-item record under `docs/lifecycle/`, without reading the target. *Provenance and fail-closed findings* are the reconciler's refusals when an entry's recorded source disagrees with the artifact or its state cannot be decided.
- **Shaping item, shaping-item guard.** A shaping item is work that is still being framed or researched, not built. `work-loop`'s shaping-item guard stops it from building such an item and names the right skill instead: `shape` goes to `frame-intent`, `research` to `desk-research-project-start`, `strategy` to `frame-situation` or `frame-intent`, `design` to `experience-status`, and `signal` is declined as monitoring only. *Unsupported legacy* is the reconciler's label for an entry in an old shape it does not interpret.
- **`next_queue`, `next_shape`.** The "next build item" and "next shaping item" lines `workspace-status` prints at the start of a session, each taken as the first matching entry in list order.
- **Captured item.** Work recorded for later that is not yet an intent, brief, or spec, such as a defect note. *Materialize before register* is `work-intake`'s rule that the item's own file is written before anything points at it.
- **Ladder kind, ordinal.** RFC-0103 types most intents as `intent:<slug>`. Intents the traceability graph already classifies by their `Kind:` or `Level:` header keep that classification as their kind, for example `capability:`, `outcome:`, or `opportunity:`. An ordinal is a filename number such as `FEAT-0029`, which RFC-0103 refuses as a pointer because it can change.
- **RFC-0105 D3's four gates.** Before the registry can be deleted: an inventory of every reader and writer; a decision for every registry-only fact; evidence that each kept behaviour still works; and compatibility closure, meaning legacy entries, adopters, and references are migrated or retired.
- **RFC-0064's writer rows.** The milestone rows that have `work-loop` move a spec from active to shipped, and `receive-brief` move a brief from draft to ready, in the registry.

### Goals

- New work is oriented, dispatched, resumed, and blocked from its own headers, with no registry write.
- Every fact the headers cannot yet supply has a named per-item home, and a named owner for its reader.
- The spec-to-intent pointer is written in one form a reader resolves without guessing.

### Non-goals

- **Deleting `workspace.toml` or `workspace-status`.** RFC-0105 D3's four gates still govern that, through [FEAT-0034](../product/intents/FEAT-0034-workspace-registry-retirement.md).
- **Migrating legacy entries.** Existing entries stay readable until FEAT-0034's specifications move them.
- **Typing `Contract:`.** Its versioned target shape still needs its own decision, as RFC-0103 states.

## Proposal

### D1 — Retire registration one responsibility at a time

Registration for an artifact type stops in the `core` release in which the last responsibility its entries feed ships its replacement. Until then its writers keep working unchanged. The table names each responsibility, its replacement, and its owner.

| Responsibility | Fed by entries for | Replacement | Owner |
| --- | --- | --- | --- |
| Orientation: what exists and what is outstanding | intents, briefs, specs, captured items | `navigate-intents`' outstanding-work view over intent, brief, and spec headers; a captured-item reader under D3 | Slice 1 of the intent navigation delivery brief; a FEAT-0034 specification |
| Dispatch and resume of a spec | specs | Header-derived readiness: a spec is ready from its own `Status:`, its sibling `plan.md`, and its `Depends on:` targets, and active from its own `Status:` | A FEAT-0034 specification |
| Dependency blocking | intents, briefs, specs, captured items | `Depends on:` headers, under D3 | A FEAT-0034 specification |
| Selecting among several ready specs | specs | An argless start that finds more than one ready spec lists them and asks, as an active resume with more than one candidate already does | A FEAT-0034 specification |
| Next-item suggestions | intents, briefs, specs | Removed, or replaced by a stated rule, under D3 | A FEAT-0034 specification |
| Brief coverage evidence | specs | The spec's own `Brief:` header, read by `author-delivery-brief` and the brief coverage lint | A FEAT-0034 specification |
| Routing a supplied shaping item to its shaping skill | intents, captured items | The guard matches a captured-item file that carries a `Type:` line and routes it by that value, using today's mapping from type to skill. It matches nothing else: not an intent, not a spec, and not an item without a `Type:` line. Today the guard matches no entry in this registry, because the one typed entry parses as unsupported legacy, so routing that item is an intended change, recorded in the equivalence record | A FEAT-0034 specification |
| Cross-pack shaping intake, such as OKR gap entries | intents | Each gap is written as a captured item with its own file and `Status:` line, under D3 | A FEAT-0034 specification, with the producing pack |
| Lifecycle collection moves | intents, briefs, specs | None needed: the artifact's `Status:` is its lifecycle state | Stops with the type's registration |

The dispatch and blocking replacements must reproduce every case the canonical reconciliation handles today, or record an accepted removal for it, in their specification's behavioural-equivalence record. Those cases are: a cross-repository dependency settled by the coordination receipt in its containing brief; a local dependency whose target was pruned, settled by its completion receipt; a dependency on a defect; a cooled dependency settled by its lifecycle record; a brief whose child scope is unknown; and the provenance and fail-closed findings that today keep a spec out of the ready set. In addition to those cases, this RFC removes one behaviour outright: the `unregistered_work` refusal, which stops a spec that has no registry entry, is retired when spec registration stops. This RFC's acceptance is the authority for that removal under RFC-0105 D3; eugenelim, its author, proposed it on 2026-10-08. After it, an Approved spec with its `plan.md` and finished `Depends on:` targets is dispatchable without being queued. This RFC fixes the target, and the equivalence record fixes the definition.

Registration consistency is unchanged until a type's registration stops. A writer that still runs keeps its collection moves. Intent entries keep today's rule: an intent leaves the registry when its status leaves the collection that admits it.

When a type's registration stops, the contracts that required it change in the same release, through their own errata or amendment citing this RFC: RFC-0064 D4 and its writer rows, `docs/product/AGENTS.md`'s brief-coverage rule, FEAT-0005's terminal move, FEAT-0001's rename lockstep, and ADR-0119 D4, superseded in part so that an intent's lifecycle state comes from its own `Status:`. ADR-0119 D4's other point, that registration needs no initiative bucket, is unaffected.

### D2 — Type intent-valued `Discovery:` pointers

An intent-valued `Discovery:` value is written as the kind the traceability graph registers for the target, and its slug. That is `intent:<slug>` for most intents, and the ladder kind for an intent the graph types by its `Kind:` or `Level:`, such as `capability:<slug>`, exactly as RFC-0103 D2 already applies to `Parent intent:`. A value that names a research document, a notes file, or any other non-intent file stays a repository-relative path and is provenance, not a graph edge.

This amends RFC-0103 D1's adoption condition for one field. `Discovery:` adopts the typed form for its intent targets although its research targets have no kind. The reason is that only the intent targets are graph edges, and a research kind that no reader uses would be a node type built for a lint. RFC-0103's other rules apply unchanged: its D1 refuses an ambiguous bare slug in every field, and its D2 refuses an ordinal in place of a slug.

The new-spec template and every skill that writes `Discovery:` emit the typed form. A forward-only check refuses an untyped intent-valued `Discovery:` in any spec a change adds or modifies. The legacy values are swept once.

### D3 — Per-item homes for what headers cannot yet supply

FEAT-0034's de-risk found three such facts, recorded in its [De-risk record](../product/intents/FEAT-0034-workspace-registry-retirement.md#de-risk-record--2026-10-08).

- **Dependencies.** 98 `needs` edges, 64 of them on 41 outstanding entries. A dependency is written as `Depends on:` in the preamble of the item that waits, as a comma-separated list of RFC-0103 typed references. It is a blocking edge. It stays distinct from `Related intents:`, which never blocks. Three intents already write `Depends on:`, and nothing reads it. A FEAT-0034 specification builds its reader and migrates the 98 edges.
- **Captured items not written as an intent, brief, or spec.** 75 on 2026-10-08. 51 point at their own file, 49 of which carry no status line and 2 of which point at a spec's verification ledger. The other 24 have no file. Each captured item gets its own file, written by `work-intake`'s materialize-before-register route. The file carries a `Status:` line and a `Kind:` line holding its registry entry's `kind`, such as `defect` or `design`. An item whose registry entry carries a shaping `type` keeps that value as a `Type:` line; no other item gains one. Slug-only entries that carry no `kind` get one assigned by the migration, listed in its equivalence record. A FEAT-0034 specification builds their reader. Until it ships, captured items stay registered under D1.
- **Order.** Not a stored fact. The registry header and `workspace-status` both declare list order non-semantic. Two behaviours read it: the first-in-list `next_queue` and `next_shape` suggestions, and an argless `work-loop` start, which takes the first ready spec. This RFC authorises removing the suggestions, and replaces first-item selection with listing the ready specs and asking. A FEAT-0034 specification may instead give the suggestions a deterministic rule it states. Selecting among several ready specs always lists them and asks; no rule may choose one automatically. A human priority, if one is ever needed, is a header field on the item, never a position in a shared list.

## Options considered

**D1** is ordered by how fast registration stops:

- **Do nothing.** Wait for FEAT-0034's full retirement. The file keeps growing and conflicting, and keeps missing work.
- **Stop all new registration when the navigator ships.** This breaks dispatch: `work-loop` refuses an unregistered spec.
- **Retire one responsibility at a time, each with its replacement (recommended).** Slower to finish, and the behaviours removed without a replacement are named: the `unregistered_work` refusal, and the first-in-list suggestions unless given a stated rule.

**D2** is ordered by how much of the field the grammar covers:

- **Do nothing.** The pointer stays in three forms, and every reader keeps normalising it.
- **Type intent-valued pointers only (recommended).** Covers every graph edge and leaves provenance alone.
- **Add a `research:` kind.** Types every value, but builds a node kind nothing reads.

**D3's order** is the one contested part:

- **Do nothing.** Keep first-in-list suggestion and selection, which keeps shared-list position meaningful and keeps the registry needed.
- **Remove the suggestion and ask when several specs are ready (authorised here).** The outstanding-work view shows what is open; choosing among it stays a human decision.
- **Replace it with a stated deterministic rule.** Keeps a suggestion without a shared list. Left to FEAT-0034's specification.

## Risks & what would make this wrong

- **A replacement misses something its responsibility did.** *Falsifiable:* RFC-0105 D3's behavioural-equivalence gate. Each FEAT-0034 specification compares the old and new outcome over a frozen corpus before its writer stops. *Mitigation:* a writer keeps working until its replacement ships.
- **The header view misses outstanding work.** FEAT-0034's validation hook gates *deleting* the registry, not this RFC. It requires at least two weeks after derivable registration stops in which no session misses outstanding work `navigate-intents` should have listed. Registration for any type stops only after the navigator's release, and the navigator is tested against the registry before that release.
- **Status words are read inconsistently.** 59 shipped specs with text after the status word, and 16 with a non-standard status header, would have read as outstanding. Both were repaired before this RFC: the closure terminality reader now uses the spec-status lint's leading-word rule, and the 16 headers use the standard form. *Mitigation:* the spec-status lint refuses an unknown leading status word.
- **`Depends on:` cannot carry everything `needs` does.** *Falsifiable:* FEAT-0034's migration compares edge sets before and after. 95 of the 98 edges are already typed, and none carries a receipt.
- **External adopters rely on registration.** Not visible from this repository. RFC-0105 D3's compatibility-closure gate still holds the file until adopters are covered.
- **Work becomes dispatchable without a queueing step.** With the `unregistered_work` refusal retired, a spec that meets D1's readiness rule can be started without being queued. *Mitigation:* approval is already a human gate, so queueing was a second confirmation of the same decision, and an argless start that finds several ready specs always lists them and asks.
- **Drawback:** registration for specs ends last, after the dispatch replacement ships, so the contention it causes falls only gradually.

## Evidence & prior art

- [FEAT-0034's de-risk record](../product/intents/FEAT-0034-workspace-registry-retirement.md#de-risk-record--2026-10-08), 2026-10-08, survived its predeclared kill lines. It found 388 registry entries, 218 of them in non-terminal collections. 143 of those point at artifacts and agree with the artifacts' own `Status:`. Headers hold 195 outstanding artifacts, 52 of them unregistered. The residue is 98 `needs` edges, 75 captured items, and no stored order. It tested orientation; dispatch and cleanup were outside its probe, which is why D1 names their replacements separately.
- [RFC-0105](0105-artifact-derived-navigation-and-workspace-retirement.md) D3 requires accepted authority for a deliberate removal and a named replacement for each retained responsibility.
- [RFC-0103](0103-cross-artifact-reference-grammar.md) D1's adoption condition and D2's ladder kinds are what D2 amends and follows.

## Follow-on artifacts

- **Specs under FEAT-0034:** header-derived dispatch, resume, and ready-spec selection in `work-loop` and `workspace-status`, with their behavioural-equivalence record; the `Depends on:` reader and the `needs` migration; captured-item files, their reader, and their migration; removal or replacement of the first-in-list suggestion. Each one stops its registration writer in the release it ships.
- **Brief change and spec, slice 5 of the intent navigation delivery brief:** on acceptance, the brief's slice 5 takes on typed `Discovery:` in the writers, the forward check, and the one-time sweep of legacy values, which it currently holds back pending this decision.
- **RFC-0103 errata entry, applied on the day this RFC is accepted and dated that day.** Wording first approved by eugenelim on 2026-10-08, then corrected the same day for two citation errors. The corrected wording below awaits the owner's approval:

  > **D1's adoption condition is amended for `Discovery:` by [RFC-0106](0106-stop-registering-derivable-work.md) D2.** D1 holds that a pointer field adopts `<kind>:<slug>` "only once every artifact it can name has a kind and a slug rule". `Discovery:` now adopts the typed form for its intent targets only. A value names the kind the traceability graph registers for its target: `intent:<slug>`, or, as RFC-0106 D2 provides, the ladder kind of an intent `recognize_ladder` already claims, such as `capability:<slug>`. A value naming a research document, a notes file, or any other non-intent file stays a repository-relative path. It is provenance, not a graph edge, so the absence of a research kind no longer blocks the field. This record's other rules are unchanged: D1 still refuses an ambiguous bare slug in every field, and D2 still refuses an ordinal in place of a slug. `Contract:` is unaffected and still waits on its own decision.

  If RFC-0106 D2 changes before acceptance, the wording returns to the owner for approval.
- **Contract updates, each in the release its writer stops:** RFC-0064 D4 and its writer rows, `docs/product/AGENTS.md`, FEAT-0005, FEAT-0001, and a partial supersession of ADR-0119 D4, each citing this RFC.
- **Guides:** the core orientation guide routes outstanding-work questions to `navigate-intents`, in the navigator's release, owned by the `intent-navigation` spec's Durable Outputs.
