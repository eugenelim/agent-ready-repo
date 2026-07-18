# Spec: m1-brief-queue

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no machine interface; the brief file and skill are document/prose artifacts -->
- **Shape:** integration <!-- wiring existing skill infrastructure to the workspace.toml coordination artifact; all changes are skill-prose and seed template edits, no application LLD -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who receives an externally-authored multi-feature brief today has no
structured path from raw external input (an email, a Linear Issue, a prose
description) to a queued, workspace-visible brief — and a brief that passes
decomposition today does not automatically surface in `check-workspace` as
ready to pick up. This spec wires the `brief_queue` end-to-end, closing both
gaps with three targeted changes.

First, the **brief template** gains four Definition-of-Ready (DoR) fields —
`Status`, `Rabbit holes`, `Instrumentation`, and a `## Design artifacts` section
— so a brief carries the full information a team needs to assess readiness before
decomposition begins. Existing briefs are grandfathered: the new fields are
optional retroactively, and `receive-brief` handles both the new shape and the
old one without any break.

Second, **`receive-brief`** is extended to write back to the workspace after
decomposition: it sets `Status: Ready` in the brief file's frontmatter and moves
the brief path from `[brief_queue].draft` to `[brief_queue].ready` in
`workspace.toml`. If `workspace.toml` is absent the skill degrades silently to
its previous behaviour — decomposition proceeds unchanged.

Third, a new **`author-brief`** skill takes any unstructured external input
(email thread, prose description, Linear Issue text, stakeholder message) and
guides the user through the DoR fields conversationally, producing a compliant
brief file and writing its path into `[brief_queue].draft` in `workspace.toml`
so `check-workspace` can surface it immediately. If `workspace.toml` is absent,
`author-brief` creates the brief file and notes the missing registration.

Success: any external input source becomes a queued, workspace-visible brief in
one skill invocation; briefs that pass decomposition surface as ready in
`check-workspace` without manual TOML edits; and `work-loop` (Batch 3) can
claim the next ready brief without human bookkeeping.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the brief template **source** at `packs/core/seeds/docs/product/briefs/_template.md`;
  run `make build-self` after to project the updated seed to adopters. Never
  edit the projected copy directly.
- Edit the `receive-brief` skill **source** at
  `packs/core/.apm/skills/receive-brief/SKILL.md`; run `make build-self` after.
- Place the new `author-brief` skill at
  `packs/core/.apm/skills/author-brief/SKILL.md` with valid frontmatter that
  passes `tools/lint-skill-spec.py`.
- Treat all new brief template fields as **additive and optional retroactively** —
  existing briefs without `Status`, `Rabbit holes`, `Instrumentation`, or
  `## Design artifacts` remain valid; `receive-brief` handles both shapes.
- Degrade gracefully in both skills: if `workspace.toml` is absent, `receive-brief`
  runs decomposition-only (its previous behaviour); `author-brief` creates the
  brief file and logs that the `workspace.toml` registration was skipped.
- Write `workspace.toml` **in the working directory** (not via git cross-branch
  write) and stage it as part of the same diff. The file on `main` is edited in
  place per the RFC-0064 write protocol.
- Use **comment-preserving edits** when writing to `workspace.toml` — targeted
  text insertion or a comment-aware TOML library (e.g. `tomlkit`); never a
  full `tomllib.loads()` + `tomli_w.dumps()` round-trip that strips comments.
  Verify after each write that the seed's comments are intact.
- Run `make build-self` then `make build-check` and `python tools/lint-skill-spec.py`
  against both skill files before declaring done.

### Ask first

- Any change to the DoR gate definition (what fields are required for a brief to
  qualify as `Ready`) beyond what RFC-0064 D6 specifies: Outcome + Appetite +
  ≥1 Rabbit hole + Spec map skeleton.
- Any change to the `workspace.toml` `brief_queue` sub-table schema (adding,
  removing, or renaming keys) — the schema is sealed by Batch 2; Batch 4 writes
  to it, not redefines it.
- Expanding `author-brief` to also run decomposition (that is `receive-brief`'s
  job; the two skills have distinct entry points and must stay distinct).

### Never do

- **Never** modify `workspace.toml`'s schema — the `["<slug>".brief_queue]`
  sub-table with `executing / ready / draft` keys is defined by Batch 2; Batch
  4 writes to it unchanged.
- **Never** auto-advance a brief from `ready → executing` — that transition
  belongs to `work-loop` (Batch 3), not to any skill in this batch.
- **Never** add a new top-level directory or a cross-pack import — `author-brief`
  and the extended `receive-brief` live entirely within `packs/core/.apm/skills/`;
  the brief template is a seed in `packs/core/seeds/`.
- **Never** write execution state into `workspace.toml` — it records declared
  intent only; the platform owns execution state.
- **Never** hand-maintain the brief's coverage map (`Spec map`) or set its `Status`
  column by hand — coverage rollup is the lint's job, not Batch 4's job.
