# Spec: workspace-status queue reconciliation

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (workspace.toml schema and workspace integrity doctrine)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `workspace-status` skill surfaces every inconsistency between the actual
`Status:` field in a `docs/specs/<slug>/spec.md` file and that spec's position
in `workspace.toml`'s `[work].queue`, `[work].active`, and `[work].shipped`
lists — so a stale or incomplete `workspace.toml` never gives a misleading
"nothing to do" picture.

Three classes of inconsistency are detected and surfaced together in a
**Reconciliation** block that appears before the normal initiative output:

1. **Untracked live spec** — a `spec.md` under `docs/specs/` carries
   `Status: Approved` or `Status: Implementing`, but its canonical path
   (`spec/<slug>`) is absent from every initiative's queue, active, and shipped
   lists. The workspace.toml is incomplete; real work is invisible. The skill
   surfaces the finding and suggests running `queue-add` to add the entry —
   `queue-add` owns the add path.

2. **Stale queue or active entry** — a path in `[work].queue` or `[work].active`
   has a corresponding `spec.md` whose `Status:` is `Shipped` or `Archived`.
   The work is done or cancelled but the entry was never moved out. The skill
   offers to clean this up immediately — moving Shipped entries to
   `[work].shipped` and removing Archived entries — with user confirmation
   before writing. This write path is owned here rather than delegated to
   `queue-add` because `queue-add`'s domain is adding entries, not removing or
   moving existing ones.

3. **Prematurely-shipped entry** — a path in `[work].shipped` has a
   corresponding `spec.md` whose `Status:` is `Approved` or `Implementing`.
   workspace.toml says done; the spec disagrees. No automatic fix is offered —
   the cause may be either a stale spec Status or a wrongly-moved entry; human
   judgement is required.

