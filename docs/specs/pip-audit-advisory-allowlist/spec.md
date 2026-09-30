# Spec: pip-audit-advisory-allowlist

- **Status:** Shipped
- **Owner:** repository maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) D8 (pip-audit is the SCA gate), [ADR-0083](../../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md) (the npm allowlist this mirrors), [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md) (a quiet scanner becomes a gate through a wrapper with a self-test), [ADR-0113](../../adr/0113-sast-guarantee-moves-from-the-local-gate-to-gate-sast.md) (`gate-sast` owns the scan)
- **Contract:** none <!-- the allowlist schema is CI-only gate configuration read by one repository script; no published interface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`make sast` exits 0 on a tree whose only known Python advisories are ones a
maintainer has accepted in writing, and the acceptance decays loudly rather than
quietly.

Right now the Python SCA leg is red on every pull request, including pull
requests that change nothing near it. Semgrep 1.178.0 — the latest release,
dated 2026-09-23 — declares `pyjwt[crypto]~=2.13.0`, which excludes the 2.14.0
release that fixes all ten currently-published PyJWT advisories. Nothing in this
repository can reach 2.14.0 while that pin stands, so there is no available fix:
a direct pin or a constraints entry produces an unsatisfiable resolve, not a
remediation.

The leg already carries one of those ten as a bare `--ignore-vuln
CVE-2026-102274` flag with its reasoning in a Makefile comment. That vehicle
does not scale to ten and, more importantly, it cannot fail. Its reasoning is
prose beside a flag; nothing checks that the retirement condition has not
already fired, or that a later author did not append an eleventh id without
writing anything at all. `tools/audit-npm.py` solved this same problem for the
npm leg under ADR-0083, and its allowlist header already names this leg's
`--ignore-vuln` flags as the weaker sibling.

This spec moves the Python leg onto that pattern and adds the thing the npm
allowlist does not have: **the suppression's own expiry is a gate failure, not a
documented obligation on the next author.** ADR-0102 records the absence of that
detector as its known weakness — "a trigger with no detector is aspirational" —
and accepts it there because re-scanning excluded paths would reintroduce the
cost the exclusion exists to avoid. No equivalent cost applies here: the audit
already enumerates every advisory on every run, so an entry that has stopped
matching is free to notice.

ADR-0102 is cited for that reasoning only. It governs `SEMGREP_EXCLUDE`
path-scoped exclusions — a different control on a different leg — and does not
govern a `pip-audit` suppression. Nothing currently does, which is why AC9 asks
for a record.

### What this spec does not mechanize, and why

The acceptance rests on a reachability claim: no code path under `make sast`
reaches PyJWT's entry points. **No check in this spec establishes that claim,
and this spec does not try to.**

An earlier draft specified a mechanical evidence pin over the file set
referencing `jwt`. It was removed after review showed the oracle could not
perform the comparison the criterion claimed: a call-path change inside an
already-approved file moves no file set, the walk's natural scope missed a
second PyJWT call site in `mcp` inside the same audited closure, the walked
artifact is not the resolved one, and the approved set churns on any in-range
Semgrep release. A proxy that cannot see the failure it names is worse than an
absent check, because it manufactures assurance.

The claim is therefore recorded for what it is: a **human-verified, dated,
version-stamped finding** in AC9's ADR, covering the whole audited closure, with
a named owner and a re-verification obligation. What remains mechanical is the
part that can be: whether the advisories are still being reported, and whether
the fix has arrived.

## Boundaries

### Always do

- Keep the decision to suppress **per advisory id, scoped to one package**, and
  make each entry's written reason address that advisory's own trigger. The ten
  advisories span signature forgery, JWKS-fetch abuse, a revocation bypass and
  two availability bugs; they do not share one reachability sentence, even when
  the same fact happens to dispose of all of them.
- Print every active suppression on every run, with the package it was accepted
  for, and mark any match made only through an alias.
- Fail the gate when an allowlist entry stops matching **and the evidence shows
  the fix arrived**. An accepted risk that has silently expired is the failure
  mode this spec exists to prevent.
- Keep the three evidence states apart — fix arrived, fix absent, nothing
  audited for that package. They look identical at the entry level and have
  different remedies, and only one of them justifies deleting a written record.
- Fail closed on every path where the gate cannot render a verdict, and prefer
  the safe branch whenever evidence cannot be ordered or parsed.
- Treat the allowlist file as untrusted data: a malformed entry, or an entry
  naming a package outside the file's own declared allowed set, is a tool error.
