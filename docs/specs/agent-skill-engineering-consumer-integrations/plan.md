# Plan: Agent skill engineering consumer integrations

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** the mechanism precedent is
  `packs/architect/.apm/skills/architect-review/SKILL.md:107-120` — architect
  consuming core's `project-knowledge`, the repository's one cross-pack
  optional-provider consumption. The same-pack examples (`work-loop:388`,
  `architect-design:93`) are **not** admissible here; ADR-0097:171-177 excludes
  them. See § *Mechanism precedents* for the full table and the one recorded
  deviation. Test-shape anchors:
  `tests/roster/test_ase_shipped_statement_agreement.py` (bound-roots
  anti-vacuity at `:57-64`, per-member control at `:97-109`),
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py` (staged
  `tmp_path` roots calling `verify_catalogue`), and
  `tests/roster/test_thirty_day_cooling_and_retirement.py:1626-1629` (recorded
  merge-base version literal, strict-greater). Declaration precedent:
  `packs/architect/pack.toml:82-91`.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`.

### Mechanism precedents

Every mechanism this slice introduces, with the closest existing implementation
of the same responsibility and whether we match or deviate. It exists because two
earlier drafts each got the mechanism wrong: the first found the precedent in the
opening search and filed it as background rather than as a precedent; the second
built this table and matched against a population the governing record excludes. A
search result kept in the author's head is indistinguishable from a search never
run, and a match against the wrong population is worse than no match at all.

**Population, and why it is stated.** The governing record defines it.
ADR-0097:171-177 expressly excludes same-pack routing as a precedent for this
case — "*their authored same-pack consumers may continue to address them
statically because source, provider, and consumer share one pack ownership and
delivery boundary*" — so the admissible population is **cross-pack consumption of
an optional provider**. An earlier version of this table matched against two
same-pack examples, returned a confident "Match", and produced a design the one
admissible precedent contradicts. Each row now quotes the precedent's own words or
field value; a bare citation is not a verdict.

| Mechanism this slice adds | Closest admissible implementation | Verdict |
| --- | --- | --- |
| Consumer step invoking an optional cross-pack provider | `architect-review/SKILL.md:107-120` — architect consuming core's `project-knowledge`. It names the seam ("*submit exactly this strict shape through the public `project-knowledge --enquire` seam*"), inlines the envelope as literal JSON, bounds the call ("*The budget is one query and no refinement*"), forbids implementation discovery ("*Do not locate the provider's implementation or persistence; normal skill discovery is the only handoff*"), and fixes the receipt ("*record exactly `project-knowledge unavailable`*") | **Match on four, one recorded deviation.** Adopt the inlined request, the budget, the no-implementation-discovery rule and the fixed receipt. **Deviate** on naming: the precedent names an authored public seam, while this provider is a *generated router*, which ADR-0097:97-99 forbids a consumer from naming. Address by contract version instead |
| Same-pack routing — `work-loop:388` → `project-knowledge`; `architect-design:93` → its own `references/knowledge-surfaces.md` | — | **Not admissible**, per ADR-0097:171-177. Recorded because an earlier draft matched here |
| Where the consumption contract lives | The admissible precedent keeps it **in the consumer**: `architect-review` states envelope, budget and receipt inline and delegates nothing to a file inside the provider's pack | **Match.** `provider-contract.md` is the provider pack's own statement, read by its authors and by AC1; a consumer never loads it and has no path to it |
| External declaration `kind` | The two shipped anchors **disagree**: `packs/core/pack.toml:88-97` is `kind = "review"`; `packs/architect/pack.toml:82-91` — `project-knowledge-review-enquiry`, "*Bounded architecture-review knowledge enquiry*" — is `kind = "handoff"`. `guides/_shared/reference/catalogue-authoring-standards.md:530-535` defines `augment` as "*the target pack's skill is inlined into the consuming skill's workflow*", which a read-only provider call is not. It defines `input` as the target providing an artifact the declaring pack's skill reads; this consumer instead passes control to a discovered capability at a defined boundary, so it does not read a target-provided artifact | **Follow architect: `kind = "handoff"`** — the anchor for the identical responsibility. Pinned by AC6 and AC7 so the choice is reviewable after merge |
| Repository-level prose-binding suite | `tests/roster/test_ase_shipped_statement_agreement.py` — bound-roots anti-vacuity `:57-64`, per-member control `:97-109`, pinned set sizes | **Match** |
| Staged-catalogue verification | `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py` — `tmp_path` roots calling `verify_catalogue(root)` | **Match** |
| Version floor in a test | `tests/roster/test_thirty_day_cooling_and_retirement.py:1626-1629`, `tests/roster/test_cooling_scope_closure.py:1053-1058` — recorded merge-base literal, strict-greater, never a remote read | **Match.** An earlier draft read `origin/main`; both precedents reject that |
| Recording an ungated review walk | `docs/specs/agent-skill-engineering-composition-floors/qa.md` § *Review ledger* | **Match** |
| Per-slice implementation record | `docs/architecture/agent-skill-engineering.md` § 11 *Last verified*, which carries a paragraph per shipped slice | **Match.** An earlier draft wrote § 4 instead |

