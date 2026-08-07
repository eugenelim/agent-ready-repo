---
name: jira-brief-intake
description: Use this skill when the user points at a Jira epic (or a board / sprint / JQL selection of issues) and wants it turned into shippable specs -- "turn PROJ-100 into specs", "decompose this epic", "we plan kanban-style in Jira, break this epic into a product brief". The skill pulls the epic and its children via the `jira` skill, maps them onto a product brief (epic -> Outcome, child issues -> Shape B user stories tagged with their Jira key, epic key -> `Epic:` pointer), writes it to `docs/product/briefs/<slug>.md`, and hands off to the `receive-brief` skill to elicit gaps, decompose, and build. Do NOT use for a single feature (use `new-spec`) or a defect (use `jira-defect-flow`).
metadata:
  version: "1.0"
---

# Skill: jira-brief-intake

This is choreography, not invention. It is the adapter between a tracker and
the brief-intake pipeline, for teams that keep the *what/why* of a body of work
in a Jira **epic and its child issues** rather than in a written brief. It
composes two things that already exist:

- **`jira` skill** (sibling in this pack) — every Jira read. You never write a
  raw Jira REST call here, and this skill is **read-only**: it never transitions,
  comments, attaches, creates, updates, or deletes.
- **`receive-brief` skill** (shipped by the host repo's `core` pack; resolved
  by name through the harness) — the brief inbox: it **elicits** missing
  load-bearing fields conversationally, **decomposes** the brief into
  independently-shippable slices, and **executes** each through `new-spec` →
  `work-loop`. This skill does **not** re-explain or re-implement any of that —
  least of all elicitation. It assembles the brief from Jira and hands off.

The one thing this skill owns is the **Jira → brief mapping** that neither side
can do alone: `receive-brief` knows nothing about Jira, and `jira` knows
nothing about briefs. If you find yourself writing a Jira REST call, or
interrogating the user for a missing Outcome, stop — the first belongs in
`jira`, the second in `receive-brief`.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## Cross-skill invocation — name, not path

This skill names sibling skills (`jira`, `receive-brief`, `new-spec`) **by
their `name:` field, never by path**. Install locations vary by IDE and scope,
and skills can be renamed at install time. Path coupling silently breaks every
alternative layout.

The contract: when this skill says *"via the `jira` skill: `get-issue $KEY
...`"*, the agent uses its native skill-dispatch mechanism to invoke the skill
registered under that name with those arguments. In Claude Code that's the
Skill tool (`/<skill-name>` or programmatic dispatch); in other IDEs it's the
equivalent. **If you find yourself writing `~/.claude/skills/jira/...` or any
other hardcoded path here, stop — look up the skill by name instead.**

Install guidance for the named dependencies lives in `manifest.json` under
`deps.skills` — that's a *where to get them* hint, not a runtime path.

## Prerequisites

Before stage 1, confirm two things — they behave differently:

1. **`jira` is installed and authenticated — a hard dependency.** Invoke it:
   `jira: check`.
   - Exit 0 → proceed.
   - Exit 2 → the user must act. Tell them to run `credential-setup`
     themselves (it's interactive — do not run it for them), then stop. **Do
     not dispatch any read into an auth failure.**
   - There is **no degraded path** without `jira` — it performs every read this
     skill depends on.

2. **`receive-brief` is installed — a soft dependency.** Probe whether your
   harness can dispatch a skill registered under the name `receive-brief`.
   - Present → the normal flow (stage 3 hands off to it).
   - Absent → the **graceful-degradation** flow (stage 4). You still produce the
     brief; you just inline the decompose/execute instruction instead of
     handing off. Decide this now so stage 2 knows which shape to write.

## Lifecycle

### Stage 1 — Intake: pull the epic and its children

Fetch the epic with the fields a brief needs, via the `jira` skill:

```
get-issue $EPIC_KEY --fields "summary,description,labels,issuetype,status" --expand renderedFields
```

Then **enumerate its children**. Jira has no single "get children" verb, and the
parent↔child relationship is named differently across flavors — so query both
forms through the `jira` skill's `search` and use whichever returns issues:

```
# Cloud team-managed projects use `parent`:
search "parent = $EPIC_KEY ORDER BY created ASC" --fields "summary,description,issuetype,status"

