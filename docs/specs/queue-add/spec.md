# Spec: queue-add — bridge session-surfaced items into the work queue

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (workspace.toml schema, D2–D9), ADR-0054 (skill-naming taxonomy — utility write-skill branch)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service <!-- prompt-only skill that transforms input and writes a file; no UI -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A session frequently surfaces work that should become future specs — work-loop
scope-deferrals, session-audit remediation items, review recommendations,
follow-ons. Today the only way to carry these into a later session is a manual
edit of `workspace.toml`, or a hand-written prompt telling the next session what
to do. Both lose fidelity: the originating session holds context (the problem,
the fix, the affected file, the decisions already taken) that a cold-start
session cannot reconstruct.

`queue-add` is the bridge. Given a bulleted or numbered list of items in the
current session's context, it derives spec paths, infers hard dependencies from
the list's own sequencing language, **prioritizes and logically groups** the
items, and appends them to the active initiative's `[work].queue` in
`workspace.toml` — each entry carrying a comment rich enough that a cold-start
session can write the full spec without revisiting this one. When the items are
well-shaped and ready but not initiative-scale, it routes them instead to the
repo-level `[backlog]` (RFC-0064 amendment 2026-07-20) — the single view of open
work not scoped to an active initiative. For items that do not cleanly fit either
home it runs an escalation rubric and *suggests* the right destination (§
Grouping). It never creates spec files, and it never modifies the
`workspace.toml` schema. The user reviews the full proposed change before
anything is written.

The user is an agent (or the human driving it) at the end of a working session,
holding a list of "things we should do later." Success is: those items land in
the queue, correctly sequenced and grouped, with enough context attached that
the next session picks them up cold and produces the right spec.

## Boundaries

### Always do

- Use a **comment-preserving** write (targeted text insertion, or `tomlkit`) —
  never a `tomllib` + `tomli_w` round-trip. The rich per-entry comments are the
  whole point of the feature; a round-trip strips them.
- Write per-entry comments rich enough for a cold-start session: **problem,
  fix, affected file/skill, and key decisions already taken.** One-liners are
  insufficient (observed: this initiative's own early queue entries had to be
  expanded before a fresh session could act on them).
- Infer `needs` dependencies **only** from explicit sequencing language in the
  list ("after X", "depends on Y", "once Z ships", "then").
- Present the complete proposed change — entries, comments, order, and any
  inferred `needs` — and get user sign-off **before** writing.
- Derive `spec/<slug>` paths in kebab-case from each item's text and confirm
  them with the user.

### Ask first

- **Which initiative** the batch joins, when more than one section has
  `status = "active"`. Never guess.
- **The destination**, when the items are not scoped to an active initiative:
  confirm routing to the repo-level `[backlog]` (the default), or an escalation
  suggestion (`author-brief`, `roadmap-intents.md`, `rfc-candidates.md`, a new
  RFC, or a new initiative). See the escalation rubric in § Grouping.
- **Slug on collision:** if `docs/specs/<slug>/` already exists, or `<slug>` is
  already present in `queue`/`active`, prompt before proceeding.
- **Priority order** among items that no dependency sequences, when there is
  more than one such item — see § Prioritization.
- **Escalation to a brief** when the batch reads as a shaped work unit rather
  than an ad-hoc remediation batch — see § Grouping.

### Never do

- **Create spec files.** This skill writes `workspace.toml` only. Authoring the
  spec is `new-spec`/`work-loop`'s job in a later session.
- **Add a field the schema does not define.** The schema is sealed (RFC-0064
  D2–D4). No `priority`, `rank`, or `group` key on entries — priority is
  expressed as queue order + comment rationale; grouping as a comment header.
- **Fabricate a dependency.** If the list does not sequence two items, they are
  independent; do not invent a `needs`.
- **Encode a priority *preference* as a `needs`.** Only a real "cannot start
  until" becomes a dependency; preference is queue order + comment. A spurious
  `needs` would falsely serialize parallel-safe work.
- **Force-fit orphan items into an ill-matching initiative**, or auto-create an
  initiative. Route to the findings register or suggest a new initiative
  instead.
