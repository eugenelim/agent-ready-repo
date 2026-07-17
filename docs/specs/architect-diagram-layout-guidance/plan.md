# Plan: architect-diagram — Mermaid layout guidance and skill design guide

All paths relative to repo root.
Skill base: `packs/architect/.apm/skills/architect-diagram/`

## Tasks

### Task 1 — Write fixture test harness

Depends on: none
Verification mode: goal-based

Approach: Create `scripts/test_fixtures.py` inside the skill directory. Parametrises
over `scripts/testdata/*.mmd` via `glob`; invokes `mmdc -i <fixture> -o <tmp>` via
subprocess; asserts exit code 0. Uses `shutil.which("mmdc")` — skips all cases if
mmdc absent. No conftest.py.

Done when: `python -m pytest packs/architect/.apm/skills/architect-diagram/scripts/test_fixtures.py -v`
reports 1 skipped (empty glob, no `testdata/` yet), session exits 0.

---

### Task 2 — Write all fixture files

Depends on: Task 1
Verification mode: goal-based

Approach: Create `scripts/testdata/` and write each of the 16 fixture files listed in
AC7. Verify each with `mmdc -i <file> -o /tmp/test.svg` as it's written. If
`mindmap-tidy.mmd` or `c4-container.mmd` (with `UpdateLayoutConfig()`) fails to parse,
surface before proceeding (Assumption 3 and 5 in spec).

Done when: `python -m pytest packs/architect/.apm/skills/architect-diagram/scripts/test_fixtures.py -v`
reports 15–16 passed, 0 failed.

---

### Task 3 — Update `references/mermaid-flowchart.md`

Depends on: Task 2 (fixtures validate new ELK/curve/subgraph-direction syntax)
Verification mode: goal-based

Content to add (all grounded in `mermaid-layout-survey.md`):
- `## Edge routing — curve style` section (AC1)
- `## Layout control` section (AC2 — subgraph direction, inheritDir,
  subGraphTitleMargin, spacing directives, label wrapping)
- `## ELK renderer — for complex graphs` section (AC3)
- Update `## Common architecture pitfalls` (AC4 — invisible links, edge label overlap
  + grammaticality)

Done when:
- `grep -c "## Edge routing" .../references/mermaid-flowchart.md` ≥ 1
- `grep -c "## Layout control" .../references/mermaid-flowchart.md` ≥ 1
- `grep -c "## ELK renderer" .../references/mermaid-flowchart.md` ≥ 1
- `grep -c "invisible" .../references/mermaid-flowchart.md` ≥ 1
- `grep -c "grammatical" .../references/mermaid-flowchart.md` ≥ 1

---

### Task 4 — Update `references/mermaid-c4.md`

Depends on: Task 3
Verification mode: goal-based

Content to add: `## Layout config` section (AC5 — c4ShapeInRow, c4BoundaryInRow,
UpdateLayoutConfig(), statement-ordering caveat, Lay_* unsupported).

Done when: `grep -c "c4ShapeInRow" .../references/mermaid-c4.md` ≥ 1

---

### Task 5 — Update `references/mermaid-mindmap.md`

Depends on: Task 4
Verification mode: goal-based

Content to add: `## Layout algorithms` section (AC6 — cose-bilkent, tidy-tree,
maxNodeWidth, padding, when to use which).

Done when: `grep -c "tidy-tree" .../references/mermaid-mindmap.md` ≥ 1

---

### Task 6 — Write explanation guide and update README

Depends on: Task 5
Verification mode: manual QA

Approach: Write `docs/guides/architect/explanation/architect-diagram-skill-design.md`
with all seven sections from AC9. No imperative instructions. Update
`docs/guides/architect/README.md` with `## Explanation` section (AC10).

Done when:
- Guide file exists with all seven sections
- No step-by-step instructions in guide prose
- `grep -c "Explanation" docs/guides/architect/README.md` ≥ 1

---

### Task 7 — Pack bump and changelog

Depends on: Task 6
Verification mode: goal-based

Done when:
- `grep "0.12.0" packs/architect/pack.toml` passes
- `grep "0.12.0" .claude-plugin/plugin.json` passes
- `make build-self` exits 0 and `marketplace.json` updated
- Changelog entry exists
