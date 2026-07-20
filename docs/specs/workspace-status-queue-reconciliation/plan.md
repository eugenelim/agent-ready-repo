# Plan: workspace-status queue reconciliation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One file changes: `.claude/skills/workspace-status/SKILL.md`. A new **Step 2a**
(inserted between the current Step 2 "Resolve the DAG" and Step 3 "Surface
results") runs the reconciliation logic and populates the Reconciliation block.
Step 3 is updated to place that block at the top of the output before any
initiative section.

The reconciliation runs three passes:

1. **Forward scan** (untracked live specs): walk `docs/specs/*/spec.md`, grep
   for `Status: Approved` or `Status: Implementing`, derive the canonical path
   `spec/<dirname>`, and check whether it appears in any initiative's queue,
   active, or shipped list.

2. **Backward scan** (stale queue/active entries): for every path in every
   initiative's queue and active lists, resolve `docs/specs/<slug>/spec.md`
   (stripping the `spec/` prefix), and check its Status field. Flag entries
   where Status is Shipped or Archived.

3. **Shipped scan** (prematurely-shipped): for every path in `[work].shipped`,
   resolve spec.md and check for Status: Approved or Implementing.

The riskiest part is the cleanup offer: the skill must name every entry to
change and must not write until the user confirms. The `queue-add` precedent
(comment-preserving write — targeted text insertion or `tomlkit`) is followed.

Since this is a prompt-only skill, implementation is the prose edit. Gates are
manual QA: construct scenarios, invoke the skill, read output.

## Constraints

- RFC-0064: workspace.toml schema — `[work].queue` contains bare strings or
  `{path, needs}` inline objects; `[work].shipped` contains bare strings only.
- `work-loop-queue-shipped-fix` spec: path resolution rule (strip `spec/`
  prefix) and the precedent for similar stale-detection in work-loop's Step 0.
- `queue-add` spec: comment-preserving write discipline for workspace.toml edits.
- CONVENTIONS.md § Spec metadata contract: Status vocabulary
  `Draft | Approved | Implementing | Shipped | Archived`.

## Construction tests

**Manual verification:**
- After the skill edit, run `workspace-status` against this repo's
  `workspace.toml`. Confirm: (a) the Reconciliation block appears before
  initiative sections; (b) any genuine inconsistencies are correctly surfaced;
  (c) `spec/workspace-status-queue-reconciliation` itself — Status: Approved,
  present in queue — generates no warning.

**Integration tests:** none beyond per-task scenarios.

## Design (LLD)

### Behavior & rules

The reconciliation logic, in prose for a prompt-only skill:

**Path extraction:**
- For a bare-string entry `"spec/foo"`: path = the string.
- For an inline-object entry `{path = "spec/foo", needs = "..."}`: path = the
  `path` field value.
- Canonical slug: strip the `spec/` prefix → slug. Spec file:
  `docs/specs/<slug>/spec.md`.
- Status extraction: read the line matching `- **Status:**` in spec.md and
  extract the first token after the colon (before any comment).

**Three-pass reconciliation table:**

| Check | Input | Flag when | Warning type |
|---|---|---|---|
| Forward scan | spec.md file | Status: Approved or Implementing; `spec/<slug>` absent from all lists | Untracked live spec |
| Backward scan | queue/active entry | spec.md Status: Shipped or Archived | Stale queue/active entry |
| Shipped scan | shipped entry | spec.md Status: Approved or Implementing | Prematurely-shipped |

**Output format (Reconciliation block):**

```
**Reconciliation** — N inconsistenc(y/ies) detected:

  Untracked live specs (Approved or Implementing, not in any list):
  - `spec/<slug>` (Status: Approved) — add to [work].queue or run queue-add

  Stale queue/active entries (spec shows Shipped or Archived):
  - `spec/<slug>` in [ini-002 work].queue — Status: Shipped
  - `spec/<slug>` in [ini-002 work].active — Status: Archived

  Prematurely-shipped entries ([work].shipped, spec shows live status):
  - `spec/<slug>` in [ini-002 work].shipped — Status: Implementing
    Possible causes: (1) spec Status not updated after shipping, or
    (2) workspace.toml entry moved before the work was done.

Stale entries found — offer to clean up now?
  Shipped entries move to [work].shipped (bare string, needs dropped).
  Archived entries are removed from queue/active.
  Reply Y to apply, or edit workspace.toml manually.
```

The `N inconsistenc(y/ies)` count is the total across all three types. When N
is zero the entire block is omitted. Each warning line names the initiative
(`[ini-002 work]`) so multi-initiative repos are unambiguous.

**Cleanup write (Type 2 only, after Y confirmation):**
- Shipped entry in queue: remove from queue, append as bare string to shipped.
- Archived entry in queue: remove from queue. No addition to shipped.
- Same logic for active entries, with the ask-first caveat.
- Use a comment-preserving write — targeted text insertion or `tomlkit`, matching
  the `queue-add` precedent. Never a `tomllib` + `tomli_w` round-trip (strips
  comments). Append to the **same initiative's** `[work].shipped`; dedup before
  appending (skip if the bare path is already present in that shipped list).

Traces to: AC1–AC11, AC13.

## Tasks

### T1: Reconciliation step in workspace-status SKILL.md produces correct output

**Depends on:** T2

**Touches:** `.claude/skills/workspace-status/SKILL.md`

**Tests:**
- Scenario A (AC1): a spec.md with Status: Approved exists, `spec/<slug>`
  absent from all workspace.toml lists → Reconciliation block shows it under
  "Untracked live specs."
- Scenario B (AC2): a path in `[work].queue`, spec.md shows Status: Shipped →
  "Stale queue/active entries" warning; cleanup offer present.
- Scenario C (AC3): a path in `[work].queue`, spec.md shows Status: Archived →
  same section; cleanup offer names the entry as "remove."
- Scenario D (AC4): a path in `[work].shipped`, spec.md shows Status:
  Implementing → "Prematurely-shipped entries" warning; no cleanup offer.
- Scenario E (AC5): path in queue, no spec.md → no warning emitted.
- Scenario F (AC6): all live specs tracked, all queue/active entries with
  non-terminal Status → Reconciliation block absent.
- Scenario G (AC9): inline-object entry `{path = "spec/foo", needs = "..."}` →
  path extracted correctly; warning names `spec/foo`.
- Scenario H (AC10): inconsistency in a second initiative → detected and
  surfaced alongside the first initiative's findings.
- Scenario I (AC11): a `workspace.toml` with a stale inline-object queue entry
  `{path = "spec/foo", needs = "work:spec/bar"}` surrounded by comments, with
  `spec/foo/spec.md` showing `Status: Shipped`; after the user confirms the
  cleanup offer, the resulting workspace.toml retains surrounding comments and
  contains `"spec/foo"` in `[work].shipped` as a bare string.
- Edge: `Status: Draft` spec absent from all lists → no warning (AC boundary).
- Edge: `Status: Archived` spec absent from all lists → no warning (AC boundary).
- Edge: spec.md present but no `- **Status:**` line → no warning (AC5 extension).
- Scenario J (AC8 no-confirm path): stale entry present, cleanup offer displayed,
  user declines — diff fixture workspace.toml before/after and assert
  byte-unchanged.
- Scenario K (ask-first for active entries): a path in `[work].active` has
  `Status: Archived`; the skill surfaces the stale warning and, before offering
  cleanup, prompts the extra confirmation: "Is this path being worked on in this
  session?" — cleanup is not offered until the user confirms it is not active.
- Scenario L (AC7 ordering): construct a fixture workspace.toml with one
  inconsistency (an untracked live spec) and one non-empty initiative queue
  section; invoke workspace-status and assert the Reconciliation block appears
  before the initiative section header, with the initiative output unchanged
  below it.
- Scenario M (AC13 Archived-removal write): construct a fixture workspace.toml
  with a stale `{path = "spec/foo", ...}` entry in `[work].queue` and
  `spec/foo/spec.md` showing `Status: Archived`; after user confirms cleanup,
  diff before/after and assert the entry is removed from queue, nothing is
  added to shipped, and surrounding comments/whitespace are intact.

**Approach:**
1. Read the current `SKILL.md` in full.
2. Insert Step 2a after Step 2 ("Resolve the DAG"). The step describes the
   three-pass reconciliation: forward scan (walk `docs/specs/*/spec.md`),
   backward scan (walk queue/active entries), shipped scan (walk shipped
   entries). Each pass is documented with the path extraction rule, the Status
   grep pattern, and the flag condition.
3. Define the Reconciliation block output format in Step 2a, with the exact
   section headers, per-entry line format (naming initiative and list), and
   the cleanup offer wording.
4. Update Step 3 ("Surface results"): prefix the initiative sections with the
   Reconciliation block if N > 0; omit the block when N = 0.
5. Add cleanup-write procedure under Step 2a: after the user confirms, for
   each stale entry in queue/active, apply the appropriate action (move or
   remove) using a comment-preserving write. State the ask-first rule for
   active entries explicitly.

**Done when:** All thirteen verification scenarios A–M are walkable against the
updated SKILL.md prose, and the manual dogfood run correctly identifies real
inconsistencies in this repo's workspace.toml (the pre-existing untracked-live
specs have been triaged in T2 before this run, so findings reflect genuine gaps
not pre-existing noise).

