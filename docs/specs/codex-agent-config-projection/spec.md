# Spec: codex-agent-config-projection

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`dropped-primitives-coverage`](../dropped-primitives-coverage/spec.md), [`distribution-adapters`](../distribution-adapters/spec.md)
- **Brief:** none
- **Contract:** none <!-- adapter contract TOML is internal build-pipeline data, not a root contracts/<type>/ API surface; mirrors named in Adapter contract data below -->
- **Adapter contract data:** [`docs/contracts/adapter.toml`](../../../docs/contracts/adapter.toml), [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Correct the Codex `agent` projection so pack-authored agent frontmatter keeps
portable intent when projected to `.codex/agents/<name>.toml`. Codex adopters
must receive OpenAI model IDs instead of Anthropic aliases, and Claude-style
`tools:` declarations must be translated to documented Codex configuration
fields (`sandbox_mode`, `features.shell_tool`, `web_search`, and
`tools.web_search`) rather than being silently discarded or emitted as an
undocumented generic `tools = [...]` array.

## Boundaries

### Always do

- Map source `model:` aliases through the adapter contract before TOML emission.
- Map source `tools:` through documented Codex config fields only; warn for each
  source tool token with no Codex mapping.
- Preserve existing body behavior: markdown body still lands verbatim in
  `developer_instructions`.
- Keep the contract mirror files byte-identical.

### Ask first

- Adding a new projection mode, mapping DSL beyond this spec's narrow
  `related-values` companion, top-level contract table, or pack manifest field.
- Changing source agent frontmatter in `packs/**/.apm/agents/*.md`.
- Changing model choices for the source packs themselves.

### Never do

- Do not emit an undocumented top-level `tools = [...]` key in Codex agent TOML.
- Do not preserve Anthropic model IDs or aliases in Codex agent TOML.
- Do not add a dependency or new top-level directory.
- Do not silently drop a declared tool token that has no mapping.

## Testing Strategy

| Behavior from Objective | Verification mode | Why this mode |
| --- | --- | --- |
| Codex model aliases project to OpenAI model IDs | TDD via `test_codex_agent_toml.py` and contract tests | Pure projection logic with a small, enumerable alias table. |
| Codex tool declarations project to documented config keys | TDD via `test_codex_agent_toml.py` and adapter tests | The tool-intent reduction is deterministic and must avoid widening or silent loss. |
| Unknown model/tool values are dropped with warnings | TDD via stderr-capturing unit tests | Kiro already uses build-time warnings for unmapped values; Codex should match that safety shape. |
| Existing Codex agent TOML body behavior is unchanged | Regression tests in the existing serializer suite | Body preservation is already load-bearing and must not regress while adding config keys. |
| Contract docs and bundled data stay mirrored | Goal-based targeted tests | Existing contract tests validate both files and schema conformance. |

## Acceptance Criteria

- [x] **AC1.** Both adapter contract files add Codex `model` values mapping `opus` -> `gpt-5.5`, `sonnet` -> `gpt-5.5`, and `haiku` -> `gpt-5.4-mini`, plus related `model_reasoning_effort` values mapping `opus` -> `xhigh`, `sonnet` -> `medium`, and `haiku` -> `medium`.
- [x] **AC2.** Both adapter contract files add Codex `tools` values mapping source tokens to Codex tool intents: read (`Read`, `Grep`, `Glob`), write (`Edit`, `Write`, `MultiEdit`), shell (`Bash`), and web search (`WebFetch`, `WebSearch`).
- [x] **AC3.** Codex agent TOML never emits a generic top-level `tools` key.
- [x] **AC4.** `model: opus|sonnet|haiku` in source frontmatter emits documented OpenAI model IDs in the TOML `model` key and emits the paired `model_reasoning_effort`.
- [x] **AC5.** An unknown source `model:` value is omitted from output and produces a build-time stderr warning naming the dropped value.
- [x] **AC6.** A declared read-only tool set emits `sandbox_mode = "read-only"`, `features.shell_tool = false`, and `web_search = "disabled"`.
- [x] **AC7.** A declared write-capable tool set emits `sandbox_mode = "workspace-write"`.
- [x] **AC8.** A declared `Bash` token emits `features.shell_tool = true`.
- [x] **AC9.** A declared `WebFetch` or `WebSearch` token emits documented Codex web-search config (`web_search = "live"` and `tools.web_search = true`).
- [x] **AC10.** Unknown source tool tokens are omitted from derived config and produce build-time stderr warnings naming the dropped token.
- [x] **AC11.** Agents with no `tools:` frontmatter inherit Codex defaults and do not receive synthetic `sandbox_mode`, `features.shell_tool`, `web_search`, or `tools.web_search` keys.
- [x] **AC12.** Existing behavior for `name`, `description`, and `developer_instructions` round-trip is unchanged.
- [x] **AC13.** Targeted Codex projection and contract tests pass.
- [x] **AC14.** Prior docs that made the stale Codex capability claim are amended with errata pointing to this correction.

## Assumptions

- Technical: Codex custom agents are TOML files under `~/.codex/agents/` or `.codex/agents/` and can include config keys such as `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` (source: https://developers.openai.com/codex/subagents).
- Technical: Codex config documents `features.shell_tool`, top-level `web_search`, `[tools].web_search`, and `sandbox_mode`; no official source found for a generic top-level custom-agent `tools = [...]` array (source: https://developers.openai.com/codex/config-reference).
- Technical: OpenAI's Codex model guidance names `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, and `gpt-5.3-codex-spark`; it recommends `gpt-5.5` for best coding and `gpt-5.4-mini` for faster, lighter subagent-style work (source: https://developers.openai.com/codex/models).
- Technical: Codex custom-agent examples pair `gpt-5.4-mini` read-only subagents with `model_reasoning_effort = "medium"`; lower efforts exist but the official examples do not use them for mini subagents (source: https://developers.openai.com/codex/subagents).
- Technical: The current Codex projection code only preserves `name` and `description` and silently drops `tools` and `model` (source: `packages/agentbundle/agentbundle/build/projections/codex_agent_toml.py`).
- Process: Full work-loop mode applies because this changes a public adapter contract and projected agent behavior (source: `AGENTS.md`, `.claude/skills/work-loop/SKILL.md`).
- Product: Alias tiering is inferred from existing source conventions: `opus` and `sonnet` both warrant the current frontier GPT family but differ by reasoning effort; `haiku` is fast/light and maps to the documented mini model (source: `docs/CONVENTIONS.md` model-selection table plus OpenAI Codex model guidance).