- Keep every new `tools/` file pure-stdlib Python per `tools/AGENTS.md`.

### Ask first

- Adding a package to the allowlist's declared allowed-package set.
- Extending the allowlist to a manifest other than `tools/requirements-sast.txt`.
- Changing what blocks: every non-allowlisted advisory blocks, at every severity.

### Never do

- Widen `SEMGREP_EXCLUDE` for this. It is a different control on a different
  leg, and the Makefile says so.
- Suppress by package, by severity band, or by anything coarser than a single
  advisory id scoped to a single package.
- Pass `--ignore-vuln` for an id the allowlist does not carry.
- Make the SCA leg non-blocking, or remove it from the gate chain, to get past
  these advisories.
- Accept an advisory on the grounds that CI is red.
- Instruct a maintainer to delete a written acceptance on evidence that does not
  establish the fix is present.
- Claim, in a criterion or a message, a property the check does not compare.

## Acceptance Criteria

Each criterion names the failure mode it excludes, because a criterion that
omits its failure mode cannot be falsified. Every criterion below governs the
**wrapper process** `tools/run-pip-audit-gate.py`; the surrounding Makefile
recipe keeps its own existing guard exit codes.

- [x] **AC1 — the gate passes on an accepted tree.** `make sast` exits 0 when
  the only advisories the Python leg finds are the ten allowlisted PyJWT
  entries. *Excludes: the leg is red on every pull request and the whole SAST
  guarantee gets routed around.*

- [x] **AC2 — an undocumented or out-of-bounds entry is a tool error.** The
  wrapper exits 2, naming the offending entry, when any entry has a missing,
  non-string or blank `id`, `package`, `fixed_in`, `reason` or
  `unblocked_when`; when `allow` is not an array of tables; when `allowed_packages` is absent, is
  not a list, or holds a non-string; or when an entry's `package` is outside
  that list. The list's own shape is checked because a bare string would turn
  the membership test into a substring match, which is the widening the field
  exists to prevent.
  *Excludes: the allowlist decaying into an undocumented mute list, and the
  vehicle silently widening from one transitive package to any dependency
  without that widening being a visible edit.*

- [x] **AC3 — a non-allowlisted advisory still blocks.** Any advisory not
  matched by an entry causes exit 1 and is printed, at every severity, for every
  package. An entry matches only when the advisory's primary `id` equals the
  entry's `id` **and** the reporting dependency's name equals the entry's
  `package`, both under PEP 503 canonicalisation. Aliases are not a match path.
  *Excludes: a wrapper that mutes more than it was asked to — an id collision or
  a mis-copied entry suppressing an advisory in a dependency nobody accepted
  while the printed line still says `pyjwt`; a correctly-spelled `PyJWT`
  matching nothing because the report canonicalises and the entry does not; and
  an acceptance growing to cover a new advisory that merely lists an accepted
  one among its aliases. Measured on the live feed: `pip-audit` with its default
  `pypi` service returns each of the ten with its CVE as the primary `id` and a
  single GHSA alias, so matching on the primary id costs nothing and an alias
  branch would only widen.*

- [x] **AC4 — only a real retirement reads as one.** When an entry's advisory is
  absent from the report, the wrapper exits 2 and prints one of three messages,
  chosen by evidence:

  | Evidence | Message | Says remove? |
  | --- | --- | --- |
  | Package present, resolved version orderable and >= `fixed_in` | the retirement condition has fired | yes |
  | Package present, the two versions compare as fix-not-yet-reached | the advisory is absent but the fix is not | no |
  | Package present, either version not orderable | the versions could not be compared | no |
  | Package absent from the report entirely | nothing was audited for this package | no |

  A permanently absent advisory — one the feed has withdrawn — is the one case
  where removing the entry is correct even though no fix shipped. The message
  for rows 2 and 3 names that possibility and the sanctioned remedy: confirm
  against the feed, then either keep the entry or remove it with a note in
  AC9's record. That is a maintainer decision, never the gate's instruction.

  *Excludes two failures at once: the aspirational-trigger failure ADR-0102
  records, where the suppression outlives its cause with nothing to notice; and
  its mirror, where a degraded advisory feed or a truncated resolve reads as ten
  fired retirement conditions and a maintainer following the gate's own
  instruction deletes ten written acceptances for a cause that was never true.*

