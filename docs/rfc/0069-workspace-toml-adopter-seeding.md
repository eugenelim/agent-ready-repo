# RFC-0069: workspace.toml adopter seeding

<!-- Glossary for cold readers:
  adopter — a team installing agentbundle packs into their own repo to get the
    governance framework (skills, agents, seeds) delivered by the pack.
  workspace.toml — TOML coordination manifest; the repo's declared-intent
    file; per-initiative sections declared via `["ini-NNN"]` headers.
  agentbundle — the CLI that installs pack primitives (skills, agents, hooks,
    seeds) into an adopter's repo.
  core pack — the foundation pack (`packs/core/`) that every agentbundle
    install starts with; ships seeds like AGENTS.md, CONVENTIONS.md, etc.
  Seeds — files in `packs/<pack>/seeds/` delivered to the adopter's repo on
    install via the standard seed-delivery pipeline.
  workspace-status — the skill that reads workspace.toml and surfaces queue
    state (ready items, blocked items, active signals).
  EXCLUDED_PATTERNS — a tuple in self_host.py that lists paths the self-host
    build preserves on disk rather than overwriting from the seed template.
  self-host build / make build-self — the mechanism by which this catalogue
    repo projects its own pack source into its `.claude/` and `.agents/`
    directories so the repo's own agents use the latest skill versions.
-->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-22
- **Date closed:** 2026-07-22
- **Decision weight:** light
- **Related:** RFC-0064 (workspace.toml schema + workspace-status skill), RFC-0002 (self-hosting; Manual semantics and EXCLUDED\_PATTERNS), RFC-0001 (seed delivery contract), docs/specs/core-install-seed-delivery/ (seed delivery mechanics)

## Reviewer brief

- **Decision:** seed `workspace.toml` to adopters on `agentbundle install` so the file exists from day one, consistent with the installed CONVENTIONS.md which references `workspace.toml [backlog].open`.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Add `packs/core/seeds/workspace.toml` — a minimal schema-commented TOML file with a `[backlog]` section and no live initiative data.
  - Add `"workspace.toml"` to `EXCLUDED_PATTERNS` in `self_host.py:351` (Manual semantics per RFC-0002) to protect the repo's curated coordination file from being overwritten on reprojection.
  - Register `"workspace.toml"` in `REQUIRED_PLACEHOLDERS` in `tools/lint-catalogue-seeds.py:94` with `("[backlog]",)` — asserting the section header is present.
  - Bump core pack version and add a `[Unreleased]` changelog entry (seed addition requires a version bump per repo convention).
- **Affected surface:** core pack seeds, `self_host.py` (build), `lint-catalogue-seeds.py` (seed registry), agentbundle adopter install.
- **Stakes:** reversible — a seed file can be removed from the pack if the approach proves wrong; EXCLUDED\_PATTERNS and REQUIRED\_PLACEHOLDERS are one-line reverts.
- **Review focus:** (1) whether seeding is the right delivery mechanism vs workspace-status-initialise-only; (2) whether the minimal-template approach (comments + [backlog] only) is right given workspace-status has a richer full-schema template.
- **Not in scope:** workspace.toml schema (RFC-0064/ADR-0031); the workspace-status initialise path content; tracker integration; the broader workspace management design (RFC-0062).

## The ask

**Recommendation (BLUF):** Approve adding `workspace.toml` as a minimal, schema-commented core-pack seed so adopters receive a parseable coordination file on install, eliminating the gap where the installed CONVENTIONS.md references `workspace.toml [backlog]` but install never creates the file.

