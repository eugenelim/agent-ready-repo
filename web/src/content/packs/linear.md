---
name: Linear
scope: user
tagline: "Turn a Linear Issue into a product brief and keep it in sync"
skills:
  - linear
  - linear-brief-intake
  - linear-brief-sync
installCommand: "agentbundle install --pack linear --scope user"
docsUrl: /guides/linear/
---

Turns a Linear Issue or Project into a structured product brief, then keeps
the brief in sync as the Issue evolves. Read-only during the review — nothing
is written until you confirm the draft or the sync diff.

**The agent never sees your API key.** Credentials resolve in-process via
the `credential-brokers` pack.

---

Try this first:

```
Run linear check to confirm my credentials.
```

What you get: credentials confirmed — workspace name and your identity shown.
Nothing changed, nothing written to Linear.

---

### What you can do

**Turn an Issue into a product brief**

Point the agent at a Linear Issue or Project ID. It reads the issue,
maps it onto a structured brief (problem statement, user jobs, acceptance
criteria), and presents the draft for your review.

```
Intake Linear issue LIN-456 as a product brief.
```

---

**Keep the brief in sync**

When the Linear Issue changes after the brief is written, run `linear-brief-sync`
to pull the delta. It shows only the fields that changed, section by section,
and waits for your approval before writing anything.

```
Sync the brief for LIN-456 with the latest changes in Linear.
```

`linear-brief-sync` refuses to run if the brief status is `Executing` — it
won't modify a brief that engineering is actively building against.

---

**Hand off to the build queue**

After you approve the brief, `receive-brief` elicits any gaps, decomposes
into specs, and chains `new-spec` → `work-loop`.

```
The brief looks good. Hand it off to receive-brief.
```

---

### What changes

**Reads:** the Linear Issue or Project via the `linear` primitive (credentialed
GraphQL). The API key is stored under namespace `linear` via `credential-setup`
and never passed to the model.

**Writes:** `docs/product/briefs/<slug>.md` — on initial intake, after your
approval. `workspace.toml` is updated when the brief enters the queue.
Linear-sourced fields in an existing brief — on sync, only the fields you
approve.

Nothing is written to Linear. Issues and Projects in Linear are never modified.

---

### The sync lifecycle

Issue created → `linear-brief-intake` → brief at `Draft` → `receive-brief` →
specs + `work-loop` → brief at `Executing` → Issue updated in Linear →
`linear-brief-sync` (only when brief is not `Executing`) → approved delta
applied → brief updated

---

### Skills included — under the hood

You do not need to name these skills. They activate from natural-language requests.

| Skill | What it does |
| --- | --- |
| `linear` | Credentialed GraphQL primitive — `check`, `get-issue`, `get-project` subcommands. The agent never sees the API key. |
| `linear-brief-intake` | First-time intake: reads an Issue or Project via `linear`, maps to a product brief, writes to `docs/product/briefs/` on approval, hands off to `receive-brief`. |
| `linear-brief-sync` | Delta catch-up: re-fetches the Issue, diffs Linear-sourced fields against the existing brief, presents section-level changes for your approval. Refuses when brief is `Executing`. |
