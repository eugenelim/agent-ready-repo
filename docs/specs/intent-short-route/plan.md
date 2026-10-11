# Plan: intent-short-route

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:**
  - The experience-design fold: `docs/specs/xd-copy-router/` and the `content-design`
    skill, for the mode table, one procedure per mode, and the evidence note.
  - The pack and roster tests named in spec AC-0007.
  - `packages/agentbundle/agentbundle/commands/pack_evals.py`, the activation runner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline.

## Approach

The order is: measure first, build beside the old skills, switch, then delete only
after the evidence passes.

1. Record the three source skills' baselines while they still exist.
2. Build `intent/` next to them, moving content without changing behavior.
3. Retarget every caller, test, and doc.
4. Prove routing and activation in a world where the sources are already gone.
5. Delete the sources, bump versions, and self-host.

The riskiest part is the description. It must fit in 1024 characters and still win
shaping queries against `intake-intent` and `frame-situation`. That is why evidence
gates the deletion.

## Constraints

- RFC-0107 D1, D2, and D6, and ADR-0140: route mode stays stateless, and retired names
  get no alias.
- `packs/AGENTS.md` and `packages/AGENTS.md` set the version, eval-harness, and
  self-host rules.
- The experience-design precedent: no alias, the name sweep lands in the same PR, and
  deletion waits for evidence.

## Construction tests

**Integration tests:**
- the retargeted pack and roster modules in AC-0007;
- `tools/test_workspace_status.py`;
- `test_routing_precedence.py`.

**Manual verification:** AC-0008.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise: guides | T7 | Edited guides; regenerated SVG | AC-0010, AC-0027, AC-0034 |
| Product truth: pack and site pages | T7 | Edited pages | AC-0010 |
| Architecture: `lifecycle-flow.md` | T7 | Edited flow | AC-0010 |
| Decision rationale: ADR-0111 erratum | T9 | Erratum entry | AC-0040 |
| Release history: changelog | T9 | Entries for each released pack | AC-0025, AC-0029, AC-0031, AC-0032 |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T8

- **Skill layout.**
  - `intent/SKILL.md` keeps the route-mode rules inline, so routing needs no reference
    load.
  - `## Modes` holds the four-row table. Each verb row names its entry condition and
    its reference file.
- **Content moves unchanged.**
  - frame-intent's procedure body becomes `references/frame.md`.
  - Its references, `assets/intent-template.md`, and `examples/` move to
    `intent/references/`, `intent/assets/`, and `intent/examples/`.
  - de-risk and decompose move the same way.
  - On 2026-10-10 the source references had twelve distinct basenames, so the move
    collides with nothing. T2 re-checks this.
- **Tool authority.**
  - Claude Code reads a skill's `allowed-tools` as tools it may use without asking,
    not as a restriction. A list on `intent` would pre-approve its tools for every
    mode, including route mode, which only reads, and de-risk and decompose, which
    read untrusted input.
  - Before the fold, frame-intent listed `Read Write Edit Agent`; de-risk-intent and
    decompose-intent listed none, so their writes prompted.
  - `intent` declares no `allowed-tools`. Every mode's writes and edits prompt under
    the user's permission settings; frame loses the pre-approval it had.
  - Claude Code needs no grant for `Agent` by default, so reviewer dispatch still
    runs unprompted. The rule that de-risk never dispatches `adversarial-reviewer`
    rests on the mode's procedure text, as it did before the fold.
  - The boundaries metadata declares that the skill writes files and reads untrusted
    input; it grants no pre-approval.
- **The description names three verbs and three exclusions.** It names the three
  verbs, the route behavior, and three "do not use" targets: `intake-intent`,
  `new-spec`, and `frame-situation`. Changes after the probe has run follow the spec's
  Ask-first rule, and the shipped text is frozen by AC-0021.
