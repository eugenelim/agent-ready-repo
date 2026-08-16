# Spec: boundary validation for CLI path arguments in shipped work-loop scripts

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (governance surface — ADR-0017 SAST gate; public-interface change — shipped pack scripts installed into adopter repos)
- **Constrained by:**
  - [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) — SAST/SCA gate authority; remediation ladder (fix > pragma > `.snyk`)
  - `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py:72–80` — the in-repo exemplar of the target pattern
  - `tools/semgrep/env-path-taint.yml` — existing custom taint rule; this spec adds a sibling, does not modify it
- **Contract:** none (script-internal; CLI surface unchanged)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Make the shipped `work-loop` scripts read CLI path arguments through a
**visible, intraprocedural normalize-and-validate boundary**, so that
taint-based SAST engines running in *adopter* repositories stop reporting
CWE-22/23 path-traversal findings against code we ship.

This is **mostly** a scanner-legibility fix, plus one genuine vulnerability
found during review.

`lint-traceability.py` was already safe: every read under `--root` is
re-confined through `_within()` / `_confined()`, and the only defect is that
the confinement is *interprocedural and shaped as a comprehension filter*,
which no taint engine follows.

**`lint-spec-status.py` had no confinement at all** — `grep -c "_within\|_confined"`
returned 0 against 25 in its sibling. An earlier draft of this spec asserted the
control covered both scripts; that was wrong and unverified. Review caught it,
and it concealed a real traversal: `_CONTRACT_TOKEN_RE` admitted `.` and `/`, so
a `- **Contract:** contracts/../../secret.json` header in an untrusted `spec.md`
resolved outside `--root` and was read. Reproduced end-to-end — the target's
presence changed the warning text, giving an existence oracle, plus a
content-substring oracle via `"x-spec" in ctext`. `docs/architecture/security.md`
declares `filesystem_read_untrusted` a boundary, so hostile repo content is in
scope. This spec now also closes that.

## Why suppression is not available

Three suppression vehicles exist; none reaches an adopter.

1. **`# nosec`** — Bandit-only. Does not reach Snyk (ADR-0017 § remediation ladder).
2. **Semgrep rule exclusion** — our gate only. Does not reach an adopter.
3. **`.snyk` policy file** — does not ship in any pack, and *cannot* without new
   machinery: `agentbundle install` has no YAML-merge mode, so two packs each
   shipping a `.snyk` would clobber one another. Deferred — see
   `[backlog].open` slug `agentbundle-install-yaml-merge`.

Suppression also does not scale: each adopter org runs its own scanner
(Snyk, Checkmarx, Veracode) with its own ignore store. **Fixing the source is
the only remediation that reaches every adopter at once.** This is ADR-0017's
own rung 1.

## Evidence

18 Snyk Code CWE-23 findings were reported against two shipped scripts,
observed in an adopter checkout at `.kiro/skills/work-loop/scripts/`
(an adapter projection; `.kiro/` is absent from this repo).

Every finding traces to **two lines**:

| File | Line | Expression |
|---|---|---|
| `lint-spec-status.py` | 442 | `root = args.root.resolve() if args.root else _repo_root()` |
| `lint-traceability.py` | 1251 | `root = (args.root.resolve() if args.root else _repo_root()).resolve()` |

Snyk flags derived sinks up to ~800 lines downstream, including lines whose
*immediately preceding statement* is `if not _within(d, root): continue` —
conclusive evidence the existing sanitizer is not recognised.

### Verified analyser limits (spike, this session)

| Claim | Method | Result |
|---|---|---|
| OSS Semgrep taint is intraprocedural | Control with source in `main()`, sink in a called function, same file | **0 findings** — does not cross a call |
| A taint rule cannot reproduce the Snyk finding | Ran argv-source taint rule against real `lint-traceability.py` | **0 findings** |
| A taint rule would flood the gate | Same rule across `tools packs packages` | **20 findings**, all operator-supplied-root false positives |
| A boundary rule *can* pin the root cause | Structural rule at the argv-entry site | **Fires on exactly the 2 lines above** |
| A boundary rule cannot be repo-wide | Same rule across `tools packs packages` | **73 findings** — untenable as a blocking gate |
| CodeQL already clears this flow | `py/path-injection` in `security-extended`, run log confirmed executed | **0 alerts** |

