# Plan: pip-audit-advisory-allowlist

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Repository anchors

- **Governing sources read:** root `AGENTS.md`, `tools/AGENTS.md` (pure-stdlib
  rule; hyphenated `test-*.py` are standalone entry points a pytest sweep does
  not collect), `docs/AGENTS.md`, `AGENT_RULES.md` (table is empty),
  `packs/core/.apm/skills/new-spec/assets/plan.md` (task grammar).
- **Analogous implementation:** `tools/audit-npm.py` +
  `tools/npm-audit-allowlist.toml` + `tools/test-audit-npm.py` (ADR-0083) — the
  same problem on the npm leg, three files, same recipe position (self-test
  first, live audit second).
- **Second analogue:** `tools/run-semgrep-gate.py` + `tools/test-semgrep-strict-gate.py`
  — the wrapper-and-self-test shape ADR-0084 established for a scanner whose
  silence is ambiguous.
- **Hardening and helper source:** `tools/audit-requirements.py` — env scrub at
  `:45-65`, `_PIP_AUDIT_TIMEOUT_S = 300` at `:43,190-202`, `-s pypi` at
  `:185-190`, PEP 503 `_canonical` at `:70-72`, `_NAME` requirement-line regex
  at `:66-68`. `tools/test-audit-requirements.py:213-227` pins the scrub.
- **Named deviations, each deliberate:**
  1. **Timeout exit code.** `audit-requirements.py:194-202` returns 1 on
     `TimeoutExpired`; this wrapper returns 2, because its exit 1 is reserved
     for "there is a vulnerability" (AC8). The two legs therefore differ on one
     code in the same recipe. Accepted: an ambiguous 1 is the worse failure.
  2. **Reuse rejected on evidence.** `tools/audit-requirements.py` was read, not
     assumed: `_DIRECT_SAST_MANIFEST` (`:52-56`) exists specifically to
     *exclude* this manifest, and `partition()` (`:117`) splits requirement
     lines by first-party name, not advisories. Its helpers are the reuse; its
     control flow is not the seam.
  3. **No evidence pin.** The npm allowlist has no stale-entry detector; this
     adds one. It does **not** add the mechanical reachability pin an earlier
     draft carried — see Risks.

## Design (LLD)

### One file holds the acceptances and their bounds

`tools/pip-audit-allowlist.toml`:

```toml
allowed_packages = ["pyjwt"]

[[allow]]
id             = "CVE-2026-102268"
package        = "pyjwt"
fixed_in       = "2.14.0"
reason         = """<this advisory's trigger, and why this run cannot reach it>"""
unblocked_when = "Semgrep permits PyJWT>=2.14.0"
```

`allowed_packages` bounds the vehicle. Without it the file accepts an entry
naming any dependency and a live CVE, and every mechanical check passes;
this repository has no CODEOWNERS file and `CONTRIBUTING.md:263-278` treats
CODEOWNERS-driven routing as an above-Profile-C measure to adopt on felt
friction, so a declared in-file bound is the cheap control available and
widening it becomes a visible edit.

Matching is on the advisory's **primary `id`** only; aliases are not a match
path. Measured on the live feed: pip-audit's default `pypi` service returns each
of the ten with its CVE as the primary `id` and one GHSA alias, so an alias
branch would widen the vehicle without matching anything the primary id does
not.

`package` is part of the match key, canonicalised PEP 503 on both sides.
pip-audit's JSON emits `dep.canonical_name`, so an entry spelled `PyJWT` — the
published spelling — would otherwise match nothing and then trip the retirement
branch with a message about a fix that never arrived.

`fixed_in` lets AC4 tell a fix from feed silence, and AC5 keeps it honest: while
the advisory is still reported, `fixed_in` must appear in that advisory's own
`fix_versions`, so the copy cannot drift and an unreachable value cannot
permanently disable the detector.

### The subprocess environment, built by rule

