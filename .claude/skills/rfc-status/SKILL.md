---
name: rfc-status
description: "Surface the current RFC landscape at a glance — how many RFCs are in each lifecycle state, which are active, and how many findings are waiting in the candidate register. Triggers on 'rfc status', 'show rfcs', 'what rfcs are open', 'rfc dashboard', 'how many rfcs', 'rfc candidates', 'rfc report', or any request for an overview of the RFC landscape. Read-only: never creates or modifies RFC files."
---

# /rfc-status

Surface the current RFC landscape in one pass. Useful at session start (with
`workspace-status`) or any time you need to know what governance work is in
flight before proposing or opening a new RFC.

## When to invoke

Any request for an RFC overview: "what RFCs are active?", "rfc status", "show
me open rfcs", "how many rfcs do we have?", "any rfc candidates?". Also runs
as a sub-step of `workspace-status` to populate the findings count line.

## Procedure

### 1. Scan `docs/rfc/*.md`

Read every `.md` file in `docs/rfc/`. For each file, extract the `**Status:**`
front-matter line. The valid lifecycle states per CONVENTIONS.md §3 are:

```
Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental | Superseded
```

`Shipped` is a spec status, not an RFC status — if encountered, treat as
unrecognised and surface in a `⚠ Unrecognised status` group.

Group results by state. Within each group, list RFCs as:
`RFC-NNNN: <title>` (derive title from the first `# RFC-NNNN: …` heading).

### 2. Scan `docs/product/findings/rfc-candidates.md`

If the file exists, count the non-header data rows in the register table
(rows that are not the separator `|---|…` row or the header row). Surface the
count separately — this is not a lifecycle state but a holding queue for
candidate ideas.

### 3. Scan `docs/product/findings/roadmap-intents.md`

Same as step 2: count non-header data rows.

### 4. Surface results

Format output with the following sections (omit groups with zero entries):

---

**RFC landscape — `docs/rfc/`**

Active (in-flight):

| State | RFCs |
|---|---|
| Draft | RFC-NNNN: … |
| Open | RFC-NNNN: … |
| Final Comment Period | RFC-NNNN: … |
| Experimental | RFC-NNNN: … |

Resolved:

| State | Count |
|---|---|
| Accepted | N |
| Rejected | N |
| Withdrawn | N |
| Superseded | N |

**Findings registers — `docs/product/findings/`**

- RFC candidates: N entries (add via `work-loop` deferral or `frame-situation` escalation)
- Roadmap intents: N entries (add via `work-loop` deferral)

---

If `docs/rfc/` does not exist: surface a one-line note — "No `docs/rfc/`
directory found — run `new-rfc` to create the first RFC."

If `docs/product/findings/` does not exist: omit the Findings registers
section without error.

## What this skill is not

- Not `new-rfc` — it only reads; it never creates or modifies.
- Not `workspace-status` — it gives the RFC/findings slice only; `workspace-status` gives the full queue picture.