Note: `work-loop`'s Step 0 stale-queue warning (shipped in `work-loop-queue-
shipped-fix`) also detects `Status: Shipped` entries in queue/active — but only
for the spec currently being worked, during a work-loop session. This
reconciliation check is complementary: it runs at session-start orientation
across all specs and all initiatives, and additionally handles `Status: Archived`
and offers a write-path cleanup. Both detectors are intended to coexist; they
serve different contexts and will not double-report in normal use.

When no inconsistencies are found, the Reconciliation block is omitted entirely
— no noise in a clean workspace.

The user is any agent or developer running `workspace-status` at session start
or mid-session. Success is: stale or missing queue entries are never invisible,
and the user knows exactly what needs attention and how to act.

## Boundaries

### Always do

- Walk every directory under `docs/specs/` that contains a `spec.md` to detect
  untracked live specs (Type 1). Canonical queue key: `spec/<dirname>`.
- Strip the `spec/` prefix from queue/active/shipped entries before constructing
  the spec.md path `docs/specs/<slug>/spec.md` — the resolution rule established
  by `work-loop-queue-shipped-fix`.
- Handle both bare-string queue entries (`"spec/foo"`) and inline-object entries
  (`{path = "spec/foo", needs = "..."}`) by extracting the `path` field.
- Surface the Reconciliation block at the top of the output, before any
  initiative section — warnings must precede the queue data they qualify.
- For stale entries (Type 2), offer to clean up and wait for explicit user
  confirmation before writing. Cleanup: Shipped → move from queue/active to
  `[work].shipped` as a bare string (dropping `needs` and other fields);
  Archived → remove from queue/active entirely. Use a comment-preserving write.
- Check all initiatives in workspace.toml, not just the first.
- Degrade gracefully on a missing spec.md — a path with no corresponding
  spec.md generates no warning (the spec may not exist yet).
- Degrade gracefully on a spec.md with no parseable `- **Status:**` line —
  treat it as having an unknown status and emit no warning for that path.

### Ask first

- Any write to workspace.toml for the stale-entry cleanup. The offer must name
  every entry to change before anything is written.
- Removing a path from `[work].active` — confirm the path is not currently
  being worked on in this session before removing it.

### Never do

- Auto-apply any workspace.toml change without explicit user confirmation.
- Surface an inconsistency for a path with no corresponding spec.md — absence
  of the file is not an inconsistency.
- Offer cleanup for Type 3 (prematurely-shipped) entries — the cause is
  ambiguous; surface the problem and name both possible causes, then stop.
- Add new top-level dependencies, new modules, or any code — prompt-only edit.
- Check specs under directories other than `docs/specs/`.
- Warn about `Status: Draft` specs absent from any list — a Draft spec has not
  yet been approved; it is not expected to appear in workspace.toml.
- Warn about `Status: Archived` specs absent from all lists — an Archived spec
  is cancelled work with no obligation to appear in workspace.toml.

## Testing Strategy

Behaviors fall into two verification modes:

- **Manual QA — output scenarios** (AC1–AC11, AC13): construct a minimal
  workspace.toml and spec.md with the relevant Status, invoke the skill, and
  read the Reconciliation block against the expected content; for mutation
  scenarios (AC8, AC11, AC13), diff the fixture workspace.toml before/after.
  The feature is prompt-only prose in SKILL.md — no compilable artifact to
  stub — matching the precedent of `work-loop-queue-shipped-fix`.
- **Goal-based check** (AC12): `grep -rlnE '^- \*\*Status:\*\* (Approved|Implementing)' docs/specs/*/spec.md`
  after the implementing PR returns only specs present in a workspace.toml
  initiative list. Verifiable by a one-line shell command.

The dogfood run: after the skill edit, invoke `workspace-status` against this
repo's actual `workspace.toml`. The repo currently has several specs with live
Status not tracked in any initiative queue; the Reconciliation block is expected
to surface them as genuine findings. Confirm each finding matches a real
inconsistency. Plan T2 handles pre-dogfood triage of these pre-existing cases.

## Acceptance Criteria

- [ ] **AC1.** Given a `docs/specs/<slug>/spec.md` with `Status: Approved` or
  `Status: Implementing` whose canonical path `spec/<slug>` does not appear in
  any initiative's queue, active, or shipped list, workspace-status surfaces an
  "Untracked live specs" warning naming the spec path and its Status, and
  suggests running `queue-add` or editing `workspace.toml` manually.

- [ ] **AC2.** Given a path in `[work].queue` or `[work].active` whose
  `spec.md` shows `Status: Shipped`, workspace-status surfaces a "Stale
  queue/active entries" warning naming the path, its current list, and the
  spec's Status, and offers to move it to `[work].shipped`.

- [ ] **AC3.** Given a path in `[work].queue` or `[work].active` whose
  `spec.md` shows `Status: Archived`, workspace-status surfaces the same
  "Stale queue/active entries" warning and offers to remove it (not move
  to shipped — Archived means cancelled, not done).

- [ ] **AC4.** Given a path in `[work].shipped` whose `spec.md` shows
  `Status: Approved` or `Status: Implementing`, workspace-status surfaces a
  "Prematurely-shipped entries" warning naming the path, stating that the cause
  is either a stale spec Status or a wrongly-moved workspace.toml entry, and
  making no cleanup offer.

- [ ] **AC5.** Given a path in queue/active/shipped with no corresponding
  `spec.md` file, no warning is emitted for that path. Given a `spec.md`
  that exists but has no parseable `- **Status:**` line, no warning is
  emitted for that path.

- [ ] **AC6.** Given a consistent workspace — all live specs tracked, all
  queue/active entries with non-terminal Status — the Reconciliation block is
  omitted from the output entirely.

- [ ] **AC7.** The Reconciliation block appears before all initiative sections
  when inconsistencies are found. The initiative queue output follows unchanged.

- [ ] **AC8.** When the skill offers to clean up stale entries (AC2, AC3), no
  write to `workspace.toml` occurs unless the user explicitly confirms. The
  offer names each entry to change. When the user declines, `workspace.toml`
  is byte-unchanged.

- [ ] **AC9.** Inline-object queue entries (`{path = "spec/foo", needs = "..."}`)
  are handled correctly: the `path` field is extracted for spec.md lookup and
  for naming in the warning output.

- [ ] **AC10.** The reconciliation check runs across all initiatives in
  `workspace.toml`, not just the first.

- [ ] **AC11.** Cleanup for a stale `Status: Shipped` entry uses a
  comment-preserving write: the entry is moved to the same initiative's
  `[work].shipped` as a bare string (dropping `needs` and other fields),
  without duplicating an entry already present in shipped, and leaving
  surrounding comments, inline objects, and whitespace intact.

- [ ] **AC12.** After the implementing PR merges, every `docs/specs/<slug>/`
  directory whose `spec.md` has `Status: Approved` or `Status: Implementing`
  has its canonical path (`spec/<slug>`) present in at least one initiative's
  queue, active, or shipped list — verified by
  `grep -rlnE '^- \*\*Status:\*\* (Approved|Implementing)' docs/specs/*/spec.md`
  cross-checked against workspace.toml. No "intentional omission" exceptions:
  any live-status spec absent from all lists is an inconsistency that must be
  resolved (stamp, queue, or add to shipped) before this AC is met.

- [ ] **AC13.** Confirmed cleanup for a stale `Status: Archived` entry uses a
  comment-preserving write: the entry is removed from the initiative's
  queue/active list; nothing is added to `[work].shipped`; surrounding comments,
  inline objects, and whitespace are intact.

## Assumptions

- Technical: `workspace-status` is prompt-only; no compiled code is modified
  (source: `.claude/skills/workspace-status/SKILL.md`; workspace.toml queue
  comment "Skill modified: workspace-status").
- Technical: spec.md Status field uses the exact form `- **Status:** Approved`
  etc. (source: CONVENTIONS.md § Spec metadata contract; existing specs).
- Technical: path resolution — strip `spec/` prefix from a queue entry to get
  slug, then look up `docs/specs/<slug>/spec.md` — is established precedent
  (source: `work-loop-queue-shipped-fix/spec.md` lines 38–42).
- Technical: shipped list entries are always bare strings; queue/active may
  contain inline objects with a `path` field (source: workspace.toml schema
  and `work-loop-queue-shipped-fix/spec.md`).
- Technical: `docs/architecture/reference.md` does not exist; stack detection
  not applicable (source: `ls docs/architecture/`).
- Process: dependency `needs = "work:spec/spec-A-workspace-status-rename"` is
  satisfied — spec-A is in shipped (source: workspace.toml).
- Process: `Status: Archived` has no explicit CONVENTIONS workflow; it
  represents cancelled/abandoned work set manually (source: CONVENTIONS.md
  § Spec metadata contract — vocabulary defined, lifecycle path not documented).
- Product: warning placement before initiative sections; cleanup offer for stale
  entries; no offer for prematurely-shipped; warn about all inconsistency types
  (source: user confirmation 2026-07-20).