One deviation is claimed and recorded above: the consumer addresses the provider
by contract version rather than by the seam's name, because ADR-0097:97-99 forbids
naming a generated router. Any future task that cannot fill its row must say the
search was run and empty, not leave the row absent.

## Approach

The consumer step inlines its own request, matching the repository's one
cross-pack precedent for consuming an optional provider. Two earlier drafts got
this wrong in opposite directions: the first had each consumer restate ten
obligations, which made the criteria circular; the second delegated the contract
to a file inside the provider's pack, which a consumer has no path to and which
is absent exactly when the provider is. Inlining a bounded request is what
`architect-review` actually does, and it makes every token in the step traceable
to the fixture or to the contract version.

T2 therefore publishes only the diagnostic vocabulary — the receipts the
consumers quote — not a set of consumer obligations, which belong in the consumer.

Order: T0 rebases and records the version literals, T1 lands the suite red, T2
publishes the vocabulary, T3 and T4 write the two steps, T5 the catalogue
guidance, T6a the architecture paragraph and registration, T6b the projections
and release surface.

## Constraints

- **ADR-0097** fixes the membrane, the minimization rule, the authority
  precedence rule, and the layout-independence rule (`:97-99`) that forbids the
  consumer relying on the owning pack's product name, installation path or
  generated router path.
- **ADR-0093** keeps raw OKF a build-time source.
- **RFC-0097 § D2 rule 5** keeps `pack.toml` syntax and AgentBundle commands out
  of portable instructions; **rule 1** excludes generic CI requests.

### Measured facts — canonical home

The derivations are recorded here; the spec cites this section while retaining
the outcomes its reader needs.

| Fact | Value | Source |
| --- | --- | --- |
| `CAT-S003` body ceiling | errors at `n > 1000` | `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:520` |
| `work-loop` / `architect-design` bodies | 822 and 280 lines; headroom 178 and 720 | measured with `skill_spec_lint`'s own extraction (`:388,401,518`) |
| Suite reach | `tests/` at `Makefile:530`; `make ci` reaches it via `test-after-build-check` at `Makefile:670` | `Makefile` |
| Manifest regeneration | `$(PYTHON) -m agentbundle catalogue self-host --root . --write` | `Makefile:78` |
| **`make ci` never runs `self-host --check`** | The check appears only under the `build-self` target's `DRY_RUN=1` branch (`Makefile:70,72`); no step of `build_check` invokes it. Stated as a negative — `build_check` defines 63 steps and this plan does not enumerate them | `Makefile:67-79,156,670`; `tools/repo/build_gate_chain.py` |
| Dirty-tree refusal | `run_self_host` refuses unless `--force` | `packages/agentbundle/agentbundle/build/self_host.py:1300-1303` |
| Scaffold twin | `python3 tools/catalogue/sync_authoring_scaffold.py --write`; gated by `tools/test_scaffold_projection.py` at `Makefile:617` | those files |
| Guides linter | `Makefile:620` runs the linter's *contract test*; the only real-tree scan is the path-filtered CI job at `.github/workflows/docs.yml:103-109` | those files |
| CAT-V-019 | `consumers` (`packages/agentbundle/agentbundle/catalogue_tooling/verify.py:2117-2127`), self-target (`:2140`), semver (`:2150-2163`) unconditional; `providers` gated at `:2165`. Entry point `verify_catalogue(root)` at `:2224` | `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` |
| Pinned baseline | `236ae549c`; `core 2.23.0`, `architect 0.15.5`, `agent-skill-engineering 0.4.0`. Recorded in the test module at T0. Do not re-fetch during implementation — the literals are only meaningful against one fixed base | the rebased tree at T0 |
| `/now/` projection | `web/src/lib/now-highlights.generated.json`, gated by `tools/test_build_site_routing.py:2098,2128` via `Makefile:584`; stale only if an entry adds a `Highlights` subsection | those files |

