# Lean spec — design-craft eval coverage (pack-eval-coverage-rollout, Tier 1 + Tier 4)

Mode: light (no risk trigger fired). Single logical task — extend the
`pack-activation-evals` rollout to the `design-craft` pack, copying the
byte-shape already shipped in `core`/`converters` (Tier-A activation) and
`architect`/`product-engineering` (Tier-4 LLM-judge). Familiar pattern,
single-person, no inter-task dependencies, no new module/layer/dependency,
reversible. Recorded against the parent spec (Shipped/frozen) the way the
architect/product-engineering rollout was — `notes/` + `manual-qa.md` +
`docs/backlog.md`, no competing top-level spec.

## Objective

Give all four `design-craft` judgment/authoring skills the two eval layers
that apply to judgment skills (no deterministic B-lite layer):

- **Tier-A activation** — `evals/eval_queries.json` per skill (~8–10
  should-trigger + ~8–10 near-miss should-NOT-trigger) + a `[pack.evals]`
  block in `pack.toml`.
- **Tier-4 LLM-judge** — `evals/evals.json` per skill (`expected_output`
  + `assertions` matched to the skill's discipline).

Skills: `aesthetic-direction`, `design-critique`, `design-system-foundations`,
`layout-and-information-architecture`.

## Acceptance criteria

- [x] Each of the 4 skills ships `evals/eval_queries.json`: a flat JSON array
      of `{query: non-empty str, should_trigger: bool}`, ~8–10 each way (10/10
      per skill), the negatives near-misses (share design vocabulary/concepts
      but route to a different design-craft skill — or to a `build`/copy/architect
      concern — not trivially-irrelevant prompts). Validates under `lint-skill-spec.py`.
- [x] `pack.toml` carries `[pack.evals]` with `skills = [<all four>]`.
- [x] Each of the 4 skills ships `evals/evals.json`: `{skill_name (==dir),
      evals: [{id, prompt, expected_output, assertions:[…]}]}`, no `expect`/
      `files` (judgment skills, no B-lite). Assertions trace to each skill's
      procedure + anti-patterns. Validates under `lint-skill-spec.py`.
- [x] `design-critique` rubric spot-checked live via `run-pack-evals.py --pack
      design-craft --mode judge --judge-adapter codex` and seen to discriminate:
      a rubric-complete critique **PASS** / a vague "bigger buttons, nicer blue"
      polish note **FAIL** (and gradient near-miss FAILs en route confirmed the
      rubric grades strictly per assertion).
- [x] `lint-skill-spec.py` passes (and the design-craft agnosticism lint).
- [x] `design-craft` bumped `0.1.0 → 0.1.1` in `pack.toml` and
      `.claude-plugin/plugin.json`; `make build-self` refreshes
      `marketplace.json` to `0.1.1` (verified: the `self` subcommand
      regenerates the marketplace aggregation).
- [x] `pack-eval-coverage-rollout` backlog entry + `manual-qa.md` updated to
      record design-craft coverage.

## Task list

1. Author 4 × `eval_queries.json` (activation).
2. Author 4 × `evals.json` (judge rubrics).
3. `[pack.evals]` block + version bump (pack.toml, plugin.json).
4. `make build-self` → marketplace.json.
5. Live judge spot-check (good vs weak).
6. `lint-skill-spec.py` + the design-craft agnosticism lint + gates.
7. Update backlog + manual-qa.md.

## Boundaries

- **Never** print stack tokens or values (hex, px/rem, ARIA roles, framework
  names) anywhere — the rubrics *grade for* agnosticism; queries/rubrics stay
  portable method. (The `*.md` agnosticism lint does not scan JSON, but the
  discipline is the pack's whole point.)
- **Never** add a B-lite `expect`/`files` block — these are judgment skills.
- **Touch only** the design-craft pack's `evals/`, its `pack.toml`/`plugin.json`
  version + `[pack.evals]`, `marketplace.json` (via build-self), the backlog
  entry, and `manual-qa.md`. No runner/lint code changes.

## Declined temptations

- Tempted to add `expect`/`files` deterministic blocks; declining — the four
  skills produce judgment artifacts (docs/critiques), not deterministic files.
- Tempted to wire a design-craft line into the converters `evals.json`
  carry-over CI gate; declining — that gate is converters-specific (backlog
  `pack-evals-converters-gate-consolidation` owns consolidation), and judge
  evals.json is keyed by file presence, not a pack allowlist.
- Tempted to create a new top-level spec; declining — the parent spec is the
  home, frozen; rollout is recorded in notes/manual-qa/backlog per precedent.
