# Phase-scoped policy delivery: what exists today

> Discipline: repository inventory (measured)

Commissioned 2026-09-03 for the `cross-adapter-behavior-enforcement` intent. Traces how guidance reaches an acting agent per phase, and whether prevention and detection coexist for any rule today. Retained so the intent can cite it rather than restate it.

---

## 1. Existing inlining precedents

| Precedent | Relevance decision | Inlining instruction | Consumer | Actual control |
|---|---|---|---|---|
| `cloud-implementation-craft` | The `operational-safety` Module index says: “authoring infra / a managed-runtime deployment / live interaction” ([module row](packs/core/.apm/skills/operational-safety/SKILL.md:156)). “Infra-flavored” is further defined as the destructive/irreversible trigger plus the security index’s IaC/deploy-config match ([definition](packs/core/.apm/skills/work-loop/references/pre-execute-review.md:241)). | The infra reference says the orchestrator “inlines” the module into the implementer’s EXECUTE brief through the Module index ([instruction](packs/core/.apm/skills/work-loop/references/infra-verification.md:187)). | `implementer`; its contract expects the module as context and says not to load the skill itself ([consumer contract](packs/core/.apm/agents/implementer.md:31)). | **PROSE-DIRECTED decision and PROSE-DIRECTED inlining.** [Cited] The index calls itself deterministic, but an agent detects the trigger, reads the file, and composes the brief. No executable dispatcher implements those steps. |
| Operational failure-mode modules: `state-and-idempotency`, `blast-radius`, `environment-isolation`, `cost-and-teardown`, `drift-and-rollback`, `observability-and-smoke`, and—when applicable—`cloud-implementation-craft` | The Module index’s `Load when` column maps observed failure modes to modules ([index](packs/core/.apm/skills/operational-safety/SKILL.md:126), [rows](packs/core/.apm/skills/operational-safety/SKILL.md:148)). The outer trigger is infra/destructive or persistent-representation/mixed-version work ([trigger](packs/core/.apm/skills/operational-safety/SKILL.md:51)). | The library instructs the orchestrator to detect failure modes, load matching files, and inline their contents into the reviewer brief ([three steps](packs/core/.apm/skills/operational-safety/SKILL.md:51)). Work-loop repeats that direction ([REVIEW instruction](packs/core/.apm/skills/work-loop/SKILL.md:540)). | `quality-engineer`, whose own contract expects those modules and forbids self-loading them ([consumer contract](packs/core/.apm/agents/quality-engineer.md:68)). | **PROSE-DIRECTED decision and PROSE-DIRECTED inlining.** [Cited] The routing table is deterministic data-like prose; applying it to a diff and inserting the selected text are model actions, not code. |

The clearest deciding quotations are:

> “Detects which operational failure modes the diff or spec crosses.”  
> “Loads only the matching modules…”  
> “Inlines the selected modules’ content…”  
> — [operational-safety loading procedure](packs/core/.apm/skills/operational-safety/SKILL.md:51)

> “On infra-flavored work, the orchestrator inlines the `cloud-implementation-craft` module … into the implementer’s EXECUTE brief.”  
> — [infra-verification](packs/core/.apm/skills/work-loop/references/infra-verification.md:187)

## 2. Current phase-to-guidance map

