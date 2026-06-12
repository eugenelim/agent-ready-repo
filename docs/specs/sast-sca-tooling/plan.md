# Plan: SAST/SCA tooling (Bandit + pip-audit + Semgrep)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two interleaved strands: **stand up the gate** (config + Makefile target + CI
workflow for three scanners) and **clear the gate** (fix the genuine findings,
suppress the tool-specific false positives) so the gate lands green in the same
PR. The riskiest part is the tuning: Bandit must fail on the real medium+ issues
without drowning in the 1,951-entry `assert`-in-tests low tail, so the
`bandit.yaml` floor (severity≥medium, confidence≥medium, exclude tests, skip
B101) is load-bearing and verified empirically. The `loop-cohort.py` SHA-1 fix
touches a **projected** skill script, so its source edit lands under `packs/` and
is reprojected with `make build-self`. Order: build the Bandit config and prove
the baseline first, then fix/suppress findings until Bandit is clean, then layer
pip-audit and Semgrep, then CI + the `.snyk` scaffold + docs.

## Constraints

- **ADR-0017** — the three tools are CI-only dev dependencies, never runtime
  deps; suppression is real-fix-first, then `# nosec` (Bandit), then `.snyk`
  (Snyk-native).
- **Self-hosting projection** (memory `feedback_self_host_projection`) —
  `loop-cohort.py` source is `packs/core/.apm/skills/work-loop/scripts/`; edit
  there + `make build-self`, never the `.claude/` copy.
- **Stdlib purity** — `agentbundle`/`credbroker` are `dependencies = []`; the
  research skill's `arxiv-retriever.py` declares "Python 3 stdlib only" in its
  docstring. No fix may add a runtime dependency to these.
- **Windows-portable tooling** (memory `feedback_new_tools_python_not_bash`) —
  no new bash tool scripts; the gate is a Makefile target chained into the
  existing `make build-check` / `build-check.yml`.

## Construction tests

Per-task `Tests:` below. No cross-cutting integration test — every gate is a
goal-based one-liner (run the scanner, assert exit 0) per the spec's Testing
Strategy.

**Integration tests:** none beyond per-task goal-based checks.
**Manual verification:** `make sast` on a clean tree exits 0; `make build-check`
stays green; `make build-self` leaves the tree drift-clean.

## Design (LLD)

### Dependencies & integration

Three OSS scanners, pinned in a new `tools/requirements-sast.txt` (CI installs
it; contributors `pip install -r` it once). `make sast` **detects** the three
binaries and **fails clean** with an install hint if absent (Tier-1
declare/detect/fail-clean per memory `project_skill_prereq_pattern`) — it does
not auto-install. CI installs explicitly, then runs the same commands. Traces to:
AC "make sast exists", AC "dogfooded into make build-check".

### Interfaces & contracts

- `make sast` — the entry point; runs `bandit` → `pip-audit` → `semgrep`,
  stopping at the first failure. **Chained into `make build-check`** so the
  repo's single native gate runs it locally and in `build-check.yml` CI.
- `bandit.yaml` (repo root) — `exclude_dirs` for test trees, `skips: [B101]`,
  invoked with `--severity-level medium --confidence-level medium`.
- `.snyk` — Snyk-native suppression policy (documented scaffold).
No standalone `sast.yml`; the existing `build-check.yml` covers CI enforcement.
Traces to: every AC.

### Failure, edge cases & resilience

- **pip-audit + first-party packages:** `credbroker` appears in skill
  `requirements.txt` files. pip-audit audits the active env (after editable
  installs of the two packages) plus the third-party deps; first-party lines that
  don't resolve from an index are excluded from `-r` audits, audited via the
  installed-package path instead.
- **Semgrep registry drift:** rulesets pull from the network at scan time;
  documented as an accepted risk in ADR-0017, mitigation (pin/vendor) deferred.
Traces to: AC pip-audit, AC Semgrep.

### Quality attributes (NFRs)