## Scope

**In scope** — the four shipped `work-loop` scripts with an argv→path boundary:

| File | Line(s) | Argument |
|---|---|---|
| `lint-traceability.py` | 1251 | `--root` |
| `lint-spec-status.py` | 442 | `--root` |
| `loop-cohort.py` | 1083, 1147 | `--report` |
| `check-spec-status.py` | 72 | `spec_dir` / `--file` — **already correct**; used as the reference pattern, not modified |

**Out of scope** (deferred to `[backlog].open`):

- The other ~68 argv→path sites across `packs/` (converters, atlassian,
  workspace-status, receive-brief) and `packages/agentbundle` — slug
  `pack-argv-path-boundary-sweep`.
- `tools/` — not shipped; ADR-0017 explicitly carves out dev-only CLIs.
- YAML-merge in `agentbundle install` — slug `agentbundle-install-yaml-merge`.
- Making CodeQL a required check — slug `codeql-required-check`.
- **JS SAST coverage** — slug `sast-javascript-coverage`. Split out because
  enabling coverage is the small half; triaging the findings it turns on is
  the real cost, and bundling that here would stall this fix.

**Declined, not deferred:**

- **Extending `SAST_DIRS` to `web/`** (62 JS/TS/Astro files). `web/` is the
  platform site — built and deployed from this repo, never installed into an
  adopter repo. It carries none of the shipped-artifact exposure that
  motivates this spec. Revisit only if `web/` gains a server-side runtime.

## Coverage audit (this session)

A scanner-coverage audit was run before finalising scope, to check whether the
Snyk findings pointed at a wider gap. Findings recorded here so the next
reader does not repeat it:

| Question | Result |
|---|---|
| Do unloaded Semgrep rulesets find anything? | 32 findings; 4 new classes — `path-join-resolve-traversal`, `tarfile-extractall-traversal`, `non-literal-import`, `detect-non-literal-regexp` |
| Are any of them genuine? | **No.** `catalogue.py:150` and `archive.py:379` both already pass `filter="data"`; `render-proof.js:418–441` findings sit inside that file's own `validateOutputPath` |
| What does Bandit contribute at the gate floor? | **Nothing today** — 266 findings, all LOW severity, zero at or above medium/medium. The gate can only fire on *new* medium+ findings |
| Is shipped JS scanned? | **No** — by any of the three scanners. Quantified in the `sast-javascript-coverage` backlog entry |

### CWE coverage vs. Snyk Code

