# Requests For Comments

> Proposals for change. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc)
> for when to open an RFC vs. an ADR vs. just opening a PR.

| #    | Title | Status | Opened     | Closed |
| ---- | ----- | ------ | ---------- | ------ |
| [0001](0001-one-bundle-three-layers.md) | One bundle, three layers — portable agent-template distribution | Accepted | 2026-05-21 | 2026-05-21 |

## Adding a new RFC

```bash
N=$(printf "%04d" $(( $(ls docs/rfc/ 2>/dev/null | grep -E '^[0-9]{4}' | sed 's/-.*//' | sort -n | tail -1 || echo 0) + 1 )))
cp docs/_templates/rfc.md docs/rfc/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-rfc "<title>"` (defined in `.claude/skills/new-rfc/SKILL.md`).
