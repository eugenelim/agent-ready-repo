# RFC-0078: workspace-mcp — ACP-observable skill runtime for the core pack

<!-- Written for a cold reader. Glossary: "workspace-mcp" = an optional MCP
server (Model Context Protocol server) that bridges loop-engine FSM events,
workspace queue state, and git lifecycle to ACP-compliant AI orchestrators.
"ACP" = Agent Communication Protocol — the open protocol Conductor and Zed use
to dispatch AI coding agents. "Core pack" = packs/core, the default skill pack
shipped to all adopters. "Loop-engine" = the CLI state machine at
scripts/loop-engine.py that drives work-loop's 10-state FSM.
"Class A adapter" = AI host that honours `session/new.mcpServers` injection
(Claude Code, Codex CLI, Copilot CLI); workspace-mcp is injected per session.
"Class B adapter" = AI host that reads MCP config from a repo-local file instead
of accepting per-session injection (Kiro CLI); workspace-mcp is pre-configured.
The detailed design is in docs/architecture/workspace-mcp/design.md.
The design-doc Codex review conclusions are in docs/rfc/0078-notes/. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-03
- **Date closed:** 2026-08-03
- **Decision weight:** heavy <!-- Crosses the charter's "habit, not a tool"
  principle boundary; adds a new runtime component; the permissions.allow
  projection it depends on is a one-way-door change to the agentbundle Claude
  adapter contract. -->
- **Related:**
  - [docs/architecture/workspace-mcp/design.md](../architecture/workspace-mcp/design.md) (precursor design doc; this RFC is the charter gate described in Rollout § Stage 0 (d))
  - [ADR-0061](../adr/0061-loop-infrastructure-phase-1.md) (loop-infrastructure phase 1 — related prior art, not the daemon constraint)
  - ADR-0062 (to be authored after acceptance: "workspace-mcp per-session-only constraint")

---

## Reviewer brief

- **Decision:** Whether to ship workspace-mcp — a per-session MCP server that
  bridges loop-engine FSM events, workspace queue state, and git lifecycle to ACP
  control planes — as a component of the core pack (D1), and whether to approve
  the five empirical Stage 0 spikes as the mandatory gate before Stage 1
  implementation begins (D2).
- **Recommended outcome:** Accept D1 (ship in core pack, co-located with
  workspace-status scripts; module canonical home in agentbundle package) and D2
  (approve the five empirical spikes; do not start Stage 1 until all five close).