### T2: Pre-dogfood triage — resolve pre-existing untracked-live specs

**Depends on:** none

**Touches:** `docs/specs/*/spec.md`, `workspace.toml`

**Tests:**
- After triage, `grep -rlnE '^- \*\*Status:\*\* (Approved|Implementing)' docs/specs/*/spec.md`
  returns only specs whose canonical path appears in a workspace.toml
  initiative list (AC12).
- Any spec left with a live status but not yet queued has an explicit signed-off
  reason recorded in the commit message or PR description.

**Approach:**
1. Run `grep -rlnE '^- \*\*Status:\*\* (Approved|Implementing)' docs/specs/*/spec.md`
   to enumerate all live specs.
2. Cross-check each against all initiative queue/active/shipped lists. The repo
   currently has ~6 untracked-live specs (e.g. `apm-install-route-parity`,
   `ast10-pack-compliance`, `catalogue-curation`, `frontend-engineering-skill`,
   `mermaid-rendering-improvements`, `render-proof`). For each, surface the
   finding to the user with a triage question:
   - "Is this shipped? If so, stamp `Status: Shipped` and I'll add it to
     workspace.toml shipped."
   - "Is this abandoned? If so, stamp `Status: Archived`."
   - "Is this legitimately queued but missing from workspace.toml? Run
     `queue-add` or I'll edit manually."
   Each decision requires explicit user confirmation — do not auto-stamp.
