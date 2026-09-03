# Behavior controls inventory: what enforces, and what only appears to

> Discipline: repository inventory (measured)

Commissioned 2026-09-02 for the `cross-adapter-behavior-enforcement` brief. Independent desk research; findings are cited to their sources and labelled by evidence class. Retained so the briefs can cite it rather than restate it.

---

Legend: **[M]** measured directly from code/search; **[C]** repository-declared contract; **[I]** inference from measured implementation. Paths are relative to `.`.

## Highest-value conclusions

| Set | Inventory |
|---|---|
| Portable across all five | **[M]** `agentbundle` schema validation, projection safety, path confinement, scope rails, seed delivery, and catalogue verification. Skill directories—including scripts/assets—are copied without semantic rewriting. **[I]** Their files are portable, but prose-triggered behavior still depends on model compliance. |
| Host-specific | **[M]** Hooks have different event names/paths; commands are dropped on Codex and Copilot; Cursor drops fine-grained agent tool lists; agent model aliases differ; only Gemini receives the `AGENTS.md` context bridge; root `.codex/config.toml` restricts Codex only. |
| Model-invariant | **[M]** Process exit codes; installer write fences; schema/lint failures; CI job failures; native host tool/sandbox restrictions; deterministic artifact checks. |
| Model-dependent | **[M]** Hook stdout reminders, command bodies, agent-body instructions, seed prose, Markdown templates, semantic eval judging, and anything requiring a model to select a skill/subagent. |
| Adopter-facing | **[M]** Pack `.apm` primitives, seeds, projected hooks/agents/commands, skill assets/scripts, and installer safety. |
| Maintainer-only | **[M]** Root `Makefile`, `.github/workflows/**`, most `tools/**`, root `.codex/config.toml`, current self-host projections, catalogue source tests. `tools/hooks/pre-pr.py` is the deliberate adopter-safe exception. |
| Can stop mid-loop | **[M]** Native agent tool/sandbox denial and host `PreToolUse` hooks could stop actions in principle, but this repository ships no `PreToolUse` wiring. Installer safety stops writes before projection. |
| Cannot presently stop mid-loop | **[M]** Both lifecycle-wired hook bodies return `0`. Eval is report-only. Commands, seeds, templates, and reminder output are advisory. |
| Can stop later | **[M]** `pre-pr.py` can reject a push if separately wired; local gates return nonzero; CI jobs can fail. **[I]** Whether a failed CI job blocks merge depends on branch protection, which is not encoded here. |

## Hooks

### Shipped sources

| Control and anchor | Trigger | Enforcement and contract | HARD/advisory | Hosts | Model swap |
|---|---|---|---|---|---|
| User-prompt wiring: [`work-loop-check.toml:19`](packs/core/.apm/hook-wiring/work-loop-check.toml:19). Body: [`work-loop-check.py:13`](packs/core/.apm/hooks/work-loop-check.py:13), [`:26`](packs/core/.apm/hooks/work-loop-check.py:26). | **[M] Mechanical:** every `UserPromptSubmit`/mapped equivalent runs `python tools/hooks/work-loop-check.py`. | **[M]** Prints a fixed reminder that non-trivial repository changes use work-loop; performs no classification; always returns `0`; reads no hook input. | Advisory. Cannot block. | All five, with host mappings below. | Process invocation survives; behavioral effect requires model to read/obey stdout. |
| Session wiring: [`session-start.toml:34`](packs/core/.apm/hook-wiring/session-start.toml:34). Body: [`session-start.py:260`](packs/core/.apm/hooks/session-start.py:260). | **[M] Mechanical:** `SessionStart`/mapped equivalent. | **[M]** Emits pending adaptation context; wired invocation omits `--show-knowledge`, so knowledge replay does not run. Normal path returns `0`; malformed explicit CLI arguments return `2` at [`:119`](packs/core/.apm/hooks/session-start.py:119). Environment-selected paths are confined at [`:102`](packs/core/.apm/hooks/session-start.py:102). | Normal lifecycle path advisory. | All five, with mappings below. | Confinement/exit behavior survives; emitted context requires model consumption. |
| Pre-PR body: [`pre-pr.py:5`](packs/core/.apm/hooks/pre-pr.py:5), [`:81`](packs/core/.apm/hooks/pre-pr.py:81), [`:117`](packs/core/.apm/hooks/pre-pr.py:117), [`:133`](packs/core/.apm/hooks/pre-pr.py:133). | **[M] Discretionary:** manual execution or consumer-installed Git pre-push hook. No `.apm/hook-wiring` entry invokes it. | **[M]** Runs available knowledge, loop-cohort, and adopter artifact checks; child failure returns `1`; missing optional tools are skipped; clean/empty path returns `0`. | HARD only when invoked/wired; otherwise dormant. | Python body is host-neutral; no automatic host activation. | Yes—deterministic subprocess results. |
| Kiro IDE companion: `packs/core/.apm/kiro-ide-hooks/work-loop-check.kiro.hook:5`. | **[M] Mechanical on Kiro IDE only:** `promptSubmit`. | **[M]** `askAgent` injects the reminder. | Advisory; no stop action. | None of the requested five; Kiro-only supplemental primitive. | Requires model compliance. |

### Host projections

| Host | Projection and event | Blocking implication |
|---|---|---|
| Claude Code | **[M]** Bodies → `tools/hooks/`; wiring → `.claude/settings.local.json`; commands preserved: [`adapter.toml:183`](packages/agentbundle/agentbundle/_data/adapter.toml:183), [`:219`](packages/agentbundle/agentbundle/_data/adapter.toml:219), [`:227`](packages/agentbundle/agentbundle/_data/adapter.toml:227). Events remain `SessionStart` and `UserPromptSubmit`. | **[M]** Shipped bodies return `0`; no block. |
| Codex | **[M]** Bodies → `tools/hooks/`; wiring → `.codex/hooks.json`; command dropped: [`adapter.toml:574`](packages/agentbundle/agentbundle/_data/adapter.toml:574). Current projection confirms both events at [`.codex/hooks.json:3`](.codex/hooks.json:3). | Same. |
| Copilot | **[M]** Bodies and generated hook JSON → `.github/hooks/`; command dropped: [`adapter.toml:501`](packages/agentbundle/agentbundle/_data/adapter.toml:501). Events become `sessionStart` and `userPromptSubmitted`, mapped in `copilot_hooks_json.py:61`. Unmapped events fail projection. | Same for shipped hooks. Mapping failure is build-time HARD. |
| Cursor | **[M]** Bodies → `.cursor/hooks/`; wiring → `.cursor/hooks.json`; events become `sessionStart` and `beforeSubmitPrompt`: [`adapter.toml:632`](packages/agentbundle/agentbundle/_data/adapter.toml:632), [`:669`](packages/agentbundle/agentbundle/_data/adapter.toml:669). Unmapped events are dropped with a build log. | Shipped hooks do not block. Unknown event handling is fail-open. |
| Gemini CLI | **[M]** Bodies → `.gemini/hooks/`; wiring → `.gemini/settings.json`; events remain `SessionStart` and map `UserPromptSubmit` → `BeforeAgent`: [`adapter.toml:725`](packages/agentbundle/agentbundle/_data/adapter.toml:725), [`:760`](packages/agentbundle/agentbundle/_data/adapter.toml:760). Unmapped events fail projection. | Shipped hooks do not block. Mapping failure is build-time HARD. |

