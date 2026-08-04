---
name: GitHub
scope: user
tagline: "Turn a GitHub Milestone into a product brief"
skills:
  - github-brief-intake
installCommand: "agentbundle install --pack github --scope user"
docsUrl: /guides/github/
---

Reads a GitHub Milestone — title, description, and all linked issues — and
maps it onto a structured product brief. Nothing is written until you approve
the draft. The brief lands in `docs/product/briefs/` and hands off to
`receive-brief` for gap elicitation, decomposition, and spec-chained execution.

**Starts read-only.** No files are written until you confirm the brief.

---

Try this first:

```
Turn our Q3 milestone into a product brief.
```

What you get: milestone and issues read from GitHub · a structured brief drafted
with problem statement, user jobs, acceptance criteria, and a `receive-brief`
handoff — ready for your review before anything is written.

---

### What you can do

**Turn a Milestone into a product brief**

Point the agent at any GitHub Milestone — by name, number, or `org/repo` path.
The agent reads the milestone and its issues, extracts shape, problem statement,
and user stories, and presents a draft brief for your review.
Nothing is written until you approve.

```
Intake the 'v2 launch' milestone from your-org/my-repo as a product brief.
```

---

**Hand off to the build queue**

Once you approve the brief, the agent writes it to
`docs/product/briefs/<slug>.md` and runs `receive-brief` to elicit any gaps,
decompose the brief into specs, and chain `new-spec` → `work-loop`.

```
The brief looks good. Write it and hand off to receive-brief.
```

---

### What changes

**Reads:** the Milestone title and description; all linked issues (title,
description, labels, assignees). Requires the `gh` CLI installed; for private
repos, run `gh auth login` first.

**Writes:** `docs/product/briefs/<slug>.md` — only after you approve the draft.
`workspace.toml` is updated when `receive-brief` registers the brief in the queue.

Nothing else changes. The Milestone and issues in GitHub are never modified.

---

### Skills included — under the hood

You do not need to name these skills. They activate from natural-language requests.

| Skill | What it does |
| --- | --- |
| `github-brief-intake` | Reads a GitHub Milestone and its issues; maps them to a Shape B product brief; writes to `docs/product/briefs/` on approval; hands off to `receive-brief`. |
