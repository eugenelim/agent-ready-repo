# Plan: work-loop queue-to-shipped fix

**Trio:**
- Files touched: `packs/core/.apm/skills/work-loop/SKILL.md` (source), two projections, `workspace.toml`, this spec
- Done when: updated prose handles all cases A–L2 in the spec without ambiguity; three SKILL.md copies are byte-identical; `adversarial-reviewer` returns Clean
- Not changing: workspace-status skill, `spec/workspace-status-queue-reconciliation` queue entry, pack version numbers

**Declined:**
- Tempted to add "surface next queue item" to Step 0 — declining; done-step fix makes this a UX nice-to-have, not a correctness fix, and it duplicates workspace-status output.
- Tempted to make Fix 2 a hard halt — declining; Step 0 is a non-blocking orientation step by contract; halting on a previous session's stale drift would gate unrelated work and is a heavier imposition than a contained diff edit.
- Tempted to auto-move stale entries in Fix 2 — declining; auto-mutating workspace.toml in Step 0 contaminates the current session's PR diff with an out-of-scope edit.
- Tempted to treat Archived as Shipped-equivalent — declining; Archived can mean abandoned/withdrawn and mislabels incomplete work.
- Tempted to also fix workspace-status in the same PR — declining; separate skill, separate scope.

---

## Task 1 — Fix done-step in pack source (Fix 1)

**Depends on:** none
**Verification mode:** manual QA

**Tests:** read the revised done-step bullet against Cases A, B, C, D, G, J, K.
- Case A: path in queue (not active) → moved to shipped ✓
- Case B: path in active → moved to shipped (unchanged) ✓
- Case C/D/J: path in neither → skip, no edit ✓
- Case G: path in active AND queue → active checked first, moved from active ✓
- Case K: this spec's own path is in queue (added by Task 4a) → Fix 1 moves it to shipped and stages the edit in this PR's diff ✓

**Approach:** in `packs/core/.apm/skills/work-loop/SKILL.md`, replace the
done-step bullet beginning "If `workspace.toml` is present…" (~line 814).

Replace:
```
  - **If `workspace.toml` is present** in the working directory and
    `["<slug>".work].active` contains the current spec's path, edit
    `workspace.toml` in the working directory: move that path from
    `["<slug>".work].active` to `["<slug>".work].shipped`, and stage the
    file as part of the shipping PR diff. Use a comment-preserving edit
    (targeted insertion or `tomlkit` if available; never a full `tomllib` +
    `tomli_w` round-trip that strips comments). If `workspace.toml` is
    absent, skip this step — no edit, no error.
```

With:
```
  - **If `workspace.toml` is present** in the working directory, search each
    active initiative's `["<slug>".work].active` and `["<slug>".work].queue`
    for the current spec's path (check `active` before `queue` in each
    initiative; stop at the first match). Each `[work]` entry is either a bare
    string or an inline object with a `path` field (`slug` is a shaping-queue
    field only and never appears in `[work]`). If found, edit `workspace.toml`:
    move that path to `["<slug>".work].shipped` as a bare string (dropping
    `needs` and any other fields from an object entry), and stage the file as
    part of the shipping PR diff. Use a comment-preserving edit (targeted
    insertion or `tomlkit` if available; never a full `tomllib` + `tomli_w`
    round-trip that strips comments). If the path is in no initiative's lists,
    or if `workspace.toml` is absent, skip this step — no edit, no error.
```

**Bundled fix (same file, same concern):** line 177 reads `read docs/specs/<path>/spec.md` where `<path>` is the stored active-spec value in the form `spec/<slug>` — producing a non-existent `docs/specs/spec/<slug>/spec.md` path. Fix it to: strip the `spec/` prefix from the stored path to get `<slug>`, then read `docs/specs/<slug>/spec.md`. Instruction to add inline: "(strip the leading `spec/` from the stored path to get the slug)".

**Done when:** diff shows the done-step bullet change, the line-177 bundled fix, and nothing else.

---

## Task 2 — Add Step 0 stale-queue warning in pack source (Fix 2)

**Depends on:** Task 1 (both tasks edit the same file; must be sequential to avoid a parallel-dispatch collision on `packs/core/.apm/skills/work-loop/SKILL.md`)
**Verification mode:** manual QA