- **The held-out activation set.**
  - It holds 30 positives (ten per verb) and 12 negatives, two each owned by
    `intake-intent`, `frame-situation`, `discovery-loop`, `new-spec`, `bug-fix`, and
    `architect-design`.
  - It is written in T1 and never shown to the probe.
  - With 3 runs per query there are 90 positive runs, so one run is about 1.1
    percentage points. That is fine enough to test the 3-point bound.
- **Where the activation runs happen.**
  - `pack_evals` reads each skill's own `evals/eval_queries.json`, through
    `read_eval_queries`.
  - The pre-fold run uses a disposable worktree.
    - Each source skill's query file holds its owned positives, plus all 12 negatives.
    - Both runs call `run_eval` from a scratch driver with `project_root` set to a
      prepared projection holding that world's `product-engineering`, `core`, and
      `architect`. The runner itself does not change.
    - Each projection is built in a fresh OS temporary directory outside every
      repository, which is the same rule `run_eval` enforces on its default path.
    - That rule confines only working-directory and parent-directory discovery.
    - The driver therefore wraps the runner's existing `ClaudeCodeDetector` and adds
      `--setting-sources project,local` to each `claude -p` call. The wrapper is passed
      to `run_eval` through its `detector` argument.
    - An isolated `HOME` cannot be used, because it loses the host login. The ledger
      entry of 2026-10-10 records this.
    - The score reads only the per-query `trigger_rate` that `pack_evals` writes for
      each skill.
    - A negative's pre-fold rate is the highest of its three per-skill rates. Any one
      skill firing is enough to fire "any of the three", so that rate can only
      understate how often any source fires, never overstate it. The bound therefore
      errs toward failing.
  - The post-fold run uses a second disposable worktree after T7. In it:
    - the three source directories are deleted;
    - `[pack.evals].skills` drops their names;
    - self-host has run;
    - `intent`'s query file is the held-out set.
  - Nothing from either worktree is committed.

### Behavior & rules

Owned by: T2

- **Route-mode signals:**
  - **Short route:** the user can name an outcome or a single bet.
  - **Longer route:** the problem itself is unclear, or the bet is large.
  - **Supervised route:** the request is a raw whole-product idea.
  - **Out of stage:** a defect goes to `bug-fix`, an already-shaped feature goes to
    `work-intake`, and an architecture choice goes to `architect-design`.

  When two route signals fire at once, route mode asks one question.
- **Orientation and next offers.**
  - The lifecycle map is a short ordered list per route, so it reads the same in
    every host.
  - Each mode reference keeps the source procedure intact. It gains only an opening
    orientation line and a closing `## Next` section that maps the mode's outcome to
    at most three offers.
  - Offers are phrased as questions to the user. No mode invokes another.
  - The longer-route stages still name their separate skills until
    `intent-longer-and-supervised-verbs` folds them in. Their order is read from
    `frame-situation`'s entry-point step, and a pack test holds the two equal.
  - When `discovery-loop` or its `discovery-lead` agent calls a mode, the loop's gate
    order wins. The `## Next` section says so on its first line.
  - Review gates follow ADR-0111 and frame-intent's existing review sections. The
    shaping review comes first. It is a gate when a review route is available, and
    optional otherwise. The adversarial read comes after it,
    before de-risk, and is advisory. Downstream gates are named at the hand-off by
    their owning skills and never run by `intent`.
  - Frame's review sections move unchanged. Its `## Next` section takes the three
    AC-0037 states, and it offers the shaping review only while the intent has no
    current review. When no review route exists, frame recommends de-risk.
  - `de-risk`'s reviewer boundary is rescoped from the skill to the mode, because
    `intent`'s frame mode now offers the adversarial read.
  - No mode stores the route. `de-risk` therefore offers both route-labelled survive
    stages, and asks only when the conversation shows no route.

### Dependencies & integration

Owned by: T5, T6, T7

Callers are located by searching for the three names. They cluster in these places.

- **Core:**
  - `work-intake/SKILL.md` § Public routing precedence;
  - `_SHAPING_TYPE_TO_SKILL` and `check_shaping_guard` in `workspace_status_engine.py`;
  - `init-project`, `work-loop`, and a comment in `lint-traceability.py`.