- **Never** make the `workspace.toml` write blocking: both skills degrade
  gracefully when the file is absent **or unparseable**; a missing or malformed
  file must never stop skill execution. A present-but-unparseable file degrades
  the same as an absent file — log a named diagnostic and continue with
  file-only operation.
- **Never** silently overwrite an existing brief file — if `docs/product/briefs/<slug>.md`
  already exists, `author-brief` must prompt the user before proceeding (or stop
  and report the collision).

## Testing Strategy

All three deliverables are skill-prose + seed edits — no executable logic that
carries a compressible invariant — so verification is **goal-based** and
**manual QA**, with no TDD.

- **Brief template field additions** — goal-based: verify `Status`, `Rabbit holes`,
  `Instrumentation`, and `## Design artifacts` are present in the seed after
  `make build-self`; verify an existing old-shape brief still passes any relevant
  lint.
- **`receive-brief` extension** — goal-based: verify the skill SKILL.md documents
  the `Status: Ready` write step and the `draft → ready` TOML move; verify the
  degrade path is documented and tested by running the skill against a repo
  without `workspace.toml` (no error, decomposition-only).
- **`receive-brief` workspace write** — manual QA: run the skill on a test brief
  with `workspace.toml` present; confirm the brief path moves from `draft` to
  `ready` and `Status: Ready` appears in the brief file.
- **`author-brief` skill frontmatter / structure** — goal-based: verify the file
  exists at its conventional path; frontmatter passes `tools/lint-skill-spec.py`;
  `make build-self` projects cleanly and `make build-check` is green.
- **`author-brief` elicitation and write behavior** — manual QA: invoke the skill
  with a raw email body as input; verify it elicits missing DoR fields, creates a
  compliant brief file, and writes the path into `[brief_queue].draft` in
  `workspace.toml`. Invoke with `workspace.toml` absent; verify the brief file
  is created and the missing TOML registration is noted, with no error thrown.
- **End-to-end brief queue flow** — manual QA: `author-brief` (raw input → draft),
  then `receive-brief` (decompose → ready); verify `check-workspace` surfaces the
  brief as ready without manual TOML edits.

## Acceptance Criteria

- [ ] **Brief template** at `packs/core/seeds/docs/product/briefs/_template.md`
  gains four new fields:

  1. A **`Status:`** header field (sibling to `Received:` and `Owner:`) with
     valid values `Draft | Ready | Executing | Shipped`; set by hand at DoR
     gate and at ship; distinct from the auto-derived Spec map coverage column.
  2. A **`Rabbit holes:`** section listing design traps, known uncertainties, and
     out-of-bound explorations to skip — ≥1 entry is required by the DoR gate
     for a brief to qualify as `Ready`.
  3. An **`Instrumentation:`** section naming the telemetry, events, or
     dashboards the team will use to measure whether the outcome landed —
     distinct from **Success metrics** (which state the *target*; Instrumentation
     names the *measurement mechanism*).
  4. A **`## Design artifacts`** section (header, not a flat field) linking
     upstream shaping artifacts (journey maps, screen flows, capability maps,
     opportunity assessments) that informed the brief.

- [ ] The new fields are **additive and retroactively optional**: an existing
  brief without them passes `make build-check` and all brief-related lints
  without modification; `receive-brief` handles both the new shape and the old
  shape without error.

- [ ] After `make build-self`, the updated template is projected to the
  conventional adopter path (seeded to `docs/product/briefs/_template.md` in a
  fresh `agentbundle install`); `make build-check` exits 0.

- [ ] **`receive-brief`** skill source at
  `packs/core/.apm/skills/receive-brief/SKILL.md` documents an explicit
  workspace-write step that runs after decomposition is confirmed:

  1. Checks the DoR gate (Outcome + Appetite + ≥1 Rabbit hole + Spec map
     skeleton) against the brief before writing `Status: Ready`. If any gate
     field is absent, `receive-brief` surfaces the gap and asks the user to
     fill it before proceeding — it does not silently stamp `Ready` on a brief
     that does not meet the gate.
  2. Sets `Status: Ready` in the brief file's frontmatter (edits the brief file
     in the working directory and stages it).
  3. Moves the brief's path from `[brief_queue].draft` to `[brief_queue].ready`
     in `workspace.toml` using a comment-preserving edit (edits the file in the
     working directory and stages it). When multiple initiatives are active,
     `receive-brief` searches all active initiatives' `brief_queue.draft` lists
     for the path and moves it within whichever contains it; if found in none,
     it sets `Status: Ready` in the brief file only and logs that the path was
     not found in any `draft` list.

- [ ] **`receive-brief` degrades gracefully** when `workspace.toml` is absent,
  unparseable, or parseable but has no `brief_queue` sub-table for an active
  initiative: the skill proceeds with decomposition only (its previous
  behaviour); no error is thrown; the degrade condition and the named diagnostic
  are documented in the skill body.

- [ ] **`author-brief`** skill ships at `packs/core/.apm/skills/author-brief/SKILL.md`
  with valid frontmatter that passes `tools/lint-skill-spec.py`; after
  `make build-self`, the skill is projected to `.claude/skills/author-brief/SKILL.md`.