# Server / Data Center and company-managed Cloud use the "Epic Link" field:
search '"Epic Link" = $EPIC_KEY ORDER BY created ASC' --fields "summary,description,issuetype,status"
```

`"Epic Link"` **does not exist** on team-managed Cloud and a JQL referencing it
errors there; `parent` is empty for an epic on company-managed/Server. Try one,
and **fall back to the other** when it errors on a missing field or returns
zero rows. Never assume a single form — silently returning zero children is the
failure this guards against.

**Other intake shapes** (kanban teams often have no epic):

- **A board / sprint / JQL selection** instead of an epic: the user gives you a
  JQL (or a saved-filter / board scope). The matched issues become the brief's
  stories. There is then **no single parent to derive the Outcome from** —
  record that as a gap for `receive-brief` to elicit (do not invent one).
- **A single non-epic issue with no children**: that is *one feature*, not a
  multi-feature brief. **Stop and recommend `new-spec`** (and, if it's a
  defect, `jira-defect-flow`). Ask before treating it as a brief — do not force
  a one-ticket scope into the intake pipeline.

### Stage 2 — Map to a Shape B brief

Write a draft brief to `docs/product/briefs/<slug>.md`, where `<slug>` is
kebab-case derived from the epic summary (it must match the filename and the
`Brief:` back-link `receive-brief` later stamps on derived specs). If core is
installed, copy its `docs/product/briefs/_template.md`; otherwise use the
**carried shape** below.

The Jira → brief mapping is **Shape B** (story-list), because an epic with
children *is* a story list:

| Brief field | Jira source |
|---|---|
| `Outcome` | the epic's summary + description, in the user's terms (the problem and what changes for them) |
| `Scope / Non-goals` | the epic description / labels, where stated — never invented |
| `Epic:` pointer | the **epic key** (e.g. `PROJ-100`) — provenance back to the tracker, exactly what this field is for |
| `User stories` (`US-n`) | one per child issue (below) |

**Each child issue becomes one `US-n` line in this pinned format** — the trace
`receive-brief` will complete with `Satisfies: US-n` on derived spec acceptance
criteria depends on it:

```
- **US-1.** (PROJ-101) As a <role>, I want <capability>, so that <benefit>.
- **US-2.** (PROJ-102) <child summary, carried verbatim when it isn't story-shaped>
```

The Jira key is a parenthetical immediately after the id — the slot the bare
template line leaves undefined. Reshape the child's summary into the
*As a … I want … so that …* grammar **only when the source supports it**;
otherwise carry the summary verbatim and let `receive-brief` refine it during
Elicit. **Never invent a role or benefit the child issue does not state.**

Leave `Success metrics`, `Appetite`, and any silent `Scope` to
`receive-brief` — surfacing and filling those gaps is its Elicit stage, not
yours. The `Spec map`'s Status column is auto-derived downstream; leave it.

### Stage 3 — Hand off to `receive-brief` (the normal flow)

Invoke the `receive-brief` skill **by name**, pointing it at the brief file you
just wrote. From here, `receive-brief` owns everything:

- **Elicit** — it ingests the brief and asks the user for any missing
  load-bearing field (Outcome, Scope). A thin epic is normal input; it elicits
  rather than rejects. **Do not pre-empt this** by interrogating the user
  yourself.
- **Decompose** — it cuts the stories into independently-shippable slices and
  surfaces the cut for confirmation.
- **Execute** — it chains `new-spec` → `work-loop` per slice and stamps the
  `Brief:` / `Satisfies: US-n` back-links.

Your job ends at the handoff. Do not duplicate the Decompose/Execute stages.

### Stage 4 — Graceful degradation (the `receive-brief`-absent flow)

When the Prerequisites probe found **no** `receive-brief` skill, do not stop —
you have still produced a useful brief. Inline the following instruction for the
agent to act on directly, and note that the downstream `new-spec` and
`work-loop` skills **may likewise be absent** (if `core` isn't installed, none
of them are) — fall back to the host repo's own spec/build process where they
are:

> **Decompose & execute (inlined because `receive-brief` is not installed).**
> 1. **Elicit the gaps.** The brief above may be missing its Outcome or Scope.
>    Ask the user for those load-bearing fields — do not invent them. Offer
>    defaults for Success metrics / Appetite; never block on them.
> 2. **Decompose by shippability, not by component.** Cut into slices each
>    *independently shippable and testable* — one feature a build loop can carry
>    end to end. Group the `US-n` stories into slices. Flag any epic-sized story
>    for splitting; flag any Outcome no slice covers as a gap.
> 3. **Surface the cut and wait for confirmation** before authoring any spec.
> 4. **Execute** each confirmed slice through your repo's spec process (the
>    `new-spec` skill if installed, else your repo's equivalent), then build it
>    (the `work-loop` skill if installed, else your repo's loop). Stamp each
>    derived spec with a `Brief:` back-link to this brief and a
>    `Satisfies: US-n` marker on the acceptance criteria that satisfy a story.

#### Carried brief shape (used only when core's `_template.md` is absent)

Keep this minimal — headings + the `US-n` line format, not a full copy of the
canonical template (which lives at `docs/product/briefs/_template.md` when core
is installed):

```markdown
# Brief: <one-line outcome>

