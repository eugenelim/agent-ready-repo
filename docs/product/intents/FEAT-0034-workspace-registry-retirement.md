# Workspace registry retirement

- **Slug:** `workspace-registry-retirement`
- **Status:** Draft
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:workspace-coordination-reorganization
- **De-risked:** 2026-10-08
- **Shaping-reviewed:** 2026-10-08
- **Decomposed:** no

## Outcome

- **Steerable input:** Reduce the share of coordination operations that require an edit to one repository-wide mutable registry while assigning every retained fact and behavior to a named owner.
- **Lagging outcome:** People and agents coordinate, dispatch, and close repository work with fewer shared-file conflicts and no loss of coordination safety or duplicated inventory.
- **Guardrail:** Retirement fails closed until the consumer inventory, state disposition, behavioral-equivalence evidence, and compatibility closure are complete. No dependency, priority, provenance, dispatch, lifecycle, cooling, repair, rollback, prune, legacy, or external-adopter behavior disappears by inference.

## Opportunity

- **Functional job:** Coordinate, dispatch, and close repository work without every participant editing one shared registry or losing the safety behavior it currently carries.
- **Emotional job:** Remove the hot file with confidence that a hidden reader, writer, or workspace-only fact has not been missed.
- **Social job:** Show maintainers and adopters a reviewable migration record that names where every old responsibility went and proves the retained behavior.
- **Struggling moment:** `workspace.toml` duplicates artifact identity and lifecycle while also carrying real non-derivable choices. Its readers and writers span skills, runtime projections, manifests, seeds, tests, and guides, so deleting the file or replacing only its read-only view would strand accepted coordination behavior.

## Boundary

This feature owns the gated retirement path required by [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md):

1. a closed inventory of every operative reader, writer, projection, fixture, seed, guide, and adopter-facing promise;
2. a per-fact disposition into canonical artifact metadata, derived state, external projection, temporary migration state, or deliberate removal under accepted authority;
3. equivalence evidence for required reconciliation, dependency, provenance, dispatch, lifecycle, cooling, repair, rollback, and prune outcomes; and
4. compatibility closure for legacy entries, public activation, manifests, seeds, operative references, corpus gates, and final deletion.

It also owns the transition sequencing that keeps `workspace-status` and `workspace.toml` supported until all four gates pass. Mutation moves only to the workflow that owns the affected artifact or lifecycle; it does not move into `navigate-intents`.

It does not own the `navigate-intents` feature, intent identity or graph rules, tracker projection, lifecycle policy, renderer design, or changes to accepted behavior without separate authority. It does not choose a replacement repository-wide registry. Where priority, dependency, or another workspace-only fact has more than one lawful destination, the accepted specification must choose an owner before migration.

The feature must preserve the parent's two inherited constraints: any replacement must either provide stable per-entry identity or preserve safe single-parse enumeration, and it must decide whether repo-origin `source.revision` is an admission pin before retaining or removing that field.

## Owner

- Platform Core maintainer. Accountable for the inventory, per-fact decisions, equivalence evidence, and certification that all four retirement gates passed.

## Unresolved questions

- Which accepted artifact or external projection owns human priority and dependency choices after the registry retires. If RFC-0106 is accepted, its D3 answers it: a dependency is `Depends on:` on the waiting item, and any human priority is a header field on the item.
- Whether any external adopter depends on behavior not visible in tracked repository files.
- Whether array order carries priority anywhere beyond the known index-based join and `next_queue` projection.
- Which legacy records require a temporary compatibility seam, and what evidence closes it.
- Which accepted sibling contracts require an amendment or superseding authority before their workspace writer or dependency behavior can change.

## Cascading intent impacts

This retirement changes the future owner of coordination behavior; it does not make every historical `workspace.toml` locator stale today. The migration inventory distinguishes current contracts from historical provenance and updates only the current owner when its gate passes.