## Construction tests

**Integration tests:** one module,
`tests/roster/test_agent_skill_engineering_consumer_integrations.py`.

**Manual verification:** a three-item walk per consumer (every *Always do*
element is present and none is expanded beyond it; the invocation condition
matches the stated trigger; and the surrounding workflow is otherwise unchanged),
recorded in `docs/specs/agent-skill-engineering-consumer-integrations/qa.md`
alongside the sibling composition-floors slice's `qa.md`, with the per-item
result and the reviewing session named. That file is the artifact; without it the
ungated half has no record.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility · `provider-contract.md` | T2 | Diagnostic vocabulary published | Consumers inline their own requests |
| Current product truth · two `SKILL.md` bodies | T3, T4 | Existence criteria green; `qa.md` records the three-item walk | Bodies at or below the ceiling |
| Current architecture · § 11 *Last verified* | T6a | Slice paragraph in the 2a/2b form | Consumer half recorded |
| Interface compatibility · roster module | T1 | Anti-vacuity passes; assertions labelled by class | Green under `make ci` |
| Maintainer guidance · § 11 + twin | T5 | Obligation stated; twin byte-identical | Scaffold suite green |
| Operations · registration and projection | T6a, T6b | Three rows and the `[backlog].open` entry; projection equals source | `make build-self` clean |
| Release history · three `pack.toml`, changelog | T6b | Versions exceed the recorded literals and match topmost entries | `make build-check` green |

## Tasks

### T0: The branch is current with `origin/main` and the version literals are recorded

**Depends on:** none
**Verification mode:** goal-based check
**Touches:** tests/roster/test_agent_skill_engineering_consumer_integrations.py
(the three literals only; T1 adds the assertions)

**Tests:** `git merge-base --is-ancestor origin/main HEAD` succeeds; the three
`pack.toml` versions read from the rebased tree match the recorded literals.

**Approach:** the `Depends on:` governance change has merged, and this branch is
rebased onto **`236ae549c`**, which is the pinned baseline for the whole
implementation. Read each pack's version from the rebased tree and record it as
the merge-base literal AC10 compares against, in the precedent's shape
(`test_thirty_day_cooling_and_retirement.py:1272`): a module constant whose
trailing comment names the source path and the merge-base SHA.

Record only after the rebase: doing so before pins a number `origin/main` has
already passed. `core` moved twice while this contract was in review — 2.21.0 →
2.22.0, then 2.23.0 — which is the whole reason this task exists.

**Do not re-fetch or re-rebase during implementation.** The literals are only
meaningful against one fixed base; re-syncing mid-flight invalidates them and
silently re-reds AC10. Rebase again only after T6b, and re-record the literals if
you do.

**Done when:** the branch is a descendant of the pinned baseline and the three
literals are recorded in the test module.

### T1: The suite is red, with each assertion labelled by class

**Depends on:** T0
**Verification mode:** goal-based check
**Touches:** tests/roster/test_agent_skill_engineering_consumer_integrations.py

**Tests:**
- Bound-roots anti-vacuity: assert the walk opened both consumer bodies, both
  `pack.toml` files, `provider-contract.md`, the architecture document, the
  projection, the guides file and its twin, and each record.
- Load the diagnostic set from `provider-cases.json`'s distinct non-null
  `expected.diagnostic` values; assert non-empty and that `token=secret-value`
  is not a member. Load the zero-candidate diagnostic from the `absent` case.
- The task-kind **set** is loaded from `provider-contract.md`, which is AC3's
  stated oracle and is external to this slice. Do not read it from a
  `[[pack.integrations]]` entry: that schema carries no task-kind field, and the
  entries are authored by T3 and T4, so the assertion would compare this slice's
  output against itself. Which two members each consumer sends is authored in
  AC3 and is the criterion's authored-statement half.
- Staged catalogues assert each staged manifest carries its entry **before**
  calling `verify_catalogue(root)`.
- Version comparison uses the T0 literals and strict-greater; the module never
  reads `origin/main`.
- Every assertion carries an `external-comparison`, `same-slice` or
  `authored-statement` label in a comment, matching the spec's three classes.
  An assertion covering a two-part criterion carries both of its labels; AC3 is
  the only such criterion.

**Done when:** the module collects, anti-vacuity passes, the three base-green
guards (AC5, AC11, AC12) pass as the spec says they must at the base commit, and
every remaining assertion is red for its recorded reason.

