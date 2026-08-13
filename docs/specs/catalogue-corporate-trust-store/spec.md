# Spec: catalogue corporate trust store

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0086 (decisions D1–D4)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter on a corporate laptop installs a pack from a `git+https://` catalogue
source and the install succeeds, even when their network runs a TLS-inspecting
proxy that re-signs `github.com` with a root CA their IT department manages.

The tool reaches this outcome without the adopter knowing what a PEM file is.
When the default certificate store cannot verify the connection, `agentbundle`
consults the administrator keychain their IT team already provisions,
announces on stderr that it did so, and continues. This is narrower than what
`curl` or Safari do: they evaluate every keychain and honour per-certificate
trust settings, while this reads one keychain and does not read those settings. Verification stays strict throughout: the fallback
adds trust anchors and never removes one, and no code path disables
verification or accepts an unverified peer.

An adopter or IT department that already holds a CA bundle gets a second,
explicit route: `AGENTBUNDLE_CA_BUNDLE`, `SSL_CERT_FILE`, `SSL_CERT_DIR`, and
`REQUESTS_CA_BUNDLE` are honoured on `git+https://` sources, so the variable the
reference documentation advertises finally works for the source form adopters
actually use. The `catalogue+https://` and `archive+https://` paths keep their
existing `AGENTBUNDLE_CA_BUNDLE`-only, replace-the-store behaviour; the
difference is documented rather than silently reconciled.

When verification still fails, the error names the probable cause and the next
action instead of surfacing a raw OpenSSL string.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep verification strict on every path: `check_hostname` on, `CERT_REQUIRED`,
  full chain validation. The fallback adds anchors; it never removes one.
- Announce the system-trust fallback on stderr every time it fires, naming the
  host and the trust source. A trust decision the adopter cannot see is a
  trust decision they cannot audit.
- Read trust material only from `/Library/Keychains/System.keychain`, the one
  store that requires administrator rights to write.
- Preserve today's trust decisions and connection count when no relevant
  environment variable is set and the default store verifies successfully. One
  deviation is intentional and is not "unchanged": passing an explicit context
  means a process-wide `ssl._create_default_https_context` override no longer
  reaches this fetch. That is a hardening, matching
  `credbroker/_sso.py:702-708`, which constructs its context for the same
  reason — a global override must not weaken the request that decides which
  code an adopter installs.

### Ask first