| Phase/surface | Guidance that reaches the actor | Arrival |
|---|---|---|
| Spec authoring: `new-spec` | `new-spec/SKILL.md`; its managed output-rendering block; `assets/spec.md`; effective root/scoped `AGENTS.md`; mapped architecture, decisions, conventions, and analogous implementations ([procedure](packs/core/.apm/skills/new-spec/SKILL.md:60)). Interface-bearing specs conditionally use `contract-types`; UI specs conditionally use `creative-direction`/`design-review`. | Skill invocation plus actor-directed reads. Templates are copied. Conditional additions are selected by prose. [Cited] |
| Plan authoring | The same `new-spec` skill authors `plan.md`; there is no separate plan-author skill. `assets/plan.md` supplies Design/LLD, task, dependency, `Tests:`-before-`Approach:`, and durable-output structure ([template](packs/core/.apm/skills/new-spec/assets/plan.md:91), [tasks](packs/core/.apm/skills/new-spec/assets/plan.md:161)). | Template plus prose in `new-spec`; `Shape:` controls which design subsections the author retains. [Cited] |
| Work-loop PLAN / pre-EXECUTE | Work-loop itself; repository anchors; verification-mode guidance; conditional `tdd-stubs`, `verification-modes`, `infra-verification`, and `pre-execute-review`. Fired review roles are adversarial, security, design-intent, and frontend pre-flight ([trigger table](packs/core/.apm/skills/work-loop/SKILL.md:290)). Security review receives matching `security-checklists` modules. | Actor loads references when prose triggers fire. Security modules are prose-directed inline prompt text. FSM state mechanically prevents illegal phase transitions, but does not assemble prompts. [Cited] |
| EXECUTE / implementation | Main actor: work-loop verification-mode discipline, conditional `contract-acquisition`, conditional `frontend-engineering`, and conditional infra reference ([EXECUTE](packs/core/.apm/skills/work-loop/SKILL.md:399)). Subagent: `implementer.md`, task body, worktree path, spec/plan paths, cited files, optional bundled-fix authorization, and conditional `cloud-implementation-craft`. | Base implementer contract is projected agent configuration. Task/spec/plan are brief fields or reads. `cloud-implementation-craft` is prose-directed inlining. [Cited] |
| GATES | Repository-defined lint/typecheck/test commands; frontend pack’s GATES commands when activated; infra’s layered static/preview/apply/smoke/rollback doctrine when applicable ([GATES](packs/core/.apm/skills/work-loop/SKILL.md:437)). | Read from `AGENTS.md`, README, active pack guidance, and plan task. Exit codes and FSM transitions are mechanical. No policy module is inlined at this phase. [Cited] |
| Post-gates REVIEW | Always adversarial review; then warranted specialists. Security gets boundary-matched `security-checklists`; quality gets failure-mode-matched `operational-safety`; quality also receives `contract-acquisition`; experience/frontend/design reviewers get their named artifacts and rubrics ([reviewers](packs/core/.apm/skills/work-loop/SKILL.md:527)). | Reviewer selection and module inlining are prose-directed. Report persistence, path validation, strict classification, counters, and FSM transitions are mechanical. [Cited] |
| Closeout | Separate `close-work` skill, not work-loop. It consumes the work-loop evidence envelope, workspace state, durable-output map, semantic-surface resolver, and its own disposition/safety rules ([boundary](packs/core/.apm/skills/close-work/SKILL.md:42)). | Skill invocation and actor-directed reads. `close_work.py` and `cooling.py` provide the deterministic decision/effect seam ([seam](packs/core/.apm/skills/close-work/SKILL.md:119)). [Cited] |

## 3. Can module arrival be checked?

**No dispatched-brief arrival check exists.** [Measured]

Searches used:

```text
rg -n "cloud-implementation-craft" packs/core/tests packages/agentbundle/tests tools .github
```

The only hit was the IaC canary’s module pathname. That canary checks that the reference file exists ([workflow](.github/workflows/iac-release-loop-canary.yml:34)); it does not inspect a brief.

```text
rg -n "inlined.{0,40}(brief|prompt)|brief.{0,40}inlined|prompt.{0,40}module|selected modules.{0,40}brief" \
  packs/core/tests packages/agentbundle/tests tools .github
```

Exit status: `1`; no matches.

```text
rg -n "developer_instructions|prompt|brief" \
  packs/core/.apm/skills/work-loop/scripts/loop-cohort.py \
  packs/core/.apm/skills/work-loop/scripts/loop-engine.py \
  packs/core/.apm/skills/work-loop/scripts/_loop_guards.py
```

No prompt or brief assembler appeared. [Measured]

