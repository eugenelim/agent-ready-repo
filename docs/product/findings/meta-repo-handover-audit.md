# Meta-repo to component-repo handover: audit and proposed flow

Audited 2026-10-10. Scope: how a platform feature intent defined in a value-stream
meta-repo reaches each component repo as a delivery brief, and how delivery status gets
back up. Companion to [`pe-skill-routing-survey.md`](pe-skill-routing-survey.md).

## Answer

There is no working handover today. Every guide says each per-component brief "crosses
into its component repo", and no skill can carry it there.

The fix reuses a pattern Core already has for trackers:

1. The meta-repo writes a per-component **slice**, not a brief.
2. The component repo **acquires** that slice through `work-intake`, pinning the meta-repo
   revision.
3. The component repo authors its own brief from it.
4. The meta-repo **reconciles** status by reading each component brief back as a
   receipt.

This makes the case for folding brief authoring into `work-intake`: on the component side,
acquire, admit, brief, and refresh become one lifecycle with one owner.

## How it breaks today

### Nothing moves the brief

- `decompose-intent` says "each brief then crosses into its component repo"
  (`decompose-intent/SKILL.md:96-97`), and so do ADR-0022 (`:70`) and
  `run-a-capability-across-a-value-stream.md:63`. None names how.
- `author-delivery-brief` writes only inside its own repository root (`:69-72`).
  `continue` needs "an existing, confined repository brief" (`:117`).
- Run in the meta-repo, it creates a meta-repo brief, registers it in the meta-repo's
  `workspace.toml`, and its slice step calls `new-spec` in a repo with no app code.

### Two authorities for one brief

- `decompose-intent` pins its briefs at `docs/product/briefs/<slug>.md` without saying
  which repo (`align-value-stream/SKILL.md:144-149`).
- A hand copy in the component repo then holds a second Status and Spec map. Nothing says
  which copy is canonical. This contradicts the skill's own "federate, never copy" rule.

### No source mode fits a sibling repo

- Source authority is closed to `repo-origin | tracker-origin`
  (`contracts/jsonschema/normalized-intake.schema.json:36-39`).
- A pasted brief claims `repo-origin`, whose refresh "never changes local requirements".
  Calling it `tracker-origin` fails with `refresh-unavailable`, because no profile exists.
- `intake-intent`'s copy-and-pin admission covers chat and vault intents only, not briefs
  from another repository.

### The parent pointer is not a cross-repo locator

- The brief template carries `Parent intent: <kind>:<slug>` with no repo or revision
  (`packs/core/seeds/docs/product/briefs/_template.md:18`).
- RFC-0083 (`:311`) requires a "durable parent-intent locator and coordination reference".
- `lint-traceability.py` (`:952-955`) accepts cross-repo ids shaped `x/y`, `x@v`, or
  `repo·slug`. A bare `intent:<slug>` in a component repo likely reads as `dangling`, a
  hard violation. This comes from reading the code, not from a run.

### Promised fields are missing

- `decompose-intent` stamps `contract@version`, a courier snapshot, and a provider or
  consumer role on each brief (`SKILL.md:93-95`). The Core brief template has none of
  these fields.
- RFC-0083 says the parent intent lists affected repos and their brief locators. The
  intent template has no field for that.

### Status has two disconnected stories, and neither flows up

- **Product-engineering:** a rollup table reconciled by hand, with statuses `delivered |
  in-progress | not-started | unknown` (`cross-component-rollup.md:39-46`).
- **Core:** reviewed coordination receipts, implemented for brief `needs` edges
  (`workspace-toml-schema.md:201-225`). Intent closure receipts are specified in RFC-0083
  (`:348-352`) but not built.
- Rollup statuses don't map to brief statuses. `Withdrawn` and `Cancelled` have no rollup
  value.
- No component-side step reports a shipped slice. The release side already uses a bot PR
  from each component repo to a config repo (RFC-0075 `:177`). Product work does not reuse
  it.

### Smaller breaks

- `frame-intent` says an `app` leaf "is" a brief (`intent-model.md:88`).
  `decompose-intent` makes a single shippable feature a delivery contract.
- Business-unit slices are "cut by component". `author-delivery-brief` says component work
  "is not independently shippable merely because it can be implemented separately"
  (`:186-187`).
- ADR-0022 and the value-stream spec still route through the deprecated `receive-brief`.
- `align-value-stream`, `catalog-currency.md:38-43`, and ADR-0022 D12 defer polyrepo
  structuring to `monorepo-extras`. That pack contains only `new-package`.
- Nothing detects a contract version bump in a component repo's courier snapshot.

