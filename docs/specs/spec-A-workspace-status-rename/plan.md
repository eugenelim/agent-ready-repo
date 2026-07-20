# Plan: spec-A-workspace-status-rename

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure rename-and-sweep, with no logic changes. The shape: rename the skill directory in source, update frontmatter, update all operative references derived from `git ls-files | xargs grep -l "check-workspace"`, add the verb taxonomy section to `author-a-skill.md`, then run `make build-self` to regenerate the projected tree. The lint gate (zero `grep` hits over the operative set) is the hard acceptance criterion; everything else is in service of passing it.

The riskiest part is the operative-reference sweep: the RFC identifies ~46 tracked files. The implementation must derive the exact list at runtime (`git ls-files | xargs grep -l "check-workspace"`) rather than using the RFC's illustrative list, which may be stale. Classification (operative vs. historical) follows the RFC-0067 §Change A rules exactly.

Order of operations: rename source → update frontmatter → sweep references → add taxonomy section → build-self → lint gate → open PR.

## Constraints

- RFC-0067 §Change A: no alias; clean retire only; operative/historical classification rules are normative.
- ADR-0054: verb taxonomy table content is normative; the `## Naming your skill` section must reproduce it accurately.
- CONVENTIONS §2: frozen ADR bodies and shipped spec bodies are never edited.
- CONVENTIONS §Pack source-of-truth split: `make build-self` must be run after source edits; direct edits to projected paths are caught by `make build-check` and rejected.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Lint gate (cross-cutting, runs at T6):**
```bash
git ls-files | xargs grep -Hn "check-workspace" | \
  grep -v "docs/adr/0051-" | \
  grep -v "docs/adr/0053-" | \
  grep -v "docs/adr/0054-" | \
  grep -v "docs/product/changelog.md" | \
  grep -v "docs/specs/" | \
  grep -v "docs/rfc/0067-"
# Must return zero hits. (-H forces filename:line even in single-file xargs batches)
```

**Build gate (cross-cutting, runs at T7):**
```bash
make build-check
# Must exit 0.
```

## Tasks

### T1: Rename skill directory and update pack manifest

**Depends on:** none
**Touches:** packs/core/.apm/skills/, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, .claude-plugin/marketplace.json

**Tests:**
- Goal-based (AC1): `ls packs/core/.apm/skills/workspace-status/` succeeds; `ls packs/core/.apm/skills/check-workspace/` fails.
- Goal-based (AC2): `name: workspace-status` present in frontmatter; `description:` contains "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next".
- Goal-based (AC3): `grep "workspace-status" packs/core/pack.toml` returns a hit; `grep "check-workspace" packs/core/pack.toml` returns nothing.
- Goal-based (AC4): `grep "workspace-status" packs/core/.claude-plugin/plugin.json` returns a hit.

**Approach:**
- `git mv packs/core/.apm/skills/check-workspace packs/core/.apm/skills/workspace-status`
- Update `name:` in `packs/core/.apm/skills/workspace-status/SKILL.md` from `check-workspace` to `workspace-status`.
- Update `description:` to add RFC-0067 §A1 trigger phrases (cold-start phrasing, "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next").
- Update `packs/core/pack.toml` skills array entry.
- Update `packs/core/.claude-plugin/plugin.json` skill entry name.

**Done when:** AC1, AC3, AC4 hold; `git mv` recorded cleanly in `git status`. (The SKILL.md H1 title and any body self-references to `check-workspace` are swept in T3, not T1.)

---

### T2: Derive and classify all operative references

**Depends on:** T1

**Tests:**
- Goal-based: `git ls-files | xargs grep -l "check-workspace"` produces a list; every hit is classified as operative or historical using RFC-0067 §Change A rules; no hit is left unclassified.

**Approach:**
- Run `git ls-files | xargs grep -l "check-workspace"` to get the live file list.
- For each file, apply the RFC-0067 §Change A classification:
  - **Historical (leave as-is):** `docs/adr/0051-*.md`, `docs/adr/0053-*.md`, `docs/adr/0054-*.md` (ADR-0054 discusses the rename as narrative — ~8 references are historical record), `docs/product/changelog.md`, `docs/specs/**`, `docs/rfc/0067-*.md`, this RFC's own body.
  - **Operative (rewrite):** everything else — skill body, AGENTS.md files, seeds, pack manifests, plugin.json, marketplace.json, README files, cross-pack routing references, guides, product docs, site/, web/, docs/rfc/README.md, docs/rfc/0064-*.md (Draft), `workspace.toml` (line 5 comment).
- Produce a working list of operative files for T3.

**Done when:** Every file in the grep output has an operative/historical classification. Working list is noted in .context/ for T3.

---

### T3: Sweep all operative references to `workspace-status`

**Depends on:** T2
**Touches:** operative files derived in T2

**Tests:**
- Goal-based (AC9): after editing, `grep -Hn "check-workspace"` on each operative file returns zero hits.

**Approach:**
- Edit each operative file from T2's list, replacing `check-workspace` with `workspace-status` where it appears as an operative reference.
- Special care for `docs/rfc/0064-ini-001-ai-native-ecosystem.md` (Draft — the ADR-0009/strategy-pack reference in D9 names `check-workspace`; update it).
- For seed files (`packs/core/seeds/AGENTS.md`, workspace.toml seed comment), update the prose reference.
- For `docs/CONVENTIONS.md`, update the routing-table entry if it names `check-workspace` by skill name.
- Confirm no operative file retains `check-workspace` after edits.

**Done when:** Zero operative hits; historical files untouched.

---

### T4: Add `## Naming your skill` section to `author-a-skill.md`