- [Intent graph navigation](FEAT-0002-intent-graph-navigation.md) owns the artifact-derived read-only orientation successor. It must remain independent of `workspace.toml`; this feature owns retiring the old orientation surface after parity, not implementing the new navigator.
- [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md) currently renames an intent and its workspace path reference together. That lockstep write remains required during compatibility, then disappears only when the registry path ceases to be operative.
- [Single-ladder migration](FEAT-0004-single-ladder-migration.md) depends on initiative-free registration today. Its end state must instead use canonical intent parentage and artifact lifecycle, with any workspace registration treated as transitional compatibility rather than the new ladder's authority.
- [Lifecycle and closure](FEAT-0005-lifecycle-and-closure.md) is Accepted and currently assigns a terminal registration move to `close-work`. This feature cannot silently rewrite that contract. The retirement specification must preserve the writer during compatibility, then cite accepted authority for its amendment or removal when canonical lifecycle no longer needs a workspace collection move.
- [External tracker projection](CAP-0004-external-tracker-projection.md) and its children consume dependency, priority, and observation state that may currently be joined through workspace entries. State disposition must name the canonical or external owner before the registry stops supplying those joins.

Frozen records and completed intents that name `workspace.toml` only as their historical source remain unchanged. Operative guides, routes, manifests, tests, and current intent contracts move only when the four retirement gates prove their replacement.

## Projection

No tracker projection is selected. Tracker-origin refresh and human selection may be assigned to an external projection only through the state-disposition decision; this feature does not presume that owner.

## Assumptions

- Every operative consumer, including external adopter promises, can be named and migrated or explicitly retired under accepted authority. **Untested.** In-repository consumers can be listed by search; external adopters cannot be seen from here, and RFC-0105 D3's compatibility-closure gate holds the registry until they are covered.
- **Riskiest assumption:** Everything orientation needs can be derived from artifact preamble headers except a small, nameable residue, and each residual fact can get one canonical owner without recreating a repository-wide mutable registry. **Survived 2026-10-08,** with the residue reshaped; see the De-risk record.
- Provenance, lifecycle, cooling, dispatch, and cleanup facts outside orientation can each receive one canonical owner. **Partly supported:** registry provenance is already checked against artifact headers, and cooling already lives in per-item lifecycle records. Dispatch and cleanup are untested.
- A frozen equivalence corpus can distinguish preserved behavior from an intentional, separately authorized removal.
- The migration can preserve safe duplicate handling and stable per-entry identity without relying on array position across independent reads.
- Removing the hot file will not relocate the same contention to a generated assembly step or another single-owner projection.
- **Knowledge surface:** in-repo workspace implementations, package projections, manifests, tests, fixtures, seeds, guides, RFC-0105, and the workspace-coordination capability probe.

The parent proved that a staged retirement has a viable destination class for every tracked repository responsibility. The 2026-10-08 record below tests per-fact ownership for orientation. External adopters, equivalence replay, and dispatch and cleanup ownership stay open and travel into decomposition as gate work.

## De-risk record — 2026-10-08

- **Level kind:** feature, but the dominant unknown is architectural rather than desirability. Nobody is asking whether a hot file should stop being hot. The bet is whether the facts it holds can move somewhere without a new hot file.
- **Reversibility triage:** one-way door. Deleting the registry and moving its writers changes contracts that `close-work`, `intent-identity-and-registration`, brief coverage, and adopter guides all depend on. Stopping new registration is cheap to reverse; losing a fact nobody re-recorded is not.
- **Prototype-approach:** `validate-first`. A read-only walk of `workspace.toml`, its readers, and the artifact headers can fail the bet before any migration is chosen.

### Owner direction, 2026-10-08

The owner, eugenelim, directed that the intent graph find all outstanding work so the `workspace.toml` construct can retire, and that registration on the hot file stop for anything the headers can supply. The `navigate-intents` [delivery spec](../../specs/intent-navigation/spec.md) and [FEAT-0002](FEAT-0002-intent-graph-navigation.md)'s 2026-10-08 Amendment carry the derived half. This record tests the other half.

### Why this assumption and not the consumer inventory

The framed riskiest assumption was that every operative consumer, including external adopters, can be named and migrated. Evidence on hand separated the two candidates.

- **Consumer inventory.** In-repository readers and writers can be listed by search; that is labor, not risk. External adopters cannot be seen from this repository at all, so no desk probe can test them. RFC-0105 D3's compatibility-closure gate already keeps `workspace-status` supported until that gap closes. The inventory decides how long retirement takes, not whether it can happen.
- **Residue ownership.** If some fact the registry holds can live only in one shared, mutable, repository-wide file, retirement cannot happen at all; it only renames the hot file. Nothing on hand tested this. That makes it the riskier bet.