Security-posture gate: "zero medium+ Bandit findings, zero Semgrep findings,
zero known-vulnerable deps" is the pass/fail bar (spec ACs). Traces to: all gate
ACs.

## Tasks

### T1: Bandit config + `make sast` (bandit leg) proves the baseline

**Depends on:** none

**Tests:**
- Goal-based: `bandit -r tools packs packages -c bandit.yaml --severity-level
  medium --confidence-level medium` at the configured floor **surfaces** the
  SHA-1 and XML findings and **does not surface** the `assert`/test-only tail
  (B101, test-tree B103/B108) — presence-of-signal + tail-suppression, not an
  exact-count match (the count drifts the moment anyone adds a `urlopen`/`sha1`).

**Approach:**
- Add `tools/requirements-sast.txt` pinning `bandit`, `pip-audit`, `semgrep`.
- Write repo-root `bandit.yaml`: `exclude_dirs` for `**/tests/**` /
  `**/build/tests/**` (test code uses `assert`, chmod, `/tmp` legitimately),
  `skips: [B101]`, each with a justifying comment.
- Add `.PHONY: sast` + a `sast:` target to the Makefile; first leg runs Bandit
  with the floor above. Detect the three binaries up front; fail clean with an
  install hint if missing.

**Done when:** `make sast` reaches the Bandit step and Bandit reports the known
medium+ findings (not the low tail).

### T2: Fix the two weak-SHA-1 findings (digest-preserving)

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/config.py, packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, .claude/skills/work-loop/scripts/loop-cohort.py (regenerated by build-self, not hand-edited)

**Tests:**
- Goal-based: Bandit no longer reports B324 at those two sites.
- Existing package/skill tests stay green (digests are byte-identical:
  `usedforsecurity=False` does not change SHA-1 output).

**Approach:**
- `config.py:482` and `loop-cohort.py:748` (pack source): add
  `usedforsecurity=False` to the `hashlib.sha1(...)` call.
- `make build-self` to reproject `loop-cohort.py` into `.claude/`.

**Done when:** both B324 findings gone; `make build-self` drift-clean; package
tests green.

### T3: Disposition the false positives + harden the arXiv parse

**Depends on:** T1

**Touches:** tools/lint-agent-artifacts.py, tools/lint-skill-spec.py, packages/agentbundle/agentbundle/catalogue.py, packs/research/.apm/skills/research/scripts/arxiv-retriever.py, packs/research/.apm/skills/research/scripts/perplexity-retriever.py, packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py

**Tests:**
- Goal-based: post-change Bandit medium+ run reports **zero** issues.
- `arxiv-retriever.py` still parses a real arXiv Atom response (manual: run it
  against a query, JSON on stdout).

**Approach:**
- `yaml.load` ×2 (`lint-agent-artifacts.py:189`, `lint-skill-spec.py:360`): add
  `# nosec B506 — Loader is a yaml.SafeLoader subclass (class def above)`.
- `catalogue.py` (B202 tarfile + B310 urlopen): this line **already carries its
  real fix** — `extractall(filter="data")` rejects unsafe members. Drop the
  stray `# noqa: S202` / `# noqa: S310` comments (nothing reads `# noqa: S`).
  Run Bandit on the file: if B202 still fires (Bandit can't see the `filter=`
  kwarg), add `# nosec B202 — real fix in place: extractall(filter="data")
  rejects unsafe members; Bandit cannot see the kwarg` — **not** re-filed as a
  pattern FP. The `urlopen` is a constant assembled-base GitHub archive URL:
  `# nosec B310 — constant github.com archive base assembled from parsed
  owner/repo/ref`.
- `arxiv-retriever.py`: (a) **real fix** — upgrade `ARXIV_API` from `http://` to
  `https://` (arXiv supports TLS; base stays constant), addressing B310 honestly;
  (b) B314 is a **stdlib pattern FP** (ElementTree resolves no external
  entities/DTDs on 3.11+) — `# nosec B314 — stdlib ElementTree resolves no
  external entities/DTDs (3.11+); arXiv is a constant first-party endpoint over
  TLS`; (c) `# nosec B310 — constant https arXiv API base`. **No** content-
  scanning guard (fragile, evasion-prone) and no runtime dependency — keeps the
  script stdlib-only per its docstring.
