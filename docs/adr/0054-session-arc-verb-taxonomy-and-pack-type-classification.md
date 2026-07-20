# ADR-0054: Session-arc verb taxonomy and pack-type classification for skill naming

- **Status:** Accepted
- **Date:** 2026-07-20
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0067 (driving RFC — all decisions); RFC-0025 (work-loop light mode — no-new-skill precedent for Change C); RFC-0050 (clean-retire rename precedent: design-craft → experience-design rename with no install-time alias); ADR-0051 (workspace-toml format — check-workspace named as historical record); ADR-0053 (product-strategy pack — check-workspace routing record)

## Decision summary

- **Decision:** We will adopt a canonical five-verb taxonomy (`status`, `start`, `check`, `init`, `resume`) and a four-type pack classification (episodic / sustained-project / sustained-derived / stateless) as the naming and design framework for session-arc skills across all catalogue packs.
- **Because:** Three packs already span sessions (desk-research, experience-design, product-strategy), and without a shared vocabulary pack authors independently solve the same arc-design questions — producing inconsistent naming, missing orient skills, and repeated reviewer cycles catching the same gaps.
- **Applies to:** All catalogue packs that carry durable work across sessions; every future pack RFC that adds a status skill, a project-start skill, or a config-driven output path.
- **Tradeoff accepted:** Clean retire of `check-workspace` → `workspace-status` creates a brief breaking-change window for adopters who invoke the old name; there is no backward-compatible shim.
- **Revisit if:** A new pack type emerges that doesn't fit the four-type classification, or the verb taxonomy accumulates enough exceptions that the banned-label list must be revised.

## Context

RFC-0067 (accepted 2026-07-20) identified that the catalogue had three packs producing durable work across sessions (desk-research, experience-design, product-strategy) but no shared vocabulary for naming the skills that let a user cold-start orientation. The workspace-level orient skill was named `check-workspace` — an action verb, not the information it provides. Pack authors had no documented framework for deciding whether their pack needs a status skill, a project-start skill, or a vault-path pattern. As more packs landed, pack authors would independently solve the same arc-design questions without a shared vocabulary, leading to inconsistent naming, missing orient skills, and repeated reviewer cycles.

The session-arc vocabulary (Arrive → Orient → Work → Persist → Collaborate) already existed in the `workspace-design` skill. RFC-0067 applied it to pack authoring by establishing the verb taxonomy and pack-type classification this ADR records.

## Decision

We will maintain the following as authoritative conventions for session-arc skill naming and pack design across the catalogue:

### Verb taxonomy (operative skill names)

| Verb | Meaning | Activation phrasing |
| --- | --- | --- |
| `status` | Orient — "where am I / what's next?" | Cold-start phrases, "what's on today", "orient me" |
| `start` | Create/begin a sustained project | "start a research project", "kick off an investigation" |
| `check` | Quality/health read — "is it good / saturated / done?" | "is this ready", "should I keep gathering" |
| `init` | Repo-scaffold only | `init-project`, `adapt-to-project`; cf. `git init` |
| `resume` | Return to prior work | Activation phrase — not a skill name; see work-loop's argless trigger |

**Banned as skill names:** `arrive`, `orient`, `onboard`, `return`, `onboarding` — these are UX-stage labels (from the `workspace-design` session-arc vocabulary), not user-facing commands.

### Pack-type classification

| Type | Description | Examples |
| --- | --- | --- |
| **Episodic** | No persistent state between sessions; each invocation is standalone | architect, product-strategy, converters, iac-terraform |
| **Sustained-project** | Creates and manages a durable project that persists across sessions | desk-research |
| **Sustained-derived** | Reads from and builds upon a durable project created elsewhere | experience-design (reads from journey maps, screen flows, blueprints) |
| **Stateless** | Pure workflow transformation; no file-system output | (hypothetical utility packs) |

Episodic packs do not require a `*-status` skill — there is no persistent thread state to orient to.

### Rename: `check-workspace` → `workspace-status` (clean retire)

The `workspace-status` skill is the canonical cold-start orient skill for workspace-level orientation. The old name `check-workspace` is removed entirely from operative references in one PR; all operative references are swept in the same PR. No alias is maintained. The clean-retire approach follows RFC-0050 precedent.

Historical-record files (frozen ADR bodies, changelog entries, shipped spec bodies) are left as-is per CONVENTIONS §2 — a mechanical rename is not a decision reversal and does not require a superseding ADR or erratum.

### Argless work-loop resume: list-and-ask disambiguation

