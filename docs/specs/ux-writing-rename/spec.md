# Spec: ux-writing-rename

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0066](../../rfc/0066-experience-pack-surface-genre-and-skill-uplift.md) D7 — approved the rename in principle; deferred to "a separate product-engineering RFC"; this spec discharges that mandate via an errata to RFC-0066 (per RFC-0055)
  - [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) OQ3 — confirms scope is PE pack + experience-design inbound refs; requires grep-verified count before ship
  - [ADR-0038](../../adr/0038-rename-design-craft-pack-to-experience.md) — alias-free rename precedent: rename live surface, bridge frozen governance, no install-time alias
- **Contract:** none — skill directory rename and documentation changes; no API contract.
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user reading or invoking the product-UI-copy skill encounters it only as `ux-writing`. The `voice-and-microcopy` skill directory in `product-engineering` is renamed; frontmatter updated; all operative references across `product-engineering`, `experience-design`, `product-strategy`, guides, and web content swept in the same PR. RFC-0066 gains an `## Errata` entry discharging the "separate product-engineering RFC" requirement from D7. Lint gate over the operative set returns zero `voice-and-microcopy` hits.

## Boundaries

### Always do

- Derive the exact operative reference list from `git ls-files | xargs grep -l "voice-and-microcopy"` at implementation time, not from this spec's illustrative list.
- Classify each hit as operative or historical before rewriting: frozen RFC/ADR/spec bodies and `docs/product/changelog.md` shipped entries are historical — leave them.
- Update experience-pack inbound references in lockstep (RFC-0066 §Follow-on artifacts names them exactly).
- Run `make build-self` after all source edits; commit the projected tree in the same PR.
- Add `## Errata` to RFC-0066 (after `## Follow-on artifacts`); entry must be Approver-signed per RFC-0055.
- Record grep-verified count in this spec before opening the PR (RFC-0071 OQ3).

### Ask first

- Any operative file that, on inspection, carries both an operative and a historical `voice-and-microcopy` reference in the same location.
- Changing the skill's trigger description beyond updating the `name:` field and removing the self-reference in the scope-boundary note.

### Never do

- Edit frozen RFC bodies (0048, 0050, 0053, 0062, 0066 body, 0071 body) — historical records.
- Edit frozen ADR bodies.
- Edit `docs/specs/` bodies for this purpose — spec prose is a historical record.
- Edit `docs/product/changelog.md` shipped entries.
- Edit `docs/rfc/README.md` row descriptions — those describe what the RFCs say; updating the row for RFC-0066 post-ship is a separate follow-on.
- Add an alias or backward-compatibility shim for `voice-and-microcopy` — ADR-0038 is alias-free.

## Testing Strategy

All criteria use **goal-based check**: each corrected reference is verifiable by running `grep` against the renamed source path, or the lint gate output. No production code changes; no TDD-mode tasks.

One **manual QA** step: after `make build-self`, confirm `packs/product-engineering/.apm/skills/ux-writing/` exists and `voice-and-microcopy/` does not (PE skills are not projected to `.claude/skills/`; that path is core-only).

**Grep-verified count (RFC-0071 OQ3):** record the number of operative files updated here before opening the PR.

<!-- Grep-verified count: 21 operative files updated (pre-sweep count, 2026-07-27: 18 inbound refs + workspace.toml + SKILL.md + evals.json in renamed dir) -->

## Acceptance Criteria

- [x] **AC1.** `packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exists; `packs/product-engineering/.apm/skills/voice-and-microcopy/` does not.
- [x] **AC2.** `SKILL.md` frontmatter `name:` field reads `ux-writing`. Scope-boundary self-reference in the body updated to `ux-writing`.
- [x] **AC3.** Lint gate: `git ls-files | xargs grep -Hn "voice-and-microcopy"`, excluding the historical set (frozen RFC bodies 0048/0050/0053/0062/0066/0071, all ADR bodies, all `docs/specs/` bodies, `docs/product/changelog.md`, `docs/rfc/README.md`, `docs/rfc/0053-notes/` spike artifacts), returns zero hits.
- [x] **AC4.** `make build-self` exits 0 (confirmed at implementation time: `product-engineering` skills are NOT projected to `.claude/skills/` or `.agents/skills/` — those paths are core-only; the source directory at `packs/product-engineering/.apm/skills/ux-writing/` is the authoritative location).
- [x] **AC5.** RFC-0066 gains a `## Errata` section (after `## Follow-on artifacts`) with an entry noting this spec discharges the D7 "separate product-engineering RFC" requirement. Entry is Approver-signed per RFC-0055.
- [x] **AC6.** `docs/product/changelog.md` gains an `[Unreleased]` entry noting the rename.
- [x] **AC7.** `make build-check` exits 0.
- [x] **AC8.** All operative references derived at runtime from `git ls-files | xargs grep -Hl "voice-and-microcopy"` (excluding the AC3 historical set) are updated to `ux-writing`. Known operative files include: `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md`, `packs/experience-design/.apm/skills/user-flow/SKILL.md`, `packs/experience-design/.apm/skills/user-flow/assets/design-tool-handover-template.md`, `packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md`, `packs/experience-design/.apm/skills/user-flow/references/screen-flow.md`, `packs/experience-design/.apm/skills/design-review/references/quality-floor.md`, `packs/experience-design/.apm/skills/content-design/SKILL.md`, `packs/experience-design/README.md`, `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md`, `packs/product-engineering/README.md`, `packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md`, `guides/README.md`, `guides/experience-design/reference/experience-design.md`, `guides/product-engineering/README.md`, `guides/product-engineering/how-to/write-product-microcopy.md`, `web/src/components/marketing/PackCatalogue.astro`, `web/src/content/journeys/discovery.md`, `web/src/content/packs/product-engineering.md`, `workspace.toml` (remove rename mention from `product-engineering-shaping-doctrine` comment).

## Assumptions

- Technical: `pack.toml` and `plugin.json` for `product-engineering` already use `ux-writing` in their description fields and have no skills-array entry for `voice-and-microcopy` — no manifest changes needed beyond the directory rename and frontmatter update (verified at spec time).
- Technical: `make build-self` regenerates core-pack projected paths (`.claude/skills/`, `.agents/skills/`); `product-engineering` skills are not projected to these paths — they ship to adopters via `agentbundle install` (verified at implementation time).
- Process: RFC-0066 is Accepted — post-acceptance corrections use `## Errata` (not `## Amendments`) per RFC-0055.
- Process: RFC-0071 OQ3 records a grep-verified count requirement; that count is recorded in this spec before the PR opens.