Every `PIP_*` name is removed, **except** `PIP_CONFIG_FILE`, which is *set* to
`os.devnull`. That exception is the whole point: `/etc/pip.conf` and
`~/.config/pip/pip.conf` can carry `index-url` or `constraint` lines that re-aim
the resolve, and no environment scrub reaches a file — pointing
`PIP_CONFIG_FILE` at `os.devnull` is what suppresses them, while *removing* it
would re-enable them. Proxy and CA names are removed in both cases, because
`urllib.request.getproxies_environment` case-folds and makes a second pass in
which the lowercase names win. `PATH`, `PYTHONPATH` and pip's cache directory
stay outside the envelope, and the wrapper says so.

### Version ordering, stated because stdlib has none

`tools/AGENTS.md` forbids third-party imports, so `packaging.version` is
unavailable. The comparison rule is defined once in `spec.md` AC5 — match
`^\d+(\.\d+)*$` on both sides, split, intify, **zero-pad the shorter to the
longer**, compare. The padding is what makes `2.14` and `2.14.0` equal, which
case 19a pins; a bare tuple compare fails it. Anything else — a pre-release, a local version, an
epoch, a non-numeric segment — is **not orderable**, and not-orderable takes
AC4's safe branch. This is deliberately narrower than PEP 440: the only
comparison needed is "did the fix arrive", and the cost of a wrong answer is an
instruction to delete a written acceptance.

### The wrapper does its own partitioning

`tools/run-pip-audit-gate.py <manifest>` takes the manifest as **argv**, so
`tools/test-audit-requirements.py` can keep building its expected recipe line
from `_MOD._DIRECT_SAST_MANIFEST` and the exclusion stays tied to the
invocation. It runs `pip-audit -f json -s pypi -r <manifest>` with no `--ignore-vuln`
flags and partitions the result itself.

Grounded against the installed pip-audit 2.10.1
(`pip_audit._format.json.JsonFormat._format_dep`):

```python
# resolved dependency
{"name": <canonical>, "version": ..., "vulns": [{"id", "fix_versions", "aliases", "description"}]}
# skipped dependency — no "version", no "vulns"
{"name": <canonical>, "skip_reason": ...}
```

**`-S`/`--strict` was adopted in an earlier revision and is now removed.** The
reasoning that adopted it — root `AGENTS.md` ranks a native platform capability
above hand-rolling, and `docs/specs/pip-audit-batching/spec.md` measured it at
11.3s versus 11.1s — was sound in general and wrong here. Read in the installed
2.10.1: `_cli.py:555-558` calls `_fatal(f"{spec.name}: {spec.skip_reason}")`
*inside the audit loop*, and `_fatal` exits before `_cli.py:635-636` formats
anything. Under `-S` a skipped dependency therefore never reaches stdout at all,
and AC6's detector — which needs the dependency's name — would be reading a
shape the flag guarantees cannot exist. Omitting the flag is what makes the skip
observable. `-s pypi` is kept, matching the sibling's explicit service
selection.

**pip-audit's return code.** The normal run of this gate exits **1**, because
the wrapper passes no `--ignore-vuln` and ten advisories are found. So 0 or 1
with parseable JSON proceeds to `evaluate`; any other code, or unparseable
stdout at any code, is exit 2. Reading non-zero as failure would make AC1
unreachable.

Delegating suppression to `--ignore-vuln` would hide the suppressed advisories
from the wrapper, and AC4 needs to see them. pip-audit's JSON carries **no
severity field**, so the gate cannot and does not partition by severity.

### Exit contract, with precedence

Scoped to the wrapper process; the recipe's own `command -v` guards keep their
existing codes.

| Exit | Means |
| ---: | --- |
| 0 | Every advisory allowlisted, every entry live, every direct requirement audited |
| 1 | At least one advisory no entry covers — and no exit-2 condition |
| 2 | The gate could not render a trustworthy verdict |

Precedence is exit 2 over exit 1, because "do not trust this result" dominates
"there is a vulnerability". Both sets are printed either way. `main()` wraps its
body so an unhandled exception cannot leak Python's default exit 1 and read as a
finding.

## Tasks

### T1: Allowlist file and its ten entries

**Depends on:** none

