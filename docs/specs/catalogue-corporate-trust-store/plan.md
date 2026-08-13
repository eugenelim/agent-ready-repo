# Plan: catalogue corporate trust store

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change adds one new module and rewires one function.

`system_trust.py` is new and owns everything platform-specific: resolving trust
anchors from the environment, and — on macOS only — shelling to `/usr/bin/security`
to export administrator keychain certificates. It exists as a separate module
because `catalogue.py` documents "No subprocess calls anywhere in this module",
and that guarantee is worth keeping accurate rather than quietly breaking.

`catalogue.py::_fetch_and_extract` gains a two-attempt shape. Attempt one uses a
context built from the environment — identical to today's behaviour when no
variable is set, because `ssl.create_default_context()` is what `urlopen` already
uses. If and only if that raises `ssl.SSLCertVerificationError`, attempt two
retries against a context additionally carrying administrator keychain anchors,
after printing a notice to stderr. Any other error, and any failure of attempt
two, raises `CatalogueError` with remediation text.

The riskiest part is not the retry — it is *which* certificates the fallback
trusts. A blind keychain dump over-trusts relative to what the administrator
domain actually asserts (30 certificates dumped versus 12 with trust settings,
on the machine probed). The plan contains that risk two ways: the login keychain
is never read, and the anchors are *added* to the default store rather than
replacing it, so the fallback can only ever widen trust to certificates an
administrator installed. Honouring per-certificate "Never Trust" settings is
deferred, recorded, and called out for security review rather than hand-waved.

Order of operations: T1 (pure env resolution, no I/O) → T2 (keychain export,
subprocess boundary stubbed) → T3 (wire the retry) → T4 (error text + timeout)
→ T5 (docs) → T6 (end-to-end run against a real failing source).

## Constraints

- `docs/CONVENTIONS.md:1214` — networked primitives must honour
  `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `SSL_CERT_DIR`. This change exists
  because `catalogue.py` does not.
- `docs/CONVENTIONS.md:1201`, `:1218` — no `SSL_VERIFY=false` default, no
  `--insecure` default. No such flag is added.
- `packages/agentbundle/pyproject.toml:11` — `dependencies = []`. Stdlib only;
  `truststore` and `certifi` are both out despite solving part of this.
- `packages/credbroker/credbroker/_sso.py:702-726` — the in-repo reference for
  augment-not-replace precedence. Followed, including suppressing `OSError` /
  `ssl.SSLError` on a stale path so a fleet-wide stale variable cannot harden
  into a failure.
- `packages/agentbundle/agentbundle/catalogue.py:23` — the no-subprocess
  guarantee. Kept true by delegation, and the docstring updated to say so.
- `AGENTS.md` § Privacy — no certificate subject names, keychain contents, or
  proxy hostnames in any committed file, including test fixtures.

## Construction tests

**Integration tests:** `tests/integration/test_trust_fallback_tls.py` — a
throwaway certificate authority signs a `localhost` server certificate, so
attempt one fails real TLS verification exactly as an adopter behind an
inspecting proxy fails, and the authority then arrives through the same seam the
keychain populates. Covers: the failing premise, recovery, recovery from a dump
whose good certificate is surrounded by unparseable blocks, refusal under the
opt-out, and the explicit-`AGENTBUNDLE_CA_BUNDLE` route. Skipped when `openssl`
is unavailable, since generating an X.509 certificate needs a dependency this
package refuses; the unit suite still covers sequencing on those hosts.

Getting this test to pass surfaced a property worth recording: Python 3.13's
`create_default_context()` enables `VERIFY_X509_STRICT`, so the fixture CA needs
a Subject Key Identifier, `basicConstraints`, and `keyUsage`, and the leaf needs
an Authority Key Identifier. Three successive fixture failures looked exactly
like the bug under test before that was understood.

**Manual verification:** recorded in `notes/manual-qa.md`, which also lists what
was deliberately not exercised. Note the integration test above now carries the
recovery proof; the manual runs corroborate it against a real host.
- Resolve a `git+https://` source with `SSL_CERT_FILE` pointed at a zero-CA PEM,
  which reproduces the reported failure deterministically on any machine.