**Tests:** read the reconciliation prose against Cases E, F, G (dangling queue), H, I.
- Case E (stale queue from previous session): warning emitted, PLAN proceeds ✓
- Case F (stale active from previous session): warning emitted, PLAN proceeds ✓
- Case G (dangling queue entry left by Fix 1): flagged as stale on next session, PLAN proceeds ✓
- Case H (no spec.md): silently skipped ✓
- Case I (Status: Implementing): silently skipped ✓
- Non-blocking confirmed: warning appears in orientation output, then PLAN begins normally ✓

**Approach:** in `packs/core/.apm/skills/work-loop/SKILL.md`, inside the
"If present" branch of Step 0 (the indented bullet block at ~lines 160–168),
add the following as the last bullet in that block, after the Active spec line.
The stale-check iterates every active initiative (matching the Step 0 multi-
initiative note at `SKILL.md:172-174`):

```
     - **Stale-queue check.** For each active initiative, for each entry in
       `["<slug>".work].queue` and `["<slug>".work].active`: resolve the entry's
       path (bare string, or the `path` field of an inline object — `slug` is a
       shaping-queue field only, never in `[work]`), then
       strip its `spec/` prefix to get the slug and look up
       `docs/specs/<slug>/spec.md`. If that file exists and its `**Status:**`
       value is `Shipped` (ignoring any trailing `<!-- ... -->` comment), surface
       a warning (then continue — this check is non-blocking):
       > Warning: workspace.toml drift: `<path>` is in `<queue|active>` but
       > spec.md shows Status: Shipped — move it to shipped in workspace.toml
       > before starting work.
       If a path appears in both lists, surface it once and name both. If
       `spec.md` is absent or Status is anything other than `Shipped`, skip
       silently.
```

This bullet sits inside the "If present" conditional, so it only runs when
`workspace.toml` exists — matching the surrounding block's guard.

**Done when:** prose handles all cases; the new bullet is inside the "If
present" indented block and not at the outer numbered-item level.

---

## Task 3 — Sync projections (byte-identity)

**Depends on:** Task 2 (pack source must be fully edited before projecting)
**Verification mode:** goal-based

```bash
diff packs/core/.apm/skills/work-loop/SKILL.md .claude/skills/work-loop/SKILL.md
diff packs/core/.apm/skills/work-loop/SKILL.md .agents/skills/work-loop/SKILL.md
# both silent (exit 0)
```

**Done when:** both diffs exit 0.

**Approach:** run `make build-self` (the canonical projection command; add `FORCE=1` if the tree is dirty). Do not hand-copy bytes — `make build-self` is the sanctioned mechanism and will catch any normalization the projection applies beyond verbatim copy.

---

## Task 4a — Add this spec to workspace.toml queue

**Depends on:** none
**Verification mode:** goal-based

Add `"spec/work-loop-queue-shipped-fix"` to `["ini-002".work].queue`. This is
self-validation (Case K): Fix 1 will find this entry and move it to `shipped`
as part of the done-step at ship time, staging the move in this PR's diff.

**Done when:**
```bash
grep "work-loop-queue-shipped-fix" workspace.toml
# shows the entry in the queue array
```

---

## Task 4b — Done-step fires in-session at ship time

**Depends on:** Tasks 1, 3, 4a (done-step needs the updated skill projected and the spec in queue)
**Verification mode:** goal-based

When this PR is ready to ship, the done-step runs in-session and stages four
changes as part of this PR's diff (all atomic):
1. Moves `spec/work-loop-queue-shipped-fix` from `queue → shipped` in workspace.toml.
2. Flips `- **Status:** Implementing` → `- **Status:** Shipped` in this spec file.
3. Marks all ACs `- [x]` in this spec file.
4. Adds a one-line entry to `docs/product/roadmap.md` per the done-step roadmap reminder.

No automation post-merge, no manual edit. Leaving any one undone is a doc-drift
invariant violation.

**Done when:** final `workspace.toml` has `spec/work-loop-queue-shipped-fix` in
`shipped` and absent from `queue`. The add-to-queue (Task 4a) and the done-step
move land as separate commits; the aggregate diff from `main` shows the entry
only in `shipped`.