**[M]** The repository defines commands, mappings, and emitted files, but does not encode each host runtime’s general “nonzero means block” contract. That gap does not affect the shipped lifecycle hooks because both normal paths explicitly return `0`.

**[C] Conflict:** [`tools/hooks/README.md:114`](tools/hooks/README.md:114) says non-Claude wiring is consumer-side, while the adapter contract mechanically projects wiring for Codex, Copilot, Cursor, and Gemini. The executable adapter contract is newer/more specific.

## Subagents and agent definitions

**[M]** Fifteen source agents exist. Every one declares both `tools:` and `model:`. Representative mechanical boundaries:

| Source | Declared constraint | Host treatment |
|---|---|---|
| [`implementer.md:4`](packs/core/.apm/agents/implementer.md:4) | Edit/Write/Bash-capable, model `sonnet`. | Claude allowlist; Codex maps to `workspace-write`; Copilot retains list; Cursor loses list/coarsens to `readonly=false`; Gemini maps allowlist. |
| [`shaping-reviewer.md:4`](packs/core/.apm/agents/shaping-reviewer.md:4) | Read-only tool set, `opus`. | Codex maps to `read-only`; Cursor derives `readonly=true`; Gemini/Copilot/Claude retain native restriction. |
| [`adversarial-reviewer.md:4`](packs/core/.apm/agents/adversarial-reviewer.md:4), [`quality-engineer.md:4`](packs/core/.apm/agents/quality-engineer.md:4), [`security-reviewer.md:4`](packs/core/.apm/agents/security-reviewer.md:4) | Read/search plus bounded Bash, model pinned. | Same host degradation differences. |
| Codex mapping | [`adapter.toml:869`](packages/agentbundle/agentbundle/_data/adapter.toml:869) | **[M]** Tool intents become sandbox/features; model aliases become Codex model/effort. |
| Copilot mapping | [`adapter.toml:895`](packages/agentbundle/agentbundle/_data/adapter.toml:895) | **[M]** Tools retained after validation; model dropped. |
| Cursor mapping | [`adapter.toml:914`](packages/agentbundle/agentbundle/_data/adapter.toml:914) | **[M]** Fine-grained tools dropped; model retained; read-only intent becomes Boolean `readonly`. |
| Gemini mapping | [`adapter.toml:934`](packages/agentbundle/agentbundle/_data/adapter.toml:934) | **[M]** Tool allowlist and model tier both mapped. |

- **[M] Trigger:** subagent definition becomes active only when a user/orchestrator selects that agent. Selection is discretionary.
- **[M] HARD portion:** once loaded, native tool/sandbox restriction is host-enforced and model-invariant.
- **[M] Advisory portion:** role, review discipline, output format, and completion language in the body remain prose/model-dependent.
- **[M] No all-five-identical constraint:** Cursor’s Boolean degradation and Copilot’s dropped model prevent parity.

## Commands

| Control | Trigger/enforcement | Hosts | Model dependence |
|---|---|---|---|
| `packs/core/.apm/commands/conventions-check.md:1`, body at `:10` | **[M] Discretionary:** explicit command selection. It asks the model to inspect/report and expressly does not auto-fix. Advisory. | **[M]** Claude → `.claude/commands/`; Cursor → `.cursor/commands/`; Gemini → `.gemini/commands/*.toml`. Codex and Copilot drop it. Anchors: [`adapter.toml:210`](packages/agentbundle/agentbundle/_data/adapter.toml:210), [`:671`](packages/agentbundle/agentbundle/_data/adapter.toml:671), [`:768`](packages/agentbundle/agentbundle/_data/adapter.toml:768). | Entire command body depends on model execution. Any subprocess linter it subsequently invokes is model-invariant once started. |

## Settings, permissions, and projection safety

| Control | Scope | What it enforces | Strength/model |
|---|---|---|---|
| [`.codex/config.toml:1`](.codex/config.toml:1) | Maintainer checkout, Codex only. | **[M]** `approval_policy="on-request"`; default `repo-codex-authoring`; root read, narrowly listed write prefixes for `.codex`/`.agents`. | HARD native runtime restriction; model-invariant. Not exported as a pack seed. |
| Adapter allowed prefixes, e.g. [`adapter.toml:235`](packages/agentbundle/agentbundle/_data/adapter.toml:235) | All adapter installs. | **[M]** Constrains installer writes under adapter/scope-specific prefixes. | HARD during install; not a runtime tool permission. |
| `safety.py:175`, `:317` | Installer/build. | **[M]** Refuses path escape, unsafe target, or writes outside allowed prefixes; atomic write path. | HARD/model-invariant. |
| `scope_rails.py:16`, `:85` | Installer scope selection. | **[M]** Refuses non-empty seeds and incompatible hook wiring at user scope. | HARD/model-invariant. |
| `install.py:488`, `:694`, `:1078`, `:1280`, `:1393` | Pack installation. | **[M]** Validates metadata/scope/adapter, reports dropped primitives, confines paths, and detects conflicts. | Validation/path errors HARD. Dropped primitive is warning-only unless its projector fails closed. |

**[M] Absence:** no checked-in Claude settings, Cursor settings/rules, Gemini settings, or Copilot instruction file exists in this checkout. Those settings are generated at install/self-host time where supported.

## Mechanical authored-artifact gates

