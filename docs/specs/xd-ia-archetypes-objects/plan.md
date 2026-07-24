# Plan: xd-ia-archetypes-objects

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec,
> this document is allowed to change as you learn.

## Approach

Six files change: a new `references/page-archetypes.md` in the IA skill (the
core deliverable); an update to `information-architecture/SKILL.md` adding
two new numbered steps (archetype routing and product-object mapping) that
reference the new file; a new how-to guide in
`docs/guides/experience-design/how-to/page-archetypes.md`; updates to
`docs/guides/experience-design/README.md` and
`web/src/content/journeys/experience-design.md`; and the pack version bump
in both `pack.toml` and `.claude-plugin/plugin.json`.

All tasks verify via goal-based checks (file presence, field counts, grep) and
visual / manual QA (content completeness). No test runner is needed — these
are documentation artifacts verified by inspection.

## Constraints

- ADR-0038: skill changes are additive, alias-free.
- RFC-0071 (ini-003): all XD changes must land as a minor bump (1.2.x → 1.3.0 for this spec).
- Rule 4 (process): pack.toml and plugin.json must be updated atomically.
- Rule 6 (process): run check-contract-drift.py after any ownership-field changes.

## Construction tests

**Cross-cutting verification:**

```bash
# AC-1: page-archetypes.md exists
ls packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md

# AC-2: >=12 archetype sections (H2 headings with archetype numbering)
grep -c "^## [0-9]" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md

# AC-7: SKILL.md references page-archetypes.md
grep "page-archetypes" packs/experience-design/.apm/skills/information-architecture/SKILL.md

# AC-8: how-to guide exists
ls docs/guides/experience-design/how-to/page-archetypes.md

# AC-11: pack version parity
grep "^version" packs/experience-design/pack.toml
python3 -c "import json; d=json.load(open('packs/experience-design/.claude-plugin/plugin.json')); print(d['version'])"

# AC-12: contract drift
python3 tools/check-contract-drift.py --root .

# AC-13: workspace.toml parseable
python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb')); print('ok')"
```

## Tasks

### Task 1: Author references/page-archetypes.md

**Depends on:** none
**Verification mode:** visual / manual QA + goal-based check (field count)

**Tests:**
```bash
# File exists
ls packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
# >=12 archetype H2 sections
grep -c "^## [0-9]" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
# All 10 required fields present in each archetype (spot check first and last)
grep "**Primary user**\|**Job**\|**First-screen contract**\|**Primary action**\|**Expected result**\|**Next action**\|**Proof**\|**Read/write consequence**\|**Critical states**\|**Navigation behavior**" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md | wc -l
# Product-object mapping section exists
grep -q "Product-object mapping" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
# Card-use test section exists
grep -q "Card-use test" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
# Attention contract section exists
grep -q "Attention contract" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
# Permission contract section exists
grep -q "permission contract" packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md
```

**Approach:** Author the complete reference file at
`packs/experience-design/.apm/skills/information-architecture/references/page-archetypes.md`.
The file has four major sections:
1. Page archetypes (12+ entries, each with 10 fields)
2. Product-object mapping (five roles + visual weight rules)
3. Card-use test (criteria + non-card alternatives)
4. Attention contract (4 levels)
5. Read/write permission contract (6 levels)

### Task 2: Update information-architecture/SKILL.md

**Depends on:** Task 1
**Verification mode:** goal-based check

**Tests:**
```bash
grep "page-archetypes" packs/experience-design/.apm/skills/information-architecture/SKILL.md
grep "Identify the archetype\|product-object" packs/experience-design/.apm/skills/information-architecture/SKILL.md
```

**Approach:** Add two new numbered steps to the IA procedure before the existing step 1:
- Step 0 (prepend, after the existing multi-surface step 0): "Identify the surface archetype" — route to `references/page-archetypes.md`, identify archetype, apply its first-screen contract.
- Step 0b: "Identify the product object" — route to `references/page-archetypes.md` product-object mapping section.

Actually, keep the existing step numbering intact and add the archetype/object steps as sub-steps of step 1 ("Frame the surface and route by genre"), since archetype selection refines the genre routing already there.

### Task 3: Author docs/guides/experience-design/how-to/page-archetypes.md

**Depends on:** Task 1
**Verification mode:** visual / manual QA

**Tests:**
```bash
ls docs/guides/experience-design/how-to/page-archetypes.md
grep -c "|" docs/guides/experience-design/how-to/page-archetypes.md  # table rows
```

**Approach:** Write the how-to guide following the pattern of
`author-design-intent.md`. Include: decision procedure ("which archetype?"),
the 12+ archetype quick-reference table (columns: archetype, primary user, job,
first-screen contract), and brief guidance on applying attention and permission
contracts.

### Task 4: Update docs/guides/experience-design/README.md

**Depends on:** Task 3
**Verification mode:** goal-based check

**Tests:**
```bash
grep "page-archetypes" docs/guides/experience-design/README.md
```

**Approach:** Add one line to the How-to section listing the new guide.

### Task 5: Update web/src/content/journeys/experience-design.md

**Depends on:** Task 1
**Verification mode:** goal-based check

**Tests:**
```bash
grep "archetype\|product.object" web/src/content/journeys/experience-design.md
```

**Approach:** Update step 4 ("Design each screen") in the journey page to
explicitly name archetype identification and product-object mapping as the
first two sub-steps before structural IA is designed. Also add
`information-architecture` annotation to the skill entry to name these as
required inputs.

### Task 6: Bump pack version to 1.3.0

**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5
**Verification mode:** goal-based check

**Tests:**
```bash
grep "^version" packs/experience-design/pack.toml
python3 -c "import json; d=json.load(open('packs/experience-design/.claude-plugin/plugin.json')); assert d['version']=='1.3.0', d['version']; print('ok')"
```

**Approach:** Update `version = "1.2.1"` to `version = "1.3.0"` in pack.toml
and the corresponding `"version"` field in `.claude-plugin/plugin.json`.

### Task 7: Update workspace.toml (spec → shipped)

**Depends on:** Task 6
**Verification mode:** goal-based check

**Tests:**
```bash
python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); shipped=d['ini-003']['work']['shipped']; assert any('xd-ia-archetypes-objects' in str(s) for s in shipped), 'not in shipped'; print('ok')"
```

**Approach:** Move `{path = "spec/xd-ia-archetypes-objects", needs = [...]}` from
`["ini-003".work].queue` to `["ini-003".work].shipped` as a bare string
`"spec/xd-ia-archetypes-objects"`.

## Changelog

- 2026-07-23: Initial plan authored.
