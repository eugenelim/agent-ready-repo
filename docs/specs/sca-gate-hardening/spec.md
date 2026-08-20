# Spec: sca-gate-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — no public interface. The gate's *behaviour* changes: it now
  fails on conditions it previously passed, which § Blast radius bounds.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk trigger that fired: security boundary — this is the
repository's SCA gate, one of five required merge contexts, and every criterion here
turns a silent pass into a failure. Adversarial review is a NAMED SKIP (operator
disabled subagent dispatch); a mutation battery per criterion stands in for it and the
results are recorded in AC6 rather than asserted. -->

## Objective

`make sast`'s pip-audit leg has six ways to report success while auditing less than it
appears to. All six came out of the security review on `spec/pip-audit-batching`, which
was **archived without shipping** — none is caused by batching, and every one is live in
`make sast` today. Each was left as its own entry because each is its own decision; they
are taken together because all six land in one 210-line file plus its self-test, and the
triage of "did this gate actually run" happens once.

One of the six, AC2, was initially triaged OUT of this batch as an either/or needing a
decision. On reading it against the code the choice collapsed: its two options are
"count include lines as content" and "exit 2 on one", and exiting 2 would refuse a shape
the self-test already blesses. The reasoning is recorded in `plan.md` § Declined
patterns rather than left as a silent scope change.

Success: every silent-skip path either audits or fails, the data sources are pinned in
code rather than inherited from the environment, and the audited input set has a floor
that fails by name when it shrinks.

## Acceptance Criteria

- [x] **AC1 — `--strict`, so an unresolvable dependency is not silently skipped.**
  `-S/--strict` is passed. Without it a dependency the advisory service cannot serve
  (a PyPI 404 for that name+version) is skipped while pip-audit still exits 0 — the
  same "a silent no-op is not a pass" class ADR-0084 already gated for bandit.

  Measured free, warm cache, same nine manifests, both green:
  `HEAD 1.12s / 2.20s` vs `this change 1.23s / 1.26s`. (Frame matters: a *cold*-cache
  first run of the same leg took 77s on this machine. All four figures above are
  warm-cache, back to back, after a discarded warm-up run — a cold-vs-warm comparison
  would have manufactured a 7× regression that is not there.)

- [x] **AC2 — dependency-bearing option lines count as content.**
  `partition()` sends every `-`-prefixed line into the audited half, and the emptiness
  test then excluded exactly those lines. So a manifest whose only content was
  `-r nested.txt`, `-c constraints.txt` or `-e .` printed
  `no third-party requirements to audit` and was audited **zero** times, at exit 0.

  `_is_dependency_bearing()` now recognises `-r/--requirement`, `-c/--constraint`,
  `-e/--editable`, `-f/--find-links` as content, matching on the option token so
  `--requirement=x.txt` counts too. `--index-url`, `--extra-index-url` and
  `--no-binary` deliberately do **not**: they configure resolution, they do not add a
  requirement.

  Latent rather than live — no such manifest exists today — but self-test case 4
  already blesses `-r other.txt` as a supported shape, so the shape is sanctioned.

- [x] **AC3 — the advisory feed and index cannot be re-aimed by the environment.**
  `-s pypi` and `--format columns` are passed explicitly, and `PIP_AUDIT_*`,
  `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL` are stripped from the child environment.
  pip-audit defaults its service, OSV URL, format and output from `PIP_AUDIT_*`, and
  the resolution venv's pip honours the index variables; either can produce
  `No known vulnerabilities found` at exit 0 without touching a tracked file. The
  realistic trigger is a stale shell profile, not an attacker.

  **`-s`, not `--service`.** The long form is `--vulnerability-service`
  (pip-audit 2.10.1); `--service` is not accepted, and the first revision of this
  change used it. It did not fail loudly — the run surfaced as
  `argument project_path: not allowed with argument -r/--requirement`, which does not
  name the offending flag. Caught by invoking the real leg rather than by reading the
  diff, and the corrected form is verified against a live manifest at exit 0.

- [x] **AC4 — an indefinite hang becomes a failure.**
  Every pip-audit invocation carries `timeout=300`, and `TimeoutExpired` is caught and
  returned as a failure with a named message rather than surfacing as a traceback.
  Each invocation measures 7–17s cold, so 300s is well clear of normal; the failure
  being bounded is a pathological resolver backtrack hanging CI, not a slow audit.