3. Apply confirmed lifecycle stamps and workspace.toml edits. For any spec
   stamped `Status: Shipped`, verify its Acceptance Criteria are all checked
   (`[x]`) or marked deferred — per CONVENTIONS.md § 4 metadata contract. If
   ACs are unchecked without a deferral marker, resolve with the user before
   stamping (open a follow-up or add the deferral marker) rather than leaving
   the metadata in violation.
4. Commit separately from the SKILL.md edit so the diff is auditable.

**Done when:** `grep -rlnE '^- \*\*Status:\*\* (Approved|Implementing)' docs/specs/*/spec.md`
returns only specs that are either in a workspace.toml queue/active list or are
newly authored (like this spec itself, which is in the queue).

## Rollout

Prompt-only change to a skill file. No infra, no deployment sequencing.
Reversible by reverting the SKILL.md edit. The change also updates the packed
(projected) copy at `.agents/skills/workspace-status/SKILL.md` via `make
build-self`; that copy is regenerated in the same PR.

## Risks

- **Pre-existing live-untracked specs:** the repo currently has ~6 specs with
  `Status: Approved` or `Status: Implementing` absent from workspace.toml.
  These are real inconsistencies, not false positives — AC12 requires they are
  resolved before the PR merges. T2 triages each with explicit user confirmation:
  stamp Shipped (with AC-checkbox verification), stamp Archived, or add to
  queue. No "intentional omission" path exists — a live-status spec absent from
  all initiative lists will re-fire the Reconciliation block on every subsequent
  session-start; the only clean resolution is to fix the Status or queue it.
- **Large `docs/specs/` directory slowing session start:** walking all
  spec.md files adds a file-read step to every `workspace-status` invocation.
  The repo currently holds ~161 spec directories. For a prompt-only skill
  invoked interactively, reading ~161 short markdown files is acceptable —
  each Status line is near the top of each file. Not a concern unless the
  spec count grows by another order of magnitude.

## Changelog

- 2026-07-20: initial plan