**Tests:** reviewer-checked (AC10), run after this task exists.
`no stub (reviewer-checked)`.

**Done when:** `tools/pip-audit-allowlist.toml` parses under `tomllib` and
carries `allowed_packages` plus ten `[[allow]]` entries whose `fixed_in` values
match the `fix_versions` the live report publishes.

Each `reason` states that advisory's own trigger, then why this invocation
cannot reach it, addressing both call sites in the audited closure — semgrep's
`jwt.decode`/`PyJWKClient` and `mcp`'s `jwt.encode`. CVE-2026-102268 (the sole
CVSS-CRITICAL) gets its own statement; CVE-2026-102267 and CVE-2026-101917 state
the no-client-construction premise.

### T2: The self-test

**Depends on:** none

**Tests:** this task *is* the red.

| # | Input | Expect | AC |
| ---: | --- | --- | --- |
| 1 | Every vuln allowlisted, every entry live, all direct reqs audited | 0 | AC1, AC8 |
| 2 | Entry missing `id` | 2, names the entry | AC2 |
| 3 | Entry missing `package` | 2, names the entry | AC2 |
| 4 | Entry missing `reason` | 2, names the entry | AC2 |
| 5 | Entry with blank `unblocked_when` | 2, names the entry | AC2 |
| 6 | Entry missing `fixed_in` | 2, names the entry | AC2 |
| 7 | Entry field present but non-string | 2, names the entry | AC2 |
| 8 | `allow` not an array of tables | 2 | AC2 |
| 9 | Entry `package` outside `allowed_packages` | 2, names both | AC2 |
| 10 | One vuln not allowlisted | 1, names the id | AC3 |
| 11 | Same id reported against a different package | 1, not suppressed | AC3 |
| 12 | Report spells the package `PyJWT`, entry spells it `pyjwt` | 0 | AC3 |
| 13 | Vuln whose CVE appears only in `aliases`, entry keyed to it | 1, not suppressed | AC3 |
| 14 | Advisory absent, package present at >= `fixed_in` | 2, retirement fired, says remove | AC4 |
| 15 | Advisory absent, package present below `fixed_in` | 2, fix not present, does **not** say remove | AC4 |
| 16 | Advisory absent, package present at an unorderable version | 2, says versions could not be compared, does **not** say remove | AC4, AC5 |
| 16a | Advisory absent, resolved orderable but `fixed_in` unorderable | 2, same not-compared message | AC4, AC5 |
| 17 | Advisory absent, package absent from report | 2, nothing audited for it, does **not** say remove | AC4 |
| 18 | Resolved `2.9.0` vs `fixed_in` `2.14.0` | 2, fix not present — reddens on a lexicographic compare | AC5 |
| 19 | Advisory present, `fixed_in` not in its `fix_versions` | 2, names the disagreement | AC5 |
| 19a | Advisory present, `fixed_in` `2.14` vs published `2.14.0` | 0, compares equal | AC5 |
| 20 | Dependency carrying `skip_reason` | 2, names it | AC6 |
| 21 | A direct requirement of the manifest missing from the report | 2, names it | AC6 |
| 21a | Manifest derivation yields an empty floor | 2, names the manifest | AC6 |
| 21b | `allowed_packages` absent, a bare string, or holding a non-string | 2 | AC2 |
| 22 | Non-allowlisted advisory **and** a skipped dependency | 2, both printed | AC8 |
| 23 | Child env computed with `PIP_CONSTRAINT`, `PIP_INDEX_URL`, `HTTPS_PROXY`, `https_proxy` set | all absent from the computed env | AC7 |
| 23a | Child env computed with `PIP_CONFIG_FILE` set to a real path | present and equal to `os.devnull`, not removed | AC7 |
| 23b | pip-audit returns 1 with parseable JSON | proceeds to evaluate, not exit 2 | AC8 |
| 24 | pip-audit exceeds the timeout | 2 | AC7 |
| 25 | pip-audit exits non-zero, unparseable stdout | 2, distinguishable from 1 | AC8 |
| 26 | pip-audit binary absent | 2 | AC8 |
| 27 | Decision function raises an unexpected exception | 2, not 1 | AC8 |

