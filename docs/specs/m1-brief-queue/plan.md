# Plan: m1-brief-queue

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three independent tasks: template seed edit, skill prose extension, new skill
authoring. Each is a self-contained file change in `packs/core/`; none touches
executable code. The dependency order is T1 → T2, T3 (T2 and T3 can run in
parallel once T1 is done, since they edit different files). All changes run
through `make build-self` before gates, because the seed and skill files must
project cleanly to the adopter paths.

The riskiest part is `author-brief`'s elicitation design (T3) — the
skill must correctly identify which DoR fields the input already satisfies and
ask only for what is missing, without rejecting partial input. The worked-example
approach (T3 includes a brief example call in the skill body) is the mitigation.
The workspace-write degrade (both T2 and T3) is mechanically simple: a
`workspace.toml`-present check before the TOML edit, with a one-line diagnostic
when absent.

## Constraints

- RFC-0064 (Draft, 2026-07-18): Batch 4 ACs define the three deliverables;
  the DoR gate (D6: Outcome + Appetite + ≥1 Rabbit hole + Spec map skeleton);
  and the write protocol (in-working-directory, staged as part of the spec PR).
- `workspace.toml` schema is sealed by Batch 2; Batch 4 writes to it, not
  redefines it (`brief_queue.draft / ready / executing` keys are the only write
  targets).
- `receive-brief` is a projected skill — edit source at
  `packs/core/.apm/skills/receive-brief/SKILL.md`; run `make build-self`.
- Brief template is a projected seed — edit source at
  `packs/core/seeds/docs/product/briefs/_template.md`; run `make build-self`.

## Construction tests

**Integration tests:** none beyond per-task tests — the three tasks touch
disjoint files.

**Manual verification (end-to-end brief queue flow):**

1. With `workspace.toml` present (INI-002 `brief_queue.draft` seeded with a
   test path), invoke `author-brief` with a raw email body as input; verify the
   skill elicits Outcome + Appetite + Rabbit holes; verify the brief file is
   created at `docs/product/briefs/<slug>.md`; verify the path appears as a
   string element in `[brief_queue].draft` in `workspace.toml`; verify the
   seed's TOML comments are intact after the write.
2. Run `receive-brief` on that brief; verify it performs decomposition, sets
   `Status: Ready` in the brief file's frontmatter, and moves the path from
   `draft` to `ready` in `workspace.toml`; verify comments are intact.
3. Run `check-workspace`; verify the brief surfaces as ready to pick up.
4. Repeat steps 1–2 with `workspace.toml` absent; verify both skills complete
   without error and log the named degrade diagnostic.

## Design (LLD)

### Design decisions

- **New fields are additive-only** — appended to the brief template after existing
  fields; no existing field is moved, renamed, or removed. Traces to: AC1, AC2.
- **`Status:` is a header field, not a section** — sibling to `Received:` and
  `Owner:` in the header block, set by hand. The Spec map's Status column is
  auto-derived (different field, different level). Traces to: AC1.
- **`author-brief` stops at draft** — it does not run `receive-brief`'s
  decomposition and does not set `Status: Ready`. The two skills have distinct
  entry points; conflating them would make `author-brief` a superset of
  `receive-brief` (scope creep) and break the single-responsibility contract.
  Traces to: AC11, AC12.
- **Write protocol: in-working-directory edit, staged in the same PR** — per
  RFC-0064's resolved write-protocol Known Unknown. No worktree, no cross-branch
  write. Skills document this as a note. Traces to: AC4 (receive-brief write),
  AC8 (author-brief write).
- **Comment-preserving TOML writes** — `workspace.toml` is comment-heavy; a
  `tomllib` + `tomli_w` round-trip would strip all comments. Skills must use
  targeted text insertion or a comment-aware library (e.g. `tomlkit`). Manual
  QA verifies the seed's comments survive the write. Traces to: AC4, AC8.

### Behavior & rules

- **DoR gate for `Ready` (eligibility and enforcement):** Outcome present +
  Appetite present + ≥1 Rabbit hole entry + Spec map has at least one placeholder
  row. Any brief missing one of these is `Draft`, not `Ready`. `receive-brief`
  checks the gate before writing `Status: Ready`; if any gate field is absent,
  it surfaces the gap and asks the user to fill it — it does not silently stamp
  Ready on a non-gate-passing brief. The gate is documented in both skills.
  Traces to: AC4 (enforcement), AC11 (documentation in both skills).
