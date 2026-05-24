# Requests For Comments

> Proposals for change. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc)
> for when to open an RFC vs. an ADR vs. just opening a PR.

| #    | Title | Status | Opened     | Closed |
| ---- | ----- | ------ | ---------- | ------ |
| [0001](0001-bundle-distribution-by-adapter-spec.md) | Bundle distribution by adapter spec + ecosystem build pipeline | Accepted | 2026-05-21 | 2026-05-22 |
| [0002](0002-self-hosting.md) | Self-hosting via the ecosystem build pipeline | Accepted | 2026-05-21 | 2026-05-22 |
| [0003](0003-spec-and-cli.md) | Adapter contract publication + reference CLI | Accepted | 2026-05-21 | 2026-05-22 |
| [0004](0004-install-scope-per-pack.md) | Install-scope dimension — repo or user — defaulted and constrained per pack | Draft | 2026-05-23 | |
| [0005](0005-user-scope-hook-support.md) | User-scope hook support — body reroot + wiring merge mode | Draft | 2026-05-23 | |
| [0006](0006-skill-secrets-storage.md) | Credential storage for credentialed skills — tiered env/keyring/dotfile + two-layer architecture | Accepted | 2026-05-24 | 2026-05-24 |

## Adding a new RFC

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-rfc/scripts/next-ordinal.py docs/rfc)
cp .claude/skills/new-rfc/assets/rfc.md docs/rfc/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-rfc "<title>"` (defined in `.claude/skills/new-rfc/SKILL.md`).