- **Package:** the `_data` engine mirror and `workspace_mcp.py`.
- **Other packs:**
  - six experience-design skill descriptions, and `process-mapping`'s skill, asset,
    and evals;
  - governance-extras: the `design-proposal-product-engineering` integration and
    `new-rfc`;
  - product-strategy: `run-okr-cascade`, `run-swot`, and `write-prfaq`;
  - product-engineering: sibling skills, references, and pack docs.
- **Tools:**
  - `render-lifecycle-graphics.py` and `add-rendering-directives.py`;
  - `lint-knowledge-surface-parity.py` and `repo/check_contract_drift.py`, which pin
    reference paths;
  - the tests for those tools, and `test_live_demo_guide.py`.

## Tasks

### T1 — Pre-fold baseline

**Depends on:** none
**Mode:** bounded routing-classification evidence; activation
**Touches:** `docs/specs/intent-short-route/notes/`
**Tests:**
  - The eleven pre-fold classifications from AC-0019, against the AC-0035 candidate set,
    recorded as AC-0033 requires.
  - The held-out set is written. Its pre-fold `pack_evals` run is recorded for AC-0023.
**Done when:** the note and the ledger hold both pre-fold results.

### T2 — Build `intent/` beside the sources

**Depends on:** T1
**Mode:** goal-based
**Touches:** `packs/product-engineering/.apm/skills/intent/**`
**Tests:**
  - Structural checks for AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, and AC-0006.
  - Lifecycle checks for AC-0036 and AC-0037.
  - `test_skill_census.py` passes, with `intent` added to the census fixture.
  - The AC-0030 collision check over the moved paths.
  - The modules retargeted for AC-0007 run against `intent/` while the sources still
    exist.
**Done when:** these tests pass and catalogue lint is clean.

### T3 — Merge evals

**Depends on:** T2
**Mode:** goal-based
**Touches:** `intent/evals/**`, `notes/verification-ledger.md`
**Tests:**
  - An owner, polarity, mode-key, and duplicate check over `eval_queries.json`
    (AC-0016).
  - The intake-intent negatives (AC-0017).
  - The evals.json carry-or-drop listing (AC-0018).
**Done when:** these tests pass.

### T4 — `discovery-loop` and `discovery-lead`

**Depends on:** T2
**Mode:** goal-based
**Touches:** `discovery-loop/SKILL.md` and its references, `agents/discovery-lead.md`
**Tests:** `test_intent_triad_execution_wiring.py`, retargeted for AC-0014 and AC-0015.
**Done when:** these tests pass.

### T5 — Core and package callers

**Depends on:** T2
**Mode:** TDD for the engine mapping; goal-based otherwise
**Touches:** the Core skills and engine, plus the package mirror and MCP named in Design
**Tests:**
  - `tools/test_workspace_status.py` expects `intent` (AC-0011).
  - `test_routing_precedence.py` (AC-0012).
**Done when:** these tests pass.

### T6 — Other packs and integrations

**Depends on:** T2
**Mode:** goal-based
**Touches:** experience-design, governance-extras, product-strategy, and the
`product-engineering/pack.toml` integrations
**Tests:** the AC-0013 integration values, and catalogue lint.
**Done when:** these tests pass.

### T7 — Tools, tests, guides, site, and docs

**Depends on:** T4, T5, T6
**Mode:** goal-based
**Touches:**
  - tools and their tests;
  - `guides/**`, `web/src/content/**`, and the pack docs;
  - `docs/architecture/lifecycle-flow.md`, `docs/product/journeys/`, and
    `docs/product/workspace-toml-deps.md`;
  - `workspace.toml` comments that cite retired skill paths;
**Tests:**
  - The AC-0010 search. It excludes the three source directories, the
    `[pack.evals].skills` line, and
    `packs/agent-skill-engineering/tests/fixtures/skill-census.json`, all of which T9
    clears.
  - The AC-0027 guide text.
  - The AC-0034 regeneration check.
  - The AC-0028 guide text.
