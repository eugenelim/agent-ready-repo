# Plan: adopter-clean-enforcement-gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The shipped `pre-pr.py` (`packs/core/.apm/hooks/pre-pr.py` → projects to
`tools/hooks/pre-pr.py`) is stripped to an **adopter-clean** gate: run
`loop-cohort.py check` against any active `docs/specs/*/state.json`, plus a
commented "wire your own lint/test here" stub, degrading gracefully — and
referencing **none** of the 7 catalogue linters. This repo keeps its full gate
via a new **repo-native** `tools/pre-pr-catalogue.py` (never projected) that runs
the 8 catalogue checks and then delegates to the shipped `pre-pr.py`; `make pre-pr` and
CI's aggregator job point at it. The rest is reference/doc hygiene
(`plan.md` template → `loop-cohort schedule`; `session-start.py` hint;
`max_iterations` single-source; `CONVENTIONS.md`/`conventions-check.md`/`README.md`
honesty; `AGENTS.local.md` direction) plus a `make build-self` reproject and two
backlog follow-ups. Riskiest bit: the `max_iterations` single-source touches the
`loop-cohort` schema self-test (a CI-only gate) and `lint-agents-md` drift-watch
#10a — both must move in lockstep or CI red-flags after local gates pass.

## Constraints

- **RFC-0015** owns `lint-plan-deps.py`; **RFC-0013** owns `add-credentialed-skill`
  / `example-credentialed-skill` — neither is touched; both get backlog follow-ups.
- **RFC-0002** self-host projection — pack-source edits require `make build-self`;
  `make build-check` must stay green; catalogue-internal tooling must not project.
- The local-only convention is recorded in `AGENTS.local.md`, not `CONVENTIONS.md`
  (RFC-gated).

## Construction tests

**Integration tests:**
- Run the shipped `pre-pr.py` in a tmp adopter-shaped tree (no `tools/lint-*`,
  no active specs → exit 0; with an active `state.json` → runs `loop-cohort
  check`, exit 0) (T1; AC2).

**Manual verification:**
- Reviewer confirms `CONVENTIONS.md` § Enforcement / `conventions-check.md` /
  `README.md` describe the adopter gate honestly (T6; AC7).

## Tasks

### T1: `pre-pr.py` shipped gate is adopter-clean and degrades gracefully

**Depends on:** none

**Tests:**
- Source assertion: `packs/core/.apm/hooks/pre-pr.py` matches **neither**
  `tools/lint[-_]` **nor** `test-lint-credentialed-skills` (catches the underscore
  `lint_credentialed_skills.py` + the self-test, not just `tools/lint-`). (AC1)
- Integration: run the hook in a tmp tree with no linters and no `docs/specs/*/state.json`
  → exit 0, prints a no-op/skip notice. (AC2)
- Integration: with one active `docs/specs/<f>/state.json` present → it invokes
  `loop-cohort.py check` and exits 0 (or surfaces the caps result), never a
  missing-linter crash. (AC2)

**Approach:**
- Rewrite the hook to run only: for each active spec `state.json`, the shipped
  `loop-cohort.py check <spec-dir>` (`--phase implement` + `--phase review`);
  then a commented stub block
  (`# Wire your own gate here, e.g.: _run("lint", ["make", "lint"])`).
  The hook is adopter-agnostic: it discovers `loop-cohort.py` under whichever
  adapter skill root the work-loop installed into (`.claude/`, `.agents/`,
  `.kiro/`, `.apm/`), never assuming Claude Code's `.claude/` layout.
- Remove all 8 catalogue `_run(...)` calls (the 6 `tools/lint-*.py`,
  `tools/lint_credentialed_skills.py`, `tools/test-lint-credentialed-skills.py`).
  Keep `_run`'s graceful contract but make absence-of-tool a skip, not a crash
  (those checks now live only in the catalogue-only hook).
- De-stale the docstring (drop the linter list + the `pre-pr.sh` port note).

**Done when:** AC1 + AC2 tests pass.

### T2: catalogue-only hook runs the 8 checks; repo gate stays green

**Depends on:** T1

**Tests:**
- `tools/pre-pr-catalogue.py` references all 8 catalogue checks (the exact ordered
  set the old `pre-pr.py` ran) and delegates to `tools/hooks/pre-pr.py`. (AC3)