**Done when:** all 33 cases run from `python3 tools/test-run-pip-audit-gate.py`
and fail against an absent wrapper for the right reason.

### T3: The wrapper

**Depends on:** T2

**Tests:** the T2 suite goes green. `evaluate(report, allowlist, direct_requirements)`
is pure; the subprocess call is a separate seam.

**Done when:** all 33 T2 cases pass and `make lint-ruff lint-mypy` is clean.

Pure stdlib (`tomllib`, `json`, `subprocess`, `re`, `os`, `pathlib`). Module
docstring states the exit contract, the precedence rule, the narrowed version
ordering, the environment rule and its envelope, why `--strict` is absent, and
why partitioning is local.

The two helpers borrowed from `tools/audit-requirements.py` — PEP 503
`_canonical` (`:70-72`) and the `_NAME` requirement-line regex (`:66-68`, used
to derive AC6's floor from the manifest) — are **copied with a pointer comment,
not imported**. That module is hyphenated, so importing it needs
`importlib.util.spec_from_file_location`, and loading it executes its body
including the `sys.stdout.reconfigure(...)` side effect at `:35-36` — the hazard
`tools/test-all.py:42-48` documents by name. Two short functions are not worth
that coupling.

**Mutation proof:** three mutations, each naming the cases it must redden —
(a) partition treats every advisory as allowlisted and every entry as matched:
cases 10, 11 redden; (b) stale detector reports every entry live: 14, 15, 16,
17 redden; (c) version compare switched to string comparison: 18 reddens.
Recorded in the verification ledger.

### T4: Recipe swap and the anchors that gate it

**Depends on:** T1, T3

**Tests:** goal-based.

**Done when:** `make sast` exits 0 and its output names ten suppressions with
their package; `python3 tools/test-audit-requirements.py` passes; and
`python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` passes.
The digest assertion is `test_sast_sca_and_terminal_verdict_surfaces_match_approved_bytes`
(`:2188`) and is reachable **only** under pytest — a bare
`python3 tools/…dedup….py` prints a usage line and asserts nothing about the
pins, so naming it here would be a Done-when that cannot fail for the right
reason.

The recipe swap and the first two anchor repairs are **one task on purpose**.
`tools/test-audit-requirements.py` runs at `Makefile:378`, *inside*
`sast-unleased`, and asserts the old `@pip-audit -r tools/…` recipe line — so
the moment the recipe changes, `make sast` cannot exit 0 until that assertion
moves. Splitting them would give this task an observable it cannot reach.

1. Replace the `@pip-audit … --ignore-vuln CVE-2026-102274` line and its comment
   block with the self-test then the wrapper, matching the sibling SCA legs.
2. Add `tools/pip-audit-allowlist.toml` to `SAST_CONFIG`, for the reason
   `Makefile:230-232` already gives its npm sibling — "an added suppression must
   be validated by the gate it loosens". An earlier draft omitted it as
   redundant with `SAST_DIRS`; that left two sources asserting different rules
   for the same decision.
3. `tools/test-audit-requirements.py` — move the recipe assertion to the wrapper
   spelling, still built from `_MOD._DIRECT_SAST_MANIFEST` so the exclusion and
   the invocation stay one source.
4. `tools/test_local_ci_shared_test_deduplication.py` — re-pin
   `MAKE_BASELINE_DIGESTS` for `sast-unleased` and `SAST_CONFIG`. Per that
   file's own discipline, justify by reproducing **all eight** extracted
   surfaces and confirming only those two moved.

### T5: The remaining descriptive surfaces

**Depends on:** T4

**Tests:** goal-based.

**Done when:** the falsified clauses in the two comment surfaces AC11
enumerates carry no reference to a flag or a direct invocation that no longer
exists; `python3 tools/test-all.py` passes; the new backlog slug resolves in
`workspace.toml`. The predicate is scoped to those surfaces on purpose: a
repo-wide `grep -rn -- '--ignore-vuln'` returns fifteen hits, including
`docs/adr/0083…:113` and `docs/specs/npm-sca-gate/plan.md:46`, which Out of
scope deliberately leaves alone — an unscoped search would be unsatisfiable by
this spec's own construction.

1. `docs/architecture/verification-graph.md:188-202` — every clause the fifth
   wrapper falsifies, not only the quoted sentence: "The SAST leg is not four
   tool invocations", the four-wrapper enumeration, "two more run it directly"
   (now one), **its identifying sub-clause** "one against
   `tools/requirements-sast.txt`, the single manifest the wrapper deliberately
   excludes" — after this change that manifest is the one that moves *behind* a
   wrapper and the remaining direct call is the `/dev/stdin` extras audit, so
   decrementing the count alone would leave the sentence naming the wrong
   invocation — and the self-test/gate table gains a row.
2. `tools/test-all.py` — register the new self-test, matching `audit-npm`, the
   closest analogue. (`test-audit-requirements.py` is absent from that roster
   for the reason its header comment gives; that reason does not apply here.)
3. Correct the stale "four suppressions" counts in
   `tools/npm-audit-allowlist.toml:9-11` and `tools/audit-requirements.py:52-55`,
   whose last referent T4 removes. ADR-0083's identical sentence is left alone
   and recorded in T6's ADR.
4. Register the un-hardened pip-audit invocations in `workspace.toml
   [backlog].open`. The four slugs the archived `pip-audit-batching` spec claims
   were recorded are **not** in `workspace.toml` — verified, zero hits — so the
   spec's Out-of-scope carve-out has no owner until this exists.

### T6: The governing record

**Depends on:** T4

**Tests:** reviewer-checked (AC9). `no stub (reviewer-checked)`.

**Done when:** `docs/adr/0131-…md` exists with Status Accepted, is listed in
`docs/adr/README.md`, and carries the call paths, walked distributions, versions,
date, reproducing command, envelope statement and two residuals AC9 names.

## Rollout

No rollout dimension applies: a CI-only gate change with no runtime surface, no
persisted state, no migration and no mixed-version window. It takes effect on
the first `make sast` after merge, and reverts by reverting the commit.

## Risks

- **The reachability claim has no automated detector.** A future `semgrep` or
  `mcp` release could reach PyJWT from the scan path and nothing in this
  repository would notice. This is accepted deliberately — an earlier
  mechanical pin was removed for manufacturing assurance it could not deliver —
  and is owned by T6's ADR, which records the verified call paths, the versions
  and date, and the command that reproduces the walk. Mitigation is
  re-verification at the named trigger, not a check.
- **The audited floor does not see the transitive closure.** AC6 compares the
  manifest's three direct requirements (`bandit`, `pip-audit`, `semgrep`)
  against the audited set. A resolve that keeps all three but loses a
  transitive package carrying an advisory exits 0. Accepted rather than closed:
  a closure-wide expected-name-set would churn on every upstream release, which
  is the failure the removed pin already demonstrated. Owned by T6's ADR.
- **The acceptance is wider than the evidence.** The evidence covers the
  `make sast` invocation. The suppression silences these ten advisories for
  every contributor who installed `tools/requirements-sast.txt`, including one
  who runs `semgrep mcp` from that install. AC9 requires the ADR to say so.

## Assumption trio

- **Files touched:** `tools/pip-audit-allowlist.toml`,
  `tools/run-pip-audit-gate.py`, `tools/test-run-pip-audit-gate.py`, `Makefile`,
  `tools/test-audit-requirements.py`,
  `tools/test_local_ci_shared_test_deduplication.py`, `tools/test-all.py`,
  `tools/npm-audit-allowlist.toml` (comment only),
  `tools/audit-requirements.py` (comment only),
  `docs/architecture/verification-graph.md`, `workspace.toml`,
  `docs/adr/0131-…md`, `docs/adr/README.md`. Nothing under `packs/`,
  `packages/`, or `.github/workflows/`.
- **Done means:** `make sast` exits 0 on this tree; all 33 self-test cases pass;
  the anchor suites pass; `make lint-ruff lint-mypy` clean.
- **Not changing:** the semgrep floor, `SEMGREP_EXCLUDE`, `bandit.yaml`,
  `tools/audit-npm.py`'s behaviour, `tools/audit-requirements.py`'s behaviour,
  the resolver exclusion, the gate chain, or which jobs run on a pull request.

## Declined patterns

- **The mechanical reachability pin.** Removed on an explicit owner decision
  after two review rounds produced four blockers and three concerns against it
  without converging — wrong scope (it missed `mcp`'s `jwt.encode` inside the
  same audited closure), an oracle weaker than the property it claimed,
  `PYTHONPATH` able to green it, and churn on every in-range Semgrep release.
  The reason is rung-1: not genuinely needed, and actively harmful, because a
  proxy that cannot see the failure it names manufactures assurance.
- **Per-approved-file content digests** as a stronger pin. Moot once the pin
  went, and independently declined: a digest churns on every patch release.
- **A generic severity policy engine.** Rung 1 — pip-audit publishes no
  severity, so it would rank a field that does not exist.
- **`packaging.version` for ordering.** A new dependency under root `AGENTS.md`
  and forbidden by `tools/AGENTS.md`; the narrowed numeric comparison plus a
  safe branch covers the one question asked.
- **Folding anything into `tools/check-semgrep-version.py`.** Rung 2, rejected:
  its name and docstring scope it to the version range.
- **Reusing `tools/audit-requirements.py`'s control flow.** Rung 2, rejected on
  read — see Named deviation 2. Its helpers *are* reused.
- **Adopting CODEOWNERS for the allowlist.** Declined as out-of-frontier
  repository sizing, not on a recorded prohibition: `CONTRIBUTING.md:263-278`
  is conditional above-Profile-C guidance, and an earlier draft overstated it
  as a decision to decline. `allowed_packages` is the substitute.
- **Hardening the other pip-audit invocations.** Work-frontier rule; the owner
  scoped this to the new invocation, and T5 registers the remainder.

## Changelog

- 2026-09-29 — Plan approved by repository maintainers; baseline sealed.
- 2026-09-29 — Spec approved by repository maintainers after three
  pre-EXECUTE review rounds; the mechanical reachability pin was removed by
  owner decision in round 2 and the hardening scope was set by owner decision
  before round 1's revision.
- 2026-09-29 — Drafted.
- 2026-09-29 — Revised from adjudicated pre-EXECUTE review round 1.
- 2026-09-29 — Revised from review round 3. `--strict` **removed** after both
  reviewers independently read `_cli.py:555-558` and found it exits inside the
  audit loop, so a skipped dependency never reaches the JSON the detector
  needs — a reversal of round 2's native-capability finding, recorded rather
  than silently switched. Alias matching dropped after the live feed was
  measured to return CVEs as primary ids. pip-audit's own return code given a
  stated reading, since the normal run exits 1. Environment rule corrected:
  `PIP_CONFIG_FILE` is set to `os.devnull` rather than removed, and proxy names
  are scrubbed in both cases. AC6's floor derivation specified and given an
  empty-floor case. Helpers copied rather than imported, to avoid the
  hyphenated-module import and its stream-reconfigure side effect. T4's
  Done-when corrected to the pytest invocation that actually runs the digest
  assertion; T5's predicate scoped to AC11's surfaces. Self-test grown to 33.
- 2026-09-29 — Revised from review round 2. Pin removed per owner decision and
  replaced by a Risks section and an ADR obligation; T4 and the two gating
  anchors merged after `tools/test-audit-requirements.py` was found to run
  inside `make sast`, making the old ordering unreachable; `-S` and `-s pypi`
  adopted; version ordering, exit precedence, PEP 503 canonicalisation,
  `allowed_packages` and the `fixed_in` cross-check added; manifest passed as
  argv to preserve the `_DIRECT_SAST_MANIFEST` coupling; self-test grown to 27
  cases; T5 added for the descriptive surfaces and the missing backlog
  registration.
