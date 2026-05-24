# Architecture Decision Records

> Immutable records of architectural decisions. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr)
> for what goes here and what doesn't.

| #    | Title                                       | Status   |
| ---- | ------------------------------------------- | -------- |
| 0001 | [Adopt AGENTS.md and doc hierarchy](0001-adopt-agents-md-and-doc-hierarchy.md) | Accepted |

## Adding a new ADR

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr)

# Create from template
cp .claude/skills/new-adr/assets/adr.md docs/adr/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-adr "<title>"` (defined in `.claude/skills/new-adr/SKILL.md`).