- [ ] `author-brief` accepts unstructured external input (email body, prose
  description, Linear Issue text) as its starting material and elicits any
  missing DoR fields — **Outcome**, **Appetite**, and at least **one Rabbit hole**
  — conversationally, never rejecting input for non-conformance (same
  "meet-where-it-is" contract as `receive-brief`).

- [ ] `author-brief` creates a compliant brief file at `docs/product/briefs/<slug>.md`
  — shaped by the updated template — sets `Status: Draft`, and writes the brief's
  path into `[brief_queue].draft` in `workspace.toml` (edits in the working
  directory and stages the file). When `workspace.toml` contains more than one
  active initiative section (`status = "active"`), `author-brief` prompts the
  user to select which initiative's `brief_queue.draft` list the new brief joins;
  it does not guess. When `workspace.toml` is parseable but contains no active
  initiative, or the active initiative has no `brief_queue` sub-table,
  `author-brief` degrades with the same named diagnostic and manual-add
  instruction as the absent/unparseable case.

- [ ] `author-brief` refuses (with a prompt) to create a brief file when
  `docs/product/briefs/<slug>.md` already exists — it does not silently
  overwrite an existing brief.

- [ ] **`author-brief` degrades gracefully** when `workspace.toml` is absent
  or unparseable: the skill creates the brief file; it logs that the
  `workspace.toml` registration was skipped with a named diagnostic and a
  one-line instruction for the user to add the path manually as a list element
  in `[<initiative-slug>.brief_queue].draft`; no error is thrown.

- [ ] The DoR gate is documented in both `author-brief` and the updated
  `receive-brief` as the *eligibility condition* for the `Ready` transition: a
  brief is **eligible for `Ready`** when it carries **Outcome**, **Appetite**,
  **≥1 Rabbit hole**, and a **Spec map skeleton** (at minimum one placeholder
  row). Meeting the gate does **not** automatically set `Status: Ready` — that
  write is performed only by `receive-brief` after decomposition is confirmed.
  A brief that exits `author-brief` — even if all four gate fields are populated —
  is always `Status: Draft`; `receive-brief`'s write-back step is what sets
  `Status: Ready`.

- [ ] `author-brief` does **not** run decomposition and does **not** set
  `Status: Ready` — it creates and queues the brief as `Draft`, stopping before
  the `receive-brief` decompose step. The skill body explicitly names
  `receive-brief` as the next step to take after authoring.

- [ ] `make build-self` runs cleanly; `make build-check`, and
  `python tools/lint-skill-spec.py` on both skill files all exit 0.

## Assumptions

- Technical: Brief template source is `packs/core/seeds/docs/product/briefs/_template.md`;
  current fields are Slug, Received, Owner, Epic, Parent intent, Outcome,
  Success metrics, Scope/Non-goals, Appetite, User stories, Spec map — the four
  new fields are absent today (source: `packs/core/seeds/docs/product/briefs/_template.md`).
- Technical: `receive-brief` skill source is `packs/core/.apm/skills/receive-brief/SKILL.md`;
  no `workspace.toml` write step exists in the current skill body (source:
  `packs/core/.apm/skills/receive-brief/SKILL.md`).
- Technical: No `author-brief` skill exists yet — `ls packs/core/.apm/skills/` lists
  adapt-to-project, bug-fix, check-workspace, contract-acquisition, frontend-engineering,
  init-project, new-spec, operational-safety, receive-brief, security-checklists,
  work-loop — `author-brief` is absent (source: `ls packs/core/.apm/skills/`).
- Technical: `workspace.toml` exists at repo root after Batch 2 ships; the
  `["<initiative-slug>".brief_queue]` sub-table carries `executing`, `ready`,
  `draft` keys per the RFC-0064 schema (source:
  `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § workspace.toml schema).
- Technical: Brief `Status` valid values are `Draft | Ready | Executing | Shipped`;
  DoR "Ready" gate is Outcome + Appetite + ≥1 Rabbit hole + Spec map skeleton
  (source: RFC-0064 D6).
- Process: Constrained by RFC-0064 (Draft); Batch 4 is independent of Batch 3
  and depends on Batch 2 (source:
  `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § M1 delivery batches).
- Technical: Skills project from `packs/core/.apm/skills/` to `.claude/skills/`
  via `make build-self`; new skills require valid frontmatter passing
  `tools/lint-skill-spec.py` (source: existence of `tools/lint-skill-spec.py` +
  `Makefile` `build-check` target).
- Technical: Shape is `integration` — no new executable code, no new module
  boundary; all changes are skill-prose + seed template edits conforming to the
  pattern established by `receive-brief` and `check-workspace` (source:
  RFC-0064 Batch 4 delivery table; pattern confirmed by reading existing skills).
- Technical: Write protocol for `workspace.toml` is in-working-directory edit
  staged as part of the spec PR; no cross-branch write, no worktree (source:
  RFC-0064 Known unknowns, Write protocol § Resolved).