| Gate family and anchor | Trigger | Enforcement | Audience/portability |
|---|---|---|---|
| Catalogue verifier: [`verify.py:2197`](packages/agentbundle/agentbundle/catalogue_tooling/verify.py:2197) | `agentbundle catalogue verify`, build/release CI. | **[M]** Nineteen ordered checks: config/schema, source lint, versions, profiles, dependencies, adapter compatibility, primitive layout, clean build, projected agents, marketplace/manifests, drift, self-host defaults, preflight, fixtures, integration. Stops nonzero. | Engine portable and model-invariant. Adopters receive it with CLI; this repository’s invocation policy is maintainer-only. |
| Catalogue lint: `catalogue_tooling/lint.py:1578`, `:1775`, `:1822`, `:2255`; `skill_spec_lint.py:191`, `:320`, `:831` | `catalogue lint`, verifier, pre-PR. | **[M]** Validates manifests, agent metadata/tool/model shape, opt-in seeds, skill/eval schema, and pack/eval cross-references. | HARD when invoked; portable CLI. |
| Projection validation | `verify.py:834`; adapter implementations and [`adapter.toml:118`](packages/agentbundle/agentbundle/_data/adapter.toml:118). | **[M]** Checks generated agent artifacts and adapter-supported primitive mappings. | HARD build-time; adapter-specific results, model-invariant. |
| Maintainer pre-PR aggregator: [`pre_pr_catalogue.py:1`](tools/catalogue/pre_pr_catalogue.py:1), [`:59`](tools/catalogue/pre_pr_catalogue.py:59), [`:110`](tools/catalogue/pre_pr_catalogue.py:110) | `make pre-pr` at [`Makefile:91`](Makefile:91), or build chain. | **[M]** Stops at child nonzero. Runs verify, deep skill lint, build lint, SSO configuration checks, knowledge/eval/journey/OKF checks, then adopter pre-PR. | HARD when invoked. Explicitly never projected to adopters. |
| Full build chain: [`build_gate_chain.py:220`](tools/repo/build_gate_chain.py:220) | `make build-check` at [`Makefile:156`](Makefile:156), Windows mirror, CI. | **[M]** Sequential nonzero-stop chain. | Maintainer-only, model-invariant. |
| Delivery state/traceability | [`build_gate_chain.py:250`](tools/repo/build_gate_chain.py:250) | Build-check. | **[M]** Tests and runs spec-status, delivery-brief coverage, traceability, and workspace-status contracts. | HARD maintainer gate. The underlying scripts ship in skills and can be run by adopters. |
| Catalogue leaks | [`verify_host_checks.py:209`](tools/catalogue/verify_host_checks.py:209), [`:266`](tools/catalogue/verify_host_checks.py:266) | Build-check at [`build_gate_chain.py:284`](tools/repo/build_gate_chain.py:284). | **[M]** Fails on maintainer-only names/RFC/knowledge identifiers leaked into linted seeds or core skill Markdown; refuses unsafe linked trees; returns `1` on findings. | HARD maintainer gate; model-invariant. |
| Catalogue/release route policy | [`build_gate_chain.py:296`](tools/repo/build_gate_chain.py:296) | Build-check. | **[M]** Curation guard, experience-agnostic check, scope differential, plugin membership/roster, publish refusals, route docs/site parity, pack descriptions, maintainer-email privacy. | HARD maintainer-only. |
| Supply-chain/security policy | [`build_gate_chain.py:423`](tools/repo/build_gate_chain.py:423), [`Makefile:324`](Makefile:324) | Build-check; `make sast`. | **[M]** npm install-script permission, `nosec`/`nosemgrep` form, Bandit, Semgrep, dependency audits, workflow posture. Missing required SAST binaries fail the SAST target. | HARD maintainer-only when invoked; model-invariant. |
| CI/workflow integrity | [`build_gate_chain.py:476`](tools/repo/build_gate_chain.py:476) | Build-check. | **[M]** Local/CI parity, Windows workflow, security workflow, CodeQL posture, SAST reachability, test roster, contract drift. | HARD maintainer-only. CodeQL itself is repository-declared advisory. |
| Architecture/ownership | [`build_gate_chain.py:568`](tools/repo/build_gate_chain.py:568) | Build-check. | **[M]** Adapter-layer boundary, dependency declaration, generated-path ownership, each paired with self-test; catalogue-curation test floors. | HARD maintainer-only. |
| Composite CI | [`Makefile:670`](Makefile:670), [`.github/workflows/build-check.yml:67`](.github/workflows/build-check.yml:67) | Local `make ci`; GitHub events. | **[M]** Build-check + Ruff + mypy + test roster; workflows also provision dependencies and run publication/security-specific checks. | Process-HARD. Merge-blocking status not proven without branch-protection data. |

## Eval harness

| Surface | Measured control |
|---|---|
| Activation input | **[M]** `eval_queries.json` queries test whether the expected skill activates. Runner contract at `pack_evals.py:1`; threshold `0.5` at `:52`; repeated runs default to three. |
| Driver | **[M]** In-harness live activation supports headless Claude only. Cursor/Kiro GUI routes are rejected; no Codex, Copilot, or Gemini activation detector exists at `pack_evals.py:222`. |
| Output grading | **[M]** `evals.json` supplies deterministic file/output assertions and semantic rubrics. B-lite checks occur at `pack_evals.py:806`; semantic judge at `:944`. Missing workspace/evidence fails grading closed. |
| Non-Claude model | **[M]** Yes for judging: built-in judge backends include Claude and `codex exec --sandbox read-only` at `pack_evals.py:327`. **No** for the live activation driver. Custom judge configuration can add backends. |
| Blocking | **[M]** `pack-evals.yml:3` declares report-only; weekly/manual workflow at `:17`; bounded summary upload at `:71`. CLI live-detection misses exit `0` at `pack_evals.py:1277`. It does not gate PRs or runtime actions. |
| Model invariance | **[M]** Deterministic output/file assertions survive a model swap. Activation and semantic judge results are model-dependent. |

## Seeds, projections, templates, and assets

### Seeds

