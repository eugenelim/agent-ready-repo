# Spec: pip-audit-batching

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017 (pip-audit is the SCA gate, auditing the dependency
  manifests the repo owns; scanners stay CI-only dev dependencies), ADR-0086 (the
  SAST/SCA leg is its own `gate-sast` job and is the critical path, so additions to it
  translate 1:1 into PR latency), ADR-0083 (the npm SCA leg travels with the same gate
  and is untouched here)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — `tools/audit-requirements.py` is an internal gate script with no
  published interface. Its argv shape (`<requirements.txt> ...` and `--build-system
  <pyproject.toml> ...`) and its exit codes (`0` clean, `1` at least one file failed,
  `2` gate configuration error) are consumed only by `make sast` and
  `tools/test-audit-requirements.py`; all of it stays as it is.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Three risk triggers fire: a compliance/governance surface (this
changes how the repo's SCA gate runs, governed by ADR-0017 and ADR-0086), a
security boundary (the gate's fail-closed behaviour and its file I/O), and a
structural change to how the gate invokes its scanner. -->

## Objective

`make sast` audits the repo's nine requirements files for known-vulnerable
dependencies in as few `pip-audit` processes as it can safely use, rather than one per
file. The seven-file `pip-audit` segment costs about 25 seconds instead of about 61. A
maintainer running the local gate, and the `gate-sast` job that is the CI critical
path, both get that time back without the gate becoming quieter in any respect.

Merging is earned, not assumed. Two requirements files share a `pip-audit` process
only when neither can constrain the other's dependency resolution — `pip-audit`
resolves every `-r` file into one environment, so a pin that narrows the resolution
would make the merged audit examine a version combination no adopter installs, and
would examine strictly fewer `(name, version)` pairs than auditing the files
separately. Any file that could narrow the resolution is audited on its own. Every
file is audited exactly once, and never zero times.

Nothing about the gate's reporting or its failure behaviour degrades. Every skipped
first-party pin is still named against its own file; a file with nothing third-party to
audit still says so; every audit names the real requirements paths it covers before it
runs, so a finding is locatable; a vulnerability anywhere fails the gate; and a
dependency the scanner could not collect fails the gate rather than being silently
skipped at exit 0.

The four `--ignore-vuln` CVE suppressions that `make sast` applies to
`tools/requirements-sast.txt` remain confined to that one invocation, because
`--ignore-vuln` is invocation-global and merging it would silently extend those four
suppressions across every other requirements file.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the gate fail-closed. Any condition the script cannot reason about — an
  unreadable file, broken first-party discovery, a file it cannot prove safe to merge,
  a dependency the scanner could not collect — results in a narrower batch or a
  non-zero exit, never a wider batch and never a green gate.
- Treat a batch's non-zero result as final. The per-file re-run that follows a batch
  failure is diagnostic; it can add a failure but can never clear one.
- Flush each audit's header and per-file reporting to stdout **before** the
  `pip-audit` process it describes writes anything, so the ordering holds when stdout
  is a pipe (a CI log) and not only a terminal.
- Name every file whose pins are skipped and every file with nothing to audit,
  individually, exactly as the per-file loop does.
- Audit every file exactly once. A file that cannot join a batch is audited alone.

### Ask first

- Changing the argv contract or exit codes of `tools/audit-requirements.py`, or the
  set of files `make sast` passes it.
- Weakening or relocating any `--ignore-vuln` suppression, or the two invocations
  (`tools/requirements-sast.txt` and the `/dev/stdin` extras audit) that `make sast`
  deliberately keeps separate.
- Changing `--build-system` mode, which already aggregates both pyprojects into a
  single audit and is not part of this problem.

### Never do

- Never fold the `tools/requirements-sast.txt` invocation or the `/dev/stdin` extras
  invocation into a batch. Both carry invocation-global flags or a distinct input;
  merging either applies its suppressions to files that never earned them.
- Never merge two files when the merged resolution could differ from auditing them
  separately — including through a pip option line, which applies to the whole merged
  resolution.
- Never add a dependency. The script is stdlib-only and stays that way; no
  requirements parser, no resolver library, no new module boundary.
- Never report success for a file that was not actually audited, and never let a
  batched run exit 0 when any constituent audit failed.
- Never claim a vulnerability was found on a failure path, because `pip-audit` exits
  `1` both for a finding and for a failure to collect dependencies.

## Testing Strategy

Each user-visible outcome from the Objective, paired with a mode and why:

- **Batch grouping, the merge-safety rule, coverage conservation, and partitioning
  are TDD.** They are pure functions over lists of requirement lines with a
  compressible invariant — given these files, produce these groupings — so they are
  tested directly in `tools/test-audit-requirements.py` with no network and no
  subprocess. This is where the gate's correctness actually lives, and the existing
  self-test already runs inside `make sast` for exactly that reason.
- **Exit-code aggregation and the diagnostic re-run are TDD**, exercised through a
  fake runner injected in place of `subprocess.run`. This is the only way to prove
  "a batch failure is never cleared by a clean re-run" without a live vulnerable pin,
  which no requirements file in this repo provides and which would make the self-test
  network-dependent and flaky.
- **Suppression containment is TDD**, and split across two surfaces because the leak
  paths differ: the argv the script builds is asserted in the self-test, and the
  Makefile's own text is asserted there too, because the realistic regression is a
  maintainer adding `--ignore-vuln` to the batched recipe line to unblock a red gate —
  which no argv-level assertion can see.
- **Stdout ordering is TDD at the subprocess level, not the call level.** A call-order
  assertion passes even when `flush=True` is missing, because stdout is block-buffered
  to a pipe; so the test runs the script as a subprocess with `stdout=PIPE` and a stub
  `pip_audit` on `PATH`, and asserts the order of the captured bytes.
- **The end-to-end gate is goal-based**: `make sast` exits 0 and the pip-audit segment
  shows the expected number of invocations. `Done when:` `make sast` is green.
- **Timing and the CI landing are manual QA**, recorded observations: a local
  timestamped `make sast` before and after, and a `gh run view --log` attribution of
  `gate-sast` before and after, using the same method both times.
- **Resolution equivalence is manual QA**, a recorded proof re-runnable on demand: the
  batched audits' resolved `(name, version)` set equals the union of the per-file
  audits' resolved sets. It is deliberately not wired into `make sast`, because doing
  so would require both a batched and a serial run on every invocation and cancel the
  entire saving.

## Acceptance Criteria

- [ ] Requirements files whose audited pins carry only lower-bound specifiers, and no
      pip option lines, are audited together in a single `pip-audit` process; every
      other file is audited in its own process. For the nine files as they stand this
      is **two** processes in place of today's seven.
- [ ] The `--build-system`, `tools/requirements-sast.txt`, and `/dev/stdin` audits
      remain three separate `pip-audit` processes, unchanged.
- [ ] The `pip-audit` segment of `make sast` for the nine-file set completes in under
      30 seconds, measured by timestamping the run's output lines.
- [ ] For every one of the nine files, the run prints that file's own label, its
      skipped first-party pins with reasons, or its "no third-party requirements to
      audit" line — the same per-file reporting the loop produces.
- [ ] Every audit prints a header naming the real requirements paths it covers,
      immediately before that audit runs. This holds for a single-file audit too,
      whose `-r` argument is a temporary path that appears in `pip-audit`'s output but
      identifies nothing to the operator.
- [ ] Each header and its per-file reporting appear **before** the `pip-audit` output
      they describe when stdout is a pipe, verified by asserting line order on bytes
      captured from a subprocess run.
- [ ] A vulnerability in any one of the nine files makes `make sast` exit non-zero.
- [ ] The union of all batch memberships equals the set of files whose partition is
      non-empty, with no file omitted, duplicated, or placed in an empty batch. Batch
      membership is derived from the same predicate that decides whether to print "no
      third-party requirements to audit", so the two cannot disagree.
- [ ] A batch's non-zero result is retained regardless of what the diagnostic per-file
      re-run returns: a fake runner that fails the batch and passes every member still
      produces a non-zero aggregate.
- [ ] No failure message asserts that a vulnerability was found, because `pip-audit`
      exits `1` both for a finding and for a dependency-collection failure.
- [ ] Every audit of the nine-file set passes `-S`/`--strict`, so a dependency whose
      collection fails makes the gate fail instead of being skipped while the process
      still exits 0.
- [ ] No `--ignore-vuln` flag appears in the argv of any invocation the script builds
      for the nine-file set, and in the `Makefile` every `--ignore-vuln` occurrence
      sits on the `tools/requirements-sast.txt` invocation. A self-test case fails if
      either changes.
- [ ] The script exits `2` when an argv element is not an existing file, rather than
      auditing a smaller set than it was asked to.
- [ ] `tools/test-audit-requirements.py` still passes and has grown cases for batch
      grouping, merge-safety splitting, coverage conservation, exit-code aggregation,
      the diagnostic re-run, stdout ordering, and suppression containment. No existing
      case is weakened or deleted.
- [ ] The batched audits' resolved `(name, version)` set equals the union of the
      per-file audits' resolved sets for the nine files as they stand, and the script
      that re-proves it is committed and runnable rather than described in prose.
- [ ] Before and after timings are recorded for both surfaces, measured the same way:
      a local timestamped `make sast`, and a `gh run view <run-id> --log` attribution
      of the `gate-sast` job.
- [ ] `SKIP_SAST=1 make build-check`, `make sast`, `python3 tools/lint-ruff.py`, and
      `python3 -m pytest tools/test_build_gate_chain.py -q` are all green.

## Assumptions

- Technical: `pip-audit`'s `-r` flag is repeatable and audits every named file in one
  process, propagating exit 1 on a finding (source: probe —
  `python3 -m pip_audit -r a.txt -r b.txt` with `urllib3==1.26.5` in the second file
  reported 10 vulnerabilities and exited 1, 2026-08-17). `tools/requirements-sast.txt`
  pins `pip-audit>=2.10,<3`, and the probe verified 2.10.1; a bump within that range is
  a known re-probe point.
- Technical: `pip-audit` resolves all `-r` files into a **single** environment, so any
  constraint in any member file shapes the whole merged resolution (source: read of
  `pip_audit/_dependency_source/requirement.py`, 2.10.1, 2026-08-17). This is why
  merge safety is a property of the pins, not of the file count.
- Technical: `pip-audit` 2.10.1 exits `1` and only `1` for every failure — a finding
  and a `DependencySourceError` are indistinguishable by exit code (source: probe —
  the two `sys.exit` sites in the installed package are `_cli.py:192` and
  `_cli.py:638`, both `sys.exit(1)`, 2026-08-17). `2` is argparse's bad-argv code, not
  a pip-audit failure mode.
- Technical: **no** `pip-audit` output format names the requirements file a finding
  came from — `columns` has no such column and `json` carries only
  `name` / `version` / `vulns` per dependency (source: probe —
  `python3 -m pip_audit -r a.txt -r b.txt --format json`, 2026-08-17). Naming the
  temp files after their sources therefore cannot restore attribution, which is why
  every audit prints the real paths it covers before it runs.
- Technical: seven of the nine files spawn a `pip-audit` process today, not nine —
  `packs/atlassian/.apm/skills/flow-metrics/requirements.txt` is comments-only and
  `packs/credential-brokers/.apm/skills/credential-setup/requirements.txt` holds only
  the first-party `credbroker` pin, so both partition to empty and print "no
  third-party requirements to audit" (source: `make sast` baseline output, 2026-08-17)
- Technical: the merged resolution currently equals the union of the per-file
  resolutions — 25 `(name, version)` pairs on each side, no divergence in either
  direction (source: probe comparing one batched `--format json` run against seven
  per-file runs, 2026-08-17). This is the canonical home for that result; the plan
  cites it rather than restating it.
- Technical: across the nine files there are 11 distinct packages, of which only
  `credbroker` is pinned inconsistently, and it is first-party so `partition()`
  removes it before `pip-audit` sees anything. The only non-lower-bound specifier is
  `tomlkit==0.15.1` in `tools/requirements.txt`, and no file carries a pip option
  line — which is why the merge-safety rule yields exactly two invocations today
  (source: read of the nine files, 2026-08-17)
- Technical: `-S`/`--strict` is green against the current nine files and costs nothing
  measurable (source: probe — the batched run with `--strict` exited 0 in 11.3s versus
  11.1s without, 2026-08-17), so adopting it closes a fail-open at no cost
- Technical: `--ignore-vuln` is invocation-global, which is why `make sast` isolates
  the `tools/requirements-sast.txt` audit (source: `Makefile:252-265` and its
  comment, plus `pip-audit --help`)
- Process: `tools/audit-requirements.py` is listed in `SAST_CONFIG`
  (source: `Makefile:194`), so a diff touching it forces `gate-sast` to run — the
  change is validated by the gate it changes
- Process: this work is not part of `docs/specs/ci-gate-parallelization/`, which is
  `Shipped (2026-08-17)` and frozen, so it carries its own spec (source:
  `docs/specs/ci-gate-parallelization/spec.md:3`, user confirmation 2026-08-17)
- Product: the brief's stated target of `gate-sast` 158s → ~90s does not hold. Only
  seven of the ten `pip-audit` invocations in `make sast` are collapsible; CI pays
  about 7s each; and merge safety costs one extra invocation. The recoverable time is
  about 30s in CI (`gate-sast` 160s → ~130s) and about 36s locally (`make sast` 172s →
  ~136s) (source: timestamp attribution of `gate-sast` on run 32063058843 and of a
  local `make sast`, plus a measured two-invocation split at 25.1s, 2026-08-17)
- Process: a failing batch triggering a diagnostic per-file re-run is the accepted
  attribution mechanism — the green path pays nothing and the red path pays the old
  cost, on the reasoning that a red SCA gate is a stop-and-fix event rather than a hot
  path (source: user confirmation 2026-08-17)
- Process: a textual merge-safety guard is the accepted false-green defence, in
  preference to documenting a residual or asserting equivalence inside `make sast`
  (source: user confirmation 2026-08-17). The rule shipped here is **stricter** than
  the one put to the user: security review established that an upper bound narrows the
  merged resolution whether or not the bounded package is named in a second file,
  because it also constrains packages reached transitively, and that a narrowed
  resolution audits a strict subset of the per-file `(name, version)` pairs — so it is
  never louder, only quieter. The stricter rule closes that hole entirely at a
  measured cost of one extra invocation, about 14s.
