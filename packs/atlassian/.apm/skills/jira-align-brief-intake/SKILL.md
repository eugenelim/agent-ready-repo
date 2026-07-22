---
name: jira-align-brief-intake
description: Use this skill when the user points at a Jira Align Feature and asks you to turn it into a product brief or shippable specs — "intake Feature 1234", "turn JA feature 789 into specs", "pull this Jira Align feature into a brief". The skill fetches the Feature and its child stories/tasks/defects via the `jira-align` skill, maps them onto a Shape B product brief (Feature title/description → Outcome, children → `US-n` user stories tagged with their Jira Align IDs, Feature ID → `Epic:` provenance pointer), writes it to `docs/product/briefs/<slug>.md`, and hands off to `receive-brief` to elicit gaps, decompose, and build. 1-way intake only — never writes back to Jira Align. Use the field mapping in `references/field-mapping.md` (customize for your org before first use). Do NOT use for defects (use `jira-defect-flow` for Jira defects) or for individual Jira issues (use `jira-brief-intake` for Jira epics).
metadata:
  version: "1.0"
---

# Skill: jira-align-brief-intake

This is choreography, not invention. It composes two things that already exist:

- **`jira-align` skill** (sibling in this pack) — all Jira Align reads.
  You never write a raw Jira Align REST call here and never invoke a write
  verb.
- **`receive-brief` skill** (shipped by the host repo; resolved by name
  through the harness) — owns Elicit (fill missing Outcome/Scope
  conversationally), Decompose (cut into shippable slices), and Execute
  (chain `new-spec` → `work-loop`). This skill does **not** reimplement
  elicitation; it hands off the assembled brief and steps back.

If you find yourself writing a Jira Align REST call or interrogating the
user for missing Outcome/Scope fields, stop — the right place is one of
the two above.

## One-time setup: customise the field mapping

Before first use on a new Jira Align instance, open
`references/field-mapping.md` and fill in:

1. **Workflow state vocabulary** — your instance's state names in the
   "Customize for your org" table. Standard names (`Planned`, `In Progress`,
   `Completed`) are pre-filled; replace or extend them.
2. **PI naming pattern** — the cadence label format your org uses (e.g.,
   `PI 2026-Q1`, `PI 24`).

This is a one-time step per instance. The brief this skill produces will be
wrong in the State context sentence if the state names don't match.

## Cross-skill invocation — name, not path

This skill names sibling skills (`jira-align`) and host skills
(`receive-brief`) **by their `name:` field, never by path**. Install
locations vary by IDE and scope. The contract: when this skill says *"via
the `jira-align` skill: `get features <ID> …`"*, the agent uses its native
skill-dispatch mechanism to invoke the skill registered under that name
with those arguments.

Install guidance for the named dependencies lives in `manifest.json` under
`deps.skills` — that's a *where to get them* hint, not a runtime path.

## Prerequisites

Before Stage 1, confirm:

1. The `jira-align` skill is installed and reachable. Invoke it:
   `jira-align: check`. Exit 0 → proceed. Exit 2 → tell the user to run
   `credential-setup` themselves (interactive — they run it, not you) and
   stop. `jira-align` is a hard dependency; there is no degraded path
   without it.
2. The `receive-brief` skill is installed (from `agent-ready-repo` or
   wherever the consumer keeps it). If not, note the absence — **do not
   stop**. The core-absent branch in Stage 4 handles this gracefully.

## Lifecycle

### Stage 1 — Intake

Fetch the Feature with all fields needed to populate the brief, via the
`jira-align` skill:

```
jira-align: get features <ID> --expand ownerUser,milestones
```

Check for the **three intake requirements** of a Feature:

| Requirement | Where it lives in Jira Align |
|---|---|
| Title (what this feature delivers) | `title` field |
| Description or scope notes | `description` and/or `notes` fields |
| Owner / program context | `ownerUser` (expanded), `programID` |

When any requirement is missing or empty, note the gap — don't stop.
`receive-brief` elicits what's missing in Stage 4.

### Stage 2 — Enumerate children

Fetch the Feature's child items by resource type:

```
jira-align: list stories --filter "featureID eq <ID>"
jira-align: list tasks --filter "featureID eq <ID>"
jira-align: list defects --filter "featureID eq <ID>"
```

Collect whichever resource types return results. A Feature with no children
is valid but thin — ask the user before proceeding (see Boundaries: Ask
first).

For each child item, record:
- Resource type: `stories`, `tasks`, or `defects`
- `id`
- `title` (the story text)

### Stage 3 — Map fields to brief

Using `references/field-mapping.md` as your guide, map the fetched data
onto the Shape B brief template.

**Heading and provenance:**

```
# Brief: <Feature title>

- **Slug:** `<kebab-case-slug>` (derive from the Feature title)
- **Received:** <today's date>
- **Owner:** <owner from ownerUser, or ask>
- **Status:** Draft
- **Epic:** <JIRAALIGN_BASE_URL>/features/<ID>
```

