# Plan: AGENTS.md lost obligations

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Constraints

- Every edit lands in the narrowest surface that governs the rule. Restoring a rule
  to the root when a scoped file owns it would re-inflate the root and undo #1049's
  intent.
- Class line caps are **not** raised. Measured headroom before this change:
  `packs/AGENTS.md` 42/80, `packs/AGENTS.local.md` 49/80,
  `packages/AGENTS.local.md` 27/80, root `AGENTS.md` 84/120,
  `packs/core/seeds/AGENTS.md` 76/100, root `AGENTS.local.md` 41/60,
  `profiles/AGENTS.md` 28/80, `web/` and `docs-site/` 32/80, `guides/` 33/80,
  `packages/AGENTS.md` 36/80, `credbroker/AGENTS.md` 25/80,
  `agentbundle/AGENTS.md` 27/80, `_example` 22/35. Total restoration is ~55 lines
  spread across fourteen files; no file approaches its cap.
- Sources of truth only. `docs/CONVENTIONS.md`, `_data/catalogue-scaffold/**`,
  `.claude/**`, `.agents/**`, `.codex/**` are regenerated, never hand-edited.
- Restored prose must be portable where it ships: no `docs/rfc/`, `docs/adr/`,
  `docs/specs/<slug>`, or `contracts/` pointer in `packs/**` or `**/seeds/**`.

## Tasks

### Task 1 — adopter-shipped pack authoring surface
Depends on: none

`packs/AGENTS.md` — AC1, AC2, AC3, AC4, AC5. Add a security-and-authoring delta
block. Portable phrasing only; this file projects into the catalogue scaffold and
ships to adopters who have no `contracts/` or `docs/` tree.

`packs/AGENTS.local.md` — AC6. Restore the allowed-content carve-out beside the
grep it qualifies, including the anti-inference sentence.

`profiles/AGENTS.md` — AC17.

### Task 2 — repo-root and adopter-seed instruction surfaces
Depends on: none

Root `AGENTS.md` — AC7, AC10, AC11, AC25 (restore the mechanism word so the two
shipped skills' bolded quotation resolves).
`packs/core/seeds/AGENTS.md` — AC7, AC10, AC11, AC12, AC25.
Root `AGENTS.local.md` — AC9, AC26.
`packages/AGENTS.local.md` — AC8.

### Task 3 — site, guide, and package surfaces
Depends on: none

`web/AGENTS.md` — AC13, AC14. `docs-site/AGENTS.md` — AC13, AC15.
`guides/AGENTS.md` — AC16. `packages/AGENTS.md` — AC18.
`packages/credbroker/AGENTS.md` — AC19. `packages/agentbundle/AGENTS.md` — AC20.
`packages/credbroker/AGENTS.local.md` and `packages/agentbundle/AGENTS.local.md` —
AC21. `packages/_example/AGENTS.md` and
`packs/monorepo-extras/seeds/packages/_example/AGENTS.md` — AC22, kept
byte-identical.

### Task 4 — falsified instructions
Depends on: none

`packs/core/.apm/skills/work-loop/SKILL.md` — AC23. Rewrite the marker comment to
state the single-home rule and that a copy fails CI.
`tools/lint-agents-md.py` — AC24, comment only; no logic change.

### Task 5 — mechanical coupling
Depends on: 1, 2, 3, 4

Run by Claude, not the worker (`python3 <script>` is refused for the worker):

1. `python3 tools/catalogue/sync_authoring_scaffold.py --write` then `--check` (AC28).
2. `make build-self` — reproject `.claude/`, `.agents/`, `.codex/`, and
   `docs/CONVENTIONS.md` from the edited `packs/core/**` sources.
3. Version bumps (AC29), each **conditional on that pack's content actually
   changing in the final diff** — read `git diff --stat` and bump only what moved,
   rather than bumping every pack the plan mentions:
   - `packs/core/pack.toml` + `packs/core/.claude-plugin/plugin.json` — patch,
     because AC7/AC10–AC12/AC25 edit `packs/core/seeds/AGENTS.md` and AC23 edits
     `packs/core/.apm/skills/work-loop/SKILL.md`. Both are `seeds/**` and `.apm/**`
     pack content. 2.9.5 → 2.9.6.
   - `packs/monorepo-extras/pack.toml` + its `.claude-plugin/plugin.json` — patch,
     **only if** AC22 changes
     `packs/monorepo-extras/seeds/packages/_example/AGENTS.md`. That path is
     `seeds/**` content of this pack, so the rule fires; if the final diff leaves the
     file untouched, do not bump. 0.1.6 → 0.1.7.
   - `packages/agentbundle/pyproject.toml` + `agentbundle/version.py` — the scaffold
     under `agentbundle/_data/catalogue-scaffold/` is bundled package data, so a
     `packs/AGENTS.md` or `profiles/AGENTS.md` edit changes the wheel. 0.38.2 →
     0.38.3; `agentbundle-v0.38.2` is tagged and released, so this is a new version
     rather than a borrowed unreleased one.
4. `docs/product/changelog.md` release entries.
5. Commit carries `Engine-Change-RFC: n/a — <reason>`, following #1049's precedent
   for instruction-surface work.

## Verification

Full gate set after every source change, each captured to its own file with its own
exit code:

- `python3 tools/lint-agents-md.py`
- `python3 tools/catalogue/sync_authoring_scaffold.py --check`
- `python3 -m pytest packs/core/tests/pack/ -q`
- `python3 -m pytest tools/test_lint_agents_md_risk_block.py -q`
- `python3 -m pytest tools/test_lint_agents_md_progressive_disclosure.py -q`
- `make lint-ruff`
- `make ci`

Baselines recorded before any edit: `lint-agents-md` rc=0,
`sync_authoring_scaffold --check` rc=0, `packs/core/tests/pack/` rc=0 (15 passed).
Pack suites must be invoked one process per skill directory; the Makefile warns
against collapsing them and a collapsed run fails collection on duplicate test
basenames.

## Risks

- **Parent/child duplication check.** `lint-agents-md.py` flags a scoped file that
  exactly duplicates its parent. Restoring the same rule to both root `AGENTS.md`
  and the seed is intended and permitted (they are not parent/child), but a scoped
  file must not copy a root bullet verbatim.
- **Seed link contract.** `packs/core/tests/pack/test_work_intake_surface.py` asserts
  the seed carries exactly two relative link targets. Restored seed prose must add no
  markdown link.
- **Risk-trigger lint.** Any file other than the three work-loop `SKILL.md` paths
  carrying `risk-triggers:start` fails. AC23 rewrites prose inside the existing
  marker; the marker itself stays exactly one complete block in the canonical source.

## Follow-ups

- `_profile_lint_one` duplicate-name false-positive ordering violation.
- Converting restored security rules (AC1–AC4) into machine checks.
- Gate G's changelog condition, and whether it should assert the package CHANGELOG.
