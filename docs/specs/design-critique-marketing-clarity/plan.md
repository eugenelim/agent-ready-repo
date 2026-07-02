# Plan: design-critique-marketing-clarity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Implementing

## Tasks

### Task 1: Add marketing clarity mode to design-critique SKILL.md

**Verification mode:** Visual / manual QA

**Done when:** `design-critique` SKILL.md contains a mode 3 (marketing clarity)
with the three criteria (tweet test, five-second scan, painkiller-first), modes
are renumbered 1–4, frontmatter description includes marketing trigger phrases,
and a human reading the skill can trace exactly what gets checked on a marketing
page.

**Tests:** `no stub (mode)` — prose doc; scenario-based verification per spec.

**Approach:**
1. Edit `packs/experience/.apm/skills/design-critique/SKILL.md`:
   - Update frontmatter `description:` to add marketing/copy trigger phrases
   - Renumber existing mode 3 (taste) → mode 4
   - Insert new mode 3 (marketing clarity) between heuristics and taste
   - Add trigger condition, three criteria, severity mapping, source label
2. Run `make lint-packs` to verify pack metadata is valid.
3. Run `make build-self` to project the updated skill.

**Depends on:** none

### Task 2: Bump experience pack version

**Verification mode:** Goal-based check

**Done when:** `packs/experience/pack.toml` version reads `0.4.0` and
`make build-self` produces a clean `marketplace.json` reflecting the new version.

**Tests:** `no stub (mode)` — verify with `grep '"version": "0.4.0"' marketplace.json`

**Approach:**
1. Bump `[pack] version` in `packs/experience/pack.toml` from `0.3.0` to `0.4.0`.
2. Bump `"version"` in `packs/experience/.claude-plugin/plugin.json` from `0.3.0`
   to `0.4.0` (marketplace.json aggregates from plugin.json, not pack.toml).
3. Run `make build-self` to regenerate marketplace.json.

**Depends on:** Task 1 (build-self regenerates from source edits)

### Task 3: Update changelog and close backlog item

**Verification mode:** Goal-based check

**Done when:** `docs/product/changelog.md` has an `[Unreleased]` entry for the
marketing clarity mode; `docs/backlog.md` item
`design-critique-marketing-clarity-criterion` is closed with a shipped note.

**Tests:** `no stub (mode)` — grep for entry existence.

**Approach:**
1. Add entry to `docs/product/changelog.md` `[Unreleased]` / `### Added`.
2. Add shipped tombstone to `docs/backlog.md` under the item heading.

**Depends on:** Task 1
