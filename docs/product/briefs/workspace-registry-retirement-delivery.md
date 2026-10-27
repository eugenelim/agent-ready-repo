# Brief: coordinate repository work from the artifacts themselves and retire workspace.toml

- **Slug:** `workspace-registry-retirement-delivery`
- **Received:** 2026-10-25
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Executing
- **Cut-closed:** <!-- Required before Status: Shipped, refused while Status: Draft. -->
- **Ready confirmed:** 2026-10-25 by the repository owner, after a clean independent delivery-brief shaping review of git blob `1af95a54bf2decb6ece31d7c3a4acb866e1f1e69`. Amended 2026-10-27 at the repository owner's request: the list-order risk rewritten to match FEAT-0034's settled answer, after an independent delivery-brief shaping review of git blob `9083db6589a9fa6d858408a2ea7125d5f6a62633` left no sustained finding.
- **Slices confirmed:** 2026-10-25 by the repository owner: candidate slices 1 to 9, in the order listed. Slice 1 is materialized first, because its inventory settles questions the later slices depend on; each later slice is materialized as a spec when it is picked up. Amended 2026-10-26 by the repository owner: the two-week trial cut, slice 5 shrunk to a script run once before each registration stop, and the appetite cut from about five weeks to about three, after a clean independent delivery-brief shaping review of git blob `1fb9d8d2c234e74aabd608c77e590581e18c8744`.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/FEAT-0034-workspace-registry-retirement.md`](../intents/FEAT-0034-workspace-registry-retirement.md), decomposed to this brief by the owner on 2026-10-25.
- **Parent intent:** intent:workspace-registry-retirement

## Outcome

Today every coordination change edits one shared file, `workspace.toml`. A maintainer or agent should be able to capture, order, dispatch, and close repository work by editing only the artifact the work is about. Every fact the registry holds today has to keep one named home, and no coordination safety can be lost. When this brief is delivered, the registry and its read path are gone. Adopters move their own registry content with one repair run in a session.

## Success metrics (optional)

- Every `needs` edge in the registry at migration time appears as a `Depends on:` header on the waiting item, in an edge-for-edge comparison.
- Every captured item in the registry at migration time lives in its own file with a `Status:` line.
- Run just before each registration stop, the registry comparison finds no failing difference.
- The dispatch replay finds no spec whose ready or active result differs from `canonical.ready` or `canonical.active` without an accepted removal entry.
- An adopter's registry converts with one repair run. Every behavior that is not carried over is named in the retirement spec with its removal authority.

FEAT-0034's [de-risk record](../intents/FEAT-0034-workspace-registry-retirement.md#prototype-results) holds the 2026-10-08 baseline: 98 `needs` edges and 75 captured items.

## Scope / Non-goals

**In scope:**

- The one workspace-retirement spec RFC-0105 D3 requires. It holds the consumer inventory, the per-fact disposition, the equivalence evidence, the compatibility-closure checklist, and the Platform Core maintainer's certification of all four gates.
- Accepted authority, such as an RFC-0105 or RFC-0106 errata entry, for each behavior the repair does not carry over.
- `Depends on:` on specs and briefs, and its reader. The canonical reconciliation blocks on `Depends on:` instead of `needs`, with the blocking equivalence record.
- The captured-item file shape (`Status:`, `Kind:`, and `Type:` where a shaping type exists) and its reader. `work-loop`'s shaping-item guard routes a captured-item file that carries a `Type:` line, as RFC-0106 D1 says. Every captured-item writer moves to writing these files and stops registering them: `work-intake`, and producers such as `run-okr-cascade` jointly with the producing pack.
- An optional priority header field and its reader.
- The registry comparison defined in FEAT-0034 § Registry comparison, run as slice 5 says.
- Removal of the first-in-list `next_queue` and `next_shape` suggestions.
- Stopping each registration writer, with the amendment to the contract that requires it in the same release, citing RFC-0106 D1:
  - ADR-0119 D4 and FEAT-0001's lockstep rename, for intents;
  - RFC-0064's `receive-brief` writer row, for briefs;
  - FEAT-0005's terminal move for `close-work`, split by type: intents and briefs with their registration, specs with theirs;
  - RFC-0064 D4, its `work-loop` writer rows, and the brief-coverage rule in `docs/product/AGENTS.md`, for specs.
- Brief coverage evidence from each spec's own `Brief:` header, read by `author-delivery-brief` and the brief coverage lint.
- Header-derived dispatch in `work-loop`. An argless start that finds several ready specs lists them and asks. The `unregistered_work` refusal is removed.
- One repair, run in a session, that each fact-class slice extends with its own migration step.
- Compatibility closure:
  - shrink `workspace-status` to the repair;
  - move seeds, manifests, guides, and operative references;
  - retire what is left of RFC-0064's registry definition;
  - delete `workspace.toml`.

**Non-goals:**

- A replacement repository-wide registry, generated index, or assembly step.
- Any shipped skill other than the repair reading the old `workspace.toml` shape after its replacement ships. A reader may still refuse unmigrated content and name the repair.
- Retiring the `workspace-status` skill name. A later release does that under RFC-0067.
- Tracker sync reading the priority field. [External tracker projection](../intents/CAP-0004-external-tracker-projection.md) owns that.
- Any change to `navigate-intents`, including its readiness bridge, except keeping the bridge's pinned copy of the `workspace-status` finding table equal to the engine's when a slice adds a finding code, as the bridge's parity test requires (owner decision, 2026-10-25). The [readiness hand-over spec](../../specs/intent-view-readiness-handover/spec.md) gives the bridge's re-pointing to the `navigate-intents` owner, in the release where dispatch moves.
- FEAT-0004's end state. FEAT-0004 amends it in its own record.
- Rewriting frozen records or completed intents that name `workspace.toml` only as history.

## Constraints / Appetite

Appetite: about three weeks, set by the owner on 2026-10-26. That is about two and a half weeks for slices 1 to 8, then about half a week for slice 9. If slices 1 to 8 run past about three weeks, re-cut the remaining slices rather than extend. The basis is the pace of the [intent navigation](intent-navigation-delivery.md) and [intent identity](intent-identity-and-registration.md) briefs.

- Every registry writer stays until the release that amends the contract requiring it (FEAT-0034 C5, RFC-0106 D1).
- A type's registration stops only when every responsibility RFC-0106 D1's table lists for its entries has shipped a replacement.
- `workspace-status` and `workspace.toml` stay supported until RFC-0105 D3's four gates pass and the Platform Core maintainer certifies them.
- Blocking never lapses. An unmigrated `needs` edge makes the reconciliation refuse and name the repair. It never reads as no dependency.
- Skill scripts use the standard library only (ADR-0074).
- Every corpus read goes through the blessed confinement helpers.

## Assumptions / Risks

- **Dispatch equivalence is untested.** The 2026-10-08 de-risk tested orientation only. The dispatch replay may find a case the headers cannot reproduce, for example a cross-repository dependency settled by a coordination receipt. A failure keeps spec registration in place.
- **External adopters are invisible from here.** The no-seam decision drops behavior that lives outside tracked files. Each such removal needs accepted authority, and upgrade notes are only the notice.
- **A list-order reader added outside two skill directories could go unseen.** [FEAT-0034 § Unresolved questions](../intents/FEAT-0034-workspace-registry-retirement.md#unresolved-questions) holds the answer to where list order is read: each known reader is a `reads_order = true` row in the [inventory](../../specs/workspace-retirement/inventory.toml), and the `entry position` row of the retirement record's [Disposition](../../specs/workspace-retirement/retirement-record.md#disposition) removes list order for all of them. Each reader leaves in a named slice. Slice 6 removes the `next_queue` and `next_shape` suggestions and disposes of the next-actions contract that picks them. Slice 8 removes `work-loop`'s first-ready start in favour of list-and-ask, and in that release the `navigate-intents` owner re-points the readiness bridge. Slice 9 shrinks `workspace-status` and its packaged engine copy to the repair, and moves the two guides and drops their first-ready instruction. Until slice 9 deletes `workspace.toml`, a new file in the `workspace-status` or `work-loop` skill directory already falls under an inventory row marked `reads_order`. Anywhere else, nothing checks that mark. The roster inventory check makes each non-exempt tracked file that names `workspace.toml`, `workspace-status`, or `workspace_status` carry a row, but a new order reader outside those two directories is seen only if someone marks its row `reads_order`. A reader that names none of those words gets no row unless someone adds one. Either way, the `entry position` disposition would not name it.
- **Contention may move rather than vanish.** No metric measures a new hot file after the stops. The non-goal against a replacement registry, generated index, or assembly step is the guard, and review checks each slice against it.
- **Five accepted contracts still require registration.** RFC-0106 D1 names them: RFC-0064 D4 and its writer rows, the brief-coverage rule, FEAT-0005, FEAT-0001, and ADR-0119 D4. Each writer slice is blocked until its contract is amended. Those amendments are governance work, not code.

## Delivery slices

Numbers give the delivery order. Slices 2 to 6 may start once slice 1 lands, and slice 5 also needs the navigator's outstanding-work view. Each slice that stops a writer names its own dependencies.

1. **Retirement spec.** This slice creates the spec RFC-0105 D3 names, with all four sections. It fills in the consumer inventory and the per-fact disposition. The inventory lists the `navigate-intents` readiness bridge. The disposition names each behavior the repair drops and its authority. It also settles FEAT-0034's two open questions: other uses of list order, and other contracts that need amending. It records whether `author-delivery-brief` and the brief coverage lint already take coverage from `Brief:` alone, and names what is left to change if not.
2. **Dependency edges on the waiting item.** `Depends on:` on specs and briefs, and its reader. The canonical reconciliation blocks on `Depends on:` and refuses unmigrated `needs` content. The slice adds the repair step that migrates `needs` edges, and runs it here with an edge-for-edge comparison. Its blocking equivalence record goes into the retirement spec. It covers the coordination receipt, the pruned target, the defect, and the cooled dependency.
3. **Captured items in their own files.** The file shape, its reader, its repair step, and shaping-item routing from a file that carries a `Type:` line. Every captured-item writer then moves to the file and stops registering, with the contract amendment that requires it. That writer stop depends on slices 2 and 5.
4. **Priority header field.** The optional field and its reader. No repair step is needed, because the registry stores no priority today.
5. **Registry comparison.** Depends on the navigator's outstanding-work view from the [intent navigation brief](intent-navigation-delivery.md). A script that compares the navigator's outstanding work with the registry and classes each difference, as FEAT-0034 § Registry comparison defines. It runs once just before each registration stop: captured items in slice 3, intents and briefs in slice 7, and specs in slice 8. It has no weekly cadence and no CI job. Each run's result is recorded in the spec that stops that registration. A failing difference keeps that type's registration, under FEAT-0034 § Validation hook.
6. **Suggestions removed.** Remove `next_queue` and `next_shape`, under RFC-0106 D3.
7. **Intent and brief registration stops.** Depends on slices 2, 3, 5, and 6, and on the navigator's outstanding-work view from the [intent navigation brief](intent-navigation-delivery.md). Amend ADR-0119 D4, FEAT-0001's lockstep rename, RFC-0064's `receive-brief` writer row, and FEAT-0005's terminal move for intents and briefs. Stop every writer of intent and brief entries, including `close-work`'s collection moves for them.
8. **Dispatch from headers.** Depends on slices 2, 5, 6, and 7, and on the navigator's outstanding-work view. Header-derived readiness, list-and-ask, removal of `unregistered_work`, and brief coverage taken from `Brief:` alone, with whatever slice 1 found left to change. The dispatch replay goes into the retirement spec. Spec registration stops only if the replay passes. RFC-0064 D4, its `work-loop` writer rows, the brief-coverage rule, and FEAT-0005's terminal move for specs are amended in the same release, and `close-work` stops moving spec entries.
9. **Compatibility closure and deletion.** Gated on all four RFC-0105 D3 gates. Shrink `workspace-status` to the repair, publish the upgrade notes, and move seeds, manifests, and operative references. Complete the closure checklist and record the certification in the retirement spec and the retiring change. Then delete `workspace.toml`.

## Spec map

The Status column is derived from each spec; it is not hand-edited.

| Spec | Status |
| --- | --- |
| `workspace-retirement` | <auto> |
| `depends-on-headers` | <auto> |
| `captured-item-files` | <auto> |
| `priority-header-field` | <auto> |

## Governance references (optional)

- [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md): D3 sets the four retirement gates, the one retirement spec, and who certifies them.
- [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md): D1 says when each registration stops and names the five contracts to amend. D3 puts dependencies and priority on the item and authorises removing the suggestions.
- [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md): D4 and its writer rows require registration. Slices 7 and 8 amend them, and slice 9 retires the rest of its registry definition.
- [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md): D4 reads intent lifecycle from the workspace record. Slice 7 amends it.
- [RFC-0108](../../rfc/0108-skill-html-view-standard.md): D3 admits the readiness bridge that slice 8's release re-points.
- [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md): the clean-retire convention for the later `workspace-status` name retirement.
- [ADR-0074](../../adr/0074-the-work-loop-owns-its-state-lock.md): skill scripts are standard-library-only.

## Design artifacts (optional)

- [FEAT-0034 § De-risk record — 2026-10-08](../intents/FEAT-0034-workspace-registry-retirement.md#de-risk-record--2026-10-08): the registry measurements, constraints C1 to C5, and both validation hooks.
- [CAP-0003 § De-risk record](../intents/CAP-0003-workspace-coordination-reorganization.md#de-risk-record): every tracked responsibility has a destination class.