The supervisor procedure does enumerate ordinary brief fields—task ID/body, worktree, spec/plan paths, and bundled-fix authorization ([brief fields](packs/core/.apm/skills/work-loop/references/supervisor-mode.md:115)). Its mechanical report check validates the returned task heading, not the input brief or module presence ([report check](packs/core/.apm/skills/work-loop/references/supervisor-mode.md:128)). [Cited]

## 4. Existing “taught and checked” rule

**Yes: credential values must never travel through a credentialed CLI’s argv.** [Cited]

| Half | Implementation |
|---|---|
| Prevention / teaching | The acting implementer reads `docs/CONVENTIONS.md`; that document says credentialed skills never touch the token ([architecture](docs/CONVENTIONS.md:1393)) and names the six forbidden value flags ([argv ban](docs/CONVENTIONS.md:1500)). Each credentialed skill must also carry an exact broker-specific “Never put … on the command line” instruction. |
| Detection / deterministic check | `CAT-L031` requires the security heading and broker-specific teaching phrases ([phrase check](packages/agentbundle/agentbundle/catalogue_tooling/lint.py:2023)), then AST-walks credentialed CLI scripts and rejects banned `argparse.add_argument` flags ([artifact check](packages/agentbundle/agentbundle/catalogue_tooling/lint.py:2056)). A fixture proves `--api-key` produces `CAT-L031` ([test](packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py:1944)). |

Both halves live in the same `_check_credentialed_skills` check: required teaching phrases are data in `_CS_REQUIRED_PHRASES_BY_BROKER`, while executable prohibitions are data in `_CS_BANNED_FLAGS` ([constants](packages/agentbundle/agentbundle/catalogue_tooling/lint.py:784)). [Cited]

They are co-located and tested, but not generated from one semantic rule: the prose flag list and `_CS_BANNED_FLAGS` remain duplicate representations. Thus this is a real “both” precedent, with a residual synchronization risk. [Inferred]

## 5. Existing phase-scoped selection keys

| Candidate key | Declared data or inferred? | Current mechanical use |
|---|---|---|
| Work-loop phase | **Declared, tool-written data.** `engine-state.json.state` has explicit FSM values from `SPEC-PLAN-DRAFTING` through `DONE` ([schema](packs/core/.apm/skills/work-loop/references/state-schema.md:84)). | Mechanical transition and guard enforcement. This is the strongest existing phase key. |
| Spec `Shape:` | **Declared in `spec.md`, but selected by an agent or user.** Allowed values are `ui`, `service`, `data`, `integration`, `mixed` ([field](packs/core/.apm/skills/new-spec/assets/spec.md:10)). | Prose directs plan scaffolding and UI readiness. No `Shape:` reader was found in work-loop/new-spec scripts. [Measured] |
| Task verification mode | **Declared in plan prose after agent selection.** TDD, goal-based, visual/manual, and infra/deploy are selected during PLAN ([selection](packs/core/.apm/skills/work-loop/SKILL.md:278)). | Implementer follows it. Search of work-loop/new-spec scripts for these mode names returned no matches, so declaration/presence is not mechanically parsed. [Measured] |
| Task dependency fields | **Declared plan data-like prose:** task ID, `Depends on:`, optionally `Touches:` ([grammar](packs/core/.apm/skills/new-spec/assets/plan.md:188)). | Mechanically parsed for scheduling and overlap prediction. It does not currently select policy. |
| Infra/task flavor | **Inferred by an agent.** The repository gives a closed prose definition, but no persisted `flavor` field or classifier function was found. | Drives infra references, reviewers, and module selection through prose. |
| Pack membership | **Declared data** in `pack.toml`; integrations also declare consumer/provider/`when` metadata ([frontend integration](packs/core/pack.toml:77)). | Installation/projection is mechanical. Whether a phase condition fires is still evaluated by work-loop prose. |
| Profile membership | **Declared data** as `[[packs]]` entries ([example](profiles/full-ceremony.toml:12)). | Mechanically selects installed packs, but profiles “introduce no new skills, agents, hooks, or commands”; they are coarse installation-time scope, not runtime phase state. |

## 6. Implementer’s real contract

