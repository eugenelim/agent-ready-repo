# Plan: workspace-status-next-actions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Single-file prose edit: insert a `### 6. Next-actions` section into `packs/core/.apm/skills/workspace-status/SKILL.md` (the source file; `.claude/skills/...` and `.agents/skills/...` are generated projections) as the last step under `## Procedure` (before `## See also`), then run `make build-self` to regenerate both projected copies. The section is a decision-tree procedure for the LLM: open with the DAG-only preamble → resolve choices from Step 2 state → detect parallel opportunity → detect harness → emit. No new files, no new dependencies.

The riskiest part is the harness-detection instruction: it must discriminate on feature presence (`--bg` in `claude --help` output), not on exit code, and degrade gracefully when the flag is absent or Bash is unavailable. Manual QA in Case B validates both branches.

## Constraints

- RFC-0064: workspace.toml schema — queue entry shapes (`path`, `needs`, `slug`, `type`) the procedure must read correctly from Step 2 state.
- `spec/spec-A-workspace-status-rename`: defines the canonical name `workspace-status` and the frontmatter trigger list — both preserved as-is.

## Construction tests

**Integration tests:** none beyond per-task tests — the change is isolated to one skill file.

**Manual verification (Case B, both harness branches):**
- Case B (Claude Code): invoke workspace-status with ≥2 unblocked items; confirm ASCII graph rendered + numbered parallel choice with `claude --bg` present.
- Case B (non-`--bg`): invoke in an environment where `claude --help` does not include `--bg`; confirm prose suggestion emitted, no `claude --bg`.

## Design (LLD)

### Behavior & rules

The next-actions section (Step 6) is inserted before `## See also`, as the last step under `## Procedure`. It applies this decision tree.

**Step 6 preamble (required, verifiable):**
```
Using Step 2 DAG state only — do not re-read workspace.toml:
```

**Choice derivation:**

```
active_spec  = first entry in [work].active (if any)
next_queue   = first entry in [work].queue with all `needs` satisfied (if any)
unblocked    = all entries in [work].queue with all `needs` satisfied
next_shape   = first entry in [shaping_queue].active (if any);
               else first entry in [shaping_queue] ready (unblocked, not shipped)
```

**Graph trigger (≥2 unblocked work items):**

Emit before numbered choices:
```
Work queue — parallel opportunities:

  <slug-A>  [ready]
  <slug-B>  [ready]
  <slug-C>  [blocked by <slug-A>]
```
Slug column right-padded to longest slug for alignment. Root nodes (unblocked) annotated `[ready]`; dependent nodes annotated `[blocked by <dep-slug>]` where `<dep-slug>` is the resolved slug from Step 2 state with the queue-prefix (`work:`, `shape:`, etc.) stripped — e.g. `needs = "work:spec/alpha"` renders as `[blocked by spec/alpha]`.

**Harness detection (used when graph is rendered):**

Check whether `--bg` appears in `claude --help` output (not exit code alone — exit code is unreliable as `--help` short-circuits flag validation). The parallel offer occupies the first numbered slot when present (before the role-labelled choices). If `--bg` found → Claude Code CLI:
```
1. Run in parallel:
   Session A: claude --bg "work-loop docs/specs/<slug-A>/"
   Session B: claude --bg "work-loop docs/specs/<slug-B>/"
```
If `--bg` absent from help, or Bash unavailable → prose (same first slot):
```
1. To run in parallel, open two sessions:
   Session A: work-loop docs/specs/<slug-A>/
   Session B: work-loop docs/specs/<slug-B>/
```

**Numbered choices (follow graph + parallel offer if present):**

1. (if active spec) `work-loop docs/specs/<slug>/` — continue active spec
2. (if next queue item) `work-loop docs/specs/<slug>/` — next queue item
3. (if actionable shaping item) `<skill-command>` on `<slug>`; if required pack not installed: "requires `<pack-name>` pack — install to work this item" (per Step 4 format)
4. (always) Start new work: `new-spec` · `new-rfc` · `new-adr` · `queue-add`