- **Change if accepted:**
  - `packages/agentbundle/agentbundle/workspace_mcp.py` — new module (pure stdlib
    Python 3.11+; no new runtime dependencies); installable as
    `python3 -I -m agentbundle.workspace_mcp` for untrusted/CI spawn.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py`
    — thin alias that invokes the agentbundle module; for trusted path-based spawn.
  - `packages/agentbundle/agentbundle/_data/adapter.toml` — new additive-merge
    projection target for `permissions.allow` in `.claude/settings.json` (Stage 1
    prerequisite for Claude Code headless sessions; requires agentbundle version bump
    + `Engine-Change-RFC: RFC-0078` footer). **Note:** this is authorized by D1 only
    if the additive-merge can be implemented without a breaking adapter-contract change;
    if it cannot, a follow-on RFC must authorize the contract change before Stage 1 starts.
    Equivalent headless-permission mechanisms for Codex CLI and Copilot CLI are
    discovered and documented in Stages 2a and 2b respectively (see Rollout table).
  - `docs/architecture/workspace-mcp/design.md` — status updated from Draft to
    Accepted once spikes close and implementation begins.
  - ADR-0062 authored: "workspace-mcp per-session-only constraint."
- **Affected surfaces:** core pack (new script), agentbundle Claude adapter (new
  projection target if non-breaking), `.claude/settings.json` for adopters
  (additive `permissions.allow` entries injected on `agentbundle install core`).
- **Stakes:** Costly-to-reverse once adopters have `permissions.allow` entries
  injected. The `permissions.allow` projection is the one-way-door element.
- **Review focus:** D1 — does shipping an MCP server in core satisfy the charter's
  Principle 1 ("universal") and Principle 3 ("habit, not a tool"), or should
  workspace-mcp route to Option 2 (agentbundle-only, no core-pack alias)? D2 — are
  the five empirical spikes sufficient to de-risk Stage 1?
- **Not in scope:** Persistent daemon mode (per-session-only constraint is a design
  requirement of this RFC; ADR-0062 will capture it); convergence orchestration
  (Stage 4); Gemini CLI and OpenCode (deferred); Jira/Linear write-back; the seven
  implementation-level architectural decisions in design.md § ADR-worthy decisions
  (each becomes an ADR after this RFC is accepted).

---

## The ask

**Recommendation (BLUF):** Accept workspace-mcp as an optional core-pack component,
ship it after all five empirical Stage 0 spikes close, and authorize the additive-merge
permissions.allow projection for the agentbundle Claude adapter (subject to it being
implementable without a breaking contract change).

**Why now (SCQA):** Control planes (Conductor, Zed) can dispatch AI coding agents via
ACP — Claude Code has been in the ACP registry since August 2025. The complication is
that no structured progress signal crosses the ACP boundary: the control plane receives
free-form text with no machine-readable signal for loop-engine FSM phase transitions,
human gate decisions, or artifact creation. This leaves the control plane blind to
everything that happens inside a session. The question is how to close that observability
gap, and whether the mechanism — an MCP server spawned per session — belongs in core or
as a separate distribution unit.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| -- | -------- | -------------- | --- | --------- | --------------- |
| D1 | Should workspace-mcp ship as a component of the core pack (vs. agentbundle package, standalone distribution, or deferred)? | Ship in core pack, co-located with workspace-status scripts | No new deps; opt-in per session; per-session-only constraint; charter analysis below shows it can clear Principles 1 and 3 with stated caveats | This review | Confirm or route to agentbundle package / standalone / defer |
| D2 | Should the five empirical Stage 0 spikes (a)–(e) be the mandatory gate before Stage 1 implementation? | Yes — Stage 1 does not start until all five close | Each spike validates a design-sinking assumption; taken together they de-risk: notification relay (c), instruction durability (a), notification naming (b), module-mode spawn (d), and threading-model concurrency (e) | This review | Confirm spike list, or request additions |

---

## Problem & goals

### The observability gap

The work-loop skill advances through a 10-state FSM (states like `SPEC-PLAN-DRAFTING`,
`CODE-HUMAN-GATE`, etc.) managed by `loop-engine.py`. A control plane dispatching a
work-loop session via ACP receives a stream of free-form text with no structured signal for:

- Which FSM state the session is in.
- When a human gate is reached (cannot prompt the operator without polling for silence).
- What artifacts were created (cannot commit them without separate session prompts).
- What the workspace queue contains (cannot select the next item without prior knowledge
  of this repo's skill stack).

The same gap applies to non-FSM skills: desk-research asks clarifying questions and
writes research briefs to disk; frame-intent and journey-mapping ask about personas and
output shaping artifacts. Every interactive moment where the AI asks a question is an
elicitation that the control plane is currently blind to.

Full goals and non-goals are in the design doc (§ Goals and Non-goals). Summary:

**Goals (abbreviated):** structured FSM transition notifications with zero missed events;
human-gate intercept before the session suspends; `workspace_status()` DAG-resolved
queue view parseable without prior skill knowledge; skill-agnostic control-plane dispatch;
zero behavior change when workspace-mcp is not configured.

**Non-goals (abbreviated):** persistent daemon mode; convergence orchestration (Stage 4);
Gemini CLI / OpenCode support; replacing loop-engine's FSM; Jira/Linear write-back.

---

## Proposal

### Architecture summary

workspace-mcp is a per-session MCP server spawned by the control plane. It communicates
over MCP stdio transport (no TCP port binding; multiple concurrent sessions are isolated
by process). Five services:

1. **Event bridge** — tail-polls `.loop-run/events.jsonl` (the append-only file that
   loop-engine already writes per FSM transition) and maintains internal FSM state exposed via `workspace_status()` (spike (c) fallback — `_agentbundle.core/skill-state-change` notifications generated but not relayed by claude-agent-acp 0.64.0). Uses an outbox pattern — write event to `.loop-run/events.pending`,
   commit state atomically, then append to `events.jsonl` — so a crash before the state
   write doesn't produce phantom replays on recovery. Seq (sequence number) deduplication
   guards against double-delivery for idempotency.
2. **Universal elicitation** — a session instruction injected at startup routes all AI
   questions through an `elicit()` MCP tool rather than direct text output; the tool
   calls `elicitation/create` (MCP server→client direction — workspace-mcp requests a
   response from the AI host, not the other way around) to surface the question to the
   control plane. Response-file fallback for adapters that don't support
   `elicitation/create` (Codex CLI confirmed; Kiro CLI expected).
3. **`workspace_status()` tool** — DAG-resolved (dependency-graph–resolved, following
   `needs:` edges from workspace.toml) view of the workspace queue: ready, shaping,
   blocked (with named unmet `needs:` edges), and active items. Pack-presence filter
   returns unavailable items with `available: false, required_pack: "<name>"` rather
   than excluding them, so the control plane can surface installation prompts.
4. **git tools** — `git_status`, `git_branch`, `git_commit`, `git_push` via subprocess.
   Reactive: the harness calls `git_status()` after TurnEnd and commits uncommitted
   artifacts rather than relying on declarative `git_managed` flags per item type.
5. **Artifact watcher** — 200ms snapshot-diff (compare two filesystem listings taken
   200ms apart and emit events for new files) on manifest-derived output directories;
   emits `_agentbundle.core/artifact-created` when new files appear.

The design doc contains the full pseudocode, notification contract table, adapter-class
split, pressure-test scenarios, and security analysis.

### Charter analysis (D1)

workspace-mcp is evaluated against all four charter principles:

**Principle 1 — Universal across tech stacks.** A control-plane-driven session is a
specific use case, not universal. However, workspace-mcp is opt-in per session and
absent from the default experience: an adopter who does not use a control plane never
encounters it, and the skills it observes are universal across all stacks. The
`permissions.allow` injection on `agentbundle install core` is the one place where the
default install is touched — this is a narrow, additive-only, revocable entry (manually)
that enables opt-in functionality rather than imposing a workflow. The reviewer should
judge whether this additive injection crosses the charter's default-install principle.
If the honest read is that a control-plane-only component cannot clear Principle 1 in
core, D1 should route to Option 2 (agentbundle package module only) below.

**Principle 2 — Substantive, not duplicative.** ACP-observable FSM state and structured
elicitation interception are not encoded anywhere else in the catalogue; the design doc
demonstrates the gap is real.

**Principle 3 — A habit, not a tool.** workspace-mcp is infrastructure (an MCP server).
Three constraints limit drift: (i) opt-in per session (never auto-started); (ii) pure
stdlib Python 3.11+, no new runtime dependencies; (iii) per-session exit enforced in
code — no persistent daemon. The constraint in (iii) is a design requirement of this RFC;
ADR-0062 will capture it as a durable architectural decision after acceptance.

**Principle 4 — Used often enough to stick.** Control-plane adoption is growing (Conductor
is active; Zed is in ACP registry); this is a new feature, so frequency is projected, not
measured. Principle 4 is the weakest bar for new features by design.

**Conclusion:** workspace-mcp can clear the charter with stated caveats, but the Principle
1 / default-install tension on `permissions.allow` injection is the reviewer's judgment
call. If the reviewer routes D1 to Option 2, the implementation is unchanged; only the
distribution unit changes.

### Spawn paths

workspace-mcp ships its logic in `packages/agentbundle/agentbundle/workspace_mcp.py`
(the agentbundle Python package), making it importable as `agentbundle.workspace_mcp`
after `pip install agentbundle`. The core-pack script (`workspace_mcp_server.py`) is a
thin alias that invokes the agentbundle module. Two spawn paths exist:

- **Trusted/normal (path-based):** The control plane passes the projected script path
  in `session/new.mcpServers`. Standard for managed adopter environments.
- **Untrusted/CI (module-based):** `python3 -I -m agentbundle.workspace_mcp`. The `-I`
  flag prevents the checkout directory from being added to `sys.path`, blocking a
  checkout-controlled `agentbundle/` from shadowing the installed wheel — a supply-chain
  injection risk. Required for CI and multi-tenant contexts where the checkout is not
  trusted.

Stage 0 spike (d) validates that the module entry point is installed and accepts the same
env vars as the projected script.

### Stage 0 spikes (D2)

Five empirical spikes (a)–(e) gate Stage 1. The unlettered **(RFC gate)** row below is
the RFC acceptance gate itself — listed for completeness, not an empirical de-risk
exercise. The reviewer is asked to confirm D2 on the basis of the five empirical spikes.

| ID | Assumption being validated | Failure consequence |
| -- | ------------------------- | ------------------- |
| (a) Instruction durability | `session/new` instruction survives across turns in at least one production AI host | If false: control plane must re-inject the preamble on each `session/prompt`; elicitation path changes |
| (b) Notification naming | `x-core/` matches ACP v1 extension-naming convention | **CLOSED:** `x-core/` is NOT the ACP convention; renamed to `_agentbundle.core/` per observed `_claude/sdkMessage` pattern. ADR-0068 updated. |
| (c) Notification relay | MCP `notifications/message` frames reach the control plane as `session/update` events in a production AI host + ACP adapter combination | **CLOSED (fallback):** frames are NOT relayed by `claude-agent-acp@0.64.0`; control plane polls `workspace_status()` (extended with FSM state fields) instead. AC3/AC7/AC8 updated. |
| (d) Module-mode spawn | `python3 -I -m agentbundle.workspace_mcp` is installed and accepts the same env vars as the projected script | If false: trusted-spawn path is unusable; fix install guide and entry point before Stage 1 |
| (e) Threading model | Python stdlib daemon threads + bounded worker-thread pool (pool size 4) handle `elicit()`'s blocking `elicitation/create` call under real MCP stdio concurrency — specifically, nested re-entrancy where the `elicitation/create` response arrives on a separate read-loop iteration while the original `elicit` worker is blocked waiting | If false: asyncio rewrite required before Stage 1; the design's threading model (design.md § Decision 7) is unsound |
| **(RFC gate)** | This RFC is accepted | If rejected: route to Option 2 / standalone / defer; not an empirical spike |

**Two additional assumptions the reviewer may assess for the spike list (D2):**

- **`session/new.mcpServers` production support.** The design's Class A injection
  depends on Claude Code, Codex CLI, and Copilot CLI honoring `session/new.mcpServers`
  in production. If any adapter ignores it, that adapter is Class B only. This can be
  verified as part of Stage 1 validation rather than as a pre-Stage-1 spike, since
  Stage 1 would discover the issue immediately.
- **`permissions.allow` projection feasibility.** The Stage 1 prerequisite (a new
  additive-merge projection target in `adapter.toml`) may require a breaking change to
  the adapter contract, which would itself need a separate RFC. If the reviewer believes
  this risk is high enough to block D1 acceptance, add a sixth empirical spike to
  validate feasibility before sign-off.

Stage 1 does not start until spikes (a)–(e) close. Rollback: if spike (c) fails and
no viable fallback is designed, implementation is deferred until the relay issue resolves.

### Stage 1 prerequisites (named)

Two named prerequisites must be resolved before Stage 1 starts, in addition to the five
spikes (a)–(e) closing:

1. **Headless-permission projection for each Class A adapter.** In an unattended session,
   each AI host prompts for MCP tool approval before calling workspace-mcp tools; a prompt
   with no human present hangs the session. Each Class A adapter has its own mechanism:

   - **Claude Code** — `permissions.allow` entries in `.claude/settings.json`. A new
     additive-merge projection target in the agentbundle Claude adapter
     (`packages/agentbundle/agentbundle/_data/adapter.toml`) must be added (Stage 1
     prerequisite; version bump + `Engine-Change-RFC: RFC-0078` required; authorized by
     D1 if non-breaking; follow-on RFC if breaking). Entries to inject:
     ```json
     "mcp__workspace-mcp__workspace_status", "mcp__workspace-mcp__elicit",
     "mcp__workspace-mcp__git_status", "mcp__workspace-mcp__git_branch",
     "mcp__workspace-mcp__git_commit", "mcp__workspace-mcp__git_push"
     ```
   - **Codex CLI** — equivalent pre-approval mechanism unknown; discovered and documented
     in Stage 2a. Until documented, adopters using Codex in headless mode must configure
     permissions manually or pass `--dangerously-skip-permissions`.
   - **Copilot CLI** — equivalent pre-approval mechanism unknown; discovered and documented
     in Stage 2b. Same manual fallback applies.

2. **Needs-resolution semantics for autonomous dispatch.**
   `is_need_satisfied()` (`workspace_status_engine.py:456-533`) implements documented
   intentional behavior (SKILL.md:90, schema.md:114): a `shape:` or `research:` target
   absent from the active shaping queue is treated as *satisfied*. This is correct for
   human-managed dispatch (a human knows context the engine doesn't) but is unsafe for
   autonomous dispatch: the control plane may start a dependent item whose prerequisite
   was never created. Closing this requires a SKILL.md/schema.md semantics update (or
   a scoped override for autonomous-dispatch mode), not a local bug fix. This change
   must be designed and accepted before Stage 1 enables autonomous dispatch.

### Rollout stages

| Stage | Scope | Gate |
| ----- | ----- | ---- |
| 0 | Spikes (a)–(e) + RFC acceptance | All six close (five empirical + this RFC) |
| 1 | Claude Code adapter, work-loop, single session | FSM visibility, elicitation intercept, git commit/push, notification relay; Claude Code permissions projection |
| 2a | Codex CLI | `session/new.mcpServers` injection; response-file elicitation fallback; **document Codex headless-permission mechanism** |
| 2b | Copilot CLI | `session/new.mcpServers` injection; `elicitation/create` support (unconfirmed); **document Copilot CLI headless-permission mechanism** |
| 2c | Kiro CLI (Class B) | `.kiro/settings/mcp.json` pre-config; V3 agent format + `@mcp` tag; kiro-cli adapter V3 prerequisite |
| 3 | Non-FSM skills (desk-research, PE, XD) | Artifact watcher; elicitation for clarifying questions |
| 4 | Multi-instance, worktrees, convergence | Separate scope |

---

## Options considered

The option axis is **distribution unit**: where does workspace-mcp live? The four options
below exhaust the space (inside the existing default unit, inside the existing CLI package,
a new unit, or no unit now).

| Option | Description | Recommended? |
| ------ | ----------- | ------------ |
| 1 | **Core pack** (this RFC's D1 recommendation) | ★ Yes, with caveats |
| 2 | **agentbundle package module** | Fallback if Principle 1 objection sustains |
| 3 | **Standalone distribution** (`agentbundle-workspace-mcp` PyPI package) | No |
| 4 | **Defer** | No |

### Option 1 — Ship in core pack (recommended)

workspace-mcp co-located with workspace-status in the core pack. Opt-in per session;
pure stdlib; no new deps; per-session-only constraint.

**Trade-offs:** Crosses Principle 3 ("habit, not a tool") — accepted under three
constraints (opt-in, no deps, per-session exit). The Principle 1 / default-install
tension on `permissions.allow` injection is the open question. **Prior art:** workspace-status
is already infrastructure-adjacent (it runs engine code at query time); workspace-mcp
extends the same engine for a session-scoped use case.

### Option 2 — agentbundle package module only (recommended fallback)

The module `agentbundle.workspace_mcp` is the canonical implementation under **both**
options (both Options 1 and 2 place the logic in `packages/agentbundle/`). What Option 2
changes: the core pack ships **no** alias script (`workspace_mcp_server.py`); adopters
invoke workspace-mcp exclusively via `python3 -I -m agentbundle.workspace_mcp` or a
control-plane-supplied path. Adopters who want unattended sessions must add
`permissions.allow` entries manually (or via `agentbundle[workspace-mcp]` extras, if
that install path is created) rather than receiving them automatically from the core pack.

**Trade-offs:** Cleanest dissolution of the Principle-3 tension (agentbundle is
explicitly infrastructure tooling, not a habit-pack; no MCP-server code or default-install
permission injection enters the core pack). Slightly higher adopter friction (no auto-injected
permissions on `agentbundle install core`). **Favored when:** the Principle 1 / default-install
objection to Option 1 sustains, or the `permissions.allow` additive-merge projection cannot
be implemented without a breaking adapter-contract change.

**Favored when:** The Principle 1 / default-install objection to Option 1 sustains, or
the `permissions.allow` additive-merge projection cannot be implemented without a breaking
adapter-contract change.

### Option 3 — Standalone PyPI package (`agentbundle-workspace-mcp`)

A new PyPI package, separately versioned and released.

**Trade-offs:** Two-package install burden; separate release management; deep coupling
to agentbundle's FSM events schema (which changes with loop-engine version bumps) means
the two packages must be co-versioned anyway, erasing most independence benefit. Not
the right unit boundary when the component is tightly coupled to agentbundle internals.

### Option 4 — Defer

Close this RFC with "not yet."

**Trade-offs:** Spikes (a)–(e) can run independently of this RFC's acceptance.
Cost of delay: Conductor and Zed sessions remain blind to work-loop phase; every gate
resolution requires human polling; control-plane dispatch remains skill-dependent (no
`workspace_status()` tool). **Favored when:** spike (c) fails and no viable fallback is
designed; or the charter review finds Options 1 and 2 both untenable.

---

## Risks & what would make this wrong

- **Charter Principle 3 violation is real, not dismissed.** workspace-mcp is an MCP
  server. If the Approver reads Principle 3 strictly, D1 is wrong and Option 2 is the
  correct route. **Mitigation:** three constraints limit the infrastructure footprint;
  Option 2 is a clean fallback with unchanged implementation.

- **Spike (c) — notification relay — resolved with fallback.** `claude-agent-acp@0.64.0` does not relay MCP `notifications/message` frames (`case "notification": break`). The poll-based fallback (`workspace_status()` extended with FSM state fields) is adopted for Stage 1. Gate resolution latency increases from sub-second (push) to the control plane's poll interval (suggested 500ms–2s). Real-time push will be available when claude-agent-acp adds `notifications/message` relay support (or when a PR ships the missing `case "mcp_notification"` handler).

- **`permissions.allow` projection is a one-way door (Claude Code).** Once
  `agentbundle install core` merges the six MCP tool entries into `.claude/settings.json`,
  removing them requires manual surgery by the adopter. A removal-projection capability
  does not currently exist in agentbundle. For Codex CLI and Copilot CLI, equivalent
  pre-approval mechanisms are not yet known and will be documented in Stages 2a/2b;
  those mechanisms may or may not involve agentbundle-managed projection.
  **Mitigation:** additive-merge is versioned; removal from Claude Code settings remains
  manual until a removal-projection capability is built. Accepted cost.

- **Trusted spawn (-I) is not enforced at runtime.** A control plane that omits `-I`
  allows checkout-controlled packages to shadow the installed wheel. **Mitigation:** install
  guide specifies `-I` as mandatory for untrusted/CI contexts; the trusted-spawn section
  in design.md documents both JSON examples. Runtime enforcement is not feasible without
  control-plane cooperation. Accepted: guidance is in the install guide.

- **Kiro CLI kiro-cli adapter prerequisite blocks Stage 2c.** The `kiro-cli` adapter must
  emit V3 Markdown agents before Stage 2c can start. If that work item slips, Stage 2c
  slips. **Mitigation:** Stage 2c is gated on the adapter update; Stages 1, 2a, 2b do not
  depend on it.

- **Session instruction compliance is prompt-following, not enforced.** The AI may skip
  `elicit()` for very short responses ("sure", "yes"). **Mitigation:** accepted for short
  responses; instruction is strongest for option-selection and structured decisions.

**Key assumptions (falsifiable):**
1. `session/new.mcpServers` is honored in production by at least one Class A AI host.
   False → Class A collapses to Class-B-only.
2. Python stdlib daemon threads + bounded worker pool handle `elicit()` MCP stdio
   concurrency correctly (nested `elicitation/create` re-entrancy included).
   False → asyncio rewrite required before Stage 1. Validated by spike (e).
3. The agentbundle Claude adapter can gain an additive-merge projection target for
   `permissions.allow` without a breaking contract change. False → a follow-on RFC
   authorizes the contract change before Stage 1 starts; D1 acceptance does not
   pre-authorize a breaking contract change.

---

## Evidence & prior art

**Spike / de-risk result:** No production spikes have run. The design doc was reviewed
by Codex CLI in eight rounds (C1–C8); the distilled conclusions are in
[`docs/rfc/0078-notes/codex-review-conclusions.md`](0078-notes/codex-review-conclusions.md).
Round 8 returned zero P1 findings, confirming design-level internal consistency. This is
not a substitute for running Stage 0 spikes against live adapters.

**Repo precedent:**
- workspace-status skill (`packs/core/.apm/skills/workspace-status/`) — the existing
  workspace tooling workspace-mcp co-locates with and extends.
- `packages/agentbundle/agentbundle/_data/adapter.toml` — the Claude adapter projection
  that the Stage 1 prerequisite extends.
- ADR-0061 (`docs/adr/0061-loop-infrastructure-phase-1.md`) — loop-infrastructure
  phase 1; related prior art (not the daemon constraint; that becomes ADR-0062).

**External prior art:**
- MCP specification 2025-06-18: `elicitation/create` (server→client request) and
  `notifications/message` (server→client notification) are standard MCP primitives.
- ACP v1: adapts `elicitation/create` from MCP; `session/new.mcpServers` is the
  ACP-native per-session injection path.
- Kiro CLI V3 agent format + `@mcp` tag: the Class B pre-configured pattern.

---

## Open questions

1. **Notification namespace form.** **CLOSED by Stage 0 spike (b).** `_agentbundle.core/` is the confirmed form, consistent with `_claude/sdkMessage` observed in `claude-agent-acp@0.64.0`. All artifacts updated. ADR-0068 updated.

2. **`permissions.allow` removal path.** If an adopter wants to remove workspace-mcp,
   what is the mechanism? Additive-merge has no defined removal path.
   *Recommended default:* manual removal for now; document the manual step in the install
   guide; defer removal-projection capability to a follow-on RFC if demand emerges.
   *Owner:* eugenelim. *Decide by:* Stage 1 design is finalized.

3. **Copilot CLI `elicitation/create` support.** Flagged as unconfirmed.
   *Recommended default:* assume response-file fallback until Stage 2b validation.
   *Owner:* eugenelim. *Decide by:* Stage 2b begins.

---

## Follow-on artifacts

Filled in when this RFC is Accepted:

- ADR-0062: workspace-mcp per-session-only constraint
- ADR-0063: Session instruction over per-skill gate modification
- ADR-0064: events.jsonl as the FSM event source
- ADR-0065: elicit() + elicitation/create + response-file fallback
- ADR-0066: Reactive git at TurnEnd (vs. declarative git_managed)
- ADR-0067: Lifecycle manifest (built-in defaults + workspace-types.d/ extension)
- ADR-0068: Notification namespace
- ADR-0069: Threading model (daemon threads + bounded worker pool)
- Spec: `docs/specs/workspace-mcp/` (Stage 1 implementation spec; authored after Stage 0
  spikes close and both Stage 1 prerequisites are confirmed)

---

## Errata

**Erratum 2026-08-03 — `schema.md` does not exist; citations are stale.**
Sections "Proposal" (§ Autonomous dispatch mode, line ~276–280) cite `schema.md:114` and `SKILL.md:90` as authorities for needs-resolution semantics. `schema.md` does not exist in this repo. `SKILL.md:90` is inside a TOML template block, not needs-resolution prose. Both citations are stale; the canonical authority is SKILL.md §2 (needs-resolution table). Stage 1 implementation (AC19, Task 4) strips these citations from `workspace_status_engine.py` comments. The RFC body is frozen; corrected here by erratum.

**Erratum 2026-08-03 — events.jsonl is new Stage 1 work, not pre-existing.**
Section "Architecture summary" (§ Proposal, item 1) states: "tail-polls `.loop-run/events.jsonl`
(the append-only file that loop-engine already writes per FSM transition)." This is incorrect.
As of RFC acceptance, loop-engine does **not** write `events.jsonl`. The events.jsonl append
(including the outbox protocol for crash-consistency) is a Stage 1 implementation work item
captured in spec.md AC0 and plan.md Task 1. ADR-0064 has been updated to reflect this.
The RFC body is frozen per convention and corrected here by erratum.
