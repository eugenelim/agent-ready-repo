# jira-brief-intake — canonical examples

Four shapes you'll meet most often. Replace `PROJ-100` etc. with values from
your environment. Every read here goes through the `jira` skill; this skill
issues **no** Jira write verb, so none appears below.

## Notation

These examples reference sibling skills **by name**, never by path. A line like
`jira: get-issue PROJ-100` means *invoke the skill registered under the name
`jira` with subcommand `get-issue` and the given args*. How that dispatch
happens depends on the IDE:

- **Claude Code**: the Skill tool, or `/jira get-issue PROJ-100` (and similarly
  for `receive-brief`).
- **Cursor / Kiro / Codex / Gemini**: the IDE's skill/rule invocation equivalent.
- **Raw CLI** (no IDE): `cd` to the `jira` skill's install dir and run
  `python scripts/jira.py get-issue PROJ-100`. Where that dir lives depends on
  where the user installed the skill.

Path locations like `~/.claude/skills/jira/...` are install-time details, not
contract.

---

## 1. Epic with children — the happy path

User: *"Turn PROJ-100 into specs."*

```
# Prerequisites
jira: check                      # exit 0 → proceed
# (probe that `receive-brief` is dispatchable → present → normal flow)

# Stage 1 — intake
jira: get-issue PROJ-100 --fields "summary,description,labels,issuetype,status" --expand renderedFields

# Enumerate children — try the team-managed form first, fall back to Epic Link:
jira: search "parent = PROJ-100 ORDER BY created ASC" --fields "summary,description,issuetype,status"
# → returns PROJ-101, PROJ-102, PROJ-103
```

Stage 2 writes `docs/product/briefs/team-billing-portal.md` (slug from the epic
summary), Shape B:

```markdown
# Brief: Team admins manage their own billing

- **Slug:** `team-billing-portal`
- **Received:** 2026-06-15
- **Owner:** billing team
- **Epic:** PROJ-100

## Outcome
<from PROJ-100's description — the problem and what changes for admins>

## Scope / Non-goals
**In scope:** <from the epic description, where stated>
**Non-goals:** <where stated; else leave for receive-brief to elicit>

## User stories
- **US-1.** (PROJ-101) As an admin, I want to change my team's plan, so that I don't email support.
- **US-2.** (PROJ-102) As an admin, I want to update payment methods self-serve.
- **US-3.** (PROJ-103) Download past invoices as PDF.   <!-- summary carried verbatim; not story-shaped -->

## Spec map
| Spec | Status |
| --- | --- |
| `<feature-slug>` | <auto> |
```

Stage 3 hands off: `receive-brief: docs/product/briefs/team-billing-portal.md`.
`receive-brief` elicits the missing Outcome/metrics, decomposes the three
stories into slices, and chains `new-spec` → `work-loop`.

---

## 2. Board / sprint / JQL selection — no single epic

User: *"We run a kanban board; turn the 'Q3 onboarding' epic-less backlog into specs."*

Kanban teams often have no parent epic. The user gives a JQL (or a saved filter
/ board scope); the matched issues become the stories.

```
jira: search "project = ONB AND labels = q3-onboarding ORDER BY rank ASC" --fields "summary,description,issuetype,status"
# → ONB-12, ONB-15, ONB-18, ...
```

There's no parent to derive the **Outcome** from. Write the stories
(`- **US-1.** (ONB-12) …`) and **leave Outcome as a surfaced gap** — do not
invent one. `Epic:` is omitted (there is no coordinator). Hand off; `receive-brief`
elicits the Outcome from the user before it decomposes.

---

## 3. A single non-epic issue — recommend `new-spec`

User: *"Make a brief from PROJ-250."* — but `PROJ-250` is a single Story with no
children.

```
jira: get-issue PROJ-250 --fields "summary,issuetype,status"
# issuetype = Story; a child query returns nothing
jira: search "parent = PROJ-250" --fields summary     # → empty
jira: search '"Epic Link" = PROJ-250' --fields summary  # → empty (or field-missing error)
```

One issue is one feature, not a multi-feature brief. **Stop and recommend
`new-spec`** (or `jira-defect-flow` if it's a defect), and ask before treating
it as a brief:

> PROJ-250 is a single Story with no children — that's one feature, which
> `new-spec` handles directly. Want me to scaffold a spec from it instead, or
> did you mean a different (epic) key?

---

## 4. `receive-brief` not installed — graceful degradation

User: *"Turn PROJ-100 into specs"* — but the `core` pack isn't installed, so the
Prerequisites probe finds no `receive-brief`.

Stages 1–2 are unchanged: you still pull the epic + children and write the brief
(using the **carried shape** in `SKILL.md`, since core's `_template.md` is also
absent). Stage 3 is replaced by stage 4: instead of handing off, you inline the
decompose/execute instruction for the agent to act on, and note that `new-spec`
/ `work-loop` may also be absent:

> Wrote `docs/product/briefs/team-billing-portal.md` from PROJ-100 and its three
> children. `receive-brief` isn't installed, so I'll continue inline: first I
> need the Outcome (PROJ-100's description is thin) — what changes for admins
> when this ships? Then I'll cut the three stories into independently-shippable
> slices, surface the cut for your sign-off, and author each through this repo's
> spec process (`new-spec` if present, else the repo's equivalent).

The brief is still the durable artifact; only the hand-off degraded to an
inlined instruction.
