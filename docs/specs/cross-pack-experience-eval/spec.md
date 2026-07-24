# Spec: cross-pack-experience-eval

**Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
**Mode:** full (risk triggers: structural — new eval surface + new standalone tool; cross-pack impact across four packs)
**Owner:** eugenelim
**Plan:** [`plan.md`](plan.md)
**Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) (ini-003 M5), [spec/xd-state-reviewer-doctrine](../xd-state-reviewer-doctrine/spec.md) (1.5.0 upstream — three-pass design-review doctrine must be validatable at chain level)
**Contract:** tools/check-xd-chain.py; packs/experience-design/.apm/evals/cross-pack-fixtures.json; docs/guides/experience-design/how-to/run-cross-pack-eval.md; tools/test-all.py (wired); pack version 1.5.0 → 1.6.0

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

No cross-pack eval coverage validates that the full XD skill chain (design-token-taxonomy → design-system-foundations → information-architecture → copy-direction → design-review) fires in the right sequence and that pack boundaries stay clean. Skills can drift — a `Do NOT use` guard can reference a non-existent neighbor, or a chain skill can disappear after a rename — without any sentinel catching it.

This spec delivers:

1. **Deterministic checks** (`tools/check-xd-chain.py`) — five structural invariants validated without an LLM: chain completeness, no phantom handoffs, boundary guards present, Digital Experience Contract copies present, and description-length check (each chain skill description within the 1024-char agentbundle cap).
2. **Cross-pack eval fixtures** (`packs/experience-design/.apm/evals/cross-pack-fixtures.json`) — four golden-path scenario types, three multi-intent routing examples, three boundary violation cases, and three weak regression fixtures — all in report-only mode (calibrate before promoting to gates).
3. **Integration with existing toolchain** — the deterministic checker produces report output in the same style as existing linters; exits 0 in report-only mode (the default); a `--gate` flag promotes it to a fail-closed gate when calibration is complete. The self-test is wired into `tools/test-all.py`.
4. **How-to guide** (`docs/guides/experience-design/how-to/run-cross-pack-eval.md`) — how to run the checker, interpret report-only output, and promote to a gate.

**Done when:** the deterministic checks pass (`check-xd-chain.py --gate --root .` exits 0 against the live repo); fixture file is valid and has the required coverage breadth; the how-to guide is published.

## Boundary guard adjacency map

The checker uses an **explicit adjacency map** derived from the actual frontmatter of the five chain skills (not a theoretical bidirectional chain). Each skill must backtick-reference its designated neighbors in its `description:` frontmatter field:

| Skill | Must backtick-reference |
|-------|------------------------|
| design-token-taxonomy | `design-system-foundations` |
| design-system-foundations | `design-token-taxonomy`, `information-architecture` |
| information-architecture | `copy-direction` |
| copy-direction | `content-design`, `tone-of-voice` |
| design-review | `copy-direction` |

`design-review` also guards `creative-direction`, `design-token-taxonomy`, and `information-architecture` using unquoted references — these are present and correct but outside the backtick-check scope (the spec does not require a format change in SKILL.md content).

## Phantom handoff exemption

The phantom-handoff check finds every backtick-quoted name in the `description:` frontmatter field and verifies each resolves to an existing SKILL.md within the experience-design pack. It **exempts cross-pack references**: a backtick name accompanied by explicit pack-qualification in the surrounding sentence (e.g., `ux-writing` in the `product-engineering` pack) is not a phantom. Pack names themselves (e.g., `` `product-engineering` ``) are also exempt. Scanning the full description (not only `Do NOT use` sentences) means future additions of backtick-quoted terms outside guard clauses are also checked.

## Boundaries

