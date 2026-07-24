# Plan: xd-state-reviewer-doctrine

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Additive changes to three layers: (1) the shared reference (`quality-floor.md`),
(2) the skill body (`design-review/SKILL.md`), and (3) docs and journey surfaces.
No existing content is deleted — missing states are added to quality-floor.md;
the three-pass structure replaces the current single-pass procedure while
preserving the genre rubrics and anti-patterns that follow it. Evals gain
weak-fixture queries. New files: `how-to/design-review.md`, and a state-coverage
reference in `docs/guides/experience-design/reference/`. The journey page gains
a description of the three-pass gate. Pack bumped 1.4.0 → 1.5.0 in both
`pack.toml` and `plugin.json`; `build-self` regenerates the marketplace
aggregate; `workspace.toml` moves the spec entry to shipped.

Riskiest part: the SKILL.md description must stay ≤ 1024 characters while
describing a richer skill — measure it before committing.

## Constraints

- RFC-0071 D3d: three-pass experience-reviewer; severity tiers; rendered evidence.
- RFC-0071 D9: minor version bump per spec.
- ADR-0024 / lint-experience-agnostic: no framework or platform names in SKILL.md.
- Rule 4 (task brief): plugin.json version must match pack.toml version.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual verification:**
1. `python3 tools/lint-experience-agnostic.py` exits 0 after SKILL.md edits.
2. `python3 tools/check-contract-drift.py --root .` exits 0 (design-review/references/digital-experience-contract.md unchanged).
3. `python3 tools/build_gate_chain.py build-self --force --packs-dir packs` exits 0; dry-run shows no drift.
4. Read quality-floor.md top-to-bottom: all 18 state names present.
5. Read SKILL.md: three-pass structure visible; severity tiers defined; rendered-evidence rule stated.

## Design (LLD)

### Design decisions

- **Three-pass structure replaces single-pass procedure** in SKILL.md § Procedure. The existing numbered steps move into Pass 3 (contract review); Pass 1 and Pass 2 are new introductory passes. The genre rubrics stay after the procedure — they are not moved into a pass. Traces to: AC2, AC3, AC4.
- **Severity tiers defined once, referenced throughout** — defined at the top of the procedure section; applied in all three passes. Traces to: AC3.
- **State coverage reference is a new file** at `docs/guides/experience-design/reference/state-coverage.md` rather than appending to the existing `experience-design.md` reference (which is the skill catalogue, not a topic reference). Traces to: AC8.
- **Journey page edit is additive** — the existing `design-review` skill entry in `whatChanges` and the `G-experience-review` gate gain a sentence describing the three-pass structure. Traces to: AC9.

### Component / module decomposition

Files touched:
- `packs/experience-design/.apm/skills/design-review/references/quality-floor.md` (expand)
- `packs/experience-design/.apm/skills/design-review/SKILL.md` (restructure procedure)
- `packs/experience-design/.apm/skills/design-review/evals/eval_queries.json` (add weak fixtures)
- `packs/experience-design/.apm/skills/design-review/evals/evals.json` (update assertions)
- `docs/guides/experience-design/how-to/design-review.md` (new)
- `docs/guides/experience-design/reference/state-coverage.md` (new)
- `web/src/content/journeys/experience-design.md` (update)
- `packs/experience-design/pack.toml` (bump 1.4.0 → 1.5.0)
- `packs/experience-design/.claude-plugin/plugin.json` (bump 1.4.0 → 1.5.0)
- `docs/specs/xd-state-reviewer-doctrine/spec.md` + `plan.md` (this PR)
- `docs/specs/README.md` (add to active list)
- `workspace.toml` (move to shipped)

## Tasks

### T1: Expand quality-floor.md to 18 states

**Depends on:** none

**Tests:**
- `grep -c "^\*\*" packs/experience-design/.apm/skills/design-review/references/quality-floor.md` ≥ 18 (one bold term per state)
- Manual: all 18 state names appear verbatim — loading, empty, error, partial, disabled, content, success, first-run, no-results, permission/denied, offline, blocked, destructive-confirmation, long-content, large-data-set, high-zoom, reduced-motion, keyboard-only

**Approach:**
- Rewrite `## 1. Handle all states` in quality-floor.md to list all 18 states as a table matching the FE matrix, with design-intent treatments (not build-time treatments).
- Keep the existing introductory paragraph; replace the bullet list with the expanded prose.
- Preserve the `permission/denied` extended note, folding it into the full state entry.

**Done when:** quality-floor.md contains all 18 state entries.

---

### T2: Restructure design-review SKILL.md procedure to three passes

**Depends on:** T1

**Tests:**
- `grep -c "Pass [123]" packs/experience-design/.apm/skills/design-review/SKILL.md` ≥ 3
- `grep "blocker\|concern\|suggestion" packs/experience-design/.apm/skills/design-review/SKILL.md | wc -l` ≥ 3
- `grep -i "rendered evidence\|rendered surface" packs/experience-design/.apm/skills/design-review/SKILL.md` returns ≥ 1 match
- Manual: three passes are named and structured; severity tiers defined; rendered evidence rule stated

**Approach:**
- Before the existing `## Procedure` numbered steps, add: `## Severity tiers` section defining blocker / concern / suggestion with explicit rules.
- Rename the existing `## Procedure` to a three-pass structure: Pass 1 (cold-read), Pass 2 (primary task + unhappy path), Pass 3 (contract review — contains existing steps, renumbered).
- Add rendered-evidence requirement at the top of the procedure.
- Update the frontmatter `description` to mention three-pass structure; measure it ≤ 1024 chars before committing.
- Keep all genre rubrics and anti-patterns unchanged.