- [x] **AC5 — the filtered manifest no longer lands in a shared directory.**
  Each filtered manifest is written inside a per-run `TemporaryDirectory()` (0700)
  instead of `NamedTemporaryFile` in the shared system temp dir. The file *mode* was
  already safe (`O_EXCL`, 0600); the **directory** was the issue, because a relative
  `-r` / `-c` / `--find-links` / local-path reference inside a manifest re-resolves
  against the file's own directory — which was world-writable.

- [x] **AC6 — every new control is proved able to fail.**
  A green gate is worth nothing unless breaking what it guards turns it red. Each
  mutation applied and reverted, `Makefile` confirmed byte-identical afterwards:

  | Mutation | Result |
  | --- | --- |
  | Drop `$(find packs …)` from the Makefile invocation | exit 1, `FAIL the Makefile still enumerates packs manifests by find` |
  | A `packs/**/requirements.txt` disappears (rename) | exit 1, `FAIL packs manifest count is 8 … found 7` naming the survivors |
  | A new `tools/requirements*.txt` appears | exit 1, `FAIL the tools/ manifest roster is unchanged` |
  | Revert AC2's predicate | exit 1, `FAIL an include-only manifest counts as having content to audit` |
  | Revert AC3's env scrub | exit 1, two failures (`PIP_AUDIT_*`, `PIP_INDEX_URL`) |

  The self-test's own first revision also failed for the right reason and was
  corrected: its Makefile-line predicate matched the `SAST_CONFIG :=` assignment,
  which also names `tools/audit-requirements.py`. It now matches on the recipe
  invocation prefix, and a `the … invocation was located in the Makefile` case fails
  if no recipe line is found at all — so an empty match cannot pass the two
  assertions that read it.

- [x] **AC7 — the audited input set has a floor.**
  `Makefile`'s `$(find packs -name requirements.txt | sort)` has its exit status
  swallowed by the pipeline, so a renamed, moved or deleted manifest shrank the
  audited set silently at exit 0 and nothing asserted the expected count. The
  self-test now pins:
  - the invocation still enumerates packs manifests by `find` and still names
    `tools/requirements.txt` explicitly;
  - `_EXPECTED_PACK_MANIFESTS = 8`, so a vanished manifest fails by name;
  - `_EXPECTED_TOOLS_MANIFESTS`, the four-file roster, so a **new**
    `tools/requirements*.txt` cannot silently join the unaudited set.

  The three unaudited `tools/` manifests stay unaudited — that is
  `sast-requirements-not-audited`, a separate open entry with its own
  audit-vs-Dependabot decision. This criterion pins the roster so a fourth is
  deliberate; it does not widen coverage.

- [x] **AC8 — the self-test does not reach the network.**
  AC2's case asserts the content predicate directly instead of calling `audit()`,
  which would spawn pip-audit against a nonexistent include — network I/O and a usage
  error inside a self-test. Runtime went 5.6s → 3.5s, and the predicate is the thing
  under test.

## Blast radius

This change makes a required merge context **stricter**. Conditions that previously
passed and now fail:

- a dependency the advisory service cannot resolve (AC1);
- a manifest whose only content is an include (AC2) — no such manifest exists today;
- a pip-audit run exceeding 300s (AC4);
- a shrunken or grown manifest roster (AC7).

Verified before proposing: the real leg over all nine current manifests exits **0**
under the new flags. So nothing in the tree trips the new failures — they are
guards, not a backlog of work this PR creates.

## Boundaries

**Never do**

- Add the three unaudited `tools/` manifests to the audit invocation. That is
  `sast-requirements-not-audited` and needs its audit-vs-Dependabot decision first;
  AC7 pins the roster instead.
- Batch the per-manifest invocations. `spec/pip-audit-batching` was archived
  precisely because batching trades away per-manifest SCA fidelity.
- Relax `--strict` if a future manifest trips it. A dependency the service cannot
  serve is the finding, not the noise.
- Touch the four `--ignore-vuln` semgrep-transitive suppressions. Unrelated leg,
  and their unblock condition is still unmet (semgrep 1.166.0 pins `mcp==1.23.3`).

## Assumptions

1. **`-s pypi` is the correct flag and `pypi` a valid choice.** Verified against
   `pip-audit --help` (2.10.1: `choices: osv, pypi, esms`, default `pypi`) and by a
   live invocation at exit 0. Passing it explicitly pins today's default against a
   future upstream change as well as against the environment.
2. **300s is comfortably above normal.** Each invocation measures 7–17s cold. The
   number is a hang bound, not a performance budget.
3. **No manifest currently relies on a relative include resolving against the shared
   temp dir.** None contains `-r`, `-c` or `--find-links` at all, which is also why
   AC2 is latent.
