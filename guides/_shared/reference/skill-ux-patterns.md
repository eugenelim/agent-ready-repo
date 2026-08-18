---
title: Skill UX patterns
summary: Apply the detailed alignment, truncation, command-bar, confirmation, card, and progress patterns used by structured skill output.
pack: _shared
kind: reference
---

# Skill UX patterns

Craft-depth companion to [Output rendering directives](output-rendering.md). That document defines which rendering shape to declare in `## Output rendering` (Table, Status list, Diagram, etc.) and the canonical glyph set. **This page covers the craft rules within each shape**: column alignment, truncation limits, the persistent command bar pattern, the delete-gate box, card format for review flows, and progress reporting. Read both when authoring a skill that surfaces structured output in chat.

## Where to declare

Any skill that surfaces structured output in chat must include an `## Output rendering` section in its SKILL.md body, placed **before the first procedural `##`**. Declare there: what columns appear and their alignment rules, which status glyphs the skill uses, truncation limits, and whether it maintains a persistent command bar. The body's procedural sections then refer back to this contract rather than repeating rendering decisions inline.

## Status glyphs

Use this set consistently — never invent new glyphs, never use emoji for status:

| Glyph | Meaning |
|-------|---------|
| `●`   | In progress / running |
| `✓`   | Done / complete |
| `○`   | Idle / waiting / pending |
| `⚠`   | Blocked / needs attention |

Lead each status row with the glyph: `● Scanning messages…`, `✓ Inbox processed`. For auth and session steps, one item per line with the glyph aligned:

```
● Opening session…
✓ Session authenticated
○ Waiting for user action
```

## Column alignment

- **Right-align** numeric columns, age/date columns, and rank/position columns — use `---:` in the separator row.
- **Left-align** text columns (names, topics, previews).
- Cap tables at ~5 columns. Beyond that, switch to a per-item detail list.

```markdown
| # | Sender | Topic | Age | Count |
|--:|--------|-------|----:|------:|
| 1 | Example Corp | Contract renewal | 3d | 12 |
```

## Truncation limits

Apply these limits to columns that show free-form text. They are guides, not hard character counts — the goal is a readable table at typical chat widths.

| Column type | Limit | Tail form |
|-------------|-------|-----------|
| Sender / name | ≤ 28 chars | `… ` |
| Subject / topic | ≤ 40 chars | `… ` |
| Preview / summary | ~ 55 chars | `… ` |
| Table row count | 30 rows | `… N more <type>` |

The tail row always appears on its own line after the table: `… 14 more senders`.

## Persistent command bar

Any skill that drives a stateful multi-step workflow (queue triage, thread review, session management) must end **every response** with the command bar for the current context — even when not prompting for input. The user should never need to ask what they can do next.

Format — one line, arrow lead, actions in brackets, separator `·`, quit last:

```
→ [r]ead thread · [a]rchive · [s]nooze · [b]ack · [q]uit
```

The bar changes as context changes. At a queue it shows queue-level verbs; inside a thread it shows thread-level verbs. Always rebuild it for the current state rather than carrying a stale bar from the previous step.

## Delete-gate box

Any destructive irreversible action must be gated by a confirmation box before execution. Show the box, wait for the user to type `yes`, then act. Never proceed on any other input.

```
┌─ DELETE GATE ─────────────────────────────────────────────────────┐
│ Scope:        [what will be deleted — senders, files, rows]       │
│ Count:        N [items]  (from dry-run)                           │
│ Risk:         VERY LOW · LOW · MEDIUM · HIGH                      │
│ Reversible:   Yes — [where items go] · No — [what is lost]        │
│                                                                   │
│ Type "yes" to proceed, anything else to cancel.                   │
└───────────────────────────────────────────────────────────────────┘
```

**Risk ratings:**
- `VERY LOW` — reversible, affects only data the user flagged explicitly, no side-effects
- `LOW` — reversible, bulk operation on a filtered set
- `MEDIUM` — partially reversible, or affects data beyond what the user named
- `HIGH` — irreversible, or affects shared/external state

Always include a dry-run count from a preceding read-only pass — never ask to delete `N items` when you haven't yet confirmed what N is.

## Card format — one-by-one review flows

When walking through items one at a time (a review queue, a triage flow), use a consistent card layout so the user always knows their position and what to do:

```
[n/N] <title / sender>  ·  <count>  ·  <recency>
<Tier: X>  ·  <flag>  ·  <flag>
Preview:  "<truncated preview text…>"

[d]elete  [k]eep  [m]ove → [action]  [s]kip  →
```

- The position header `[n/N]` appears on the first line — always.
- Metadata (tier, flags) goes on the second line — keep it to two or three short tokens.
- Preview is truncated per the limits above.
- Action row is the persistent command bar for this item's context.

## Progress reporting

Report progress inline — no bars:

```
Scanning page 3/10 (142 messages so far)
```

For multi-phase work, include the phase:

```
Phase 2/3: Classifying senders (38/200)
```

Never draw ASCII progress bars — they don't render consistently across chat surfaces.
