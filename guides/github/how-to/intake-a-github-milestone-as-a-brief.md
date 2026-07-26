# How to intake a GitHub Milestone as a product brief

**Use this when:** you have a GitHub Milestone with grouped issues and want to turn the full story map into a product brief that feeds the `receive-brief` intake pipeline.
**Prerequisites:** `github` pack and `gh` CLI installed; for private repos, authenticated with `gh auth login` — see [Prerequisites](#prerequisites).
**Result:** a Shape B product brief at `docs/product/briefs/<slug>.md`, handed off to `receive-brief` for gap elicitation, decomposition, and spec-chained execution.

Turn a GitHub Milestone — and the issues grouped under it — into a
[Shape B product brief](../../core/reference/product-brief-fields.md) that
feeds the `receive-brief` intake pipeline.

## Prerequisites

1. **`github` pack installed** — `agentbundle install --pack github <catalogue>`
2. **`gh` CLI installed** — [https://cli.github.com](https://cli.github.com)
3. **For private repos: authenticate** — run `gh auth status`; if unauthenticated,
   run `gh auth login`.

Public repos are accessible anonymously. The skill notes the unauthenticated
posture in the produced brief.

## Full intake flow

### 1. Point your agent at a milestone

Tell your agent, for example:

- "Turn our Q3 milestone into specs."
- "Intake the 'v2 launch' milestone from your-org/my-repo."
- "Pull GitHub milestone #4 and create a brief."

The `github-brief-intake` skill fires automatically when the agent recognises
a GitHub Milestone intake request.

### 2. The skill lists and confirms the milestone

The skill fetches all milestones from the repo and asks you to confirm which
one to use (or matches your input). It then enumerates all issues under that
milestone — open *and* closed — so the story map captures the full scope of
work, including completed items.

### 3. Review the story map

The skill maps each issue to a Shape B user story:

```
- **US-1.** (#42) As a developer, I want one-click install, so that I can start in 60 seconds.
- **US-2.** (#43) CLI displays installed pack versions. [closed]
```

- Issue number is pinned in the `(#NNN)` parenthetical — used for traceability.
- Closed issues are annotated `[closed]`.
- Story text is reshaped to *As a … I want … so that …* where the issue title
  supports it; otherwise the title is carried verbatim for `receive-brief` to refine.

### 4. Confirm the slug

The skill proposes a kebab-case slug derived from the milestone title (e.g.
`q3-launch`) and confirms it with you before writing. If a brief already exists
at `docs/product/briefs/<slug>.md`, you are asked to confirm overwrite.

### 5. Write the brief

The brief is written to `docs/product/briefs/<slug>.md` with:

- **Outcome draft** from the milestone title and description.
- **User stories** (`US-1` … `US-n`) — one per issue, in the pinned format.
- **Epic:** pointer to the milestone's GitHub URL for provenance.

Thin milestones (no description, sparse issue titles) are fine — `receive-brief`
elicits what's missing in the next step.

### 6. Hand off to `receive-brief`

The skill calls `receive-brief` by name. From here, `receive-brief` owns the
rest:

1. **Elicit** — fills missing Outcome / Scope conversationally.
2. **Decompose** — cuts the stories into independently-shippable slices and
   confirms the cut with you.
3. **Execute** — chains `new-spec` → `work-loop` per slice; stamps `Brief:` and
   `Satisfies: US-n` back-links onto derived specs.

## Auth-degradation path (unauthenticated, public repo)

If `gh auth status` shows you are not logged in but the repo is public, the
skill reads anonymously. The produced brief notes this in its `## Assumptions`
section:

> Data pulled anonymously — no `gh auth login`; public repo confirmed.

Proceed as normal. If the read returns 404, the repo may be private or
nonexistent — run `gh auth login` and retry.

## Single-issue redirect

If you point the skill at a single issue with no milestone container, the skill
stops and recommends `new-spec` — one issue is one feature, not a multi-feature
brief. Confirm before the skill proceeds.

## Optional post-intake write-back

After the brief is written and you have confirmed it, the skill can:

- **Comment** on issues (e.g. a brief-slug link as a triage note).
- **Label** issues.
- **Close** issues.

Each action type requires a separate explicit confirmation. The skill never
edits issue bodies — write-back is comment / label / close only.

## What to do when `receive-brief` is not installed

If the `core` pack is not installed (and therefore `receive-brief` is absent),
the skill still produces the brief and inlines a decompose/execute instruction
you can follow directly. Note that `new-spec` and `work-loop` may also be absent
in this case — fall back to your repo's own spec/build process.

## Next steps

- The produced brief is at `docs/product/briefs/<slug>.md`.
- `receive-brief` drives the rest of the intake pipeline.
- For more on the brief format and Definition of Ready fields, see
  [`product-brief-fields.md`](../../core/reference/product-brief-fields.md).
