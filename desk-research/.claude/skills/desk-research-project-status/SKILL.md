---
name: desk-research-project-status
description: "Orient to the current desk-research project at a glance — reads overview.md and surfaces phase, working hypothesis, stop-signal verdict, and what to do next. Triggers on 'where are we on the X research', 'status of the Y investigation', 'resume the Z project', 'what phase is the research in', 'where did we leave off on the research', or any return-to-a-named-research-project phrasing. Read-only: never advances phase, never modifies any file."
---

# /desk-research-project-status

Cold-start orient for a sustained desk-research project. Run this when you return to a project and want to know where it stands — what phase it is in, what the current working hypothesis is, and what to do next.

**Read-only** by contract (ADR-0054): it never advances `phase`, never invokes `desk-research-project-digest` or `desk-research-project-synthesize`, and never modifies `overview.md`.

## When to invoke

Any return-to-a-named-research-project phrasing: *"where are we on the X research"*, *"status of the Y investigation"*, *"resume the Z project"*, *"what phase is the research in"*, *"where did we leave off on the research"*. Also useful at session start alongside `workspace-status` to orient to a sustained research thread.

For a one-off lookup (no project), use `/desk-research` instead. For a saturation check, use `/desk-research-project-check`.

## Procedure

### 1. Resolve `[research] output_dir`

Read the output directory from the config chain — **read-only; do not elicit**:

1. **Repo-scope:** `./agentbundle-layout.toml` `[research] output_dir` — if the file exists and the key is present.
2. **User-scope:** `~/.agentbundle/agentbundle-layout.toml` `[research] output_dir` — if the file exists and the key is present.
3. **Not configured:** stop. Surface: "No `[research] output_dir` configured — run `desk-research-project-start` to set up your first project (it will configure the path)."

Resolve `output_dir` to its full absolute path (`~`-expand, reject `..` escapes). Never write to any config file.

### 2. Find the project folder

Look for direct subdirectories of `output_dir` that contain an `overview.md`. A project folder is named `<YYYY-MM-DD>-<slug>` by convention.

- **No project folder found:** surface the no-project message (step 3).
- **One project folder found:** proceed to step 4.
- **Multiple project folders found:** proceed with the most recent (highest date prefix). At the end of the output, list any others with their slug and current `phase` as a brief note.

### 3. No-project branch

Surface:

> No research project found — run `desk-research-project-start` for a sustained project, or `desk-research` for a one-off lookup.

Stop here. Do not create any file or folder.

### 4. Read `overview.md` and surface status

Read `<project-folder>/overview.md`. Extract the following frontmatter fields:

| Field | Notes |
|-------|-------|
| `phase` | Valid values: `capture`, `digest`, `synthesize`, `feedback` |
| `working_hypothesis` | May be empty — surface as "(none yet)" if blank |
| `stop_signal` | Initial value `not-yet-assessed`; updated by hand or by `desk-research-project-check` |
| `verdict_status` | Optional — written only by `desk-research-project-check`; omit if absent |

Also read: `question` (the research question, for context).

Surface the status in this format:

---

**Research project: `<slug>`** (`<project-folder>`)

**Question:** <question from frontmatter>

**Phase:** `<phase>` — <next-step recommendation (see table below)>

**Working hypothesis:** <working_hypothesis, or "(none yet)">

**Stop signal:** `<stop_signal>`<if verdict_status is present: ` — verdict: <verdict_status>`>

---

### 5. Next-step recommendations by phase

| Phase | Next step |
|-------|-----------|
| `capture` | Run `desk-research-project-digest` to build the synthesis matrix and memos from accumulated sources. |
| `digest` | Run `desk-research-project-synthesize` to produce the research brief from the synthesis matrix. |
| `synthesize` | Brief is ready — share with stakeholders. When feedback has been received, advance `phase` to `feedback` in `overview.md`. |
| `feedback` | Project complete — brief has been shared and feedback is being incorporated. No further skill to run. |

If `phase` contains an unrecognised value, surface it as-is with a note: "Unrecognised phase — expected one of: capture, digest, synthesize, feedback."

## What this skill is not

- Not `desk-research-project-digest` — it reads the current state; it does not build the synthesis matrix.
- Not `desk-research-project-synthesize` — it reads the current state; it does not produce the brief.
- Not `desk-research-project-check` — it reports the `stop_signal` value as stored; it does not evaluate saturation.
- Not `workspace-status` — it gives the research-project slice only; `workspace-status` gives the full initiative queue picture.