Numbering is sequential; omitted items collapse the numbers (no gaps). The parallel-session offer (when present) occupies a numbered slot between the graph and Choice 1.

### Failure, edge cases & resilience

- **`[work].active` contains multiple entries:** use first entry only for Choice 1; no change to existing multi-active rendering.
- **Unblocked queue entry is an inline object `{path = "...", needs = ...}`:** extract `path` field for slug resolution; same logic as Step 2's existing needs-resolution.
- **All queue items blocked:** `unblocked` list is empty → no graph (0 < 2), Choice 2 omitted.
- **Queue has exactly 1 unblocked item:** no graph, no parallel offer; Choice 2 emitted normally.
- **`--bg` check fails or Bash unavailable:** treat as probe failure; degrade to prose. Do not block.
- **Shaping entry's required pack not installed:** emit "requires `<pack>` pack" note on the Choice 3 line; do not omit Choice 3 silently.

## Tasks

### T1: `### 6. Next-actions` section produces correct output for all four fixture cases

**Depends on:** none

**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`

**Tests:**
- **Case A (skill installed):** `active = ["spec/foo"]`, `queue = [{path="spec/bar", needs="work:spec/baz"}]` (baz in shipped), `shaping_queue.active = ["my-shape"]` (type=`shape`, `frame-intent` available) → 4 numbered choices in order (active spec, queue item, shaping item with `frame-intent` command, start new work); no graph. Verifies: AC Choice 1, Choice 2, Choice 3 (skill-command branch), "Start new work".
- **Case A (pack absent):** `active = ["spec/foo"]`, `queue = [{path="spec/bar", needs="work:spec/baz"}]` (baz in shipped), `shaping_queue.active = [{slug="my-research", type="research"}]`, `desk-research` pack not installed → Choice 3 line reads `"requires \`desk-research\` pack — install to work this item"` rather than `desk-research-project-start`. Verifies: AC Choice 3 (pack-absent branch); uses a `type=research` entry because Step 4 names the pack explicitly for that type.
- **Case B (≥2 unblocked):** `active = []`, `queue = ["spec/alpha", "spec/beta", {path="spec/gamma", needs="work:spec/alpha"}]` → ASCII graph with `alpha [ready]`, `beta [ready]`, `gamma [blocked by spec/alpha]`; then 3 numbered choices (parallel offer, first unblocked item `spec/alpha`, start new work); `spec/gamma` absent from choices. Verifies: AC graph, parallel offer, Choice 2.
- **Case B harness branch — Claude Code:** `--bg` in `claude --help` output → numbered choice includes `claude --bg` commands. Verifies: AC parallel offer (Claude Code branch).
- **Case B harness branch — other:** place a stub `claude` script ahead of the real binary on `PATH` (e.g. `#!/bin/sh\necho "Usage: claude [options]"\n exit 0`) whose `--help` output does not contain `--bg` → prose suggestion emitted, no `claude --bg` in output. Remove the stub after the check. Verifies: AC parallel offer (fallback branch).
- **Case C:** `active = []`, `queue = []`, `shaping_queue.active = []` → exactly 1 numbered choice (start new work). Verifies: "Start new work" always present, section always present.
- **Case D (all blocked):** `active = []`, `queue = [{path="spec/alpha", needs="work:spec/beta"}]` (beta not in shipped) → no graph, Choice 2 omitted, no parallel offer. Verifies: AC graph absent when <2 unblocked, AC Choice 2 omitted when none.
- Preamble check: `grep "Using Step 2 DAG state only" packs/core/.apm/skills/workspace-status/SKILL.md` returns a hit in Step 6. Verifies: AC no-re-read preamble.
- No re-read check: Step 6 prose in the `.apm` source contains no instruction to open or parse `workspace.toml`. Verifies: AC no re-read.
- Trigger list unchanged: `grep "what's next" packs/core/.apm/skills/workspace-status/SKILL.md` returns a hit in the frontmatter description; `grep "what should I work on" packs/core/.apm/skills/workspace-status/SKILL.md` returns a hit in the frontmatter description. Verifies: AC frontmatter unchanged.
- Insertion point: `### 6. Next-actions` appears before `## See also` in the `.apm` source. Verifies: correct procedure nesting.