### T2: The seam's diagnostic vocabulary reaches an installed surface

**Depends on:** T1
**Verification mode:** goal-based check
**Touches:** packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/references/provider-contract.md

**Tests:**
- T1's publication criterion.
- `test_shipped_contract_prose_states_the_same_bounds_as_the_fixture`
  (`packs/agent-skill-engineering/tests/integration/test_provider_contract.py:439`)
  reads this file.
- `tests/roster/test_ase_shipped_statement_agreement.py` walks this tree.
- `test_pack_boundary.py` forbids AC-number, `docs/specs|rfc|adr/` and
  `workspace.toml` references in the portable tree.

**Approach:** add the seven diagnostics to the *Provider response* section, beside
the `provider integrity unavailable` sentence already there. Nothing else. The
consumer obligations an earlier draft planned to add here live in the consumer
step instead, per the cross-pack precedent; `pack.toml`-syntax hygiene for the
portable tree is already enforced by `test_pack_boundary.py`.

**Done when:** the vocabulary is projected and every suite above is green.

### T3: `work-loop` inlines its request to the capability

**Depends on:** T1, T2
**Verification mode:** manual QA at review, plus the existence and layout criteria
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/pack.toml

**Tests:**
- T1's existence, layout and `core` declaration assertions.
- The three-item walk, recorded in `qa.md`.
- `skill_spec_lint` reports no new `CAT-S003`. The step is ~6 lines against 178
  of headroom.
- **Prose-pinned consumers of this body.** Derive the re-run set from a
  repository-wide search for readers of `work-loop/SKILL.md`, not from a
  directory guess: it includes `packs/core/tests/skills/work-loop/`,
  `packs/core/tests/pack/test_finding_adjudication_contract.py`,
  `tests/roster/test_tdd_stub_lifecycle_contract.py`,
  `tests/roster/test_wave4_durable_outputs_and_release.py`,
  `tools/test_workspace_status.py`, `tools/lint-agents-md.py` and
  `tools/test-pre-pr.sh`. State the search used and its bound.
- `tools/test_workspace_status.py:1632-1640` compares two SHA-256 section hashes
  scoped to Step 0 and the Finish checklist; a PLAN-step insert should not move
  them. Confirm.

**Approach:** insert as an **unnumbered `###` subsection** inside `## Step 1.
PLAN`, following the `### Project-knowledge integration` precedent at
`SKILL.md:378` — the shipped way this body carries an optional-provider step. No
ordinal moves, so nothing outside the step changes and `Never do` holds. Do not
touch the *Work-loop contract* paragraph at `:30`; its "three net-new
obligations" count is about the self-coverage gate, not this step.

**Done when:** the walk is recorded, the assertions are green, and the
renumbering result is noted.

### T4: `architect-design` inlines its request to the capability

**Depends on:** T1, T2
**Verification mode:** manual QA at review, plus the existence and layout criteria
**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/pack.toml

**Tests:**
- T1's existence, layout and `architect` declaration assertions.
- AC8's staged-catalogue run. Both manifests exist only once this task lands, so
  this is where `verify_catalogue` first goes green over the provider-present and
  provider-absent catalogues.
- The three-item walk, recorded in `qa.md`.

**Approach:** insert as the last paragraph of Procedure step 2, after
`SKILL.md:124` and before step `3.`. Do **not** route obligations to
`references/knowledge-surfaces.md`: `SKILL.md:90-94` loads it only on detecting an
enterprise MCP tool, internal CLI or in-repo doc set, and that file scopes
eligibility to those — an installed pack capability is neither, so the
obligations would not load when this seam runs. The step states them itself.
Author the `[[pack.integrations]]` entry here, with `kind = "handoff"`.

**Done when:** the walk is recorded, AC8 is green over both staged catalogues,
and the assertions are green.

### T5: The extension-path obligation is stated in catalogue guidance

**Depends on:** T1
**Verification mode:** goal-based check
**Touches:** guides/_shared/reference/catalogue-authoring-standards.md, packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md

**Tests:** T1's § 11 and twin criteria; `tools/test_scaffold_projection.py`. The
repo-only-reference constraint is **CI-only**, so run
`python3 tools/lint-guides-no-repo-only-refs.py` manually before pushing.

**Approach:** one scoped sentence, written with no `RFC-NNNN`/`ADR-NNNN` token
and no real spec-slug reference. Sync the twin with
`python3 tools/catalogue/sync_authoring_scaffold.py --write`.

