# Plan: architect-design system-shape overlay

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0118 fixes the shared names; the workload axis in
  `packs/architect/.apm/skills/architect-design/SKILL.md` step 4 is the
  analogous shipped routing axis this one is built beside;
  `packs/architect/tests/skills/architect-design/test_design_scope_routing.py`
  is the analogous construction path, and its marker-anchored style is reused
  rather than re-invented. Named deviation: the workload axis descends a tiered
  concept directory and this one descends a flat category, so the two are not
  symmetric in what they load.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Add one routing axis to a procedure that already carries two. The axis is one
marker-delimited region of skill prose, a construction suite, an eval case,
and a release. The bet behind it — that routing more lenses adds concerns rather
than bulk — is not settled here and is not settled by this delivery: eight
review rounds established that the probe's questions are empirical, the probe
ran on 2026-09-20 and returned no verdict, and nothing gates this release on
one. `docs/product/intents/architect-design-conditional-overlays.md` carries
the bet and what follows from it.

## Constraints

- The corpus ontology is pinned by exact equality in
  `packs/architect/tests/pack/test_architecture_lenses_corpus.py`, so the axis
  adds no concept file, no category, and no index.
- `packs/architect/tests/skills/architect-design/` runs on the pull request in
  build-check's `pytest catalogue-test carve-out destinations (RFC-0082)`
  step, so a break there reds the PR rather than waiting for a dispatch.
- The `agentbundle:output-rendering` span in `SKILL.md` is regenerated
  byte-for-byte by `tools/add-rendering-directives.py`. A marker region added
  inside step 4 leaves that regenerator reporting no drift for this skill, so
  the two marker vocabularies do not collide.
- The skill description is pinned by equality at two ends in
  `packs/architect/tests/skills/architect-design/test_yagni_contract.py` — one
  string bundling the invocation sentence and the trigger list, and one
  closing refusal. The middle is deliberately free.
- Shipped pack content cites no catalogue-internal record, so the shape rule is
  stated directly in `SKILL.md` and ADR-0118 is named only here.

## Construction tests

**Integration tests:** none beyond per-task tests. The axis is skill prose; the
one cross-file property — that the eval case names a concept path the corpus
actually ships — is asserted inside T2's test rather than as a separate suite.
That assertion reads three trees: `evals.json`, the source concept corpus, and
the projection the skill actually descends.

**Manual verification:** three criteria, all delivery-time. AC-0094's version
increment has no repository gate — `test_pack_metadata.py` decides only that
the two manifests agree, so the increment itself is read against the merge
base by hand. AC-0099 and AC-0101 are goal-based: one read of ADR-0118's
`## Errata`, and a literal-token comparison against the skill region. Each
observation is recorded in `notes/verification-ledger.md`; nothing else here
needs a human. The overlay's own bet is not tested by this delivery; the study
the intent names tests it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Release history / `docs/product/changelog.md` | T5 | A free-standing `##` entry placed as AC-0096 states | The Highlights decision is written |
| Decision rationale / ADR-0118 § Errata | T6 | The dated erratum, with its tokens matched against the skill region | A later slice reads all three names without opening this spec |
| Current product truth / `SKILL.md` | T1, T2 | `test_shape_axis_routing.py` green; the eval case present | The eval harness exercises the axis |

## Design (LLD)

### Design decisions

- **The trigger is an open decision, not a vocabulary match.** A shape is
  selected when a decision the design still has to make turns on that shape's
  coordination mechanism. Rejected alternative: a numeric cap such as "load at
  most two shapes". A cap is a bound with no origin — nothing in the corpus or
  the intent produces the number two — and it does not stop bulk, because two
  irrelevant shapes are as much bulk as three. The open-decision filter is
  self-limiting and traces directly to the risk the intent names.
- **A selected shape concept loads whole.** The six shape concepts are flat
  single files; `genai-agentic` is a directory of five, which is why the
  workload axis gates tiers and this one does not. Recording the asymmetry
  here stops a later reader from "fixing" it into a tier selector that has
  nothing to select.
- **The axis lives inside the Stage-0 concept step, beside the workload axis,
  not as a new procedure step.** Both axes feed the same artifact — the Stage-0
  concept — and a new step would separate two routings that are read together.
- **`no shape lens selected` is a receipt value, not a provider diagnostic.**
  The skill already carries a closed diagnostic set for the knowledge-provider
  handoff. This string belongs to the working receipt and is deliberately
  worded so it cannot be mistaken for one of those seven.