| Aspect | Contract |
|---|---|
| Declared inputs | One plan task, worktree path, spec path, and plan path ([frontmatter description](packs/core/.apm/agents/implementer.md:2)); then `AGENTS.md`, `docs/CONVENTIONS.md`, the targeted spec/plan, cited files, and conditional cloud module ([load order](packs/core/.apm/agents/implementer.md:19)). [Cited] |
| Source tool allowlist | `Read, Edit, Write, Grep, Glob, Bash` ([frontmatter](packs/core/.apm/agents/implementer.md:4)). No web, Skill, or agent-dispatch tool. [Cited] |
| Source model | `sonnet` ([frontmatter](packs/core/.apm/agents/implementer.md:5)). [Cited] |
| Current Codex projection | `gpt-5.5`, medium reasoning, `workspace-write`, web disabled ([projected config](.codex/agents/implementer.toml:1)). The adapter contract maps `sonnet` to those values and turns any write intent into a writable sandbox ([mapping](contracts/adapter.toml:854)). [Cited] |
| Required | Implement only the assigned task; obey its verification mode; run documented gates; commit; return the fixed report shape. [Cited] |
| Permitted | Edit within the assigned worktree. Optional ride-alongs are permitted only when the brief explicitly authorizes bundled fixes and they meet the three-tier carve-out ([envelope](packs/core/.apm/agents/implementer.md:46)). [Cited] |
| Forbidden | Reviewing the spec/plan, dispatching subagents, merging, editing the primary worktree, silently widening scope, editing gates to pass, or reporting ready with failed gates ([anti-patterns](packs/core/.apm/agents/implementer.md:143)). [Cited] |

Mechanically constrained: model choice, writable-vs-read-only sandbox, web disablement, and—with adapter differences—the exposed tool surface. The supervisor can mechanically check the returned task heading against the assigned ID. [Cited]

Not mechanically constrained: “one task,” exact worktree confinement within the writable workspace, no self-review, no merge, verification-mode compliance, gate honesty, and inclusion of the cloud module. Those remain prose contracts. [Inferred]

## 7. Cost and ceilings

No implementer-brief token budget, prompt-size limit, line ceiling, or module-byte ceiling was found. [Measured]

Search:

```text
rg -n -i \
  "token budget|context budget|brief.{0,40}(limit|ceiling|max|budget)|prompt.{0,40}(limit|ceiling|max|budget)|line ceiling|line limit|max.{0,20}lines" \
  packs/core/.apm/agents/implementer.md \
  packs/core/.apm/skills/work-loop \
  packs/core/.apm/skills/operational-safety \
  contracts/adapter.toml docs/CONVENTIONS.md
```

Result: no matches.

The only applicable cost control is progressive disclosure: load only matching modules so “the agent prompt stays lean” ([rationale](packs/core/.apm/skills/operational-safety/SKILL.md:8)). That is a selection rule, not a measured ceiling. [Cited]

Measured source sizes:

```text
wc -l packs/core/.apm/agents/implementer.md \
      packs/core/.apm/skills/operational-safety/references/cloud-implementation-craft.md
```

Result: 154 lines and 109 lines, 263 combined. [Measured]

Work-loop explicitly says token-budget state fields are absent in Phase 1 ([state schema](packs/core/.apm/skills/work-loop/references/state-schema.md:76)). The implementer’s “be terse” rule applies to its returned report, not its input brief ([report rule](packs/core/.apm/agents/implementer.md:94)). [Cited]

## Direct answer

**Phase-scoped policy delivery is achievable by extending the current mechanism:** the work-loop’s orchestrator-driven `Module index → select matching reference → inline into phase-specific subagent brief` mechanism, keyed first by the mechanically recorded FSM phase and then by declared task/spec attributes. [Inferred]

It does not need a new conceptual delivery mechanism. It **does need a new mechanical prompt-assembly/arrival validator** if “delivery” must be provable: today both selection and inlining are prose-directed, and nothing records or checks that the selected module reached the implementer’s brief.