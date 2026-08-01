# QA Evidence: work-loop-step0-observability AC9

**Date:** 2026-08-01
**Spec:** `docs/specs/work-loop-step0-observability/spec.md`
**AC:** AC9 — Argless work-loop invocation with exactly one active spec produces an orientation block that includes "Beginning on `docs/specs/<slug>/spec.md`".

## Setup

Disposable worktree at `/tmp/wl-qa-S6L3` (HEAD of `eugene/work-loop-step0-observability-reassess`).

Updated SKILL.md projection copied into worktree from main tree root:
```sh
cp .claude/skills/work-loop/SKILL.md /tmp/wl-qa-S6L3/.claude/skills/work-loop/SKILL.md
```

Synthetic fixture:
- `docs/specs/qa-test-echo/spec.md` — template-shaped, `Status: Approved`
- `docs/specs/qa-test-echo/plan.md` — template-shaped, `Status: Drafting`

Minimal `workspace.toml` (replaced full workspace.toml to ensure exactly one active item):
```toml
["ini-999"]
name = "QA"
status = "active"
milestone = "qa"

["ini-999".work]
queue = []
active = ["spec/qa-test-echo"]
shipped = []
```

## Command

```sh
cd /tmp/wl-qa-S6L3
claude -p "work-loop" --output-format stream-json --verbose
```

## Observed orientation block (first assistant turn)

```
**ORIENT — Step 0**

| Field | Value |
|---|---|
| Initiative | QA (`ini-999`) |
| Milestone | qa |
| Active spec | Beginning on `docs/specs/qa-test-echo/spec.md` |

One active item found; proceeding to PLAN.
```

## AC9 verdict

**PASS.** The orientation block includes `Beginning on \`docs/specs/qa-test-echo/spec.md\`` as
the "Active spec" field, alongside Initiative and Milestone. The updated SKILL.md instruction
("If exactly one, include 'Beginning on `docs/specs/<slug>/spec.md`' in this orientation block.")
was followed correctly.