- The same with `AGENTBUNDLE_NO_SYSTEM_TRUST=1`, confirming the fallback stays
  dormant and the message says so.
- The same with `system_anchor_pem` stubbed to `None`, covering the non-macOS
  shape: no notice, one connection.

## Design (LLD)

Shape is `service`; the sub-sections below are the pruned set.

### Interfaces & contracts

`system_trust.py` exposes two functions and no class:

- `resolve_trust_paths(env) -> tuple[str | None, str | None]` — pure. Maps an
  environment mapping to `(cafile, capath)` under the precedence
  `AGENTBUNDLE_CA_BUNDLE` > `SSL_CERT_FILE` > `REQUESTS_CA_BUNDLE` for the
  file, `SSL_CERT_DIR` for the directory. Raises `CatalogueError` when
  `AGENTBUNDLE_CA_BUNDLE` names a missing path — deliberately louder than the
  other two, because it is the variable an adopter sets by hand for this
  feature, where a typo should be reported rather than absorbed. Satisfies
  AC 1, AC 3, AC 4.
- `build_context(env=None, *, system_anchors: str | None = None) -> ssl.SSLContext`
  — starts from `ssl.create_default_context()`, applies the resolved paths, and
  loads `system_anchors` PEM text when given. The anchors are passed **in** by
  the caller rather than fetched here, so the caller can establish whether a
  fallback is possible before announcing one. Asserts `check_hostname` and
  `verify_mode` before returning, so a future edit cannot silently weaken the
  context.

The subprocess boundary is injected as a module-level `_RUNNER` seam so tests
assert the argument vector without touching a real keychain. Satisfies AC 8.

### Data & schema

No persisted schema, and no on-disk artifact at all. The exported PEM is held in
memory and passed to `load_verify_locations(cadata=...)`; nothing is written to a
temporary file, so employer-identifying certificate material never rests on disk
and never reaches a log.

Environment surface added: `AGENTBUNDLE_NO_SYSTEM_TRUST` (opt-out, any truthy
value). Existing variables are read, not defined, by this change.

### Failure & resilience

| Condition | Behaviour |
| --- | --- |
| No variables, default store verifies | One connection; unchanged. AC 11 |
| `AGENTBUNDLE_CA_BUNDLE` missing path | `CatalogueError` naming the path. AC 3 |
| `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` stale | Suppressed; default store applies. AC 4 |
| Verify fails, keychain completes chain | Stderr notice, retry, success. AC 5, AC 6 |
| Verify fails, keychain does not help | `CatalogueError` with remediation. AC 12 |
| Verify fails, opt-out set | Original error, no retry. AC 7 |
| Non-macOS platform | No notice, no second connection; error names the platform. AC 14 |
| `security` absent or non-zero | Treated as "no anchors"; original error surfaces. |
| Proxy black-holes the connection | Timeout, not an indefinite hang. AC 13 |

Retry is bounded at exactly one additional attempt, and only for
`ssl.SSLCertVerificationError` — never for a timeout, DNS failure, or HTTP
error, so the change cannot turn a transient outage into doubled load.

### Quality attributes

Observability: the stderr notice is the only new output, and it is
unconditional when the fallback fires — a silent trust widening would be the
defect. Privacy: the notice names the host and the trust source, never a
certificate subject.

## Tasks

### T1 — `resolve_trust_paths` and `build_context` in a new `system_trust.py`

**Depends on:** none
**Mode:** TDD
**Implements:** spec Objective's explicit-bundle route; AC 1, 2, 3, 4, 9, 10.

**Tests:**
- `AGENTBUNDLE_CA_BUNDLE` wins over both `SSL_CERT_FILE` and
  `REQUESTS_CA_BUNDLE` when all three are set.
