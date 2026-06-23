# Lean spec — governance-extras eval coverage (pack-eval-coverage-rollout, Tier 1 + Tier 4)

Mode: light (no risk trigger fired). Single logical task — extend the
`pack-activation-evals` rollout to the `governance-extras` pack, copying the
byte-shape already shipped in `core`/`converters` (Tier-A activation) and
`architect`/`product-engineering`/`design-craft` (Tier-4 LLM-judge). Familiar
pattern, single-person, no inter-task dependencies, no new module/layer/
dependency, reversible. The `[pack.evals]` block is an additive field on an
established manifest interface (same as `core`/`design-craft`), not a new
interface. Recorded against the parent spec (Shipped/frozen) the way the
design-craft rollout was — `notes/` + `manual-qa.md` + `docs/backlog.md`, no
competing top-level spec.

One thing differs from design-craft and is load-bearing: **governance-extras is
self-host-projected** (`make build-self` projects core + governance-extras into
this repo's own `.claude/skills/` + `.agents/skills/`), and the build-self drift
gate is part of `make build-check`. So after editing the source under
`packs/governance-extras/.apm/skills/`, run `make build-self` and confirm
`make build-check` is green (it covers the projection drift here — it did not for
design-craft, which is not self-host-projected).

## Objective

Give all three `governance-extras` judgment/authoring skills the two eval layers
that apply to judgment skills (no deterministic B-lite layer):

- **Tier-A activation** — `evals/eval_queries.json` per skill (~8–10
  should-trigger + ~8–10 near-miss should-NOT-trigger) + a `[pack.evals]`
  block in `pack.toml`.
- **Tier-4 LLM-judge** — `evals/evals.json` per skill (`expected_output`
  + `assertions` matched to the skill's discipline).

Skills: `new-adr`, `new-rfc`, `update-conventions`.

## Acceptance criteria

- [x] Each of the 3 skills ships `evals/eval_queries.json`: a flat JSON array
      of `{query: non-empty str, should_trigger: bool}`, 10 each way per skill,
      the negatives near-misses (share governance/decision vocabulary but route
      to a sibling governance skill — `new-adr`↔`new-rfc`↔`update-conventions` —
      or to `new-spec`/`bug-fix`/`new-guide`/a plain PR, not trivially-irrelevant
      prompts). Validates under `lint-skill-spec.py`.
- [x] `pack.toml` carries `[pack.evals]` with `skills = [<all three>]`.
- [x] Each of the 3 skills ships `evals/evals.json`: `{skill_name (==dir),
      evals: [{id, prompt, expected_output, assertions:[…]}]}`, no `expect`/
      `files` (judgment skills, no B-lite). Assertions trace to each skill's
      procedure + anti-patterns. Validates under `lint-skill-spec.py`.
- [x] At least one rubric spot-checked live via `run-pack-evals.py --pack
      governance-extras --mode judge --judge-adapter codex --artifacts <file>`
      and seen to discriminate good-vs-weak.
- [x] `lint-skill-spec.py` passes.
- [x] `governance-extras` bumped `0.3.0 → 0.3.1` in `pack.toml` and
      `.claude-plugin/plugin.json`; `make build-self` projects the new evals
      and refreshes `marketplace.json`; `make build-check` is green (drift gate
      covers the self-host projection).
- [x] `pack-eval-coverage-rollout` backlog entry + `manual-qa.md` updated to
      record governance-extras coverage.

## Task list

1. Author 3 × `eval_queries.json` (activation).
2. Author 3 × `evals.json` (judge rubrics).
3. `[pack.evals]` block + version bump (pack.toml, plugin.json).
4. `make build-self` → projection + marketplace.json; `make build-check` green.
5. Live judge spot-check (good vs weak).
6. `lint-skill-spec.py` + gates.
7. Update backlog + manual-qa.md.

## Boundaries

- **Touch only** the governance-extras pack's `evals/`, its `pack.toml`/
  `plugin.json` version + `[pack.evals]`, the self-host projection +
  `marketplace.json` (via `make build-self`), the backlog entry, and
  `manual-qa.md`. No runner/lint code changes.
- **Never** edit the projected paths (`.claude/skills/`, `.agents/skills/`,
  `marketplace.json`) by hand — they are generated; edit the source under
  `packs/governance-extras/.apm/skills/` then `make build-self`.
- **Never** add a B-lite `expect`/`files` block — these are judgment skills.

## Declined temptations

- Tempted to add `expect`/`files` deterministic blocks; declining — the three
  skills produce judgment artifacts (an ADR, an RFC, a routing decision), not
  deterministic files to re-derive.
- Tempted to give `update-conventions` a B-lite check on "did it open an RFC";
  declining — the skill's value is the judgment to route through RFC and exempt
  trivial edits, which is a rubric assertion, not a deterministic post-condition.
- Tempted to create a new top-level spec; declining — the parent spec is the
  home, frozen; rollout is recorded in notes/manual-qa/backlog per precedent.
