---
name: github-brief-intake
description: Use this skill when the user points at a GitHub Milestone and wants it turned into shippable specs — "turn our Q3 milestone into specs", "intake this milestone as a brief", "we track work in GitHub Issues, pull milestone v2-launch into the spec pipeline". The skill pulls the milestone and its issues via the `gh` CLI, maps them onto a product brief (milestone title -> Outcome draft, open and closed issues -> Shape B user stories tagged with their issue number, milestone URL -> `Epic:` provenance pointer), writes it to `docs/product/briefs/<slug>.md`, and hands off to the `receive-brief` skill to elicit gaps, decompose, and build. Do NOT use for a single issue without a milestone (use `new-spec`) or when the user wants to pull multiple repos (this skill is single-repo, single-milestone).
metadata:
  version: "1.0"
---

# Skill: github-brief-intake

This is choreography, not invention. It is the adapter between a GitHub
Milestone and the brief-intake pipeline, for teams that keep the *what/why* of
a body of work in **GitHub Issues under a Milestone** rather than in a written
brief.

It composes two things that already exist:

- **`gh` CLI** (system dependency, not a skill — installed separately; `gh`
  owns its own auth and credential management) — every GitHub read. You never
  write a raw GitHub REST API call inside this skill; `gh api` and
  `gh issue list` are the only verbs used.
- **`receive-brief` skill** (shipped by the host repo's `core` pack; resolved
  by name through the harness) — the brief inbox: it **elicits** missing
  load-bearing fields conversationally, **decomposes** the brief into
  independently-shippable slices, and **executes** each through `new-spec` →
  `work-loop`. This skill does **not** re-explain or re-implement any of
  that — least of all elicitation. It assembles the brief from GitHub and
  hands off.

The one thing this skill owns is the **GitHub Milestone → brief mapping** that
neither side can do alone: `receive-brief` knows nothing about GitHub, and the
`gh` CLI knows nothing about briefs.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## Cross-skill invocation — name, not path

This skill names `receive-brief` and `new-spec` **by their `name:` field, never
by path**. Install locations vary by IDE and scope, and skills can be renamed at
install time. Path coupling silently breaks every alternative layout.

## Prerequisites

Before stage 1, do two things:

### 1. Auth posture check

Run `gh auth status`.

- **Authenticated:** proceed normally for both public and private repos.
- **Unauthenticated:** attempt to read the target repo.
  - **Read succeeds (public repo):** note the unauthenticated posture in the
    brief's `## Assumptions` section ("Data pulled anonymously — no `gh auth
    login`; public repo confirmed.") and continue.
  - **Read returns 404:** GitHub returns 404 for both a private repo and a
    nonexistent repo when called anonymously — the two are indistinguishable.
    Surface the verbatim message: "Repo or milestone not found — if this is a
    private repo, run `gh auth login` and retry; if it is public, check the
    owner/repo/milestone." Stop. Do not retry or attempt further reads.

Never dispatch further reads after a 404 or other non-success response.

### 2. `receive-brief` availability

Probe whether your harness can dispatch a skill registered under the name
`receive-brief`.

- **Present** → normal flow (stage 3 hands off to it).
- **Absent** → graceful-degradation flow (stage 4). You still produce the
  brief and inline the decompose/execute instruction. Note: if `receive-brief`
  is absent, downstream `new-spec` and `work-loop` may likewise be absent —
  acknowledge this in the degradation branch output.

Decide this now so stage 2 knows which shape to write.

## Lifecycle

### Stage 1 — Intake: resolve owner/repo and enumerate the milestone

**Resolve `{owner}/{repo}`** from the user's input (e.g. `eugenelim/my-repo`).
If not given explicitly, read from the current repo context:

```
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'
```

**List available milestones** (if the user has not named one):

```
gh api repos/{owner}/{repo}/milestones \
  --jq '[.[] | {number, title, description, html_url, open_issues, closed_issues}]'
```

Surface the list and ask the user to pick. If the user has given a milestone
title or number, match it from the list.

**Enumerate all issues in the milestone** — include both open and closed so
the story map captures the full scope:

```
gh issue list --repo {owner}/{repo} --milestone "<milestone-title>" --state all \
  --json number,title,body,labels,url,state