**Done when:** § 11 states it, the twin matches, and the linter is clean.

### T6a: The architecture record, three registration rows, and Follow-on entry

**Depends on:** T3, T4, T5
**Verification mode:** goal-based check
**Touches:** docs/architecture/agent-skill-engineering.md, docs/specs/README.md, workspace.toml, docs/product/briefs/agent-skill-engineering.md (Spec map row only)

**Tests:** T1's architecture and registration criteria.

**Approach:** add the slice paragraph to § 11 *Last verified*, matching the 2a,
2b and composition-floors entries — that is where this document records what is
implemented. Add the AC16 `[backlog].open` entry in `workspace.toml`. Touch only
the brief's `Spec map`; every cell of the slice table belongs to the `Depends on:`
change.

**Done when:** AC13, AC14, and AC16 pass.

### T6b: Projections and the release surface

**Depends on:** T6a
**Verification mode:** goal-based check
**Touches:** packs/{core,architect,agent-skill-engineering}/pack.toml (version field only), docs/product/changelog.md, .claude-plugin/marketplace.json, .claude/skills/work-loop/SKILL.md, .agents/skills/work-loop/SKILL.md

**Tests:** T1's projection and version criteria; `make build-self` from a
committed tree; `make build-check` with `build/` and `dist/` cleaned first.

**Approach:** bump each pack past its recorded T0 literal, one topmost changelog
entry each. If any entry carries a `Highlights` subsection, regenerate the
`/now/` projection with `python3 tools/build-site.py --journeys-only`. Never
hand-edit `.claude-plugin/marketplace.json`.

**Done when:** both gates are green and the projection equals its source.

## Rollout

Big bang, reversible; no infrastructure. T0 precedes everything; T2 precedes
T3/T4 because they quote the diagnostic vocabulary it publishes; T6b's regeneration follows
every pack-source edit and runs from a committed tree.

## Risks

- **A stale projection shipping green.** `make ci` cannot catch it; only the
  criterion and T6b's explicit `make build-self` do.
- **Restatement creeping back.** The failure of five review rounds. If a
  consumer step grows past a handful of lines, it has started restating a
  contract `provider-contract.md` owns.
- **The review walk going unrecorded.** `qa.md` is the artifact; without it the
  ungated half is unfalsifiable after the fact.
- **The guides linter is CI-only.** A green local suite says nothing about § 11.

## Changelog

- 2026-09-01: initial plan; oracle-first ordering after a spike showed the
  catalogue index drops `fallback` at projection.
- 2026-09-01: re-derived oracle dropped after round 1.
- 2026-09-02: contract shrunk after round 2 (26-of-34 prior-round-repair).
- 2026-09-02: scope split after round 3; the governance half moved out.
- 2026-09-02: prose gating abandoned after round 5.
- 2026-09-02: **mechanism changed to delegation after round 6.** Review found
  that this repository's shipped precedent for consuming an optional provider is
  delegation in ~3 lines — `work-loop:388` for `project-knowledge`,
  `architect-design:93` routing to `references/knowledge-surfaces.md` — while
  this plan had each consumer restate ten obligations inline. The restatement was
  the root cause of five rounds of circular criteria: a spec cannot gate prose it
  also dictates. The obligations now live once in `provider-contract.md` (T2),
  the consumer step is ~6 lines, and the criteria check existence of tokens whose
  values come from the fixture and each pack's own declaration. Also corrected:
  version comparison uses a recorded merge-base literal rather than reading
  `origin/main`, which two roster modules explicitly reject; T0 makes the rebase a
  prerequisite because `core` shipped 2.22.0 mid-review; the architecture record
  goes to § 11 *Last verified* where that document keeps it; the review walk is
  recorded in `qa.md`; and T6 is split so each `Done when` names a bounded set.
- 2026-09-02: **mechanism changed from delegation to request-inlining after
  rounds 7 and 8.** ADR-0097:171-177 says, "Their authored same-pack consumers
  may continue to address them statically because source, provider, and consumer
  share one pack ownership and delivery boundary." The round-6 `work-loop:388` and
  `architect-design:93` population was not admissible. The admissible
  cross-pack precedent, `architect-review/SKILL.md:107-120`, names the seam,
  states the envelope literally, bounds one query with no refinement, forbids
  implementation discovery, and fixes the absence receipt. The consumer instead
  addresses the capability by contract version because ADR-0097:97-99 forbids
  naming the generated router.
