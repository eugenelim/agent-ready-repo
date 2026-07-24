# Plan: cross-pack-experience-eval

**Spec:** docs/specs/cross-pack-experience-eval/spec.md

## Tasks

### T1 — Create cross-pack-fixtures.json
**Depends on:** none
**Mode:** goal-based
**Done when:** `python3 -c "import json; json.load(open('packs/experience-design/.apm/evals/cross-pack-fixtures.json'))"` exits 0 and file has ≥4 golden_path, ≥3 multi_intent_routing, ≥3 boundary_violations, ≥3 weak_regression entries.

Create `packs/experience-design/.apm/evals/` directory and `cross-pack-fixtures.json` with structured scenario fixtures covering:
- 4 golden-path types: public marketing+docs, SaaS onboarding+workspace, internal dashboard, transactional service
- 3 multi-intent routing examples: audit-and-rebuild, full-stack-from-opportunity, unify-marketing-docs-onboarding
- 3 boundary violation cases: design-system-foundations doing IA's job, IA doing copy-direction's job, copy-direction doing design-review's job
- 3 weak regression fixtures: locally-polished-but-globally-weak, chain-ordering-violation, phantom-handoff

Tests: no stub (goal-based)

---

### T2 — Create check-xd-chain.py
**Depends on:** none
**Mode:** goal-based
**Done when:** `python3 tools/check-xd-chain.py --gate --root /tmp/xd-cpe` exits 0 and reports all five checks.

Create `tools/check-xd-chain.py` implementing five deterministic checks, stdlib only (no third-party libraries):
1. Chain completeness — all 5 chain skills exist at expected SKILL.md paths
2. Phantom-handoff — backtick-quoted skill names in `Do NOT use` guards resolve to existing skills (cross-pack references exempted)
3. Boundary guards — each chain skill's description references its required neighbors per the adjacency map in spec.md
4. Contract copies — Digital Experience Contract files exist in all 4 packs
5. Description length — each chain skill description ≤1024 chars

Report-only default (exit 0 always); `--gate` flag enables fail-closed mode (exit 1 on any failure).

Tests: no stub (goal-based)

---

### T3 — Create test-check-xd-chain.py
**Depends on:** T2
**Mode:** goal-based
**Done when:** `python3 tools/test-check-xd-chain.py` exits 0.

Create `tools/test-check-xd-chain.py` with tests:
- A: Real repo in report-only mode → exit 0
- B: Real repo in `--gate` mode → exit 0 (all checks pass)
- C: Injected missing chain skill → `--gate` exits 1
- D: Injected phantom skill reference → `--gate` exits 1
- E: Injected missing boundary guard → `--gate` exits 1
- F: Injected missing DEC contract copy → `--gate` exits 1
- G: Injected description over 1024 chars → `--gate` exits 1

Tests: no stub (goal-based)

---

### T4 — Create how-to guide
**Depends on:** T2
**Mode:** goal-based
**Done when:** `docs/guides/experience-design/how-to/run-cross-pack-eval.md` exists and covers: how to run the checker, how to interpret report-only output, and how to promote to a gate.

Tests: no stub (goal-based)

---

### T5 — Bump pack version to 1.6.0
**Depends on:** none
**Mode:** goal-based
**Done when:** `grep '"1.6.0"' packs/experience-design/pack.toml` and `grep '"1.6.0"' packs/experience-design/.claude-plugin/plugin.json` both exit 0.

Approach: Update `version = "1.5.0"` → `"1.6.0"` in `pack.toml` and `"version": "1.5.0"` → `"1.6.0"` in `.claude-plugin/plugin.json`.

Tests: no stub (goal-based)

---

### T6 — Wire test-check-xd-chain into test-all.py
**Depends on:** T3
**Mode:** goal-based
**Done when:** `grep "test-check-xd-chain" tools/test-all.py` exits 0.

Approach: Add `("test-check-xd-chain", [sys.executable, "tools/test-check-xd-chain.py"])` to the TESTS list in alphabetical order.

Tests: no stub (goal-based)

---

### T7 — Update workspace.toml
**Depends on:** T1, T2, T3, T4, T5, T6
**Mode:** goal-based
**Done when:** `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0 and `spec/cross-pack-experience-eval` is absent from `["ini-003".work].queue` and present in `["ini-003".work].shipped`.

Approach: Remove the `{path = "spec/cross-pack-experience-eval", needs = [...]}` block from queue and append `"spec/cross-pack-experience-eval"` to the shipped list. Keep the comment block above the removed entry (commented out, not deleted). Do NOT truncate the file — it is over 1350 lines.

Tests: no stub (goal-based)

---

### T8 — Run gates and build verification
**Depends on:** T1, T2, T3, T4, T5, T6, T7
**Mode:** goal-based
**Done when:**
- `python3 tools/check-xd-chain.py --gate --root .` exits 0
- `python3 tools/test-check-xd-chain.py` exits 0
- `python3 tools/check-contract-drift.py --root .` exits 0
- `python3 tools/build_gate_chain.py build-self --force --packs-dir packs` exits 0
- `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs` exits 0

Tests: no stub (goal-based)
