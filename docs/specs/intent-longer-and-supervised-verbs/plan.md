# Plan: intent-longer-and-supervised-verbs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:**
  - The slice 1 fold: `docs/specs/intent-short-route/` (spec, plan, and `notes/`), and
    the `intent` skill it built, for the mode table, one procedure per mode, the
    `Stage:` and `## Next` shape, the evidence note, and the activation driver.
  - `packs/product-engineering/tests/pack/test_intent_skill_structure.py`, which pins
    that shape and is extended here.
  - `packages/agentbundle/agentbundle/commands/pack_evals.py`, the activation runner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `notes/verification-ledger.md`. A genuine artifact error follows the
> controlled-amendment path.

## Approach

The order is the slice 1 order: measure first, build beside the old skills, switch, then
delete only after the evidence passes.

1. Build `initiative` beside the sources, moving the longer-route modes out of `intent`;
   `intent` keeps `ground` and `de-risk`'s validation-plan section. Trim `discovery-loop`.
   Every candidate description is then final.
2. Hash those descriptions, write a fresh held-out set, and record the pre-fold activation
   baseline on it while the nine sources exist. The pre-fold probe of 2026-10-11 stands.
3. Split the evals, then retarget Core, the package, other packs, tools, tests, guides,
   and docs.
4. Prove routing and activation in a world where the sources are gone.
5. Accept ADR-0145, then write the erratum and the brief edit, delete the sources, bump
   versions, record the release, and self-host.

The riskiest part is still activation. ADR-0145 splits the modes so each description has
room for the nouns users type; whether that recovers the narrow skills' trigger rate is
what the activation run decides.

## Constraints

- RFC-0107 D1, D2, and D6, ADR-0140, and ADR-0145: route mode stays stateless and lives
  only in `intent`, `discovery-loop` stays separate and calls modes of both `intent` and
  `initiative`, and retired names get no alias. ADR-0145 stays `Proposed` until the T8
  evidence passes.
- ADR-0111 D8, as its Errata entry reads: the `de-risk` mode never dispatches
  `adversarial-reviewer`. The validation-plan section inherits that rule.
- `packs/AGENTS.md`: shipped pack content cites no internal governance record, every
  non-cosmetic pack change bumps the pack, and a pack update also updates its eval
  harness.
- `tools/lint-pack-test-boundary.py`: pack tests read nothing above their pack, and
  build paths from literal segments.
- Commits touching `packages/agentbundle` carry an `Engine-Change-RFC:` trailer.

## Construction tests

**Integration tests:**
- `test_intent_skill_structure.py`, `test_intent_triad_execution_wiring.py`,
  `test_architect_optional_offers.py`, and `test_de_risk_intent_reviewer_boundary.py`;
- `tools/test_workspace_status.py`;
- `tests/roster/test_skill_census.py`, `tests/roster/test_rfc0099_activation_coverage.py`,
  and `tools/test_live_demo_guide.py`.

**Manual verification:** AC-0010.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise: guides and graphic | T7 | Edited guides; regenerated SVG | AC-0016, AC-0018, AC-0034 |
| Product truth: pack and site pages | T7 | Edited pages | AC-0016 |
| Architecture: `lifecycle-flow.md` | T7 | Edited flow | AC-0016 |
| Decision rationale: ADR-0145, RFC-0107 erratum, brief | T9 | The accepted ADR, the erratum, and the edited brief | AC-0044, AC-0046, AC-0047 |
| Release history: changelogs | T9 | Entries for each released artifact | AC-0030 to AC-0033 |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T7, T8, T9

- **Two skills.** ADR-0145 decides the split. `intent` holds route, `frame`, `de-risk`,
  `decompose`, and `ground`. `initiative` holds `situate`, `find`, `diverge`, `bet`,
  `map`, and `canvas`, with no route mode. Each mode's procedure body is
  `references/<mode>.md` of its skill. The source assets and examples move flat into the
  skill holding their mode, and `map`'s two example folders keep their subfolders, giving
  the file sets AC-0011 lists. The longer-route modes cite no shared `intent` reference
  file, so `initiative` needs no copy of one.
- **Cross-skill names.** A mode reference names its own skill's modes and the other
  skill's modes with their skill prefix (`intent de-risk`, `initiative bet`), so an
  offer always names an invocable target.
- **Two-procedure modes.** `diverge.md` opens with one entry rule: a scored initiative or
  capability opportunity runs the options procedure, which writes `solution-options.md`;
  a framed intent that wants candidate product shapes runs the shapes procedure, which
  writes discovery slots. `de-risk.md` keeps its single-bet procedure and gains a
  validation-plan section, entered when a converged set of assumptions needs a validation
  plan and instrument scaffolds. Neither section adds a dispatch.