- [x] **AC5 — `fixed_in` cannot drift or disable the detector.** While an
  entry's advisory is still being reported, the wrapper exits 2 if the entry's
  `fixed_in` matches no entry in that advisory's reported `fix_versions` under
  the same numeric-tuple rule below, not under string equality — pip-audit emits
  PEP 440-normalised version strings, so a hand-written `2.14` and a published
  `2.14.0` are the same version and must compare equal. A membership test that
  cannot be decided takes AC4's safe branch rather than erroring. **Version
  comparison is defined once, here, and both AC4 and AC5 use it**: each side
  must match a dotted all-numeric release (`^\d+(\.\d+)*$`); the two are split
  on `.`, converted to integers, and the **shorter is zero-padded to the longer
  before comparing**, so `2.14` and `2.14.0` are equal and `2.9.0` is below
  `2.14.0`. Zero-padding is the load-bearing half: a bare tuple comparison makes
  `(2, 14)` and `(2, 14, 0)` unequal and would fail a published version against
  the same version written with fewer segments. Any side not matching the
  pattern — a pre-release, a local version, an epoch, a non-numeric segment — is
  "not orderable" and takes AC4's safe branch.
  *Excludes: an entry written with an unreachable `fixed_in` — carelessly or
  deliberately — that suppresses today and can never reach the retirement
  branch, which would reintroduce the exact aspirational-trigger failure through
  the field AC4 depends on; and a naive string or tuple comparison ordering
  `2.9.0` above `2.14.0`, or a pre-release above its own release, and thereby
  instructing deletion of a record on evidence the fix is absent.*

- [x] **AC6 — an unaudited tree is not a clean one.** The wrapper exits 2,
  naming what is wrong, when the report carries any dependency with a
  `skip_reason` (pip-audit's skipped-dependency shape, which has no `vulns`
  key), or when any direct requirement of the manifest under audit is absent
  from the report's audited, non-skipped dependencies. The floor is derived from
  the manifest passed on the command line, not from a hard-coded path, and a
  derivation yielding an empty set is itself exit 2. **The wrapper does not pass
  `--strict`**: in pip-audit 2.10.1 `--strict` calls `_fatal()` on the first
  skipped dependency inside the audit loop (`_cli.py:555-558`), exiting before
  any formatter runs, so the skipped dependency never reaches the JSON and the
  only record of its name is a stderr log line. Omitting the flag is what makes
  the skip visible in the report at all. *Excludes: an unaudited dependency
  partitioned into the clean half; a resolve that falls below the manifest's own
  direct requirements; and a floor that silently empties — an unreadable or
  reshaped manifest yielding no names would otherwise let every report pass. A
  count-greater-than-zero floor would not exclude the second. **Does not
  exclude** a resolve that keeps all three direct requirements but loses or
  shrinks the transitive closure beneath them: the floor compares names in the
  manifest, not the closure, so an unaccepted transitive package carrying an
  advisory could drop out and read as clean. That residual is narrowed by AC7,
  which removes the ambient-constraint vector, and by a manifest edit being a
  tracked, reviewable change — but it is not closed, and AC9's record names it. Recorded as live
  weaknesses in `docs/specs/pip-audit-batching/spec.md` (`sca-no-strict-flag`,
  `sca-audited-set-has-no-floor`); this closes them for this invocation, by a
  different mechanism than `--strict`.*

