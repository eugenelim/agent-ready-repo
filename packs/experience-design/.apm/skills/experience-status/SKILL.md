---
name: experience-status
description: "Orient to the current design thread at a glance — reads design artifacts from the configured output directory and surfaces what exists, what's missing, and which skill to run next. Triggers on 'where are we with the design', 'what experience artifacts do we have', 'status of the design thread', 'what's next in the design', 'show me what design work exists', or any cold-start orient for the experience-design work thread. Read-only: never writes files, never elicits configuration. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# /experience-status

Cold-start orient for a sustained experience-design thread. Run this when you return to design work and want to know what artifacts exist, what's missing from the minimal viable thread (journey map → screen flow → per-screen briefs), and which skill to run next.

**Read-only** by contract (ADR-0054): it never writes files, never elicits `[design] output_dir` (stops at "not configured"), and never advances state.

## Output rendering

Status list — Lead each row with a status glyph — ● running, ✓ done, ○ idle, ⚠ blocked — status first, one item per line, labels aligned.
Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## When to invoke

Any cold-start orient for the design thread: *"where are we with the design"*, *"what experience artifacts do we have"*, *"status of the design thread"*, *"what's next in the design"*, *"show me what design work exists"*. Also useful at session start alongside `workspace-status` to orient to an ongoing experience thread.

Not for reviewing the quality of design artifacts — use `design-review` for that.

## Procedure

### 1. Resolve `[design] output_dir`

Read the output directory from the config chain — **read-only; never elicit**:

1. **Repo-scope:** `./agentbundle-layout.toml` `[design] output_dir` — if the file exists and the key is present.
2. **User-scope:** `~/.agentbundle/agentbundle-layout.toml` `[design] output_dir` — if the file exists and the key is present.
3. **Not configured:** stop. Surface:

   > No `[design] output_dir` configured — run `journey-mapping` to create your first artifact (it will set the path).

   Do not prompt for a path. Do not write to any config file.

Resolve `output_dir` to its full absolute path (`~`-expand, reject `..` escapes).

### 2. Scan design artifacts

Read from the following paths under `output_dir` — create no directories or files:

| Path pattern | Expected frontmatter / marker | Artifact type |
|---|---|---|
| `<output_dir>/journeys/*.md` | `type: customer-journey` | Journey map |
| `<output_dir>/screens/*-flow.md` | `type: screen-flow` | Screen flow |
| `<output_dir>/screens/<slug>/*.md` | bold-body marker `- **Type:** screen-brief` | Per-screen brief |
| `<output_dir>/blueprints/*.md` | `type: service-blueprint` | Service blueprint |

For each path pattern, glob the files and read enough of each file to extract the relevant field or marker. Treat a missing directory as zero files (not an error).

**Per-screen briefs:** the `- **Type:** screen-brief` marker appears in the body (not frontmatter) of brief files written by `user-flow`. A file under `screens/<slug>/` that does NOT contain this marker is not a brief (it may be a handover file or draft — skip it for counting purposes).

### 3. No-artifacts branch

If no files match any pattern across all four paths: surface

> No design artifacts found — run `journey-mapping` to start the design thread.

Stop here.

### 4. Steel-thread check

The minimal viable design thread runs: **journey map → screen flow → per-screen briefs**. Check each link:

| Check | Pass condition | Fail action |
|---|---|---|
| **Journey map exists** | At least one `journeys/*.md` with `type: customer-journey` | Report missing: suggest `journey-mapping` |
| **Screen flow exists** | At least one `screens/*-flow.md` with `type: screen-flow` | Report missing: suggest `user-flow` |
| **Per-screen briefs exist** | At least one `screens/<slug>/*.md` with `- **Type:** screen-brief` marker | Report missing: suggest `user-flow` |
| **Journey stage → brief coverage** | All frontstage actions in the journey map have a corresponding screen brief | **Manual check required** — cross-referencing journey stage actions against screen brief slugs requires reading both artifacts; surface as "manual check required — compare `journeys/*.md` frontstage actions against `screens/<slug>/` brief files." |

### 5. Surface results

Format output with the following sections (omit sections with zero entries):

---

**Design thread — `<output_dir>`**

**Journey maps** (`journeys/`): N found
<list each: `<slug>.md` — <title or first heading if readable>>

**Screen flows** (`screens/`): N found
<list each: `<slug>-flow.md`>

**Per-screen briefs** (`screens/`): N found across N flow(s)
<list each flow slug and the brief count under it>

**Service blueprints** (`blueprints/`): N found
<list each: `<slug>.md`>

**Steel-thread check:**
- Journey map: ✓ exists / ✗ missing — run `journey-mapping`
- Screen flow: ✓ exists / ✗ missing — run `user-flow`
- Per-screen briefs: ✓ exist / ✗ missing — run `user-flow`
- Journey stage → brief coverage: manual check required — compare `journeys/*.md` frontstage actions against `screens/<slug>/` brief files.

**What to run next:** <one of the following, in order of priority>
- If journey map is missing: run `journey-mapping`
- If screen flow is missing (but journey map exists): run `user-flow`
- If per-screen briefs are missing (but flow exists): run `user-flow`
- If all three exist: thread is complete — run `service-blueprint` if backstage mapping is needed, or `creative-direction` / `design-token-taxonomy` / `interaction-design` to enrich the screen briefs.

---

If `output_dir` exists but all four paths have zero files: fall through to the no-artifacts branch (step 3).

## What this skill is not

- Not `journey-mapping` — it reads what exists; it does not author a journey map.
- Not `user-flow` — it reads what exists; it does not sequence screens or write briefs.
- Not `design-review` — it checks structural completeness (thread gaps), not design quality.
- Not `workspace-status` — it gives the experience-design slice only; `workspace-status` gives the full initiative queue picture.