**Outcome** (load-bearing — do not leave empty):

Combine `description` and `notes` into one paragraph. When both are present,
lead with the description and append notes as context. When only one is
present, use it. When neither is present, write `[Outcome not provided —
receive-brief will elicit]` as a placeholder; do not invent.

Then append a one-line state context sentence using the mapping in
`references/field-mapping.md`'s state vocabulary table:

```
*(Current state: <state value> — <Brief handling from your org's mapping>)*
```

Example: `*(Current state: In Progress — active delivery)*`. When `state`
is absent from the Feature response, omit the line.

**Scope / In scope:**

When `acceptanceCriteria` is present on the Feature, use it as the In scope
prose. Otherwise leave the heading with an empty placeholder; `receive-brief`
elicits it.

**User stories (Shape B):**

Map each child to a `US-n` story line. The format is pinned:

```
- **US-n.** (stories/<id>) <story text>
```

Substitute `tasks/` or `defects/` for the resource type. For `<story text>`:
- Reshape the child's `title` into the *As a … / I want … / so that …*
  grammar **when the title itself contains a role and benefit** (e.g. "As a
  PM, track sprint velocity…"). Do not invent a role that isn't in the title.
- Carry the title verbatim when a role/benefit cannot be inferred — do not
  invent. `receive-brief` refines during Elicit.

The `US-n` index is sequential across all resource types, ordered by:
stories first, then tasks, then defects.

**Program Increment context (optional):**

When `milestones` expands to a PI record, add a one-line note in the brief's
`## Context` section (add the heading if absent):

```
> **Program Increment:** <PI name from milestones> — carry forward as
> appetite signal; confirm with `receive-brief`.
```

### Stage 4 — Write brief and hand off

Write the assembled brief to `docs/product/briefs/<slug>.md`. If the file
already exists, ask the user whether to merge or replace before writing.

**Core-present path (receive-brief installed):**

Hand off to `receive-brief` by name:

```
receive-brief: docs/product/briefs/<slug>.md
```

`receive-brief` elicits missing fields (Outcome gaps, Scope, Success
metrics, Appetite), runs DoR, decomposes, and chains into `new-spec` →
`work-loop`. Your role ends at the hand-off.

**Core-absent path (receive-brief not installed):**

When `receive-brief` is unavailable, inline the following instruction and
act on it directly:

> **Core-absent brief — act on this directly:**
>
> The brief at `docs/product/briefs/<slug>.md` is assembled from Jira Align
> data. Proceed as follows:
>
> 1. **Elicit missing fields.** Ask the user to fill in any empty headings
>    in the brief (Outcome gaps, Success metrics, Scope, Appetite).
> 2. **Decompose.** For each `US-n` story that warrants its own spec,
>    open `docs/specs/<feature-slug>/spec.md` and ask the user to confirm
>    the decomposition before proceeding.
> 3. **Execute.** For each confirmed spec, invoke `new-spec` by name (if
>    installed), then `work-loop`. If neither is installed, tell the user
>    which packs to install and stop.

## Don't

- Don't read `~/.agentbundle/credentials.env` from the skill body.
- Don't write a raw Jira Align REST call — use the `jira-align` skill.
- Don't invoke `create`, `update`, `delete`, or `raw` with a mutating
  method on the `jira-align` skill. Intake is read-only.
- Don't re-run `credential-setup` for the user or pipe the token into it.
- Don't reimplement `receive-brief`'s elicitation — hand off and step back.
- Don't invent Outcome, Scope, or story text the Jira Align source doesn't
  support. Surface the gap; let `receive-brief` elicit it.
- Don't reference this skill, `jira-align`, or `receive-brief` by path —
  always by name.
- Don't claim portability across all Jira Align instances without asking the
  adopter to customise `references/field-mapping.md` first.

## Edge cases

- **Feature not found (404):** the `jira-align` CLI exits 3 and prints the
  server message. Surface it to the user and stop — do not guess or
  substitute.
- **Credentials missing / expired (exit 2):** tell the user to re-run
  `credential-setup` and regenerate their API token on the Jira Align
  Profile page.
- **Feature with no children:** confirm with the user before assembling a
  brief from title + description alone — a Feature with no stories is
  unusual and may indicate the wrong ID or incomplete Jira Align data.
- **Custom fields:** Jira Align instances expose org-specific fields in
  responses. When a field named in `references/field-mapping.md`'s
  "Customize for your org" section is present in the Feature response, use
  it. When it is absent, skip it and note the gap in the brief.
- **Large child sets (> 100):** the `jira-align` CLI paginates transparently
  up to `--limit`. For features with many children, consider scoping the
  intake to a representative subset and noting the total count in the brief;
  confirm with the user.
