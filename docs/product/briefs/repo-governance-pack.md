# Brief: Rename governance-extras to repo-governance and add decision routing, decision health and governance setup as modes

- **Slug:** `repo-governance-pack`
- **Received:** 2026-10-25
- **Owner:** eugenelim
- **Status:** Executing
- **Cut-closed:** <!-- Required before Status: Shipped, refused while Status: Draft. Replace with an ISO 8601 date then evidence once the cut is final. -->
- **Source / provenance:** [RFC-0110](../../rfc/0110-repo-governance-pack.md) with its two 2026-10-25 errata (`sha256-bytes-v1:598d683510c1b9f3842065a6a03c9837e7cb312c484a67d26b86359ff10ac8b6`).

## Outcome

A repository that installs one pack can answer four questions: who decides, how to
decide, what was decided, and whether it is still current.

- The pack is called `repo-governance`, so its name says what it does. It still works
  with or without core.
- An adopter on `governance-extras` 1.x, using an agentbundle release that carries the
  hint, who runs `install` or `upgrade` against a catalogue at or after the rename is told the pack was renamed and given the three
  migration steps, instead of "not found".
- Someone unsure how to decide is routed to the right record, or to an existing decision
  they can reuse.
- Decisions that have come due, been superseded, or lost their check are reported
  instead of found by accident.
- Teams that outgrow one maintainer get help drafting decision rights.

## Success metrics (optional)

Each comes from RFC-0110's validation section or D3's completion check as amended by its
errata, except the activation metric, which the owner added on 2026-10-25 because of
RFC-0107's erratum.
Each is measured in the slice that owns it.

- **Rename hint:** on Git, local-path and archive catalogue sources at or after the rename
  release, `upgrade --pack
  governance-extras` and `upgrade --all` print the rename and the three steps, change
  nothing, and the steps then complete in order without `--force`. `iac-terraform` ends on
  its new requirement, including when it was recorded from a pre-rename archive or has no
  recorded source; in both cases the hint states the source change. Under `upgrade --all`,
  an install recorded from a pre-rename archive upgrades unchanged, because that archive
  still contains `governance-extras`.
