# Plan: codex-agent-config-projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog at
> the bottom.

## Approach

Keep the existing `codex-agent-toml` mode and extend its mapping interpreter to
understand the same `normalize` / `values` contract fields Kiro already uses.
The contract supplies model aliases and tool-intent tokens; the Codex
serializer reduces those tokens to documented TOML config keys. Tests land
first in the existing Codex serializer and contract suites, then the contract
mirror and projection code are updated.

Declined patterns: no broad new mapping DSL or projection mode; the only
contract grammar addition is a narrow `related-values` companion for projecting
Codex's documented `model_reasoning_effort` from the same `model:` source
alias. No generic `tools = [...]` output, because Codex docs do not document
that key; no MCP-server synthesis from `tools:`, because that would invent
server names and widen scope; no dependency, because TOML emission is already
hand-rolled in this module.

## Constraints

- Constrained by `dropped-primitives-coverage`: keep the existing
  `codex-agent-toml` mode and body-to-`developer_instructions` convention.
- Constrained by `distribution-adapters`: adapter behavior is contract-driven
  from `docs/contracts/adapter.toml` and the bundled `_data` mirror.
- OpenAI docs constrain the emitted TOML shape to documented Codex config keys.

## Construction tests

Targeted command:

```bash
PYTHONPATH=packages/agentbundle python3 -m pytest \
  packages/agentbundle/tests/unit/test_codex_agent_toml.py \
  packages/agentbundle/tests/unit/test_codex_projection_modes.py \
  packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py \
  packages/agentbundle/agentbundle/build/tests/test_contract_v08.py
```

Finish-time checks also run `make build-check` and
`.claude/skills/work-loop/scripts/lint-spec-status.py`.

## Design (LLD)

### Design decisions

- AC1-AC5: keep model aliasing in the frontmatter mapping table using
  `values`, with `related-values` for the paired Codex
  `model_reasoning_effort`.
- AC2-AC10: map tools to intermediate intent tokens in the contract, then
  reduce those intents inside `codex_agent_toml.py` to documented Codex config.
- AC11: distinguish absent `tools:` from present-but-empty/unmapped `tools:`;
  absence inherits Codex defaults, while declared tools produce explicit
  least-privilege config plus warnings for dropped tokens.

### Interfaces & contracts

The public contract is the `frontmatter-mapping."codex-agent-frontmatter-v0.8"`
table in both adapter contract TOML files. The output interface is Codex custom
agent TOML under `.codex/agents/`.

### Failure, edge cases & resilience

Unknown model aliases and tool tokens are omitted rather than emitted as invalid
Codex config. Each omission emits a stderr warning, matching Kiro's existing
mapping behavior and preventing silent loss.

## Tasks

### T1: Contract tests pin Codex model and tool mappings

**Depends on:** none

**Tests:**
- Update `test_contract_v08.py::test_codex_frontmatter_mapping_table` to assert
  Codex `model` and `tools` mapping entries and their values.

**Approach:**
- Add assertions only; expect red until the contract TOML files are updated.

**Done when:** the updated contract test fails for the current mapping and
passes after T3.

### T2: Serializer tests pin model and tool projection behavior

**Depends on:** none

**Tests:**
- Add tests in `test_codex_agent_toml.py` for model alias projection, unknown
  model warning/drop, read-only tools, write tools, Bash, web search, unknown
  tool warnings, no generic `tools` key, and no synthetic keys when `tools:` is
  absent.
- Extend `test_adapter_codex.py` to assert the adapter emits mapped config from
  the contract.

**Approach:**
- Use `tomllib.loads` for output assertions and `redirect_stderr` for warnings.

**Done when:** the new tests fail on the current serializer and pass after T4.

### T3: Update adapter contract mapping

**Depends on:** T1

**Tests:**
- Run `test_contract_v08.py`.

**Approach:**
- Add Codex `model` and `tools` mapping subtables to both contract TOML files.
- Keep the two files byte-identical.

**Done when:** contract tests pass.

### T4: Implement Codex mapping and TOML emission

**Depends on:** T2, T3

**Tests:**
- Run `test_codex_agent_toml.py`, `test_adapter_codex.py`, and
  `test_codex_projection_modes.py`.

**Approach:**
- Extend `_apply_mapping` to support `normalize = "to-list"` and `values`.
- Add warning behavior for unmapped model/tool values.
- Convert mapped Codex tool-intent tokens into `sandbox_mode`,
  `features.shell_tool`, `web_search`, and `tools.web_search`.
- Amend RFC/spec docs that made the stale Codex drop/no-slot claim.
- Add TOML boolean emission for dotted config keys.

**Done when:** targeted serializer and adapter tests pass.

### T5: Errata and stale-doc correction

**Depends on:** T3, T4

**Tests:**
- Grep confirms RFC-0001 and `dropped-primitives-coverage` name the correction
  instead of leaving the old claim unqualified.

**Approach:**
- Add a dated erratum to RFC-0001 for the old Codex subagent/hook claims.
- Add a dated erratum to the shipped dropped-primitives spec for the old
  `tools`/`model` no-slot claim.

**Done when:** AC14 is met and targeted doc references resolve.

### T6: Gates and review

**Depends on:** T1-T5

**Tests:**
- Run the targeted pytest command, `make build-check`, and
  `.claude/skills/work-loop/scripts/lint-spec-status.py`.

**Approach:**
- Fix any gate failures within the scoped files.
- Run a manual adversarial and quality pass if subagent dispatch is unavailable.

**Done when:** gates pass or any blocked gate is reported with exact failure
output.

## Rollout

Big-bang contract correction in the adapter bundle. Existing packs do not need
frontmatter changes; their next Codex projection receives the corrected TOML.
Rollback is reverting the contract mapping and serializer behavior.

## Risks

- Web access projection could be too broad if mapped to live search. This plan
  uses `live` only when source declares `WebFetch` or `WebSearch`, because the
  source author explicitly requested web access.
- Codex config defaults may change. Tests pin our emitted TOML shape to current
  documented keys, not undocumented behavior.

## Changelog

- 2026-06-10: initial plan.
- 2026-06-10: implementation complete; targeted tests and `make build-check` pass.