**Done when:** these tests pass.

### T8 — Post-fold probe and activation

**Depends on:** T3, T7
**Mode:** bounded routing-classification evidence; activation; manual QA
**Touches:** `notes/`
**Tests:**
  - One scored post-fold attempt: the eleven cases, three runs each, on one
    byte-identical AC-0035 candidate set (AC-0019), recorded per AC-0033.
  - The shipped descriptions match that attempt's candidate set byte for byte (AC-0021).
  - The pass rule (AC-0020) and the caveat (AC-0022).
  - The one post-fold `pack_evals` run on the passing attempt's descriptions, against both bounds per measured host (AC-0023).
  - A new scored attempt only after a recorded failure, an owner revise choice, and a changed candidate description (AC-0019).
  - After a revision under AC-0023: no held-out query verbatim in a revised description, and the ledger caveat beside the re-measured result (AC-0023).
  - The two-route check (AC-0008).
  - The guided walk through the route reply and the short route (AC-0038, AC-0039).
**Done when:** every check passes. Any failure stops the slice here, before T9.

### T9 — Delete sources, bump, record, self-host, and observe

**Depends on:** T8
**Mode:** goal-based
**Touches:** the three source directories, `pack.toml` and `plugin.json` files, the
`packages/agentbundle` version, `docs/product/changelog.md`, `packages/agentbundle/CHANGELOG.md`,
`packs/agent-skill-engineering/tests/fixtures/skill-census.json`,
`docs/adr/0111-intent-review-splits-well-formedness-from-assumption-attack.md`, and the
projections
**Tests:**
  - The AC-0009 absence and membership checks.
  - AC-0024 versions.
  - `test_skill_census.py` passes, with the three retired names removed from the census
    fixture.
  - The changelog entries for AC-0025, AC-0029, AC-0031, and AC-0032.
  - The ADR-0111 erratum for AC-0040.
  - For AC-0031, an install-then-update observation of a removed skill directory,
    recorded in the ledger.
  - AC-0026 lint and verify after self-host.
  - The AC-0010 search again.
**Done when:** these tests pass.

## Rollout

- **Delivery:** big bang. The release owner, eugenelim, publishes
  `product-engineering` 1.0.0 and the patch releases of every other edited pack on the
  same day. The changelog entries are the evidence.
- **Reversibility:** revert the PR and republish the previous versions. Adopters who
  already deleted stale directories reinstall the earlier `product-engineering`.

## Changelog

- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
- 2026-10-10: spec approved by eugenelim (AC-0023 isolation amendment)
- 2026-10-10: plan approved by eugenelim (AC-0023 isolation amendment)
- 2026-10-10: spec approved by eugenelim (AC-0020 pre-fold baseline amendment)
- 2026-10-10: plan approved by eugenelim (AC-0020 pre-fold baseline amendment)
- 2026-10-10: spec approved by eugenelim (lifecycle orientation amendment)
- 2026-10-10: plan approved by eugenelim (lifecycle orientation amendment)
- 2026-10-10: spec approved by eugenelim (review-gate amendment)
- 2026-10-10: plan approved by eugenelim (review-gate amendment)
- 2026-10-11: spec approved by eugenelim (AC-0020 repeated-run amendment)
- 2026-10-11: plan approved by eugenelim (AC-0020 repeated-run amendment)
- 2026-10-11: spec approved by eugenelim (AC-0023 revise-path amendment)
- 2026-10-11: plan approved by eugenelim (AC-0023 revise-path amendment)
- 2026-10-11: spec approved by eugenelim (AC-0006 tool-authority amendment)
- 2026-10-11: plan approved by eugenelim (AC-0006 tool-authority amendment)
- 2026-10-11: spec approved by eugenelim (agent-dispatch sentence correction)
- 2026-10-11: plan approved by eugenelim (agent-dispatch sentence correction)