- `SSL_CERT_FILE` wins over `REQUESTS_CA_BUNDLE` when both are set, matching
  `credbroker`.
- `SSL_CERT_DIR` is returned as `capath` independently of the file precedence.
- A missing `AGENTBUNDLE_CA_BUNDLE` path raises `CatalogueError` naming it.
- A missing `SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` path does not raise, and
  the returned context still verifies a public host.
- The returned context reports `check_hostname is True` and
  `verify_mode is ssl.CERT_REQUIRED` in every branch, including the
  all-unset branch.
- A context built with a private-CA-only bundle still carries the public roots
  — asserted by certificate count strictly exceeding the bundle's own count,
  which is the augment-not-replace property.

**Approach:** `create_default_context()`, then `load_verify_locations` guarded
by `contextlib.suppress(OSError, ssl.SSLError)` for the inherited variables and
an explicit existence check for `AGENTBUNDLE_CA_BUNDLE`.

### T2 — macOS administrator keychain export

**Depends on:** T1
**Mode:** TDD
**Implements:** AC 5's anchor source; AC 8.

**Tests:**
- The argument vector contains `/Library/Keychains/System.keychain`, and **no**
  path containing `login`, and **no** path naming Apple's
  `SystemRootCertificates.keychain` (RFC-0086 D4).
- `sys.platform != "darwin"` returns no anchors without invoking the runner.
- A non-zero runner exit returns no anchors and does not raise.
- A runner returning no PEM block returns no anchors.
- A parseable certificate survives unparseable neighbours on either side of it,
  which is the property per-block loading exists for.
- No test asserts on real keychain contents, so the suite is machine-independent
  and no employer-identifying string enters a fixture.

**Approach:** `subprocess.run` behind the `_RUNNER` seam, `find-certificate -a -p`
against the administrator keychain, then load the returned PEM **one certificate
block at a time** via `load_verify_locations(cadata=...)`. No temporary file:
`cadata` takes an in-memory string, so employer-identifying certificate material
never rests on disk.

### T3 — two-attempt fetch in `catalogue.py::_fetch_and_extract`

**Depends on:** T1, T2
**Mode:** TDD, integration surface
**Implements:** AC 5, 6, 7, 11.

**Tests:**
- The integration test named under Construction tests above.
- With no variables and a verifying store, exactly one `urlopen` call is made
  (asserted on a counting stub) — the unchanged-behaviour guarantee.
- `ssl.SSLCertVerificationError` triggers exactly one retry; a
  `URLError(timeout)` triggers none.
- The stderr notice fires exactly once, names the host, and stdout stays empty.
- `AGENTBUNDLE_NO_SYSTEM_TRUST=1` suppresses the retry and re-raises the
  original error.

**Approach:** extract the `urlopen` + `tarfile` body into a local closure taking
a context, call it twice at most.

### T4 — remediation error text and fetch timeout

**Depends on:** T3
**Mode:** goal-based check
**Implements:** AC 12, 13, 14.

**Tests:**
- `Done when:` the `CatalogueError` raised on an unrepairable verification
  failure contains the words identifying probable cause and next action, and
  a raw `_ssl.c` fragment is not its only content — asserted by substring.
- `Done when:` `grep -n "timeout" packages/agentbundle/agentbundle/catalogue.py`
  matches the `urlopen` call.
- `Done when:` `catalogue.py`'s docstring names `system_trust.py` as the
  subprocess delegate.

### T5 — reference documentation

**Depends on:** T4
**Mode:** goal-based check
**Implements:** AC 15.

**Tests:**
- `Done when:` `guides/_shared/reference/agentbundle.md` documents the fallback,
  `AGENTBUNDLE_NO_SYSTEM_TRUST`, and that the trust variables apply to all
  source forms; and its `AGENTBUNDLE_CA_BUNDLE` row no longer implies the
  variable is Artifactory-only.
- `Done when:` `make build-self` is clean, so projected copies stay in sync.

### T6 — end-to-end run against a genuinely failing source