- **Overwrite** an existing spec directory or brief.
- **Block on a missing/unparseable `workspace.toml`.** Degrade to a named
  diagnostic (see AC7) and continue; never throw.

## Prioritization

The ecosystem has a deliberate, coherent posture that this skill reuses rather
than reinventing:

1. **The `workspace.toml` schema has no priority field, and none is added.**
   Sequencing is expressed structurally via `needs` (a dependency DAG resolved
   by `workspace-status`), and priority-among-ready-items is
   expressed as **queue order plus a one-line rationale in the entry comment**
   — the convention the file already uses ("Reliability before UX:
   reconciliation first, then next-actions").

2. **Three distinct axes, never conflated:**
   - `needs` = a **hard dependency** (sequence) — B cannot start until A ships.
     Inferred only from explicit sequencing language. Machine-resolved into the
     DAG.
   - **absence of `needs` = parallelism.** Parallelism is already first-class in
     this model (RFC-0064 D7: the whole reason `needs` exists is to express
     "these three run in parallel, this one waits for that one");
     `workspace-status` surfaces items with no path between them as **parallel
     candidates**. There is no separate parallel marker and none is added.
   - queue order + comment = **soft priority** — among items that are all
     ready, which a session should prefer first. Human judgement; advisory only.

   The load-bearing discipline: **a priority *preference* must never be encoded
   as a `needs`.** Writing a spurious dependency to force an order would falsely
   serialize parallel-safe work and remove it from the parallel-candidates set.
   Preference lives in queue order + comment; only a real "cannot start until"
   becomes a `needs`. The group comment may annotate a parallel-safe set
   explicitly (e.g. "items 3–5 are parallel-safe; do 1 → 2 first") as advisory,
   human-readable guidance — including a hint that a parallel-safe set could be
   handed to `work-loop` supervisor mode as one batch.

3. **Prioritization is rubric-agnostic by design.** This mirrors the PE pack's
   `decompose-intent` step-5 rank pattern: the skill ships the *step*, not a
   fixed scoring formula. When priority among independent items is a real call,
   `queue-add` **elicits** it — offering the adopter's own rubric (RICE,
   value-vs-effort, Torres opportunity-sizing, or a custom matrix) and recording
   the resulting order with a one-line rationale. It never imposes a formula and
   never writes a numeric score into the file.

4. **When to elicit vs. skip:**
   - Dependencies fully determine the order, or there is one item → **skip**
     elicitation; order follows the DAG.
   - Two or more items are mutually independent → **elicit**: ask the user to
     rank them (offering a rubric as a prompt, not a gate), then record the
     order + rationale.

## Grouping

A batch of related items — e.g. a session audit that produced five remediation
items, some depending on others — needs a *logical home*. This ecosystem
already has the shapes; `queue-add` routes to them rather than inventing a new
grouping primitive.

**The two homes `queue-add` writes to.** `queue-add` appends only to the two
destinations it owns; for everything else it *suggests* and defers the write to
the owning skill:

1. **An active initiative's `[work].queue`** — well-shaped, ready work that is
   scoped to an active initiative. If more than one initiative is active, prompt
   (never guess).
2. **The repo-level `[backlog].open`** — well-shaped, ready work that is *not*
   initiative-scale (RFC-0064 amendment 2026-07-20). This is the home for the
   common ad-hoc case — e.g. five items from an experience audit of the
   marketing + doc site when there is no web-presence initiative. `[backlog]` is
   repo-durable and initiative-agnostic; new discoveries land here.

**Escalation rubric — what to suggest when it doesn't cleanly fit.** The spine is
one question: *is it shaped enough to become a spec now, and at what scale?*

