# Plan: queue-add

- **Spec:** [`spec.md`](spec.md)

## Approach

`queue-add` is a prompt-only skill in the `core` pack, a sibling of
`author-brief` and `receive-brief`. No new Python tool: the agent performs the
comment-preserving `workspace.toml` edit directly, exactly as `author-brief`
does for the `brief_queue`. The deliverable is a `SKILL.md`, a version bump, a
changelog entry, and a projection.

## Design (LLD)

### Skill procedure (mirrors the write-skill convention)

1. **Ingest** — take the bulleted/numbered list from context (or the user's
   paste).
2. **Derive** — for each item, propose a kebab-case `spec/<slug>` from the item
   text; collision-check against `docs/specs/<slug>/` and existing
   `queue`/`active` entries.
3. **Infer deps** — scan each item for explicit sequencing language; build
   `needs` edges only where present; map to `work:spec/<slug>` or
   `backlog:<slug>`.
4. **Route (destination gate)** — the two homes queue-add owns: an active
   initiative's `[work].queue` (initiative-scoped work; prompt if >1 active) and
   the repo-level `[backlog].open` (well-shaped ready work not scoped to an
   initiative — the default for ad-hoc/orphan items). For an item that fits
   neither, run the escalation rubric and *suggest* the right home
   (`author-brief` / `roadmap-intents.md` / `rfc-candidates.md` / new RFC / new
   initiative); never force-fit or auto-create.
5. **Prioritize** — partition items into dependency-ordered and mutually
   independent; for the independent set (size ≥ 2), elicit an order, offering a
   rubric as a prompt. Record order + one-line rationale. Never encode a
   preference as a `needs` (preserves parallel candidates).
6. **Group** — pick the grouping shape: (a) shaped unit (shared outcome +
   appetite) → suggest `author-brief`; (b) atomic bundle (must ship together —
   shared HARD-gate / dangling hazard) → one queue entry enumerating the coupled
   parts + the hazard; (c) independent batch (default) → flat entries under one
   labeled comment header, annotating any parallel-safe set.
7. **Compose comments** — per entry, write the cold-start-sufficient comment
   (problem / fix / affected file / decisions).
8. **Confirm** — show the full proposed change; wait for sign-off.
9. **Write** — targeted comment-preserving insertion into the resolved
   `[work].queue` or `[backlog].open` (creating the top-level `[backlog]` table
   with its header comment if it does not yet exist); degrade to the named
   diagnostic if `workspace.toml` is absent/unparseable/queue-less.
10. **Hand off** — tell the user the entries are queued and that
    `workspace-status` will surface them (noting, for a freshly created
    `[backlog]`, that rendering arrives with the M3 backlog-section spec).

### Resilience

- Missing/unparseable/queue-less `workspace.toml` → named diagnostic listing the
  derived entries and the manual-append instruction; no throw.
- >1 active initiative → prompt for selection.
- Slug collision → prompt.

## Tasks

- [x] **T1 — Author `packs/core/.apm/skills/queue-add/SKILL.md`.** Frontmatter
      (name + description with triggers and the "do NOT use" delimiters against
      author-brief/receive-brief/workspace-status); body implementing the
      procedure above, including the § Prioritization and § Grouping decision
      logic and the Anti-patterns-to-refuse list. `Depends on: none`.
- [x] **T2 — Bump `core` pack version** in `packs/core/pack.toml` and the
      matching `plugin.json`; add a `[Unreleased]` changelog entry for the new
      skill. `Depends on: T1`.
- [x] **T3 — Project + verify.** Ran `make lint-packs`, `make build-self`,
      confirmed `.claude/skills/queue-add/` matches source and `make build-check`
      is green; checked `git status` for projection-only drift. `Depends on: T2`.
- [ ] **T4 — Manual QA** against a scratch `workspace.toml` per the spec's
      Testing Strategy; confirm comment preservation, correct `needs`, elicited
      order, rich comments, no spec files created. `Depends on: T3`.

## Changelog

- Initial plan drafted for `queue-add`, reflecting the prioritization
  (rubric-agnostic, reuse `decompose-intent` rank pattern) and grouping
  (brief-vs-comment-batch decision tree) design settled with the user.