- **`receive-brief` workspace write sequence:** (1) confirm decomposition with
  user; (2) check DoR gate — surface any missing fields and pause if any are
  absent; (3) set `Status: Ready` in brief file frontmatter; (4) search all
  active initiatives' `brief_queue.draft` lists for the brief path and move it
  to the matching initiative's `brief_queue.ready` list using a
  comment-preserving edit; if not found in any `draft` list, set Status only
  and log; (5) stage both files. Order matters: the brief's own status is
  updated before the queue pointer moves.
- **`author-brief` workspace write sequence:** (1) elicit missing DoR fields;
  (2) check for slug collision — prompt if `docs/product/briefs/<slug>.md`
  exists; (3) create brief file with `Status: Draft`; (4) check `workspace.toml`
  — degrade if absent/unparseable/no-active-initiative/no-`brief_queue`; if
  multiple active initiatives, prompt user to select target; (5) append the
  brief's path as a string element into `["<slug>".brief_queue].draft` using a
  comment-preserving edit; (6) stage both files.
- **Degrade trigger (both skills):** degrade on: (a) absent file, (b) present
  but unparseable, (c) parseable but no active initiative, (d) parseable but
  active initiative has no `brief_queue` sub-table. All four cases: log named
  diagnostic, continue with file-only operation, no error thrown. Never use
  `tomllib.loads()` to decide degrade for the absent case; a path-existence check
  suffices; a caught parse exception handles unparseable; a key-missing check
  handles the no-brief_queue case.

### Failure, edge cases & resilience

- **`workspace.toml` absent, unparseable, no active initiative, or active
  initiative has no `brief_queue` sub-table (both skills):** degrade to
  file-only operation; log a named diagnostic and a one-line instruction:
  for `author-brief`, instruct the user to add the path as a string element
  to `["<initiative-slug>".brief_queue].draft` (e.g. append
  `"docs/product/briefs/<slug>.md"` to the list); no error thrown. Traces to:
  AC5 (receive-brief degrade), AC10 (author-brief degrade).
- **Brief path already in `ready` (receive-brief):** idempotent — if the path
  is already in `ready`, do not duplicate it; log "already ready, no TOML
  change." Traces to: AC4.
- **Brief path in both `draft` and `ready` (receive-brief):** dedupe — remove
  from `draft`, ensure exactly one entry in `ready`; log the inconsistency.
  Traces to: AC4.
- **Brief path not found in `draft` (receive-brief):** brief may have been
  authored manually (no `author-brief`). In this case, only set `Status: Ready`
  in the brief file; skip the TOML move and log that the path was not in
  `draft` (do not error). Traces to: AC4.
- **Slug collision (`author-brief`):** if `docs/product/briefs/<slug>.md`
  already exists, prompt the user before overwriting; never silently clobber an
  existing brief. Traces to: AC9.
- **Multiple active initiatives (`author-brief`):** if `workspace.toml` has more
  than one section with `status = "active"`, prompt the user to select which
  initiative's `brief_queue.draft` list the new brief joins. Traces to: AC8.
- **`author-brief` with partial input that already satisfies some DoR fields:**
  skill detects which fields are present in the provided input and elicits only
  the missing ones. Traces to: AC7.

## Tasks

### T1: Add DoR fields to brief template seed and project

**Depends on:** none

**Tests:**
- Goal-based: after `make build-self`, the four new fields (`Status:`, `Rabbit
  holes`, `Instrumentation`, `## Design artifacts`) are present in the projected
  seed at the adopter path.
- Goal-based: an existing brief file without the new fields passes all relevant
  lints (no new required-field error).
- Goal-based: `make build-check` exits 0 after the seed edit + build-self.

**Approach:**
- Edit `packs/core/seeds/docs/product/briefs/_template.md`:
  - Add `- **Status:** Draft <!-- Draft | Ready | Executing | Shipped -->` as a
    header field, after `Owner:` and before `Epic:`.
  - Add a `## Rabbit holes` section (after `## Appetite`, before `## User stories`)
    with a comment explaining: design traps and known uncertainties to skip;
    ≥1 entry required for the DoR gate.
  - Add an `## Instrumentation` section (after `## Rabbit holes`) with a comment
    explaining: the telemetry, events, or dashboards used to *measure* whether
    the outcome landed — distinct from Success metrics (which state the *target*
    value; Instrumentation names the *measurement mechanism*).
  - Add a `## Design artifacts` section (at the end, after `## Spec map`) with
    a comment explaining: links to upstream shaping artifacts (journey maps,
    screen flows, capability maps, opportunity assessments) that informed this
    brief.
  - Update the template header comment to mention the new fields.
