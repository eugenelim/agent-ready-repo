# Plan: Visual handoff golden path

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tests/AGENTS.md` (repository-level assertions live in
  `tests/roster/`; registration obligations) and `tools/lint-pack-test-boundary.py`
  check 8; analogous construction path
  `tests/roster/test_credential_brokers_atlassian_integration.py` (copies a pack
  into a temporary catalogue and runs `install.run` from a parsed `install`
  namespace); analogous registration in commit 73960b9f0 (two roster tests: a
  named `build-check.yml` step plus both `tools/lint-ci-parity.py` axes).
  Deviation: no existing test installs two packs together; this one runs the
  install twice into one repository.

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

Build one roster test module over one fixture tree. A module-scoped fixture
installs both packs into a temporary repository; every rule the test applies is
parsed from that installation. A table walk resolves each fixture path; value,
loop and eval checks run against the same installation. The riskiest part is
the walk turning into a second copy of the contract, so it reads every decision
cell from the installed tables and fails on any vocabulary it does not know,
and AC-0008's mutation controls prove the cells drive the outcome.

## Constraints

- ADR-0130 — the design-to-build handoff is conditional and gap-routed: a gap
  holds an axis, it never demotes.
- ADR-0132 — the approved-target rung resolves only on `visual_target: confirmed`.
- `tools/lint-experience-agnostic.py` — no value shapes in
  `packs/experience-design/**.md`; the value-bearing fixtures live under
  `tests/roster/fixtures/`.
- `packs/AGENTS.md` — the evals change bumps the frontend pack patch version and
  carries no internal-governance citation.
- User decision 2026-10-03 — no change to `agentbundle pack evals run`; golden
  eval prompts begin after the handoff read and state what it extracted.
- User decision 2026-10-03 — the eval runner's `output_excludes` is a plain
  substring test (`pack_evals.py:908-910`), so golden cases exclude the
  fallback's declaration forms and placeholder value, never the bare `--ds-`
  prefix a correct explanation may mention.
- User decision 2026-10-04, replacing the exclusion forms above — `--ds-*` is
  the pack's system-token namespace, used when a taxonomy records no naming of
  its own, so golden cases exclude only the fallback's own colour values.

## Construction tests

**Integration tests:** the whole deliverable is one integration test module,
`tests/roster/test_visual_handoff_golden_path.py`; per-task `Tests:` name its parts.
**Manual verification:** one in-harness or headless run of
`agentbundle pack evals run frontend-engineering` over the golden cases, where
the environment supports it; otherwise its unavailability is recorded in the
verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Executable cross-pack contract — the roster test and fixtures | T1, T2, T3, T4 | `pytest tests/roster/test_visual_handoff_golden_path.py` green | CI step present and green |
| Release history — changelog | T4 | `## [frontend-engineering][0.4.2]` section | `catalogue verify` exits zero |

## Design (LLD)

### Design decisions

- **Install, then read.** The test runs `agentbundle install --pack <p> --scope
  repo --adapter claude-code` once per pack into one temporary repository, each
  from a temporary catalogue holding a copy of the pack, and reads skills from
  `.claude/skills/`. Reading `packs/` source would prove nothing about the
  shipped projection. Traces to AC-0001.
- **A table walk, not a re-statement.** The walk evaluates each precedence
  row's `Requires` cell from a closed predicate vocabulary, joined by ` and `,
  and raises on any other token. The composition rung is the first row whose
  predicate holds; the values rung is the first holding row whose `Binds` cell
  does not begin `Composition only`. Standalone admission evaluates the
  installed `admits` tokens the same way. A refusal consults the installed
  `refusal-demotes` cell: `never` halts; `always` continues down the ladder,
  which is what makes AC-0008's mutation observable without the unknown-token
  guard. Traces to AC-0002–AC-0008.
- **Predicate meanings — fixed test assumptions.** No installed cell defines
  these, so the walk states them once and the scenarios exercise them:

  | Predicate | Holds when |
  | --- | --- |
  | `visual_target: <v>` | the resolved direction's frontmatter `visual_target` equals `<v>`; `<v>` must be one of the values the installed creative-direction template declares |
  | `artifact-resolved` | the read resolved the direction or the taxonomy |
  | `established-surface` | the scenario declares `incumbent_system = true` |
  | `no-higher-rung-resolved` | no row above held |
  | `no-upstream-gap-held` | the walk holds no gap |
  | `no-applicable-design-artifact` | the read resolved no artifact |
  | `no-incumbent-system` | `incumbent_system = false` |
  | `no-upstream-authority-to-complete` | the walk holds no gap |
  | `handoff-read-completed` | the read ended without a refusal |


- **Per-domain value outcome.** The value domains are the rows of the installed
  taxonomy template's Authority table. For each domain the walk returns one
  of: `taxonomy`, `incumbent`, `fallback`, `local-premise`, or a held gap
  `(domain, operation kind)`. A resolved taxonomy supplies every domain it does
  not record unresolved; an unresolved domain is held as
  `domain-completion-required`. A resolved direction beside a named-skip
  taxonomy slot with no incumbent holds every domain as
  `taxonomy-supply-required`. Otherwise an incumbent supplies the domain, and
  only an admitted standalone path reaches the fallback. The two gap sources
  are implemented here and pinned by asserting the installed `gap-sources`
  cell still names both a named-skip `tokens/<slug>.md` slot and a needed
  domain unresolved; the operation kinds and the record's two fields are read
  from `gap-record-contents`. Traces to AC-0004, AC-0005.
- **Incumbent presence is a declared fixture fact.** Detecting an incumbent
  system is agent judgement, so each `scenario.toml` declares
  `incumbent_system`; the confirmed fixture also ships the incumbent file its
  taxonomy traces to. Traces to AC-0004, AC-0006, AC-0010.
- **Values are compared by role.** A taxonomy role `accent.action` in the
  Color table binds to `--color-accent-action`; a spacing step `space.3` binds
  to `--space-3`. Fixture colours and spacing are chosen outside the installed
  fallback block's value set, so a substituted fallback value is always a
  mismatch. Each Accessibility pairing names its element class (`Body text`,
  `Large text …`, `UI components …`) as the installed contrast-floor table
  spells it; the threshold is that row's ratio. Traces to AC-0009–AC-0013,
  AC-0023.
- **Run records are JSON event lists.** Each event has a `step`
  (`render`, `observe`, `correct`, `gate`, `residual`) and its fields — a
  render's `state` and `capture`, an observation's `material_gaps` with
  `class`, a gate's `name`, `ran`, `reason` when not run, and `result_state`
  for the rendered-page inspection. The checker reads its bounds from the
  installed `## Loop bound` table, state names from the installed
  `## Representative states` table, and gate order from the installed GATES
  headings. A top-level `manifest.unverified_items` mirrors the installed
  evidence-manifest row. Negative records are derived in-test from the
  confirmed one for AC-0016, and from the no-browser one for
  AC-0017. Traces to AC-0014–AC-0017, AC-0024.
- **Model evals stay skill-local.** Golden cases live in the frontend skill's
  `evals.json`, because frontend owns the consumption choice; their
  `expect.output_contains` values are cross-checked against the fixture
  taxonomy from the installed copy. Traces to AC-0018–AC-0020.

<!-- Owned by: T1, T2, T3, T4. -->

### Data & schema

Fixture tree, under `tests/roster/fixtures/visual-handoff-golden-path/`:

| Path | Holds |
| --- | --- |
| `<scenario>/scenario.toml` | `slug`, `incumbent_system`, `conditional_states` |
| `<scenario>/agentbundle-layout.toml` | `[design] output_dir = "design"` (absent for `standalone`) |
| `<scenario>/design/direction/checkout.md` | `type: creative-direction`, `visual_target` |
| `<scenario>/design/tokens/checkout.md` | `type: token-taxonomy` with Authority, Color and Spacing role tables, Accessibility pairings, Unresolved decisions |
| `confirmed/src/styles/brand.css` | incumbent evidence |
| `confirmed/implementation/tokens.css`, `index.html` | golden implementation |
| `confirmed/run-record.json`, `no-browser/run-record.json` | run records |

The seven fixture directories are the ones the spec's Agent Rules § Ask first names.

<!-- Owned by: T1, T2, T3. -->

## Tasks

### T1: Six fixture paths resolve through the installed rules

**Depends on:** none
**Touches:** tests/roster/test_visual_handoff_golden_path.py, tests/roster/fixtures/visual-handoff-golden-path/**
**Tests:**
- AC-0001: module-scoped install fixture; a missing installed table raises a named assertion.
- AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007: one test per scenario asserting the walk's composition rung, value rung, value source, gaps, record and loaded-file set.
- AC-0008: two in-test mutations of the installed `visual-observation.md`, each re-walking one scenario.
- `stub: true`

```python
from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "visual-handoff-golden-path"
SCENARIOS = (
    "confirmed",
    "unconfirmed",
    "missing-taxonomy",
    "unresolved-domain",
    "standalone",
    "refusal",
)


def test_every_scenario_fixture_is_present() -> None:
    """Verifies AC-0001's surface: each of the six paths has a fixture tree."""
    missing = [s for s in SCENARIOS if not (FIXTURES / s / "scenario.toml").is_file()]
    assert not missing, f"scenario fixtures missing: {missing}"
```

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py tests/roster/test_visual_target_exclusive_property.py -q` passes.

### T2: Concrete values travel from taxonomy to implementation

**Depends on:** T1
**Touches:** tests/roster/test_visual_handoff_golden_path.py, tests/roster/fixtures/visual-handoff-golden-path/confirmed/**
**Tests:**
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0023: provenance, incumbent, contrast, rung-name and adaptation tests over the confirmed fixture, the installed `design-system` rung table and the installed contrast-floor table.
- AC-0013: consumption test plus the two in-test substitutions.
- no stub (implementation-discovered) — discovery predicate: the T1 install fixture and fixture-taxonomy parser exist; proof obligation: the substitution mutation reds the consumption check.

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py tests/roster/test_visual_target_exclusive_property.py -q` passes.

### T3: Render, observe and correct precede the gates

**Depends on:** T1
**Touches:** tests/roster/test_visual_handoff_golden_path.py, tests/roster/fixtures/visual-handoff-golden-path/confirmed/run-record.json, tests/roster/fixtures/visual-handoff-golden-path/no-browser/**
**Tests:**
- AC-0014, AC-0015, AC-0024: ordering, bound and representative-state tests over the confirmed run record.
- AC-0016: five in-test negative records.
- AC-0017: no-browser record test reading the installed result-state table, plus two in-test negatives derived from that record — a Chromium-requiring gate set to `ran: true`, and one of their reasons emptied — each rejected.
- no stub (implementation-discovered) — discovery predicate: the T1 install fixture exists; proof obligation: each negative record is rejected by name.

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py -q` passes.

### T4: Golden model-eval cases and the frontend release

**Depends on:** T2, T3
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py, docs/product/changelog.md, tests/roster/test_visual_handoff_golden_path.py, tests/roster/test_visual_target_exclusive_property.py
**Tests:**
- AC-0018, AC-0019, AC-0020: tests over the installed `evals.json`, cross-checking each AC-0019 case against its own scenario's fixture taxonomy.
- `test_visual_target_exclusive_property.py`: after every fixture, test and eval file of this delivery exists, re-measure the non-Markdown carrier count, raise `NON_MARKDOWN_CARRIER_FLOOR` to it, and update the measurement date and docstring history in the same edit, as that module's docstring requires.
- AC-0022: goal-based — `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .`; no stub (goal-based).
- The frontend pack's own suite stays green: `python3 -m pytest packs/frontend-engineering/tests -q`.

**Approach:**
- Release order follows `packs/AGENTS.local.md` § Marketplace and release pipeline: bump `pack.toml` and `plugin.json`, move the release pin in `test_visual_authority_release.py`, run `FORCE=1 make build-self` to regenerate `marketplace.json`, then write the changelog section. The Highlights disposition is "none": eval cases do not change what a consumer of the pack can do; the PR records that verdict.

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py tests/roster/test_visual_target_exclusive_property.py -q` passes after the floor edit, and the frontend pack suite and both catalogue commands pass.

### T5: The roster test runs in CI

**Depends on:** T1
**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py
**Tests:**
- AC-0021: goal-based — `python3 tools/lint-ci-parity.py` exits zero and `tools/test_build_gate_chain.py` passes; no stub (goal-based).

**Done when:** both commands exit zero.

Review shape: one review unit, DEEP — the fixtures, test, and eval cases prove
one handoff and cannot be reviewed apart.

## Rollout

Test, fixture and eval content only. The frontend pack ships a patch release
whose only change is eval content; rollback is a revert.

## Changelog

- 2026-10-03: spec approved by eugenelim
- 2026-10-03: plan approved by eugenelim
