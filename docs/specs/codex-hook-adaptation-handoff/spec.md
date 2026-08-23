# Spec: Core install handoff and hook documentation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Audit:** [`hook-adapter-audit.md`](hook-adapter-audit.md)
- **Constrained by:** `docs/specs/local-scope-install/spec.md`, `docs/specs/agentbundle-first-value-handoff/spec.md`, `docs/specs/portfolio-pack-first-value-contract/spec.md`; accepted [ADR-0095](../../adr/0095-level-a-first-value-optional-next-action.md) owns the Level A contract amendment
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no REST/event/RPC interface surface; `adapter.toml` and `pack.schema.json` are internal build-pipeline data this change reads and does not modify, named under Always do below -->
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every successful direct core install at repository or local scope prints an
explicit next action telling the adopter to ask an agent to run
`adapt-to-project`, without relying on a lifecycle hook. Living documentation
accurately describes current Codex and APM hook support, local-scope omissions,
and the distinction between the deterministic CLI `adapt` command and the
agent skill. The accompanying audit records current Claude Code, Codex,
Copilot, Cursor, Gemini, Kiro, and APM hook-contract drift without expanding
this change into adapter repairs.

## Boundaries

### Always do

- Emit the core handoff after successful repo and local installs even when a
  hook is disabled, untrusted, unsupported, output-incompatible, or has no
  marker to consume.
- Retain local scope's current guarantees: no seeds, adaptation marker, layout
  section, or chained CLI adaptation.
- Keep fresh core user-scope installation unsupported.
- Treat `pack.toml` as the source of installer handoff text,
  `contracts/adapter.toml` as the direct-adapter projection source, `.apm` as
  portable hook source, and first-party runtime documentation as the current
  external contract.
- Correct living README, guide, architecture, source comments, and tests that
  pin invalid commands or obsolete support claims.
- After ADR-0095 is accepted, add status-only partial-supersession pointers to
  the two shipped first-value specs whose frozen bodies describe
  `next-action` as Level B-only.
- Keep runtime support, projection, enablement, workspace/hook trust, output
  compatibility, and marker availability as separate facts.

### Ask first

- Any functional adapter projection, hook-body output, event mapping, command
  path, or runtime-configuration change.
- Any local-scope seed, marker, layout, or chained-adaptation change.
- Any change to the `adapt-to-project` skill or its implementation.
- Any adapter-contract version or schema change.

### Never do

- Edit generated `.agents`, `.codex`, or `.claude` projections directly.
- Claim that version support or a projected file proves hook execution.
- Claim a local setting bypasses the active managed permission profile.
- Force-enable hooks, trust a project or hook, or inspect protected trust and
  configuration storage.
- Add `--scope` to `agentbundle adapt` or document it as an alias for the
  `adapt-to-project` agent skill.
- Hide adapter-audit findings by broadening this small onboarding repair.
- Rewrite frozen historical spec bodies, RFCs, or work-loop fixture corpora
  merely because their captured historical text is now stale. The only frozen
  spec edits allowed here are ADR-0095's status-line pointers after acceptance.

## Testing strategy

- **First-value handoff — TDD.** Unit tests pin optional `next-action` output
  for Level A, unchanged Level B behavior, unchanged Level A behavior when the
  field is absent, and unchanged output for packs without first-value metadata.
- **First-value lint — TDD.** CAT-L030 validates an optional `next-action` at
  either level while retaining the Level B required-field rule.
- **Install integration.** Real core repo and local installs pin the exact
  `Next:` line. Existing local-scope tests continue to prove seed, marker,
  layout, and chained-adapt omission; fresh user scope remains refused.
- **Documentation and disclosure — goal-based.** Tests reject "Codex lacks
  hooks", `agentbundle adapt --scope`, the obsolete APM support group, and
  claims that every install writes a marker.
- **Adapter audit regressions — goal-based.** Existing adapter projection tests
  run unchanged to prove this change does not silently alter hook projection.
  The audit note, rather than duplicated generated matrices, records current
  first-party contract findings.

