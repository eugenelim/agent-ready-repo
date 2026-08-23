# Adopter route walkthrough

- **Date:** 2026-08-21
- **Reviewer:** Codex primary work-loop implementation session
- **Scope:** Cold-reader traversal of the published adopter sources for starting,
  deferring, inspecting, refreshing, and migrating repository work across the
  core, Jira, Jira Align, GitHub, and Linear routes.
- **Run/session boundary:** The observations below come from the current
  worktree in one source-first session. They cover source validation and the
  generated-site dry run; they do not claim a production site build, a browser
  visual review, tracker network access, or a remote tracker mutation. T6 owns
  the production build and release-projection checks.

## Fixture and build inputs

- `guides/README.md` and the shared work-intake how-to, responsibility
  explanation, and routing/lifecycle reference.
- Core capture-work compatibility, legacy migration, workspace schema, routing,
  and session-orientation pages.
- Atlassian, GitHub, and Linear guide indexes and pack journeys.
- The core routing matrix, four profile intake matrices, seven refresh lifecycle
  states per profile, and the reviewed migration selection/workspace fixtures.
- The owning `work-intake`, `workspace-status`, profile intake, and refresh skill
  sources used to check capability claims.
- `tools/validate_guides.py`, `tools/check-guide-index.py`,
  `tools/lint-guide-titles.py`, `tools/lint-journey-contract.py`,
  `tools/lint-pack-journeys.py`, and `tools/build-site.py --dry-run`.

## Observed routes and results

1. **Landing to start.** `guides/README.md` reaches “Use work intake,” which
   begins with an ordinary request rather than a tracker-specific command. The
   route returns artifact kind/path, lifecycle membership, processor, authority,
   dispatchability, and one next action. Equivalent normalized content uses the
   same core route for all four tracker profiles.
2. **Defer.** “Remember this for later” creates a canonical Draft artifact and
   workspace registration, then stops non-dispatchable. It does not reconstruct
   a spec from a comment or turn every feature-shaped request into a brief.
3. **Status.** The same how-to sends orientation and triage requests to
   `workspace-status`. The documented operation is read-only and exposes
   reconciliation, authority, refresh, and legacy findings without dispatching
   a retained legacy membership.
4. **Refresh.** A registered tracker-origin artifact routes through its profile
   and lifecycle locks. Local field decisions are distinct from a remote
   coordination action; the latter requires its own exact confirmation. The
   matrix covers Draft, Accepted, Ready, Approved, Implementing, Executing, and
   Shipped for Jira, Jira Align, GitHub, and Linear.
5. **Migration.** A `legacy_entry` finding routes from the shared how-to to the
   core migration how-to. Planning consumes a reviewed, human-authored selection
   and remains read-only; apply requires a separate human-authored confirmation
   and configured migration approver. The ledger supports recovery and rollback,
   and rollback retains canonical artifacts.

## Validation evidence

- Guide schema/frontmatter and links: `validate_guides.py` checked 192 pages
  with 5 documented exemptions.
- Guide index coverage: all 20 pack guide indexes passed.
- Guide titles: all 197 titles passed.
- Journey frontmatter/contracts: all 17 journey contracts passed.
- Pack journey stages and human gates: all 14 pack-local journeys passed.
- Generated-site dry run: 192 navigable guide pages were placed in 21 groups,
  all 14 pack journeys were synchronized, 197 guide files were mirrored, and
  the dry run completed successfully. The existing `user-guide-diataxis`
  placement warning remains unrelated to this work.
- Semantic searches found no adopter claim that reconstructs specifications from
  workspace comments, no universal one-way tracker claim, and no unconditional
  feature/issue/story-to-brief rule after correcting the feature-intent journey,
  live-demo guide, and shaping guide to route one independently shippable feature
  directly to a spec. Remaining
  `capture-work` hits are the
  compatibility alias, migration titles/links, or the pre-existing example slug
  `capture-work-v2`; none is a new non-alias invocation.

The walkthrough therefore reaches every required adopter operation through one
current model while keeping the human route, field, privacy, and mutation
decisions visible.