- [x] **AC7 — no ambient configuration can re-aim the resolve or the feed.**
  The pip-audit subprocess runs under a bounded timeout and with an environment
  built to a stated rule, not a list: every variable whose name begins `PIP_` is
  removed (covering pip's option mapping and pip-audit's own `PIP_AUDIT_*` feed
  and service knobs), **except** `PIP_CONFIG_FILE`, which is *set* to
  `os.devnull` rather than removed — removing it would re-enable the very files
  it can suppress. The transport names are removed in **both cases**:
  `HTTP_PROXY`/`http_proxy`, `HTTPS_PROXY`/`https_proxy`, `ALL_PROXY`/`all_proxy`,
  `NO_PROXY`/`no_proxy`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`,
  `SSL_CERT_FILE`, `SSL_CERT_DIR`. A timeout exits 2. The envelope is stated in
  the wrapper: `PATH`, `PYTHONPATH` and pip's cache directory remain outside it.
  *Excludes: `sca-ambient-env-can-green-the-gate` — a stale export or an
  on-disk `pip.conf` re-pointing the advisory feed, the index, or the resolved
  version that AC4's branch and AC5's cross-check both read, to a green result
  at exit 0 without touching a tracked file — and `sca-no-timeout-on-pip-audit`.
  A three-name list would not exclude it: `PIP_CONSTRAINT` alone re-aims the
  resolved version, `/etc/pip.conf` is reachable by no environment scrub, and
  `urllib`'s proxy lookup case-folds and prefers the lowercase names.*

- [x] **AC8 — a tool failure is neither a clean gate nor a finding.** Exit 1
  means one thing only: at least one advisory no entry covers. Every other
  non-success — network, resolver, unparseable output, absent binary, timeout,
  malformed allowlist, retired or undecidable entry, skipped dependency, missing
  direct requirement, or an unhandled exception inside the wrapper itself —
  exits 2. pip-audit's own return code is read as follows: 0 or 1 with parseable
  JSON on stdout proceeds to evaluation, because 1 is what a normal run returns
  once any advisory is found and the wrapper passes no `--ignore-vuln`; any
  other return code, or unparseable stdout at any return code, is exit 2. Where
  both an exit-2 condition and an uncovered advisory are present, exit 2 wins
  and both are printed. *Excludes: a resolver outage reading as a
  pass; a wrapper crash reading as a blocking advisory and sending the reader to
  look for a vulnerability that is not there; and a report that is both
  untrustworthy and non-clean being reported only as non-clean.*

- [x] **AC9 — the vehicle and the residual have a governing record.** An
  accepted ADR states that a `pip-audit` advisory suppression is a legitimate
  vehicle, fixes its required shape, records the ten acceptances, and names the
  owner who retires them. It records the reachability finding as evidence a
  reader can re-verify: the concrete call paths (`jwt.PyJWKClient` and
  `jwt.decode` in `semgrep/mcp/utilities/token_verifier.py`, reached only via
  `make_token_verifier` → `setup_mcp_server` in `semgrep/commands/mcp.py`, the
  `semgrep mcp` subcommand; and `jwt.encode` in
  `mcp/client/auth/extensions/client_credentials.py`, reached only through
  private-key-JWT client authentication), the distributions walked, the versions and
  the date walked, **and the versions the audit resolves**, naming the delta
  when they differ — `pip-audit -r` resolves the newest version each range
  allows, so the walked tree is routinely not the audited one. It states the
  envelope explicitly: the acceptance covers the `make sast` invocation, and a
  contributor running `semgrep mcp` from the same install is outside it. It
  records two residuals — that no check in this repository verifies the call
  path, and that reviewer attention is the only anchor on the allowlist file.
  The record states that accurately: this repository has no CODEOWNERS file,
  and `CONTRIBUTING.md:263-278` lists CODEOWNERS-driven review routing among
  above-Profile-C measures to adopt "when the friction of *not* having them
  exceeds the friction of adopting them" — conditional sizing guidance, not a
  decision to decline. Adopting it for one file is a judgment this change does
  not make. *Excludes: a suppression whose
  only authority is the diff that added it; a residual that exists only in a
  reviewer's head; and a later reader who cannot tell what was checked, against
  what version, or where the acceptance stops.*

- [x] **AC10 — each reason addresses its own advisory.** Every entry's `reason`
  states that advisory's trigger and why this invocation cannot reach it. The
  one advisory rated CRITICAL by its published CVSS v3.1 base vector —
  CVE-2026-102268, `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` — carries its own
  statement rather than inclusion in a list. CVE-2026-102267 and CVE-2026-101917
  fire on a JWKS fetch with no JWT involved, and state the narrower premise that
  actually carries them: no `PyJWKClient` is constructed on this path. Reasons
  address `mcp`'s `jwt.encode` call site as well as semgrep's, since both are in
  the audited closure. *Excludes: a group-level residual that reads as diligence
  while having been checked against nothing; a criterion no reviewer can
  falsify because it names neither the advisory nor the severity's source; and a
  residual argued only against the distribution that was noticed first.*

- [x] **AC11 — every surface describing this recipe moves with it, and the
  carve-out has a real owner.** Updated in the same change: the recipe assertion
  in `tools/test-audit-requirements.py`; `MAKE_BASELINE_DIGESTS` in
  `tools/test_local_ci_shared_test_deduplication.py` for every surface that
  moved; the falsified clauses of the SAST paragraph and its self-test table in
  `docs/architecture/verification-graph.md`; the `tools/test-all.py` roster; and
  the stale `--ignore-vuln` counts in `tools/npm-audit-allowlist.toml` and
  `tools/audit-requirements.py`, whose last referent this change removes. The
  residual for the pip-audit invocations this change does **not** harden is
  registered in `workspace.toml [backlog].open`. The digest re-pin is confirmed
  confined to the surfaces this change edits. *Excludes: a false GATES failure
  read as unrelated; a byte pin bumped without checking what else moved; an
  architecture document describing the gate as it was; a comment pointing at a
  flag that no longer exists; and an Out-of-scope carve-out resting on backlog
  slugs that are not in the register — verified absent from `workspace.toml`,
  present only in an Archived spec that claims they were recorded.*

## Testing strategy

**AC2–AC8 — TDD, self-test entry point.** `tools/test-run-pip-audit-gate.py`, a
standalone hyphenated entry point per `tools/AGENTS.md`. It drives the wrapper's
decision function against synthetic pip-audit JSON and synthetic allowlists, so
no case needs the network or a real resolve. Each case asserts the exit code
**and** that the message names the entry, advisory or dependency, because an
exit code alone does not tell a contributor what to do. The env-scrub case
asserts the computed child environment, which is the observable available
without spawning.

**AC1 — goal-based check.** `make sast` exits 0. Recorded as observed output.

**AC9, AC10 — reviewer-checked.** `security-reviewer` is the intended reader for
AC10: the question is whether each reachability claim actually disposes of its
advisory's trigger. That review runs **after** the allowlist file exists, since
there is no reason text to read before it.

**AC11 — goal-based check.** Each anchor suite runs directly; the digest re-pin
is verified by reproducing all eight extracted Makefile surfaces and confirming
only the intended ones moved; a search for `--ignore-vuln` returns no prose
describing a flag that no longer exists; the new backlog slug resolves.

## Out of scope

- Fixing the advisories. There is no reachable fix while Semgrep pins
  `pyjwt[crypto]~=2.13.0`; this spec governs the acceptance, not a remediation.
- Mechanically verifying the reachability claim. Removed under review and
  explained above; AC9 owns it as a dated human finding instead.
- Running Semgrep from a pinned container or vendored install. That would move
  the SCA surface into an image rather than resolve it, and changes how every
  contributor runs the gate. Considered and declined, not deferred.
- Hardening the **other** pip-audit invocations in the recipe. AC6 and AC7 close
  their weaknesses for the new invocation only, so it is not born carrying a
  known silent-false-pass path. AC11 registers the remainder as a backlog item
  with an owner, because the slugs the archived spec refers to are not in the
  register.
- Adopting CODEOWNERS. No CODEOWNERS file exists here, and
  `CONTRIBUTING.md:263-278` treats it as an above-Profile-C measure to adopt on
  felt friction rather than as a precaution. Introducing it for one file is a
  repository-sizing judgment outside this change; `allowed_packages` is the
  in-file substitute.
- Migrating the `SEMGREP_EXCLUDE` entries or the Bandit suppressions.
- Amending ADR-0083's "four live `--ignore-vuln` entries" sentence. That count
  is already wrong at HEAD, where one flag remains; amending an accepted ADR is
  its own governance act. AC9's ADR records the stale reference instead.
- Any behavioural change to `tools/audit-npm.py` or `tools/audit-requirements.py`.
  Only their stale comment counts are corrected, under AC11.

## Changelog

- 2026-09-29 — Drafted.
- 2026-09-29 — Revised from adjudicated pre-EXECUTE review round 1.
- 2026-09-29 — Shipped. All eleven criteria met; `make sast` exits 0. Execution
  observations, including two task-row exit-code mis-predictions and six
  defensive behaviours added under post-gates review, are in
  [`notes/verification-ledger.md`](notes/verification-ledger.md) rather than
  here: no settled decision was falsified, so neither approved artifact needed
  a controlled amendment.
- 2026-09-29 — Revised from pre-EXECUTE review round 2. The mechanical
  reachability pin was **removed** on an explicit owner decision after it
  produced four blockers and three concerns across two rounds without
  converging, including a missed PyJWT call site in `mcp` inside the audited
  closure; the claim it proxied is now a dated, closure-wide human finding owned
  by AC9's ADR. AC4 split into a three-outcome branch table; AC5 added to stop
  `fixed_in` drifting or disabling the detector, with stated comparison
  semantics; AC6 switched to `--strict` and to flooring on the manifest's own
  direct requirements; AC7's scrub restated as a rule after `PIP_CONSTRAINT` and
  the transport names were shown to escape the old list; AC8 given an explicit
  exit precedence; AC3 given PEP 503 canonicalisation and alias visibility; AC11
  extended to the backlog registration, after the four slugs it relied on were
  verified absent from `workspace.toml`.