**Why now (SCQA — Situation/Complication/Question):** The m3-backlog-absorption spec ("m3" = Milestone 3; Shipped) moved all deferred-item tracking from `docs/backlog.md` to `workspace.toml [backlog].open`. PR #616 removed the `docs/backlog.md` seed and updated the installed CONVENTIONS.md to point at `workspace.toml [backlog].open`. This leaves a gap: CONVENTIONS.md tells adopters that deferred items live in `workspace.toml [backlog].open`, but `agentbundle install` never creates `workspace.toml`, so the file is absent on fresh install. The workspace-status skill already handles the absent case interactively ("offer to initialise"), but there is no path that creates `workspace.toml` as part of initial install, before an adopter first reaches workspace-status.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|----|----------|----------------|-----|-----------|-----------------|
| D1 | Seed `workspace.toml` via install, or rely on workspace-status-initialise only? | **Seed it** (option A) | Consistent with AGENTS.md/CONVENTIONS.md delivery; closes the "install + read CONVENTIONS.md" → "no workspace.toml" gap immediately | This review | Confirm or redirect to option B/C |
| D2 | What content should the seed contain? | **Minimal: schema comments + `[backlog]` section only, no initiative sections** | Avoids surfacing a fake initiative on first `workspace-status` run; workspace-status's "offer to initialise" path remains the right tool for the full schema setup | This review | Confirm or propose different content |
| D3 | How to register and validate the seed without a fragile byte-comparison? | **Register in `REQUIRED_PLACEHOLDERS` with `("[backlog]",)`** — checks the section header is present in the seed file; defer full-schema parity lint to a follow-on | Simple, robust; full parity between seed and workspace-status template is a separate problem (workspace-status's "blank file" template is richer than this seed, and that's intentional) | This review | Confirm or propose alternative lint |
| D4 | Should `workspace.toml` be added to `EXCLUDED_PATTERNS`? | **Yes** — RFC-0002 Manual semantics; `docs/CHARTER.md` is the in-repo precedent (`self_host.py:369`) | Without it, every `make build-self` would overwrite the repo's initiative queue with the blank seed template | This review | Confirm |

## Problem & goals

### Problem