- **Rename completeness:** a search for `governance-extras` returns only frozen files,
  fixtures, the rename-map entry, and surfaces that must name the old name: the migration
  text in the changelog and README, the hint's tests and fixtures, and the live records
  about the rename (this brief and the rename spec and plan), as
  [RFC-0110's second erratum](../../rfc/0110-repo-governance-pack.md#errata) admits. The
  rename spec owns the exact exception list.
- **Stage 2 seam:** on `new-rfc`'s routing eval examples, `navigate-decisions route` and
  core's work loop never give contradictory routes.
- **Stage 5 accuracy:** on this repository's `docs/adr/`, every `health` finding is real
  when checked by hand, every "needs a person to judge" item really is prose-only, and it
  reports every due trigger and missing signal that a hand check of `docs/adr/` finds.
- **Mode activation:** each mode's spec measures the host skill's positive trigger rate
  before the mode is added, sets a floor below that baseline, and passes only if the rate
  after the mode is added stays at or above the floor. The floor is at most 3 percentage
  points below the baseline, the margin RFC-0107 used. The new mode's own queries must
  load the host skill at or above the same floor.

## Scope / Non-goals

**In scope:** four slices, in the erratum's D6 order. Each adds a mode to an existing
skill, except the rename.

1. **Rename (D3).**
   - `packs/governance-extras/` becomes `packs/repo-governance/` at 2.0.0, with display
     name "Repository Governance". Every live surface is renamed under RFC-0110's
     live-versus-frozen rule.
   - A catalogue-owned rename map, `governance-extras` → `repo-governance`, that travels
     with Git, local-path and release-archive sources. The old name stays in it for good.
   - `install` and `upgrade` print the rename hint instead of "not found", change nothing,
     and never install the new name by themselves.
   - `iac-terraform` requires `repo-governance ^2.0` and takes a minor bump.
     `profiles/full-ceremony.toml` lists the new name.
   - An agentbundle release that carries the hint.
   - The three migration steps in the changelog and the `repo-governance` README, for
     adopters on an older CLI who never see the hint.
   - One PR. Outside tests, fixtures, eval updates and release fragments, its diff holds
     only: renamed names and paths, version bumps, the rename map, the map-lookup and hint
     code with its D3 trust rules, and the migration text above. The rename spec owns the
     exact list.
     Tests cover each catalogue source shape against the real command and each D3 trust
     rule.
2. **Stage 2, how to decide: `navigate-decisions route`.**
   - A read-only mode that holds `new-rfc` step 0's routing, including its reuse route,
     which searches for an existing decision.
   - It adds an advice step (whom to consult) and a one-way or two-way door check.
   - `new-adr` fills its existing `Consulted` field from that advice step. No new field.
   - `new-rfc` keeps its step 0 and `new-adr` keeps its "When to invoke" checks. Both
     point to `route` when the route is unclear.
3. **Stage 5, keep current: `navigate-decisions health`.** A read-only mode. It reports
   `Revisit if:` triggers whose date or version has passed, and lists prose-only triggers
   as "needs a person to judge". It also reports superseded ADRs still cited as current by
   an Accepted record, `Confirmation` signals naming a missing file, and a count of ADRs
   with no `Confirmation` block. It never runs checks.
4. **Stage 1, who decides: `new-rfc governance`.**
   - A mode that drafts or amends `GOVERNANCE.md`, may draft `CODEOWNERS`, and may propose
     a `CHARTER.md` link to `GOVERNANCE.md`.
   - It stays silent in a single-maintainer repository that did not ask.
   - It is the only writing stage, so its spec adds the confined write operation to
     `file_safety` and records it in `AGENTS.md`.

**Non-goals:**

- Stage 4, enforce: proposing checks, `AGENT_RULES.md` rows, lint rules or fitness tests.
  The erratum cuts it with no follow-on.
- A new skill. Every stage ships as a mode of `navigate-decisions` or `new-rfc`.
- Write modes on `navigate-decisions`. It stays read-only.
- Automatic pack aliases that install or upgrade the new name for an adopter.
- Moving ownership of core's starter files `AGENT_RULES.md`, `CHARTER.md` or `AGENTS.md`.
- AI-agent policy, guardrail or compliance tooling, including runtime decision tracing,
  where agent actions are recorded as a decision graph and checked while the agent runs.
  That would need its own RFC.
- Editing frozen records that name `governance-extras`, or adding errata to them.
- Live dashboards, notifications or issue-tracker sync.
- Approval workflows that circulate a document or collect sign-off.

## Constraints / Appetite

- **Order is fixed by D6 as amended:** rename, then stage 2, stage 5 and stage 1. New
  modes land under the final pack name once. Stage 2 comes before stage 1 because stage 1
  refers to it.
- **Each slice is its own spec**, built through core's work loop.
- **Each mode stays whole on its own**: it works when the other modes are not invoked.
- **Trust model binds every spec.** The five general rules and the stage 1, 2, 5 and D3
  blocks in [RFC-0110 § Trust model](../../rfc/0110-repo-governance-pack.md#trust-model)
  become acceptance criteria in the spec they name. The D3 block binds the rename hint.
- **[RFC-0110 D4](../../rfc/0110-repo-governance-pack.md#d4--core-keeps-its-starter-files)
  binds stage 1:** core keeps its starter files, and stage 1 only proposes edits to them.
- **Security:** the rename spec and the specs for stages 1, 2 and 5 each get a spec-stage
  security pass before they are built.
- **Appetite: about 4 weeks**, from 2026-10-26 to 2026-11-20, set by the owner on
  2026-10-25.
- **No slice is cut by the team:** a slice that does not fit the appetite is flagged to
  the owner, who decides. The rename and stage 5 are never cut.

## Assumptions / Risks

- **The rename is a one-way door for adopters.** Adopters on an older CLI still see "not
  found"; only slice 1's migration text reaches them.
- **Between migration steps 1 and 3, `iac-terraform` lists an unsatisfied requirement.**
  No command checks this between installs; step 3 clears it.
- **Rename churn can hide real change.** Review checks the rename diff against the rename
  spec's allowed set.
- **Modes may load less often than narrow skills.** RFC-0107's erratum measured a 12 to
  14 point drop when nine skills folded into modes. Each mode's spec measures activation;
  a mode that fails may split into its own skill, which needs a new erratum.
- **`new-rfc governance` writes files that steer reviews** (`GOVERNANCE.md`,
  `CODEOWNERS`). RFC-0110's stage-1 trust block governs those writes.
- **Stage 2 may conflict with core's work loop.** The work loop picks light or full build
  mode; `route` picks which record to write. The stage-2 spec names this seam and tests
  it.
- **`route` overlaps `new-rfc`'s triggers.** A "how should I decide" request can load
  `new-rfc` instead of `navigate-decisions`, whose description today excludes creating
  records. The stage-2 spec decides the description change and measures how often route
  queries load `navigate-decisions` versus `new-rfc`, using the mode-activation metric's
  baseline-and-floor method.
- **`governance` sits beside `new-rfc`'s mandatory step 0.** Step 0 routes before
  anything else and can return early, and the skill's opening scopes it to RFCs in
  `docs/rfc/`. The stage-1 spec decides whether the mode runs, bypasses or relies on
  step 0 for the RFC-0091 route choice.
- **Stage 1 may add ceremony** to a single-maintainer repository.
- **Accepted:** dependency checks match by name and version only, so another catalogue's
  `repo-governance` would satisfy `iac-terraform`.

## Rabbit holes (optional)

- An empty `governance-extras` stub release. The RFC rejected it: a stub would install
  silently and satisfy `iac-terraform` with nothing.
- Renaming the build-pipeline fixture pack under
  `packages/agentbundle/tests/build_pipeline/fixtures/packs/governance-extras/`. It models
  a generic pack, and renaming it tests nothing new.

## Spec map

| Spec | Status |
| --- | --- |
| `repo-governance-rename` | Implementing |
| `navigate-decisions-route` | Draft |
| `navigate-decisions-health` | Draft |
| `new-rfc-governance` | Draft |

## Governance references (optional)

- [RFC-0110](../../rfc/0110-repo-governance-pack.md): the direction this brief delivers,
  including the trust model every slice inherits. Its Errata section records the
  stage-4 cut and the move to modes.
- [RFC-0091](../../rfc/0091-right-size-rfc-governance.md): the strongest-route rule for
  governance-model changes that stage 1 applies.
- [RFC-0107](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md): the
  activation evidence on folding skills into modes.
- [ADR-0038](../../adr/0038-rename-design-craft-pack-to-experience.md): the earlier pack
  rename, done with no migration aid. RFC-0110 D3 says why this rename needs more.

## Design artifacts (optional)

- [`governance-extras-without-core`](../../specs/governance-extras-without-core/spec.md):
  the spec under which the pack installs and works without core.
