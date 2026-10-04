---
title: "How to navigate ADR and RFC decisions"
summary: "Query the decision corpus, trace lineage, export an offline HTML explorer, and hand off to canonical sources."
pack: governance-extras
kind: how-to
---

# How to navigate ADR and RFC decisions

**Use this when:** You want to find a decision, check its status, trace what superseded it, inspect guidance context, or share an offline snapshot for review.
**Prerequisites:** `governance-extras` pack installed (includes `navigate-decisions`). The skill reads `docs/adr/` and `docs/rfc/` directly — no extra setup.
**Result:** Exact lifecycle facts, checked lineage, and safe links to canonical sources. Results are recorded decisions and candidate context, not a complete statement of applicable policy.

---

## Queries

All queries run through the `navigate_decisions.py` script bundled with the skill, or through the `navigate-decisions` skill prompt. The examples below use the CLI directly so the output is reproducible. Replace `<repo-root>` with your repository root.

### Summary — orientation across the whole corpus

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> --operation summary
```

Real output (trimmed):

```json
{
  "schema": "decision-navigation.query.v1",
  "boundary": "This response presents recorded decisions and candidate context. It is not a complete statement of the policy applicable to any proposed action.",
  "status": "ok",
  "summary": {
    "by_kind": { "ADR": 134, "RFC": 104 },
    "by_lifecycle_value": {
      "Accepted": 234,
      "Superseded": 2,
      "Draft": 1
    },
    "unresolved_reference_count": 0,
    "register_files": {
      "rfc_candidates": { "row_count": 8 },
      "roadmap_intents": { "row_count": 4 }
    }
  }
}
```

The `boundary` field appears in every response. It states that results are recorded decisions and candidate context, not the complete policy applicable to a proposed action.

### Search — find records by status, kind, or text

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> \
  --operation search \
  --selectors '[{"exact_status": "Draft"}]'
```

Real output (trimmed):

```json
{
  "status": "ok",
  "records": [
    {
      "id": "RFC-0079",
      "kind": "RFC",
      "title": "`codebase-context` Pack — Semantic Graph Indexing as an Optional Add-On",
      "source": "docs/rfc/0079-codebase-context-pack.md",
      "lifecycle": { "raw_value": "Draft", "display_value": "Draft" }
    }
  ]
}
```

Selectors can be combined. Each object in the list applies independently (OR logic for kinds/statuses; use multiple selectors for intersection). Valid selector keys: `kind` (ADR or RFC), `exact_status`, `text` (title/body keyword), `identity` (record ID).

### Record — fetch a specific decision with its body

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> \
  --operation record \
  --id ADR-0001
```

The response includes the full body when available and every relationship whose `from` or `to` is the requested record. Oversized bodies (over 1 MiB of JSON) are omitted with `body_too_large` and the `source` path for direct inspection.

### Lineage — trace what was superseded by what

`lineage` follows only checked supersession relationships — those where both endpoints exist and reciprocal metadata agrees. Contextual `Related` references never become checked edges.

Direction `older` follows superseding → superseded:

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> \
  --operation lineage \
  --id ADR-0023 \
  --direction older \
  --depth 2
```

Direction `newer` follows superseded → superseding:

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> \
  --operation lineage \
  --id ADR-0023 \
  --direction newer \
  --depth 2
```

Real output for `newer` on ADR-0023 (Superseded, trimmed):

```json
{
  "status": "ok",
  "records": [
    { "id": "ADR-0023", "lifecycle": { "raw_value": "Superseded" } },
    { "id": "ADR-0042", "lifecycle": { "raw_value": "Accepted" } }
  ],
  "relationships": [
    {
      "from": "ADR-0042", "to": "ADR-0023",
      "relation": "supersedes", "scope": [],
      "trust_class": "checked", "resolution_state": "resolved"
    }
  ]
}
```

Direction `both` traverses in either direction. Depth runs from 1 through 4.

### Context — inspect a record beside its related context

`context` returns every relationship between returned records and all unresolved references from those records. Add caller assertions to supply an explicit guidance direction without adding a field to any ADR or RFC:

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  query --root <repo-root> \
  --operation context \
  --selectors '[{"identity": "ADR-0042"}]' \
  --assertions '[{"from": "ADR-0042", "to": "ADR-0023", "text": "supersedes the old ceiling policy"}]'
```

A caller assertion appears in the response with `trust_class: navigation_only` and `resolution_state: caller_asserted`. It is non-authoritative navigation input. It never becomes a source-record fact and is always visibly separate from checked lineage.