- **The shape-axis names go to ADR-0118's `## Errata`.** ADR-0118 is where
  cross-slice names are settled, and S3's trigger reads the system shape, so
  the open-decision trigger, the whole-load rule, and the receipt value cross
  a slice boundary. They are recorded there rather than only in this plan,
  which is working material and is not adopter-visible. Rejected alternative:
  leaving them in this spec, which is the per-slice naming ADR-0118's decision
  drivers explicitly rejected.

Owned by: T1, T6

### Behavior & rules

The axis resolves in three steps, all inside the Stage-0 concept work: descend
`concepts/system-shapes/index.md` and read its titles, which is all it carries
alongside a lifecycle label; open only the shapes the design plausibly is, and
confirm the match against each opened concept's own `Scope and routing
signals` section, asking whether an open decision turns on that shape's
coordination mechanism; load whole the concepts that pass and record their
paths in the working receipt, or record `no shape lens selected`.

Owned by: T1

### Dependencies & integration

No new dependency. The axis reads a generated corpus index the skill already
enters through `../architecture-lenses-reference/references/okf/index.md`, and
the existing "architecture lenses unavailable" degradation already covers an
absent or invalid router.

Owned by: T1

### Failure, edge cases & resilience

The interesting edge is a design matching several shapes with an open decision
in each — a streaming pipeline inside a layered application. The rule loads
both, because both decisions are real; the filter that keeps this from
becoming bulk is that each loaded shape had to carry a decision, not that a
count was capped.

Owned by: T1

## Tasks

### T1: the shape axis routes, and its region cannot be moved without failing

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/tests/skills/architect-design/test_shape_axis_routing.py

**Tests:**
- A new suite `test_shape_axis_routing.py` reuses the marker-anchored style of
  the neighbouring `test_design_scope_routing.py`: it slices the region between
  `<!-- shape-axis:start` and `<!-- shape-axis:end -->`, whitespace-normalizes
  it, and asserts against that slice only. A whole-file search is what lets the
  region be deleted while prose elsewhere keeps the check green (AC-0084,
  AC-0085, AC-0086, AC-0087, AC-0088).
- Occurrence is asserted with `str.count(...) == 1` per marker and ordering
  with `str.index` positions in the same read: `str.index` returns a first
  offset and cannot detect a duplicate, so a count is what makes the
  exactly-once half of the criterion observable (AC-0089).
- `stub: true` — the seven functions in
  `packs/architect/tests/skills/architect-design/test_shape_axis_routing.py`,
  read off that file rather than derived from the criteria:
  `test_the_shape_axis_cites_the_system_shapes_index_as_its_descent_path`
  (AC-0084), `test_a_shape_concept_is_selected_only_on_an_open_decision`
  (AC-0085), `test_several_open_decisions_load_every_matching_shape`
  (AC-0086), `test_a_selected_shape_concept_loads_whole_with_no_tier_selection`
  (AC-0087), `test_the_receipt_records_no_shape_lens_selected_when_none_apply`
  (AC-0088), and for AC-0089 the pair
  `test_the_shape_axis_is_anchored_by_one_start_and_one_end_marker` and
  `test_the_shape_axis_sits_between_scope_determination_and_template_selection`.

  ```python
  # STUB: AC-0084
  def test_the_shape_axis_cites_the_system_shapes_index_as_its_descent_path() -> None:
      assert "concepts/system-shapes/index.md" in _region()
  ```

  `_region()` takes no argument: it slices `SKILL.md` between the two
  shape-axis markers and whitespace-normalizes the result.

  **Red observed 2026-09-20, ahead of this gate, and re-derived since.** T1 was
  executed before the engine reached `CODE-IMPLEMENTATION`, at the owner's
  direction, so the probe's routed arm could be authored against the real
  region. Against a region-stripped `SKILL.md` the suite gives three distinct
  failures, re-derived after the helper gained its missing-marker guard: the
  five `_region()` tests fail
  `AssertionError: shape-axis region is missing a marker` from that guard,
  which runs before the slice; the marker-count test fails
  `AssertionError: assert 0 == 1`; and the ordering test raises
  `ValueError: substring not found` from `str.index`. The last two read the
  whole file and never call `_region()`, which is why a single-failure
  account of this red was wrong about exactly the pair discharging AC-0089. `notes/verification-ledger.md` records the
  re-derivation and the deviation.

**Approach:**
- The region is placed after the workload-axis sentences that close step 4's
  routing paragraph and before the Stage-0 stopping-point paragraph, so the two
  orthogonal axes read as a pair.

**Done when:** `python3 -m pytest packs/architect/tests/skills/architect-design/ -q` is green, including the pre-existing suites that read the same file.

### T2: the eval harness exercises the axis

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-design/evals/evals.json, packs/architect/tests/skills/architect-design/test_shape_axis_routing.py

**Tests:**
- `stub: true` — `test_the_eval_case_exercises_the_shape_axis`, AC-0090:

  Approved payload, in two parts, because appending imports mid-file reds
  `E402` and the lint gate T5 requires clean. Both parts are byte-exact:
  ruff reads placement, so a prose description of where a line goes is not
  enough. Part one replaces the file's existing import line and inserts two
  constants above `SHAPE_START` — the import order is the one `I001` accepts:

  ```python
  import json
  import re
  from pathlib import Path
  ```

  ```python
  EVALS = PACK_ROOT / ".apm" / "skills" / "architect-design" / "evals" / "evals.json"
  CONCEPTS = PACK_ROOT / "okf" / "architecture-lenses" / "concepts"
  ```

  Part two is appended at the end of the file, preceded by two blank lines so
  `E302` is satisfied; byte identity is verified against this block:

  ```python
  # STUB: AC-0090
  def test_the_eval_case_exercises_the_shape_axis() -> None:
      evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
      case = next(c for c in evals if "system-shapes/" in json.dumps(c))
      expected = case["expected_output"]
      assert "shape axis" in expected
      assert "open decision" in expected
      paths = re.findall(r"system-shapes/[\w-]+\.md", expected)
      assert paths, "expected output names no system-shapes concept path"
      assert any((CONCEPTS / p).exists() for p in paths), paths
  ```

  All three of AC-0090's conjuncts are asserted on `expected_output`, and each
  can fail alone. The axis token is `shape axis`, which both the hyphenated
  spelling the spec uses and an unhyphenated one contain, and which no concept
  path supplies. `findall` rather than `search`, because the region's own
  descent path `concepts/system-shapes/index.md` matches the pattern and does
  not exist under `okf/.../concepts/` — it lives only in the generated
  projection — so taking the first match would red an expected output that
  satisfies AC-0090. A missing path fails an assertion rather than raising
  `AttributeError` on `.group`. The case is selected on
  the whole record, but nothing is asserted from outside `expected_output`.

  Red before T2: `next(...)` raises `StopIteration` because no case names a
  shape path. The assertions read `expected_output` alone, because that is the
  field AC-0090 constrains; a case naming the axis only in `assertions` does
  not discharge it. The on-disk check stops the expectation naming a concept
  the corpus does not ship.
**Approach:**
- The new case takes id 13. The id space is mixed — integers 1 to 12 plus four
  string ids — so "the next integer" is 13, and the roster suite indexes by id
  rather than position, leaving its id-3-to-7 save-mode contracts untouched.
  That is how to add it, not a check of any criterion.

**Done when:** `python3 -m pytest packs/architect/tests/skills/architect-design/test_shape_axis_routing.py::test_the_eval_case_exercises_the_shape_axis -q` is green — the assertion exists and passes, which no other check observes — the eval file parses, the new case is present, and the suite from T1 is green.

### T5: the pack release closes

**Depends on:** T1, T2

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- The conformance suite the spec's Testing Strategy names for AC-0094 decides
  that `pack.toml` and `plugin.json` agree; its path is stated there, not here. It does not decide the increment,
  and nothing in the repository does: `tools/repo/check_release_impact.py`
  covers `packages/agentbundle/` and `contracts/`, not `packs/`. The increment
  is therefore a delivery-time read against the merge base, recorded rather
  than gated (AC-0094).
- `marketplace.json` is written by `FORCE=1 make build-self`, never by hand
  (AC-0095).
- The entry's placement is decided by the two `tools/test_build_site_routing.py`
  assertions the spec's Testing Strategy names for AC-0096, run over the real
  changelog. Whether a Highlights block is owed is decided by nothing
  mechanical, for the reason that same section records.

- `no stub (goal-based check)` for AC-0094, AC-0095 and AC-0096: each is
  discharged by an existing suite or by regeneration, so there is no new test
  to earn a red from.

**Approach:**
- The Highlights disposition follows `packs/AGENTS.local.md` § Marketplace and
  release pipeline, step 4, which owns both the decision and where a no-change
  verdict is recorded — the pull-request description, not the changelog. It is
  decided from what this release ships: the axis changes what an adopter's
  design run loads, so the entry carries a `### Highlights` subsection.