```

`{owner}/{repo}` is the value resolved in Stage 1. Use the milestone title in
`--milestone` — the `gh` CLI accepts a milestone number or title. If the issue list returns
empty, produce the brief with an empty Shape B section and an elicit note (see
Stage 2 — empty milestone edge case) rather than aborting.

**Single-issue input (no milestone):** If the user points at a single issue
with no milestone container, that is one feature — `new-spec` territory, not a
multi-feature brief. Stop and recommend `new-spec` (confirm before proceeding).

### Stage 2 — Map to a Shape B brief

Write a draft brief to `docs/product/briefs/<slug>.md`, where `<slug>` is
kebab-case derived from the milestone title (it must match the filename and the
`Brief:` back-link `receive-brief` later stamps on derived specs). Confirm the
slug with the user before writing; check whether a file already exists at that
path and require explicit confirmation to overwrite.

If `core` is installed, copy its `docs/product/briefs/_template.md`; otherwise
use the **carried shape** below.

The GitHub → brief mapping is **Shape B** (story-list):

| Brief field | GitHub source |
|---|---|
| `Outcome` | the milestone title + description, in the user's terms |
| `Scope / Non-goals` | the milestone description, where stated — never invented |
| `Epic:` pointer | the **milestone `html_url`** — provenance back to GitHub |
| `User stories` (`US-n`) | one per issue (below) |

**Each issue becomes one `US-n` line in this pinned format** — the trace
`receive-brief` completes with `Satisfies: US-n` on derived spec acceptance
criteria depends on it:

```
- **US-1.** (#42) As a <role>, I want <capability>, so that <benefit>.
- **US-2.** (#43) <issue title, carried verbatim when it isn't story-shaped> [closed]
```

The issue number is a parenthetical immediately after the id. Reshape the
issue's title into the *As a … I want … so that …* grammar **only when the
source supports it**; otherwise carry the title verbatim and let `receive-brief`
refine it during Elicit. **Never invent a role or benefit the issue does not
state.** Closed issues (where `state == "CLOSED"` — uppercase, as returned by
`gh issue list`) are annotated `[closed]` after the story text.

**Empty milestone edge case:** when the issue list is empty, produce a brief
with the milestone metadata (title → Outcome draft, html_url → Epic:) and an
empty `## User stories` section, followed by an elicit note: "No issues found
in this milestone — `receive-brief` will elicit user stories during the Elicit
stage."

Leave `Success metrics`, `Appetite`, and any silent `Scope` to
`receive-brief` — surfacing and filling those gaps is its Elicit stage, not
yours. The `Spec map`'s Status column is auto-derived downstream; leave it.

### Stage 3 — Hand off to `receive-brief` (the normal flow)

Invoke the `receive-brief` skill **by name**, pointing it at the brief file you
just wrote. From here, `receive-brief` owns everything:

- **Elicit** — it ingests the brief and asks the user for any missing
  load-bearing field (Outcome, Scope). A thin milestone is normal input; it
  elicits rather than rejects. **Do not pre-empt this** by interrogating the
  user yourself.
- **Decompose** — it cuts the stories into independently-shippable slices and
  surfaces the cut for confirmation.
- **Execute** — it chains `new-spec` → `work-loop` per slice and stamps the
  `Brief:` / `Satisfies: US-n` back-links.

Your job ends at the handoff. Do not duplicate the Decompose/Execute stages.

### Stage 4 — Graceful degradation (the `receive-brief`-absent flow)

When the Prerequisites probe found **no** `receive-brief` skill, do not stop —
you have still produced a useful brief. Inline the following instruction for
the agent to act on directly. Note that downstream `new-spec` and `work-loop`
skills **may likewise be absent** (if `core` is not installed, none of them
are) — fall back to the host repo's own spec/build process where they are:

> **Decompose & execute (inlined because `receive-brief` is not installed).**
> 1. **Elicit the gaps.** The brief above may be missing its Outcome or Scope.
>    Ask the user for those load-bearing fields — do not invent them. Offer
>    defaults for Success metrics / Appetite; never block on them.
> 2. **Decompose by shippability, not by component.** Cut into slices each
>    *independently shippable and testable* — one feature a build loop can carry
>    end to end. Group the `US-n` stories into slices. Flag any milestone-sized
>    story for splitting; flag any Outcome no slice covers as a gap.
> 3. **Surface the cut and wait for confirmation** before authoring any spec.
> 4. **Execute** each confirmed slice through your repo's spec process (the
>    `new-spec` skill if installed, else your repo's equivalent), then build it
>    (the `work-loop` skill if installed, else your repo's loop). Stamp each
>    derived spec with a `Brief:` back-link to this brief and a
>    `Satisfies: US-n` marker on the acceptance criteria that satisfy a story.

#### Carried brief shape (used only when core's `_template.md` is absent)

```markdown
# Brief: <one-line outcome>

- **Slug:** `<slug>`
- **Received:** <YYYY-MM-DD>
- **Owner:** <who owns this repo's slice>
- **Epic:** <milestone html_url>

## Outcome
<the milestone title / description, reworded as a problem and user-facing outcome — elicit if the milestone is thin>

## Success metrics
<observable signals; offer a default if absent>

## Scope / Non-goals
**In scope:**
-
**Non-goals:**
-

## User stories
- **US-1.** (#NNN) As a <role>, I want <capability>, so that <benefit>.

## Spec map
| Spec | Status |
| --- | --- |
| `<feature-slug>` | <auto> |
```

### Stage 5 — Post-intake write-back (optional, offer only after brief is confirmed)

After the brief is written and the user has confirmed it, offer (do not
require) to update the GitHub issues:

- **Comment** on one or more issues (e.g. a brief-slug link or a triage note).
  Confirm per issue or per batch — the user decides the comment text.
- **Label** one or more issues. Confirm per label application; never remove
  labels without explicit confirmation.
- **Close** one or more issues. Confirm individually — closing is irreversible
  without a reopening step.

**Each action type requires separate explicit user confirmation.** Never combine
comment + label + close into a single prompt — they have different blast radii.

**Never edit the body of a GitHub issue.** Post-intake write-back is strictly
comment / label / close; issue body text is immutable for this skill.

## Don't

- **Don't write a raw GitHub REST call.** Use `gh api` and `gh issue list`;
  never `curl https://api.github.com/...` inside the skill body.
- **Don't reimplement `receive-brief`'s Elicit stage.** Do not interrogate the
  user for a missing Outcome or Scope — produce the brief and hand off (or, in
  the degraded path, hand the eliciting *instruction* to the agent).
- **Don't invent an Outcome, Scope, or story** the milestone or its issues
  don't state. A thin milestone is fine — surface the gap; `receive-brief`
  elicits it.
- **Don't force a single issue into a brief.** One issue → `new-spec`. A
  label-filtered list with no milestone → confirm the grouping is intentional
  first.
- **Don't become a cross-repo coordination hub.** Carry the milestone URL as
  the `Epic:` pointer only; do not coordinate work across repos.
- **Don't hardcode a skill or template path.** Look skills up by name only.
- **Don't edit issue bodies.** Post-intake write-back is comment / label /
  close — never body mutation.
- **Don't add credentialed-skill frontmatter.** `gh` owns its own credential
  chain; this skill never touches a token. No `credentialed:` field is needed.