- `perplexity-retriever.py:70`: `# nosec B310 — constant https Perplexity API
  base`.
- `sso-broker.py:511`: `# nosec B310` with an honest reason **plus** a scheme
  guard (round-2 security review, C5): reject any resolved URL whose scheme is
  not `http`/`https` (exit 3) before `urlopen`. This is boundary input-validation
  returning the existing error code — `http` and `https` both still work, so it
  is not a contract change (ADR-0003 unaffected). Tested in T9. (Round-1 had
  deferred this as a behavior change; round-2 security review adopted the safe
  allowlist form — see plan changelog.)

**Done when:** post-change Bandit medium+ run is clean; arXiv parse still works.

### T4: pip-audit leg of `make sast`

**Depends on:** T1

**Tests:**
- Goal-based: `make sast`'s pip-audit step runs and reports no known-vulnerable
  pinned versions across `tools/requirements.txt`, the two packages, and the
  shipped per-skill `requirements.txt` files (or records any acceptance).

**Approach:**
- Add the pip-audit invocation to `make sast`: audit `tools/requirements.txt`
  and each skill `requirements.txt` (third-party lines), plus the installed
  editable packages. Handle first-party `credbroker` per the resilience note.

**Done when:** pip-audit runs clean (or documented acceptance) in `make sast`.

### T5: Semgrep leg of `make sast`

**Depends on:** T1, T3

**Tests:**
- Goal-based: `semgrep --config p/python --config p/security-audit --error`
  reports no findings on the post-fix tree.

**Approach:**
- Add the Semgrep invocation to `make sast` after the fixes land. Triage any
  additional findings Semgrep raises (fix or justify) so the leg is clean.

**Done when:** Semgrep leg of `make sast` exits 0.

### T6: Dogfood the gate — chain `make sast` into `make build-check`

**Depends on:** T1, T4, T5

**Touches:** Makefile, .github/workflows/build-check.yml

**Tests:**
- Goal-based: `make build-check` invokes the SAST gate (grep the recipe; run it
  and observe Bandit/pip-audit/Semgrep execute) and stays green on the post-fix
  tree.
- Goal-based: `build-check.yml` installs `tools/requirements-sast.txt` (+ the
  editable packages pip-audit needs) **before** `make build-check`.
- Goal-based: the Windows job (`build-check-windows.yml`) is untouched and does
  not invoke Semgrep (it runs `python -m agentbundle.build check` +
  `python tools/hooks/pre-pr.py`, never `make`).