- Run `make build-self`.
- Verify the projected seed matches the source.

**Done when:** `make build-self` and `make build-check` exit 0; the four new
fields are present in the projected template; an existing brief without them
passes all lints.

### T2: Extend `receive-brief` with `Status: Ready` write and workspace move

**Depends on:** T1

**Tests:**
- Goal-based: the skill SKILL.md source contains documentation of the
  workspace-write step (the two sub-steps: Status field write + TOML path move).
- Goal-based: the degrade path is documented in the skill body.
- Manual QA: run the skill on a brief that passes the DoR gate (Outcome +
  Appetite + ≥1 Rabbit hole + Spec map skeleton); confirm `Status: Ready`
  appears in the brief frontmatter and the path has moved from `draft` to
  `ready`; confirm the seed's TOML comments are intact after the write.
- Manual QA: run the skill on a brief that is missing one DoR gate field
  (e.g. no Rabbit holes); confirm the skill surfaces the gap and waits for
  the user to fill it before stamping `Ready`.
- Manual QA: run the skill with `workspace.toml` absent; confirm decomposition
  completes without error and the degrade diagnostic is emitted.
- Manual QA: run the skill when the brief path is in both `draft` and `ready`;
  confirm the path is removed from `draft` and exactly one entry remains in
  `ready` (dedupe check).

**Approach:**
- Edit `packs/core/.apm/skills/receive-brief/SKILL.md`:
  - In the `### 3. Execute` section (or as a new `### 4. Write back` section
    after Execute), add a workspace-write step that documents:
    1. Check the DoR gate against the brief (Outcome + Appetite + ≥1 Rabbit hole
       + Spec map skeleton). If any gate field is absent, surface the gap and ask
       the user to fill it before proceeding — do not stamp `Ready` on a brief
       that does not pass the gate.
    2. Set `Status: Ready` in the brief file's frontmatter (heading block; add
       the field if absent using value `Ready`).
    3. Move the brief's path from `[brief_queue].draft` to `[brief_queue].ready`
       in `workspace.toml` using a comment-preserving edit (see Design decisions).
       Cases: path in `draft` only → move to `ready`; path in both `draft` and
       `ready` → remove from `draft`, leave the single `ready` entry (dedupe);
       path in `ready` only → no-op, log "already ready"; path not found in either
       → set Status field only, log that path was not in `draft`.
    4. Stage both files.
    5. Degrade if `workspace.toml` is absent, unparseable, or has no `brief_queue`
       sub-table: skip the TOML edit; complete Status write in the brief file only;
       log named diagnostic.
  - Update the skill's `## When to invoke` or `## Anti-patterns` to note that
    `author-brief` is the entry point for unstructured external input (different
    skill, different entry point).
  - Add a note on the DoR gate: what makes a brief `Ready` (Outcome + Appetite +
    ≥1 Rabbit hole + Spec map skeleton).
- Run `make build-self`.

**Done when:** `make build-self` and `tools/lint-skill-spec.py` on the skill
both exit 0; `make build-check` is green; manual QA passes (see above).

### T3: Author `author-brief` skill

**Depends on:** T1

**Tests:**
- Goal-based: `packs/core/.apm/skills/author-brief/SKILL.md` exists with valid
  frontmatter (name, description fields); `tools/lint-skill-spec.py` exits 0.
- Goal-based: after `make build-self`, the skill is present at
  `.claude/skills/author-brief/SKILL.md`; `make build-check` is green.
- Manual QA: invoke `author-brief` with a raw email body as input; verify the
  skill identifies the DoR fields present in the input and elicits only the
  missing ones; verify the brief file is created at `docs/product/briefs/<slug>.md`.
- Manual QA: verify the brief path is written into `[brief_queue].draft` in
  `workspace.toml` (with `workspace.toml` present).
- Manual QA: invoke with `workspace.toml` absent; verify the brief file is
  created and the degrade note is emitted; no error.
- Manual QA: verify the skill explicitly names `receive-brief` as the next step
  after authoring (per AC12).
- Manual QA: invoke with a slug that matches an existing brief file; verify the
  skill prompts before proceeding (slug collision guard).
- Manual QA: invoke with `workspace.toml` containing two active initiatives;
  verify the skill prompts for initiative selection before writing.