`agentbundle install core` seeds AGENTS.md, docs/CHARTER.md, docs/CONVENTIONS.md, and docs/specs/README.md. The installed CONVENTIONS.md (since PR #616) directs adopters to use `workspace.toml [backlog].open` for deferral tracking and `workspace-status` to view open backlog items. But `workspace.toml` is not a seed, so it does not exist after install. An adopter who follows the CONVENTIONS.md instructions immediately after install has no `workspace.toml` to write deferred items into.

The workspace-status skill handles the absent case: it offers to create a blank file or bootstrap with the user's first initiative. But this recovery path requires the adopter to know to invoke workspace-status, which may not happen until they're already mid-session encountering the CONVENTIONS.md reference.

### Goals

1. Close the install→CONVENTIONS.md consistency gap: if CONVENTIONS.md says deferred items live in `workspace.toml [backlog].open`, install should deliver `workspace.toml`.
2. Deliver a file that workspace-status can parse without surfacing fake initiative data.
3. Protect the repo's curated `workspace.toml` from being silently overwritten by `make build-self` (Manual semantics per RFC-0002).

### Non-goals

- Changing the `workspace.toml` schema (RFC-0064/ADR-0031).
- Pre-populating the seed with example initiatives or placeholder initiative sections.
- Making the seed content match workspace-status's richer "blank file" full-schema template byte-for-byte (those two files serve different jobs — see D3 below).
- Delivering `workspace.toml` via any route other than the core-pack seed.

## Proposal

### D1: Seed workspace.toml via install

Add `packs/core/seeds/workspace.toml`. The existing seed delivery pipeline (RFC-0001; `install.py:1111-1145`, `deliver_seeds()` in `agentbundle.commands._common`) auto-globs `packs/<pack>/seeds/**` and delivers each file with standard Tier-1/2/3 safety (the three cases the seed-delivery contract defines):
- **Tier 1 — fresh install, file absent:** write the template.
- **Tier 1 — reinstall / upgrade, file identical:** skip (clean no-op).
- **Tier 2 — reinstall / upgrade, file differs (adopter-edited):** write a `workspace.upstream.toml` companion (`.upstream.toml` suffix = the incoming seed content saved alongside the adopter's edited file for reference); leave the adopter's file untouched.

No manifest step is required — the pipeline auto-discovers seeds.

### D2: Template content

The seed file contains schema comments and a `[backlog]` section only. No initiative sections are included, because TOML sections with placeholder values (e.g. `["<initiative-slug>"]`) are valid TOML and workspace-status would parse and surface them as a real (fake) active initiative on the first run.

The workspace-status "offer to initialise" path already delivers the richer full-schema template with initiative sections when an adopter is ready for that setup. The seed closes the narrower gap: workspace.toml exists and the [backlog] section is usable immediately.

Proposed seed content:

```toml
# workspace.toml
#
# Declared-intent coordination artifact for this repo.
# Each initiative gets its own named section. Run `workspace-status` to surface
# ready items, blocked items, and active signals — or to initialise this file
# with your first initiative and the full schema.
#
# Queue entries are strings (no deps) or inline objects {path/slug, needs}.
# `needs` uses queue-prefix notation:
#   "work:<path>"      — depends on a work queue entry
#   "shape:<slug>"     — depends on a shaping queue entry
#   "research:<slug>"  — depends on a research entry
#   "brief:<path>"     — depends on a brief queue entry
#   "backlog:<slug>"   — depends on a repo-level [backlog] item
#
# The [backlog] section below tracks open work not yet scoped to an initiative.
# Add items as: {slug = "my-deferred-item"}
# Run `workspace-status` to see all open backlog items.
# (Template above is illustrative only; seed and lint are the authoritative copy.)

[backlog]
open = []
```

### D3: Seed registration and lint

Register `"workspace.toml"` in `REQUIRED_PLACEHOLDERS` (not `SEED_REGISTRY` — that symbol doesn't exist; the registry in `tools/lint-catalogue-seeds.py:94` is `REQUIRED_PLACEHOLDERS`) with `("[backlog]",)`. The existing lint then asserts:
1. The file is present in `packs/core/seeds/`.
2. The string literal `[backlog]` appears somewhere in the file.

This is robust to comment changes, schema evolution, and whitespace variation. A byte-comparison parity lint between the seed and workspace-status's embedded full-schema template is deferred — the two templates intentionally differ (seed is minimal; workspace-status initialise is rich), so parity would be wrong.

### D4: EXCLUDED_PATTERNS

Add `"workspace.toml"` to `EXCLUDED_PATTERNS` in `packages/agentbundle/agentbundle/build/self_host.py:351`. This follows RFC-0002's "Manual semantics" (RFC-0002's term for files that are seeded once and then become the adopter's hand-maintained artifact — the self-host reprojection step, which regenerates the repo's own `.claude/` and `.agents/` directories from the pack source, skips files under Manual semantics to avoid overwriting curated content). The in-repo precedent is `docs/CHARTER.md` at `self_host.py:369`.

### D5: Core pack version bump and changelog

Adding a seed triggers a core pack version bump (patch) and a `[Unreleased]` changelog entry in the same PR, per repo convention.

## Options considered

**D1 axis: delivery mechanism for workspace.toml (exhausts: install-time / lazy-init / no-action)**

| Option | Description | Trade-offs |
|--------|-------------|------------|
| **A) Seed it** ✓ | `agentbundle install core` writes workspace.toml alongside AGENTS.md and CONVENTIONS.md | Immediate; consistent onboarding model; standard seed delivery contract applies |
| B) workspace-status initialise only | Recovery path already exists; update CONVENTIONS.md to say "run workspace-status to create" | Zero new files; but adopter must know to invoke workspace-status before encountering the CONVENTIONS.md backlog reference — a non-obvious prerequisite |
| C) Do nothing | Leave CONVENTIONS.md with a dangling reference | Honest but degrades the install experience; CONVENTIONS.md remains inconsistent until adopter discovers workspace-status |

**D2 axis: seed template completeness (exhausts: minimum viable / matched to workspace-status / richer)**

| Option | Description | Trade-offs |
|--------|-------------|------------|
| **A) Minimal — comments + [backlog] only** ✓ | Closes the immediate gap; workspace-status parses it without surfacing fake initiatives | Two-path UX: install delivers minimal file; workspace-status initialise delivers richer template with initiative sections |
| B) Full schema-documented template (matching workspace-status "blank file") | Both paths produce same output | Full template has placeholder initiative sections (`["<initiative-slug>"]`) that workspace-status would parse and surface as a fake active initiative "<Initiative Name>" |
| C) Richer template with commented-out example | More instructive | Harder to lint for accuracy; example initiative content goes stale |

**D3 axis: drift prevention (exhausts: no lint / presence+content lint / byte-comparison / single-source)**

