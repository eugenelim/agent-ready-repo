# ADR-0057: Delete core's `frontend-engineering` resident skill

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision-makers:** eugenelim
- **Amends:** [`ADR-0056`](0056-frontend-engineering-pack-promotion.md) — specifically its clause "The resident `.claude/skills/frontend-engineering/SKILL.md` is **not modified or deleted**."
- **Related:** `docs/specs/frontend-engineering-core-delegation/`

## Decision summary

- **Decision:** Delete `packs/core/.apm/skills/frontend-engineering/SKILL.md`, remove the previously-committed projected copies (`.claude/skills/frontend-engineering/` and `.agents/skills/frontend-engineering/`) via `git rm -r`, and migrate the DXC template copy from the deleted core path to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/`. Update `work-loop` to name the pack requirement and provide a named-skip fallback when the pack is absent.
- **Because:** ADR-0056 left the resident skill in place to preserve a baseline for users without the pack, but this created an unresolvable path conflict: the agentbundle footprint gate (`packages/agentbundle/agentbundle/config.py:229-286`) classifies both skills claiming the same relpath (`frontend-engineering`) as `REFUSE` — making it impossible to install the pack's 660-line version alongside core's 443-line resident. Deletion removes the conflict; the pack's version installs cleanly.
- **Applies to:** `packs/core/`, the committed projected copies under `.claude/skills/` and `.agents/skills/`, and the two `work-loop` insertion points that reference the `frontend-engineering` skill directly.
- **Tradeoff accepted:** Users who have `core` installed but not the `frontend-engineering` pack will no longer have a fallback FE skill. This is the honest outcome: the craft rules live in the pack; `core` is not the right home for them.
- **Revisit if:** An alternative conflict-resolution mechanism (pack supersedes resident rather than refusing) is implemented in agentbundle, at which point the resident could return as a thin named-skip stub.

## Context

ADR-0056 promoted `frontend-engineering` to a first-class pack (2026-07-25). Its "What does not change" section stated: "The resident `.claude/skills/frontend-engineering/SKILL.md` is not modified or deleted." That clause assumed coexistence was possible; it was not. The footprint gate's `REFUSE` verdict on any cross-pack path claim meant the pack's skill was blocked on every install attempt over a core-installed baseline.

The pack is already the canonical content owner (660 lines, four modes, evidence manifest, WCAG 2.2 AA, CWV targets). The resident was 443 lines. No content is lost from the pack's perspective. Users who need FE craft guidance install the `frontend-engineering` pack explicitly; the self-host recipe is not modified.

## Why amend rather than fully supersede ADR-0056

ADR-0056's core decision — promoting `frontend-engineering` to a first-class pack — stands unchanged. Only the "not modified or deleted" sub-clause is reversed. A full supersession would imply the pack promotion itself was wrong; it was not. This ADR amends the one clause that was invalidated by the footprint gate discovery.

## What changes

| Before | After |
|---|---|
| `packs/core/.apm/skills/frontend-engineering/SKILL.md` exists (443 lines) | Deleted |
| `.claude/skills/frontend-engineering/SKILL.md` committed (projected from core) | Deleted via `git rm -r` |
| `.agents/skills/frontend-engineering/SKILL.md` committed (projected from core) | Deleted via `git rm -r` |
| DXC template at `packs/core/.apm/skills/frontend-engineering/references/` | Moved to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/` |
| work-loop: "Frontend pre-flight (mandatory)" | work-loop: "Frontend pre-flight (`frontend-engineering` pack required; named skip if absent)" |
| Pack's `frontend-engineering` skill blocked from installing alongside core | Pack installs cleanly once core resident is removed |

## What does not change

- The pack's `frontend-engineering` skill — unchanged (660 lines; it is the canonical content owner).
- ADR-0056's promotion decision — the pack itself is correct; only the "resident not deleted" clause is amended.
- work-loop's four `frontend-engineering` pack references (atomic skills, `frontend-reviewer`) — all already gated on pack presence; no change needed.

## Options considered

**Option A — Thin stub in core, pack skill renamed:** Keep a stub that probes for `token-architecture` and routes to a renamed pack skill (e.g. `frontend-engineering-craft`). Rejected: renaming the pack's primary skill is a breaking public-interface change requiring an RFC; the footprint gate still blocks coexistence of the stub and an identically-named pack skill.

**Option B — Delete core resident and remove projected copies (selected):** Clean deletion removes the path conflict. Projected copies removed from git tracking. Users install the pack explicitly for FE guidance. No renaming required.

**Option C — Fix footprint gate to allow pack to supersede resident:** Implement a new `supersede` verdict in agentbundle that replaces the resident with the pack version on install. Rejected for now: a larger agentbundle change with its own RFC surface; the deletion achieves the same end state faster.