When `work-loop` is invoked without a spec path argument, Step 0 collects all active spec paths across all `["ini-NNN"]` sections with `status = "active"`. The behavior is:

1. **Exactly one active item** → begin the loop on that spec without asking.
2. **Zero active items** → "No active spec found — run `workspace-status` to see what's ready to start."
3. **More than one active item** (whether from a single initiative's multi-element `.active` array or across multiple initiatives) → list all active paths and ask the user to pick before beginning.

This replaces the existing "auto-pick the first path" behavior. The change is a description + body edit to `work-loop` SKILL.md per RFC-0025 no-new-skill precedent; no new skill is needed.

## Decision drivers

1. **Naming consistency** — users predict skill names across packs; inconsistency erodes trust and generates support load.
2. **Pack-author framework** — a documented design framework prevents repeated reviewer cycles on future pack RFCs; the cost of authoring it now is lower than N future rounds of review.
3. **No alias debt** — clean retire avoids permanently maintaining two names that undermine the taxonomy; RFC-0050 established this as the catalogue's rename convention.
4. **Non-surprising disambiguation** — list-and-ask is consistent with `workspace-status` disambiguation behavior; auto-picking the first path is silent and surprising when a user has two initiatives in flight.

## Consequences

**Positive:**
- Future pack authors have a documented decision framework before writing their first skill, reducing reviewer cycles.
- Users predict skill names from the taxonomy; `*-status` is the canonical cold-start pattern.
- The workspace-level orient skill name (`workspace-status`) matches the taxonomy it defines.
- Argless `work-loop` resume is non-surprising and handles multi-initiative workspaces correctly.

**Negative:**
- Clean retire creates a brief breaking-change window; adopters invoking `check-workspace` by name will get a "skill not found" error until they update. Mitigation: the rename is announced in the changelog; the new description triggers include all phrasing the old skill responded to.
- The four-type classification is a first-principles taxonomy with no external prior art; it may not cover future pack archetypes. Mitigation: `Revisit if` trigger above.

**Revisit if:** A new pack type emerges that doesn't fit the four-type classification, or the verb taxonomy accumulates enough exceptions that the banned-label list needs to be revised.

## Confirmation

- **Mode:** lint/CI + reviewer-checked
- **Signal:** The operative-reference lint gate (`grep -rn "check-workspace"` over `git ls-files`, excluding the explicit historical set) returns zero hits after Spec A ships. Future pack RFCs are reviewed against this ADR's verb taxonomy and pack-type classification by `adversarial-reviewer`.
- **Owner:** eugenelim (lint gate); `adversarial-reviewer` at spec-stage review (taxonomy conformance).

## Alternatives considered

**Alias `check-workspace` → `workspace-status` (two names permanently):** Zero breaking change; permanently maintains two names and undermines the taxonomy. Rejected — alias never cleanly removes itself; RFC-0050 established clean retire as the catalogue's rename convention.

**New `workspace-resume` skill for argless work-loop:** Creates a second activation surface; duplicates work-loop triggers; "resume" becomes ambiguous between two skills. Rejected per RFC-0025 no-new-skill precedent: a description + body change to work-loop is sufficient when no new activation surface is needed.

**Separate guide per pack archetype (four guides instead of one):** Zero staleness per pack; high maintenance N-way duplication. Rejected — archetype membership changes slowly; one shared framework at archetype level is the stable shape.

**Status skills for episodic packs:** Episodic packs have no persistent thread state to orient to. A `*-status` skill on an episodic pack would have nothing to read. Rejected — the pack-type classification is the principled boundary.

## References

- RFC-0067: `docs/rfc/0067-session-arc-conventions-and-pack-workflow-guide.md`
- RFC-0025 (no-new-skill precedent): `docs/rfc/0025-work-loop-light-mode-and-risk-based-escalation.md`
- RFC-0050 (`docs/rfc/0050-the-experience-pack.md`): clean-retire precedent — design-craft → experience-design rename with no install-time alias. Note: RFC-0067 §Evidence cites "RFC-0048 (Scope-decouple and renames)" for this precedent, but RFC-0048 in this repo is the autonomous-product-team RFC; the actual rename precedent is RFC-0050.
- `packs/experience-design/.apm/skills/workspace-design/SKILL.md` — session-arc vocabulary (Arrive → Orient → Work → Persist → Collaborate) this ADR builds on
- `packs/governance-extras/.apm/skills/rfc-status/SKILL.md` — `*-status` orient precedent