| Option | Description | Trade-offs |
|--------|-------------|------------|
| **A) REQUIRED\_PLACEHOLDERS with `("[backlog]",)`** ✓ | Simple presence+content check; robust | Does not catch schema comment drift between seed and workspace-status template; acceptable given the two templates intentionally differ |
| B) Byte-comparison parity lint against workspace-status source | Mechanical enforcement of identical content | Wrong for this design: seed (minimal) intentionally differs from workspace-status template (rich); would fail on every correct change |
| C) workspace-status reads seed file instead of embedding template | Single source; eliminates drift | workspace-status's install path writes to the adopter's repo — after install, the seed file lives in the adopter's installed workspace, not in a stable location the skill can reference from the pack; the skill has no stable path to read the seed at runtime |
| D) Seed generated from workspace-status as build artifact | Eliminates drift | Adds build pipeline complexity; same objection as C — the two files serve different jobs |

**D4: binary** — not adding `workspace.toml` to `EXCLUDED_PATTERNS` would cause `make build-self` to overwrite the repo's initiative queue data on every run. Option B is not viable.

## Risks & what would make this wrong

**Pre-mortem:**
- *workspace-status "offer to initialise" now overlaps with the seed*: if workspace.toml already exists (from the seed), workspace-status's initialise path never fires on a fresh install. An adopter wanting the full-schema template must delete workspace.toml and re-run workspace-status, or edit the file manually. Mitigation: document the workspace-status initialise path as the upgrade path, not the initial-setup path.
- *EXCLUDED\_PATTERNS path mismatch*: workspace.toml is at the seeds root, so its relative path is `"workspace.toml"` — confirmed matches how `docs/CHARTER.md` is listed at `self_host.py:369`. No subdirectory prefix is needed.

**Key assumptions (falsifiable):**
- The minimal-template approach (comments + [backlog] only) is sufficient for CONVENTIONS.md compliance. If CONVENTIONS.md references workspace.toml features beyond [backlog] (e.g., initiative sections), the seed would need to grow. Currently CONVENTIONS.md references only `workspace.toml [backlog].open` and `workspace-status`.
- workspace-status's lint for missing-but-referenced workspace.toml (absent → offer to initialise) will degrade gracefully when the file exists but is minimal (valid TOML, [backlog] present). Confirmed by reading workspace-status SKILL.md: the present-and-parseable path proceeds to DAG (Directed Acyclic Graph — workspace-status resolves dependency edges from the `needs` field across the initiative queue) resolution; an empty [backlog] and no initiative sections produce an empty output, not an error.

**Drawbacks:**
- The install and workspace-status initialise paths now produce structurally different workspace.toml files. An adopter who deletes workspace.toml and re-runs workspace-status gets the richer template; one who reinstalls gets the minimal seed. This is a UX inconsistency the two-path design introduces.
- EXCLUDED\_PATTERNS grows by one entry; minor but trends toward more exceptions.
- Core pack version bump and changelog entry required; minor operational overhead.

## Evidence & prior art

**Spike / de-risk:** No spike needed. `EXCLUDED_PATTERNS` already protects several files using identical path-matching mechanics (`self_host.py:351–393`). `workspace.toml` at the repo root matches the same way as `docs/CHARTER.md` at `self_host.py:369`. The `deliver_seeds()` function (`install.py:1111`) is file-format-agnostic; TOML files are delivered identically to Markdown files.

**Repo precedent:**
- RFC-0002 (self-hosting), particularly the 2026-05-25 amendment: "Pack seed at these paths are placeholder templates adopters receive on first install… on-disk copies are this repo's hand-maintained instance." (`docs/rfc/0002-self-hosting.md:330`) — this is the governing framework for EXCLUDED\_PATTERNS additions.
- `docs/rfc/0064-ini-001-ai-native-ecosystem.md:457,591` — workspace-status absent-file "offer to initialise" behavior; this RFC's seeding proposal complements that path (seed = install-time scaffolding; initialise = setup-time richer template).
- `docs/specs/core-install-seed-delivery/spec.md` — seed delivery contract and Tier-1/2/3 companion safety.

**External prior art:** Web search was not available in this session. Comparable ecosystem patterns: `cargo init` (Rust) seeds Cargo.toml; `npm init` seeds package.json; `go mod init` seeds go.mod — all project coordination manifests are seeded at project init rather than deferred to a secondary command. The pattern supports seed-at-install for coordination artifacts that contain per-project declarative configuration.

## Open questions

None — all decisions are recommended above and ready to decide in this review.

## Follow-on artifacts

- Spec: `docs/specs/workspace-toml-adopter-seeding/` (Implementing → Shipped in same PR)
- No ADR needed: this is an application of existing RFC-0002 Manual semantics to a new file, not a new architectural decision.
