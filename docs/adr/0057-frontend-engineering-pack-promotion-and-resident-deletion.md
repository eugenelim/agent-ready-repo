# ADR-0057: Promote `frontend-engineering` to first-class pack; delete core resident to resolve footprint conflict

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision-makers:** eugenelim
- **Related:** [`guides/frontend-engineering/`](../../guides/frontend-engineering/), [`docs/specs/frontend-engineering-core-delegation/`](../specs/frontend-engineering-core-delegation/)

## Decision summary

- **Decision:** Promote the `frontend-engineering` resident skill to a first-class pack (`packs/frontend-engineering/`) with 9 skills, a `frontend-reviewer` agent, a guide tree, and a catalogue page; and delete the core resident skill (`packs/core/.apm/skills/frontend-engineering/SKILL.md`) along with its committed projected copies (`.claude/skills/frontend-engineering/`, `.agents/skills/frontend-engineering/`). The DXC template is relocated from the deleted core path to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/`. `work-loop` is updated to name the pack requirement with a named-skip fallback when the pack is absent.
- **Because:** The skill accumulated enough depth and distinct concerns — token system architecture, accessibility engineering, performance diagnostics, rendering strategy, component API design, responsive layout, CSS architecture — that a flat single-skill surface no longer serves the full range of tasks. A pack partitions those concerns into named atomic skills a practitioner loads by task. The core resident cannot coexist with the pack: the agentbundle footprint gate (`packages/agentbundle/agentbundle/config.py:229-286`) classifies both skills claiming the same relpath (`frontend-engineering`) as `REFUSE`, blocking pack installation over a core-installed baseline. Deletion resolves the conflict cleanly.
- **Applies to:** `packs/frontend-engineering/`, `packs/core/`, the four work-loop insertion points that reference the pack's atomic skills and `frontend-reviewer`, and the committed projected copies under `.claude/skills/` and `.agents/skills/`.
- **Tradeoff accepted:** Users who have `core` installed but not the `frontend-engineering` pack will no longer have a fallback FE skill. This is the honest outcome: the craft rules live in the pack; `core` is not the right home for them.
- **Revisit if:** The pack grows beyond 12 skills (consider splitting by concern cluster: accessibility / performance / architecture). An alternative conflict-resolution mechanism in agentbundle (pack supersedes resident rather than refusing) would allow a thin named-skip stub to return to core.

## Context

The resident `.claude/skills/frontend-engineering/SKILL.md` (443 lines) covered the full create/retrofit/audit/verify workflow, CSS token discipline, accessibility patterns, GATES commands, an evidence manifest, and performance targets. That breadth served surface-level PLAN-time loading. The limitation appeared for narrowly-scoped tasks — a performance remediation, a token system design, a dedicated accessibility audit — where loading the full skill brought incidental context.

The pack's skill (660 lines) adds four explicit modes (create/retrofit/audit/verify), an 18-state matrix (vs. 6 in the resident), a 12-field page contract, an evidence manifest, Core Web Vitals targets, a brownfield checklist, and an updated WCAG baseline (2.2 AA vs. 2.1 AA). The eight atomic skills partition the main skill's concerns; the `frontend-reviewer` agent provides a diff-level reviewer.

The initial plan assumed the resident could remain as a fallback for users without the pack. That assumption was invalidated by the footprint gate: the gate's `REFUSE` verdict on any cross-pack path collision made it impossible to install the pack's skill alongside core's identically-named resident.

## Why ADR, not RFC

RFC-first is the right gate for a new top-level directory or a cross-cutting structural decision. The `packs/` directory exists; the promotion pattern (`experience-design`, `architect`, `desk-research`) is established. This is an execution decision, not a governance decision: ADR records it.

The deletion is a sub-decision of the same promotion — it resolves a mechanical constraint discovered during implementation, not a new governance question.

## Risk triggers (full-mode justification)

- **Multi-feature or dependent tasks** — 9 skills, 1 agent, 4 work-loop insertion points, a guide tree, a sidebar addition, and a catalogue page are interdependent.
- **Structural or public-interface change** — the pack introduces `frontend-reviewer` as a public interface; `work-loop` references it by name.
- **New dependency** — the pack's `frontend-engineering` skill formalizes a co-install dependency on the `experience-design` pack for genre routing.

## What changes

| Before | After |
|---|---|
| One 443-line skill in `packs/core/.apm/skills/frontend-engineering/SKILL.md` | Deleted |
| `.claude/skills/frontend-engineering/SKILL.md` committed (projected from core) | Deleted via `git rm -r` |
| `.agents/skills/frontend-engineering/SKILL.md` committed (projected from core) | Deleted via `git rm -r` |
| DXC template at `packs/core/.apm/skills/frontend-engineering/references/` | Moved to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/` |
| No pack: no atomic craft skills | 8 atomic skills partitioning the main skill's concerns |
| No diff-level reviewer | `frontend-reviewer` agent in `packs/frontend-engineering/.apm/agents/` |
| No catalogue page | `web/src/content/packs/frontend-engineering.md` |
| No guide tree | `guides/frontend-engineering/` with tutorials, how-to, and reference |
| work-loop: "Frontend pre-flight (mandatory)" | work-loop: "Frontend pre-flight (`frontend-engineering` pack required; named skip if absent)" |
| Pack's `frontend-engineering` skill blocked from installing over core | Pack installs cleanly |

## What does not change

- The pack's `frontend-engineering` skill — unchanged (660 lines; canonical content owner).
- `work-loop`'s four `frontend-engineering` pack references (atomic skills, `frontend-reviewer`) — already gated on pack presence.
- The `experience-design` co-install requirement (genre routing) — unchanged; the pack formalizes what was already a T2 gate.

## Options considered

**Option A — RFC first, then ship:** Open an RFC, gather feedback, accept, then implement. Rejected: `packs/` exists; the promotion pattern is established.

**Option B — ADR + ship (selected):** Record the decision in an ADR; implement immediately. The `packs/` precedent is the reference; no new structural decision is made.

**Option C — Thin stub in core, pack skill renamed:** Keep a stub that probes for `token-architecture` and routes to a renamed pack skill (e.g. `frontend-engineering-craft`). Rejected: renaming the pack's primary skill is a breaking public-interface change requiring an RFC; the footprint gate still blocks coexistence of the stub and an identically-named pack skill.

**Option D — Delete core resident (selected sub-decision):** Clean deletion removes the path conflict. Projected copies removed from git tracking. Users install the pack explicitly for FE guidance.

**Option E — Fix footprint gate to allow pack to supersede resident:** Implement a `supersede` verdict in agentbundle. Deferred: larger agentbundle change with its own RFC surface; deletion achieves the same end state faster. Revisit trigger documented above.