- Goal-based: `make pre-pr` **and** `make build-check` both exit 0 and run the
  full 8-check set (not the stripped shipped hook); self-host drift confirms
  `tools/pre-pr-catalogue.py` does not project. (AC3, AC9)
- Goal-based: `tools/test-pre-pr.sh` is repointed at the catalogue hook and its
  existing regression guard passes — note it only plants corruption for the
  layers it already covers (4 linters + loop-cohort), not all 8; widening it to
  the remaining checks is out of scope here. (AC3)

**Approach:**
- Add repo-native `tools/pre-pr-catalogue.py` (NOT under any pack): run the 8
  checks in order, then `subprocess`-delegate to `tools/hooks/pre-pr.py` for the
  loop-cohort half.
- Repoint **both** Makefile invocations: the `pre-pr:` target *and*
  `build-check`'s direct `$(PYTHON) tools/hooks/pre-pr.py` call (`Makefile:74`).
- Update the `.github/workflows/docs.yml` aggregator (`hooks`) job + repoint
  `tools/test-pre-pr.sh` (which asserts the aggregator's label/fail composition)
  at the catalogue hook so its existing guard (the 4 linters + loop-cohort it
  already corrupts) keeps passing against the new composition.

**Done when:** AC3 tests pass; `make pre-pr`, `make build-check`, and the CI
aggregator all run the full 8-check set.

### T3: `new-spec` plan template references the shipped scheduler

**Depends on:** none

**Tests:**
- `packs/core/.apm/skills/new-spec/assets/plan.md` contains no
  `tools/lint-plan-deps.py` (the `loop-cohort schedule` references already stand). (AC4)

**Approach:**
- Line ~76: remove the `; tools/lint-plan-deps.py enforces this` clause —
  the per-spec `loop-cohort.py schedule` (already referenced at lines ~68/78)
  is the shipped enforcement. Pure removal, not a new reference.

**Done when:** AC4 grep passes.

### T4: `session-start.py` hint carries no adopter-facing repo path

**Depends on:** none

**Tests:**
- `packs/core/.apm/hooks/session-start.py` contains no `tools/lint-` path. (AC5)

**Approach:**
- Generalize the malformed-`patterns.jsonl` hint (drop the `run tools/lint-knowledge.py`
  reference, or point at the shipped knowledge-base README).

**Done when:** AC5 grep passes.

### T5: single-source `max_iterations`

**Depends on:** none

**Tests:**
- `loop-cohort.py` DEFAULTS contains **no hard-coded `max_iterations` literal** —
  it derives the value from the bundled `assets/state.json` template (the single
  source). (AC6)
- `loop-cohort.py` still resolves the cap (derived value == template value); the
  existing `state.get("max_iterations", DEFAULTS[...])` read works. (AC6)
- The `loop-cohort` schema self-test (`tools/test-loop-cohort.sh` — **both** the
  `expected_keys` and `defaults-match-template` blocks) passes **unchanged**. (AC6)

**Approach:**
- **Keep** `max_iterations` in `assets/state.json` (it stays the canonical,
  adopter-visible per-spec knob — no semantics change, drift-watch #10a unchanged).
- In `loop-cohort.py`, replace the hard-coded `"max_iterations": 5` in DEFAULTS
  with a value **read from the bundled template** at load (the template is already
  a sibling asset `init` reads). The `defaults-match-template` self-test then holds
  trivially (DEFAULTS value came from the template), and `expected_keys` / #10a are
  untouched.
- Keep a clearly-commented last-resort constant only for the
  template-unreadable/broken-install case (not an adopter-facing knob).

**Done when:** AC6 tests + the schema self-test pass.

### T6: doc honesty — Enforcement section, conventions-check, README, AGENTS.local.md

**Depends on:** T1, T2

**Tests:**
- Goal-based: shipped `CONVENTIONS.md` § Enforcement presents the adopter gate as
  `loop-cohort` + the adopter's own linters/tests, with no catalogue `tools/lint-*`
  as the adopter's gate and no `.github/workflows/docs.yml` as the adopter's CI. (AC7)
- Goal-based: `conventions-check.md` carries a one-line note that its named linters
  are this catalogue's own (adopters substitute their project's). (AC7)
- Goal-based: `tools/hooks/README.md`'s linter counts ("four/five/three") match the
  real set. (AC7)
- `AGENTS.local.md` contains the "adopter-facing materials ship; repo-specifics
  stay local-only" direction. (AC8)

**Approach:**
- `packs/core/seeds/docs/CONVENTIONS.md` § Enforcement: reframe the adopter gate as
  `loop-cohort` + the adopter's own linters/tests; the catalogue triplet detail
  (incl. the `docs.yml` CI mention) is reframed as "for catalogue contributors" or
  dropped from the seed so adopters aren't pointed at tooling/CI they don't have.
- `packs/core/.apm/commands/conventions-check.md`: add a **one-line** note that the
  three named linters are this catalogue's own (adopters substitute their project's);
  its manual-fallback prose already exists and stays — no larger rewrite. Same-area
  ride-along: fix the stale "Run **both** repo linters" → "these" (it documents three).