### Riskiest assumption

Everything orientation needs can be derived from artifact preamble headers, except a small, nameable residue (dependency edges, queue order or priority, and captured items with no artifact of their own), and each residual fact can get one canonical owner without recreating a repository-wide mutable registry.

What would have to be true: every fact an orientation reader takes from `workspace.toml` must be either readable from the header of the artifact an entry points at, or one of the three named residual classes; each `needs` edge must join two items that each have a stable identity outside the registry; no shipped reader may need one total order across unrelated items; and each captured item must be able to live in a file of its own rather than as a line in one shared file.

### Kill condition, predeclared

There is no traffic for an internal contract, so the bar is a set of counts and named cases over the real files. It was written into this intent before the probe below was run.

**Kill the bet as framed if, over this worktree's `workspace.toml` (commit `1fe67e8f4` plus one uncommitted entry change) and the artifact corpus at the same point, any one of the following holds. One case is enough.**

- **K1 — An unnamed residual class.** A shipped orientation reader (the `workspace-status` scripts or MCP server) takes a fact from `workspace.toml` that is neither readable from the pointed artifact's preamble nor one of the three named classes. A fact class that an accepted ADR or Accepted intent already retires, such as the initiative ladder under ADR-0119, counts as disposed, not as residue.
- **K2 — A dependency edge with no identity to hang on.** A `needs` value, or the entry carrying it, names an item that has neither a path to its own file nor a stable slug, so the edge cannot be written on either end outside the registry.
- **K3 — Order that only one global list can hold.** A shipped reader orders entries from different initiatives or collections against each other, so queue order cannot live per parent or per item.
- **K4 — Captured items that must share one file.** A captured item has no file of its own, and the only home for it is a line in one file that many items share, so retiring the registry would move the contention rather than remove it.

One narrower line, also set before the probe, does not kill the bet:

- **Status reading, an owner finding only.** If any outstanding intent, brief, or spec has a `Status:` value that `closure_terminality` cannot class because it matches whole strings only, record a finding that derived outstanding work depends on fixing that reading. Do not edit the projection here.

### Prototype

Two throwaway, read-only scripts outside the repository parsed `workspace.toml` and read the preamble of every live intent, brief, and spec. They compared each registry entry with the header of the file it points at, sorted every `needs` edge by the kind of item at each end, and checked which files captured items point at. A separate read of the `workspace-status` scripts and skill listed every registry field the orientation output uses and how it uses list position. Status was read the way FEAT-0003's resolver reads it: `- **Status:**` lines only, with a trailing `<!-- -->` comment removed. Nothing in the repository was written.

### Prototype results

The registry holds 388 entries. 218 sit in collections that are not `shipped`: `open` 179, `backlog` 12, `queue` 10, `executing` 9, `draft` 7, and `ready` 1. They point at:

- 143 intents, briefs, or specs: 100 intents, 18 briefs, and 25 specs.
- 51 other files: 49 defect notes or files and 2 design notes.
- 24 entries with no file: 15 carry only a slug, and 9 carry a slug plus a pointer to one intent, `direct-skill-lifecycle`.

**The headers already carry what the registry says about artifacts.** All 143 artifact entries are outstanding by their own `Status:`, and every collection agrees with that status. No entry is stale. The `workspace-status` engine already flags a collection that disputes the header as `impossible_transition`, and flags registry provenance that disputes the header as `provenance_mismatch`. The headers also find more: 195 artifacts are outstanding by their own status (147 intents, 21 briefs, 27 specs), and 52 of those are not registered at all (47 intents, 3 briefs, 2 specs). Of the 47 intents, 36 are Accepted.

**K1 did not fire.** Orientation uses these registry fields, and each has a home:

- Path, slug, and kind: the artifact's own file and folder, or the captured-item class.
- Collection: the header's `Status:`, as shown above.
- Summary: a restatement of the artifact's title and outcome. Several summaries also restate status, which `docs/product/AGENTS.md` already forbids.
- `source` mode, ref, revision, and parent: checked for equality against the artifact's own header. No live entry is `tracker-origin`.
- Initiative name, status, milestone, and parent: retired as canonical by ADR-0119 D2, so disposed rather than residue.
- Array position: used only to tell two entries apart inside one array when matching cooled entries. Cooling itself lives in one record per item under `docs/lifecycle/`.
- `needs`: a named residual class.

**K2 did not fire.** The registry holds 98 `needs` edges: 95 typed `{type, kind, path}` edges and 3 legacy strings, all `work:spec/direct-skill-lifecycle`. None carries a completion receipt. 64 edges hang off 41 outstanding entries. By the item that waits, 33 edges sit on intents, 21 on specs, 4 on briefs, 3 on note or design files, and 3 on slug-only items. Every prerequisite path exists on disk: 38 specs, 19 intents, and 4 briefs, plus the 3 legacy strings. Every waiting item has a path or a slug.

**K3 did not fire as a stored fact. One behavior depends on position.** The registry's own header and the `workspace-status` skill both say list order is non-semantic: it must not decide routing, dependency satisfaction, processor selection, or dispatch. Where a comment explains an order, it restates `needs` ("Ordered by what unblocks what"). No artifact or comment records priority across parents. The one use of position is the suggestion menu. `next_queue` and `next_shape` name the first ready item in list order. All 10 `work.queue` entries sit in one initiative but span three parents: 2 under one brief, 3 under another, and 5 with no brief. Shaping backlogs sit in four initiatives, so `next_shape` already picks across initiatives by where a section happens to sit in the file.

**K4 did not fire.** The 51 file-backed captured items point at 51 different files, and none shares a file with another entry. Two of those files are a spec's verification ledger rather than a record of the item. The 24 items with no file are legacy. `work-intake`'s shipped contract already writes the artifact first and registers it second, including for "remember for later", so each captured item has a per-item home.

**The status-reading line fired.** Derived outstanding work would list 75 shipped specs as outstanding unless status reading changes:

- 59 specs write text after the status word, such as `Shipped (2026-09-11)`. `closure_terminality.is_spec_terminal` matches whole strings, so it treats each as not terminal.
- 16 specs write status as `**Status:**` with no leading dash, or as front-matter `status:`. The shipped field reader does not see them, and an unknown status counts as live. All 16 are Shipped.

The 195 count above reads the leading status word and leaves out those 16 specs. An exact-match reader over the same files returns 270.

### Verdict — survived

No kill line was crossed. Orientation needs no registry fact that the headers cannot supply, apart from a residue that is smaller than the owner framed. Queue order is not a stored fact today. It is one menu behavior that reads file position. The residue is:

- **Dependency edges.** 64 outstanding `needs` edges.
- **Captured items not written as an intent, brief, or spec.** 75 entries: 51 with a file of their own, of which 49 carry no status line, and 24 with no file.
- **One behavior, not a fact.** The first-in-list suggestion in `next_queue` and `next_shape`.

What travels into `decompose-intent`:

- **C1 — A dependency edge lives on the item that waits.** Write each edge as a header field on the waiting artifact, naming its prerequisite by typed reference. One edit touches one file, and no shared list is needed. The field must be a named dependency field distinct from FEAT-0002's non-blocking `Related intents:`. RFC-0106 D3 proposes the name `Depends on:`, with comma-separated RFC-0103 typed references. The three intents that already carry `Depends on:` say their enforceable edge is the registry `needs` entry, and no script reads that field today. The spec names the field and its reader.
- **C2 — A captured item gets its own file with a status line.** Give the 24 file-less items their own records first. Give the 49 file-backed items without a status line one, and move the 2 that point at a verification ledger to an item-specific record. The 3 edges that wait on file-less items move once those items have files.
- **C3 — Order is decided, not migrated.** The first-in-list suggestion is either replaced by a deterministic rule over derived facts or removed. If the owner wants human priority recorded, it goes on each item as a header field, never as a list. Removing the suggestion needs RFC-0105 D3's deliberate-removal authority, which RFC-0106 D3 proposes to supply.
- **C4 — Derived status must read the leading status word.** The derived outstanding view must agree with the artifact's own status for the 59 specs with trailing text and the 16 written in another form. Settled 2026-10-08: the terminality reader now reads the leading word, and the 16 status lines use the standard form.
- **C5 — Stop registration in the order the authority allows.** The headers can supply orientation now. Each registry writer that an accepted contract requires stays in place until that contract is amended. The owner findings below list those contracts.

