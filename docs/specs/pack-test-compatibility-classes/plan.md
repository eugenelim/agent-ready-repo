# Plan: Pack-test compatibility classes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0071 (pack = ownership and test-execution
  boundary); `guides/_shared/reference/catalogue-authoring-standards.md` § 4
  (the unconditional rule being revised) and its byte-identical scaffold
  projection; `tools/lint-pack-test-boundary.py`
  (`case_runners_keep_suites_isolated`, replaced; `case_every_suite_dir_has_a_
  runner`, preserved; `_covered` at 1244-1260, the destination resolver);
  `tools/test-lint-boundary-structural.py:599-624` and
  `tools/lint-boundary-golden.json` (both pin the current six-case output);
  `tools/pytest_collection_floor.py:79` (`actual = len(items)` — the floor is
  session-wide, so per-suite enforcement comes from single-suite invocation, not
  from the flag); `tools/test_local_ci_shared_test_deduplication.py`
  (opportunity-1 ownership). Named uncertainty: `--import-mode=importlib` node
  stability on Windows path syntax is unverified here — mitigated by keeping the
  mode class-scoped and asserting node IDs rather than assuming them.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`.

## Approach

Isolation stays the default. A small typed declaration table names the exact
sets of suites within one pack that have been *proved* to share an interpreter,
along with the pytest arguments that grouping requires. The pack-test-boundary
lint stops asserting "no invocation spans two suite directories" and starts
asserting "every invocation that spans two suite directories matches a declared
class exactly, and that class's mechanical safety invariants still hold against
the current tree."

Two derivations are kept separate, because they fail differently:

- **Test-module identity** — duplicate `test_*.py` basenames among a class's
  members. Fails loudly (`import file mismatch`, `rc=2`) in prepend mode, so it
  is self-announcing; the class must still declare how it is resolved.
- **Subject-module identity** — two same-named modules under
  `.apm/skills/*/scripts/` bound through `sys.path`. Fails *silently*: the
  second suite gets the first module and can still pass green. This is the
  higher-risk derivation and it is the one that gates class membership.

No runtime payload changes. No test file changes. No new dependency. No shared
execution framework.

## Baseline

Fetched `origin/main` = `939147d6902e8fab7e1ef3c4f12ef924deb1f34f`
(the prompt's stated `44189af4` is two commits behind; the two intervening
commits touch `tools/build_site.py` fence parsing only). Branch
`eugenelim/pytest-isolation`, worktree clean. `python3 tools/lint-pack-test-
boundary.py` is green at baseline: **6 cases, 61 destinations, 8 declared
unrun**.

### Scope of the count

The lint sees **61 destinations** across six runner files. This plan changes
**only the `Makefile`'s** pack-scoped invocations. Nine destinations are gated
solely by `build-check.yml` — `atlassian/confluence-crawler`,
`catalogue-curation/assimilate-primitive` and `-repo`,
`converters/file-to-markdown`, `markdown-to-docx`, `-pptx`, `-xlsx`,
`msg-to-markdown`, `credential-brokers/credential-setup` — and are untouched.
Eight more are `_NO_RUNNER`. Every table below is therefore labelled
**Makefile launches**, not "processes in the repository".

### Makefile pack-scoped pytest launches (derived, `Makefile:423-468`)

| Pack | Launches | Pack | Launches |
| --- | ---: | --- | ---: |
| `core` | 14 | `github` | 1 |
| `catalogue-curation` | 2 | `product-engineering` | 1 |
| `product-documentation` | 1 | `agent-skill-engineering` | 4 |
| `architect` | 4 | `linear` | 2 |
| `credential-brokers` | 1 | `converters` | 2 |
| `atlassian` | 5 | `desk-research` | 8 |
| | | **Total** | **45** |

**Derivation command (AC2).** Reproduces the 45 and the per-pack split:

```bash
sed -n '423,468p' Makefile \
  | grep -oE 'packs/[a-z-]+/tests' \
  | cut -d/ -f2 | sort | uniq -c | sort -rn
```

## Collision matrices (derived)

### Test-module basename collisions, within a pack

| Pack | Colliding basename | Suites holding it |
| --- | --- | ---: |
| `desk-research` | `test_project_knowledge_boundary.py` | **7** — `desk-research`, `-project-start`, `-project-check`, `-project-digest`, `-project-status`, `-project-synthesize`, `devils-advocate` |
| `core` | `test_project_knowledge_boundary.py` | 2 — `author-brief`, `new-spec` |
| `core` | `test_project_knowledge_handoff.py` | 2 — `work-loop`, `receive-brief` |
| `agent-skill-engineering` | `test_contract.py` | 2 — `author_or_update`, `review_or_optimize` |
| `converters` | `test_invocation_contract.py` | 2 gated (`markdown-to-html`, `mermaid-renderer`) + ungated |
| `atlassian` | 8 basenames | ungated suites only (`confluence-crawler`/`jira`) |
| `governance-extras` | `test_next_ordinal.py` | 2, both `_NO_RUNNER` |

The desk-research row is the reason the proposed class of six requires
`--import-mode=importlib`: in prepend mode a six-member group reports
**5 collection errors**, not one.

This matrix is restated here for review only. **T1 emits it from the derivation
helpers**; the prose copy is not the source of truth (AC1).

### Subject-module basename collisions under `.apm/skills/*/scripts/`

Intra-pack pairs are the only ones that can threaten a class:
`catalogue-curation` (`write_jail.py`, `ssrf_check.py`), `atlassian`
(`_client.py` ×4, `setup_sso.py`, `_sso_config.py`, `processor.py`,
`intake_adapter.py`, `notes.py`, `render.py`), `converters` (`render.py` ×3,
`safe_io.py`, `convert.py`, `contract.py`), `core` (`_statelock.py`),
`governance-extras` (`next-ordinal.py`). None of these pairs falls inside a
proposed class.

### Import-style classification of gated pack tests

| Style | Files |
| --- | --- |
| Explicit `spec_from_file_location` under a qualified name | 42 |
| `sys.path` mutation + bare sibling import | 24 (10 of them `conftest.py`) |
| Stdlib/installed imports only | remainder |
| Dynamic `importlib.import_module()` by string, or `runpy` | none |
| Name argument not a literal *at the call expression* | 1 — `architect-assess/test_profile_repo.py:23` passes a helper parameter; the literal `"architect_profile_repo_test"` is at the single call site, line 35. AC12's constant-propagation rule covers exactly this shape. |

There are 11 `conftest.py` files under `packs/*/tests/`, 10 of which mutate
`sys.path`. There is **no** `conftest.py` at the repository root, at `packs/`,
at `packs/<pack>/`, or at `packs/<pack>/tests/`, so a member's conftest exposure
is its own directory's file and nothing above it. All 11 sit in suites this plan
leaves isolated, and **none of the 18 member directories of the five proposed
classes contains one** — verified per directory.

## Import-identity characterization results

### A. Test-module identity

`--import-mode=importlib` was evaluated against the two real colliding gated
groups rather than a synthetic fixture. Both collected the full isolated union
with byte-identical node IDs and passed forward and reverse:

| Class | Isolated union | Grouped (importlib) | Node IDs | fwd | rev |
| --- | ---: | ---: | --- | --- | --- |
| `converters-invocation-contract` | 12 | 12 | identical | rc=0 | rc=0 |
| `desk-research-content` | 17 | 17 | identical | rc=0 | rc=0 |

It is **not** made the repository-wide default; it is required per class.

A second mechanism was found already in the tree: `agent-skill-engineering`'s
skill test directories carry `__init__.py` and underscored names
(`author_or_update`, `review_or_optimize`), with no `__init__.py` at
`tests/skills/`. Their duplicate `test_contract.py` therefore resolves to
distinct dotted module names under **default prepend mode**. No flag needed,
and no `__init__.py` is added anywhere by this plan.

### B. Subject-module identity

Derived loader names in the proposed members — all distinct, all resolvable:

- `architect`: `architect_profile_repo_test` (via a same-module helper; see the
  classification note above)
- `linear`: `linear_script`, `linear_intake_adapter`
- `agent-skill-engineering`, `desk-research` (6), `converters` (2): none — no
  member imports a skill-local subject at all.

No proposed class needs a new loader, so **Wave C ships no subject-import
migration**. The unsafe positional pattern is confined to suites this plan
leaves isolated.

### C. Placement of test support

Not needed. Because no proposed class requires a loader, no helper is
introduced — not pack-local, not repository-level, not a plugin.

## Agent-skill-engineering pilot result

Required first candidate. Confirmed against source: four processes; both skill
suites hold `test_contract.py`; every import in all four suites is stdlib or
installed (`pytest`, `yaml`); zero `sys.path` mutation, zero
`spec_from_file_location`, zero `conftest.py`, zero skill-local subject import.

| Experiment | Result |
| --- | --- |
| Each suite independently | 32 + 6 + 17 + 23 = 78 collected, all pass |
| Grouped collection, **prepend** mode | 78 collected — no flag needed |
| Node-ID set, isolated union vs grouped | **identical** (`diff` empty) |
| Grouped execution, forward | 78 passed, rc=0 |
| Reverse member order | 78 passed, rc=0 |
| Permutation (skills first) | 78 passed, rc=0 |
| Repeated fresh processes (3×) | stable |
| Duplicate-basename control | resolved by existing `__init__.py` |

**Verdict: the pilot is confirmed.** Four launches collapse to one, with no
import-mode flag and no source change to the pack.

## Proposed compatibility classes

Five classes, all intra-pack, all directory-scoped, all conftest-free.

| Class ID | Pack | Members | Import mode | Basename resolution | Subject imports | Before → after |
| --- | --- | --- | --- | --- | --- | ---: |
| `agent-skill-engineering-contract` | `agent-skill-engineering` | `tests/pack/`, `tests/integration/`, `tests/skills/author_or_update/`, `tests/skills/review_or_optimize/` | prepend | `__init__.py` packages | none | 4 → 1 |
| `architect-contract` | `architect` | `tests/pack/`, `tests/skills/architect-assess/`, `tests/skills/architect-design/`, `tests/skills/architect-review/` | prepend | no collision | 1 resolvable qualified name | 4 → 1 |
| `desk-research-content` | `desk-research` | `tests/pack/`, `tests/skills/desk-research-project-check/`, `…-digest/`, `…-status/`, `…-synthesize/`, `tests/skills/devils-advocate/` | **importlib** | mode | none | 6 → 1 |
| `converters-invocation-contract` | `converters` | `tests/skills/markdown-to-html/`, `tests/skills/mermaid-renderer/` | **importlib** | mode | none | 2 → 1 |
| `linear-intake` | `linear` | `tests/skills/linear/`, `tests/skills/linear-brief-intake/` | prepend | no collision | 2 literal qualified names | 2 → 1 |

### Characterization results per class

Exit codes checked at every step.

| Class | Isolated union | Grouped | Node IDs | fwd | rev |
| --- | ---: | ---: | --- | --- | --- |
| `agent-skill-engineering-contract` | 78 | 78 | identical | rc=0 | rc=0 |
| `architect-contract` | 71 | 71 | identical | rc=0 (+33 subtests) | rc=0 |
| `desk-research-content` | 17 | 17 | identical | rc=0 | rc=0 |
| `converters-invocation-contract` | 12 | 12 | identical | rc=0 | rc=0 |
| `linear-intake` | 32 | 32 | identical | rc=0 | rc=0 |

### Measured wall time (3 runs each, median)

| Class | Isolated (n) | Grouped (1) | Δ |
| --- | --- | --- | ---: |
| `agent-skill-engineering-contract` | 13.07 s (4) | 5.23 s | −7.8 s |
| `architect-contract` | 14.42 s (4) | 7.21 s | −7.2 s |
| `desk-research-content` | 18.45 s (6) | 2.91 s | −15.5 s |
| `converters-invocation-contract` | 9.05 s (2) | 5.44 s | −3.6 s |
| `linear-intake` | 11.01 s (2) | 5.90 s | −5.1 s |
| **Total** | **66.0 s (18)** | **26.7 s (5)** | **−39.3 s** |

Run-to-run spread is wide (13.07/12.80/18.88 for the pilot's isolated leg)
because the machine hosts several worktrees; magnitude carries roughly ±30 %
uncertainty, direction is robust across every repetition.

### Measured peak resident memory (`/usr/bin/time -l`, median of 3)

Isolated figure is the **maximum across the class's member processes** — the
peak the machine actually sees, since they run sequentially. AC27 allows +8 MiB.

| Class | Isolated peak (max of n) | Grouped peak | Δ | Within tolerance |
| --- | --- | --- | ---: | --- |
| `agent-skill-engineering-contract` | 51 MiB | 51 MiB | 0 | yes |
| `architect-contract` | 53 MiB | 56 MiB | +3 MiB | yes |
| `desk-research-content` | 49 MiB | 49 MiB | 0 | yes |
| `converters-invocation-contract` | 52 MiB | 52 MiB | 0 | yes |
| `linear-intake` | 70 MiB | 70 MiB | 0 | yes |

±1–3 MiB is inside this measurement's noise, which is why AC27 states a
tolerance rather than an absolute.

### Whole-surface equivalence, pre-validated

All 45 current invocations were extracted verbatim from `Makefile:423-468`
(with the `$(1)`/`$(2)` slots empty, as standalone `make test` passes them) and
run under `--collect-only`; the 32 proposed invocations were run the same way.

| Route | Invocations | Node IDs | Unique |
| --- | ---: | ---: | ---: |
| Current | 45 | 1958 | 1958 |
| Proposed | 32 | 1958 | 1958 |

`diff` of the two sorted unique sets is **empty**. Raw equals unique on both
sides, which independently proves no suite is collected twice in either route.
Direct evidence for AC4 and AC15 ahead of implementation.

The composed route was checked the same way with `$(1)`/`$(2)` populated: 1825
unique node IDs, **133 fewer**, and the removed set resolves to exactly the
three pack-side opportunity-1 files. Nothing else removed, nothing added
(AC5).

### Before → after Makefile launches by pack

| Pack | Before | After | What remains, and why |
| --- | ---: | ---: | --- |
| `core` | 14 | 14 | retained — see below |
| `catalogue-curation` | 2 | 2 | retained — `sys.path` mutation |
| `product-documentation` | 1 | 1 | already a single launch |
| `architect` | 4 | **1** | class |
| `credential-brokers` | 1 | 1 | already a single launch |
| `atlassian` | 5 | 5 | retained — `conftest.py` mutates `sys.path` |
| `github` | 1 | 1 | already a single launch |
| `product-engineering` | 1 | 1 | already a single launch |
| `agent-skill-engineering` | 4 | **1** | pilot class |
| `linear` | 2 | **1** | class |
| `converters` | 2 | **1** | class |
| `desk-research` | 8 | **3** | class of 6 + two floor-bearing suites isolated |
| **Total** | **45** | **32** | **−13 Makefile pytest launches** |

This reduces *sequential* interpreter launches — less startup, less repeated
collection, less process churn. It is not a concurrency change; nothing runs in
parallel that did not before.

### Exact commands, before and after

**Load-bearing rule: a grouped command lists its members explicitly and never
names an ancestor directory.** `pytest packs/agent-skill-engineering/tests/`
would collect a *future* suite directory too, silently enlarging the class and
breaking AC8. The lint rejects an ancestor-shaped broad invocation even when
today's covered destinations match a class exactly.

```make
# agent-skill-engineering — before (Makefile:453-456, four lines) → after
$(PYTHON) -m pytest \
	packs/agent-skill-engineering/tests/pack/ \
	packs/agent-skill-engineering/tests/integration/ \
	packs/agent-skill-engineering/tests/skills/author_or_update/ \
	packs/agent-skill-engineering/tests/skills/review_or_optimize/ -q

# architect — before (Makefile:440-443, four lines) → after
$(PYTHON) -m pytest \
	packs/architect/tests/pack/ \
	packs/architect/tests/skills/architect-assess/ \
	packs/architect/tests/skills/architect-design/ \
	packs/architect/tests/skills/architect-review/ -q

# linear — before (Makefile:457-458) → after
$(PYTHON) -m pytest \
	packs/linear/tests/skills/linear/ \
	packs/linear/tests/skills/linear-brief-intake/ -q

# converters — before (Makefile:459-460) → after
$(PYTHON) -m pytest --import-mode=importlib \
	packs/converters/tests/skills/markdown-to-html/ \
	packs/converters/tests/skills/mermaid-renderer/ -q

# desk-research — before (Makefile:461-468, eight lines) → after (three).
# The two floor-bearing lines are unchanged, byte for byte.
$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research/ -q -p tools.pytest_collection_floor --minimum-collected=9 --collection-floor-suite=packs/desk-research/tests/skills/desk-research/
$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-start/ -q -p tools.pytest_collection_floor --minimum-collected=7 --collection-floor-suite=packs/desk-research/tests/skills/desk-research-project-start/
$(PYTHON) -m pytest --import-mode=importlib \
	packs/desk-research/tests/pack/ \
	packs/desk-research/tests/skills/desk-research-project-check/ \
	packs/desk-research/tests/skills/desk-research-project-digest/ \
	packs/desk-research/tests/skills/desk-research-project-status/ \
	packs/desk-research/tests/skills/desk-research-project-synthesize/ \
	packs/desk-research/tests/skills/devils-advocate/ -q
```

`core`, `catalogue-curation`, `product-documentation`, `credential-brokers`,
`atlassian`, `github`, and `product-engineering` lines are **byte-identical** to
today.

### Files expected to change

`Makefile` (pack-test block + the comment at 396-403 + a new tools-test batch
entry); `tools/lint-pack-test-boundary.py`; `tools/pack_test_compatibility.py`
(new); `tools/test_pack_test_compatibility.py` (new);
`tools/test_pack_test_class_characterization.py` (new);
`tools/test-lint-boundary-structural.py`; `tools/lint-boundary-golden.json`
(regenerated); `tools/test-lint-pack-test-boundary.py`;
`.github/workflows/docs.yml` (path triggers);
`.github/workflows/build-check.yml` and
`.github/workflows/catalogue-tooling-ci-gates.yml` (one stale comment each);
`guides/_shared/reference/catalogue-authoring-standards.md` **and its scaffold
projection**; one new `docs/adr/` file; this spec and plan.

### Files that must remain byte-identical

Everything under `packs/*/.apm/`; **every file under `packs/*/tests/`** — no
test is edited, renamed, or moved; `tools/pytest_collection_floor.py`;
`tools/test_local_ci_shared_test_deduplication.py`;
`packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py`;
`pyproject.toml`; the bodies of `docs/specs/pack-test-boundary/`,
`docs/specs/pack-test-boundary-remaining-packs/`, RFC-0082, ADR-0071.

## Retained isolation boundaries and their reasons

| Boundary | Reason |
| --- | --- |
| `core/work-loop`, `core/receive-brief` | Opportunity-1 ownership: these two carry the `$(1)`/`$(2)` ignore arguments that exclude **three** pack-side files in `test-after-build-check` (the other two owned files are `tools/test_workspace_status*.py`, excluded by the empty `$(3)` slot). Grouping either makes that exclusion strictly more complex for no required benefit. They also collide on `test_project_knowledge_handoff.py`. |
| `core/author-brief`, `core/new-spec` | Collide on `test_project_knowledge_boundary.py` (verified: `rc=2`, `import file mismatch`). Resolvable by `importlib`, but see the Ask-first item below. |
| `core/work-intake` | Module-level `sys.path` mutation. |
| `core/hooks`, `pack`, `adapt-to-project`, `bug-fix`, `capture-work`, `close-work`, `contract-acquisition`, `project-knowledge`, `workspace-status` | **Characterized in full and rejected on AC27.** See *Core-content: a measured no-go* below. Correctness was clean; peak memory exceeded the tolerance. |
| `catalogue-curation` — both | `compile-okf`'s tests perform a module-level, never-popped `sys.path.insert(0, …)` in three files, then bare `import okf_compiler`. Grouped it passes today (156 tests, node IDs identical, fwd/rev green) but it fails this spec's own AC14. **Largest declined win: 19.62 s → 10.77 s, ≈ −8.8 s for one launch.** Carried as a deferred option below. |
| `atlassian` — all five | `packs/atlassian/tests/skills/jira/conftest.py:17` performs an unpopped `sys.path.insert(0, .apm/skills/jira/scripts)` and pytest **does** load it for the file-scoped invocation `jira/test_intake_policy.py` (proven with `--trace-config`). A grouped process would run with `jira/scripts` at `sys.path[0]`, where `_client.py`, `_sso_config.py`, and `setup_sso.py` live — so a future bare import in `jira-brief-intake` would silently bind jira's copy. Fails AC14. Dropping this candidate also removes file-scoped membership from the design entirely. |
| `desk-research/desk-research` (floor 9), `desk-research-project-start` (floor 7) | The floor plugin counts `len(items)` **session-wide**; `--collection-floor-suite` is only a display label. Per-suite enforcement therefore requires the suite be the sole target of its invocation. Grouping would silently convert two exact floors into one aggregate. |
| `product-documentation`, `credential-brokers`, `github`, `product-engineering` | Already a single Makefile launch each. |
| All `_NO_RUNNER` suites and the nine build-check-only destinations | Out of scope; unchanged. |

### Core-content: a measured no-go

A nine-member class over `core`'s unobstructed suites (`hooks`, `pack`,
`adapt-to-project`, `bug-fix`, `capture-work`, `close-work`,
`contract-acquisition`, `project-knowledge`, `workspace-status` — excluding
`work-loop`, `receive-brief`, `author-brief`, `new-spec`, `work-intake`) was
characterized in full at the plan checkpoint, because none of the usual
obstacles applied: zero `sys.path` mutations, zero `conftest.py`, and no
opportunity-1 exposure.

**Correctness was clean.**

| Check | Result |
| --- | --- |
| Node-ID set, isolated vs grouped | 523 = 523, identical |
| Grouped forward, 3 runs | 522 passed, 1 skipped, `rc=0` each time |
| Grouped reverse member order | 522 passed, 1 skipped, `rc=0` |
| Isolated, 3 runs | 522 passed, 1 skipped, `rc=0` each time |
| Skip disposition | 1 skipped on both sides |

**Wall time was a win inside heavy noise.** Isolated 248.2 / 283.1 / 262.1 s
(median 262.1); grouped 277.2 / 215.5 / 228.7 s (median 228.7) — nominally
−33.4 s (−13 %), but the ranges overlap and grouped's worst run is slower than
isolated's median.

**Peak memory failed AC27.** Isolated maximum 222 MiB (`project-knowledge`);
grouped 239 MiB; **delta +17 MiB against a +8 MiB tolerance.**

**Decision: rejected**, by owner decision at the checkpoint, on the threshold as
written. The tolerance was set before the measurement and is not being widened
to fit the result — an absolute MiB figure arguably scales badly from a 50 MiB
class to a 222 MiB one, but changing a gate after seeing what it caught is the
move that makes gates meaningless.

The structural reason core behaves unlike the shipped classes is now measured
rather than assumed: at ~0.5 s per test these suites are dominated by real work
(subprocess and filesystem), not interpreter startup, so removing eight
launches was never going to buy much. That is the honest boundary of this
initiative's benefit — it pays where startup and collection dominate, and not
elsewhere.

### Deferred option — a `catalogue-curation` Tier 3 migration

Offered at the checkpoint because it is the largest declined win and the only
genuine Tier 3 candidate in the tree.

- **Scope:** three test files (`test_apply.py`, `test_parser.py`,
  `test_render.py`) replace `sys.path.insert(0, SCRIPT_ROOT)` +
  `from okf_compiler import …` with one explicit load under
  `catalogue_curation_compile_okf_okf_compiler`.
- **Tractable because:** `okf_compiler.py` imports no sibling — only stdlib and
  `yaml` — so there is no synthetic package namespace to build. The runtime CLI
  `compile_okf.py` keeps its own sibling import and is exercised through
  `subprocess`, so `.apm/` stays byte-identical.
- **Still real work:** the `from … import` list is long, three files change, and
  `test_cli.py`'s `from test_apply import _make_catalogue` must keep resolving
  (it does — the class would use prepend mode).
- **Required red control:** add a second `okf_compiler`-named module in a
  temporary sibling skill tree and show the suite binds the wrong one.
- **Payoff:** −1 launch, ≈ −8.8 s. Total would become 31.

**Recommendation: decline for this spec.** It edits test files this plan
otherwise leaves byte-identical, and buys one launch.

## Constraints

- No `.apm/` byte and no `packs/*/tests/**` byte may change.
- No new dependency; no pytest plugin; no shared execution framework.
- `--import-mode=importlib` stays class-scoped.
- Both floor-bearing suites keep their own single-suite invocation.
- `tools/test_local_ci_shared_test_deduplication.py` must pass **unmodified**.
- **Workflow edits are permitted and required**, narrowly: `docs.yml` path
  triggers (so the new gates run), and one stale comment each in
  `build-check.yml:562` and `catalogue-tooling-ci-gates.yml:141`. No job, step,
  or command semantics change.

## Construction tests

- Parse the real `Makefile` and assert every multi-destination invocation maps
  to exactly one declared class with matching required flags.
- Assert the destinations named across all runners still cover every suite
  directory not in `_NO_RUNNER`.
- Assert no suite directory appears twice within one route.
- Assert the declared class set equals the set of classes exercised.
- Assert a pytest invocation with non-resolvable path arguments is a finding
  (AC31), with the `catalogue-tooling-ci-gates.yml` `for`-loop recorded as a
  declared exception.

## Design (LLD)

### Design decisions

**Declaration design — Option A (typed table in a linter-owned companion
module), selected.**

- *Option A — Make groups + linter-owned typed declarations.* **Selected.**
  Runner commands stay explicit and greppable; the declaration lives in a new
  `tools/pack_test_compatibility.py` as typed data with the evidence in each
  entry's fields. No new file format, no parser, no dependency, and `mypy`
  already checks it.
- *Option B — checked-in TOML registry.* Rejected: separates the declaration
  from the validator that gives it meaning and adds a parse-and-schema surface
  for no gain.
- *Option C — derive safety automatically from the current tree.* Rejected: a
  derivation saying "no collision exists today" grants permission that silently
  broadens. Derivation is kept as the *checking* half, never the *granting*
  half.

A companion module rather than the lint file itself keeps that 1670-line file
from growing a second concern and lets tests import the declarations without
importing the lint.

**Test-module identity mechanism.** Per class: existing `__init__.py` package
disambiguation (preferred — costs nothing), `--import-mode=importlib`, or "no
collision". The class declares which; the lint re-derives that the declared
resolution covers the current basenames.

**Subject-module identity mechanism.** No new mechanism. Every proposed class
either imports no skill-local subject or already uses `spec_from_file_location`
with a resolvable, distinct, qualified name. The lint enforces that property
rather than introducing a loader.

### Data & schema

```python
@dataclass(frozen=True)
class CompatibilityClass:
    identifier: str            # stable, unique, kebab-case
    pack: str                  # exactly one pack
    members: tuple[str, ...]   # exact directory paths, >=2, repo-relative
    import_mode: str           # "prepend" | "importlib"
    basename_resolution: str   # "none" | "packages" | "import-mode"
    subject_imports: str       # "none" | "explicit-qualified"
    rationale: str
```

Entries are sorted by `identifier` for display and verification.

### Interfaces & contracts

`tools/pack_test_compatibility.py` exposes `CLASSES`,
`classes_by_identifier()`, and pure derivation helpers (`import_set_for`,
`test_basenames_for`, `subject_loader_names_for`, `path_mutations_in`). It
imports nothing from the lint, so the dependency runs one way.

`import_set_for(member)` — the definition AC13 turns on — returns: the member's
collected test modules; every `conftest.py` from rootdir down to and including
the member's own directory (for a file member, that is the file's directory);
and modules imported by those. Fixture trees pytest never imports are excluded.

### Component / module decomposition

- `tools/pack_test_compatibility.py` — declarations + derivation (new).
- `tools/lint-pack-test-boundary.py` — replaces
  `case_runners_keep_suites_isolated` with
  `case_runners_use_approved_compatibility_classes`; adds
  `case_compatibility_classes_are_well_formed` and
  `case_class_members_keep_distinct_module_identity`. `CHECKS` grows 6 → 8.
- `tools/test_pack_test_compatibility.py` — contract and mutation tests (new).
- `tools/test_pack_test_class_characterization.py` — node-ID, ordering, and
  failure-injection characterization (new).

### Behavior & rules

`case_runners_use_approved_compatibility_classes` fails when an invocation
spans packs; covers ≥2 destinations with no declared class; matches a class
partially; is ancestor-shaped; or omits a required flag.

`case_compatibility_classes_are_well_formed` fails on a member outside the
declared pack; a member that does not exist; a suite in two classes; a class
with <2 members; a class no runner exercises.

`case_class_members_keep_distinct_module_identity` fails on a duplicate test
basename not covered by the declared resolution; a duplicate or unresolvable
`spec_from_file_location` name; any `sys.path` mutation in the member's import
set (including its `conftest.py`); and — for an `importlib` class — a bare
import of a sibling test module.

That last invariant comes from a real pattern:
`catalogue-curation/compile-okf/test_cli.py` opens with
`from test_apply import _make_catalogue`, which resolves only because prepend
mode puts the suite directory on `sys.path`. No proposed `importlib` class
contains such an import, but the invariant must be mechanical.

Every check fails closed: a parse error, an unreadable runner, or an
un-analyzable import form is a finding, never a skip.

### Failure, edge cases & resilience

- A missing runner file already produces one finding per consumer; that is
  preserved as the consumer count grows 2 → 3.
- `--import-mode=importlib` must appear literally on the grouped command; a
  class declaring it whose runner omits it fails.
- The `catalogue-tooling-ci-gates.yml` `for`-loop passes `"$d"`, which yields no
  static path token. The current rule never saw it. AC31 makes that shape a
  finding and records this one instance as a declared exception with its reason.

### Quality attributes (NFRs)

Wall time is the point; AC27 forbids a regression and bounds memory at +8 MiB
with a stated method.

### Dependencies & integration

None added. `tools/pack_test_compatibility.py` uses `ast`, `dataclasses`, and
`pathlib` only.

## Tasks

### T1: The compatibility model is declared, validated, and self-describing

**Depends on:** none
**Touches:** `tools/pack_test_compatibility.py`,
`tools/test_pack_test_compatibility.py`

**Tests (red first):**
- A well-formed class is accepted; a class with <2 members, a non-existent
  member, a member outside its pack, or a suite in two classes each fails
  (AC7, AC10).
- Declarations are returned in deterministic identifier order.
- The derivation helpers **emit** the two collision matrices; a hand-written
  matrix is not consulted (AC1).
- The launch-count derivation command reproduces 45 (AC2).

**Approach:** land the dataclass, an empty-but-typed `CLASSES`, the validator,
and the derivation helpers. No runner changes yet.

**Done when:** the emitted matrices match the tree, and each failure mode has a
red control that goes green.

### T2: Import-safety derivation fails closed on unsafe members

**Depends on:** T1
**Touches:** `tools/pack_test_compatibility.py`,
`tools/test_pack_test_compatibility.py`

**Tests (red first):**
- `import_set_for` includes the member's own-directory `conftest.py` for both a
  directory member and a file member, and excludes a non-imported `testdata/`
  tree (AC13).
- Duplicate basenames with `basename_resolution: none` fail;
  `packages` is accepted only when every colliding directory has `__init__.py`
  and the shared parent does not; `import-mode` only when `import_mode` is
  `importlib` (AC11).
- Two members sharing a `spec_from_file_location` literal fail (AC12).
- A name argument resolvable by intraprocedural constant propagation through a
  same-module helper is **accepted**; one that is not resolvable fails (AC12) —
  the `architect-assess` shape is the positive control.
- `sys.path.insert`/`append` anywhere in the import set fails, including in
  `conftest.py` and a non-`test_*` helper (AC14).
- In an `importlib` class, a bare sibling test-module import fails (AC14).
- An unparseable file produces a finding, not a skip.

**Approach:** AST derivation. Mutation proof per invariant: inject the unsafe
form into a temporary copy, assert red, restore byte-identically.

**Done when:** every invariant is red with its mutation and green without.

### T3: The lint enforces classes instead of blanket isolation

**Depends on:** T2
**Touches:** `tools/lint-pack-test-boundary.py`,
`tools/test-lint-pack-test-boundary.py`,
`tools/test-lint-boundary-structural.py`, `tools/lint-boundary-golden.json`

**Tests (red first):**
- Undeclared broad invocation, extra path, missing member, missing required
  flag, ancestor-shaped invocation, unused class — each fails (AC8, AC9, AC10).
- A new suite directory stays isolated (AC8).
- `every-suite-dir-has-a-runner` keeps fail-closed, non-vacuous behavior and no
  `_NO_RUNNER` entry becomes self-contradictory (AC3).
- A runner-parse failure suppresses no finding.
- A non-statically-resolvable pytest path argument is a finding, with the
  `catalogue-tooling-ci-gates.yml` loop as the declared exception (AC31).

**Approach:** replace `case_runners_keep_suites_isolated`; add the two new
checks. `CLASSES` is still empty here, so the lint must be green on the
**unchanged** `Makefile`. Note the honest limit of that proof: the current rule
reports `0 multi-directory invocation(s) checked`, so "green before" is weak
evidence — the strength comes from T3's own red controls, not from the
unchanged run.

`tools/test-lint-boundary-structural.py:599-624` pins `"passed (6 cases)."`,
`"1 of 6 checks"`, and `"2 of 6 checks"`; `tools/lint-boundary-golden.json`
base64-pins the `runner-spans-two-suites` stderr. Both must be updated and the
golden regenerated. Neither is run by `make test`; run all three scripts
directly.

**Done when:** `python3 tools/lint-pack-test-boundary.py` is green with no
runner change, and `tools/test-lint-pack-test-boundary.py`,
`tools/test-lint-boundary-structural.py`, and `tools/test-lint-boundary-
golden.py` all pass.

### T4: The new gates actually run

**Depends on:** T3
**Touches:** `Makefile`, `.github/workflows/docs.yml`

**Tests:**
- `make test` executes both new test modules (assert by name in the recipe, and
  by a deliberate failure showing up).
- `docs.yml`'s path filter includes `tools/pack_test_compatibility.py` and both
  new test files, so editing `CLASSES` alone re-triggers the boundary lint
  (AC32).

**Approach:** add both files to the `Makefile`'s explicit tools-test batch at
`Makefile:490-504`; add the three paths to `docs.yml`'s trigger list. Nothing
globs `tools/test_*.py`, so an un-wired test file is dead — this task exists
because that failure is silent.

**Done when:** removing an assertion from either new test file reddens
`make test`.

### T5: The pilot class ships

**Depends on:** T4
**Touches:** `tools/pack_test_compatibility.py`, `Makefile`,
`tools/test_pack_test_class_characterization.py`

**Tests (red first):** isolated node-ID union equals grouped (AC15); skips and
xfails equal (AC16); forward, reverse, and one permutation pass (AC17); a
failure injected into each of the four members fails the grouped run and names
that member's path (AC18); a collection error stays distinguishable from a test
failure (AC19).

**Approach:** declare `agent-skill-engineering-contract`; replace the four
`Makefile` lines with one. Do not rename either `test_contract.py`.

**Done when:** the leg is one line, the lint is green, characterization passes.

### T6: The four additional approved classes ship

**Depends on:** T5
**Touches:** `tools/pack_test_compatibility.py`, `Makefile`,
`tools/test_pack_test_class_characterization.py`

**Tests:** the same five per class, parameterized over every declared class so
a future class inherits the suite automatically.

**Approach:** one commit per class — `architect-contract`, `linear-intake`,
then the two `importlib` classes. If a class fails, restore its previous
`Makefile` lines, record the evidence here, continue with the rest.

**Done when:** all five classes are declared, lint green, parameterized
characterization green for every class.

### T7: Opportunity-1, the floors, and the untouched surfaces are proven intact

**Depends on:** T6
**Touches:** none expected — a diff here is a defect

**Tests:**
- `tools/test_local_ci_shared_test_deduplication.py` passes unmodified (AC5).
- Both floor-bearing suites are still the sole target of their invocations, and
  a mutation that groups one of them into a class reddens (AC6).
- Standalone vs composed node-ID sets differ by exactly the three pack-side
  files (AC4, AC5).
- `git diff --stat -- 'packs/*/.apm' 'packs/*/tests'` is empty (AC21).
- rootdir and configfile identical isolated vs grouped (AC20).
- The four pack-boundary checks are behaviorally unchanged (AC22).
- `self_host_windows.py` and `tools/`-scope invocations unchanged (AC23, AC24).
- Lease/run-slot files unchanged (AC25).
- The measurement commands are re-run and reported with uncertainty (AC2,
  AC26, AC27).

**Done when:** every listed command produces the stated result.

### T8: The living documentation states the new rule

**Depends on:** T7
**Touches:** `guides/_shared/reference/catalogue-authoring-standards.md` **and**
`packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/
reference/catalogue-authoring-standards.md`; `docs/adr/<next>-*.md`;
`tools/lint-pack-test-boundary.py` docstring; `Makefile:396-403`;
`.github/workflows/build-check.yml:562`;
`.github/workflows/catalogue-tooling-ci-gates.yml:141`

**Tests:** `tools/test_guide_authoring_standard.py` and
`tools/test_scaffold_projection.py` green; the ADR passes its lint; `git diff`
touches no frozen body (AC28); `git status --short` clean (AC29).

**Approach:** rewrite § 4's *One test process per skill* as default isolation
plus the class exception, keeping the two-identity distinction and adding that
`importlib` mode does not solve subject identity. Update the normative summary.
Regenerate the projection with
`python3 tools/catalogue/sync_authoring_scaffold.py --write`. Write the ADR with
the measured before/after. Correct the `Makefile` comment and the two workflow
comments that still assert the unconditional rule.

**Done when:** no living document states the unconditional rule and no
projection drift remains.

## Rollout

Each wave is a separate commit and independently revertible:

- **Wave A** = T1–T4. Reverting restores the blanket rule; no runner grouped.
- **Wave B** = T5. Reverting restores four `Makefile` lines.
- **Wave C** = *empty by evidence* — no subject-import migration is required.
- **Wave D** = T6, one commit per class; any single class reverts alone.
- **Wave E** = T7–T8, proof and documentation.

**No-go path (AC30).** If the pilot were disproved at T5, Wave A is reverted in
full — `tools/pack_test_compatibility.py`, both new test modules, the lint
changes, the `Makefile` batch entry, and the `docs.yml` triggers — leaving no
unused infrastructure, and this plan records the disproof.

## Risks

| Risk | Mitigation |
| --- | --- |
| A class passes today and breaks when a file is added | The lint re-derives basename and subject-identity safety from source every run; the declaration alone is never trusted. |
| `--import-mode=importlib` changes node IDs on Windows | Mode is class-scoped; node IDs are asserted, not assumed. Neither `importlib` class has a `conftest.py` or a cross-test import. Windows execution is a stated limitation. |
| A grouped class hides an order-dependent state leak | Forward, reverse, and permuted runs plus repeated fresh processes, per class. |
| Fewer launches trade wall time for memory | AC27 bounds both, with a stated method and tolerance. |
| The declaration grows into an execution framework | The module holds data and pure derivation helpers only, owned by the lint. |
| A new gate silently never runs | T4 exists solely for this, and proves it by making a deliberate failure surface. |

**Stated limitation.** Windows behavior is verified by construction (argv shape,
runner-form parsing) but not executed — this worktree is macOS. No grouped
command introduces a shell construct, and the Windows runner is unmodified.

## Changelog

- **Rev 3 (plan checkpoint decisions).** Owner decisions recorded: core
  characterized in full and **rejected on AC27** (+17 MiB against a +8 MiB
  tolerance) despite clean correctness and a nominal −13 % wall time — see
  *Core-content: a measured no-go*; the `catalogue-curation` Tier 3 migration
  **declined**, keeping `packs/*/tests/**` byte-identical; the narrow workflow
  edits **approved** (path triggers plus two stale comments). AC12 corrected
  from name-uniqueness to **name-maps-to-one-path**: `workspace_status_engine`
  is loaded under one literal by two core suites but resolves to the same file,
  which the old wording would have failed for no reason. Final shape: five
  classes, 45 → 32.
- **Rev 2 (post adversarial review).** Dropped `atlassian-intake-policy`:
  `jira/conftest.py` performs an unpopped `sys.path.insert` and pytest loads it
  for the file-scoped member, so the class failed this spec's own AC14. That
  also removes file-scoped membership from the design, and with it the
  destination-resolution ambiguity against `_NO_RUNNER` and the partial-coverage
  problem in `jira/`. Six classes → five; 45 → 32 (was 29). Further corrections:
  the desk-research basename collision is 7 suites, not 2; `$(1)`/`$(2)` exclude
  3 files, not 5; the collection floor is session-wide and `--collection-floor-
  suite` is only a label; the CI `for`-loop is 20 paths and is invisible to the
  parser for a different reason than stated; AC27 gained an explicit +8 MiB
  tolerance; new T4 wires the new gates in (nothing globs `tools/test_*.py`);
  T3 gained the three pinned-count files; T8 gained the scaffold projection and
  the two stale workflow comments; the nine core suites with no safety obstacle
  are now an explicit Ask-first question rather than a silent decline.
- **Rev 1.** Initial plan. Baseline `939147d6`.
