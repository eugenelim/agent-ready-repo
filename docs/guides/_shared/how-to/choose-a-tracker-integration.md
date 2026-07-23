# Choose a tracker integration for brief intake

**Use this when:** You have work in a project board or issue tracker and want to turn it into a product brief that feeds the spec-driven build pipeline.
**Prerequisites:** The relevant pack installed (`core`, `github`, `linear`, or `atlassian`) and any required tracker credentials configured.
**Result:** The correct intake skill identified for your tracker and a `receive-brief`-ready path chosen.

You have work tracked in a project board or issue tracker and want to turn it into a
[product brief](../../core/reference/product-brief-fields.md) that feeds the
spec-driven build pipeline. Use this guide to choose the right intake skill.

## Decision table

| Where your work lives | Intake skill | Pack |
|---|---|---|
| No tracker — you have unstructured input (email, message, verbal) | `author-brief` | `core` |
| GitHub — work is in a **Milestone** with Issues | `github-brief-intake` | `github` |
| Linear — work is in an **Issue** (with sub-issues) or a **Project** | `linear-brief-intake` | `linear` |
| Jira — work is in an **Epic** | `jira-brief-intake` | `atlassian` |
| Jira Align — work is in a **Feature** | `jira-align-brief-intake` | `atlassian` |

Once the brief is created, all paths converge at `receive-brief` to elicit missing
fields, decompose into specs, and hand off to `work-loop`.

## One issue is not a brief

If the input is a single issue with no container (no milestone, no sub-issues, no
Feature children), that is one feature — use `new-spec` directly. The intake skills
will recommend this redirect and wait for your confirmation.

---

## No tracker — `author-brief`

**When to use it:** you have unstructured input — an email, a stakeholder message, a
Slack thread, a verbal description — that describes multi-feature work and is not yet
a formatted brief.

**Prerequisites:** `core` pack installed.

**What it does:** extracts signal from whatever you paste in, elicits missing
Definition of Ready fields conversationally, and writes a draft brief to
`docs/product/briefs/<slug>.md`.

**How to invoke it:** tell your agent about the work — paste the email or describe
the scope. The `author-brief` skill fires automatically on unstructured brief-level
input.

**Full guide:** [Intake an external brief](../../core/how-to/intake-an-external-brief.md)

---

## GitHub — `github-brief-intake`

**When to use it:** work is organised as a GitHub **Milestone** with related Issues.

**Prerequisites:**
- `github` pack installed
- `gh` CLI installed ([cli.github.com](https://cli.github.com))
- For private repos: `gh auth login`

**What it does:** pulls all Issues under the Milestone via `gh`, maps them to Shape B
user stories (`US-n (#NNN)`), stamps the Milestone URL as the `Epic:` provenance
pointer, writes the brief, and hands off to `receive-brief`.

**How to invoke it:**
```
github-brief-intake
```
or tell your agent: "Turn our Q3 milestone into specs."

**Full guide:** [Intake a GitHub Milestone as a brief](../../github/how-to/intake-a-github-milestone-as-a-brief.md)

---

## Linear — `linear-brief-intake` / `linear-brief-sync`

**When to use it:** work is organised in a Linear **Issue** (with sub-issues) or a
Linear **Project**.

**Prerequisites:**
- `linear` pack installed
- Linear Personal API Key stored via `credential-setup` (namespace `linear`, key `API_KEY`)
- Verify with `linear: check`

**What it does:**
- **First time:** `linear-brief-intake LIN-123` fetches the Issue and its sub-issues,
  maps them to Shape B stories (`US-n (LIN-NNN)`), stamps the owning Project URL as
  `Epic:`, registers the brief under `[brief_queue].draft` in `workspace.toml`, and
  hands off to `receive-brief`.
- **After a review round changes the Linear Issue:** `linear-brief-sync LIN-123
  docs/product/briefs/<slug>.md` re-fetches and shows you section-level before/after
  diffs; writes only the fields you approve.

**Full guide:** [When to use `linear-brief-intake` vs `linear-brief-sync`](../../linear/how-to/linear-brief-intake-and-sync.md)

---

## Jira — `jira-brief-intake`

**When to use it:** work is organised in a Jira **Epic**.

**Prerequisites:**
- `atlassian` pack installed
- Jira credentials stored via `credential-setup` (namespace `jira`)
- Verify with `jira: check`

**What it does:** fetches the Epic and its child Issues via the `jira` skill, maps
them to Shape B user stories (`US-n (PROJ-NNN)`), stamps the Epic URL as `Epic:`,
writes the brief to `docs/product/briefs/<slug>.md`, and hands off to `receive-brief`.
1-way intake only — never writes to Jira.

**How to invoke it:** tell your agent: "Turn PROJ-100 into a brief."

---

## Jira Align — `jira-align-brief-intake`

**When to use it:** work is organised in a Jira Align **Feature** (program-level delivery
unit — not to be confused with a Jira Software Epic, which maps to a Jira Align Feature).

**Prerequisites:**
- `atlassian` pack installed
- Jira Align credentials stored via `credential-setup` (namespace `jira-align`)
- Customise `references/field-mapping.md` in the skill directory for your instance's
  workflow state vocabulary and Program Increment cadence before first use.

**What it does:** fetches the Feature and its child stories, tasks, and defects via the
`jira-align` skill, maps children to Shape B user stories (`US-n (stories/<id>)`),
stamps the Feature ID as the `Epic:` provenance pointer, writes the brief, and hands
off to `receive-brief`. 1-way intake only.

**How to invoke it:** tell your agent: "Turn Jira Align Feature 4521 into a brief."

---

## After intake — the common path

Regardless of which intake path you used, `receive-brief` takes over from the draft
brief:

1. **Elicit** — fills missing Outcome / Scope conversationally.
2. **Decompose** — cuts stories into independently shippable specs; confirms the cut.
3. **Execute** — chains `new-spec` → `work-loop` per spec; stamps `Brief:` and
   `Satisfies: US-n` back-links.

See [Receive a product brief and decompose it into specs](../../core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md).

## See also

- [Tracker vocabulary](../reference/tracker-vocabulary.md) — how the same concept
  maps across GitHub, Linear, Jira, and Jira Align.
- [Product brief fields](../../core/reference/product-brief-fields.md) — the full field
  list for a product brief.
