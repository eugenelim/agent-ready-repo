# Spec: new-rfc follow-on queue-write guard

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `new-rfc` skill prompts to queue follow-on implementation work in
`workspace.toml` only when an RFC transitions to Accepted within the same
session. When an RFC was accepted in a prior session and a follow-on session
generates specs or ADRs for it, the queue-write prompt is silently skipped —
a session-fragmentation drop.

Two changes close the gap. First, the `new-rfc` skill's trigger description
is extended to also fire when someone asks to generate follow-on artifacts for
an already-Accepted RFC (e.g., "create the specs for RFC-0067" or "implement
the follow-on work from that RFC"). Without this, the `## After acceptance`
section is unreachable in a follow-on session. Second, that section gains a
session-fragmentation guard: before generating any follow-on artifact, the
skill checks `workspace.toml` and re-surfaces the queue-write prompt if the
planned spec paths are absent, regardless of whether the RFC moved to
Accepted in this session or a prior one.

The re-entry invocation pattern is: a user in a fresh session asks the agent
to generate specs or ADRs for a specific Accepted RFC. The updated trigger
description routes this through `new-rfc`, which detects the RFC's `Accepted`
status and falls through to `## After acceptance` — where the guard runs the
workspace.toml check before any artifact is created.

## Boundaries

### Always do

- Check all three `[work]` arrays (`queue`, `active`, `shipped`) across all
  `status = "active"` initiative sections when testing whether paths are already
  queued.
- Match both entry forms in workspace.toml: bare strings (`"spec/foo"`) and
  inline objects (`{path = "spec/foo", needs = "..."}`).
- Re-surface the existing queue-write prompt flow (unchanged) when the guard
  fires.
- Degrade gracefully: if `workspace.toml` is absent, skip the guard silently.

### Ask first

- Any change to the existing in-session acceptance flow text (the guard is
  additive; if in doubt, surface before touching the prompt wording).
- Any wording in the trigger description that could incorrectly fire `new-rfc`
  when the user intends `new-spec` or `new-adr` for an unrelated RFC.

### Never do

- Modify `new-spec` or `new-adr` as part of this change.
- Auto-create or auto-populate `workspace.toml` entries without the user
  confirming the paths.
- Remove or weaken the existing duplicate-path check (`[work].queue` already
  contains the path → surface the duplicate).

## Testing Strategy

- **Goal-based check** — `make build-check` passes after `FORCE=1 make
  build-self`; confirms the projected skill matches the seed.
- **Goal-based check (report-only)** — `tools/run-pack-evals.py --pack
  governance-extras --mode headless --adapter claude-code --check activation`
  run against the updated `eval_queries.json`; report confirms new positive
  entries trigger and boundary negatives stay false. This is a report-only
  verification, not a gate; scenario E provides the hard manual assertion.
- **Visual / manual QA** — trace five scenarios through the updated skill:
  (A) in-session acceptance → RFC just transitioned to Accepted in this
  session; guard fires (status is Accepted, paths absent) → single prompt
  fires once; if yes: paths are added, guard on any subsequent call in this
  session finds paths present and skips; if no: workspace.toml unchanged,
  paths remain absent, a subsequent same-session invocation re-prompts
  (intentional — skill has no decline-suppression mechanism).
  (B) follow-on session, Accepted RFC, `workspace.toml` exists, paths absent
  → guard fires, prompt re-surfaced;
  (C) follow-on session, `workspace.toml` absent → guard skips silently;
  (D) follow-on session, paths already in `[work].active` or `shipped` →
  guard skips silently.
  (E) trigger boundary — the extended `new-rfc` description is read against
  positive queries ("RFC-0067 was accepted — create the follow-on specs",
  "generate the ADRs for that accepted RFC") and negative queries ("Write a
  spec for the CSV export feature", "Create an ADR for our database choice —
  we've already decided"); confirm positive queries route to `new-rfc` and
  negative queries do not. Cross-pack competitive check: also read the
  `new-spec` (core pack) and `new-adr` (governance-extras) descriptions
  against the same positive queries and record that neither fires — the
  activation eval harness checks `governance-extras` in isolation and does
  not cover cross-pack exclusivity, so this check is manual.
  (F) partial queuing — follow-on session, RFC Accepted, workspace.toml
  present; one spec path is already in `[work].queue`, a second spec path is
  absent; guard fires over the missing second path only and prompts to add it;
  the first path is not re-prompted.

## Acceptance Criteria

- [x] AC1: The `new-rfc` frontmatter `description` is extended to also trigger
  on invocations of the form "generate follow-on specs/ADRs for an Accepted
  RFC" (e.g., "create the specs for RFC-NNNN", "implement the follow-on work
  from that RFC"). The extension does not cause the skill to fire for
  unrelated `new-spec`/`new-adr` invocations.
- [x] AC2: The `## After acceptance` section opens with a session-fragmentation
  guard that, for each `spec/<path>` artifact the agent is about to generate
  (the only entry form workspace.toml's `[work]` arrays accept), checks whether
  its path appears in any active initiative's `[work].queue`, `[work].active`,
  or `[work].shipped`. The guard collects absent spec paths; if any are absent,
  it fires the prompt over the missing subset before generating any artifact.
  ADRs and CONVENTIONS edits are not representable as queue entries and are
  not included in the guard's check; they remain handled by the follow-on
  artifact list that runs after the queue-write step. The guard matches both
  bare-string (`"spec/foo"`) and inline-object (`{path = "spec/foo", ...}`)
  entry forms. It scans all `status = "active"` initiative sections, reusing
  the >1-active tie-break the write path already uses. If the user declines
  the prompt, paths remain absent and a subsequent same-session invocation
  re-prompts; this is intentional.
- [x] AC3: If `workspace.toml` is absent, the guard skips silently (no error,
  no behavior change from the pre-fix state).
- [x] AC4: The guard skips silently only when ALL planned spec paths appear in
  any active initiative's arrays. Partial presence (some spec paths queued,
  some absent) fires the guard over the missing subset — not a silent skip.
- [x] AC5: The existing in-session queue-write prompt block is preserved intact.
  The guard is a preamble, not a replacement. The lead sentence ("When the RFC
  moves to Accepted, first offer to queue…") may receive a minimal framing edit
  if needed to avoid incoherence with the already-Accepted follow-on path, but
  the prompt options (If yes / If no) and the follow-on artifact list are
  unchanged.
- [x] AC6: The projected skill at `.claude/skills/new-rfc/SKILL.md` matches the
  updated seed after `make build-self`.
- [x] AC7: The `governance-extras` pack version is `0.8.0` in `pack.toml` (the
  `[pack]` table `version` field) and `plugin.json`. The `[pack.adapter-contract]`
  `version` field in `pack.toml` is not changed.
- [x] AC8: `packs/governance-extras/.apm/skills/new-rfc/evals/eval_queries.json`
  is updated with at least three new `should_trigger: true` entries covering
  "follow-on specs/ADRs for an Accepted RFC" phrasing, and at least two new
  `should_trigger: false` entries that pin the boundary (spec/ADR requests
  with no RFC follow-on context). The existing false entries ("Write a spec for
  the CSV export feature", etc.) must still be false after the trigger-description
  change.
- [x] AC9: `docs/product/changelog.md` has an `[Unreleased]` entry for
  `governance-extras 0.8.0` describing the session-fragmentation guard.
- [x] AC10: The updated frontmatter `description` disambiguates the follow-on
  trigger from both halves of the existing `Do NOT` clause at the trigger level
  only (no changes to skill body behavior are implied):
  (a) "already-decided things (use `new-adr`)" is scoped to standalone
  architectural decision recording — not to generating follow-on artifacts
  after an RFC is accepted.
  (b) "single-feature specs (use `new-spec`)" is scoped to authoring a spec
  without an associated Accepted RFC context — the Do NOT applies to starting
  spec work independently, not to using `new-rfc` as the entry point for RFC
  follow-on work where `new-spec` is then used afterward. A query like
  "create the follow-on specs for RFC-0067" routes to `new-rfc`, not
  `new-spec`. The description remains trigger-shaped and under 1024 characters
  (Kiro frontmatter parser cap); any longer conceptual framing belongs in the
  skill body, not the description.

## Assumptions

- Technical: Updating the `new-rfc` frontmatter `description` is the right
  mechanism to make the `## After acceptance` guard reachable from a follow-on
  session — the description is the skill activation trigger read by the model.
  (source: .claude/skills/README.md § Authoring skills; AGENTS.local.md §
  Authoring or editing a skill)
- Technical: `workspace.toml` queue-prefix notation `"spec/<path>"` maps to
  `docs/specs/<path>/` on disk; the guard compares the paths the agent is
  about to create against the stored entries. (source: workspace.toml entries
  + observed filesystem layout)
- Technical: The seed path is `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`;
  the projection is `.claude/skills/new-rfc/SKILL.md`. (source: AGENTS.local.md
  projected-path table)
- Process: A non-cosmetic skill change requires a pack version bump (`0.7.0`
  → `0.8.0`). (source: AGENTS.local.md Pack versioning section)
- Technical: `workspace.toml` entries appear in two forms; the guard must
  handle both. (source: workspace.toml entry shapes at lines 31, 103–116)
