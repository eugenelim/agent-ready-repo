# Spec: capture-work — universal capture-then-triage front-door

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Amendment #3 (2026-07-20) — capture front-door, shaping-typed [backlog], capability-detected hand-off, mode tags, work-loop guard
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service <!-- prompt-only skill + two companion SKILL.md edits; no UI, no API -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`capture-work` is the single capture-then-triage entry point for adding work to
`workspace.toml`. It replaces `queue-add`, extending its scope from "append to a
known queue" to "classify the item and write it to the right destination": build
items (`[build]`) route to the active initiative's `[work].queue` or the
repo-level `[backlog].open`; shaping items (`[shape]`) route to `[shaping_queue]`
or `[backlog].open` with a `type` field. Classification happens before writing,
is surfaced to the user, and is always confirmed before the edit. For shaping
items, the skill offers a progressive capability-detected hand-off — invoking the
matching shaping skill if its pack is installed, or stamping the entry and emitting
an install hint if it is not. All prior `queue-add` routing, grouping,
prioritization, and comment-quality behaviors are preserved under the new name.

Two companion changes ship with the rename: `workspace-status` prefixes every
"Ready to start" item with `[build]` or `[shape]` so the two-room model is
immediately visible at session start, and `work-loop` gains a step-0 guard that
redirects when handed a shaping-typed item — the work-time backstop for items
that were misclassified at capture time.

The user is an agent (or the human driving it) at the end of a session, holding
work to queue — or at the start of the next session, oriented by
`workspace-status`. Success is: every item lands in the right queue, typed
correctly, with enough context that a cold-start session invokes the right skill
without re-reading this session's history.

## Boundaries

### Always do

- **Classify before writing.** Surface the classification (`[build]` or
  `[shape]` + subtype) to the user; confirm before writing, the same as the
  existing confirmation-before-write gate.
- **Write the entry first, then offer the hand-off.** For shaping items, always
  stamp the typed entry in workspace.toml first (never skip the write), then
  offer to invoke the matching skill progressively if the pack is installed.
- **Preserve all prior queue-add behaviors.** Slug derivation + collision check;
  dependency inference only from explicit sequencing language; cold-start-
  sufficient TOML comments; confirmation before write; comment-preserving edit
  (tomlkit / targeted insertion — never a tomllib+tomli_w round-trip); graceful
  degradation on absent/unparseable workspace.toml.
- **Edit canonical pack sources only.** `packs/core/.apm/skills/` for skills,
  `packs/core/seeds/` for seeds; run `make build-self` after to project changes
  to `.claude/` and `.agents/`. Never edit projected paths directly.
- **Update all consumer references atomically.** The rename from `queue-add` to
  `capture-work` must land in all operative locations (workspace-status/SKILL.md
  ×2, pack.toml, plugin.json, docs/specs/README.md, changelog,
  web/src/content/journeys/core.md, skill directory rename) in the same PR —
  no window where some paths still say `queue-add`.
- **Add `[build]`/`[shape]` prefix to every "Ready to start" item** in
  workspace-status — work queue items prefix `[build]`; shaping queue items
  prefix `[shape]`; [backlog] items with a `type` field prefix `[shape]`,
  those without prefix `[build]`.

### Ask first

- **Which initiative** when more than one has `status = "active"`. Never guess.
- **Classification** when the item's mode is ambiguous — some items straddle
  build and shaping (e.g. a "research the right approach first, then implement"
  item). Surface the ambiguity and ask.
- **Shaping subtype** when the item is clearly shaping but the subtype is
  unclear. Offer: `shape` (PE six-step), `research` (desk-research pack),
  `strategy` (product-strategy pack), `signal` (ongoing monitoring),
  `design` (experience-design pack).
- **Whether to invoke the shaping skill immediately** (the progressive hand-off)
  — always ask; never auto-invoke without the user's explicit go-ahead.

### Never do