### Findings for the owner

These conflict with accepted records or sit with another artifact, so they are recorded here and not acted on.

- **ADR-0119 D4 says an intent's lifecycle state comes from the workspace record.** Derived orientation reads it from `Status:` instead, as RFC-0105 D3 and the `intent-navigation` spec do. In practice all 100 registered intents are Draft, and 36 Accepted intents are not registered. Stopping intent registration needs an amendment to D4 or a superseding record; RFC-0106 D1 proposes the partial supersession.
- **RFC-0105 D3 names priority as workspace-only state, but no canonical source records it.** The registry and the skill both call list order non-semantic. The disposition record should say whether the first-in-list suggestion is kept somewhere or removed, and cite the authority.
- **The derived outstanding view would have listed 75 shipped specs as outstanding.** Settled 2026-10-08 by the pre-work repairs under C4; the `intent-navigation` spec's AC-0058 reads the leading status word.
- **Four accepted contracts still require registration.**
  - `docs/product/AGENTS.md` makes registered spec membership the brief's confirmation evidence. The derived equivalent is the spec's own `Brief:` header.
  - FEAT-0005 assigns `close-work` a terminal registration move.
  - FEAT-0001 renames an intent and its registry path together.
  - RFC-0064 defines `workspace.toml` and `workspace-status`.

  Each needs an amendment or a superseding record before its writer stops. RFC-0105 D3's gates are unchanged.
- **The registry is already the less complete outstanding list.** It misses 52 outstanding artifacts that the headers find, and the headers miss none of the 143 artifacts it holds. That is evidence for the owner direction, and it comes from one snapshot.

### Validation hook

Desk evidence settles where each fact can live. It does not show that work stays coordinated once registration stops.

```
validation_hook:
  assumption: With registration stopped for anything the headers supply, dependency edges on the waiting artifact and captured items in their own files keep coordination safe, and no repository-wide mutable file takes the registry's place.
  kill_condition: Proceed to delete the registry only if, over at least two weeks of normal work after derivable registration stops, (a) no maintainer or agent session misses outstanding work that navigate-intents should have listed, checked weekly against the registry comparison defined below, (b) no needs edge is lost in the move to headers, checked by an edge-for-edge comparison, and (c) no single file other than the artifacts themselves shows up in more merge conflicts than workspace.toml did over the two weeks before the stop.
  activity: to-validate. A staged trial run by the owner after navigate-intents ships, with the comparisons scaffolded by plan-validation. Not run. External adopters stay outside this trial and are covered by RFC-0105 D3's compatibility-closure gate.
```

A second hook covers dispatch, which the 2026-10-08 de-risk did not test:

```
validation_hook:
  assumption: Header-derived readiness (own Status:, sibling plan.md, Depends on: targets) admits exactly the specs that workspace-status's canonical reconciliation admits as ready or active today, apart from removals that are recorded and accepted.
  kill_condition: Keep spec registration and its writers if replaying argless and named work-loop starts and resumes over a frozen corpus finds even one spec whose ready or active result differs from canonical.ready or canonical.active with no accepted removal entry, checked for each dispatch case under § RFC-0106 inputs. A spec admitted because the retired unregistered_work refusal no longer applies passes, as an accepted removal.
  activity: to-validate. The dispatch specification's equivalence replay, run before the spec registration writer stops. Not run.
```

### Registry comparison, owned here

Moved from the `intent-navigation` spec on 2026-10-08 by the owner, because it measures the registry, not the navigator. The weekly comparison the validation hook names compares `navigate-intents`' `outstanding` result with every `workspace.toml` entry in a non-terminal collection, and classes each difference.

