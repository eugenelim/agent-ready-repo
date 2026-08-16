# 2026-08-16 Experimental round 3

This note records the third RFC-0088 Experimental run. It is authoritative over
the round-2 headline verdicts where the two disagree. The
[2026-08-16 rerun note](2026-08-16-experimental-rerun.md) and its
[evidence archive](experimental-rerun-evidence-archive.md) are preserved
unchanged as the audit trail for that run; nothing there is rewritten.

The run closed the named remaining gates for S1, S2 and S5, and advanced S3 and
S4 without closing either. Two site-controlled egress channels and one platform
row remain open, two RFC clauses are now known to be wrong as written, and the
S4 gate's own text needs an approver decision before that spike can close.

Every verdict below survived a destination review round that rejected an earlier
draft of this note. That round found tautological predicates, hard-coded
literals standing in for measurements, and a privacy defect in the promoted
archive. All are recorded in [Fixture defects corrected during this run](#fixture-defects-corrected-during-this-run)
rather than quietly repaired, because several of them changed conclusions.

## Reproduction identity and integrity

- Repository ref: `6d84f380` (`docs(rfc): promote RFC-0088 Experimental rerun evidence (#955)`)
- Host: macOS 26.5.2 build 25F84, Darwin 25.5.0, arm64
- Node 26.4.0; npm 11.17.0; Python 3.13.13
- Playwright 1.62.0 from a frozen lock; lock SHA-256
  `99fcdaedf22515c7a416c957beae73e782780430e85ab4d7ae195660cec25ed0`
- Browser channels: bundled Chromium 151.0.7922.34 (Playwright revision 1234)
  and system Google Chrome 151.0.7922.138, each **measured** from
  `browser.version()` rather than assumed from the requested channel
- Chromium payload: revision-directory tree SHA-256
  `b10ac1c882c2fa58a3b73d021807359c0506da21a43eb3381f943f7bfabbbe40`
  over 334 files and 372,014,615 bytes. The launcher executable is a separate
  52,112-byte stub with its own digest; the tree digest is the payload one.
- Scanner: Trivy 0.72.0; database downloaded 2026-08-16T06:13:58Z from
  `mirror.gcr.io/aquasec/trivy-db:2`; database-file SHA-256
  `d3165081410e0c6c5771d371b3068f6fa8748f4086c7f9545c50685c87b91335`
- S4 candidate artifact: `agent-browser` 0.34.0, registry integrity verified,
  installed with `--ignore-scripts`. Its `darwin-arm64` binary is **not**
  statically inspected and is not part of the promoted archive.
- Promoted package: [`round3-evidence-archive.md`](round3-evidence-archive.md)
  — 40 manifested files, archive SHA-256
  `d13ed745df4cce3d571c2c2e69886973044ac6e2871942db9b481fbc807ee689`.
  The archive ships `build-archive.py`, `verify-note-figures.py` and
  `run-all.sh`, so the privacy gate, the figure check and the run order are all
  auditable and re-runnable rather than taken on trust.

All sites, pages, cookies, downloads, identity candidates and profiles were
synthetic and loopback-only. No live account, personal browser profile or real
credential was used. Chromium's own background traffic did attempt non-loopback
egress; the broker proxy refused it, and those refusals are visible in
`s3/s3-proxy-decisions.json`.

Every promoted observable passes a redaction step, and `build-archive.py` —
itself a manifested member, so the gate is auditable — enforces it: the build
fails on any home directory, path-mangled account name, per-user temporary
path, uid-bearing temporary root, hostname, or key material. Three members name
those strings as their own detection *patterns* (`s1/redact.mjs`,
`s2/supply-chain-policy.py`, `build-archive.py`); each carries a per-file
exemption for the exact bare literal only, never a whole-file pass, so a real
path appended to one of them still fails. Both directions were negative-tested:
injecting `/Users/someuser/secret` into a results file failed the build with
exit 2, and appending `/Users/realperson/private` to an *exempted* file failed
it too.

No key material or third-party tree is reachable from the evidence root. The
WebSocket fixture generates its self-signed pair into a temporary root outside
the tree and deletes it at teardown, and `inspect-candidates.py` installs
candidate trees — two of which carry a Critical dependency finding — outside
the tree as well.

## Reproduction procedure

**Prerequisites** — macOS arm64; Node 26.x; Trivy 0.72.0 with a database no
older than 24 h (the freshness row cannot reproduce after 2026-08-17); system
Google Chrome for the `chrome` channel rows; `openssl` for the TLS fixture,
which the WebSocket server generates on demand; and, for the S4 rows only, a
separately installed `agent-browser@0.34.0` at the pinned version, scanned
before any candidate process runs.

Reconstruct the archive with the procedure in
[`round3-evidence-archive.md`](round3-evidence-archive.md), then from the
reconstructed root:

```bash
unset PLAYWRIGHT_DOWNLOAD_HOST PLAYWRIGHT_CDN_MIRROR PLAYWRIGHT_DOWNLOAD_CONNECTION
npm ci --ignore-scripts                      # reproduces the scanned tree from the frozen lock
npx playwright install chromium
node s1/s1-lifecycle.mjs bundled 1           # repeat for bundled|chrome x 1|2
node s3/s3-egress.mjs
node s3/s3-transports.mjs
node s3/s3-webrtc-mitigation.mjs
node s2/s2-integrated.mjs
python3 s2/supply-chain-policy.py
node s5/s5-round3.mjs
python3 s4/inspect-candidates.py             # installs candidates into an isolated tree
AB_BIN=<inspected-binary> node s4/webrtc-probe.mjs
AB_BIN=<inspected-binary> node s4/execute-agent-browser.mjs
python3 verify-note-figures.py <note.md> <rfc.md>   # figures must match the artifacts
```

Every driver exits non-zero when a row it asserts fails. The two S3 drivers do
this by declaring the disposition each row established, so a regression — a
connected-address pin that stops preventing, a download escape that succeeds —
changes the observed disposition and fails the run rather than producing a
green log. `verify-note-figures.py` closes the same loop for prose: it derives
every load-bearing figure in this note from the results files and exits
non-zero if the note disagrees. The two candidate dependency scans inside
`inspect-candidates.py` are *expected* to find blocking vulnerabilities; that
is a recorded result, not a script failure.

**Network access is required** for `npm ci`, `npx playwright install`, the
controlled-vulnerable lock fixture and the candidate installs: `registry.npmjs.org`,
`cdn.playwright.dev` and the Trivy database mirror must be reachable. Only the
*fixture services* are loopback-only.

## Current spike state

| Spike | Round-3 verdict | What closed | What remains open |
| --- | --- | --- | --- |
| S1 | **Pass on the named gates** | Lifetime-based attachment expiry, forced detach at expiry, seeded dead-owner recovery, seeded live and ambiguous ownership refusal, and signature-matched typed refusals: 12 asserted rows passing, twice on each of two measured channels | The bind endpoint is a bearer credential: a never-authorised second local client attached inside an open window, and no per-attachment authorization hook exists. D7's single-use claim is withdrawn. The initial OS/browser support matrix is an approver decision |
| S2 | **Pass on the named gates** | A separate child host receives native host-owned Playwright objects, is denied child processes, out-of-allowlist reads and writes, native addons, worker threads, **and a direct read of the live browser profile**, and returns valid and invalid outputs to parent-owned closed-schema validation and two-phase release. 16 of 18 supply-chain policy checks met | The RFC's "network restrictions" clause is unachievable as written. Two declared residuals: no vendor signature manifest ships with the browser payload, and the download host is verified only at the installer's own resolution, not at connection level |
| S3 | **Partial** | Connected-address enforcement and DNS-rebinding prevention at a broker-owned proxy with a valid unpinned control; bounded redirect chains with per-hop revalidation; request-client origin policy; Service-Worker-handled page requests; real-download confinement including a symlink-through target; WSS interception with canonical `ws`→`http` / `wss`→`https` mapping | WebRTC and WebTransport egress are not prevented by any control tested. Method policy is unenforceable at the connection point. Linux proxy behaviour untested. Every proxy-based verdict was measured under a deliberately **inverted** loopback-only destination rule |
| S4 | **Partial** | Every exact candidate has a reviewed disposition resting on measured facts. The one candidate clearing the blocking dependency scan executed under a sanitized environment whose construction was verified via a stand-in child, replacing the round-2 tainted row. Playwright is retained provisionally | The gate's own text admits to execution only candidates that "clear inspection" and holds S4 open until those pass the common corpus. The static surface screen was shown **non-discriminating**, and the common S1/S3 lifecycle and crash-recovery corpus was not run. The approver must amend the gate text or commission the corpus |
| S5 | **Pass** | Host-owned candidate presentation, confirmation, rejection and discard of clear evidence, asserted against six sinks that were actually written to, two of them read back from disk; validation-surface absence asserted as a positive subset; every single-field grant mismatch refused ahead of a **real** browser launcher; eight residue classes partitioned with an explicit architectural disposition | Nothing for this gate. The disposition is that per-consumer isolation is **not** viable within one `BrowserContext`, which confirms rather than removes connection-wide trust |
| S6 | **Pass, unchanged** | — | Convention amendment still waits for acceptance |

No result authorizes acceptance or implementation.

## S1 — persistent bind lifecycle

Common precondition: Playwright 1.62.0, a fresh generated profile, a synthetic
page, and one of the two measured channels. Every row ran twice per channel.
Refusal rows accept only a signature-matched failure kind from a closed table;
anything matching no declared signature classifies as `unrecognized-failure`
and cannot satisfy an expectation. One row is marked **recorded** rather than
passed: it captures an observation and has no target, so it does not count
toward the asserted total.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S1-CHANNEL-IDENTITY` | Launch requested on a named channel | Read `browser.version()` from the launched owner | The requested browser actually launched | `151.0.7922.34` bundled, `151.0.7922.138` system Chrome | Pass — `s1/s1-*-results.json` |
| `S1-STALE-LOCK-RECOVERY` | `SingletonLock` seeded to `<host>-<dead-pid>`, companions present | Broker inspects the link without following it, then acquires | `stale`, typed `stale-lock-recovered`, lock and companions removed | Exactly that; `readlink` used, `followed:false` | Pass — same |
| `S1-LIVE-LOCK-REFUSAL` | Lock seeded to a demonstrably live pid | Broker inspects and attempts to acquire | `live`, typed `broker:ambiguous-ownership`, lock intact | Typed refusal, lock intact | Pass — same |
| `S1-AMBIGUOUS-LOCK-REFUSAL` | Lock seeded to another hostname | Broker inspects and attempts to acquire | `ambiguous(lock-owned-by-other-host)`, typed refusal, no deletion | Typed refusal, lock intact | Pass — same |
| `S1-LOCK-TARGET-NOT-FOLLOWED` | Lock seeded to an absolute path outside the profile | Broker inspects and attempts to acquire | A target carrying a path separator is refused; the named file is never opened or deleted | `lock-target-not-hostpid`; bait file intact | Pass — same |
| `S1-ATTACH-BEFORE-EXPIRY` | Bound with a 2000 ms lifetime | Client attaches and reads the live page title | Attachment observes the same live context | Title `s1-round3` returned | Pass — same |
| `S1-UNAUTHORIZED-SECOND-ATTACH` | One attachment already established in the same window | A second, never-authorised client connects with the same endpoint | Record whether the window authorises per attachment or only per bind | Second client connected | **Recorded — control gap, not a pass** — same |
| `S1-BROKER-RESPONSIVENESS` | Broker owns the browser and holds a bind window | A 25 ms heartbeat samples its own scheduling lag across launch, bind, attach, expiry | Max lag under a 750 ms bound | Worst max lag 37 ms across the four runs, over 143–177 samples each | Pass — same |
| `S1-ATTACHMENT-LIFETIME-EXPIRY-FIRED` | Bind window opened with an explicit lifetime | Wait past the lifetime without calling unbind from the test body | The broker timer expires the window on its own | Expired at the timer, `unbindError: null` | Pass — same |
| `S1-ATTACH-AFTER-EXPIRY-REFUSED` | The same endpoint string that attached successfully before expiry | A new client attaches after the timer fired | Signature-matched typed refusal, not any error | `attachment-endpoint-unavailable` via `SIG-ENDPOINT-GONE`; not connected | Pass — same |
| `S1-FORCED-DETACH-AT-EXPIRY` | A session attached before expiry is still held | Lifetime expires; the existing session is then exercised | Severed, observed as a disconnect or a **declared** severance signature | `disconnected` fired; `isConnected()` false | Pass — same |
| `S1-ATTACHMENT-ENDPOINT-CONFINEMENT` | Bind produced a Unix domain socket | Stat the socket and each parent without following links | Some ancestor is current-user-only, and the level providing it is named | Socket mode `0755`; confinement comes from a `0700` ancestor at depth 3 | Pass with named caveat — same |
| `S1-SECOND-OWNER-REFUSAL` | A live persistent context already owns the profile | Broker arbitrates, then a second owner launch is attempted anyway | Broker refuses with a recognized typed refusal before any launch | `broker:ambiguous-ownership`; second owner did not launch | Pass — same |

Two findings bound the result. The bind endpoint behaves as a **bearer
credential**: within an open window any local process holding the socket path
attaches, and Playwright exposes no server-side per-attachment authorization
hook, so a broker can bound the *window* but not the *attachment count*.
Separately, the socket's own mode is `0755`. The fixture also records
`socketIsWorldConnectableByMode: false`, which is correct — `connect(2)` on a
Unix socket requires write permission, which `0755` denies to others on macOS
and Linux. The conservative posture is retained because that enforcement is not
uniform across every BSD, and because the control actually relied on is the
`0700` per-user temporary root above the socket. No row measured connectability
from a second uid.

## S2 — artifact host and dependency gate

### Integrated child-host composition

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2-INTEGRATED-CHILD-HOST-NATIVE-PLAYWRIGHT` | Parent owns a real persistent browser and binds it; adapter is self-contained ESM | Parent spawns a separate child host with an explicit environment; the child connects and runs the adapter | A distinct process holding native `Page`/`BrowserContext` returns a payload the parent validates and releases | Exit 0; child pid differs from parent; `_Page` / `_BrowserContext`; raw request client reachable; 3 rows read; opaque handle released | Pass — `s2/s2-integrated-results.json` |
| `S2-PARENT-ONLY-SENTINEL` | Parent environment holds a fresh random sentinel | Adapter reads its own process environment from inside the child | Sentinel absent; no key outside the allowlist except accepted OS-injected ones | Sentinel absent, length 0; one OS-injected key beyond the allowlist; zero unaccounted | Pass — same |
| `S2-CHILD-RESTRICTIONS` | Child launched with `--permission`, a read allowlist that **excludes** the profile root and the whole temporary root, one writable artifacts root, and no child-process/addon/worker grants | Adapter attempts each restricted operation, including a direct read of the live browser profile | Every restriction denies | `child-process`, out-of-allowlist read and write, `dlopen`, worker, **profile file read**, **profile directory listing** and **endpoint directory listing** all denied; no escape file | Pass — same |
| `S2-NETWORK-RESTRICTION-INCOMPATIBLE-WITH-TRANSPORT` | Identical child launched without `--allow-net` | Child attempts to connect to the parent-bound Unix-domain endpoint | Determine whether raw-egress denial and native Playwright access can hold at once | Child exit 3 with `ERR_ACCESS_DENIED … Use --allow-net`; empty stdout | Pass as a negative result — same |
| `S2-PARENT-OWNED-RELEASE-VALIDATION` | Parent holds a closed output schema | Child returns malformed, extra-field, credential-shaped and oversized payloads | Every invalid shape rejected in quarantine; no result, projection or handle released | `expected-array`; `additional-property-rejected` for both `debugTrace` and `sessionCookie`; `result-bytes-exceeded` | Pass — same |

The adapter cannot read the parent-only sentinel, and the value demonstrably
exists in the parent at spawn time, so the row is not vacuous. The
credential-shaped field is rejected by **schema closure**, not by a denylist of
credential names. Closure is proved for the declared behaviour surface; the
fixture-only `probes` member is an out-of-band host diagnostic declared open,
and is not part of the released projection contract.

Two constraints emerged that the RFC does not currently reflect.

**The network-restriction clause is unachievable as written.** Node 26.4.0 has
one coarse `net` permission covering Unix-domain sockets as well as TCP.
Denying raw egress in the adapter host also denies the Playwright transport the
adapter needs. Raw-egress containment for a capable adapter host therefore
requires an OS-level boundary, which the Node Permission Model does not supply
and which must never be described as a malicious-code sandbox. `--allow-net` is
additionally flagged experimental in this Node build.

**An environment allowlist is not an exhaustive description of the child
environment.** macOS injects `__CF_USER_TEXT_ENCODING` into a Node child
regardless of the environment object supplied. The policy must assert the
absence of named sensitive keys, not an exact environment size.

Three construction details belong in a future implementation spec rather than
in the contract. The adapter host must be spawned **asynchronously** — a
synchronous spawn blocks the parent event loop, the bound endpoint stops being
serviced, and the child's attachment times out. The one-shot protocol must
**flush stdout before exiting**, because `process.exit()` discards a pending
write and a large payload then arrives truncated and is misread as malformed
rather than oversized. And a permission allowlist must be emitted as
**repeated flags**: a comma-joined `--allow-fs-read` value is order-sensitive in
Node 26.4.0 and silently drops later entries, and a bare directory path grants
only that directory entry, not its subtree.

### Supply-chain policy

Sixteen of eighteen checks are met, with two declared residuals. Evidence:
`s2/supply-chain-policy-results.json`. The check ids are
`cleanLockPassesBlockingScan`, `cleanLockActuallyParsed`,
`controlledVulnerableLockBlocks`, `allSeverityInventoryIsSeparateAndNonBlocking`,
`infrastructureFailureDoesNotReadClean`,
`findingsDistinguishableFromInfrastructureFailure`, `databaseFreshWithinPolicy`,
`databaseSourceIntegrityRecorded`, `exactLockDigestRecorded`,
`exactBrowserRevisionRecorded`, `browserPayloadTreeDigestRecorded`,
`browserLauncherDigestRecorded`, `installerResolvesOnlyApprovedHosts`,
`downloadOverrideEnvUnsetAtPolicyRun`, `silentWaiverFilesDisabledInEveryScan`,
`platformCodeSignatureOnBrowserBinary`,
and the two unmet: **`downloadHostVerifiedAtConnectionLevel`** and
**`vendorSignatureManifestVerified`**.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2-SCAN-CLEAN` | Frozen runtime lock, current database | Blocking High/Critical scan of the exact lock file | Exit 0, no finding, lock actually parsed | Exit 0; target `package-lock.json` parsed; 0 findings | Pass — same |
| `S2-SCAN-CONTROLLED-VULNERABLE` | Lock pinning a package with known High findings | Same blocking scan | Exit 1 with findings | Exit 1; 1 Critical finding | Pass — same |
| `S2-SCAN-ALL-SEVERITY-INVENTORY` | Same clean lock | Separate non-blocking all-severity scan | Inventory is separate and does not block | Exit 0 | Pass — same |
| `S2-SCAN-DATABASE-MISSING` | Empty cache with updates disabled | Same blocking scan | Infrastructure failure cannot read as clean | Exit 1, 0 findings, fatal database error | Pass — same |
| `S2-FINDINGS-VS-INFRASTRUCTURE` | The two failing runs above | Compare their shapes | A finding-driven failure is distinguishable from an infrastructure failure | Findings 1 versus 0 at the same nonzero exit | Pass — same |
| `S2-WAIVERS-DISABLED` | Policy sets `--ignorefile /dev/null` | Every scan invocation | No silent waiver path | Flag present on all four scans | Pass — same |
| `S2-DATABASE-FRESHNESS-AND-INTEGRITY` | Database metadata on disk | Read timestamp and digests | Age within 24 h; database digest recorded | Age 2.5 h; database and metadata SHA-256 recorded | Pass — same |
| `S2-BROWSER-PAYLOAD-DIGEST` | Installed Chromium revision directory | Tree-hash every file, and separately hash the launcher | The payload, not the launcher stub, is pinned | Tree digest `b10ac1c882c2fa58a3b73d021807359c0506da21a43eb3381f943f7bfabbbe40` over 334 files and 372,014,615 bytes, plus a separate 52,112-byte launcher digest | Pass — same |
| `S2-BROWSER-DOWNLOAD-SOURCE` | Installer asked to resolve without fetching | `playwright install chromium --dry-run` | The hosts the installer would contact | `cdn.playwright.dev` and `playwright.download.prss.microsoft.com`, both approved | Pass at resolution level — same |
| `S2-DOWNLOAD-SOURCE-CONNECTION-LEVEL` | Same install path | Observe the host actually connected to | A connection-level confirmation | **Not measured.** The installer's own resolution is not a packet capture | **Declared residual** — same |
| `S2-BROWSER-SIGNATURE-MANIFEST` | Same payload | Glob the revision directory for `*.sig`, `*.asc`, `*.sha256`, `CHECKSUMS*`, `SHA256SUMS*`, `*.sigstore` | A vendor signature manifest to verify | Zero matches. The `*.manifest` paths present are macOS application-bundle directories, not signature manifests | **Declared residual** — same |
| `S2-DOWNLOAD-OVERRIDE-PINNING` | Playwright registry code | Search for download-host override variables | Record whether the source can be redirected | `PLAYWRIGHT_DOWNLOAD_HOST`, `PLAYWRIGHT_CDN_MIRROR`, `PLAYWRIGHT_DOWNLOAD_CONNECTION` all present, all unset at policy run | Pass with named risk — same |
| `S2-PLATFORM-CODE-SIGNATURE` | Installed browser binary | `codesign -dv` | A platform signature is present and valid | Signed | Pass — same |

The RFC's stated requirement is an exact browser-revision digest **or**
signature, and the payload tree digest satisfies it. Integrity therefore rests
on digest pinning **plus** the platform code signature; there is no vendor
per-file manifest, and the download host is environment-overridable, so a build
must pin those three variables rather than merely name approved hosts.

## S3 — safety-rail limits

Common precondition: fresh generated browser profiles, purpose-built loopback
services, and a broker-owned egress proxy configured as the browser's only
egress path. Each destination keeps an independent receive log, and no row
concludes "prevented" from a client-side exception alone. A UDP probe supplies
ground truth for channels that never appear in an HTTP log.

**Scope caveat that applies to every proxy-based verdict below.** The corpus
deliberately **inverts** the production destination-class rule: it is
loopback-only, so the proxy allows loopback and refuses everything else. In
production the rule is the reverse. These rows are evidence that the *control
point* works and that policy is enforceable there; they are not yet evidence
for the production destination-class policy itself.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Disposition and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3-PROXY-IS-CONNECTION-POINT` | Browser launched with a broker-owned proxy as its only egress path | Navigate to a declared origin by hostname | The proxy, not the browser, resolves the name and opens the socket | Proxy recorded the resolved address `127.0.0.1`; destination received the request | **Established** (positive path, not a refusal) — `s3/s3-egress-results.json` |
| `S3-ROUTE-CONNECTED-ADDRESS-UNOBSERVABLE` | A context route observes a navigation | Probe what the route callback can learn, by API name | Route exposes the requested hostname only | `connectedAddress` and `remoteAddress` accessors both `undefined`; exposed API is url/method/headers/postData/frame/resourceType | **Unobservable** — same |
| `S3-DNS-REBINDING-PINNED` | `rebind.test` pinned to `127.0.0.1`; a second server listens on `[::1]` at the same port | Resolution flipped to `::1`; page navigates again | Proxy refuses on pin mismatch; second address receives zero | `connected-address-pin-mismatch`; attacker receipts 0 | **Prevented** — same |
| `S3-DNS-REBINDING-UNPINNED-CONTROL` | Identical setup with the pin removed | Same navigation | Traffic reaches the second server, proving the pinned case is not vacuous | Attacker received 1 | **Control-valid** — same |
| `S3-REDIRECT-CHAIN-BOUNDED` | Sanctioned handler with `maxRedirects: 0`, per-hop revalidation, 3-hop bound | An allowed chain, an over-long chain, and one whose hop leaves the declared origin | Allowed chain completes; others refused before egress | 3 hops to `final:declared`; `hop-bound-exceeded` at 4; `hop-origin-not-declared`; undeclared receipts 0 | **Prevented** — same |
| `S3-REQUEST-CLIENT-ORIGIN-AT-PROXY` | Only the declared origin is a declared tunnel authority | Request an undeclared origin through the request client | Refused at the proxy; destination receives zero | 403; undeclared receipts 0 | **Prevented** — same |
| `S3-REQUEST-CLIENT-METHODS-AT-PROXY` | Same client against a declared, tunnel-authorised origin | Issue GET, HEAD, POST, PUT, PATCH, DELETE | Whether method policy is enforceable at the connection point | All six reached the destination; the proxy saw only `CONNECT` | **Unobservable at the connection point** — same |
| `S3-CONNECT-TUNNEL-POLICY-VISIBILITY` | Both cleartext and CONNECT decisions in one run | Compare what the proxy can observe in each | Origin and address enforceable for both; method and path only for cleartext | 11 cleartext decisions with methods visible; 25 CONNECT decisions with host:port only; the address pin **is** applied on the CONNECT path | **Detected** — same |
| `S3-PAGE-ROUTE-PRECEDENCE-AND-REMOVAL` | Broker context route installed; adapter adds a page route and unroutes the context rail | Fetch an undeclared origin through both paths | The JavaScript rail is defeated but the proxy still refuses | Undeclared receipts 0 across both | **Prevented at the proxy; in-browser rail defeated** — same |
| `S3-SERVICE-WORKER-HANDLED-PAGE-REQUEST` | Secure-context origin with a registered Service Worker; context route installed; **no proxy** (service workers need a secure context, and loopback bypasses the proxy) | Request a path the worker answers itself, then one it re-issues to a second origin | Whether routing observes each case | Worker-synthesised reply: routing did **not** observe it and the origin server received nothing. Worker-relayed fetch: routing observed and aborted it; second origin received 0 | **Prevented for relayed egress** — same. The synthesised-reply conclusion rests on one origin's receive count, with no proxy or packet observer in that variant |
| `S3-RAW-NODE-EGRESS` | Adapter holds raw `node:http` access | Call an undeclared origin from an unrestricted process, then from a permission-model child without `--allow-net` | Unrestricted call invisible to browser rails; restricted child denied | Unrestricted reached the destination (status 200) and the broker proxy log gained **zero** entries; the restricted child was denied and the destination received nothing | **Unobservable when unrestricted; prevented only in a child that does not need the Playwright transport** — same |
| `S3-DOWNLOAD-CONFINEMENT-REAL-API` | Real browser download; a symlink inside the job root points outside it | Commit through the real host path, then drive traversal, absolute and symlink-through targets into that same commit and `saveAs` | Commit lands under the realpath-resolved job root; every adapter-supplied path refused before `saveAs`; no file outside the root | Commit under the real job root; all four adapter paths refused with `confinement-violation`; zero escape files | **Prevented** — same |
| `S3-LINUX-PROXY-BEHAVIOUR` | Linux is not part of this run's platform | No Linux host available | A Linux proxy-inheritance result | Not run | **Not tested — explicit deferral** — same |
| `S3-WS-CANONICAL-TUPLE` | Canonical mapping under test as a pure function | Map `ws`/`wss`/`http`/`https` including default ports and mixed case | `ws`→`http`, `wss`→`https`; cleartext and secure never compare equal | All seven mappings correct; same host:port yields distinct keys | **Unit-pass** (a pure function, not an egress result) — `s3/s3-transports-results.json` |
| `S3-WS-ROUTE-INTERCEPTION` | `routeWebSocket` installed before any page exists | Open a declared `ws`, an undeclared `ws`, and a declared `wss` | Declared transports connect; the undeclared handshake never reaches its server | Declared ws open (1 upgrade); undeclared closed 1008 with **0** upgrades; declared **wss** open (1 upgrade), secure interception observed | **Prevented** — same |
| `S3-WEBRTC-EGRESS` | Independent UDP probe as STUN server | Peer connection with default flags, then `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` with and without a proxy, then `--disable-features=WebRTC,RTCPeerConnection` | Whether site-controlled WebRTC egress can be stopped | 1 STUN binding request and an `srflx` candidate in **every** variant | **Not prevented; egress observed** — same and `s3/s3-webrtc-mitigation-results.json` |
| `S3-WEBTRANSPORT` | Same probe | Attempt a session with default flags, then `--disable-features=WebTransport,WebTransportH3` | Whether the API is reachable and whether a flag removes it | Constructor present in both; 5 UDP packets in both | **Not prevented; egress observed** — `s3/s3-transports-results.json` |

The load-bearing change is architectural: **the broker-owned proxy, not the
route API, is the connection point.** Connected-address policy and DNS pinning
are enforceable there because the proxy resolves the name itself and then
connects to the resolved address literal, leaving no gap between check and
connection. Routing cannot do this — the route callback sees a hostname, and
the `connectedAddress` accessor does not exist.

The proxy's reach is bounded and the bound is precise. For a CONNECT tunnel it
sees only `host:port`; method and path are inside TLS. Playwright routes the
context-associated request client through an HTTP proxy with CONNECT **even for
a cleartext `http` origin**, so every mutating method reached the destination
while the proxy saw only `CONNECT`. Method policy for that client is therefore
a host-wrapper rail, and an admitted native adapter can bypass it by using the
raw request client. Page-route precedence, route removal and raw Node egress
independently confirm the trusted-code claim: no JavaScript-level rail is a
boundary.

**WebRTC and WebTransport remain acceptance blockers.** Neither is observable
to any Playwright rail or to the proxy, and no launch flag tested removed
either. A caveat on the negative result: Chromium silently ignores unknown
`--disable-features` names, and both disabled variants behaved identically to
their controls, which is also what an ignored flag looks like. The run did not
read back the browser's accepted command line, so the honest statement is that
**no flag name identified here removed the surface** — not that the feature
resisted a flag known to have been applied. S4 found a different launcher that
does disable the WebRTC API, which shows the channel is controllable.

## S4 — substitution check under amended D2

Stage one inspected every exact in-scope candidate without executing it: exact
registry tarball, published integrity digest verified, `--ignore-scripts`
install into an isolated tree, blocking dependency scan, and a read-only pass
over the shipped files. Stage two executed only under an explicit environment
allowlist, a fresh synthetic profile, and scanned dependencies.

### Stage one — and why its keyword screen is not a gate

| Candidate | Version | Integrity verified | Tree size | Files read (code/doc) | Blocking scan | Surface categories in **code** | In **documentation only** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `playwright` | 1.62.0 | Yes | 3 | 84 / 36 | Clean | 5 categories | none |
| `agent-browser` | 0.34.0 | Yes | 1 | 7 / 25 | Clean | **none** | 6 categories |
| `openchrome-mcp` | 1.12.9 | Yes | 118 | 5324 / 174 | **Fails** — CVE-2026-56876 High in `extract-zip` | 8 categories | none |
| `opendevbrowser` | 0.0.40 | Yes | 118 | 5540 / 247 | **Fails** — same CVE | 7 categories | none |

An earlier draft of this note presented these counts as disqualifying evidence.
Scanning every tree on equal footing shows they are not. **The retained
substrate trips five of the same categories**, because Playwright's own code
legitimately contains `--remote-debugging-port`, storage-state and cookie
vocabulary. And `agent-browser` has **zero** code hits: its logic lives in a
Mach-O binary that this pass does not statically inspect, so its documentation
hits are the weakest evidence in the table, not the strongest.

The keyword screen is therefore a **triage aid, not an admission instrument**.
Every disposition below rests on measured facts — the dependency scan, the
resolved lock, an executed surface, or an observed refusal.

### Dispositions

| Candidate | Exact offending surface | Why unavoidable in the proposed constrained mode | Exact artifact inspected | Falsifiable revisit trigger |
| --- | --- | --- | --- | --- |
| `agent-browser` 0.34.0 | A cookie-read surface returning a non-empty payload to its caller, and an unauthenticated loopback CDP endpoint `ws://127.0.0.1:<port>/devtools/browser/<uuid>` carrying no per-connection token | Both **measured under execution**. The containment mode that would constrain the tool (`--allowed-domains`) was run together with `--profile` and the candidate refused with exit 1: *"--allowed-domains is not supported with --profile because Chrome may restore existing pages before network containment is installed."* It cannot provide containment and the per-connection profile D4 requires at the same time; without containment the credential surface and the unauthenticated control channel remain | `agent-browser@0.34.0`, registry integrity `sha512-eR6Ey4I/…44g==` | A version supporting `--allowed-domains` together with a dedicated per-connection profile, removing the cookie/storage export surface, and binding a per-launch authenticated endpoint |
| `openchrome-mcp` 1.12.9 | Fails the blocking dependency scan (CVE-2026-56876 High in `extract-zip`); ships a fixed unauthenticated debugging port `9222` in `dist/index.js`; carries an `argon2` native addon in the resolved lock; carries a self-update command in `dist/cli/update-command.js` | The failing scan means the amended rule's execution precondition is unmet, so it cannot proceed to stage two at all. The fixed port is the connection model rather than an option, the native addon is a lock-level dependency, and self-update contradicts explicit-approval upgrade | `openchrome-mcp@1.12.9`, integrity `sha512-LKmwS1Wt…10Rg==`, 118-package tree, lock SHA-256 `de5a6118dffc9024…` | A version with a clean blocking scan that binds an unguessable per-launch authenticated endpoint, without the native addon or self-update |
| `opendevbrowser` 0.0.40 | Fails the same blocking scan; resolves `node_modules/playwright-core` at **1.62.1**, a second Playwright copy at a version other than the pinned 1.62.0 | The failing scan blocks stage two. The second Playwright copy is in the resolved lock, not a runtime option, and contradicts the single-exact-dependency rule and S2's single-copy proof | `opendevbrowser@0.0.40`, integrity `sha512-wG/PO9hI…zPPg==`, 118-package tree, lock SHA-256 `f4b8f461e08d2a62…` | A version with a clean scan that pins the host's exact Playwright and ships without the plugin/extension relay |
| `playwright` 1.62.0 | None measured | — | `playwright@1.62.0`, integrity `sha512-Z14dG305…Sylw==`, 3-package tree. Carries one optional darwin-only native addon (`fsevents`), unlike the two scan-failing candidates' required addons | Retained as the provisional substrate |

### Stage two — sanitized execution of the one candidate that cleared the scan

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Outcome and evidence |
| --- | --- | --- | --- | --- | --- |
| `S4-SANITIZED-CANDIDATE-EXECUTION` | A sentinel exists in the parent; the candidate environment is constructed explicitly | Enumerate a stand-in child's environment with `/usr/bin/env` under the identical construction, then run the candidate | No SSH agent socket, session token or parent sentinel present in the child | A `/usr/bin/env` stand-in spawned under the identical construction observed exactly `HOME`, `PATH`, `TMPDIR`, with zero keys beyond the passed set and no forbidden key; candidate exit 0. The stand-in does not link CoreFoundation, so it cannot exhibit the `__CF_USER_TEXT_ENCODING` injection a Mach-O child would; the forbidden-key result holds, the exhaustiveness result is scoped to the stand-in | **Pass** — replaces the round-2 tainted row — `s4/s4-agent-browser-round3-results.json` |
| `S4-AB-SURFACE-ENUMERATION` | Exact integrity-verified artifact | Invoke the candidate help surface | Which admission-relevant surfaces the binary exposes | cookies, storage, auth, `--state`, `--restore`, `--auto-connect`, `--allowed-domains`, daemon and MCP all present | Recorded — same |
| `S4-AB-NATIVE-ABI-BRIDGE` | Fresh generated synthetic profile, no domain allowlist | Ask the candidate for its CDP url, then `connectOverCDP` | Whether it can supply native Playwright objects | Native `_Page` / `_BrowserContext`; endpoint loopback `ws` with **no per-connection token** | **Native ABI available** — same |
| `S4-AB-CONSTRAINED-MODE-VS-PROFILE-AND-ABI` | Containment mode and an explicit profile requested together | Run the combination, then attempt the native bridge under containment alone | Whether containment, a per-connection profile and the ABI hold together | Combined run **exit 1** with the refusal text quoted above; containment alone reports a CDP url and the bridge connects | **Containment excludes a per-connection profile** — same |
| `S4-AB-WEBRTC-CONTAINMENT` | Independent UDP probe; isolated candidate sessions; clean daemon; the page reports its own outcome back to the receive log | Same synthetic peer-connection page without, then with, the domain allowlist | A valid control reaches the probe; the constrained arm is interpretable only if the page ran | Control: page served, peer connection attempted, **1** STUN packet. Constrained: page served, peer connection **not** attempted, page reported `SecurityError: RTCPeerConnection blocked while domain filtering is active`, **0** STUN packets | **API disabled in constrained mode** — `s4/s4-webrtc-containment-results.json` |
| `S4-AB-CREDENTIAL-EXPORT-SURFACE` | A synthetic cookie in a generated synthetic profile | Invoke the candidate cookie-read surface | Whether the substitute broker can export session material to its caller | Non-empty payload returned; cookie **name** present. No value printed, logged, compared or archived | **Export surface present** — same |

**Verdict: retain Playwright provisionally; D2 is not reopened, and S4 stays
Partial.** `agent-browser` does not remove material lifecycle responsibility
without widening effective authority — it adds a credential-export surface and
an unauthenticated CDP control channel, and cannot provide containment together
with the per-connection profile D4 requires.

S4 nonetheless remains **Partial**, not Pass, for a reason the evidence itself
surfaced. The gate text admits to execution only candidates that "clear
inspection" and holds S4 open until every such candidate has passed the common
S1/S3 lifecycle, handoff, native-ABI, crash-recovery and containment corpus.
Stage one's screen has now been shown non-discriminating, so "clears inspection"
has no sound operational meaning as implemented; the precondition actually used
was clearance of the blocking dependency scan. And the common corpus was not
run — only the native-ABI, containment, endpoint-character, credential-surface
and sanitized-execution subsets were. Closing S4 requires an approver decision:
either amend the gate to state the precondition actually used and accept that an
execution-backed *exclusion* discharges the corpus requirement, or commission the
full corpus for `agent-browser`.

One result cuts across S3 and is recorded as a lead. Under `--allowed-domains`,
`agent-browser` raises `SecurityError: RTCPeerConnection blocked while domain
filtering is active` — a **named mechanism**, not an unexplained suppression:
the candidate disables the WebRTC API while its allowlist is active. The
foundation should investigate the same mechanism rather than record WebRTC as
inherently uncontrollable. The result is n=1 and unreplicated.

## S5 — cross-pack vertical

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S5-CANDIDATE-DISPLAY-CONFIRM-DISCARD` | `resolve-identity` produced three fixed-schema candidates carrying clear correlation values; six sinks (`providerStdout`, `providerStderr`, `artifacts`, `diagnosticEvents`, `checkpoints`, `modelResults`) are written to during the flow, two of them to disk | Host renders the candidates in its own confirmation surface; the user accepts one and rejects two | Only confirmed bindings persist; rejected clear evidence discarded; no candidate value reaches any of the six sinks | Three rendered; two rejected; retained record holds only a generated binding id and an alias; **no** correlation value survives, including the accepted one; all six sinks carried content and none contained a candidate value, verified in memory and by reading the on-disk sinks back | Pass — `s5/s5-round3-results.json` |
| `S5-VALIDATION-SURFACE-AND-PRE-BROWSER-REFUSAL` | Validation execution object and an exact grant tuple; the authorizer's allow path calls a **real** `chromium.launchPersistentContext` | Assert the validation surface is a subset of the expected keys, then vary each grant field in turn | No behavior/grant/artifact/log/checkpoint surface; every single-field mismatch refuses before any launch | Surface is exactly `{page, context, signal, job, connection}`; all 11 varied fields refused with a field-named reason; **zero** browser launches during the mismatches; the positive case launched exactly once, proving the launcher was reachable throughout | Pass — same |
| `S5-CROSS-CONSUMER-RESIDUE` | Consumer A leaves eight residue classes in one shared connection, each **verified as planted** before teardown | Broker runs best-effort teardown — now including `ctx.request.dispose()` — then consumer B executes on a fresh page in the same connection | The survival map partitions exactly the classes A left, each with a definite result | **Cleared by teardown:** context route, context listener, stray page, and the held request-client reference. Three classes **survive**: init script, context state (origin `localStorage`), and A's committed download. **Not cross-page by construction:** the patched page global, which can never reach B's fresh document regardless of teardown and is therefore excluded from the cleared count | Pass — same |
| `S5-ISOLATION-CONTRACT-VIABILITY` | The teardown surface Playwright actually exposes | Attempt a complete teardown, then probe six named removal/revocation APIs and a disposal attempt | Whether a viable per-consumer isolation contract exists below a new context | `unrouteAll`, `clearCookies`, `clearPermissions`, listener removal, page closure **and `ctx.request.dispose()`** are available and were all exercised. `removeInitScript`, `removeAllInitScripts`, `clearInitScripts`, `initScripts` and `revokeRequest` are all **`undefined`**; `addInitScript` returns a disposable handle, but only to the registrant | Pass — same |

Of the eight classes consumer A planted, **3 survive** teardown, 4 are cleared
by it, and 1 (the patched page global) is not cross-page by construction and so
is excluded from the cleared count.

The architectural disposition is measured rather than assumed:
**per-consumer isolation is not viable within one `BrowserContext`, but the gap
is narrower than round 2 recorded.** An earlier draft of this note claimed no
API revokes a held request client. That was wrong: `ctx.request.dispose()`
exists, was never called, and when the teardown actually calls it consumer A's
held client fails with a closed-target error and the side-channel server
receives **zero** — the class moves from surviving to cleared. Its bluntness is
the caveat: it disposes the context's request client, which consumer B shares,
so a broker using it must re-establish B's client rather than treat it as a
targeted revocation.

What remains genuinely unrecoverable is narrower and sharper. A broker can
remove only the init scripts it registered itself — `removeInitScript`,
`removeAllInitScripts`, `clearInitScripts`, `initScripts` and `revokeRequest`
are all `undefined` — so an init script an adapter registered persists into
every later consumer, along with origin-scoped storage and any artifact already
committed to the shared job root.

The three stronger options each cost something the RFC currently requires: one
`BrowserContext` per consumer sacrifices the shared authenticated session; one
browser process per consumer forces re-authentication; OS-level isolation of the
adapter host is a different product boundary and, per S2, the Node Permission
Model cannot supply it.

This **confirms** the RFC's existing position that native-adapter trust is
connection-wide, and supplies the measurement it was missing.

## Fixture defects corrected during this run

Recorded beside the rows they affected, because several changed conclusions.
Every promoted result postdates its fix — the whole suite was regenerated after
the final fixture change, and `verify-note-figures.py` confirms every figure in
this note against those artifacts.

This list is distinct from the RFC's numbered *Security and runtime corrections
in force*; references of the form "correction 7" in the RFC point there, not
here.

| Defect | Rows affected | Effect on the conclusion |
| --- | --- | --- |
| The promoted archive leaked the operator's account name and uid in four scanner command strings | Whole archive | Redactors rewritten and a **hard privacy gate** added to the archive builder, negative-tested by injecting a `/Users/…` path and confirming the build fails |
| `existsSync` follows a symlink, so a dangling `SingletonLock` read as absent | `S1-LIVE-LOCK-REFUSAL`, `S1-AMBIGUOUS-LOCK-REFUSAL` | Presence checks switched to `lstat`; the rows had been failing for a fixture reason, not a rail reason |
| An absolute lock target parsed as `<host>-<pid>`, so `/tmp/bait-1234` read as a remote owner | `S1-LOCK-TARGET-NOT-FOLLOWED` | Broker now rejects any target carrying a path separator before parsing — a real hardening change, not just a test fix |
| `S1-UNAUTHORIZED-SECOND-ATTACH` had a literal `true` predicate and was counted in the pass total | S1 headline | Reclassified **recorded**; S1's asserted total is 12, and the bearer-credential gap moved into the open column |
| The child read allowlist enclosed the whole temporary root, and therefore the live browser profile | `S2-CHILD-RESTRICTIONS` | Allowlist narrowed and three profile/endpoint read probes added; all now denied. The earlier row could not have detected an adapter reading cookies off disk |
| The download escape half re-implemented the confinement predicate instead of calling it | `S3-DOWNLOAD-CONFINEMENT-REAL-API` | Now drives the real commit and `saveAs`, adds a symlink-through target and `realpath` canonicalization |
| Four scans shared one output filename, so one scan read another's findings | `S2-SCAN-DATABASE-MISSING` | Unique output per scan; the fail-closed row had been reporting a previous scan's finding count |
| The approved-download-host check filtered out unapproved hosts before testing, so it could not fail | `S2-BROWSER-DOWNLOAD-SOURCE` | Replaced with the installer's own `--dry-run` resolution; connection-level verification demoted to a declared residual |
| The "browser payload digest" hashed a 52 KB launcher stub | `S2-BROWSER-PAYLOAD-DIGEST` | Replaced with a 334-file, 372 MB tree digest; the launcher digest is recorded separately |
| The signature-manifest result was a hard-coded `False` | `S2-BROWSER-SIGNATURE-MANIFEST` | Now an actual glob; it matched macOS bundle directories, which are excluded as not signature manifests |
| S5's leakage and refusal rows asserted on values the fixture had just set | `S5-CANDIDATE-DISPLAY-CONFIRM-DISCARD`, `S5-VALIDATION-SURFACE-AND-PRE-BROWSER-REFUSAL` | Rewritten against six sinks that are actually written (two read back from disk) and a real browser launcher as the refusal counter |
| S5 classified eight survival keys that were not the eight classes A left; the listener and stray page were never re-probed | `S5-CROSS-CONSUMER-RESIDUE` | Survival map now partitions exactly what A left. This exposed a **false positive**: `strayPage` had been counting the context's default page |
| The isolation row's central finding was a hard-coded array of unavailable API names | `S5-ISOLATION-CONTRACT-VIABILITY` | Now probes six named APIs and a disposal attempt |
| The S4 containment-versus-profile refusal was a hard-coded literal that no run produced | `S4-AB-CONSTRAINED-MODE-VS-PROFILE-AND-ABI` | Now measured: the combined invocation really exits 1 with the recorded refusal text. This claim carries the D2 and D4 dispositions |
| The S4 WebRTC row counted zero STUN packets as containment without proving the peer connection ran | `S4-AB-WEBRTC-CONTAINMENT` | The page now reports its own outcome to the receive log. This **changed the finding**: the constrained arm never attempted the connection because the API is disabled, and the mechanism is now named |
| The S4 environment row inspected the parent's env object rather than the child's | `S4-SANITIZED-CANDIDATE-EXECUTION` | Now observes the real child environment |
| The stage-one surface screen was presented as disqualifying evidence | S4 stage-one table | Scanning all trees equally showed the retained substrate trips five of the same categories and `agent-browser` trips none in code. The screen is now labelled triage, and every disposition rests on measured facts |
| Driver scripts exited 0 regardless of failed rows | All | Every driver exits non-zero on an asserted failure. The two S3 drivers declare the disposition each row established, so a regression changes the observed disposition and fails the run |
| `s1/s1-run.txt` in the archive was a pre-fix artifact still reporting 13 passes | S1 headline | Regenerated from the corrected driver; it now reports 12 asserted and 1 recorded |
| The containment-versus-profile refusal keyed on `exit != 0`, which a SIGKILL timeout satisfies | `S4-AB-CONSTRAINED-MODE-VS-PROFILE-AND-ABI` | Requires exit 1, no signal, and the candidate's own refusal text. This claim carries the D2 and D4 dispositions |
| The release-validation row passed on a crashed child emitting empty stdout | `S2-PARENT-OWNED-RELEASE-VALIDATION` | Requires a clean child exit plus the exact per-shape rejection code |
| `constrainedApiDisabled` accepted any page error as containment | `S4-AB-WEBRTC-CONTAINMENT` | Requires the named `SecurityError` naming `RTCPeerConnection` |
| The WebRTC row could re-read an archived result as if it were a measurement | `S4-AB-WEBRTC-CONTAINMENT` | The probe stamps each run; a result outside a bounded recency window reports `not-tested-stale-artifact` |
| `--disable-features` was passed twice, so Chromium silently kept one value and the disabled arms differed twice | `S3-WEBRTC-EGRESS`, `S3-WEBTRANSPORT` | Merged into a single switch per variant |
| The TLS private key was generated **inside** the tree the archive is built from, and candidate trees with a Critical finding alongside it | Archive safety | Both now generated outside the evidence root; the TLS pair is deleted at teardown |
| The privacy gate was not shipped, so it could not be audited, and its exemptions were whole-file | Archive safety | The builder is now a manifested member with per-file *literal* exemptions, negative-tested in both directions |
| `ctx.request.dispose()` existed, was never called, and the row concluded no revocation API exists | `S5-CROSS-CONSUMER-RESIDUE` | Teardown now calls it. **Conclusion changed**: the held client is revoked, surviving classes drop from four to three |
| Refusal probes accepted any `denied:` prefix, so `denied:ENOENT` would have read as a denial | `S2-CHILD-RESTRICTIONS` | Requires exact codes, and the profile probe targets a file the parent verified exists |
| `ownedThroughout` treated a stat error as proof of ownership | `S1-ATTACHMENT-ENDPOINT-CONFINEMENT` | Any stat error in the chain now fails the row |
| Prose figures kept outrunning the artifacts after each rerun | Whole note | `verify-note-figures.py` derives every load-bearing figure from the results files and fails if the note disagrees |

## Sensitive-data disposition

Only synthetic inputs and redacted, bounded outputs are promoted. The archive
contains no browser profile, cookie database, trace, HAR, screenshot, download,
credential value, TLS private key, vulnerability-database cache, third-party
package tree or browser payload. The S4 candidate artifact is excluded and must
be installed separately at its pinned version. The TLS fixture generates a
throwaway self-signed pair on demand and its key never leaves the run.

The one cookie-read row records only that a non-empty payload was returned, its
size class, and that the cookie **name** appeared. The cookie was created by the
fixture and is synthetic. No cookie value was printed, logged, compared or
archived.

**Round-2 incident status.** The three exposed session tokens were rotated by
the operator before this run, and the SSH agent was checked and held no
identities. That closes agent forwarding and the three named tokens. It does not
retroactively bound the rest of that exposure: the round-2 candidate ran at the
operator's uid with the real `HOME` and the full ambient environment, so
on-disk material reachable by that account was in scope, and the run had no
egress monitoring, meaning "no evidence of misuse" is absence of evidence rather
than evidence of absence. That residual is **accepted** by the RFC approver, not
excluded. Round-3 execution passed an explicitly constructed environment whose
observed child contents were exactly `HOME`, `PATH` and `TMPDIR`.

## Decision impact

- **D2 — browser substrate.** Retain Playwright provisionally. Every candidate
  has a reviewed disposition resting on measured facts. S4 stays Partial pending
  an approver decision on the gate text.
- **D4 — connection owns the profile.** Strengthened as a discriminator, and now
  measured: it is the clause that excludes the one candidate that cleared the
  dependency scan.
- **D5 / D13 — grants and trusted code.** Confirmed by measurement, with the
  gap narrower than round 2 recorded. Of the eight residue classes verified as
  planted, three survive teardown — an init script registered by another
  holder, origin-scoped storage, and an artifact already committed to the
  shared job root — while five named removal APIs do not exist. A held request
  client *is* revocable via `ctx.request.dispose()`, but bluntly: it disposes
  the shared context client. Connection-wide native-adapter trust stands.
- **D7 — attachment and credential boundary.** Requires amendment. The bind
  endpoint is a bearer credential with no per-attachment authorization hook, so
  "single-use for attachment establishment" is not achievable with the current
  API. Lifetime expiry and forced detach *are* achievable and are now proven.
- **D13 — network posture.** Connected-address enforcement and DNS pinning move
  from unproven to prevented at a broker-owned proxy, under an inverted
  loopback-only destination rule that is not yet the production policy. Method
  policy for the context request client is unenforceable at that proxy. WebRTC
  and WebTransport remain acceptance blockers.
- **D17 — dependency gate.** A complete blocking policy is demonstrated across
  16 of 18 checks. Two residuals: no vendor signature manifest, and download-host
  verification only at the installer's resolution. The download host is
  environment-overridable, so a build must pin those variables.
- **Adapter-host separation.** The composition is proven and now also denies a
  direct read of the live browser profile. The RFC's "network restrictions"
  clause is unachievable as written and must be amended.

## Review results

Recorded in the RFC's amendment history. These reviews validate the record, not
the architecture. They do not change any Experimental exit decision, authorize
acceptance, or authorize implementation.