- **Create spec files.** Writes `workspace.toml` only — same as `queue-add`.
- **Invent a dependency.** Add `needs` only from explicit sequencing language.
- **Encode a priority preference as a `needs`.** Priority is queue order +
  comment; preference never becomes a hard edge.
- **Hard-depend on an optional pack.** The core pack must never import a
  function or path from the PE, desk-research, or experience-design pack. The
  capability-detected hand-off is a conditional offer, never a hard call.
- **Write a `type` field on build entries.** `type` is a shaping-only field;
  build entries in `[work].queue` or untyped `[backlog].open` entries never
  carry it.
- **Skip the consumer sweep.** No PR lands with any surviving `queue-add`
  references in the projected or canonical paths.
- **Change the `[shaping_queue]` or `[work]` schema beyond what this spec
  authorises.** The only schema change is: `[backlog].open` entries may now
  carry a `type` field for shaping entries. No new top-level keys, no new
  sections.
- **Run a `tomllib` + `tomli_w` full round-trip** — it strips comments, which
  are the entire point of the per-entry comment convention.

## Testing Strategy

`capture-work` and its companion changes are prompt-only skills; no test files
are modified. Verification is goal-based and manual QA.

**Goal-based checks (mechanical):**

- `make build-self` exits 0 and produces `.claude/skills/capture-work/` and
  `.agents/skills/capture-work/`. No `.claude/skills/queue-add/` or
  `.agents/skills/queue-add/` directory survives.
- `grep -r "queue-add" .claude/skills/ .agents/skills/ packs/core/pack.toml packs/core/.claude-plugin/plugin.json docs/specs/README.md web/src/content/journeys/core.md` exits non-zero (no matches).
- `grep -r "\[build\]\|\[shape\]" packs/core/.apm/skills/workspace-status/SKILL.md` shows the mode-tag logic present.
- `grep "\[shape\].*use\|Shaping-item guard" packs/core/.apm/skills/work-loop/SKILL.md` returns a match in Step 0.

**Manual QA (end-to-end):**

- **Pack-absent path:** Run `capture-work` with a mixed list containing one
  build item and one research item (with desk-research pack NOT installed);
  verify: classification is surfaced, entries route correctly (build →
  `[work].queue`; research → `[shaping_queue]` or `[backlog]` with
  `type = "research"`), the install hint is emitted for the research item,
  and existing comments in workspace.toml survive the edit.
- **Pack-present path:** With desk-research pack installed, repeat with a
  research item; verify the progressive hand-off offer appears (not just an
  install hint) and that confirming it invokes `desk-research-project-start`.
- Run `workspace-status` after either scenario; verify every Ready item has a
  `[build]`, `[shape]`, or `[brief]` prefix as appropriate.
- Run `work-loop docs/specs/<shaping-slug>/` where `<shaping-slug>` points at
  an entry in `[shaping_queue]`; verify the step-0 guard emits a redirect
  naming the correct skill and stops.
- Run `work-loop docs/specs/<slug>/` where `<slug>` is a `[backlog].open`
  entry with a `type` field; verify the guard fires there too.

## Acceptance Criteria

- [x] **AC1 — Rename + activation.** The skill is named `capture-work` in
  frontmatter, directory, and activation phrases. Triggers on "capture this",
  "add this to the queue", "capture these as queue items", "queue this up",
  "add this to the backlog" (and close paraphrases). `queue-add` is no longer
  a reachable activation target — no frontmatter, no directory, no projected
  copy uses that name.

- [x] **AC2 — Classification surfaced before write.** For each input item, the
  skill surfaces its classification (`[build]` or `[shape]` + subtype) to the
  user as part of the confirmation-before-write step. No item is written
  without the user seeing its classification.