**Depends on:** T5
**Mode:** visual / manual QA
**Implements:** AC 16.

**Tests:**
- Run `agentbundle install` with `SSL_CERT_FILE` set to a zero-CA PEM, which
  reproduces the reported failure on any machine. Record stderr, exit code, and
  installed result in the PR.
- Repeat with `AGENTBUNDLE_NO_SYSTEM_TRUST=1` and record the unchanged failure.

## Risks

- **Over-trust relative to the administrator domain.** A certificate marked
  "Never Trust" is still loaded as an anchor. Bounded by never reading the login
  keychain and by augmenting rather than replacing; deferred as
  `catalogue-trust-store-trust-settings` and flagged for security review.
- **WSL adopters are not covered.** Windows itself needs no fallback — Python's
  `load_default_certs` loads the Windows `CA` and `ROOT` stores and honours each
  certificate's trust settings — but a WSL distribution reports `linux` and does
  not inherit that store, so an authority pushed to Windows is invisible inside
  it. Tracked as `catalogue-trust-store-wsl-diagnosis`; documentation and a
  targeted message, not a code path reaching across the boundary.
- **The fallback masks a genuine attack.** Mitigated by the unconditional stderr
  notice and by requiring administrator-installed material; an attacker who can
  write the administrator keychain has already won.
- **A second wall remains.** The archive fetch crosses `github.com` →
  `codeload.github.com`. An egress allowlist permitting only the former still
  fails, with a different error this change does not address. Called out so the
  PR does not over-claim.

## Changelog

- 2026-08-13 — Initial plan. Scope widened from "honour the documented
  environment variable" to "consult the OS trust store automatically" after the
  observation that the variable-only route requires an adopter to already hold a
  PEM path, which the affected population does not.

- 2026-08-13 — Review round 1 corrections. The adversarial pass found three
  confirmed defects, each verified by probe before fixing: (a) a stale
  `SSL_CERT_FILE` *empties* the default store rather than leaving it intact, so
  AC 4's original promise was false — the same mechanism this spec's own repro
  relies on; (b) `load_verify_locations(cafile=...)` loads **zero** anchors when
  any block in the PEM is malformed, while `cadata=` keeps what parsed, so the
  original file-based `_load_pem_text` could silently supply no anchors while
  the code announced a fallback — the rationale in its docstring was inverted;
  (c) the retry fired on platforms where `system_anchor_pem()` always returns
  `None`, making a pointless second connection and claiming anchors "did not
  complete the chain" when none were consulted — and the original test pinned
  that behaviour by stubbing the anchors to `None`. Anchor resolution moved
  ahead of the announcement, `build_context` now takes anchors as a parameter,
  and the affected tests were rewritten to assert the property rather than the
  call shape.

- 2026-08-13 — Security review corrections. `SystemRootCertificates.keychain` is
  no longer read: the retry context already starts from the public roots, so
  importing Apple's separately curated root program widened trust for no gain on
  the one fetch path with no post-transport integrity check. Measured on a
  corporate host, reading `System.keychain` alone produced the same anchor count
  as reading both, so nothing was lost. Anchor loading became per-block after a
  probe showed a combined `cadata=` load keeps zero anchors when the malformed
  block comes first — the same "announces a fallback that cannot happen" defect
  in a second form. Three exception-hierarchy holes closed (`TypeError` from
  non-ASCII `cadata`, `UnicodeDecodeError` from the strict-decoding runner,
  `TimeoutError` missing from the retry handler), the retry now clears a
  partly-extracted destination, and the verification-invariant scanner was
  widened to every shipped package with `check_hostname = False` and
  `CERT_OPTIONAL` added to its token list.

  Dropping Apple's keychain invalidated the original manual repro, which emptied
  the whole trust store rather than removing one root: with the store empty,
  `System.keychain` alone cannot verify a public host, so the artificial repro no
  longer demonstrates recovery. That gap is what motivated building the real-TLS
  integration test, which does not depend on the shape of the local trust store.
