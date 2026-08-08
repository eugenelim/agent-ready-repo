# RFC-0082 first-cut ownership mapping

**Provisional. Argue with it; do not implement from it.** A starting proposal for
spec 2, published so [RFC-0082](../0082-test-ownership-boundaries-and-inclusion.md)'s
taxonomy can be argued against real modules rather than in the abstract. Every
row is overturnable by reading the module — an earlier revision of this file got
several wrong, and the corrections are what produced its main finding.

Scope: `agentbundle/build/tests/` is hand-classified, because it is the tree spec
1 empties. `tests/unit/` and `tests/integration/` get signals only; an automated
verdict there would be the mechanical split D6 option C rejects.

## Finding 1 — the classification unit is the test **class**, not the module

This is the headline, and it did not survive the first attempt at this file
either. Three modules classified flatly as Engine turn out to contain
catalogue-conformance classes:

| Module | Engine part | Catalogue-conformance part |
| --- | --- | --- |
| `test_adapter_gemini.py` | `GeminiProjectionTests`, `GeminiSettingsMergeTests`, … invoke the adapter | `GeminiShippedAgentToolCoverageTests` sweeps `packs/*/.apm/agents/*.md` asserting every declared tool is in the contract map; `GeminiAllPacksAdmissibleTests` sweeps every `pack.toml` |
| `test_plugin_manifest_schema.py` | schema accept/reject behaviour | `SourcePluginJsonAuditTests` globs `packs/*/.claude-plugin/plugin.json` and asserts each validates |
| `test_shared_libs_projection.py` | projection primitive | `RealTreeInvariantTests` globs `packs/*/.apm/skills/*/scripts/*.py` asserting no pack ships a shim copy |

Both of those sweep-classes are **rule-shaped**: they assert a property of
*whatever packs exist*, which is exactly what a shipped conformance suite needs.

So the shape of spec 2's work is not what the RFC first assumed. It is not mostly
"relocate modules and rewrite rosters" — it is **extracting conformance classes
out of engine modules**. That is more invasive per unit and more valuable: this
material is already rule-shaped and portable, so it is the natural seed of the
shipped conformance suite rather than something that has to be written.

It also means "every test module gets exactly one owner" is too strong as stated.
A mixed module needs splitting, or a primary owner with a recorded exception —
spec 2 must state which.

## Finding 2 — a Tools destination the taxonomy lacked

Three modules exist to test `tools/lint-agents-md.py`, import no engine code, and
build their fixtures in `tmp_path`:
`test_lint_agents_md_{diataxis,legacy,risk}_block.py`. Per D4 they belong at
`tools/`. The RFC gained a taxonomy row for them.

An earlier draft of this file claimed "no automated signal surfaces them". That
is false and is withdrawn: a two-clause filter — never mentions `agentbundle`,
and names a `tools/*.py` path — finds exactly these three. They also share a
filename prefix. The honest claim is narrower: D6 option C's *read-based* signal
misses them. The case for hand classification rests on Finding 1, not on these.

## The discriminator used

| Signal | Reading |
| --- | --- |
| invokes an engine function, asserts on its output | **Engine** |
| no engine invocation; asserts on files under `packs/` | **Catalogue** |
| asserts against a hardcoded list of pack names | **Catalogue, roster-shaped** |
| asserts about exactly one pack's own content | **Pack** |
| exercises a script under `tools/` | **Tools** |
| **both** — invokes engine code *and* has a class sweeping the live catalogue | **Mixed — split it, or record a primary owner and the exception** |

## `build/tests/` — hand-classified

Candidate set: 36 of 44 modules matched the path-form sweep. **Four of those 36
are false positives** — they matched on synthetic fixture paths built inside
`tmp_path` and touch no live catalogue (`test_lint_packs.py` and the three
`test_lint_agents_md_*`). Treat 36 as a candidate count, not a measurement.