- [x] **AC3 — Build routing preserved.** Build-classified items route to the
  active initiative's `[work].queue` (initiative-scoped) or `[backlog].open`
  (not initiative-scoped) — the same destinations and routing logic as
  `queue-add`. All prior AC behavior (slug derivation, collision check,
  dependency inference from explicit sequencing language only, grouping
  including atomic-bundle detection, prioritization elicitation,
  escalation rubric, comment quality, confirmation, comment-preserving write,
  schema respect, graceful degradation) is preserved exactly.

- [x] **AC4 — Shaping-item routing: initiative-scoped.** When a shaping item
  is initiative-scoped, it is written to the active initiative's
  `[shaping_queue].backlog` as an inline object `{slug = "...", type = "<subtype>"}`.
  Exception: `signal`-subtype items route to `[shaping_queue].active` (not
  `.backlog`) because signals represent ongoing monitoring context, not work to
  be picked up later. If the item has an explicit dependency, `needs` is added.
  The entry carries a cold-start-sufficient TOML comment (problem, fix,
  file/skill, unblock condition). It is never written to `[work].queue`.

- [x] **AC5 — Shaping-item routing: repo-level.** When a shaping item is not
  initiative-scoped (the common ad-hoc case), it is written to
  `[backlog].open` as `{slug = "...", type = "<subtype>", needs?, source?}`.
  The `type` field is always written; no `type` is written for build entries.

- [x] **AC6 — Progressive capability-detected hand-off.** After writing a
  shaping-typed entry, the skill checks whether the matching skill's pack is
  installed by probing for the skill file in the projected skill paths (both
  `.claude/skills/<skill-name>/SKILL.md` and `.agents/skills/<skill-name>/SKILL.md`
  — pack present if either exists):
  - Pack present and user confirms: skill invokes (or offers to invoke) the
    appropriate skill (`frame-intent` for `shape`, `desk-research-project-start`
    for `research`, etc.) in the same session.
  - Pack absent: emits a named install hint (`requires <pack> pack — install to
    work this item`) and stops. No error, no blocked write.
  The entry is always written before the hand-off check. `signal`-subtype items
  skip the hand-off entirely — signals have no matching action skill.

- [x] **AC7 — workspace-status: every item prefixed.** Every item in the
  "Ready to start" section and every item in the Backlog section of
  `workspace-status` output carries an explicit room prefix:
  - In "Ready to start": `[work]` queue items → `[build]`
  - In "Ready to start": `[shaping_queue]` items → `[shape]`
  - In "Ready to start": `[brief_queue]` items → `[brief]` (briefs are
    neither build nor shaping — the prefix is renamed for visual consistency
    but not mode-classified)
  - In Backlog: `[backlog].open` items with a `type` field → `[shape]`
  - In Backlog: `[backlog].open` items without a `type` field → `[build]`
  The prefix replaces the existing label; subtype and skill-prompt rendering is
  unchanged.

- [x] **AC8 — workspace-status: queue-add references updated.** The two
  `queue-add` references in `packs/core/.apm/skills/workspace-status/SKILL.md`
  are updated to `capture-work`:
  - "add to [work].queue or run queue-add" → "add to [work].queue or run capture-work"
  - "Start new work … `queue-add`" → "Start new work … `capture-work`"

- [x] **AC9 — work-loop orient-step guard.** At work-loop step 0, after
  reading `workspace.toml`, if the spec slug (derived from the argument path or
  the active spec path) matches any shaping entry — an entry in any initiative's
  `[shaping_queue]` (active or backlog) OR a `[backlog].open` entry carrying a
  `type` field — the skill emits a redirect and stops without proceeding to PLAN:
  - For subtypes `shape`, `research`, `strategy`, `design`: "This is a `[shape]`
    item (`type = <subtype>`); use `<skill>` rather than `work-loop` — `work-loop`
    is for build items only." The redirect names the correct skill for the subtype.
  - For `signal` subtype: "This is a monitoring signal, not workable via any
    action skill — `work-loop` is for build items only."
  The guard does not fire on build items (items without a `type` field).