- This task does not start until the spec has been updated from the probe's
  findings, per the spec's `Always do` rail — which it has been. The rail says
  findings, not verdict: the probe returned none, and gating a release on a
  verdict that does not exist would make this task unstartable. It is a rail
  rather than a `Depends on:` edge because the probe is not a task in this
  plan; the edge below names only the tasks whose artifacts T5 releases.

**Done when:** the AC-0094 conformance suite is green and, for **each** of `pack.toml` and `.claude-plugin/plugin.json`, `git show "$(git merge-base HEAD origin/main)":<path>` shows exactly one patch below the committed value — the merge base, not `origin/main`'s tip, which differ in this worktree and would compare against a peer's bump. The conformance suite decides only that the two files agree in the present tense, and no repository gate reads the increment, so it is observed here and recorded in the verification ledger (AC-0094), `.claude-plugin/marketplace.json` carries the bumped version after `FORCE=1 make build-self` leaves no unstaged regeneration (AC-0095), `python3 -m pytest tools/test_build_site_routing.py tests/roster/test_okf_catalogue_discovery.py -q` is green over the real changelog — the roster case is what decides the topmost-architect clause (AC-0096), and `make lint-ruff lint-mypy` is clean.

### T6: the shape-axis names have one cross-slice home

**Depends on:** T1

