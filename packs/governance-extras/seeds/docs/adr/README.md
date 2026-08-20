# Architecture Decision Records

> Immutable records of architectural decisions. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr)
> for what goes here and what doesn't.

| #    | Title                                       | Status   |
| ---- | ------------------------------------------- | -------- |
<!-- no ADRs yet -->

## Adding a new ADR

```bash
# Find the next number (portable across macOS, Linux, native Windows).
# Point SKILL at wherever your agent installed the `new-adr` skill.
SKILL=<path to the installed new-adr skill>
N=$(python3 "$SKILL/scripts/next-ordinal.py" docs/adr)

# Create from template
cp "$SKILL/assets/adr.md" "docs/adr/${N}-<kebab-title>.md"
```

Or invoke the `new-adr` skill by name in your agent.
