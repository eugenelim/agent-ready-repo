# Spec: pip-audit-batching

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017 (pip-audit is the SCA gate; scanners stay CI-only dev
  dependencies), ADR-0086 (the SAST/SCA leg is its own `gate-sast` job and is the
  critical path, so additions to it translate 1:1 into PR latency), ADR-0083 (the npm
  SCA leg travels with the same gate and is untouched here)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — `tools/audit-requirements.py` is an internal gate script with no
  published interface. Its argv shape (`<requirements.txt> ...` and `--build-system
  <pyproject.toml> ...`) and its exit codes are consumed only by `make sast` and
  `tools/test-audit-requirements.py`; both stay as they are.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Three risk triggers fire: a compliance/governance surface (this
changes how the repo's SCA gate runs, governed by ADR-0017 and ADR-0086), a
security boundary (the gate's fail-closed behaviour and its network/file I/O), and
a structural change to how the gate invokes its scanner. -->

## Objective

`make sast` audits the repo's nine requirements files for known-vulnerable
dependencies in **one** `pip-audit` process rather than one per file, so the SCA leg
costs about 11 seconds instead of about 61. A maintainer running the local gate, and
the `gate-sast` job that is the CI critical path, both get that time back without
giving up anything the per-file loop provided: every skipped first-party pin is still
named against its own file, a file with nothing third-party to audit still says so,
any vulnerability anywhere still fails the gate, and a failing run still tells the
operator **which requirements file** to edit. Batching is refused — per file, not
globally — whenever merging two files' pins could narrow the resolution and hide a
finding the per-file audit would have caught.

The four `--ignore-vuln` CVE suppressions that `make sast` applies to
`tools/requirements-sast.txt` remain confined to that one invocation, because
`--ignore-vuln` is invocation-global and merging it would silently extend those four
suppressions across every other requirements file.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the gate fail-closed: any condition the script cannot reason about
  (unreadable file, broken first-party discovery, a batch it cannot prove safe to
  merge) results in a narrower batch or a non-zero exit, never a wider one.
- Flush the per-file label and its skipped-pin lines to stdout **before** the
  `pip-audit` process that they describe writes anything, so the ordering holds when
  stdout is a pipe (a CI log) and not just a terminal.
- Name every file whose pins are skipped and every file with nothing to audit,
  individually, exactly as the per-file loop does.
- Re-run the per-file audit when a batch fails, so the operator gets exact
  file-level attribution for the finding.

### Ask first

- Changing the argv contract of `tools/audit-requirements.py`, or the set of files
  `make sast` passes it.
- Weakening or relocating any `--ignore-vuln` suppression, or the two invocations
  (`tools/requirements-sast.txt` and the `/dev/stdin` extras audit) that `make sast`
  deliberately keeps separate.
- Changing `--build-system` mode, which already aggregates both pyprojects into a
  single audit and is not part of this problem.

### Never do

- Never fold the `tools/requirements-sast.txt` invocation or the `/dev/stdin` extras
  invocation into the batch. Both carry invocation-global flags or a distinct input;
  merging either applies its suppressions to files that never earned them.
- Never add a dependency. The script is stdlib-only and stays that way; no
  requirements parser, no resolver library, no new module boundary.
- Never report success for a file that was not actually audited. A file that cannot
  join a batch is audited on its own, not dropped.
- Never let a batched run exit 0 when any constituent audit found a vulnerability.

## Testing Strategy

Each user-visible outcome from the Objective, paired with a mode and why:

- **Batching, hazard detection, and partitioning are TDD.** They are pure functions
  over lists of requirement lines with a compressible invariant — given these files,
  produce these batch groupings — so they are tested directly in
  `tools/test-audit-requirements.py` with no network and no subprocess. This is where
  the gate's correctness actually lives, and the existing self-test already runs
  inside `make sast` for exactly that reason.
- **Suppression containment is TDD.** The assertion is structural: the argv the
  script builds for the batch contains no `--ignore-vuln`, and no batch ever includes
  `tools/requirements-sast.txt`. A test that would fail if the four suppressions
  leaked to another file is the specific case the brief requires.
- **Exit semantics are TDD**, exercised through a fake runner injected in place of
  `subprocess.run`, so "any constituent failure fails the gate" and "a failing batch
  falls back to per-file" are provable without a live audit. Verifying these against
  the real network would make the self-test slow and flaky, and would not
  deterministically produce a vulnerable pin.
- **The end-to-end gate is goal-based**: `make sast` exits 0, and the timing is read
  from a timestamped run. `Done when:` `make sast` is green and the pip-audit segment
  is one invocation.
- **Timing and the CI landing are manual QA**, recorded observations: a local
  timestamped `make sast` before and after, and a `gh run view --log` attribution of
  `gate-sast` before and after, using the same method both times.
- **Resolution equivalence is manual QA**, a one-time recorded proof: the merged
  audit's resolved `(name, version)` set equals the union of the per-file audits'
  resolved sets. It is not wired into `make sast`, because doing so would require
  both a batched and a serial run on every invocation and cancel the entire saving.

## Acceptance Criteria

- [ ] `make sast` runs **one** `pip-audit` process for the nine-file set, in place of
      the seven it runs today, and still runs the `--build-system`,
      `tools/requirements-sast.txt`, and `/dev/stdin` invocations as three separate
      processes.
- [ ] For every one of the nine files, the run prints that file's own label, its
      skipped first-party pins with reasons, or its "no third-party requirements to
      audit" line — the same per-file reporting the loop produces.
- [ ] Each file's label and skipped-pin lines appear **before** the `pip-audit`
      output they describe when stdout is a pipe, verified by reading a piped run's
      line order. (Today every label appears after all audit output in that case.)
- [ ] A vulnerability in any one of the nine files makes `make sast` exit non-zero.
- [ ] When a batched audit fails, the run then reports the finding **per file**, so
      the operator can identify which requirements file to edit without grepping.
- [ ] No `--ignore-vuln` flag appears in the argv of any batched invocation, and
      `tools/requirements-sast.txt` is never a member of a batch. A self-test case
      fails if either changes.
- [ ] Two files whose pins could narrow each other's resolution are audited in
      separate `pip-audit` invocations rather than merged: a package appearing in two
      or more files with non-identical requirement text, or carrying an upper bound
      (`==`, `<`, `<=`, `~=`, `!=`) while appearing in more than one file, forces the
      split.
- [ ] `tools/test-audit-requirements.py` still passes and has grown cases for
      batching, hazard-driven splitting, suppression containment, per-file
      attribution on failure, and exit-code aggregation. No existing case is weakened
      or deleted.
- [ ] The merged audit's resolved `(name, version)` set equals the union of the
      per-file audits' resolved sets for the nine files as they stand, recorded in
      the plan with the command that proves it.
- [ ] Before and after timings are recorded for both surfaces, measured the same way:
      a local timestamped `make sast`, and a `gh run view <run-id> --log` attribution
      of the `gate-sast` job.
- [ ] `SKIP_SAST=1 make build-check`, `make sast`, `python3 tools/lint-ruff.py`, and
      `python3 -m pytest tools/test_build_gate_chain.py -q` are all green.

## Assumptions

- Technical: `pip-audit`'s `-r` flag is repeatable and audits every named file in one
  process, propagating exit 1 on a finding (source: probe —
  `python3 -m pip_audit -r a.txt -r b.txt` with `urllib3==1.26.5` in the second file
  reported 10 vulnerabilities and exited 1, 2026-08-17)
- Technical: **no** `pip-audit` output format names the requirements file a finding
  came from — `columns` has no such column and `json` carries only
  `name` / `version` / `vulns` per dependency (source: probe —
  `python3 -m pip_audit -r a.txt -r b.txt --format json`, 2026-08-17). Naming the
  temp files after their sources therefore cannot restore attribution, which is why
  a failing batch re-runs per file instead.
- Technical: seven of the nine files spawn a `pip-audit` process today, not nine —
  `packs/atlassian/.apm/skills/flow-metrics/requirements.txt` is comments-only and
  `packs/credential-brokers/.apm/skills/credential-setup/requirements.txt` holds only
  the first-party `credbroker` pin, so both partition to empty and print "no
  third-party requirements to audit" (source: `make sast` baseline output, 2026-08-17)
- Technical: the merged resolution equals the union of the per-file resolutions for
  the current nine files — 25 `(name, version)` pairs on each side, no divergence in
  either direction (source: probe comparing one batched `--format json` run against
  seven per-file runs, 2026-08-17)
- Technical: across the nine files there are 11 distinct packages, of which only
  `credbroker` is pinned inconsistently, and it is first-party so `partition()`
  removes it before `pip-audit` sees anything; the sole upper bound is
  `tomlkit==0.15.1`, present in one file only (source: read of the nine files,
  2026-08-17)
- Technical: `pip-audit` is 2.10.1 (source: probe — `python3 -m pip_audit --version`,
  2026-08-17)
- Technical: `--ignore-vuln` is invocation-global, which is why `make sast` isolates
  the `tools/requirements-sast.txt` audit (source: `Makefile:252-265` and its
  comment, plus `pip-audit --help`)
- Process: `tools/audit-requirements.py` is listed in `SAST_CONFIG`
  (source: `Makefile:194`), so a diff touching it forces `gate-sast` to run — the
  change is validated by the gate it changes
- Process: this work is not part of `docs/specs/ci-gate-parallelization/`, which is
  `Shipped (2026-08-17)` and frozen, so it carries its own spec (source:
  `docs/specs/ci-gate-parallelization/spec.md:3`, user confirmation 2026-08-17)
- Product: the brief's stated target of `gate-sast` 158s → ~90s does not hold, and
  ~120s is the realistic landing: only seven of the ten `pip-audit` invocations in
  `make sast` are collapsible, and CI pays about 7s each, so the recoverable CI time
  is about 40s rather than 70s. The local saving is the larger one, about 50s (source:
  timestamp attribution of `gate-sast` on run 32063058843 and of a local
  `make sast`, 2026-08-17; user confirmation 2026-08-17)
- Process: a failing batch re-running the per-file loop is the accepted
  attribution mechanism — the green path pays nothing and the red path pays the old
  cost, on the reasoning that a red SCA gate is a stop-and-fix event rather than a
  hot path (source: user confirmation 2026-08-17)
- Process: the textual merge-hazard guard is the accepted false-green defence, in
  preference to documenting the residual or asserting equivalence inside `make sast`
  (source: user confirmation 2026-08-17)

### Accepted residual

The textual guard covers narrowing through **directly declared** pins. It cannot see
narrowing through a **transitive** one — an upper bound declared in file A that
constrains a package reached only through file B's dependency tree is invisible to a
text rule, and detecting it would need the per-file resolution the batching exists to
avoid. This is accepted rather than closed, on three grounds: the equivalence proof
above shows no divergence for the tree as it stands; narrowing moves resolution
toward **older** versions, which carry more known vulnerabilities rather than fewer,
so the usual direction of the error is a louder gate, not a quieter one; and the
proof is cheap to re-run when the requirements files change, with the command
recorded in `plan.md`.
