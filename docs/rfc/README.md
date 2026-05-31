# Requests For Comments

> Proposals for change. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc)
> for when to open an RFC vs. an ADR vs. just opening a PR.

| #    | Title | Status | Opened     | Closed |
| ---- | ----- | ------ | ---------- | ------ |
| [0001](0001-bundle-distribution-by-adapter-spec.md) | Bundle distribution by adapter spec + ecosystem build pipeline | Accepted | 2026-05-21 | 2026-05-22 |
| [0002](0002-self-hosting.md) | Self-hosting via the ecosystem build pipeline | Accepted | 2026-05-21 | 2026-05-22 |
| [0003](0003-spec-and-cli.md) | Adapter contract publication + reference CLI | Accepted | 2026-05-21 | 2026-05-22 |
| [0004](0004-install-scope-per-pack.md) | Install-scope dimension — repo or user — defaulted and constrained per pack | Accepted | 2026-05-23 | 2026-05-23 |
| [0005](0005-user-scope-hook-support.md) | User-scope hook support — body reroot + wiring merge mode | Accepted | 2026-05-23 | 2026-05-25 |
| [0006](0006-skill-secrets-storage.md) | Credential storage for credentialed skills — tiered env/keyring/dotfile + two-layer architecture | Accepted | 2026-05-24 | 2026-05-24 |
| [0007](0007-user-scope-converter-pack.md) | First user-scope pack — `converters` (file-to-markdown, markdown-to-html, msg-to-markdown) | Accepted | 2026-05-24 | 2026-05-24 |
| [0008](0008-claude-plugins-install-route-parity.md) | Claude-plugins install-route parity — per-pack SessionStart writer for the install→adapt chain | Accepted | 2026-05-24 | 2026-05-25 |
| [0009](0009-codex-native-skills.md) | Migrate Codex adapter from managed-block AGENTS.md to native `.agents/skills/` | Accepted | 2026-05-25 | 2026-05-25 |
| [0010](0010-apm-install-route-parity.md) | APM install-route parity — per-pack SessionStart writer projected through APM's HookIntegrator | Accepted | 2026-05-25 | 2026-05-25 |
| [0011](0011-pack-allowed-adapters.md) | Per-pack `allowed-adapters` declaration for user-scope adapter resolution | Accepted | 2026-05-25 | 2026-05-26 |
| [0012](0012-repo-scope-per-adapter-projection.md) | Repo-scope per-adapter projection — `--adapter` at `--scope repo`, dist-tree opt-in via `--emit-install-routes` | Draft | 2026-05-26 | |
| [0013](0013-credential-broker-contract.md) | Credential broker contract — in-process shim for static tokens, adapter-root subprocess for SSO; formalise four-broker model | Draft | 2026-05-26 | |
| [0014](0014-answer-first-rfc-format-and-drafting-flow.md) | Answer-first RFC format + research-and-de-risk drafting flow for `new-rfc` | Accepted | 2026-05-28 | 2026-05-28 |
| [0015](0015-wave-scheduled-supervisor-mode.md) | Wave-scheduled supervisor mode — topological-order default, parallel writes opt-in and gated on measured file-disjointness | Accepted | 2026-05-28 | 2026-05-29 |
| [0016](0016-doc-drift-mechanical-gate.md) | Doc-drift prevention — construction + judgment (template / reviewer / DECIDE / CONVENTIONS / in-repo backlog), with a catalogue-governance linter | Draft | 2026-05-29 | |
| [0017](0017-pluggable-api-contract-standards.md) | Pluggable API-contract standards (base+delta, Zalando as starter) + a contract-type-agnostic `new-spec` seam | Accepted | 2026-05-30 | 2026-05-30 |
| [0018](0018-event-asyncapi-authoring-engine.md) | Event/AsyncAPI authoring engine for `contracts` — `event-contract` skill (AsyncAPI 3.1.0 + CloudEvents 1.0.2 envelope, Zalando event rules as starter) | Accepted | 2026-05-31 | 2026-05-31 |

## Adding a new RFC

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-rfc/scripts/next-ordinal.py docs/rfc)
cp .claude/skills/new-rfc/assets/rfc.md docs/rfc/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-rfc "<title>"` (defined in `.claude/skills/new-rfc/SKILL.md`).