## Proposed flow

### Who owns what

| Artifact | Lives in | Owns |
| --- | --- | --- |
| Feature intent | meta-repo | outcome; its affected repos are derived from its slices |
| Slice | meta-repo | what one component must deliver, and every cross-repo edge |
| Delivery brief | component repo | how that repo delivers it, Ready gate, specs |
| Receipt | meta-repo | a reviewed status read of one component brief at a revision |

The meta-repo never authors a delivery brief, so no brief has two copies.

### Steps

1. **Slice, in the meta-repo.** `intent decompose` at `business-unit` Scale writes one
   slice per component under `<output_dir>/slices/<feature>/<component>.md`. Each slice is
   a `normalized-intake.v1#handoff` body: outcome, boundary, and non-goals, plus the edges
   in [§ Slice edges](#slice-edges). The feature intent records `Decomposed: <date>
   slices`.
2. **Acquire, in the component repo.** `work-intake` acquires the slice through a
   `value-stream` source profile. It reads the slice at a named meta-repo revision and pins
   that revision.
3. **Author the brief.** `work-intake brief create` prefills the brief from the slice. The
   brief's `Parent intent` is the repo-qualified locator, which the traceability lint
   already accepts. `brief continue` keeps today's Ready gate, independent review, and two
   human confirmations.
4. **Refresh.** When the slice changes, `work-intake refresh` compares revisions. It uses
   today's per-field `keep-local | accept-source | revise-both` decisions and lifecycle
   locks. `Shipped` locks requirements.
5. **Reconcile, in the meta-repo.** `align-value-stream reconcile` reads each
   `Delivered by` brief at a revision. It writes a receipt on the slice when the brief is
   `Shipped`, and an observed-status line otherwise.

Pull-based reconcile keeps the rollup "a snapshot, not a live feed", as ADR-0022 requires.
A push channel (a component-side bot PR, as in RFC-0075) can be added later on the same
receipt shape.

### Decisions

- **Source mode:** reuse `tracker-origin` with a `value-stream` profile. Its refresh and
  approval rules already fit. "Tracker" becomes a misnomer, which the RFC records.
- **Transport:** read a local meta-repo checkout with `git -C <path> show <rev>:<file>`.
  The `github` pack's API read covers remote-only setups. Either one crosses Core's
  repository confinement, so the profile goes to `security-reviewer`. The checkout path
  is per machine, so it lives in user-scope config and is never committed.

## Slice edges

### Rules the edges follow

1. **Reuse an implemented edge before adding one.** Every slice edge below maps to a field
   a validator already reads, except `Delivered by`.
2. **One cross-repo locator form:** `<repo-id>/<kind>:<slug>`. The traceability lint
   already reads `/` as a cross-repo shape. Receipt `remote_ref` already accepts it,
   because it has no `@`, `?`, or `#`.
3. **Revisions travel in their own field,** as receipts already do with
   `accepted_revision`. They never ride in the locator.
4. **Each edge has one home.** The slice owns the down edge to the component brief. The
   feature intent's list of affected repos is derived from its slices, so RFC-0083's list
   needs no second copy.

`<repo-id>` is a short kebab name for each repository. The meta-repo's
`<output_dir>/value-stream.toml` lists them, which also gives `align-value-stream` the
explicit repo list it lacks today.

### The slice

Path: `<output_dir>/slices/<feature-slug>/<component>.md` in the meta-repo. Identity is
`slice:<Slug:>`, never the filename, following the intent rule.

| Field | Direction | Target | Syntax | Count | Reuses |
| --- | --- | --- | --- | ---: | --- |
| `Slug:` | identity | — | `<feature-slug>-<component>` | 1 | intent identity rule |
| `Parent intent:` | up | feature intent, same repo | `intent:<slug>` | 1 | lint up-edge with exact-kind match |
| `Component:` | lateral | component | `component:<namespace>/<name>` | 1 | lint `Component:` node id |
| `Contract:` | lateral | shared contract | `contract:<name>@<major> (provider\|consumer)` | 0..n | lint `contract:<name>@<N>` node id |
| `Needs:` | lateral, blocking | another slice | `slice:<slug>` | 0..n | becomes `needs[type=cross-repo]` downstream |
| `Delivered by:` | down | component brief | `<repo-id>/brief:<feature-slug>` | 1 | new; the `x/y` cross-repo shape |
| `coordination-receipts` block | status, up | component brief | today's receipt shape | 0..1 | `workspace-status` receipt checks |

The component brief's slug is the feature slug, so `Delivered by` is known when the
slice is cut. Acquisition refuses, and asks, if the component repo already holds a brief
with that slug.

A receipt is written only for `Shipped`, matching today's receipt rule. Non-final status
is a snapshot line, `Observed status: <brief status> at <revision> on <date>`. It is never
authoritative.

### The feature intent, in the meta-repo

- `Decomposed: <date> slices` is a new route next to `spec`, `brief`, `direct-light`, and
  `closed-empty`. It tells the relation checker to expect slices, not a local brief.
- **Fulfilled rule:** every slice holds a `Shipped` receipt, and any `Withdrawn` or
  `Cancelled` brief has a recorded decision.
- The rollup becomes a view over slices: one row per slice, using brief status words.

### The component brief, in the component repo

| Field | Value |
| --- | --- |
| `Parent intent:` | `<meta-repo-id>/intent:<slug>` |
| `Source / provenance:` | `<meta-repo-id>/slice:<slug>` plus the meta-repo revision |
| `Contract:` (new on the brief template) | copied from the slice; the slice revision pins the snapshot |

Its `workspace.toml` entry carries these values:
- `source.mode = "tracker-origin"`, with profile `value-stream`.
- `source.ref` set to the slice locator, and `source.revision` set to the meta-repo
  commit.
- `source.coordination` set to the parent intent locator. The field is parsed today but
  never read; this gives it its first reader.
- Each slice `Needs:` becomes a `needs[type=cross-repo, kind=brief]` entry on the other
  slice's `Delivered by` brief, satisfied by today's coordination receipt.

### Validator changes these edges need

- **Traceability lint:** resolve `<repo-id>/brief:<slug>` in the meta-repo against slice
  `Delivered by` values instead of rollup cells. In a component repo, accept a
  `<repo-id>/…` pointer as externally pinned when the entry's source pin names that repo.
  Today it would be unresolved.
- **Intent-delivery relations:** accept a repo-qualified `Parent intent:` on a brief as
  remote. Today the slug pattern rejects it. Add the `slices` route.
- **A slice shape check,** modeled on the intent shape check: required fields, one
  `Parent intent`, locator syntax, no `@` outside `Contract:`.

### Naming drift fixed on the way

- `decompose-intent` writes `parent-intent:`. It becomes `Parent intent:`, the spelling
  every reader matches.
- The rollup's `` `<repo>` · `<slug>` `` brief cell becomes `<repo-id>/brief:<slug>`. The
  lint cannot match the old cell today.
- "Delivery contract" names both a leaf spec handoff and a `surface_role`. Slices use
  `Contract:` only for shared interface contracts. The RFC should rename one of the two.

## Folding briefs into `work-intake`

### What it gives

- The component side becomes one skill with modes: `route` (read-only default),
  `acquire`, `intent`, `brief create`, `brief continue`, `refresh`, `remember`.
- `intake-intent`, `author-delivery-brief`, `author-brief`, and `receive-brief` retire.
  Their listing entries total 649 description characters.
- The handover above lives in one owner instead of three.

### What it costs

- **Governance.** ADR-0098 (accepted 2026-08-27) made these separate owners. A
  superseding ADR replaces its D1, D2, D4, D5, D8, and D9, plus an erratum to RFC-0099 D1.
- **Rejected option.** RFC-0099 rejected "one generic shaping orchestrator". The ADR must
  show this is an intake lifecycle, not shaping.
- **Write-capable default.** `work-intake` already holds `Write Edit Bash` and would gain
  `Agent`. The mode guidance requires the default to behave read-only and every write
  mode to need an explicit transition naming target and scope. Today's "the handoff is
  not approval" rule must hold at each switch into `intent` or `brief`.
- **Permission pins.** `test_work_intake_surface.py:106-110` pins minimal tools per skill
  and must change.
- **Alias removal.** The aliases can go no earlier than 2026-11-26 (90 days after the Core
  2.14.0 deprecation on 2026-08-28). Removal needs a named Approver decision and the ALIAS-01
  old-prompt routing fixture.
- **Callers to migrate:**
  - 35 skill files in other packs.
  - 4 tracker eval matrices.
  - About 20 test files.
  - About 105 guide mentions.
  - `intake_router.py` processor strings.
  - `brief_shape.py`, which `close-work` imports by path.

## Recommended order

1. Write one RFC covering the `intent` consolidation, the `work-intake` fold, and the
   meta-repo handover. They share the contracts and the release.
2. Ship the handover contract first: slice artifact, repo-qualified parent locator, brief
   template fields, `value-stream` profile, and receipt-based rollup. It works with
   today's skill names.
3. Fold the skills in the next major release of Core and `product-engineering`, timed with
   the alias removal window.
