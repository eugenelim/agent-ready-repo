# Spec: spec-B-pack-status-skills

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md) — driving RFC; Change B defines both skill contracts and the `design` type addition
  - [ADR-0054](../../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md) — verb taxonomy (`status` = read-only orient) and pack-type classification
  - [Spec A](../spec-A-workspace-status-rename/spec.md) — `workspace-status` must be renamed before the routing table in this spec's B3 task is meaningful (implementation sequencing, not a hard blocker)
- **Contract:** none — skill SKILL.md authoring; no API contract.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two new `*-status` skills exist in the catalogue — `desk-research-project-status` in the desk-research pack and `experience-status` in the experience-design pack — each giving a user instant cold-start orientation into their current sustained work thread. The `design` type is recognized as a valid `shaping_queue` entry in `workspace.toml`, and the `workspace-status` routing table routes `{type = "design"}` entries to `experience-status` (falling back to `journey-mapping` if experience-design is not installed). Both new skills are read-only orient skills per ADR-0054 — they never advance state, never elicit configuration, and they surface what's missing rather than silently returning empty output.

## Boundaries

### Always do

- Keep both skills strictly read-only: no state advancement, no config elicitation, no file writes.
- Follow the vault-path resolution chain for each skill: `agentbundle-layout.toml` → user-profile → stop (no elicitation fallback).
- Add each new skill to its pack's `[pack.evals].skills` allowlist in `pack.toml`.
- Implement B2 (`experience-status`) and B3 (`design` type) in the same PR so `workspace-status` can route `design` entries to a skill that exists.
- Run `make build-self` after source edits to regenerate projected paths.

### Ask first

- Changing the steel-thread check logic in `experience-status` beyond what RFC-0067 §B2 specifies (journey-map → screen-flow → per-screen briefs).
- Changing the phase labels used by `desk-research-project-status` (capture/digest/synthesize/feedback) — these must match `desk-research-project-start`'s documented phases.
- Adding a fallback behavior other than a "not configured" message for `experience-status` when no `[design] output_dir` is set.

### Never do

- Elicit config in either skill body — `experience-status` reads `[design] output_dir` read-only and surfaces "not configured" when absent; it does not prompt.
- Advance the desk-research phase in `desk-research-project-status` — it reports the current phase, it does not call `desk-research-project-digest` or `desk-research-project-synthesize`.
- Add a `design` workspace.toml type that routes to a skill other than `experience-status` (or its `journey-mapping` fallback) — the routing contract is RFC-0067 §B3 normative.
- Create a standalone `workspace-resume` skill for work-loop invocation — that is Change C's scope, not this spec.

## Testing Strategy

All criteria use **goal-based check**: each SKILL.md is verified against the spec's behavior contract by reading it against the documented `overview.md` / artifact frontmatter / config chain. No TDD-mode tasks (skills are markdown, not compiled code). One **manual QA** step: after `make build-self`, confirm both skills appear in their projected locations.

## Acceptance Criteria

- [x] **AC1.** `packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md` exists with `name: desk-research-project-status`.
- [x] **AC2.** `desk-research-project-status` scans project subfolders under the configured `[research] output_dir` for `overview.md` files. When no project subfolder with `overview.md` is found: surfaces "No research project found — run `desk-research-project-start` for a sustained project, or `desk-research` for a one-off lookup." Does NOT advance phase.
- [x] **AC3.** `desk-research-project-status` surfaces: phase (capture/digest/synthesize/feedback), working hypothesis (the `working_hypothesis:` field from `overview.md` — may be empty), stop-signal verdict, and what the next step is given the current phase.
- [x] **AC4.** `desk-research-project-status` activation triggers include: "where are we on the X research", "status of the Y investigation", "resume the Z project", and any return-to-a-named-research-project phrasing.
- [x] **AC5.** `desk-research-project-status` is added to `packs/desk-research/pack.toml`'s `[pack.evals].skills` allowlist.
- [x] **AC6.** `packs/experience-design/.apm/skills/experience-status/SKILL.md` exists with `name: experience-status`.
- [x] **AC7.** `experience-status` resolves `[design] output_dir` read-only (config chain: `agentbundle-layout.toml` → user-profile → stop; no elicitation). When not configured: surfaces "No `[design] output_dir` configured — run `journey-mapping` to create your first artifact (it will set the path)."
- [x] **AC8.** `experience-status` reads artifact frontmatter from: `<output_dir>/journeys/*.md` (type: customer-journey), `<output_dir>/screens/*-flow.md` (type: screen-flow), `<output_dir>/screens/<slug>/*.md` (matching `- **Type:** screen-brief` bold-body marker — per-screen briefs written by `user-flow`), `<output_dir>/blueprints/*.md` (type: service-blueprint). Reports what exists, what's missing, and which skill to run next.
- [x] **AC9.** `experience-status` steel-thread check: does a journey map exist? Does a screen flow exist? Do per-screen brief files exist under `screens/<slug>/`? The third clause (whether all journey stage actions are covered by screen briefs) requires cross-referencing and is reported as "manual check required" if the skill cannot resolve it from frontmatter alone. Reports gaps on all three checks.
- [x] **AC10.** `experience-status` no-artifacts case: "No design artifacts found — run `journey-mapping` to start the design thread."
- [x] **AC11.** `experience-status` activation triggers include: "where are we with the design", "what experience artifacts do we have", "status of the design thread", "what's next in the design".
- [x] **AC12.** `experience-status` is added to `packs/experience-design/pack.toml`'s `[pack.evals].skills` allowlist.
- [x] **AC13.** `packs/core/.apm/skills/workspace-status/SKILL.md` routing table updated: `{type = "design"}` entries route to `experience-status` (or `journey-mapping` if experience-design is not installed).
- [x] **AC14.** The workspace.toml seed comment in `packs/core/seeds/` (or equivalent source) updated to include `design` as a valid `shaping_queue` type alongside the existing enum (`shape`, `research`, `strategy`, `signal`).
- [x] **AC15.** `docs/product/workspace-toml-deps.md` updated to reflect the `design` type addition.
- [x] **AC16.** `make build-self` exits 0; both skills appear at their projected paths; `make build-check` exits 0.

## Assumptions

- Technical: `desk-research-project-start` already writes an `overview.md` at `[research] output_dir` with `phase:`, `working_hypothesis:`, and `stop_signal:` fields — the field is `working_hypothesis:`, not `hypothesis:` (source: `packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md` line 51, verified at spec-authoring time).
- Technical: the three experience-design writing skills (`journey-mapping`, `user-flow`, `service-blueprint`) already write `type:` frontmatter: `customer-journey`, `screen-flow`, `service-blueprint` respectively — verified against their SKILL.md bodies per RFC-0067 §Evidence.
- Technical: `agentbundle-layout.toml` is the adopter config file with `[design] output_dir` (one `[section]` per pack, one `output_dir` key per section) — the same config chain as writing skills (source: RFC-0067 §B2 and the existing vault-path pattern).
- Process: B2 (`experience-status`) and B3 (`design` type in workspace.toml) are implemented together in one PR so the routing table addition is valid on merge (source: RFC-0067 §Drawbacks).