**In scope:**
- `tools/check-xd-chain.py` — standalone deterministic checker (stdlib only; no new dependencies)
- `tools/test-check-xd-chain.py` — self-test for the checker (same pattern as existing `test-*.py` tools in `tools/`)
- `tools/test-all.py` — add `test-check-xd-chain.py` to the TESTS list
- `packs/experience-design/.apm/evals/cross-pack-fixtures.json` — cross-pack eval fixture file (new directory `packs/experience-design/.apm/evals/`; source-only, not projected by build-self)
- `docs/guides/experience-design/how-to/run-cross-pack-eval.md` — how-to guide (Diátaxis how-to format)
- `packs/experience-design/pack.toml` + `packs/experience-design/.claude-plugin/plugin.json` — version bump 1.5.0 → 1.6.0
- `workspace.toml` — move `spec/cross-pack-experience-eval` from queue to shipped
- `.claude-plugin/marketplace.json` — regenerated by `build-self`

**Out of scope:**
- Modifying any existing SKILL.md content (the checker validates the current boundary language; it does not correct it)
- Modifying `run-pack-evals.py` (the per-skill activation eval runner)
- Adding `eval_queries.json` or `evals.json` to individual skills
- Creating a CI workflow (report-only mode is the starting state; CI wiring is a follow-on tracked in `cross-pack-eval-ci-gate`)
- Any file outside the in-scope list above

## Testing Strategy

| AC | Mode | Mechanism |
|----|------|-----------|
| AC1 — Chain completeness | goal-based | `--gate --root .` reports all 5 chain skills found |
| AC2 — Phantom handoff detection | goal-based | Checker reports no phantom skill references (cross-pack refs exempted) |
| AC3 — Boundary guards present | goal-based | Checker reports guards found per adjacency map for all 5 chain skills |
| AC4 — Contract copies present | goal-based | Checker reports DEC copies found in all 4 packs |
| AC5 — Description within cap | goal-based | Checker reports all chain skill descriptions ≤1024 chars |
| AC6 — Gate mode passes on live repo | goal-based | `python3 tools/check-xd-chain.py --gate --root .` exits 0 |
| AC7 — Report-only default exits 0 | goal-based | `python3 tools/check-xd-chain.py --root .` exits 0 (no `--gate`) |
| AC8 — Gate rejects injected failures | goal-based | Self-test: `--gate` exits 1 on injected missing skill, phantom ref, missing guard, missing contract, long description |
| AC9 — Fixtures valid JSON | goal-based | `python3 -c "import json; json.load(open('packs/experience-design/.apm/evals/cross-pack-fixtures.json'))"` exits 0 |
| AC10 — Fixture coverage | goal-based | fixtures.json has ≥4 `golden_path`, ≥3 `multi_intent_routing`, ≥3 `boundary_violations`, ≥3 `weak_regression` entries |
| AC11 — Self-test passes | goal-based | `python3 tools/test-check-xd-chain.py` exits 0 |
| AC12 — Contract drift gate | goal-based | `python3 tools/check-contract-drift.py --root .` exits 0 |
| AC13 — How-to guide published | goal-based | `docs/guides/experience-design/how-to/run-cross-pack-eval.md` exists |
| AC14 — Version bump | goal-based | `pack.toml` and `plugin.json` both read `"1.6.0"` |
| AC15 — workspace.toml updated | goal-based | `spec/cross-pack-experience-eval` absent from queue, present in shipped |
| AC16 — test-all wired | goal-based | `test-check-xd-chain` appears in `tools/test-all.py` TESTS list |

## Assumptions

1. The five XD chain skills (design-token-taxonomy, design-system-foundations, information-architecture, copy-direction, design-review) are all present at 1.5.0 on main (confirmed).
2. The Digital Experience Contract copies exist in all four packs (confirmed — `check-contract-drift.py` passes on main).
3. MINOR version bump (1.5.0 → 1.6.0) is appropriate for adding new eval capability per RFC-0071 D9.
4. Python 3.8+ is available (stdlib only — the checker uses no third-party libraries; `re`, `pathlib`, `argparse`, `subprocess` are the only imports).
5. The fixture file format (JSON with top-level sections by fixture type) is unconstrained by existing schemas — this is a new artifact type.
6. `packs/experience-design/.apm/evals/` is source-only: `build_gate_chain.py build-self` treats any non-SKILL.md content under `.apm/` as unclassified and does not project it — confirmed by dry-run (exit 0, [info] unclassified for pack-level files).
7. All five chain skill descriptions are ≤1024 chars on main (confirmed by adversarial review: all ≤981 chars).
8. The adjacency map in the "Boundary guard adjacency map" section above is correct as of 1.5.0 (confirmed against actual frontmatter).