**Approach:**
1. Read `packs/core/.apm/skills/workspace-status/SKILL.md` (the source; never edit the projected `.claude/` or `.agents/` copies directly).
2. Insert `### 6. Next-actions` section between `### 5. Missing fields` and `## See also`.
3. Open with: `Using Step 2 DAG state only — do not re-read workspace.toml:`
4. **6a — Choice derivation:** define active_spec, next_queue (first unblocked, queue order), unblocked list, next_shape (active shaping first; else first ready unblocked shaping entry).
5. **6b — Graph:** if `len(unblocked) ≥ 2`, emit ASCII graph with `[ready]`/`[blocked by <slug>]` annotations; right-pad slug column.
6. **6c — Harness detection + parallel offer:** if graph was emitted, check whether `--bg` appears in `claude --help` output; emit numbered spawn choice (Claude Code) or prose (all others).
7. **6d — Numbered choices:** parallel offer (if any) → active spec (if any) → next queue item (if any) → first actionable shaping item (if any; "requires <pack>" note when pack absent) → always: start new work (`new-spec` · `new-rfc` · `new-adr` · `queue-add`).
8. Confirm `.apm` source SKILL.md frontmatter description line is unchanged.

**Done when:** manual QA passes Case A-installed, A-absent, B (both harness variants), C, and D; preamble grep returns hit; no-re-read grep clean; `### 6. Next-actions` appears before `## See also` in `.apm` source; both frontmatter trigger-list greps return hits.

### T2: Both projected copies regenerated and byte-identical to source

**Depends on:** T1

**Touches:** `.claude/skills/workspace-status/SKILL.md`, `.agents/skills/workspace-status/SKILL.md`

**Tests:**
- `grep -c "### 6. Next-actions" .claude/skills/workspace-status/SKILL.md` returns `1`.
- `grep -c "### 6. Next-actions" .agents/skills/workspace-status/SKILL.md` returns `1`.
- `diff packs/core/.apm/skills/workspace-status/SKILL.md .claude/skills/workspace-status/SKILL.md` exits 0.
- `diff packs/core/.apm/skills/workspace-status/SKILL.md .agents/skills/workspace-status/SKILL.md` exits 0.

**Approach:**
1. Run `make build-self`.
2. Verify both projected copies updated.
3. Stage `.apm` source and both projected files.

**Done when:** both diffs exit 0 (source equals each projected copy).

## Rollout

Pure skill prose edit; no infrastructure, no flags, no external-system changes. Reversible by reverting the SKILL.md edit and re-running `make build-self`. No data migration.

## Risks

- Harness detection via `claude --help | grep -e '--bg'` may produce false positives if a future version renames the flag. Mitigation: degrading to prose is safe; a false positive at worst emits a non-working command the user can correct.
- The "start new work" choice is always rendered even when the user only wants to continue existing work. Mitigation: it is the last item, one line, low-friction to ignore.

## Deferred

- **Step 3 path bug** (`SKILL.md:62`): pre-existing Step 3 renders `docs/specs/<path>/` with the `spec/` prefix intact (e.g. `docs/specs/spec/foo/`), contradicting Step 6's path-strip instruction. Out of scope for this spec; surfaced for a follow-on fix.

## Changelog

- 2026-07-20: initial plan
- 2026-07-20: fixed harness-detection probe (exit-code → grep `--bg` in help output); clarified parallel offer as numbered choice; added Case D fixture; fixed Step 6 insertion point (before `## See also`, not after); aligned Choice 3 source (active shaping first, then ready); specified pack-absent behavior for Choice 3
- 2026-07-20: fixed graph slug column consistency (both `[ready]` and `[blocked by]` use the bare path with `spec/` preserved); added path-resolution note to Step 6a; marked Status Done
- 2026-07-20: fixed `next_shape` to exclude `type=signal` entries (mirrors Step 3/4 exclusion of signal from actionable items); updated Choice 3 AC wording; clarified manual QA verification as prose-review (no executable artifact)