Snyk Code's published rule tables were parsed and diffed against our stack
(Snyk Python rules: 43 rules / 43 CWEs; JS+TS: 53 rules / 42 CWEs; ours:
376 Semgrep rules → 74 CWEs, plus Bandit's 24 — union **84**).

| | Snyk CWEs | Ours | Gap |
|---|---|---|---|
| Python | 43 | 84 (union) | **10** — CWE-23, 209, 280, 321, 346, 453, 547, 757, 916, 1104 |
| JS/TS | 42 | 84 nominal, **0 effective** (Bandit is Python-only; `p/python` is Python-only) | **13** — CWE-23, 126, 208, 312, 346, 347, 547, 606, 640, 770, 916, 1287, 1321 |

**The load-bearing conclusion: rule count is not our problem.** We nominally
cover roughly twice Snyk's CWE count. The reported CWE-23 finding got through
not because we lack a path-traversal rule — we have CWE-22 rules and CWE-23 is
its near-synonym — but because **Bandit has no dataflow engine and OSS Semgrep
taint cannot cross a function boundary** (both verified this session). Adding
more CWE-tagged rules does not close a depth gap.

CWE tags are a coverage *proxy*, not proof of equivalent detection: two tools
can tag the same CWE and catch disjoint cases. This session is itself the
proof.

The one lever that does address depth is CodeQL, which already runs
`security-extended` for Python and is absent for JS — folded into
`sast-javascript-coverage`.

## Design

Add a module-local helper to each in-scope script, placed **in the same
function that reads `argv`** so the normalize-and-check is intraprocedural:

```python
def _validated_root(candidate: Path | None, fallback: Callable[[], Path]) -> Path:
    """Resolve a CLI-supplied scan root and assert it is a real directory.

    The normalize-then-check is deliberately intraprocedural and adjacent to
    the argv read: taint analysers recognise this shape, whereas the
    downstream `_within()` / `_confined()` confinement (which remains the
    actual security control) is interprocedural and is not followed.
    """
```

**Non-goal: confining `--root` to a hardcoded prefix.** `--root` *is* the
caller-supplied scan scope of a repo linter (`lint-traceability.py:1226`
documents this). Constraining it to a fixed parent would break legitimate use.
The validator normalises and asserts directory-ness; it does not restrict
*which* directory.

## Acceptance Criteria

- [x] **AC1** — `lint-traceability.py` reads `--root` through `_validated_root()`. **Corrected during review:** the helper is called *from* the function holding `parse_args()`, not inlined into it. The original wording ("in the same function") was not met and would not have been, since a module-local helper is the readable form. What matters is that the normalise-and-check is a single hop from the argv read rather than scattered across the call graph — but note this means OSS Semgrep still cannot connect them, and the check is existence/type, not containment. Assumption 2's confidence rests on Snyk being interprocedural, which it is.
- [x] **AC2** — `lint-spec-status.py` likewise, **plus** the confinement it never had: `_within()`, `_confined()` and a size-guarded `_read()` ported from `lint-traceability.py`, applied at the spec glob, the contract join, and both reads; and `_CONTRACT_TOKEN_RE` tightened to reject `.`/`..` segments.
- [x] **AC3** — `loop-cohort.py` reads `--report` through a shared boundary helper at both sites. **Amended during EXECUTE:** this helper is *normalise-only* (`_resolved_report()` — `Path(...).resolve()`), not a raising validator as originally drafted. `_classify_report` returns `invalid` for an unreadable report, and `SKILL.md` defines `invalid` as a Surface signal with `review inspect` exiting 0 for every report-content outcome; raising would convert a defined outcome into an operational error. The normalise still meets the spec's actual goal — putting the boundary next to the argv read, where a taint analyser can see it.
- [x] **AC4** — `check-spec-status.py` is **unmodified**; its existing pattern is cited in the new helpers' docstrings as the reference.
- [x] **AC5** — CLI behaviour is unchanged for every valid input: same exit codes, same stdout, for a valid `--root`, an omitted `--root`, and a relative `--root`.
- [x] **AC6** — An invalid `--root` (nonexistent path, or a file rather than a directory) exits non-zero with a diagnostic naming the offending path, rather than raising a traceback.
- [x] **AC7** — A new Semgrep rule `tools/semgrep/argv-path-boundary.yml` fires on the pre-fix form and is silent on the post-fix form, proven by committed positive **and** negative fixtures.
- [x] **AC8** — That rule is scoped (`paths.include`) to the fixed scripts only — a ratchet, not a repo-wide sweep — with the repo-wide finding count and the expansion condition recorded in the rule header. The number lives in `tools/semgrep/argv-path-boundary.yml` alone; it drifts as the ratchet expands, so nothing else restates it.
- [x] **AC9** — `make sast` passes with the new rule loaded; no new findings in the existing gate.
- [x] **AC10** — Full existing test suite for `packs/core` work-loop scripts passes unchanged.
- [x] **AC11** — `packs/core` version bumped in all three required files (`pack.toml`, `plugin.json`, `marketplace.json`); projections re-synced via `make build-self`.
- [x] **AC12** — CHANGELOG `[Unreleased]` records the skill-script change.
- [x] **AC13** — Deferred items recorded in `workspace.toml [backlog].open`: `pack-argv-path-boundary-sweep`, `agentbundle-install-yaml-merge`, `codeql-required-check`, `sast-javascript-coverage`, `sast-cwe-delta-review`, `loop-cohort-shell-suite-to-python`; and the `web/` decline recorded with its reason.
- [x] **AC14** — *(added during review)* The `lint-spec-status.py` path traversal is closed: `_within()` / `_confined()` / size-guarded `_read()` ported in and applied at the spec glob, the contract join, and both read sites; `_CONTRACT_TOKEN_RE` rejects `.` and `..` segments while still accepting every legitimate `contracts/<type>/<name>.<ext>` form. Proven by re-running the reproduction: the existence oracle and the symlink escape both produce no output, and invariant (v) still fires on real contracts.
- [x] **AC15** — *(folded in on request)* Review fingerprints use SHA-256. `_RE_FINGERPRINT` accepts **both** 64-hex and 40-hex so a cohort mid-review at upgrade time does not hard-fail on its stored SHA-1 values; `state-schema.md` and the `--fingerprint` help text updated. Stasis detection is unaffected — fingerprints are opaque tokens compared set-wise between rounds computed by the same binary; a straddling run misses one match and self-heals.
- [x] **AC16** — *(added during review)* Both new suites gate in CI. `tools/test-all.py` is executed by no workflow (`docs.yml:102`), so `test-root-validation.py` and `test-fingerprint-width.py` get explicit `docs.yml` steps plus path triggers, and `test-semgrep-argv-boundary.py` is chained into `make sast` where semgrep is guaranteed present (in `docs.yml` it would skip silently and gate nothing).

## Testing strategy

| AC | Mode | Mechanism |
|---|---|---|
| AC1–AC4 | Goal-based | `grep` for `_validated_root` at each site; `git diff --exit-code` on `check-spec-status.py` |
| AC5 | Visual / manual QA | Invoke each script for real — valid `--root`, omitted, relative — and record exit code + stdout |
| AC6 | TDD | Test asserting non-zero exit + diagnostic on a nonexistent and a file-valued `--root`. For `--report` (per amended AC3) the assertion is instead `classification == "invalid"` at exit 0 — and the fixture must initialise a **real cohort**, since an empty spec dir exits non-zero on the missing `state.json` before the report path is read, i.e. green for a reason unrelated to the feature |
| AC7 | TDD | Semgrep run over committed `positive.py` / `negative.py` fixtures; assert 1 finding then 0 |
| AC8 | Goal-based | Assert `paths.include` present; assert rule comment records the figure |
| AC9 | Goal-based | `make sast` exit 0 |
| AC10 | Goal-based | `python3 -m pytest packs/core/tests -q` |
| AC11 | Goal-based | Three-file version grep; `git status` clean after `make build-self` |
| AC12–AC13 | Goal-based | grep CHANGELOG; parse `workspace.toml` for the three slugs |

**Verification mechanism confirmed to exist before claiming these modes:**
`packs/core/tests/skills/work-loop/` is present; `make sast` and
`make build-self` are live Makefile targets.

## Assumptions

1. **The Snyk findings are false positives.** Corroborated independently by
   CodeQL's `py/path-injection` (interprocedural, `security-extended`,
   confirmed executed) returning zero. If this is wrong, the fix is
   insufficient and the confinement logic itself needs rework.
2. **Snyk recognises the resolve-then-check shape.** Standard for taint
   engines and matches the pattern already used at `check-spec-status.py:75`,
   but **unverifiable from here** — we have no Snyk access. Residual risk:
   the fix lands and the org scan still reports. Mitigation: the change is
   independently justified as defensive hardening (AC6 converts a traceback
   into a diagnostic), so it is not wasted even if Snyk still flags.
3. **No adopter passes a `--root` that fails the new directory assertion.**
   AC5 covers the valid cases; AC6 makes the failure mode explicit.

## Erratum — 2026-08-11

Downstream Snyk Code findings against core 2.5.6 disproved assumptions 1 and 2
as blanket statements. The highlighted operator-selected root flows remain
safe, but a same-class sweep found genuine adjacent gaps: unconfined metadata
and reference probes, recursive descent before canonical pruning, managed
state reads that followed symlinks, and `append-knowledge.py`'s weaker custom
lock reader. [`core-path-confinement`](../core-path-confinement/spec.md) owns
the corrective implementation and the per-finding disposition. A zero CodeQL
result and an argv-boundary validator are useful evidence, not proof that every
derived filesystem operation is safe.