**Done when:** `python3 tools/lint-experience-agnostic.py` exits 0; three-pass structure and severity tiers visible in SKILL.md.

---

### T3: Update evals with weak fixtures

**Depends on:** T2

**Tests:**
- `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/design-review/evals/eval_queries.json')); assert any('architecture-first' in q['query'] or 'hero' in q['query'].lower() for q in d), 'missing architecture-first hero fixture'"` exits 0
- `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/design-review/evals/eval_queries.json')); assert any('cards' in q['query'].lower() for q in d), 'missing every-section-as-cards fixture'"` exits 0
- Manual: 6 weak-fixture queries present in eval_queries.json

**Approach:**
- Add 6 new `should_trigger: true` entries to eval_queries.json (one per weak fixture type).
- Update evals.json assertions to include three-pass structure checks and severity tier rules.

**Done when:** eval_queries.json contains all 6 weak fixture types; evals.json assertions cover three-pass behavior.

---

### T4: Create design-review how-to guide

**Depends on:** T2

**Tests:**
- `test -f docs/guides/experience-design/how-to/design-review.md` exits 0
- `grep -i "pass 1\|pass 2\|pass 3\|cold.read\|blocker\|concern\|suggestion" docs/guides/experience-design/how-to/design-review.md | wc -l` ≥ 6

**Approach:**
- Create `docs/guides/experience-design/how-to/design-review.md` as a Diátaxis how-to guide.
- Show the three-pass structure with worked examples per pass.
- Show severity rubric with one example per tier.
- Link to quality-floor.md and state-coverage.md.

**Done when:** guide file exists with three-pass structure and severity rubric visible.

---

### T5: Create state coverage reference

**Depends on:** T1

**Tests:**
- `test -f docs/guides/experience-design/reference/state-coverage.md` exits 0
- Manual: file contains all 18 states with example treatment per state.

**Approach:**
- Create `docs/guides/experience-design/reference/state-coverage.md` as a Diátaxis reference.
- Table: state name | when it applies | design-intent treatment | example.
- 18 rows, one per state.

**Done when:** file exists with 18 rows.

---

### T6: Update journey page to show three-pass gate

**Depends on:** T2

**Tests:**
- `grep -i "three.pass\|pass 1\|pass 2\|pass 3\|cold.read\|blocker" web/src/content/journeys/experience-design.md | wc -l` ≥ 1

**Approach:**
- In `whatChanges`, update the `design-review` sentence to mention three-pass structure.
- In step 4 ("Design each screen"), update the `design-review` mention to name the three-pass self-check.
- In step 5 ("Review independently"), update to note that `design-review` three-pass must complete before `experience-reviewer` runs.
- Keep the existing `G-experience-review` gate entry unchanged (it governs the independent review, not design-review).

**Done when:** journey page mentions three-pass design-review gate before FE handoff.

---

### T7: Bump pack version and update workspace.toml

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- `python3 -c "import tomllib; d=tomllib.load(open('packs/experience-design/pack.toml','rb')); assert d['pack']['version']=='1.5.0'"` exits 0
- `python3 -c "import json; d=json.load(open('packs/experience-design/.claude-plugin/plugin.json')); assert d['version']=='1.5.0'"` exits 0
- `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0 (TOML valid)

**Approach:**
- Bump `version` in `packs/experience-design/pack.toml` from `1.4.0` to `1.5.0`.
- Bump `version` in `packs/experience-design/.claude-plugin/plugin.json` from `1.4.0` to `1.5.0`.
- In `workspace.toml`, comment out the `spec/xd-state-reviewer-doctrine` queue entry and add `"spec/xd-state-reviewer-doctrine"` to the `shipped` list.

**Done when:** both version files show 1.5.0; workspace.toml TOML-parses clean.

---

### T8: Run build-self and verify no drift

**Depends on:** T7

**Tests:**
- `python3 tools/build_gate_chain.py build-self --force --packs-dir packs` exits 0
- `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs` shows no drift

**Approach:**
- Run `python3 tools/build_gate_chain.py build-self --force --packs-dir packs`.
- Run `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs`.
- If drift is shown: inspect what changed, fix, re-run.

**Done when:** dry-run shows no drift.

---

### T9: Add spec to docs/specs/README.md and finalize workspace.toml

**Depends on:** T7

**Tests:**
- `grep "xd-state-reviewer-doctrine" docs/specs/README.md` returns a match.

**Approach:**
- Add the spec to the Active specs table in `docs/specs/README.md`.
- Verify workspace.toml transition is correct with `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"`.

**Done when:** spec appears in README.md; workspace.toml is valid TOML.

## Rollout

Pure content change — no runtime, no data migration, no infrastructure. Ships
as a single PR. Reversible by reverting the PR. build-self regenerates the
marketplace aggregate.

## Risks

- SKILL.md description length: the three-pass description may push the
  frontmatter `description` field past 1024 characters — measure explicitly
  before committing (Rule 5).
- workspace.toml length (>1350 lines): do not truncate the file; read it fully
  before editing, change only the two relevant lines (Rule 7).

## Changelog

- 2026-07-24: initial plan