| Proposed owner | Module | Basis |
| --- | --- | --- |
| **Tools** | `test_lint_agents_md_diataxis_block.py` | tests `tools/lint-agents-md.py` check #8 |
| **Tools** | `test_lint_agents_md_legacy_block.py` | same script, legacy-marker warning |
| **Tools** | `test_lint_agents_md_risk_block.py` | same script, check 10g |
| **Mixed** | `test_adapter_gemini.py` | see Finding 1 — two rule-shaped sweep classes |
| **Mixed** | `test_plugin_manifest_schema.py` | see Finding 1 — `SourcePluginJsonAuditTests` |
| **Mixed** | `test_shared_libs_projection.py` | see Finding 1 — `RealTreeInvariantTests`; missed by the sweep entirely (walks `parents` for a marker rather than using `parents[N]`) |
| **Catalogue, roster** | `test_shipped_packs_v07_declarations.py` | hardcoded per-pack contract-version map |
| **Catalogue, roster** | `test_shipped_packs_v08_declarations.py` | `V08_PACKS` tuple |
| **Pack — architect** | `test_architect_design_reviewer_rubric_parity.py` | no engine import; token parity across one pack's files |
| **Pack — architect** *(contested)* | `test_architect_design_reviewer_projection.py` | engine mechanism, single-pack subject |
| **Engine** | `test_lint_packs.py` | invokes `lint_pack()` / `cmd_lint_packs()`; every pack materialised in `TemporaryDirectory` — reads no live catalogue |
| **Engine** | `test_adapter_claude_code.py`, `test_adapter_codex.py`, `test_adapter_copilot.py`, `test_adapter_cursor.py`, `test_adapter_kiro.py`, `test_adapter_kiro_alias.py`, `test_adapter_kiro_cli.py`, `test_adapter_kiro_ide.py` | invoke their adapter; live pack is input |
| **Engine** | `test_adapter_root_bins_projection.py`, `test_user_libs_projection.py`, `test_workspace_status_projection.py`, `test_build_ships_seeds.py` | build primitive classes |
| **Engine** | `test_contract.py`, `test_contract_scope.py`, `test_validate.py` | validator behaviour over the contract |
| **Engine** *(contested)* | `test_contract_v07.py`, `test_contract_v08.py` | assert `version >= (0, 8)` — a **floor, not a pin**, so portable; but both also carry hardcoded adapter/pack name lists, which are not |
| **Engine** | `test_pack_schema.py`, `test_pack_schema_allowed_adapters.py`, `test_pack_schema_install.py` | schema accept/reject behaviour |
| **Engine** | `test_pipeline.py`, `test_end_to_end_build.py`, `test_self_host_check.py`, `test_projectable_subset.py` | pipeline and build behaviour |
| **Engine** | `test_security.py`, `test_shared_prefix_contract.py` | adapter defence-in-depth; prefix routing |

**Shape:** ~27 engine, 3 tools, 3 mixed, 2 catalogue-roster, 2 pack.

**What that shape argues.** Two things, and the second corrects the RFC's first
assumption.

1. **Most of the in-package tree is genuinely engine-owned.** Spec 1's default —
   unresolved modules stay engine tests — is therefore safe, and the carve-out is
   much smaller than the raw candidate count suggests.
2. **No module in this tree is a standalone rule-shaped conformance test.** The
   rule-shaped material exists, but embedded inside three engine modules. So the
   shipped conformance suite is not assembled by moving files; it is assembled by
   extracting classes. Roster rewriting (D7) is real but is the smaller half.

## Contested calls, stated as such

1. **`test_architect_design_reviewer_projection.py`** — pack or engine? Uses the
   projection machinery to assert one pack's rubric survives. Proposed pack,
   because it fails when the *pack* changes, not the adapter.
2. **`test_contract_v0*.py`** — engine or catalogue-roster? Their version
   assertions are floors and portable; their hardcoded adapter and pack lists are
   not. Likely mixed under Finding 1's rule.
3. **`contracts/adapter.toml` as a subject.** Several modules read it. Whether
   the adapter contract is catalogue content or engine input is unsettled; it
   ships in `_DEFAULT_INCLUDE_DIRS`, which argues catalogue. Spec 2 should decide
   once, explicitly, not per-module.
4. **Granularity itself.** Splitting a module by class costs churn and can
   separate a class from shared setup. Recording a primary owner is cheaper but
   leaves catalogue assertions inside the engine suite, where the sdist ships
   them and they cannot run. Proposed: split, because the alternative reproduces
   the defect the RFC exists to end.

## `tests/unit/` and `tests/integration/` — signals only

Per-root candidate counts are method-sensitive and are **not** restated here,
because an earlier revision of this file mislabelled the strict-method figures as
loose. Spec 2 re-derives both, per root, and records the method with the number.

The one signal worth carrying forward: of the full candidate set, a majority
invoke engine code — the marker that most often means engine-owned, and the
reason a read-based split would misfile the bulk of them. Given Finding 1, expect
mixed modules here too, and expect the sweep to miss modules that locate the repo
root by walking for a marker rather than by index.