- **Slug:** `<slug>`
- **Received:** <YYYY-MM-DD>
- **Owner:** <who owns this repo's slice>
- **Epic:** <JIRA-EPIC-KEY>

## Outcome
<the problem and the user-facing outcome — LOAD-BEARING; elicit if the epic is thin>

## Success metrics
<observable signals; offer a default if absent>

## Scope / Non-goals
**In scope:**
-
**Non-goals:**
-

## User stories
- **US-1.** (JIRA-KEY) As a <role>, I want <capability>, so that <benefit>.

## Spec map
| Spec | Status |
| --- | --- |
| `<feature-slug>` | <auto> |
```

## Don't

- **Don't write a raw Jira REST call**, or re-implement a `jira` subcommand. If
  `jira` is missing a read verb you need, extend that skill — don't shim around it.
- **Don't invoke any Jira write verb** — `create-issue`, `update-issue`,
  `delete-issue`, `transition`, `comment`, `attach`. Intake is read-only. (The
  one example showing these is the *banned* list, not a usage.)
- **Don't reimplement `receive-brief`'s Elicit stage.** Do not interrogate the
  user for a missing Outcome or Scope — produce the brief and hand off (or, in
  the degraded path, hand the eliciting *instruction* to the agent).
- **Don't invent an Outcome, Scope, or story** the Jira source doesn't state.
  A thin epic is fine — surface the gap; `receive-brief` elicits it.
- **Don't force a single ticket into a brief.** One issue is one feature →
  `new-spec`. A defect → `jira-defect-flow`.
- **Don't become a cross-repo coordination hub.** Carry the epic key as the
  `Epic:` pointer only; do not reimplement a tracker (own the slice).
- **Don't hardcode a sibling skill or template path.** Look skills up by name.

## Edge cases

- **No epic, just a JQL/board scope.** The matched issues are the stories, but
  there's no parent for the Outcome. Record the missing Outcome as a gap and
  let `receive-brief` elicit it — don't fabricate one from the issue list.
- **Epic with zero children found.** Confirm you tried *both* child-query forms
  (stage 1). If genuinely empty, the epic is a one-liner with no decomposition —
  ask the user whether it's really a single feature (`new-spec`) or whether the
  children live under a different link type.
- **Child issues that are themselves epics** (a hierarchy deeper than one
  level). Flag them as epic-sized stories for splitting; don't silently flatten
  a sub-epic into a single `US-n`.
- **Custom fields hold the real scope** (some teams keep acceptance criteria in
  a custom field). Resolve names with `jira`'s `--expand names` and map what's
  there; if the scope isn't in any field you can read, surface the gap.
- **`receive-brief` present but `new-spec`/`work-loop` absent.** `receive-brief`
  itself surfaces that gap when it tries to execute — you've done your job by
  handing off; don't pre-solve its downstream.

## Examples

See [`references/examples.md`](references/examples.md) for worked patterns: an
epic-with-children happy path, a JQL/board selection, the single-non-epic-issue
→ `new-spec` case, and the `receive-brief`-absent degraded path.