- **Non-terminal collections:** `backlog.open`, `shaping_queue.backlog`, `shaping_queue.active`, `brief_queue.draft`, `brief_queue.ready`, `brief_queue.executing`, `work.queue`, and `work.active`.
- **Terminal collections:** `work.shipped`, `brief_queue.shipped`, `brief_queue.withdrawn`, `brief_queue.cancelled`, and `backlog.closed`.
- **Allowed differences:**
  - `captured_item` — a registry-only entry that names no intent, brief, or spec file;
  - `legacy_shape` — a registry-only bare `spec/<slug>` string or `{slug = ...}` table;
  - `registry_stale` — a registry-only entry whose file exists and whose own `Status:` is terminal;
  - `registry_closed_stale` — a result item whose own `Status:` is not terminal and which appears only in terminal collections;
  - `registry_omission` — a result item absent from every collection.
- **Failing differences:** a registry-only entry whose file's own `Status:` is not terminal, and a result item whose own `Status:` is terminal.

The specification this intent decomposes into owns the comparison's implementation and its run cadence.

### RFC-0106 inputs, if it is accepted

If [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) is accepted, its D1 table and D3 assign these to specifications this intent decomposes into, beyond C1 to C5. Its acceptance is the authority under RFC-0105 D3 for each change of accepted behaviour below.

- **Dispatch and resume from headers.** `work-loop` and `workspace-status` treat a spec as ready from its own `Status:`, its sibling `plan.md`, and its `Depends on:` targets, and as active from its own `Status:`. The specification's behavioural-equivalence record reproduces, or records an accepted removal for, each case the canonical reconciliation handles today: a cross-repository dependency settled by its containing brief's coordination receipt; a local dependency on a pruned target settled by its completion receipt; a dependency on a defect; a cooled dependency; a brief whose child scope is unknown; and the provenance and fail-closed findings that keep a spec out of the ready set. The `unregistered_work` refusal, emitted by `workspace-status`'s spec selector and relayed by `work-loop`, is removed without a replacement, as an accepted removal under RFC-0106 D1, recorded in the equivalence record. The 2026-10-08 de-risk tested orientation only, so this is untested.
- **Choosing among several ready specs.** An argless `work-loop` start that finds more than one ready spec lists them and asks, replacing selection of the first `canonical.ready` item. No rule may choose one automatically; RFC-0106 D3 allows a stated deterministic rule only for the suggestions.
- **Shaping-item routing.** `work-loop`'s shaping-item guard matches a captured-item file that carries a `Type:` line, routes it by today's type-to-skill mapping, and matches nothing else. Today the guard matches no registry entry, so routing such a file is an intended change, recorded in the equivalence record.
- **Cross-pack shaping intake.** Producers such as `run-okr-cascade`, which registers each OKR gap as an intent entry, write a captured-item file instead. The specification owns this jointly with the producing pack.
- **Captured-item file shape, reader, and migration.** C2's file also carries a `Kind:` line from the registry entry's `kind`, and a `Type:` line only where the entry carries a shaping `type`. Slug-only entries with no `kind` get one assigned by the migration, listed in its equivalence record. A reader for those files is part of the same specification.
- **Dependency edge migration.** Beyond C1's field and reader, the specification migrates the 98 `needs` edges into `Depends on:` headers, compared edge for edge before and after.
- **Brief coverage evidence.** `author-delivery-brief` and the brief coverage lint take a spec's membership from its own `Brief:` header, so spec registration stops serving as that evidence.
- **When registration stops.** Registration for an artifact type stops in the release in which the last responsibility its entries feed ships its replacement, and the contract that required it is amended in that release.

## Shaping review

The isolated intent-mode review completed cleanly on 2026-10-02 at revision `sha256:1c3a2709165c3c9b629ba5f490308b1fec4f4a9aef34e39f29dc6cb582a9d29a`, and again on 2026-10-08 after the de-risk record and the RFC-0106 inputs were added, at git blob `9244d5ca1f158b5923edbe9c6d653c110f407c14`, the text before this binding note. Adding the note is nonmaterial.

## Decomposition

None yet. The bet survived `de-risk-intent` on 2026-10-08; `decompose-intent` is next and must carry the constraints in the De-risk record.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`
- **Authority:** Platform Core maintainer

Framed from RFC-0105 D3 and its four retirement gates on 2026-10-02. The RFC establishes full retirement as the target but leaves every current surface supported until the accepted specification proves inventory, disposition, equivalence, and closure.