**Depends on:** none
**Touches:** docs/guides/_shared/how-to/author-a-skill.md

**Tests:**
- Goal-based (AC7): the file gains a `## Naming your skill` section after `## Body structure` with the verb table (5 rows: status, start, check, init, resume) and the banned-label list (arrive, orient, onboard, return, onboarding).
- Goal-based (AC8): the file's intro section gains the sentence linking to `pack-workflow-design.md`.

**Approach:**
- Read `author-a-skill.md` to find the `## Body structure` section.
- Insert `## Naming your skill` after that section with:
  - The verb taxonomy table from ADR-0054 §Decision (status/start/check/init/resume with Meaning and Activation phrasing columns).
  - The banned-label list sentence: "Banned as skill names: `arrive`, `orient`, `onboard`, `return`, `onboarding` — these are UX-stage labels, not user-facing commands."
- Add the intro sentence to the guide's intro paragraph (or as a callout before the first section): "If you're authoring the first skill in a new pack, read [Pack workflow design](../explanation/pack-workflow-design.md) first — it tells you how to design the pack's arc before writing individual skills." (Note: `author-a-skill.md` is at `docs/guides/_shared/how-to/`; `explanation/` is one level up and across, so the correct relative path is `../explanation/`, not `../../explanation/`. The RFC-0067 body at §A2 incorrectly writes `../../explanation/` — the spec/plan are correct.)
- Create a minimal stub at `docs/guides/_shared/explanation/pack-workflow-design.md` **only if the file does not already exist** (idempotent guard: if Spec D has already shipped the full guide, skip stub creation). The stub contains one introductory sentence noting full content is in Spec D; Spec D fills the guide body.

**Done when:** AC7 + AC8 hold; the verb table matches ADR-0054 exactly. The stub at `docs/guides/_shared/explanation/pack-workflow-design.md` resolves the link.

---

### T5: Add `[Unreleased]` changelog entry

**Depends on:** T1
**Touches:** docs/product/changelog.md

**Tests:**
- Goal-based (AC11): `docs/product/changelog.md` has an `[Unreleased]` entry noting the `check-workspace` → `workspace-status` rename and the skill addition (verb taxonomy section in author-a-skill.md).

**Approach:**
- Add an `[Unreleased]` section (or append to it if one exists) noting:
  - Renamed: `check-workspace` → `workspace-status` (clean retire — no alias).
  - Added: Verb taxonomy (`## Naming your skill`) section to `docs/guides/_shared/how-to/author-a-skill.md`.

**Done when:** AC11 holds.

---

### T6: Run lint gate — zero operative hits

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- Goal-based (AC5): the lint command returns zero hits.

**Approach:**
- Run the cross-cutting lint gate from § Construction tests above.
- If any hits remain, re-classify and fix; they are either missed operative references (fix in T3) or misclassified files.

**Done when:** AC5 holds — zero hits.

---

### T7: Rebuild projected tree and verify build gate

**Depends on:** T6
**Touches:** .claude/skills/workspace-status/, .agents/skills/workspace-status/, all adapter-projected skill paths

**Tests:**
- Goal-based (AC6): `.claude/skills/workspace-status/` and `.agents/skills/workspace-status/` exist; `.claude/skills/check-workspace/` and `.agents/skills/check-workspace/` do not.
- Goal-based (AC10): `make build-check` exits 0.

**Approach:**
- Run `make build-self` (with `FORCE=1` if the working tree is dirty from prior source edits).
- Confirm `.claude/skills/workspace-status/` and `.agents/skills/workspace-status/` are created.
- Confirm `.claude/skills/check-workspace/` and `.agents/skills/check-workspace/` are absent. If `make build-self` does not remove old projected dirs, run `git rm -r .claude/skills/check-workspace/ .agents/skills/check-workspace/` explicitly.
- Stage the regenerated projected tree.
- Run `make build-check` to confirm no drift.

**Done when:** AC6 + AC10 hold.

---

### T8: Final gates and adversarial review

**Depends on:** T7

**Tests:**
- Goal-based (AC1–AC11 all): run the full lint gate + build check; confirm all ACs hold.

**Approach:**
- Run `scripts/lint-spec-status.py` on this spec.
- Confirm `git status` is clean except intended files.
- Run adversarial review; address any Blockers.

**Done when:** All ACs checked; adversarial-reviewer returns `Clean — ready to commit.`

## Rollout

Pure repo-internal change: skill directory rename + source edits + projected tree rebuild. No external-system dependency. The rename is announced in `[Unreleased]` changelog (T5); adopters invoking `check-workspace` by name will get a "skill not found" signal after the PR merges. The new `workspace-status` description triggers cover all phrasing the old skill responded to.

## Risks

- The operative-reference sweep may miss a file if `git ls-files` output differs between the time the RFC was written (~46 files) and implementation time. Mitigation: the lint gate (T6) is the hard acceptance criterion — zero hits is objective.
- `make build-self` may require `FORCE=1` if the working tree has unstaged source edits. Mitigation: use `FORCE=1` explicitly in T7.

## Changelog

- 2026-07-20: initial plan, authored alongside the spec for RFC-0067 spec/plan/ADR follow-on work.
- 2026-07-20: pre-EXECUTE adversarial review fixes — added ADR-0054 to historical exclusion set (lint gate + T2); extended AC6/T7 to cover `.agents/skills/`; added pack-workflow-design.md stub to T4 scope (idempotent guard); simplified AC9 to runtime-derived list; noted T1 H1 handled by T3; added -H to lint gate grep; added .claude/skills/README.md (hand-authored) to AC9 illustrative list.