- **Save paths stay as the sources had them.** `canvas` writes
  `docs/product/initiatives/<slug>.md`, `ground` writes under
  `docs/discovery/<initiative>/`, and the slot-writing procedures write no file.
- **Shape directives.** `tools/add-rendering-directives.py` maps each skill to its output
  shapes and manages only `SKILL.md`. Each moved body drops its managed block.
  - T7 adds an `intent` entry (narrative, key-value, tree: `frame-domain`'s narrative
    and key-value, `plan-validation`'s key-value, and the key-value, narrative, and tree
    lines slice 1 left in `frame.md`, `de-risk.md`, and `decompose.md`) and an
    `initiative` entry (table, narrative, key-value: the union of the other seven
    sources'), so the measured `SKILL.md` files are the ones that ship.
  - T9 removes the nine source entries, together with the deletion. Removing an entry
    earlier marks its source stale.
  - The tool has no path filter, and `--write` rewrites every drifted skill. On
    2026-10-11 `--check` already reported five unrelated skills as drifted:
    `agent-skill-engineering`'s `author-or-update-agent-skill` and
    `review-or-optimize-agent-skill`, Core's `explain-diff`, `experience-design`'s
    `information-architecture`, and `repo-governance`' `navigate-decisions`. T4 to T6
    are committed before T7 runs `--write`. Just before `--write`, T7 lists the paths
    `--check` reports other than `intent/SKILL.md` and `initiative/SKILL.md`. If that
    list is not exactly those five `SKILL.md` files, T7 stops and asks the owner.
    Otherwise, after `--write`, it restores exactly those five paths with
    `git checkout --`.
- **Tool authority.** No source declared `allowed-tools` or boundaries. `ground`'s
  research goes through an optional `desk-research` call, so neither skill needs a new
  boundary.
- **The descriptions.** `intent` names its four verbs, says route mode applies only when
  the user asks which way to shape, and names four exclusions: `intake-intent`,
  `new-spec`, `discovery-loop`, and `initiative`. `initiative` names its six verbs with
  the concrete artifact each produces, and excludes `intent` and `discovery-loop`. Changes
  after the probe has run follow the Ask-first rule.
- **The `discovery-loop` description.** At most 600 characters. It keeps its five trigger
  phrases, names the `work-intake` hand-off, and sends a standalone discovery artifact to
  `intent ground` or `initiative diverge`.
- **Probe cases.** The 24 cases in `notes/probe-cases.json` stay fixed. Their pre-fold
  run of 2026-10-11 is the recorded baseline; the pre-fold descriptions are unchanged
  since. T2 updates each case's expected post-fold selection to AC-0024's table.
- **The held-out activation set.** The AC-0029 set, all new queries, written in T1 and
  never shown to the probe. It replaces the 2026-10-11 set, which informed two description
  revisions. A repeated pre-fold baseline on 2026-10-12 gave the same 0.856 positive
  rate, with an aggregate standard error of about 0.019, so the 3-point bound is about
  1.5 standard errors.
- **Where the activation runs happen.** As in the first attempts:
  - Each world is projected pack by pack (`product-engineering`, `core`, `architect`)
    into fresh OS temporary directories outside every repository, then merged.
  - A scratch driver outside the repository calls `run_eval` with `project_root` set to
    that projection and a detector that wraps `ClaudeCodeDetector` and adds
    `--setting-sources project,local`, logging each run's fired skills.
  - The pre-fold world is a disposable detached worktree of the base commit. Each
    source's query file holds its owned positives, `intent`'s holds the `frame`,
    `de-risk`, and `decompose` positives, and one file also holds the 12 negatives.
  - A negative's false-trigger rate counts runs where `intent`, `initiative`, or any
    source fired.
  - The post-fold world is a second disposable worktree after T7, with the sources
    deleted, `[pack.evals].skills` updated, self-host run, and each skill's query file
    holding the held-out positives of its modes; `intent`'s also holds the negatives.
  - Both worlds also run `discovery-loop`'s query file as it stood before this change.
  - Queries run in parallel jobs, each in its own copy of the projection. Nothing from
    either worktree is committed.

### Behavior & rules

Owned by: T2

- **Route mode.** The longer route's signal stays "the problem itself is unclear, or the
  bet is large". Its first step becomes `initiative situate`.
- **Lifecycle map.** `intent` owns the full map. The longer route lists the five
  `initiative` modes and `intent de-risk` in order, then the hand-off. The supervised
  route lists the modes `discovery-loop` calls at each gate. `initiative canvas` sits
  under a short "Off the routes" note. `initiative/SKILL.md` repeats only the longer
  route, and a pack test holds the two lists equal.
- **Next offers.** Offers are phrased as questions, and no mode starts another. When the
  conversation shows no route, `de-risk` asks which route applies. `situate`'s offer
  follows its own entry-point rule: an unknown problem leads to `find`, known problems
  with unknown options lead to `diverge`, and known options needing a committed bet lead
  to `bet`.
- **Replies.** Each mode's `Stage:` line ends "Name this stage in the first line of every
  reply this mode gives." The 2026-10-12 walks showed standalone replies skipping the
  stage without it.
- **Readiness notes.** A note that fires when a now-folded skill is absent is removed.
  A note about a skill outside the two, such as `author-delivery-brief`, stays.

### Dependencies & integration

Owned by: T4, T5, T6, T7, T9

Callers come from a case-sensitive search for the nine names, taken on 2026-10-11 over
187 tracked files. They cluster here:

- **product-engineering:**
  - `discovery-loop` (skill, references, assets) and both discovery agents;
  - `intent` references that name a source or a longer-route mode;
  - `align-value-stream`'s evals and layout reference;
  - two `pack.toml` integrations and `[pack.evals].skills`;
  - `README.md`, `JOURNEY.md`, `DESIGN.md`, and the pack tests.
- **Core:**
  - the `strategy` row in `_SHAPING_TYPE_TO_SKILL`, in `workspace_status_engine.py` and
    `workspace-status/SKILL.md`;
  - `work-loop/SKILL.md`'s shaping-item guard;
  - `new-spec/references/spec-and-plan-contract.md`.
- **Package:** the `_data` engine mirror and `workspace_mcp.py`.
- **Other packs:**
  - `desk-research/SKILL.md`;
  - `product-strategy`'s `run-okr-cascade` skill, evals, and routing reference, plus its
    pack docs;
  - `experience-design`'s `creative-direction/references/grounding.md`.
- **Tools and roster:**
  - `render-lifecycle-graphics.py` and `add-rendering-directives.py`;
  - the `RETIRED_SHAPING_SKILLS` constants in `test_intent_skill_structure.py` and
    `test_intent_triad_execution_wiring.py`, which gain the nine names in T9, together
    with the deletion, because one test asserts every listed name is absent. The constants
    in `tools/test_live_demo_guide.py` and `tests/roster/test_rfc0099_activation_coverage.py`
    pin frozen records and stay unchanged;
  - `test_architect_optional_offers.py`, whose body reads move to the mode references;
  - the skill census fixture.
- **Docs:**
  - the guide pages and three site pages;
  - `lifecycle-flow.md`, three journey records, `workspace-toml-deps.md`, and
    `docs/product/initiatives/_template.md`, which `canvas` builds from;
  - a `workspace.toml` comment that cites line numbers in the retired skills;
  - two Draft specs: `guide-invocation-outcome-coverage` and
    `how-to-sample-output-coverage`.
- **Decision records:** ADR-0145's status and `docs/adr/README.md`, RFC-0107 § Errata,
  and the brief's Outcome, success metric, Scope mode map, eval lines, and
  `discovery-loop` line.

## Tasks

### T1 — Fresh held-out set and pre-fold activation baseline

**Depends on:** T2, T4
**Mode:** activation
**Touches:** `docs/specs/intent-longer-and-supervised-verbs/notes/`
**Tests:**
  - The ledger records the hash of each candidate description this change edits
    (`intent` and `initiative` from T2, `discovery-loop` from T4) before the fresh
    held-out set is written. The set shares no query with the 2026-10-11 set, any eval
    file, or the probe cases, and no held-out query or five-word run from one appears in
    a candidate description (AC-0029).
  - Its pre-fold run, plus `discovery-loop`'s pre-change query file, is recorded with
    zero errored runs and the host's listed skills (AC-0029).
**Done when:** the ledger holds the pre-fold result.

### T2 — Build `initiative` beside the sources

**Depends on:** none
**Mode:** goal-based
**Touches:** `packs/product-engineering/.apm/skills/intent/**`,
`packs/product-engineering/.apm/skills/initiative/**`, the pack tests,
`notes/probe-cases.json`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`
**Tests:**
  - `test_intent_skill_structure.py` and a new `initiative` structure test cover AC-0001,
    AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0011,
    AC-0039, AC-0041, AC-0043, AC-0042 over the files T2 writes (each skill's `SKILL.md`,
    `references/`, `assets/`, and `examples/`), and AC-0036's no-marker half. The longer-route
    check reads `initiative/references/situate.md`.
  - `test_de_risk_intent_reviewer_boundary.py` passes (AC-0012).
  - `test_skill_census.py` passes, with `initiative` added to the census fixture.
  - The modules that read the nine sources still pass while the sources exist.
**Done when:** these tests pass and catalogue lint is clean.

### T3 — Split the evals

**Depends on:** T2
**Mode:** goal-based
**Touches:** `intent/evals/**`, `initiative/evals/**`, `notes/verification-ledger.md`
**Tests:**
  - An owner, polarity, mode-key, and duplicate check over each skill's query file
    (AC-0021, AC-0045), including the cross-owned carried queries the ledger lists.
  - AC-0042 over both skills' `evals/` folders.
  - The per-mode positive counts and the cross-skill and other negatives (AC-0022).
  - The `frame-domain` `evals.json` carry-or-drop listing, and
    `test_architect_optional_offers.py` reading its eval ids from `intent/evals/`
    (AC-0023).
**Done when:** these tests pass.

### T4 — `discovery-loop`, `discovery-lead`, and the discovery guide

**Depends on:** T2
**Mode:** goal-based
**Touches:** `discovery-loop/**` (including its evals), `agents/discovery-lead.md`,
`agents/discovery-reliability-reviewer.md`, `guides/product-engineering/how-to/run-a-discovery.md`,
`tests/roster/test_discovery_handoff_wording.py`, `notes/verification-ledger.md`
**Tests:**
  - `test_intent_triad_execution_wiring.py`, extended for AC-0013, AC-0014, AC-0038,
    AC-0040's query presence, and AC-0015 over the two pack files.
  - `tests/roster/test_discovery_handoff_wording.py` applies the AC-0015 pattern to
    `run-a-discovery.md`, with the fixed cases the criterion names.
  - The ledger lists the owner of each AC-0040 query.
  - AC-0042 over the `discovery-loop` files T4 writes, its description included, so the
    description is final before T1 hashes it.
**Done when:** these tests pass.

### T5 — Core and package callers

**Depends on:** T2
**Mode:** TDD for the `strategy` mapping; goal-based otherwise
**Touches:** the Core files and package mirror named in Design,
`tests/roster/test_workspace_status_progressive_disclosure.py`, `tools/test_workspace_status.py`,
`guides/core/explanation/two-room-model.md`, `guides/core/tutorials/your-first-workspace.md`,
`docs/product/workspace-toml-deps.md`, `notes/verification-ledger.md`
**Tests:**
  - `tools/test_workspace_status.py` expects `initiative` for `strategy` (AC-0017).
  - The `BACKEND_DIGESTS` pin for `workspace_status_engine.py` and the work-loop contract
    hash are re-pinned, each with a ledger entry.
  - The AC-0048 surfaces name `initiative` as the `strategy` destination.
**Done when:** these pass.

### T6 — Other packs and integrations

**Depends on:** T2
**Mode:** goal-based
**Touches:** `desk-research`, `product-strategy`, `experience-design`, and
`product-engineering/pack.toml`'s integrations
**Tests:**
  - The AC-0020 integration values, and catalogue lint.
  - The `product-strategy` and `experience-design` lines AC-0049's search finds name
    `initiative` or an `initiative` mode.
**Done when:** these pass.

### T7 — Tools, tests, guides, site, and docs

**Depends on:** T3, T4, T5, T6
**Mode:** goal-based
**Touches:** tools and their tests, `test_architect_optional_offers.py`, `guides/**`,
`web/src/content/**`, the pack docs, `docs/architecture/lifecycle-flow.md`,
`docs/product/journeys/`, `docs/product/workspace-toml-deps.md`,
`docs/product/initiatives/_template.md`, `workspace.toml`, the two Draft specs,
`packs/product-engineering/.apm/skills/intent/SKILL.md`, and
`packs/product-engineering/.apm/skills/initiative/SKILL.md`
**Tests:**
  - The AC-0016 search, excluding the nine source directories, `[pack.evals].skills`,
    the census fixture, and the nine map entries in `tools/add-rendering-directives.py`,
    all of which T9 clears.
  - The AC-0018 guide check.
  - The AC-0042 search over the AC-0016 surfaces, recorded in the ledger. The pack tests
    from T2 and T3 cover the two skill folders.
  - The AC-0049 search, with every hit and its disposition recorded in the ledger,
    including the `workspace.toml` comment and `route-it-to-work.md`.
  - The AC-0034 regeneration check.
  - The `intent` and `initiative` map entries and the two `SKILL.md` rewrites (AC-0036).
    Each path `--check` listed before `--write`, other than those two, shows no diff
    against the branch's merge base with `origin/main`.
**Done when:** these tests pass.

### T8 — Post-fold probe, activation, and walks

**Depends on:** T1, T3, T7
**Mode:** bounded routing-classification evidence; activation; manual QA
**Touches:** `notes/`
**Tests:**
  - One scored post-fold attempt: the AC-0024 cases, three runs each, on one
    byte-identical candidate set (AC-0026), passing AC-0025, with the AC-0028 caveat.
  - The shipped descriptions match that attempt's candidates byte for byte (AC-0027).
  - The attempt's candidate descriptions match hashes the ledger recorded before the
    held-out set was written, or, for a revised description, before that attempt; each
    revised description passes the five-word-run check (AC-0029).
  - One post-fold activation run on those descriptions, against every AC-0029 bound.
  - A new scored attempt only after a recorded failure, an owner revise choice, and a
    changed candidate description.
  - The source-to-mode diff at a recorded base commit, with each hunk attributed to an
    exempt edit (AC-0037's first half).
  - The AC-0010 walks, headless with `--permission-mode acceptEdits --allowed-tools
    "Skill Read Write Edit Agent Glob Grep"`, with an owner, non-goals, and a save path
    supplied so the walk reaches each mode's end. The ledger records those grants.
**Done when:** every check passes. Any failure stops the slice here, before T9.

### T9 — Delete sources, bump, record, self-host, and observe

**Depends on:** T8
**Mode:** goal-based
**Touches:** the nine source directories, `pack.toml` and `plugin.json` files, the
`packages/agentbundle` version files, `docs/product/changelog.md`,
`packages/agentbundle/CHANGELOG.md`,
`packs/agent-skill-engineering/tests/fixtures/skill-census.json`, the two pack-test
`RETIRED_SHAPING_SKILLS` constants, `tools/add-rendering-directives.py`,
`docs/adr/0145-shaping-entry-points-intent-and-initiative.md`, `docs/adr/README.md`,
`docs/rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md`,
`docs/product/briefs/verb-mode-skills-and-slice-handover.md`, and the projections
**Tests:**
  - First: eugenelim's sign-off sets ADR-0145 to `Accepted`, recorded in the ledger, and
    `python3 .claude/skills/new-adr/scripts/index-records.py docs/adr` regenerates the
    ADR index, and its `--check` run reports no change (AC-0047). Then the RFC-0107
    erratum (AC-0044), the brief edit (AC-0046), and the deletions, each with its own
    dated ledger entry in that order.
  - AC-0016 directory absence and the full search again, the AC-0042 and AC-0049
    searches again, and AC-0019 membership.
  - `test_skill_census.py` passes with the nine entries removed.
  - AC-0030 versions.
  - The changelog entries for AC-0031, AC-0032, and AC-0033.
  - An install-then-upgrade observation of a removed skill directory, recorded in the
    ledger, for AC-0031.
  - AC-0035 lint and verify after self-host.
  - The nine names added to the two pack-test `RETIRED_SHAPING_SKILLS` constants, and
    the pack suite passing.
  - The nine source map entries are removed, and the AC-0036 `--check` reading holds.
    The unrelated paths T7 listed still show no diff against the branch's merge base
    with `origin/main`.
  - Last, after `git fetch origin main`: the AC-0037 base comparison over the nine
    source directories, recorded with the fetched commit.
**Done when:** these tests pass.

## Rollout

- **Delivery:** big bang. eugenelim publishes `product-engineering` 2.0.0 and the patch
  releases of every other edited pack and `agentbundle` on the same day.
- **Reversibility:** revert the PR and republish the previous versions. Adopters who
  already deleted stale directories reinstall `product-engineering` 1.0.0.

## Risks

- The activation runs are long, several hundred runs per world. A host usage limit mid-run
  produces errored runs, which are re-run before scoring.
- Runs share one projection per world and some write files into it. This affects both
  worlds alike and is recorded, not corrected.

## Changelog

- 2026-10-11: spec approved by eugenelim
- 2026-10-11: plan approved by eugenelim
- 2026-10-13: spec approved by eugenelim (two-skill re-fold amendment)
- 2026-10-13: plan approved by eugenelim (two-skill re-fold amendment)