| Item shape | Destination | `queue-add` action |
| --- | --- | --- |
| Well-shaped, ready, fits an active initiative | initiative `[work].queue` | **append** |
| Well-shaped, ready, not initiative-scale | repo-level `[backlog].open` | **append** (default ad-hoc home) |
| Cluster of related features, one outcome + appetite, under an initiative | `brief_queue` via `author-brief` | **suggest** |
| Needs shaping / research / strategy before it is a spec | `shaping_queue` (`shape`/`research`/`strategy`) | **suggest** |
| Deferred AC / follow-up of an existing spec | `[backlog].open` with `source = "spec/<name> ACn"` | **append** (deferral mechanism) |
| Big future feature, not shaped or scheduled | `roadmap-intents.md` (bigger-than-backlog) | **suggest** |
| Cross-cutting design question to work through | `rfc-candidates.md` | **suggest** |
| Cross-cutting proposal needing a decision | new RFC (`new-rfc`) | **suggest** |
| Sustained, multi-quarter effort | new initiative | **suggest** (never auto-create) |

**Grouping once a home is chosen (not an RFC, so what is it?).** Three shapes,
picked by how tightly the items are coupled:

- **Independent batch** (default) — related but separable items land as
  **comment-grouped flat entries** under a single labeled comment header (the
  existing convention — e.g. `# Session audit YYYY-MM-DD — remediation batch`),
  with `needs` encoding real dependencies and, per § Prioritization, a
  parallel-safe annotation where it applies. Each item stays its own entry so it
  can be picked up, sequenced, or parallelized on its own.