**Touches:** docs/adr/0118-architect-design-scope-routed-model-first-templates.md

**Tests:**
- One read of ADR-0118's `## Errata` section decides AC-0099: the names it
  requires are fixed there, and repeating them here would give the set a
  second home that drifts from the first.
- The erratum's names are compared token-for-token against the shape-axis
  region of `SKILL.md`, over the token set AC-0101 fixes, because the pack may
  not cite the ADR and the two copies are otherwise reconciled by nothing
  (AC-0101).

- `no stub (goal-based check)` for AC-0099 and AC-0101: both are decided by
  reading a committed file, and neither adds a test.

**Approach:**
- The erratum's effect on ADR-0118's shape is read from the lint itself —
  `python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr`, which
  reports `refused: 0` over the corpus today. The roster suite
  `tests/roster/test_lint_adr_shape_corpus.py` is not that check: its own
  docstring says it asserts the lint's partition, not its findings or exit
  code, so a shape-breaking erratum leaves it green. Both guard regressions
  rather than discharging a criterion.
- The erratum carries its authority and mechanism, as the shipped errata in
  `docs/adr/0027-adr-format-is-madr-aligned-but-lean.md` do, rather than
  asserting the names alone. That is how to write it, not a criterion.
- The names are appended as an erratum rather than written into the Decision
  section: that section is frozen prose, and `## Errata` is the shipped route
  for adding to an Accepted record, as
  `docs/adr/0027-adr-format-is-madr-aligned-but-lean.md` shows.
- `docs.yml`'s `check-adr-immutability` job warns on any body edit to an ADR
  that was Accepted on the base branch. The warning is non-blocking and
  reviewers make the call, so the pull request states that the edit is an
  erratum append rather than a decision change, and the warning is expected
  rather than a surprise.

**Done when:** `python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr` still reports `refused: 0`, the erratum entry carries a date as AC-0099 requires, the three names are readable without opening this spec, and each token AC-0101 fixes matches between the erratum and the skill region.

## Rollout

A patch release of the architect pack. The axis is additive skill prose, so an
adopter who never hits a shape with an open decision sees the procedure they
have today. Reversal removes the marker-delimited region, the eval case, the construction suite, and the ADR-0118 erratum — the erratum in particular is the copy AC-0101 keeps in sync with a region that would no longer exist. What a reverted release does with its published version and changelog entry is the reverting delivery's call, not this one's.

## Risks

- The axis ships with its bet untested. The probe ran and returned no verdict,
  so T5 releases on the spec having been updated from the probe's findings, not
  on a verdict. S2 and S3 stay ungated, so the cost of being wrong is one
  revert rather than three slices built on a false premise.
- This delivery builds and releases the axis; it returns no verdict. A kill
  can only come from the study the intent names, after this release, and the
  intent carries what that costs. The cost is accepted knowingly: the axis
  sits in `main` until any such revert lands.

## Changelog

<!-- Approvals only; one line per gate, real date, approver's own handle. -->

- 2026-09-20: spec approved by eugenelim
- 2026-09-20: plan approved by eugenelim