## Acceptance criteria

- [x] **AC1 — Deterministic core handoff.** Successful core repo and local
  installs print exactly: `Next:     Ask your agent to run adapt-to-project for
  a read-only readiness check; start a new session if the skill is unavailable.`
- [x] **AC2 — Level compatibility.** A Level A pack may declare optional
  `next-action`; it prints after `Verify:` without Level B's `Try:` or
  `Expected:` labels. Level A without the field, Level B, and packs without
  `[pack.first-value]` retain prior output.
- [x] **AC3 — Validation.** CAT-L030 validates the type and 120-character limit
  of `next-action` whenever present and continues to require it for Level B.
- [x] **AC4 — Local invariants.** Local core installation continues to project
  selected-adapter primitives and local state while writing no seeds,
  adaptation marker, layout section, or chained CLI adaptation result.
- [x] **AC5 — User-scope compatibility.** Fresh core user-scope installation
  remains refused by `allowed-scopes = ["repo"]`; this change creates no user
  files or migration.
- [x] **AC6 — Codex documentation.** Living docs say Codex supports repository
  `.codex/hooks.json` and `SessionStart`, while execution still depends on the
  active feature/managed policy, project-layer trust, exact-hook review,
  command dispatchability, and marker availability.
- [x] **AC7 — APM documentation.** Living docs reflect current HookIntegrator
  support for Claude, Copilot, Cursor, Gemini, Codex, Antigravity, Windsurf,
  and Kiro, and retain OpenCode as unsupported without confusing APM targets
  with direct `agentbundle` adapters.
- [x] **AC8 — Marker documentation.** Living docs state that direct repo
  install writes a marker and chains CLI adaptation, while local scope writes
  neither. They do not claim every route or successful install writes a marker.
- [x] **AC9 — Surface separation.** Documentation states that
  `agentbundle adapt` performs deterministic substitution/bookkeeping and
  `adapt-to-project` is the agent-led workflow; it documents no `adapt --scope`.
- [x] **AC10 — Portable source comments.** Core hook-wiring comments describe
  a portable Claude-shaped authoring source transformed by adapters, not a
  Claude-only hook or obsolete Kiro exclusion.
- [x] **AC11 — Audit record.** The dated audit covers Claude Code, Codex,
  Copilot, Cursor, Gemini, Kiro IDE/CLI, and APM with official sources, current
  projection evidence, output-protocol findings, and explicit in-scope versus
  separate-decision disposition.
- [x] **AC12 — No adapter behavior change.** Direct adapter projection code,
  hook-body behavior, generated runtime files, and current projection test
  expectations are unchanged except for normal regeneration caused by the
  core patch version and source-comment update.
- [x] **AC13 — Release consistency.** Core receives the required patch version,
  generated metadata is rebuilt through owning builders, product changelog is
  updated, and generated-drift checks pass.
- [x] **AC14 — Guarantee boundary.** User-facing guidance states that the
  installer guarantees projected files, scope-specific state/omissions, and
  stdout; actual hook execution and context injection depend on the active
  runtime, policy, trust, cwd/path resolution, output protocol, and marker.
- [x] **AC15 — Frozen-contract bridge.** ADR-0095 is accepted before the Level
  A behavior ships, and the status lines of the shipped agentbundle and
  portfolio first-value specs point to the exact clauses it supersedes in
  part; their bodies remain unchanged.

## Assumptions

- Codex currently supports lifecycle hooks and repository `.codex/hooks.json`;
  current official documentation is the authority.
- The active enterprise runtime's exposed feature result is authoritative for
  this session and does not imply what another account or runtime will expose.
- Core remains a repo-only pack whose special local scope is an ephemeral
  repository install mode, not user scope.
- Adapter-fidelity gaps found by the audit require separate product decisions
  and are not silently repaired here.
- The user explicitly removed `adapt-to-project` implementation and doctor work
  from this change on 2026-08-22.
