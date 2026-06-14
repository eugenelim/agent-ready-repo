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
| [0019](0019-product-brief-intake.md) | Product-brief intake + LLD-aware spec/plan — `brief` artifact + `receive-brief` skill (own-the-repo-slice) and a stack-neutral, stack-derived `## Design (LLD)` in spec/plan | Accepted | 2026-06-01 | 2026-06-01 |
| [0020](0020-reference-architecture-foundation.md) | Reference-architecture foundation — normative `docs/architecture/reference.md` golden path (arc42), **template-instantiated on demand** (not core-seeded — avoids guaranteed stack-pack collisions); populated by stack pack / brownfield harvest / greenfield `init-project`; the LLD's steering | Accepted | 2026-06-01 | 2026-06-01 |
| [0021](0021-greenfield-inception.md) | Greenfield inception — the idea→repo front-door (research + value gate → foundation → walking skeleton), the greenfield twin of `adapt-to-project`; composes brief/foundation/spec, declines autonomous generation | Accepted | 2026-06-01 | 2026-06-01 |
| [0022](0022-kiro-adapter-split.md) | Split `kiro` adapter into `kiro-ide` (default, VS Code-fork IDE) and `kiro-cli` (terminal binary); `kiro` kept as deprecated alias; contract v0.8→v0.9; errata to RFC-0005 | Open | 2026-06-01 | |
| [0023](0023-credential-manager-broker.md) | `credbroker` — replace RFC-0013's build-projected stdlib shim with a standalone pip-installable in-process credential library (stdlib core + optional `[crypto]` encrypted vault); phased repo-path→PyPI; env Tier-1 kept as the pip-free floor; daemon/proxy (authsome) out of scope; **reverses ADR-0003** | Accepted | 2026-06-03 | 2026-06-03 |
| [0024](0024-copilot-subagent-projection.md) | Copilot full-parity projection — agents + hooks `dropped`→first-class, user-scope-capable (`~/.copilot/`), packs adapted (`research`/`core`); contract v0.9→v0.10; **supersedes RFC-0012 copilot-scope decision** | Accepted | 2026-06-04 | 2026-06-04 |
| [0025](0025-work-loop-light-mode-and-risk-based-escalation.md) | `work-loop` light mode (lean inline spec + single adversarial pass + no state machine) as the default + risk-based escalation replacing the file-count trigger; subtraction-shaped, no new skill/script/artifact | Accepted | 2026-06-05 | 2026-06-05 |
| [0026](0026-cursor-full-parity-adapter.md) | Cursor full-parity distribution adapter — project all primitives to `.cursor/*` (+ `~/.cursor/*`); first-class commands (`.cursor/commands/`), single-file `hooks.json` merge, agent tool-allowlist degraded to `readonly`; contract v0.10→v0.11; distribution-only | Accepted | 2026-06-11 | 2026-06-11 |
| [0027](0027-gemini-cli-full-parity-adapter.md) | Gemini CLI full-parity distribution adapter — project all primitives to `.gemini/*` (+ `~/.gemini/*`); keep+map agent `tools:` allowlist, tier-preserving model map (`opus→gemini-2.5-pro`/`sonnet→gemini-2.5-flash`/`haiku→gemini-2.5-flash-lite`), new `gemini-command-toml` mode (TOML commands), `AGENTS.md` `context.fileName` bridge, zero-drop hook-event mapping; distribution-only | Accepted | 2026-06-11 | 2026-06-11 |
| [0028](0028-tdd-stub-generation-in-the-core-loop.md) | TDD stub generation woven into the core loop — a load-on-demand `work-loop/references/tdd-stubs.md` turns each TDD-mode acceptance criterion into a compilable, validated red stub in `plan.md` during PLAN's *Design tests up front* step, consumed by EXECUTE; `new-spec` feeds it via a testability self-check. No new skill, no new gate, no new artifact | Accepted | 2026-06-11 | 2026-06-12 |
| [0029](0029-strengthen-security-reviewer.md) | Strengthen the `security-reviewer` — current multi-framework checklist (OWASP Top 10:2025 / ASVS 5.0 / API Top 10:2023 / LLM Top 10:2025 / CWE Top 25 / LINDDUN) delivered via an orchestrator-loaded progressive-disclosure `security-checklists` skill (depth without prompt bloat, ships to every adapter), plus a shift-left spec-stage secure-design mode wired into `work-loop` pre-EXECUTE; three-bucket tool-delegation with Tier-1 absence behavior; repo-convention awareness via `AGENTS.md`+inference (no new file); no contract change | Accepted | 2026-06-12 | 2026-06-12 |
| [0030](0030-product-engineering-pack.md) | A `product-engineering` pack — level-agnostic product shaping (a recursive `intent` tree) that de-risks via a choosable prototype-approach and decomposes into the specs `core` builds; brief = feature-intent projected onto a repo (`receive-brief` stays in `core`); contract maturity behavioral→interaction→wire-at-spec; one-way tracker projection (Linear/Jira Align/none); v1 app-scale + single-component, with a Backstage-anchored cross-component value-stream meta-repo specified for phase 2 | Accepted | 2026-06-12 | 2026-06-13 |
| [0031](0031-catalogue-package-manager-posture.md) | Package-manager *posture* for the pack catalogue — `pack.toml` as the rich superset source of truth with lossy per-tool marketplace projection; first-class metadata fields (readme/license/maintainers/links/categories/keywords) + `[pack.metadata.<tool>]` hatch; `@catalogue/pack` scoped identity; soft (warn-not-error) `categories` vocabulary; infra (hosted registry/indexer) explicitly out. Sets direction + decomposition (enriched-manifest spec first; index-contract / virtual-catalogue / provenance as follow-on RFCs) | Accepted | 2026-06-13 | 2026-06-13 |
| [0032](0032-architect-design-reviewer-subagent.md) | A forked-context `design-reviewer` subagent for the architect pack — ships the convergence loop's *preferred* fresh-context reviewer rung (read-only `Read/Grep/Glob`, reuses `architect-review` rubrics) alongside the existing skill; records the reading that the charter's "three reviewers is the ceiling" scopes the core code-review lenses, not opt-in design-side review (no charter edit) | Accepted | 2026-06-14 | 2026-06-14 |
| [0033](0033-design-craft-pack.md) | A `design-craft` pack — framework-agnostic design *discipline* for interaction/visual designers (a new audience), opt-in user-scope; four skills (`aesthetic-direction`, `design-system-foundations`, `layout-and-information-architecture`, `design-critique`) + a shared `quality-floor` checklist; strictly stack-neutral (no React/CSS/Framer, no values tables) via two guardrails; all skills, zero agents; design intent the build consumes (the design-side twin of RFC-0030's product seam) | Accepted | 2026-06-14 | 2026-06-14 |

## Adding a new RFC

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-rfc/scripts/next-ordinal.py docs/rfc)
cp .claude/skills/new-rfc/assets/rfc.md docs/rfc/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-rfc "<title>"` (defined in `.claude/skills/new-rfc/SKILL.md`).