## Temptations declined

- Tempted to modify `run-pack-evals.py` to add cross-pack modes — declining; a standalone tool has clearer boundaries and does not risk breaking per-skill activation eval behavior.
- Tempted to add cross-pack routing queries to individual skill `eval_queries.json` files — declining; cross-pack routing tests belong in the cross-pack fixture, not per-skill evals whose runner only sees one pack at a time.
- Tempted to create a CI workflow in this PR — declining; M5 brief explicitly says all new evals start report-only.
- Tempted to require bidirectional backtick guards in all chain skill pairs — declining; `design-review`'s existing unquoted guard references are correct and present; a format change to SKILL.md content is out of scope.

## Deferred

- **CI workflow** (`cross-pack-eval-ci-gate`): Once calibration confirms the deterministic checks are stable, wire `check-xd-chain.py --gate` into a CI workflow. The `--gate` flag is the hook point. (shipped: cross-pack-eval-ci-gate)
- **LLM-judge rubric** (`cross-pack-eval-llm-judge`): The golden-path fixtures describe scenarios in structured form but carry no `evals.json`-style LLM judge rubric. (shipped: cross-pack-eval-llm-judge)

## Acceptance Criteria

- [x] **AC1** — `python3 tools/check-xd-chain.py --gate --root .` reports all 5 chain skills found.
- [x] **AC2** — `python3 tools/check-xd-chain.py --gate --root .` reports no phantom skill references (cross-pack references are correctly exempted).
- [x] **AC3** — `python3 tools/check-xd-chain.py --gate --root .` reports boundary guards present for all 5 chain skills per the adjacency map.
- [x] **AC4** — `python3 tools/check-xd-chain.py --gate --root .` reports Digital Experience Contract copies found in all 4 packs.
- [x] **AC5** — `python3 tools/check-xd-chain.py --gate --root .` reports all chain skill descriptions ≤1024 chars.
- [x] **AC6** — `python3 tools/check-xd-chain.py --gate --root .` exits 0 (all five checks pass against the current repo state).
- [x] **AC7** — `python3 tools/check-xd-chain.py --root .` (without `--gate`) exits 0.
- [x] **AC8** — `python3 tools/test-check-xd-chain.py` exits 0 and exercises `--gate` failure paths on injected fixtures.
- [x] **AC9** — `python3 -c "import json; json.load(open('packs/experience-design/.apm/evals/cross-pack-fixtures.json'))"` exits 0.
- [x] **AC10** — `cross-pack-fixtures.json` contains ≥4 `golden_path` entries, ≥3 `multi_intent_routing` entries, ≥3 `boundary_violations` entries, ≥3 `weak_regression` entries.
- [x] **AC11** — `python3 tools/test-check-xd-chain.py` exits 0.
- [x] **AC12** — `python3 tools/check-contract-drift.py --root .` exits 0.
- [x] **AC13** — `docs/guides/experience-design/how-to/run-cross-pack-eval.md` exists.
- [x] **AC14** — `packs/experience-design/pack.toml` version is `"1.6.0"` and `packs/experience-design/.claude-plugin/plugin.json` version is `"1.6.0"`.
- [x] **AC15** — `workspace.toml` has `"spec/cross-pack-experience-eval"` in `["ini-003".work].shipped` and not in `queue`.
- [x] **AC16** — `tools/test-all.py` TESTS list includes an entry for `test-check-xd-chain`.