- **Atomic bundle** — when two or more items **must ship together** because
  splitting them creates a broken intermediate state (the load-bearing example:
  a shared HARD gate — a migration that removes a lint anchor while another item
  repoints that lint — where a split leaves a dangling-anchor window and red
  CI), `queue-add` records them as a **single queue entry** whose rich comment
  enumerates the coupled parts *and* the coupling hazard (why they cannot be
  split). This is stronger than a `needs` edge: `needs` orders two separately
  shippable items; an atomic bundle says there is no valid state between them.
  The tell is coupling language ("must ship together", "can't split", "would
  dangle/break if separate") or a detected shared HARD-gate hazard.
- **Shaped work unit** — when the batch coheres as one outcome + a plausible
  appetite and an initiative fits, `queue-add` *suggests* escalating to
  `author-brief` — the brief's spec map is the group container.

`queue-add` never silently creates a brief or an initiative. No new `group`
field or grouping primitive is introduced — `[backlog]`/`[work].queue` + `needs`
+ comment-header + single-entry atomic bundle + brief-spec-map cover every weight.

## Testing Strategy

- **Goal-based check** — `queue-add` is a prompt-only skill (prose, like
  `author-brief`/`receive-brief`); its "build" is projection. Verify:
  `make lint-packs` passes, `make build-self` projects the skill into
  `.claude/skills/queue-add/`, and the projected copy matches the source.
- **Visual / manual QA** — run the skill end-to-end against a scratch
  `workspace.toml`: feed a numbered list with one explicit "after X"
  dependency, confirm the proposed diff shows correct slugs, an inferred
  `needs`, rich comments, and an elicited order for the independent items; on
  confirmation, verify entries are appended, existing comments preserved, and no
  spec files created.

No TDD: the skill is prose with no compressible logical invariant. The
comment-preservation and no-schema-drift properties are checked by manual QA
against the observable file diff.

## Assumptions

- **Skills are prompt-only in this ecosystem.** `queue-add` ships as a
  `SKILL.md` under `packs/core/.apm/skills/`; no new Python tool is needed. The
  agent performs the comment-preserving edit directly (as `author-brief` does).
- **Queue order is advisory, not authoritative.** `workspace-status` treats
  no-dep items as concurrently ready; order + comment is a *soft* priority
  signal. If a future spec makes queue order authoritative, § Prioritization is
  revisited.
- **The schema is owned by RFC-0064**; this skill consumes the schema shape and
  never redefines it, consistent with `m1-work-queue`. The repo-level `[backlog]`
  destination is added by the RFC-0064 amendment (2026-07-20). `queue-add` may
  **create** the `[backlog]` table (with its header comment) when routing there
  and it does not yet exist — so the ad-hoc capture path works before the M3
  backlog-section spec lands. Until M3 wires `workspace-status` rendering and the
  deferral lint, a created `[backlog]` is captured and human-readable in
  `workspace.toml` but not yet surfaced by `workspace-status`; that is an
  acceptable ordering dependency, not lost data. `queue-add`'s `[work].queue`
  path is fully independent of M3.
- **`queue-add` is a utility write-skill**, a sibling of `author-brief` /
  `receive-brief`; the ADR-0054 verb taxonomy governs session-arc skills, not
  this one. The name is validated against the write-skill convention (§ AC13).

## Acceptance Criteria

- [ ] **Activation.** The skill triggers on "add these to the queue" / "capture
  these as queue items" (and close paraphrases) when a bulleted or numbered list
  is present in context.
- [ ] **Slug derivation & collision.** Derives a kebab-case `spec/<slug>` from
  each item's text and confirms with the user; on collision with an existing
  `docs/specs/<slug>/` or an existing `queue`/`active`/`[backlog].open` entry,
  prompts before proceeding — never overwrites.
- [ ] **Dependency inference.** Infers `needs` **only** from explicit sequencing
  language, mapping to queue-prefix notation (`work:spec/<slug>`,
  `backlog:<slug>`); independent items get no `needs`.
- [ ] **Cold-start-sufficient comments.** Every appended entry carries a comment
  block covering problem, fix, affected file/skill, and key decisions —
  sufficient for a fresh session to write the full spec. One-liners are rejected.
- [ ] **Target initiative.** Appends to the single active initiative's
  `[work].queue`; when more than one initiative is `active`, prompts for
  selection; never guesses.
- [ ] **Comment-preserving write.** Uses targeted text insertion / `tomlkit`;
  existing comments in `workspace.toml` survive the write.
- [ ] **Graceful degradation.** A missing, unparseable, or queue-less
  `workspace.toml` yields a named diagnostic and continues (no throw): the user
  is told the derived entries and how to add them manually.
- [ ] **Schema respect.** Writes only the keys the schema defines for each entry
  shape — `path` + optional `needs` for `[work].queue` entries; `slug` +
  optional `needs`/`source` for `[backlog].open` entries — and introduces no new
  key and no numeric priority field.
- [ ] **Prioritization.** When two or more mutually independent items are added,
  elicits priority (offering a rubric — RICE / value-vs-effort / Torres /
  custom — as a prompt, not a gate) and records it as queue order + a one-line
  rationale in the group comment; skips elicitation when deps determine order or
  only one item is added.
- [ ] **Grouping.** Appends an independent batch under a single labeled comment
  header; folds a must-ship-together set into one atomic-bundle entry; detects a
  shaped-unit batch (shared outcome + plausible appetite) and *suggests*
  `author-brief`. Introduces no grouping field.
- [ ] **Confirmation before write.** Presents the complete proposed change and
  obtains user sign-off before writing.
- [ ] **No spec files.** The skill writes `workspace.toml` only.
- [ ] **Naming gate.** The skill name follows sibling-of-`author-brief`/`receive-brief`
  write-skill naming (a utility write-skill, outside the ADR-0054 session-arc
  verb taxonomy), and its activation phrases route to it end-to-end without
  colliding with `author-brief`, `receive-brief`, or `workspace-status`.
- [ ] **Destination routing.** The skill writes only to the two homes it owns —
  an active initiative's `[work].queue` and the repo-level `[backlog].open` —
  choosing between them by initiative scope. For any item that fits neither, it
  runs the § Grouping escalation rubric and *suggests* the right destination
  (`author-brief`, `roadmap-intents.md`, `rfc-candidates.md`, a new RFC, or a
  new initiative), deferring that write to the owning skill — never force-fitting
  an ill-matching initiative or auto-creating one.
- [ ] **Parallelism preserved.** The skill never writes a `needs` to express a
  mere priority preference; independent items remain independent so
  `workspace-status` still surfaces them as parallel candidates. Parallel-safe
  sets may be annotated in the group comment as advisory guidance.
- [ ] **Atomic bundling.** When two or more items must ship together to avoid a
  broken intermediate state (e.g. a shared HARD-gate / dangling-anchor hazard),
  the skill records them as a *single* queue entry whose comment enumerates the
  coupled parts and the coupling hazard — not as separate `needs`-linked
  entries. It detects this from explicit coupling language or a shared-gate
  hazard and confirms the bundling with the user.