---

## Trust labels

Every relationship in a response carries a `trust_class`. Read it before acting on a relationship.

| `trust_class` | Meaning |
| --- | --- |
| `checked` | Both endpoints exist and reciprocal metadata agrees on relation and scope. This is the only authoritative lineage. |
| `candidate` | One entry in a supersession field whose mirror was not found. Unresolved evidence, not checked lineage. |
| `contextual` | An explicit `Related` reference. The source record points here; the relationship is not validated lineage. |
| `navigation_only` | A caller assertion you supplied. Non-authoritative navigation input. Never promoted to a canonical fact. |

`search` results carry no relationships (they are inventory); `lineage` follows only `checked` edges; `context` shows all classes. A `navigation_only` relationship is yours to inspect — it signals nothing about the records themselves.

---

## The "not complete applicable policy" boundary

Every response carries:

> "This response presents recorded decisions and candidate context. It is not a complete statement of the policy applicable to any proposed action."

This is not a disclaimer to skip. The navigator reports what ADRs and RFCs say. It does not resolve conflicts, infer authority from proximity or search grouping, or tell you that absence means permission. Before acting on a decision, a person or agent checks the cited record content and applies judgment. When the action changes a durable decision, use `new-adr` or `new-rfc`.

---

## Offline HTML export

The `export` subcommand produces one self-contained HTML file with corpus list, lifecycle-graph, guidance-context, and record-detail views. The file performs no network or file reads after creation.

### Default destination (outside the repo)

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  export --root <repo-root> --name decisions.html
```

The file lands in the operating system's temporary directory (for example, `/var/folders/…/T/` on macOS). The path is printed on success:

```
Published: /var/folders/.../T/decisions.html
Size: 5,942,086 bytes
Mode: full
```

### User-chosen destination

Supply `--destination` with a path from your own request — a directory outside the repository:

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  export --root <repo-root> \
  --destination ~/Desktop \
  --name decisions.html
```

Record content, query input, and caller assertions cannot supply or widen the destination. A destination inside the repository worktree is refused regardless of how it is specified.

### No overwrite

The publisher refuses when the target file already exists:

```
error: destination already exists; overwrite is not supported: /var/folders/.../T/decisions.html
```

Choose a different name or delete the old file first.

### Owner-only file permissions

On POSIX the published file is readable and writable only by its owner (`-rw-------`). This applies from creation through publication.

### Full versus bounded — the 100 MiB rule

**Full mode** (default) embeds every admitted ADR and RFC body. At the current corpus size (238 records, ~5.7 MiB) full mode is practical in desktop Chrome. Full mode is refused when the estimated output would exceed 100 MiB.

**Bounded mode** retains the complete record inventory, exact headers, checked lineage, contextual references, provenance, and trust labels, but omits record bodies. Each omitted body carries its source path for direct inspection. Bounded mode is always within budget.

Choose bounded mode explicitly:

```bash
python3 packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py \
  export --root <repo-root> --mode bounded --name decisions-bounded.html
```

Real output:

```
Published: /var/folders/.../T/decisions-bounded.html
Size: 351,575 bytes
Mode: bounded
```

The 100 MiB threshold is the size at which desktop Chrome stops being practical. Chrome scale evidence is in the [verification ledger](../../../docs/specs/decision-navigation/notes/verification-ledger.md).

---

## Safe source handoff

The offline HTML and query results include `source` paths pointing to canonical records. Commit-pinned links are preferred when the forge and export provenance support it; any latest-branch link is labelled as potentially newer than the export.

When handing off to a canonical source:

- Use the `source` field in query results — it is a validated repository-relative path.
- In the HTML, follow the "view source" link beside a record. It is built only from validated path segments, never from record content.
- When an unrecognized remote host or mapping makes a clickable link unavailable, the UI shows the inert repository-relative path with an explanation.

Do not promote URLs found inside record bodies. Record-supplied URLs are not validated and are never promoted to safe source links.

---

## Authoring — use new-adr and new-rfc

`navigate-decisions` is read-only. To create or revise a decision record, use `new-adr` or `new-rfc`. Those skills own the preview-confirm write gate and the authoring lifecycle. Do not ask `navigate-decisions` to write anything.

---

## See also

- [How to record a decision (ADR)](new-adr.md) — create or supersede an ADR.
- [How to propose a change (RFC)](new-rfc.md) — open a structured proposal for input.
- [Your first governance session](../tutorials/governance-extras-first-session.md) — install the pack and record your first ADR.