- Extending the fallback to a second platform (Windows via
  `ssl.enum_certificates`, or any Linux store beyond OpenSSL's defaults).
- Persisting a discovered CA bundle path into adopter configuration rather
  than resolving it per invocation.
- Changing `https_catalogue.py`'s existing replace-the-store semantics for
  `AGENTBUNDLE_CA_BUNDLE`, which are deliberate and are not in scope here.

### Never do

- Read the user's login keychain (`~/Library/Keychains/login.keychain-db`).
  It is writable without administrator rights, so a root landing there is not
  an IT trust decision.
- Read Apple's `/System/Library/Keychains/SystemRootCertificates.keychain`. The
  retry context already carries Python's default roots, so importing a second
  curated root program widens trust for no measured gain (RFC-0086 D4).
- Add an `--insecure` flag, a `verify=False` path, `CERT_NONE`, or any
  environment variable that disables verification
  (`docs/CONVENTIONS.md:1201`, `:1218`).
- Add a runtime dependency. `packages/agentbundle/pyproject.toml` declares
  `dependencies = []`; `certifi`, `truststore`, and `requests` are all out.
- Add a new top-level directory or module boundary outside
  `packages/agentbundle/agentbundle/`.
- Emit certificate subject names, proxy hostnames, or keychain contents into
  committed files, test fixtures, or fixture-shaped documentation. Those
  identify the adopter's employer (`AGENTS.md` § Privacy).

## Testing Strategy

- **Trust-anchor precedence and context construction: TDD.** A pure function
  mapping an environment mapping to a configured `SSLContext` has a
  compressible invariant, so it is specified by unit tests that assert
  precedence order, the augment-not-replace property, and that
  `check_hostname`/`verify_mode` are never weakened.
- **Keychain export and platform gating: TDD with a stubbed subprocess
  boundary.** The `security` invocation is injected so tests assert the exact
  argument vector — specifically that the login keychain never appears in it —
  without depending on the developer's own keychain contents.
- **Fallback retry sequencing: TDD, integration surface.** Verified across the
  `catalogue.py` → `system_trust.py` boundary with a local TLS server holding a
  throwaway self-signed CA: the first attempt fails verification, the fallback
  supplies the anchor, the retry succeeds. This proves the wiring end to end
  without depending on a real MITM proxy.
- **Error remediation text: goal-based check.** A `grep`-style assertion that
  the raised `CatalogueError` names both the probable cause and a next action.
- **Real-artifact install: visual / manual QA.** `agentbundle install` is run
  against a source whose verification fails under the default store, and the
  observed stderr notice, exit code, and installed result are recorded. A
  passing unit suite does not satisfy this.

## Acceptance Criteria

- [x] A `git+https://` catalogue fetch honours `AGENTBUNDLE_CA_BUNDLE`,
      `SSL_CERT_FILE`, `SSL_CERT_DIR`, and `REQUESTS_CA_BUNDLE`, with
      precedence `AGENTBUNDLE_CA_BUNDLE` > `SSL_CERT_FILE` >
      `REQUESTS_CA_BUNDLE` for the bundle file and `SSL_CERT_DIR` for the
      directory.
- [x] Anchors from those variables are added to the default store, so a bundle
      containing only a private CA still verifies the
      `github.com` → `codeload.github.com` redirect hop against public roots.
- [x] A non-existent `AGENTBUNDLE_CA_BUNDLE` path raises `CatalogueError`
      naming the path, matching `https_catalogue.py`'s existing behaviour.
- [x] A stale or unreadable `REQUESTS_CA_BUNDLE` path does not abort the
      fetch, and the default store still applies. A stale `SSL_CERT_FILE` or
      `SSL_CERT_DIR` empties the store instead — OpenSSL resolves its default
      paths from those variables, so the condition is not recoverable in this
      code and is documented as an operator error rather than handled.
- [x] When the default store raises `ssl.SSLCertVerificationError`, the fetch
      retries exactly once against a context augmented with administrator
      keychain anchors, and succeeds when those anchors complete the chain.
- [x] The fallback emits a single stderr line naming the host and that OS trust
      material was used. Nothing is written to stdout.
- [x] `AGENTBUNDLE_NO_SYSTEM_TRUST=1` disables the fallback. The original
      verification detail is still reported, the message states that the
      fallback was not attempted rather than that it failed, and it does not
      advise setting the variable the adopter has already set.
- [x] The keychain argument vector never includes a login keychain path, on any
      code path, asserted by a test that inspects the vector.
- [x] Every context the change constructs reports `check_hostname is True` and
      `verify_mode is ssl.CERT_REQUIRED`, asserted directly.
- [x] No code path constructs `CERT_NONE`, passes `verify=False`, or accepts
      an unverified peer, asserted by a test that scans the package sources for
      those tokens and fails on a match.
- [x] With no relevant environment variable set and a verifiable default store,
      the fetch performs exactly one connection and behaviour is unchanged.
- [x] A verification failure that the fallback cannot repair raises
      `CatalogueError` naming the probable cause (TLS interception) and a next
      action, without a raw `_ssl.c` string as the only content.
- [x] When no operating-system anchors are available (any non-macOS
      platform), no notice is printed and no second connection is made; the
      error names the platform and that the fallback covers macOS only.
- [x] Anchor material that fails to parse costs neither the default store nor
      the anchors that did parse.
- [x] The fetch passes an explicit timeout equal to
      `https_catalogue._HTTP_TIMEOUT`, so a black-holing proxy fails rather than
      hanging indefinitely.
- [x] A process-wide `ssl._create_default_https_context` override cannot weaken
      the fetch's verification.
- [x] `catalogue.py`'s module docstring describes the subprocess boundary
      accurately, naming `system_trust.py` as the delegate.
- [x] `guides/_shared/reference/agentbundle.md` documents the fallback, the
      opt-out variable, which source forms honour which variables, and the
      unrecoverable stale-`SSL_CERT_FILE` case.
- [x] `agentbundle install` is exercised end to end against a source that fails
      under the default store, and the observed stderr and exit code are
      recorded in the PR.
- [ ] Administrator "Never Trust" settings honoured (deferred: catalogue-trust-store-trust-settings)
- [ ] WSL adopters get guidance naming the Windows/distribution trust-store split (deferred: catalogue-trust-store-wsl-diagnosis)

## Assumptions

- Technical: the runtime is Python ≥ 3.11 and the package carries no runtime
  dependencies, so the fallback is stdlib-only (source:
  `packages/agentbundle/pyproject.toml:9,11`).
- Technical: the `git+https://` path honours no trust-store variable today;
  `SSL_CERT_FILE` works only incidentally through OpenSSL's default paths
  (source: probe — an empty PEM in `AGENTBUNDLE_CA_BUNDLE` left the fetch
  succeeding, the same PEM in `SSL_CERT_FILE` reproduced the adopter's error).
- Technical: a GitHub archive fetch crosses two hosts,
  `github.com` → `codeload.github.com`, so anchors must satisfy both (source:
  probe — redirect trace returned `302` to `codeload.github.com`).
- Technical: macOS trust *settings* are a separate store from the certificate
  dump, so `find-certificate -a -p` over-reports what the administrator domain
  actually trusts (source: probe — 30 certificates dumped from
  `System.keychain` against 12 reported by `dump-trust-settings -d`).
- Technical: `ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)` already sets
  `check_hostname=True` and `CERT_REQUIRED`, so the existing
  `https_catalogue.py` context is strict and needs no change (source: probe).
- Technical: `catalogue.py` declared "No subprocess calls anywhere in this
  module" before this change, so keychain access lives in a new sibling module
  and that docstring now names the delegation instead of claiming the module is
  subprocess-free by itself (source: `packages/agentbundle/agentbundle/catalogue.py`
  module docstring).
- Process: `--insecure` and `verify=False` defaults are forbidden and the three
  OpenSSL-family trust variables are required of networked primitives (source:
  `docs/CONVENTIONS.md:1201`, `:1214`, `:1218`).
- Process: `credbroker/_sso.py:702-726` is the in-repo reference for
  augment-not-replace trust-anchor precedence, and this change follows it
  (source: `packages/credbroker/credbroker/_sso.py:702-726`).
- Technical: macOS is the only platform where Python ignores the operating
  system trust store, so the fallback is macOS-only by necessity rather than by
  scoping choice. `ssl.SSLContext.load_default_certs` carries a `win32` branch
  that loads the Windows `CA` and `ROOT` stores through `enum_certificates`,
  filtering on each certificate's trust settings, and no `darwin` branch of any
  kind; Linux resolves through OpenSSL's default paths (source: probe —
  `ssl.py:515-534` read directly, and a grep for `darwin|keychain|SecTrust` in
  that file returns nothing).
- Technical: a WSL distribution reports `sys.platform == "linux"` and has no
  `enum_certificates`, so it does not inherit the Windows certificate store. A
  corporate authority pushed to Windows is invisible inside WSL until installed
  into the distribution, which is a documentation matter rather than something
  this fallback can repair (source: probe — `enum_certificates` absent off
  win32).
- Product: an install that repairs itself and says so is preferable to one that
  fails with a correct but unactionable error (source: user confirmation
  2026-08-13).