- `tools/hooks/README.md` (repo-native): correct the stale "four/five/three linters"
  counts + the pre-pr description. (`README.md` states no numeric count — leave it.)
- Append the local-only direction to `AGENTS.local.md`.

**Done when:** AC7 + AC8 hold; reviewer confirms honest framing.

### T7: reproject + green gate

**Depends on:** T1, T3, T4, T5

**Tests:**
- Goal-based: `make build-self` reprojects cleanly; `make build-check` exits 0
  (self-host drift clean; confirms catalogue-internal tooling didn't project). (AC9)

**Approach:**
- Run `make build-self`; commit the reprojected `.claude/...` + `tools/hooks/pre-pr.py`.
- Run the full agentbundle suite + `make build-check`.

**Done when:** AC9 green.

### T8: backlog follow-ups routed to owning specs

**Depends on:** none

**Tests:**
- `docs/backlog.md` contains entries for RFC-0015 (`lint-plan-deps` orphaned) and
  RFC-0013 (`add-credentialed-skill`/`example-credentialed-skill` adopter-shipping +
  the how-to-not-skill recommendation). (AC10)

**Approach:**
- Append two scoped backlog entries naming the owning spec for each:
  - RFC-0015 / `wave-scheduled-supervisor`: `lint-plan-deps.py` (its AC7
    deliverable) is invoked by **no gate** (not in `Makefile`/`.github/`) and has
    no test; this PR removed its last template anchor — decide there to wire it
    (enforce AC7) or retire it (redundant with the per-spec `loop-cohort schedule`).
  - RFC-0013 / `credential-broker-contract`: from first principles the adopter
    artifact for authoring a credentialed skill is the **how-to** (already exists:
    `docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md` + the explanation guide); the
    `add-credentialed-skill` **skill** is redundant for adopters and bound to the
    catalogue build pipeline — reconcile its + `example-credentialed-skill`'s
    adopter-shipping (demote to catalogue-local / retire) against AC27/AC43/§7.

**Done when:** AC10 entries present.

## Rollout

Bug fix to shipped `core` primitives + repo tooling. No flag; ships next release.
Reversible by revert. Existing installs unaffected until they re-run install/upgrade.

## Risks

- **`max_iterations` cross-gate coupling** (T5) — the schema self-test's
  `defaults-match-template` block requires every DEFAULTS key to be in the
  template; that's *why* the chosen mechanism keeps the key in the template and
  derives DEFAULTS from it (rather than dropping it from the template, which would
  break that block). With this mechanism `expected_keys`, `defaults-match-template`,
  and drift-watch #10a stay green unchanged. The self-test (`tools/test-loop-cohort.sh`)
  is a CI job *not* in `make build-check` — run it by hand in T5 to confirm.
- **CI aggregator job** (T2) — if `docs.yml`'s `hooks` job isn't repointed at the
  catalogue hook, the full linter set stops running via the aggregator (though the
  per-linter jobs still cover them).
- **Self-host reproject** (T7) — editing pack-source hooks/templates requires
  `make build-self`; forgetting it leaves `tools/hooks/pre-pr.py` stale and
  red-flags the drift gate.

## Changelog

- 2026-05-30: initial plan.
