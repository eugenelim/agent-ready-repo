# Plan: lint-work-loop-delivery

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

A relocation + rewiring, no logic change. `git mv` the lint and its self-test
into `packs/core/.apm/skills/work-loop/scripts/`; fix the one path the self-test
uses to find the linter; rewrite the work-loop SKILL.md framing (catalogue-only
→ shipped skill script the agent runs at finish-time, plus the catalogue CI
gate); point the Makefile at the projected copy; correct the lint docstring and
K-0009; `make build-self` to project; `make build-check` to prove drift-clean +
gate-green. The riskiest part is path resolution after the move (self-test
sibling path, repo-root discovery) — both covered by the relocated self-test
running green and a clean live-corpus run.

## Constraints

- **RFC-0016 § Errata** authorises shipping the lint to adopters as a work-loop
  skill script; the `doc-drift-prevention` catalogue-only Boundaries are
  superseded by a matching erratum (both recorded before this implementation).
  AC6 also requires **ADR-0007** (the ADR-level narrowing), written in T3 — the
  RFC erratum + spec changelog are pre-landed; the ADR is authored in this PR.
- Lint invariant logic — including the `spec-code-ref-lint` invariant-(iii)
  code-reference extension — is **frozen** for this change.

## Construction tests

**Integration:** `make build-check` exits 0 and drift-clean (projected
`.claude/skills/work-loop/scripts/` matches pack source). **Manual:** none.

## Tasks

### T1: relocate the lint + self-test into the work-loop skill

**Depends on:** none

**Tests:**
- TDD (AC1/AC2): `python .claude/skills/work-loop/scripts/test-lint-spec-status.py`
  (after build-self) is green from the new location; `git ls-files` shows the
  pair under `packs/core/.apm/skills/work-loop/scripts/` and **nothing** under
  `tools/lint-spec-status.py` / `tools/test-lint-spec-status.py`.

**Approach:**
- `git mv tools/lint-spec-status.py tools/test-lint-spec-status.py` into
  `packs/core/.apm/skills/work-loop/scripts/`.
- In the self-test, change `LINTER = REPO_ROOT / "tools" / "lint-spec-status.py"`
  to the sibling: `Path(__file__).resolve().parent / "lint-spec-status.py"`, and
  **delete the now-unused `REPO_ROOT` line** (from a skill `scripts/` dir its
  `parents[1]` is a meaningless path — a latent trap).
- Update the lint module docstring: it is now a work-loop skill script that
  ships to adopters (agent-invoked at finish-time) **and** runs as the
  catalogue's CI gate; the "do NOT wire into pre-pr.py" note stays.

**Done when:** the relocated self-test is green and `git ls-files` confirms the
move with no `tools/` remnant.

### T2: wire work-loop SKILL.md + Makefile; drop the tools/ invocation

**Depends on:** T1

**Tests:**
- Goal-based (AC3): `grep` `packs/core/.apm/skills/work-loop/SKILL.md` for a
  finish-time instruction to run `scripts/lint-spec-status.py`.
- Goal-based (AC4): `grep` the Makefile `build-check` target runs
  `.claude/skills/work-loop/scripts/lint-spec-status.py` (+ self-test) and the
  `tools/lint-spec-status.py` lines are gone.
- Goal-based (AC5): `grep -c` lint name in `packs/core/.apm/hooks/pre-pr.py` is 0.

**Approach:**
- Rewrite the § GATES catalogue-governance note: the lint is a work-loop skill
  script run at finish-time on every adapter with Python; the catalogue also
  gates it in CI. Add the finish-time invocation line to the § DECIDE
  end-of-session checklist (next to the four drift invariants).
- Makefile `build-check`: replace the two `tools/...` lines with the projected
  `.claude/skills/work-loop/scripts/...` paths (mirrors how pre-pr.py invokes
  loop-cohort from `.claude/`).

**Done when:** all three greps pass.

### T3: write ADR-0007, reconcile live references, project, gate

**Depends on:** T1, T2

**Tests:**
- Goal-based (AC6): `docs/adr/0007-*.md` exists, Accepted, cites ADR-0006 +
  RFC-0016 § Errata, records the narrowing.
- Integration (AC7): `make build-check` exits 0, drift-clean.
- Goal-based (AC7): K-0009 body no longer claims the spec-status lint is
  catalogue-only / has no `packs/` source; the lint's own invariant (iii) emits
  **no** dangling-ref warning for a stale `tools/lint-spec-status.py`.

**Approach:**
- Write **ADR-0007** (narrows ADR-0006's delivery sub-claim; see AC6).
- `make build-self` to project the new skill script + SKILL.md changes.
- **Reconcile the *live, editable* surfaces** that asserted the old
  catalogue-only location (a repo-wide grep, not a guessed list):
  - `docs/specs/README.md` `doc-drift-prevention` row — update "runs from the
    Makefile `build-check` … catalogue governance" to the corrected delivery.
  - knowledge **K-0009** (catalogue-lint-placement) and **K-0010** (body
    references `tools/lint-*.py`) — correct the spec-status lint's home.
  - `docs/backlog.md` — the "promote invariant (iii) to hard" item references
    `tools/lint-spec-status.py`; repoint it to the new path (otherwise it
    becomes a dangling code-ref the lint's own invariant (iii) would warn on).
- **Intentionally NOT swept** (Frozen bodies — immutable; the errata/ADR-0007
  carry the correction instead): RFC-0016's body, `doc-drift-prevention` AC
  bodies, ADR-0006's body, and the `spec-code-ref-lint` ACs that already shipped
  describing the lint generically. (`spec-code-ref-lint` has *no* hard-coded old
  `tools/` path to change — verified by grep.)
- Run `make build-check`.

**Done when:** ADR-0007 exists; `make build-check` is green and drift-clean;
K-0009/K-0010 and the README row corrected; no stale-path warning from the lint.

## Rollout

Big-bang within the catalogue, reversible. Adopters gain the script on their next
install (projected). No behaviour change to the lint itself.

## Risks

- **Path resolution breaks after the move** (self-test sibling, repo-root). Caught
  immediately by the relocated self-test + live-corpus run.
- **Stale `tools/lint-spec-status.py` references** linger in docs. Mitigated by a
  repo-wide grep in T3 and — fittingly — the lint's own invariant (iii) code-ref
  check, which would warn on a dangling `tools/lint-spec-status.py`.
- **build-self __pycache__ pollution** from running the script (seen before).
  Mitigated by cleaning `packs/**/__pycache__` before `build-check`.
- **The Makefile gate runs the *projected* `.claude/` copy** (mirroring how
  `pre-pr.py` invokes projected `loop-cohort.py`). Consequence: a source edit to
  the lint requires `make build-self` before `build-check` reflects it — the
  `agentbundle.build check` drift step catches an un-projected source edit, so
  this is safe, but it's the same sharp edge the `loop-cohort` contract has.

## Changelog

- 2026-05-29: initial plan (RFC-0016 § Errata follow-on — ship the lint as a
  work-loop skill script).