- **[M]** Twenty-four seed files exist under `packs/{core,governance,monorepo}/seeds/`.
- **[M]** Delivery behavior is implemented at `_common.py:80`, classification at `:120`, and write policy at `:170`: absent targets are created, identical files skipped, changed files preserved with an `.upstream` companion, fragments are not emitted standalone, and paths are jailed below the target root.
- **[M]** Seeds are adapter-neutral and adopter-facing at repo scope.
- **[M]** User-scope installation with non-empty seeds is refused by `scope_rails.py:16`.
- **[I]** Seed delivery and conflict preservation are model-invariant; behavior expressed by the delivered Markdown remains dependent on host discovery and model obedience.
- **[M]** Gemini alone gets an explicit `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge at [`adapter.toml:760`](packages/agentbundle/agentbundle/_data/adapter.toml:760). No equivalent generated context bridge exists for Copilot or Cursor.

### Shape-constraining assets outside `SKILL.md`

**[M]** These 33 files are delivered inside skill directories. Their presence/bytes are mechanically portable; Markdown shapes are advisory unless a script consumes them.

| Class | Exact anchored inventory |
|---|---|
| Governance/spec/state | `new-rfc/assets/rfc.md:1`; `new-adr/assets/adr.md:1`; `new-spec/assets/spec.md:1`; `new-spec/assets/plan.md:1`; `intake-intent/assets/minimal-intent.md:1`; `work-loop/assets/state.json:1`; `adapt-to-project/assets/reference.md:1`. |
| Product/experience | `align-value-stream/assets/rollup.md:1`; `ux-writing/assets/voice-chart.md:1`; `discovery-loop/assets/plan-tree.md:1`; `frame-intent/assets/intent-template.md:1`; `map-capabilities/assets/capability-map.md:9`; `identify-opportunities/assets/opportunity-template.md:8`; `creative-direction/assets/creative-direction.md:1`; `service-blueprint/assets/service-blueprint.md:8`; `user-flow/assets/handover.md:1`; `user-flow/assets/screen-brief.md:1`; `tone-of-voice/assets/voice-chart.md:8`; `content-design/assets/content-brief.md:8`; `journey-mapping/assets/journey-map.md:9`; `process-mapping/assets/process-map.md:8`; `copy-direction/assets/copy-direction.md:7`. |
| Architecture | `architect-design/assets/design-doc.md:1`; `architect-design/assets/concept.md:8`; `architect-assess/assets/assessment.md:1`; `architect-review/assets/risk-register.md:7`; `architect-review/assets/critique.md:5`; `architect-diagram/assets/c4-container.md:1`. |
| Compiler/converter/research | `compile-okf/assets/output-rendering.md:1`; `compile-okf/assets/procedure-wrapper.md:12`; `compile-okf/assets/router-wrapper.md:11`; desk-research methodology template `:1`; `markdown-to-html/scripts/template.html:1`. |

Mechanical exceptions:

- **[M]** `work-loop/assets/state.json` is machine-read/validated once its workflow executes.
- **[M]** Compile-OKF wrappers and the HTML template are consumed by deterministic generators.
- **[M]** All other listed Markdown assets constrain shape only when the invoking model follows the associated skill.

## Counts and absence searches

Commands used for reported counts:

```sh
rg --files --hidden packs |
  rg '/\.apm/(hooks|hook-wiring|kiro-ide-hooks|agents|commands)/' |
  awk -F'/.apm/' '{k=$2; sub("/.*","",k); n[k]++} END {for (k in n) print k, n[k]}' |
  sort
# agents 15; commands 1; hook-wiring 2; hooks 3; kiro-ide-hooks 1

rg --files --hidden packs | rg '/seeds/' | wc -l
# 24

rg --files --hidden packs |
  rg '/\.apm/skills/[^/]+/(assets/|references/[^/]*template|scripts/template\.)' |
  wc -l
# 33
```

Absence searches:

```sh
rg --files --hidden |
  rg '(^|/)(settings[^/]*\.json|hooks\.json|copilot-instructions\.md|GEMINI\.md)$|/\.cursor/rules/|/\.github/instructions/'
# Only .codex/hooks.json in the current checkout.

rg --hidden -l 'default_permissions|repo-codex-authoring|approval_policy' \
  . --glob '!dist/**' --glob '!packages/agentbundle/tests/**'