- [x] **AC10 — Consumer sweep complete.** After `make build-self`, no
  `queue-add` reference survives in operative refs: `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `docs/specs/README.md`,
  `docs/product/changelog.md` (operative [Unreleased] entry only — shipped
  historical entries may name `queue-add` descriptively),
  `web/src/content/journeys/core.md`,
  `.claude/skills/` (all files), `.agents/skills/` (all files).
  `marketplace.json` is regenerated from `plugin.json` by `make build-self` —
  verify it carries `capture-work` after the run.

- [x] **AC11 — build-self gate.** `make build-self` exits 0.
  `.claude/skills/capture-work/SKILL.md` and
  `.agents/skills/capture-work/SKILL.md` exist and are byte-identical to
  `packs/core/.apm/skills/capture-work/SKILL.md`. Neither
  `.claude/skills/queue-add/` nor `.agents/skills/queue-add/` exists after the
  run.

- [x] **AC12 — Changelog entry.** The existing `[Unreleased]` `queue-add`
  entry in `docs/product/changelog.md` is rewritten in place to cover
  `capture-work` — not a second entry added. The rewritten entry covers:
  (a) `capture-work` rename + classification extension (replacing the
  prior `queue-add` description), (b) workspace-status `[build]`/`[shape]`/
  `[brief]` mode tags, (c) work-loop orient-step guard. No historical
  mention of `queue-add` is added to the Unreleased section.

- [x] **AC13 — workspace.toml updated.** `workspace.toml` moves
  `spec/capture-work` from `[work].queue` to `[work].shipped` in the same PR.

- [x] **AC14 — roadmap.md updated.** `docs/product/roadmap.md` receives a
  one-line shipped entry for capture-work.

## Assumptions

- Technical: Skills are prompt-only SKILL.md files; canonical source is
  `packs/core/.apm/skills/`; `make build-self` projects to `.claude/skills/`
  and `.agents/skills/` (source: `m3-backlog-absorption/spec.md` Boundaries +
  queue-add directory structure)
- Technical: Eight operative consumer references require updating —
  `workspace-status/SKILL.md` (×2), `pack.toml`, `plugin.json`,
  `docs/specs/README.md`, `docs/product/changelog.md`,
  `web/src/content/journeys/core.md`, and the skill directory itself; three
  projected copies (`.apm`, `.claude`, `.agents`) (source: grep scan 2026-07-20).
  `workspace.toml` retains intentional survivors (see below).
- Technical: `workspace.toml [backlog].open` currently uses `{slug, needs?,
  source?}` — no `type` field; this spec adds `type` for shaping entries only
  (source: workspace.toml read 2026-07-20)
- Technical: work-loop SKILL.md step 0 has no shaping-item guard today (source:
  grep of work-loop SKILL.md 2026-07-20)
- Process: Constrained by RFC-0064 Amendment #3 (2026-07-20) facets 1–4 plus
  companion items (mode tags, guard) (source: RFC-0064 Amendments section)
- Process: CONVENTIONS/new-rfc/receive-brief doctrine edits are out of scope
  here — they land in `spec/workspace-journey-guides-and-planning-doctrine`
  (source: workspace.toml queue sequencing)
- Technical: `workspace.toml` retains intentional `queue-add` strings that are
  out of scope for the rename sweep: the `"spec/queue-add"` shipped-spec slug
  (historical record, never renamed) and the Amendment #3 comment "Rename
  queue-add → capture-work" (self-referential documentation). A broad
  `grep -r queue-add workspace.toml` will produce these matches; they are
  expected and intentional.
- Product: Rename target confirmed as `capture-work`; shaping subtypes:
  `research/strategy/shape/signal/design` (source: RFC-0064 D9 + workspace-status
  SKILL.md); progressive hand-off confirmed; every Ready item prefixed (source:
  user confirmation 2026-07-20)