**Approach:**
- Add `sast` to the Makefile `.PHONY` list and chain it into the `build-check`
  recipe (so the repo's single native gate runs SAST locally and in CI). Keep
  `make sast` callable standalone.
- Edit `.github/workflows/build-check.yml`: add a `pip install -r
  tools/requirements-sast.txt` step (and ensure the editable packages are
  installed) **before** the `make build-check` step; **bump `timeout-minutes`**
  (ADR-0017 already commits to Semgrep's rule-fetch + ~76k-LOC scan slowdown, so
  raise it now — e.g. 5 → 15 — rather than discover it via a red first run).
- Do **not** touch `tools/hooks/pre-pr.py`, `tools/pre-pr-catalogue.py`, or
  `build-check-windows.yml`.

**Done when:** `make build-check` runs the SAST gate green; Windows job
unchanged.

### T7: `.snyk` suppression scaffold

**Depends on:** none

**Tests:**
- Goal-based: `.snyk` is valid YAML with a documented `ignore:` example and no
  invented issue IDs.

**Approach:**
- Commit a `.snyk` policy file: header comment explaining it is the Snyk-native
  suppression vehicle (SCA ignore-by-ID with `reason`+`expires`; Code via
  Consistent Ignores), a commented worked example, and a `version` key.

**Done when:** `.snyk` present, valid, documented, no fabricated IDs.

### T8: Docs — changelog + dependency record

**Depends on:** T1-T7

**Tests:**
- Goal-based: `make build-check` green; changelog `[Unreleased]` entry present;
  dependency record names the three tools.

**Approach:**
- `docs/product/changelog.md` `[Unreleased]` → Added: the SAST/SCA gate.
- The dependency record is **ADR-0017** itself (the rule's "or an ADR" branch;
  these are dev/CI-only tools, not a package runtime dep). No `AGENTS.md` /
  `AGENTS.local.md` dep edit is required by the rule — add a one-line pointer to
  `AGENTS.local.md` only if it helps discoverability.
- Flag in the PR description: the `http://`→`https://` arXiv endpoint change as a
  deliberate finding-driven real fix (B310).

**Done when:** `make build-check` green; docs updated.

### T9: Taint coverage + session-start sanitization + sso-broker guard (round-2)

**Depends on:** T1-T8

**Touches:** tools/semgrep/env-path-taint.yml, Makefile, packs/core/.apm/hooks/session-start.py, packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/agentbundle/tests/unit/test_sso_broker_verbs.py, .github/workflows/codeql.yml

**Tests:**
- Goal-based: the custom Semgrep taint rule reports 0 on the sanitized hook and
  1 on a direct `Path(os.environ.get(...))` canary.
- Existing session-start hook tests (17 py + shell) stay green; a `..` override
  is refused.
- New sso-broker tests: `file://` → exit 3; `https` (stubbed 2xx) → exit 0.

**Approach:**
- **Taint gap (Bandit can't do dataflow):** add `tools/semgrep/env-path-taint.yml`
  (`mode: taint`, env → `pathlib.Path`), wire `--config tools/semgrep/` into
  `make sast`; add the CodeQL workflow for interprocedural taint.
- **Sanitize (ship the fix to adopters):** add `_safe_override_path` to
  `session-start.py` (reject `..` before constructing the path), route the three
  env overrides through it, reproject.
- **sso-broker guard:** `{http,https}` scheme allowlist before `urlopen`.

**Done when:** `make sast` (incl. taint rule) green; CodeQL workflow valid;
session-start + sso-broker tests green.

## Rollout

- **Delivery:** big-bang, fully reversible (revert the PR). No data migration, no
  published event. The gate runs from this PR onward — `make build-check` chains
  `make sast` locally and in the existing `build-check.yml` CI; no new workflow.
- **Infrastructure:** none beyond GitHub Actions (already in use).
- **External-system integration:** Semgrep fetches registry rulesets at scan
  time (network); pip-audit queries the PyPI advisory DB.
- **Deployment sequencing:** fixes + config land together so the gate is green
  on first CI run; `make build-self` reprojection committed alongside the
  `loop-cohort.py` source edit.

## Risks

- **Semgrep raises findings beyond the known Bandit set** (different engine,
  broader rules). Mitigation: T5 triages them; if a large unfixable set appears,
  surface and consider scoping Semgrep's rulesets or making it advisory (ADR-0017
  pre-authorizes that revisit).
- **pip-audit can't resolve `credbroker`** from an index. Mitigation: audit it
  via the installed-package path, exclude the first-party line from `-r` audits.
- **Bandit version drift** changes rule IDs/behavior. Mitigation: pin in
  `tools/requirements-sast.txt`.

## Changelog

- 2026-06-12: initial plan.
- 2026-06-12: round-2 review + scope expansion (T9). Adopted the sso-broker
  `{http,https}` scheme guard (security review C5 — round-1 had deferred it;
  round-2 took the safe allowlist form that breaks no existing scheme).
  Added taint coverage after an org Snyk finding (env→`Path` on the
  session-start hook) exposed that Bandit has no dataflow engine: a custom
  Semgrep `mode: taint` rule + a CodeQL workflow, and a source-level sanitizer
  in the shipped hook so adopters inherit the fix rather than each suppressing.