# Runtime configuration: .codex/config.toml.
# One documentation implementation note also mentions the terms.
```

**[M] Final blocking inventory:** installer/path/scope refusals, native subagent tool restrictions, invoked local gates, and failed CI processes are the only model-invariant stopping controls found. No shipped lifecycle hook currently blocks a tool call or prompt; no `PreToolUse` wiring is shipped; the eval harness, commands, seed prose, agent prose, and ordinary templates cannot stop an action.

---

# Appendix A: cognitive-load and readability controls

## Governing result

- **[Cited] `docs/product/briefs/*.md` is governed by the artifact-writing rules in [`docs/AGENTS.md`](docs/AGENTS.md:3>)** because that file applies to all of `docs/`.
- **[Measured] No active mechanical readability, word-count, token-count, or line-count gate selects brief files.**
- **[Measured] No artifact class has a different Flesch/grade calibration.** The only implemented readability numbers are Flesch ≥70, grade ≤8, minimum 30 eligible words. Artifact-specific numeric controls instead concern lines, characters, columns, paragraphs, router rows, and reference depth.
- **[Measured] The strongest differing thresholds are:** skill body warning above 500 lines/error above 1,000; AGENTS files 35–120 lines by class; skill description 1,024 characters; skill compatibility 500; skill name 64; journey tagline 120; knowledge title advisory under 80; rule-router maximum 12 rows; tables near five columns; narrative paragraphs two or three sentences.

## Controls

| Control and anchor | Artifact selection | Exact property | Enforcement | Briefs |
|---|---|---|---|---|
| **Scoped documentation rules:** [`docs/AGENTS.md:3`](docs/AGENTS.md:3>), [`:11`](docs/AGENTS.md:11>) | Every artifact below `docs/`, by directory scope | Concrete outcome/plain terms; define terms; descriptive headings; short resumable parts; one main point per section; numbered sequences vs bullets; group rather than truncate long material; self-contained arithmetic/dates/link evidence; current state without dead ends/draft notes/unrequested advice; merge duplicate rules/history/navigation; visuals only when materially clearer. | **Prose-only repository instruction.** Tests pin parts of the rule text, but no gate scans each document for compliance. | **Inside, directly.** |
| **Documentation consolidation and genre:** [`docs/CONVENTIONS.md:654`](docs/CONVENTIONS.md:654>), [`:735`](docs/CONVENTIONS.md:735>), [`:767`](docs/CONVENTIONS.md:767>) | Documentation by semantic class; guides additionally declare a Diátaxis `kind` | Current-state documentation; concise architecture docs; one subsystem file linked to ADRs; each guide is exactly one of tutorial/how-to/reference/explanation and links out instead of mixing forms; short orientation without duplicating code/spec. | **Prose-only.** Guide schema validates the declared `kind`, not prose purity. | **Inside for general current-state/no-duplication rules; outside guide-only rules.** |
| **Universal output-rendering block:** [`guides/_shared/reference/output-rendering.md:25`](guides/_shared/reference/output-rendering.md:25>), artifact clause [`:34`](guides/_shared/reference/output-rendering.md:34>) | Outputs of any skill carrying the managed block; canonical skills selected by `packs/*/.apm/skills/*/SKILL.md`, with the contract-test exclusions below | Prose artifacts: descriptive headings, short resumable sections, one fact/sentence, no repeated summary, at most one load-bearing point/section, group inventories rather than truncate; standalone arithmetic/dates/link proof; consolidate maintained prose; preserve evidence, constraints, warnings and exact names. | Artifact properties are **prose-only**. Presence and self-containedness of the block are **HARD under `make test`**, via [`test_cognitive_load_repository_contract.py:430`](tests/roster/test_cognitive_load_repository_contract.py:430>) and [`Makefile:511`](Makefile:511>). | **Conditional/indirect:** inside when a skill such as `author-delivery-brief` creates the brief; not selected by pathname. |
| **Shape-specific rendering:** [`output-rendering.md:110`](guides/_shared/reference/output-rendering.md:110>) | Opt-in shape directive used by a producing skill | Tables near **5 columns** maximum; narrative uses short `##` headings and **2–3-sentence paragraphs**; one status/item per line; trees rather than nested bullets; visuals only for material relationships. | **Advisory/prose-only.** No shape linter. | Conditional when the authoring skill uses those shapes. |
| **Managed-block synchronizer:** [`add-rendering-directives.py:305`](tools/add-rendering-directives.py:305>), [`:365`](tools/add-rendering-directives.py:365>), [`:516`](tools/add-rendering-directives.py:516>) | Canonical `packs/*/.apm/skills/*/SKILL.md`; compiler-generated sources are excluded because their compiler owns them | Rejects duplicate/misplaced/unmatched managed markers and block drift; inserts the universal block and selected shape directives. | `--check` exits nonzero, but **not wired to any Makefile/workflow target**. Manual hard check only. | Outside. |
| **Readability scorer:** [`check-output-readability.py:16`](tools/check-output-readability.py:16>), [`:197`](tools/check-output-readability.py:197>), CLI [`:319`](tools/check-output-readability.py:319>) | Only explicit CLI path arguments. Its test selects cognitive-load `.md` fixtures plus three allowlisted guidance files | Aggregate eligible prose must have at least **30 words**, Flesch ≥**70**, grade ≤**8**. Input cap **1 MiB**. Below 30 words is `insufficient`, which does **not** fail. | CLI fails on `fail`; test asserts results. **Neither checker nor its test is wired into a Makefile/CI target.** | Outside automatic selection; manually passable. |
| **Readability exclusions:** regex [`check-output-readability.py:31`](tools/check-output-readability.py:31>), extraction [`:144`](tools/check-output-readability.py:144>), test [`test_check_output_readability.py:125`](tools/test_check_output_readability.py:125>) | Any explicitly scored artifact containing a complete marker pair | `<!-- readability:exclude:start -->` through the next `<!-- readability:exclude:end -->` is removed from the Flesch corpus only. It does not deselect the file or waive other controls. Matching is non-greedy, case-insensitive and DOTALL; nesting is not parsed, and unmatched markers exclude nothing. Code, comments, tables, links, URLs, errors and technical tokens are separately removed. | Same orphan/manual checker status. | No brief currently uses the markers; briefs are not selected. |
| **Per-pack cognitive-load scenarios:** coverage test [`test_cognitive_load_repository_contract.py:475`](tests/roster/test_cognitive_load_repository_contract.py:475>); readability selection [`test_check_output_readability.py:76`](tools/test_check_output_readability.py:76>) | `packs/*/.apm/skills/*/evals/evals.json`; scenario ID prefix `cognitive-load-`. Hard roster excludes `_` packs and deliberately carves out `agent-skill-engineering`; readability test includes every non-underscore pack | Hard contract requires at least one scenario per selected pack and requires serialized scenario text to address “optional assistant narration” and preserving substance. Every scenario names `evals/files/cognitive-load/ordinary-prose.md`; core also names two quiet-work JSON transcripts. Common assertions cover outcome-first/plain/scannable output, zero optional narration, and preservation of depth/evidence/constraints/warnings/errors. | Coverage is **HARD under `make test`**. Fixture Flesch scoring is presently **orphan/manual**, because its test is not in a gate. | Outside. |
| **AGENTS progressive-disclosure lint:** constants [`lint-agents-md.py:29`](tools/lint-agents-md.py:29>), selection [`:204`](tools/lint-agents-md.py:204>), scope declarations [`:261`](tools/lint-agents-md.py:261>), duplicate runs [`:630`](tools/lint-agents-md.py:630>) | Root/scoped `AGENTS.md` and `AGENTS.local.md`, plus core seed AGENTS; explicit vendored/fixture/build exclusions | Maximum lines: root **120**, root local **60**, core seed **100**, scoped **80**, example **35**. Scoped files must state both scope and inheritance. Rejects copied runs of at least **3 nonblank lines** totaling at least **80 characters** from the nearest ancestor. | **HARD** in pre-PR catalogue checks via [`pre_pr_catalogue.py:124`](tools/catalogue/pre_pr_catalogue.py:124>), hence `make pre-pr` and `make build-check`. | Brief bodies outside; `docs/AGENTS.md` itself is inside. |
| **`CAT-S002` skill metadata ceilings:** [`skill_spec_lint.py:440`](packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:440>) | Deep lint over canonical skill directories | Skill name **1–64 chars**, description ≤**1,024**, compatibility ≤**500**. | **ERROR/HARD** under `catalogue lint --deep`, `make pre-pr`, and `make build-check`. | Outside. |
| **`CAT-S003` skill body/depth:** [`skill_spec_lint.py:516`](packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:516>), reference depth [`:543`](packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:543>) | Same deep-lint skill selection; body excludes frontmatter | Body above **500 lines** is warning; above **1,000 lines** is error. Same-skill references deeper than **one directory level** are warnings. | >1,000 **HARD**; 501–1,000 and deep references **advisory warnings**. `catalogue lint --deep`, `make pre-pr`, `make build-check`. Ordinary `catalogue verify` does not run this deep check. | Outside. |
| **`CAT-S004` progressive layout:** [`skill_spec_lint.py:549`](packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:549>) | Same deep-lint skills | Warns about loose skill-root files and top-level directories outside `scripts`, `references`, `assets`, `evals`. This supports progressive disclosure structurally; it does not inspect prose. | **Advisory warning**, deep lint/pre-PR/build-check. | Outside. |
| **`CAT-L026` description ceiling:** code registration [`diagnostics.py:40`](packages/agentbundle/agentbundle/catalogue_tooling/diagnostics.py:40>), emission [`lint.py:1721`](packages/agentbundle/agentbundle/catalogue_tooling/lint.py:1721>) | Immediate `packs/<pack>/.apm/skills/<skill>/SKILL.md` entries | Description ≤**1,024 characters**. | **ERROR/HARD** under ordinary `catalogue lint`, `make lint-packs`, verify—reported there as `CAT-V-002`—and build-check. | Outside. |
| **`CAT-L029` seed router bounded disclosure:** opt-in [`lint.py:1823`](packages/agentbundle/agentbundle/catalogue_tooling/lint.py:1823>), router checks [`seed_lint.py:570`](packages/agentbundle/agentbundle/catalogue_tooling/seed_lint.py:570>) | Pack seeds only when `[pack].lint-seeds = true`; declared seed allowlist and recognized guidance files | Root `AGENT_RULES.md` must be a compact routing table with **1–12 rows**, unique literal `.agents/rules/*.md` targets and no extra prose; topic/scoped guidance cannot route again. Also applies the seed blocklist/placeholders/pattern checks represented by `CAT-L029`. | **ERROR/HARD** under ordinary lint, verify as `CAT-V-002`, `make lint-packs`, and build-check. | Outside. |
| **Journey tagline:** [`journey_validator.py:54`](packages/agentbundle/agentbundle/catalogue_tooling/journey_validator.py:54>), threshold [`:63`](packages/agentbundle/agentbundle/catalogue_tooling/journey_validator.py:63>), caller [`index_generator.py:354`](packages/agentbundle/agentbundle/catalogue_tooling/index_generator.py:354>) | Each pack’s optional `JOURNEY.md`, when catalogue index generation parses it | Frontmatter `tagline` ≤**120 characters**. | **Hard for `agentbundle catalogue index`**, but no Makefile target was found invoking it against the repository. | Outside. |
| **Agent-skill-engineering progressive-disclosure doctrine:** [`instruction-density-and-progressive-disclosure.md:12`](packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/instruction-density-and-progressive-disclosure.md:12>), decisions [`:18`](packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/instruction-density-and-progressive-disclosure.md:18>), construction [`:25`](packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/instruction-density-and-progressive-disclosure.md:25>) | Skill artifacts when this OKF topic is explicitly routed/retrieved | Keep purpose, mode choice, invariants and routes in `SKILL.md`; move substantial conditional procedures/schemas to focused references; every resource needs a real caller/load condition; one authority per rule; no unrelated preloading; no orphan resources or token-bearing duplication. | **Advisory reference**, no generic artifact gate. | Outside. |
| **RFC fresh-reader review:** [`new-rfc/SKILL.md:170`](packs/governance-extras/.apm/skills/new-rfc/SKILL.md:170>), terminal gate [`:194`](packs/governance-extras/.apm/skills/new-rfc/SKILL.md:194>) | RFCs authored through `new-rfc`; condition fires when vocabulary is coined, unfamiliar sibling RFCs are assumed, or audience includes non-authors | Give a fresh reader only the RFC; gloss unresolved terms. | **Workflow-hard when triggered**—required before the skill’s handoff gate—but not a build/content linter. | Outside. |
| **No hard AC word budgets:** [`new-spec/SKILL.md:502`](packs/core/.apm/skills/new-spec/SKILL.md:502>) | Specs authored through `new-spec`; specifically acceptance criteria | Shaping review must reject a hard acceptance-criterion word budget; semantic atomicity/testability owns the criterion instead. | **Workflow-hard shaping-review gate**, pinned by tests; no generic spec scanner. | Outside. |
| **Knowledge-entry title target:** [`packs/core/seeds/docs/knowledge/README.md:70`](packs/core/seeds/docs/knowledge/README.md:70>) and repository copy [`docs/knowledge/README.md:79`](docs/knowledge/README.md:79>) | `docs/knowledge/patterns.jsonl` entries | One-line title; aim under **80 characters**. | **Advisory.** The knowledge linter does not enforce this maximum. | Outside. |

## Marker users

**[Measured]** The exhaustive source/projection classes returned by:

```bash
git grep -l 'readability:exclude:start'
```

are:

- `.agents/rules/cognitive-load.md`;
- `docs/AGENTS.md`;
- `guides/_shared/reference/output-rendering.md`;
- core seed copies of the cognitive-load rule and `docs/AGENTS.md`;
- canonical governed `SKILL.md` files containing the managed output block;
- generated/self-hosted `.agents/skills/**` and `.claude/skills/**` projections;
- the `_example` skill/scaffold;
- `compile-okf` output-rendering assets and projections.

They surround the authority/safety override sentence, not ordinary artifact prose. No `docs/product/briefs/*.md` marker was found.

## Scenario inventory

**[Measured: 22 scenario IDs]**

```bash
git grep -h '"id": "cognitive-load-' -- \
  'packs/*/.apm/skills/*/evals/evals.json' | wc -l
# 22
```

There is currently one in every public pack. The hard repository contract requires one in every public pack **except** `agent-skill-engineering`; that pack nevertheless has one. Twenty-one use the `cognitive-load-output-quality` name; core uses `cognitive-load-quiet-work-and-readable-receipt`.

## Mechanical versus prose-only

**Active hard make/build controls**

- AGENTS line ceilings, scope declaration and ancestor-duplication lint.
- `CAT-S002`, `CAT-S003` error tier, `CAT-L026`, and opt-in `CAT-L029`.
- Managed output-block presence/self-containedness.
- Per-pack cognitive-scenario manifest coverage.

**Advisory or workflow-only**

- Actual prose-artifact readability and structure from `docs/AGENTS.md`, output-rendering, conventions, and the agent-skill doctrine.
- `CAT-S003` warning tier and `CAT-S004`.
- RFC fresh-reader review and spec rejection of word budgets are workflow gates, not build scanners.
- Knowledge-title target.

**Executable but not wired to a repository gate**

- `check-output-readability.py`.
- `add-rendering-directives.py --check`.
- Journey tagline validation through catalogue-index generation.

## Absences established

- **[Measured] No CAT diagnostic implements Flesch, grade level, prose word count, or token count.**
- **[Measured] `CAT-L025` is registered as “primitive name exceeds max length” at [`diagnostics.py:39`](packages/agentbundle/agentbundle/catalogue_tooling/diagnostics.py:39>) but has no emitter; the effective name cap is `CAT-S002`.**
- **[Measured] No brief-specific readability or size gate exists.** The current brief’s proposed **1,599-word** spec body is proposal text, not implemented control.
- **[Cited] Non-executable documentation is explicitly sized by coherence, not the review-line taxonomy:** [`docs/CONVENTIONS.md:952`](docs/CONVENTIONS.md:952>).
- Changelog checking only verifies release/pack inventory; it imposes no cognitive-load or length property on changelog entries.

Searches used for these absences:

```bash
git grep -n -I -E \
  '(CAT-[LSV][0-9]{3}|CAT_[LSV][0-9]{3}).*(length|line|word|token|description|progressive|readab|reference|seed|router)' \
  -- packages/agentbundle/agentbundle/catalogue_tooling

git grep -n -E \
  'test_check_output_readability|check-output-readability|pytest.*tools|tools/test_' \
  -- Makefile .github tools packages pyproject.toml

git grep -n -E \
  '1599|2,392|2392|spec body.*words|body_words|word budget' \
  -- ':!docs/product/briefs/**' ':!docs/specs/**' ':!docs/rfc/**' \
     ':!docs/adr/**' ':!workspace.toml'

git grep -n -I -E \
  'fresh-reader|readability review|hard .*word budget|word budget|progressive disclosure' \
  -- packs guides docs tools packages tests Makefile
```

All cited anchors were resolved with bounded `git blame -L` reads. No tests, network, origin probes, or write commands were run.

---

# Appendix B: OKF corpus pattern suitability

## 1. Mechanical shape

- **[Cited] Authored inputs:** a pack declares `[pack.metadata.okf]` with profile `agentbundle-okf/v1` and one or more bundles containing `id`, an `okf/...` source path, and a generated `router-skill`; see [core pack.toml](packs/core/pack.toml:49) and the [closed pack-profile schema](contracts/jsonschema/okf-pack-profile-v1.schema.json:12).

- **[Cited] Bundle layout:** `okf/<bundle>/index.md`, plus Markdown concepts below `concepts/`. The root index declares `okf_version: "0.2"`; concepts typically declare `title`, `type`, `status`, `license`, compatibility/provenance fields, and domain metadata. Examples: [security index](packs/core/okf/security-checklists/index.md:1) and [access-control concept](packs/core/okf/security-checklists/concepts/access-control.md:1).

- **[Cited] Schema strictness:** the compiler requires an OKF 0.2 root index, bounds YAML and lifecycle state, rejects executable or remote-retrieval metadata, but otherwise permits domain-specific concept keys; see [validation](.agents/skills/compile-okf/scripts/okf_compiler.py:222) and [metadata validation](.agents/skills/compile-okf/scripts/okf_compiler.py:2411). The optional `x-agentbundle` procedure projection is closed data: `profile`, then `skill.name`, `description`, `instruction-section`, and optional `include`; see [extension schema](contracts/jsonschema/okf-agentbundle-extension-v1.schema.json:9).

- **[Cited] Compiler:** `.agents/skills/compile-okf/scripts/compile_okf.py` calls `compile_pack()` ([entry point](.agents/skills/compile-okf/scripts/compile_okf.py:16)). It deterministically validates twice, generates hierarchical indexes, copies concept files, renders a router `SKILL.md`, optionally renders reviewed procedure skills, and writes an ownership/digest manifest; see [rendering](.agents/skills/compile-okf/scripts/okf_compiler.py:327) and [pack compilation](.agents/skills/compile-okf/scripts/okf_compiler.py:464).

- **[Cited] Generated outputs:** `.apm/skills/<router-skill>/SKILL.md`, `references/okf/**`, optional `.apm/skills/<procedure>/**`, and pack-root `.okf-generated.json`; output-path translation is in [the compiler](.agents/skills/compile-okf/scripts/okf_compiler.py:1107). The router itself contains only prose telling an agent to read the root index and descend selectively ([router template](.agents/skills/compile-okf/assets/router-wrapper.md:13)).

- **[Measured] Current projections are byte-current:** read-only `--check` returned `OKF000 check clean` for both `core` and `architect`.

## 2. Runtime path

- **[Cited] Generic path:** authored `pack.toml` + `okf/**` → `compile_okf.py` → generated `.apm/skills/**` → AgentBundle build/install → host-specific skill directory. Raw `okf/**` is not the runtime surface: the installer reads `.apm/` and `seeds/`; `.apm/` is expressly the runtime export boundary ([pack layout](docs/architecture/pack-layout.md:44)).

- **[Inferred from the host/file contract] Context path:** the host exposes or invokes the installed skill; its `SKILL.md` enters agent context. The router then tells the agent to read indexes and concepts. Those file-read results enter context through ordinary agent tool use. The compiler and installer do not retrieve relevant concepts during a task.

### Security-checklists

- **[Cited] Important split:** the runtime security-review path does **not** use the generated `security-checklists-reference` router. It uses the separate, hand-authored `.apm/skills/security-checklists/SKILL.md` and its hand-authored `references/*.md`. That skill bears the `router-handoff=author-owned` marker and explicitly describes itself as the reviewer’s depth library ([security-checklists](packs/core/.apm/skills/security-checklists/SKILL.md:6)).

- **[Cited] Exact operational trace:**

  1. `work-loop/SKILL.md` reaches the orchestrating agent.
  2. The agent is instructed to detect crossed trust boundaries.
  3. It reads the Markdown routing table in `security-checklists/SKILL.md`.
  4. It reads matching `references/<module>.md`.
  5. It constructs a subagent dispatch message containing that module text.
  6. The host combines that caller-supplied brief with `security-reviewer.md`.

- **[Cited] The decisive instruction is prose:**  
  > “detect which trust boundaries the diff crosses, load only the matching `security-checklists` modules, inline them into the subagent’s brief”  
  — [work-loop/SKILL.md](packs/core/.apm/skills/work-loop/SKILL.md:538).

- **[Cited] The library says the same thing:**  
  > “The orchestrator drives loading; the subagent does not.”  
  It then instructs the orchestrator to detect boundaries, load modules, and inline their content ([security-checklists/SKILL.md](packs/core/.apm/skills/security-checklists/SKILL.md:47)).

- **[Cited] Failure is tolerated by prose:** the reviewer says that if no modules were inlined, it should fall back to its universal method and report that fact ([security-reviewer.md](packs/core/.apm/agents/security-reviewer.md:106)).

### Architecture references

- **[Cited] Trace:** `packs/architect/okf/architecture-lenses/**` → compiler → `.apm/skills/architecture-lenses-reference/{SKILL.md,references/okf/**}` → adapter projection → consuming architect skill reads those files directly.

- **[Cited] `architect-assess` instructs the agent:**  
  > “Read `../architecture-lenses-reference/references/okf/index.md` first. Load the base concepts … then only the selected intent, observed shape, workload, quality, and enterprise concepts.”  
  — [architect-assess/SKILL.md](packs/architect/.apm/skills/architect-assess/SKILL.md:93).

- **[Cited] Routing remains Markdown prose:** “Every assessment loads” the base set, while intent, shape, workload, and quality concepts are chosen from textual trigger tables ([concept-routing.md](packs/architect/.apm/skills/architect-assess/references/concept-routing.md:6)).

- **[Cited] `architect-design` and `architect-review` likewise tell the active agent to descend into selected concepts; they do not invoke a prompt-building process.** See [architect-design](packs/architect/.apm/skills/architect-design/SKILL.md:90) and [architect-review](packs/architect/.apm/skills/architect-review/SKILL.md:96).

## 3. Central finding: PROSE-DIRECTED

- **[Cited] Compilation and installation are mechanical. Runtime relevance selection, file loading, and security-brief inlining are agent actions directed by prose.** There is no repository process that classifies the current diff, selects modules, concatenates them, and supplies the resulting prompt.

- **[Measured absence] Executable search:**

```text
$ rg -n 'security-reviewer|security-checklists|architecture-lenses-reference' \
    packs/core/.apm/skills/work-loop/scripts \
    packages/agentbundle/agentbundle tools \
    -g '*.py' -g '*.sh' -g '*.toml'

packages/agentbundle/agentbundle/commands/pack_evals.py:823:
  **not** trust operator `*_ok` booleans (security-reviewer Blocker 3).
```

- **[Measured absence] No test asserts selected module content appears in a real subagent brief:**

```text
$ rg -n -i 'inline.*(security-checklists|module)|security-checklists.*inline|brief.*(module|security-checklists)|selected.*module|matching.*module' \
    tests packs/core/tests packs/architect/tests packages/agentbundle/tests \
    -g '*.py' -g '*.json' -g '*.md'
# exit 1; no matches
```

- **[Cited] Existing tests check construction:** modules, routing-table strings, generated files, digests, and adapter-relative paths ([security construction tests](tests/roster/test_security_checklists_okf_projection.py:46), [architecture construction tests](packs/architect/tests/pack/test_architecture_lenses_corpus.py:203)). They do not observe a production dispatch prompt.

- **[Cited] A report-only, agent-executed security routing measurement exists, but it measures returned paths, not brief assembly or module application** ([measurement](docs/rfc/0087-notes/pilot-measurements/security-checklists-in-harness.json:3)). The separate model-E2E baseline remains explicitly pending ([pending baseline](docs/rfc/0087-notes/pilot-baselines/security-checklists-pending-model-e2e.json:2)).

- **[Inferred] Therefore the OKF pattern inherits the suspected activation failure:** it packages and routes prose more cleanly, but it does not mechanically ensure that the prose is selected, inserted, or applied.

## 4. Suitability for behavior policies

- **[Cited] Load conditions are prose.** Security uses the hand-authored Markdown boundary table; architecture uses “scope and routing signals” and textual trigger tables. The compiler’s generated indexes contain titles, statuses, types, and links; `_render_indexes()` does not interpret routing signals or boundary metadata ([index renderer](.agents/skills/compile-okf/scripts/okf_compiler.py:823)).

- **[Inferred] Cognitive-load reduction and the razor fit the file format but not the present activation model.** They can be written as reference concepts, but “apply during almost every authoring act” provides no selective trigger. Making them a base module would still depend on every authoring agent obeying “always load this base module.”

- **[Inferred] Repository anchoring fits conditional routing better:** it can fire on claims about named repository targets or current-system facts. It still would not be enforced mechanically under the present pattern.

- **[Cited] An authoring-behavior OKF precedent exists:** `instruction-density-and-progressive-disclosure` covers instruction placement, duplicated context, conditional references, and token-bearing duplication ([concept](packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/instruction-density-and-progressive-disclosure.md:10)). `progressive-result-presentation-and-next-actions` is another behavior-oriented concept ([concept](packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/progressive-result-presentation-and-next-actions.md:10)). These are reference knowledge, not universal enforcement.

## 5. Reach and cost

- **[Cited] Adopters receive compiled `.apm` skills and references, not raw authored `okf/**`.** The five adapters all project skills: Claude Code to `.claude/skills/`; Codex, Copilot, Cursor, and Gemini to `.agents/skills/` ([adapter contract](contracts/adapter.toml:183), [Copilot](contracts/adapter.toml:509), [Codex](contracts/adapter.toml:568), [Cursor](contracts/adapter.toml:632), [Gemini](contracts/adapter.toml:725)).

- **[Cited] Cross-adapter tests prove colocated files and resolvable relative paths, not behavioral honouring** ([adapter projection test](tests/roster/test_architect_architecture_lenses_corpus.py:124)). Agent projections also differ by host—direct Markdown, Codex TOML, or Copilot agent Markdown—so the parent-orchestrator behavior remains host/model-dependent.

- **[Cited] Progressive disclosure is governed only by router prose:** “do not load the full bundle up front” ([generated router](packs/core/.apm/skills/security-checklists-reference/SKILL.md:13)).

- **[Cited] There is no context-token ceiling or token measurement.** Compiler safety limits are filesystem limits: 4,096 files, 2,000 concepts, 32 MiB total, and 2 MiB per Markdown file ([limits](.agents/skills/compile-okf/scripts/okf_compiler.py:46)). These permit material far larger than a useful prompt.

- **[Measured counts]:**

```text
$ find packs/core/okf/security-checklists/concepts -type f -name '*.md' -print | wc -l
11

$ find packs/architect/okf/architecture-lenses/concepts -type f -name '*.md' -not -name 'index.md' -print | wc -l
47
```

- **[Measured] No files were created or edited by this inspection. The checkout already contains unrelated modified and untracked brief/workspace files.**

**[Inferred verdict] UNSUITABLE — the strongest reason is that the critical selection-and-inlining step is an unchecked instruction to an orchestrating agent, not a mechanical operation, so the proposal preserves the same prose-activation failure it is meant to solve.**