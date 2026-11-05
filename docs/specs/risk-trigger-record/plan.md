# Plan: Risk-trigger record on the spec header

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `new-spec` `references/spec-and-plan-contract.md` § Spec metadata contract (the `Shape:` and `Priority:` bullets are the analogous optional header fields); `lint-spec-status.py` invariant (vi) and its `Acceptance Criteria:` header parsing, tested in `packs/core/tests/skills/work-loop/test_lint_spec_status.py`; deviation: none.

## Approach

Add the header field where the other spec metadata lives, teach the lint one
more per-spec invariant, and pin the guidance with one pack test. The riskiest
part is vocabulary drift between three homes: the contract table, the lint's
token set, and the risk-trigger block. One test reads all three.

## Constraints

- The risk-trigger block in `work-loop` `SKILL.md` is byte-pinned by
  `tools/lint-agents-md.py` check 10g and by pack tests; this plan reads it and
  never edits it.
- Version bump rule in `packs/AGENTS.md`: patch for changed content.

## Construction tests

**Integration tests:** none beyond per-task tests.

**Manual verification:** run `lint-spec-status.py --root . --all --verbose` on
this branch and record in the ledger that it exits 0, that this spec draws no
(vii) finding, and that `docs/specs/ast10-pack-compliance/spec.md`, whose
preamble carries a bare `**Risk triggers:**` prose line, draws none either.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Published schema | T1 | `test_risk_trigger_record_contract.py` | test green |
| Lint invariant | T2 | `test_lint_spec_status.py` (vii) cases, token-set pin | tests green |
| Agent guidance | T3 | `test_risk_trigger_record_contract.py` | test green |
| User documentation | T3 | how-to sentence | ledger grep |
| Measurement plan | T4 | `docs/product/research/mode-decision-re-measure.md` | ledger grep |
| Release history, projections | T5 | `check-core-release.py`, `self-host --check` | both exit 0 |

## Design (LLD)

### Data & schema

- Grammar: AC-0007 defines the line. Mechanism: hide HTML comments across
  the whole preamble (before the first `## ` heading) the way `parse_status`
  does, skip fenced lines, and match `^- \*\*Risk triggers:\*\*` at column 0.
  A value is `none`, or tokens split on `,` with surrounding spaces trimmed;
  matching follows AC-0003. T2 fixtures include a valid line beside an empty-valued one (no
  violation), a trailing comma (hard), and a non-`Draft` new spec with no line
  (no finding). Traces to AC-0003 to AC-0007.
- Tokens, in risk-trigger block order:

  | Token | Trigger |
  | --- | --- |
  | `security-boundary` | Compliance, governance, or security boundary |
  | `structural-interface` | Structural or public-interface change |
  | `persistent-representation` | Persistent representation or mixed-version deployment |
  | `destructive-operation` | Destructive or irreversible operation |
  | `data-transformation` | Backfill, replay, import, export, or destructive transformation |
  | `new-dependency` | New dependency |
  | `unfamiliar` | Unfamiliar |
  | `multi-person` | Multi-person |
  | `multi-feature` | Multi-feature or dependent tasks |

  The contract reference owns this table; the plan copy is delivery residue.

### Behavior & rules

- "Added since the base ref" is `base_spec_text(...)` returning `None` while
  the base resolves; with no base ref the absence check is skipped, the same
  way invariant (vi) skips. Traces to AC-0005, AC-0006.

## Tasks

### T1: The contract table and template line agree with the risk-trigger block

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md, packs/core/.apm/skills/new-spec/assets/spec.md, packs/core/tests/pack/test_risk_trigger_record_contract.py

**Tests:**
- AC-0001 — goal-based: a new pack test parses the table under the
  `Risk triggers` bullet and the bold labels of the bullets inside the
  risk-trigger markers, and compares the two ordered sequences.
- AC-0009 (template half) — goal-based: the same test counts exactly one
  header line in `assets/spec.md`.

**Done when:** `python3 -m pytest packs/core/tests/pack/test_risk_trigger_record_contract.py -q` and `make precheck` pass.

### T2: Invariant (vii) refuses malformed values and warns on a missing line

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py, packs/core/tests/skills/work-loop/test_lint_spec_status.py, packs/core/tests/pack/test_risk_trigger_record_contract.py

**Tests:**
- AC-0003 to AC-0007 — TDD at the lint's `check` boundary, with fixture specs
  in a temporary git repository: one case per clause, including a commented-out
  line, a bare `**Risk triggers:**` line, a body line, and a backticked value.
- AC-0002 — goal-based: the T1 test loads the lint module under a
  pack-and-skill-qualified name and compares its token set with the table.
- The module docstring lists (vii), and each "no base ref" skip warning names
  (vii) among the invariants it skips.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_lint_spec_status.py packs/core/tests/pack/test_risk_trigger_record_contract.py -q` and `make precheck` pass, and the manual verification above is recorded in the ledger.

### T3: PLAN step 2, eval cases and the how-to name the line

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/.apm/skills/new-spec/evals/evals.json, guides/core/how-to/plan-and-execute-non-trivial-work.md, packs/core/tests/pack/test_risk_trigger_record_contract.py

**Tests:**
- AC-0008, AC-0009 (eval half) — goal-based: the T1 test pins the PLAN step 2
  sentence and one case per eval file whose assertions name `Risk triggers`.
- AC-0010 — goal-based: `grep -n "Risk triggers:" guides/core/how-to/plan-and-execute-non-trivial-work.md`
  output recorded in the ledger.

**Done when:** the T1 test, `python3 tools/lint-agents-md.py` and `make precheck` pass.

### T4: The re-measure note names each condition

**Depends on:** none

**Touches:** docs/product/research/mode-decision-re-measure.md

**Tests:**
- AC-0011 — goal-based: one `## ` section per question, each with `Baseline`,
  `Re-measure when` and `Method` lines, checked by `grep -c` and recorded in the
  ledger.

**Done when:** the grep shows three of each line and `lint-spec-status.py --root .` exits 0.

### T5: Core release and projections

**Depends on:** T1, T2, T3

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*.md

**Tests:**
- AC-0012, AC-0013 — goal-based.

**Done when:** `python3 tools/check-core-release.py --base origin/main`, `agentbundle catalogue self-host --root . --check` and `make precheck` exit 0.

## Changelog

<!-- approvals only -->

- 2026-11-05: spec approved by eugenelim (scope)
- 2026-11-05: plan approved by eugenelim (build strategy)