**Approach:**
- Create `packs/core/.apm/skills/author-brief/SKILL.md` with:
  - **Frontmatter:**
    ```yaml
    name: author-brief
    description: Use this skill when the user has unstructured external input
      (an email, a prose description, a Linear Issue, a stakeholder message) and
      needs to produce a DoR-compliant product brief and queue it in workspace.toml.
      Triggers on "author a brief", "write a brief from this email", "create a brief
      from this Linear issue", "intake this brief", "turn this into a brief". Do NOT
      use to decompose an existing brief into specs (use receive-brief) or to author
      a single feature from scratch (use new-spec).
    ```
  - **`## When to invoke`**: entry point for unstructured external input; distinct
    from `receive-brief` (which decomposes); distinct from `new-spec` (which
    authors a single spec directly). If the input is already a well-formed brief
    file, go directly to `receive-brief`.
  - **`## Procedure`** with these steps:
    1. **Ingest** — accept whatever the user provides: pasted email, prose, issue
       text, or a link. Do not reject partial or messy input.
    2. **Identify** — scan the input for DoR fields already present (Outcome,
       Appetite, Rabbit holes). Name what was found and what is missing.
    3. **Elicit** — ask for each missing DoR field conversationally; offer a
       default where one is derivable from context ("no Appetite stated — shall
       I default to 'a few weeks, not a quarter'?"). Insist on Outcome; offer the
       rest. ≥1 Rabbit hole is required for the DoR gate; surface this gap if
       the input contains none.
    4. **Create** — confirm the slug; check for an existing file at
       `docs/product/briefs/<slug>.md` — if it exists, prompt before overwriting
       (do not silently clobber). Write the brief file using the updated template;
       set `Status: Draft`; populate all fields gathered in steps 1–3; leave a
       Spec map placeholder row.
    5. **Queue** — if `workspace.toml` is present and parseable: if multiple
       `status = "active"` initiative sections exist, prompt for target initiative;
       append the brief's path as a string list element to
       `["<initiative-slug>".brief_queue].draft` using a comment-preserving edit;
       stage the file. Degrade if `workspace.toml` is absent or unparseable:
       create the brief file only; log named diagnostic with instruction to add
       the path as a string element to `["<initiative-slug>".brief_queue].draft`
       (e.g. `"docs/product/briefs/<slug>.md"` appended to the list).
    6. **Hand off** — tell the user: "Brief is queued as draft. Run `receive-brief`
       to decompose it into specs and mark it ready."
  - **`## DoR gate`** — document the gate as an *eligibility condition*: Outcome +
    Appetite + ≥1 Rabbit hole + Spec map skeleton. A brief exits `author-brief`
    as `Draft` even when all four fields are populated; only `receive-brief`'s
    write-back step sets `Status: Ready` after decomposition is confirmed.
  - **`## Anti-patterns to refuse`** — do not run decomposition (that is
    `receive-brief`); do not set `Status: Ready` (that is `receive-brief`'s
    write-back step); do not invent a Slug the user did not confirm; do not
    fabricate missing DoR fields; do not silently overwrite an existing brief
    file; do not guess the target initiative when multiple active ones exist.
- Run `make build-self`.

**Done when:** `tools/lint-skill-spec.py` exits 0; `make build-self` and
`make build-check` exit 0; `author-brief` is projected to `.claude/skills/`; all
manual QA passes (see above).

## Rollout

Pure skill-prose and seed changes. No database, no migration, no flag, no
infrastructure. `make build-self` projects to all installed adopters on their
next `agentbundle upgrade` or fresh `agentbundle install`. Rollback is a revert
of the `packs/core/` source files + `make build-self`.

## Risks

- **Elicitation design quality (T3)**: `author-brief`'s quality depends on
  whether the skill prose correctly describes how to detect already-present DoR
  fields and elicit only the missing ones. Mitigation: the worked-example
  approach (clear `## Procedure` + `## Anti-patterns`) makes the intent
  observable; manual QA is the gate.
- **`receive-brief` TOML write idempotency (T2)**: if a brief path is already in
  `ready` and `receive-brief` runs again, a naive append duplicates it. The
  "check-before-move" and "dedupe" rules in the design are the mitigation; they
  must be documented in the skill body.
- **Comment-preserving TOML write (T2, T3)**: `workspace.toml` is comment-heavy.
  A round-trip through `tomllib` + `tomli_w` strips all comments. Skills must
  use targeted text insertion or `tomlkit`; the manual QA comment-survival check
  is the gate. If `tomlkit` is not available in the harness, targeted string
  insertion is the fallback (sufficient for simple list-append operations).

## Changelog

- 2026-07-18: initial plan
