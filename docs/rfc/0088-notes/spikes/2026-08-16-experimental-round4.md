# 2026-08-16 Experimental round 4

This note records the fourth RFC-0088 Experimental run. It is authoritative
over the round-3 headline verdicts where the two disagree. The
[round-3 note](2026-08-16-experimental-round3.md) and its
[evidence archive](round3-evidence-archive.md) are preserved unchanged as that
run's audit trail; nothing there is rewritten, and the supersession is recorded
as an append-only note at the end of it.

Round 3 left ten pre-acceptance blockers; the approver's gate-text disposition
closed one of them before this run, leaving nine. Two were the reason
acceptance was not taken: WebRTC and WebTransport egress were not prevented by
any control tested, and the run could not tell a flag that failed from a flag
that was never applied. Both are now settled.

Of those nine, four closed outright on measurement, three closed but left a
narrower residual that is carried in the list rather than dropped, and two are
unchanged. One new finding was created by measurement — the bind endpoint's
confinement does not hold on Linux — and it is a real result, not a fixture
defect.

## What changed, in one paragraph

The two blocked egress channels are controllable. A context init script that
replaces `RTCPeerConnection` with one raising a named `SecurityError` — the
same mechanism S4 measured on a different launcher in round 3 — prevents WebRTC
egress in every window realm tested — main document, same-origin iframe, `about:blank` iframe and cross-origin iframe — and not exposed at all in a dedicated Worker. The
same shim does *not* hold for WebTransport, because a dedicated Worker is a
realm the init script never enters; the broker-owned egress proxy closes that
escape, because WebTransport cannot traverse an HTTP proxy. Method policy,
recorded in round 3 as unenforceable at the connection point, becomes
enforceable when the broker terminates the tunnel. The production
destination-class rule now has its own measurements instead of inheriting
verdicts from a deliberately inverted one. An OS-level boundary for adapter-host
raw egress exists and is measured. And Linux is no longer an untested platform:
the egress rails behave as they do on macOS, while one S1 row fails there for a
reason that matters.

## Reproduction identity and integrity

- Repository ref: `328138e5` (`docs(rfc): promote RFC-0088 round-3 Experimental evidence (#970)`)
- Host: macOS 26.5.2 build 25F84, Darwin 25.5.0, arm64
- Node 26.4.0; npm 11.17.0; Python 3.13.13
- Playwright 1.62.0 from the same frozen lock as round 3; lock SHA-256
  `99fcdaedf22515c7a416c957beae73e782780430e85ab4d7ae195660cec25ed0`
- Browser: bundled Chromium 151.0.7922.34, measured from `browser.version()`
- Linux arm: Ubuntu 24.04.4 LTS, Linux 6.8.0-100-generic arm64, Node v24.18.0,
  Chromium 151.0.7922.34, via `mcr.microsoft.com/playwright:v1.62.0-noble`.
  **Scope bound:** the Linux arm covers the browser, proxy and
  destination-class rails plus the S1 lifecycle corpus. The Node Permission
  Model and `sandbox-exec` rows are macOS-only and were not re-run there, and
  the container's Node is the image's v24.18.0, not the host's 26.4.0. The
  container runs as **root** (uid 0) with Chromium's renderer sandbox
  **disabled** (`--no-sandbox`, required there). Both change how a result
  reads: "no current-user-only ancestor" is a different statement as uid 0, and
  the egress rails were measured with the renderer sandbox off.
- Promoted package: [`round4-evidence-archive.md`](round4-evidence-archive.md)

**Replication.** Every macOS arm in this note ran **once**; only the Linux S1
lifecycle corpus was repeated, twice. The macOS dispositions are therefore n=1,
several of them resting on UDP packet counts taken after fixed 2.5–3.5 s waits.
No row is replicated, and no row claims to be; treat every macOS disposition in
this note as a single observation.

All sites, pages, downloads, profiles and certificates were synthetic and
loopback-only. No live account, personal browser profile or real credential was
used. The TLS interception key material for the method-policy fixture is
generated into a temporary root outside the evidence tree and deleted at
teardown.

## Reproduction procedure

**Prerequisites** — macOS arm64 with Node 26.x for the main suite; a container
runtime for the Linux arm; `openssl` for the method-policy fixture, which
generates its own throwaway chain.

Reconstruct the archive with the procedure in
[`round4-evidence-archive.md`](round4-evidence-archive.md), then from the
reconstructed root:

```bash
unset PLAYWRIGHT_DOWNLOAD_HOST PLAYWRIGHT_CDN_MIRROR PLAYWRIGHT_DOWNLOAD_CONNECTION
npm ci --ignore-scripts            # reproduces the scanned tree from the frozen lock
npx playwright install chromium
./run-all.sh                       # the macOS suite; exits non-zero on any failed row
./run-linux.sh                     # the Linux arm; needs a container runtime
python3 verify-note-figures.py <note.md> <archive-note.md> <rfc.md>
```

`run-all.sh` regenerates every promoted **macOS** artifact, so none of those can
be stale relative to the fixture that produced it. The three Linux artifacts are
produced only by `run-linux.sh`, which now deletes them before the container
step so a failed arm cannot leave the previous run's results in place, asserts
the exact expected Linux failure set rather than swallowing the exit code, and
writes a deferral artifact when no container runtime exists. Each driver exits
non-zero when a row it asserts fails. `verify-note-figures.py` derives every load-bearing
figure in this note from the results files and exits non-zero if the note
disagrees; round 4 extends it to the figures introduced here.

**Network access is required** for `npm ci`, `npx playwright install`, the
connection-level download-host arm and the Linux image pull.

## Current spike state

| Spike | Round-4 verdict | What closed in round 4 | What remains open |
| --- | --- | --- | --- |
| S1 | **Pass on the named gates (macOS); Partial on Linux** | Playwright exposes no per-attachment authorization hook, but a broker-owned relay supplies one: a second attachment is refused and the real endpoint sees exactly 1 upstream connection | The relay bounds attachments to itself, not to the underlying endpoint path. **New:** endpoint confinement fails on Linux — no current-user-only ancestor exists |
| S2 | **Pass on the named gates** | An OS-level boundary for adapter-host raw egress is named and measured: the Playwright transport survives while raw egress is denied. Download host verified at connection level | No vendor signature manifest ships with the browser payload. The measured boundary is macOS-only and uses a vendor-deprecated tool |
| S3 | **Pass on the named gates** | WebRTC prevented in every realm tested; WebTransport prevented by the proxy including the Worker escape; method policy enforceable at a terminating connection point; the production destination-class rule measured directly; Linux proxy behaviour measured | Method-policy trust establishment is untested. Windows is untested. Every control here is a rail against site-controlled egress, not a boundary against admitted native code |
| S4 | **Pass** | Closed by approver disposition on the gate text, taken **before** this run and recorded as its own audit entry — not by any round-4 measurement | None. Each candidate's falsifiable revisit trigger stands |
| S5 | **Pass, unchanged** | — | Cross-consumer residue is disclosed and accepted, not remediable within one `BrowserContext` |
| S6 | **Pass, unchanged** | — | Convention amendment still waits for acceptance |

No result authorizes acceptance or implementation.

## S3 — WebRTC and WebTransport under a read-back command line

Round 3's caveat was exact: Chromium silently ignores unknown
`--disable-features` names, the run never read back the accepted command line,
and both disabled arms behaved identically to their controls — which is also
what an ignored flag looks like. Round 4 removes that ambiguity.

One finding here changed a conclusion, and it is recorded before the table
rather than after it. The first version of this shim replaced exactly one
binding name per interface, and every probe then constructed through that same
name — so the arm reported "prevented" while `webkitRTCPeerConnection`, a
second binding of the identical interface, stayed reachable and **emitted a
real STUN packet**. That is round 3's defect class "a remedy carrying the same
defect it was written to catch", at full size. The shim now replaces bindings
by identity, and a separate enumeration probe asserts that none survives; a
name-based check could never have established that.

Every arm reads `chrome://version`'s command line from the running browser and
derives switch presence from that page text, not from the arguments the fixture
passed. One honesty bound survives and is stated rather than buried: presence
in the accepted command line proves a switch **reached** the browser. It does
not prove Chromium **recognised** it, because unknown switches are carried
verbatim.

The matrix ran 10 launch arms — an *arm* is one browser launch, not one table
row, and two rows below describe more than one arm — and all 7 flag arms
reached the browser with
every requested feature name intact — 34 of 34 asserted checks in this fixture
pass.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R4-RTC-CONTROL` | No flags, no shim | Peer connection against an independent UDP probe | The channel egresses, or nothing below is interpretable | Constructed in all three realms; control emitted 1 STUN binding request | Pass — `s3/r4-webrtc-webtransport-results.json` |
| `S3R4-RTC-DISABLE-FEATURES` | `--disable-features=WebRTC,RTCPeerConnection` | Same | Whether the base::Feature namespace removes the surface | Switch and both names present in the accepted command line; constructor still constructs; STUN still emitted | **No effect** — same |
| `S3R4-RTC-DISABLE-WEBRTC-SWITCH` | `--disable-webrtc` | Same | Whether the bare switch removes the surface | Switch present in the accepted command line; constructor still constructs | **No effect** — same |
| `S3R4-RTC-DISABLE-BLINK` | `--disable-blink-features=WebRTC` and `=RTCPeerConnection` | Same | Whether the Blink runtime-feature namespace — untried in round 3 — removes it | Both switches present in the accepted command line; constructor still constructs; STUN still emitted | **No effect** — same |
| `S3R4-RTC-IP-HANDLING` | `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` with a proxy | Same | Whether IP-handling policy stops it | Switch present; STUN still emitted | **No effect on WebRTC** — same |
| `S3R4-RTC-SHIM` | Context init script raising a named `SecurityError`, replacing every binding by identity | Same | Whether the mechanism S4 observed on another launcher works here | `SecurityError` naming `RTCPeerConnection`; the shim arm emitted 0; the page reported `state=blocked` to its own origin | **Prevented** — same |
| `S3R4-ALIAS-ENUMERATION` | Control arm, no shim | Enumerate every own binding of each interface by its prototype marker, then construct through each | Whether one name is the whole surface | The control exposes **more than one** binding of `RTCPeerConnection`; every enumerated binding constructs | **Alias surface confirmed** — same |
| `S3R4-ALIAS-COVERAGE` | Shim installed | Construct through every enumerated binding | Whether the shim reaches all of them | Every enumerated binding of both interfaces throws the named `SecurityError` | **Prevented on every binding** — same |
| `S3R4-WT-FLAGS` | `--disable-features=WebTransport,WebTransportH3`, then `--disable-blink-features=WebTransport` | Construct a WebTransport session | Whether either namespace removes the constructor | All names present in the accepted command line; constructor still constructs; UDP still emitted | **No effect** — same |
| `S3R4-WT-SHIM` | The **same** arm and the same shim — one init script covers both interfaces and every binding of each | Same | Whether the same mechanism covers this channel | `SecurityError`; the arm's non-STUN UDP is 0 against a control that emitted 5 | **Prevented in window realms** — same |
| `S3R4-PROXY-ONLY` | Broker-owned proxy, no flags and no shim | Both channels | Which of proxy and flag was doing the work in the IP-handling arm | STUN still emitted; WebTransport `rejected:WebTransportError` with 0 non-STUN UDP | **Proxy prevents WebTransport, not WebRTC** — same |

The proxy-only arm matters. Round 3's IP-handling arm carried both a flag and a
proxy, so any difference would have been attributed to the flag by default. The
proxy alone reproduces the whole WebTransport effect, and none of the WebRTC
one.

### The realm escapes that decide whether the shim is worth anything

A page-realm shim is only a control if a site cannot step around it into a
fresh realm. Two escapes were measured, each with a control arm that has to
produce egress first.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R4-ESCAPE-SAME-REALM-FAMILY` | Shim installed | Construct in the main document, a same-origin iframe and an `about:blank` iframe | Whether the shim reaches child realms | All three throw the named `SecurityError`. `typeof` is not the discriminator — a shim is itself a function — so every realm is probed by construction | Pass — `s3/r4-webrtc-webtransport-results.json` |
| `S3R4-ESCAPE-CROSS-ORIGIN-IFRAME` | Shim installed; a second synthetic origin serves a page that runs its own peer connection and reports to its own receive log | Frame that origin | Same-origin policy blocks probing the child's globals, so this is measured by egress | Control: child reported both bindings `constructed`, 2 STUN packets — two because the child now probes `webkitRTCPeerConnection` as well. Shimmed: child reported both as `threw:SecurityError`, 0 STUN packets | **Covered** — `s3/r4-realm-escapes-results.json` |
| `S3R4-ESCAPE-WORKER` | Shim installed | A dedicated Worker constructs `WebTransport` | Whether a worker realm is reachable by a window init script | `RTCPeerConnection` is `undefined` in a worker, so WebRTC has no worker escape. `WebTransport` is a `function` there and constructs: 5 UDP packets without the shim, the same 5 with it | **Escape confirmed** — same |
| `S3R4-ESCAPE-WORKER-UNDER-PROXY` | Shim plus the broker-owned proxy | Same worker | Whether a control below the JavaScript layer closes it | The worker still constructs, and its UDP drops to 0 once the proxy is the only egress path | **Closed by the proxy** — same |

Each of those four dispositions is **asserted**, not merely recorded. A
recorded row states a measurement with no predeclared direction, which is the
right shape while the direction is unknown and the wrong shape once a blocker
closure depends on it. A browser change that closed the worker escape, or
opened the cross-origin one, now fails the run instead of quietly altering a
number.

The disposition follows from those four rows, not from the shim's existence:

- **WebRTC is prevented for site-controlled egress** by the init script alone,
  across the realms tested: main document, same-origin iframe, `about:blank`
  iframe, cross-origin iframe, and a dedicated Worker — which does not expose
  the constructor at all. **Shared workers, service workers, `srcdoc` / `data:`
  / `blob:` frames and `window.open` popups are not tested.** The proxy sits
  below all of them, so the disposition probably survives, but that is
  reasoning rather than measurement and it is carried as a residual.
- **WebTransport needs both controls.** The shim covers window realms; the
  proxy covers the worker realm the shim cannot enter. Neither alone is
  sufficient, and the RFC must require both rather than either.

Two bounds. The proxy's WebTransport prevention is a consequence of Chromium
declining QUIC through an HTTP proxy, not a policy the proxy evaluates — a
future browser that tunnels QUIC over a proxy would falsify it, and that is the
revisit trigger. And both controls are JavaScript- and configuration-layer
rails against *site-controlled* egress. Neither is a boundary against an
admitted native adapter, which reaches the network by other means; that is
D13's standing claim and round 4 does not weaken it.

### A limitation this run created and could not remove

Round 3's IP-handling verdict was measured against a loopback UDP probe, which
is a confound: IP-handling policy governs which local interfaces may source
traffic, and loopback is not a normal candidate source. Round 4 tried to remove
it by binding a second probe on the host's real private LAN address. That
failed for an environment reason: the host's application firewall discards
inbound UDP and TCP to every non-loopback listener, confirmed outside the
browser with a minimal sender/receiver pair on the same address. Every UDP
figure above is therefore a loopback figure and **round 3's confound stands**.
It is carried forward named rather than presented as removed.

## S3 — the production destination-class rule

Every round-3 proxy verdict was measured under a deliberately inverted rule:
the corpus allowed loopback and refused everything else, where production
rejects loopback, private, link-local, multicast and metadata. Those rows were
evidence that the control *point* works, not evidence for the rule the RFC
states. Round 4 measures the rule itself.

The rule is written once and used two ways — as a pure function over an address
table and as the live classifier inside the proxy — so a unit-level result and
a live refusal cannot drift apart.

Two fail-opens were found in it during review, both of the same shape: the
classifier read a spelling differently from the socket layer that would act on
it. It detected IPv4-mapped IPv6 from the **textual** prefix, so
`0:0:0:0:0:ffff:7f00:1` — the canonical expansion of `::ffff:127.0.0.1` —
classified as `public`; and it accepted non-canonical IPv4, so `012.0.0.1`
classified as `public` while glibc resolves it to `10.0.0.1`. Detection now
works off the expanded 8-group form, and any host that is not strict-form per
`net.isIP` is refused rather than parsed.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R4-DEST-UNIT` | The production rule as a pure function | A 46-row address table covering every named class, both families, and the spellings that smuggle a forbidden address past a naive check | Each address lands in its named class | All rows match, including every spelling of a mapped address — `::ffff:127.0.0.1`, `::ffff:7f00:1` and the canonical expansion `0:0:0:0:0:ffff:7f00:1` — plus NAT64 `64:ff9b::7f00:1`, 6to4 `2002:7f00:1::`, `0.0.0.0`, `100.64.0.1`, `169.254.169.254` and `fd00:ec2::254`. It also refuses the non-canonical IPv4 spellings — `012.0.0.1`, `0x7f.0.0.1`, `2130706433`, `127.1` — as unparsable rather than guessing, because glibc's `inet_aton` resolves them to forbidden addresses while a naive parser reads them as public. Six rows are on the allowed side, so the rule is not "refuse everything" | **Unit-pass** — a pure function, not an egress result — `s3/r4-destination-class-results.json` |
| `S3R4-DEST-CONTROL` | Same destinations, same browser, an allow-all rule | Navigate to the loopback and unspecified destinations | Both reachable, or every refusal below is indistinguishable from an unreachable destination | Both returned 200; the control arm delivered 2 receipts | **Control-valid** — same |
| `S3R4-DEST-FORBIDDEN` | The production rule at the proxy | Navigate to each forbidden class in turn | Refused with the matching class named, before any socket | 10 forbidden-class arms, each refused with `destination-class-refused` and its own class; forbidden destinations received 0 | **Prevented** — same |
| `S3R4-DEST-PUBLIC` | Same rule | Navigate to a public-class destination | The rule discriminates rather than refusing everything | Decision `allowed`, class `public` | **Allowed** — same |
| `S3R4-DEST-REBIND` | Pin and flip between two **public** addresses | Flip resolution under a live pin | The class rule cannot be what refuses, so the pin must be | Pinned: allowed, class `public`. Flipped: refused, `connected-address-pin-mismatch`, classification never ran | **Pin is the operative control** — same |
| `S3R4-DEST-IP-LITERAL` | The production rule, addressed by **IP literal** rather than by a synthetic name | Navigate to `127.0.0.1`, `169.254.169.254`, `10.0.0.1` and `224.0.0.1` directly | A site does not have to use a name; the class check must apply to the spelling an attacker would actually use | Every literal reached a proxy decision and was refused with its own class; the destination received 0 | **Prevented** — same |
| `S3R4-PROXY-BYPASS-SWITCH` | Same arm, accepted command line read from `chrome://version` | Look for `--proxy-bypass-list=<-loopback>` | Chromium bypasses its proxy for loopback and link-local unless the launcher disables it, which would take those exact classes off the proxy entirely | The switch is present; Playwright passes it. Read back from the browser, not assumed | **Established, and now a named requirement** — same |

The IP-literal arm matters more than its size suggests. Every other arm
addresses its destination by a synthetic name, and a name is always proxied.
Chromium bypasses its proxy for loopback and link-local destinations by
default, so had the launcher not disabled that, the two classes the production
rule most needs to refuse would never have reached the connection point at all.
Playwright passes `--proxy-bypass-list=<-loopback>` today — confirmed by
reading the accepted command line back rather than by assuming it — but a
broker that launches the browser itself owns that switch, so correction 11 now
names it as a requirement rather than leaving it an implementation detail.

**Bound on the forbidden arms.** Only the loopback and unspecified classes can
host a listener this host will actually deliver to: `127.1.2.3` times out under
macOS routing, and the private LAN address is reset by the application
firewall, both confirmed outside the browser. The private, metadata,
link-local, multicast, CGNAT, unique-local and IPv4-in-IPv6 arms are therefore
measured at the proxy decision only. The refusal precedes any socket, so there
is no receive log to read. **The Linux arm removes this bound for the private
class**, where a real receive log exists.

## S3 — method policy at a terminating connection point

Round 3 found that Playwright routes the context-associated request client
through an HTTP proxy with CONNECT even for a cleartext `http` origin, so all
six methods reached the destination while the proxy saw only `CONNECT`. Method
policy was recorded as unenforceable at the connection point. The untested
question was whether a broker that *terminates* the tunnel can see the method.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R4-METHOD-VISIBILITY` | Broker-owned proxy terminating TLS with its own generated chain | Issue GET, HEAD, POST, PUT, PATCH, DELETE through the context request client | Whether the method is visible where the address is already enforced | The proxy observed all 6 methods; the CONNECT phase itself remains method-blind, so the visibility is attributable to termination and nothing else | Pass — `s3/r4-method-policy-results.json` |
| `S3R4-METHOD-ENFORCEMENT` | GET/HEAD policy at that proxy | Same six | Allowed delivered, others refused with the destination receiving zero | GET and HEAD returned 200 with 1 receipt each; 4 mutating methods refused with 403 and 0 receipts; the destination's own log contains only allowed methods | **Prevented** — same |

**Bound, stated in the artifact as well as here.** Enforcement is measured;
trust establishment is not. The fixture accepts the interception certificate
with `ignoreHTTPSErrors` rather than installing a profile-scoped CA into the
browser profile, which is what a production broker would have to do. That half
is untested and is carried into the blocker list. And an admitted native
adapter still bypasses the browser proxy entirely with raw egress, so this is a
rail at the connection point, not a boundary.

## S2 — an OS-level boundary for adapter-host raw egress

Correction 7 withdrew the RFC's "network restrictions" clause and stated the
consequence: raw-egress containment for a capable adapter host requires an
OS-level boundary that the Node Permission Model does not supply. Acceptance
needs either a named boundary or an explicit accepted-risk decision. None had
been named or measured.

macOS `sandbox-exec` expresses the distinction Node's single coarse `net`
permission cannot: deny `network-outbound`, then re-admit exactly the
Unix-domain socket the parent bound.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R4-OSB-CONTROL` | Child host, unsandboxed, explicit environment allowlist | Connect over the bound endpoint, then call an undeclared origin with raw `node:http` | Both succeed, or the denial below proves nothing | Native `_Page` over the endpoint; raw egress returned 200 and the destination logged 1 receipt | **Control-valid** — `s2/r4-os-boundary-results.json` |
| `S2R4-OSB-SANDBOXED` | Identical child under the sandbox profile | Same two calls | Transport survives; raw egress denied; destination receives nothing | Native `_Page` still obtained; raw egress `EPERM`; the destination received 0 from the sandboxed child | **Prevented** — same |
| `S2R4-OSB-PAIR` | Both results together | — | The pair is the point: either alone was already achievable | Transport up and raw egress denied in the same process, across 7 asserted checks in the OS-boundary arm | **Separation achieved** — same |
| `S2R4-OSB-DNS` | Same profile, a **resolvable** public name | Resolve it from inside the child | Whether name resolution is a second egress path the profile leaves open | Control resolved (2 addresses); sandboxed refused with `ECONNREFUSED` and resolved nothing | **Also denied** — recorded, not a predeclared target — same |

One fixture defect is recorded because it would have read as a working denial:
a first attempt named the socket by its uncanonicalised `/var/...` path. macOS
canonicalises before evaluating a sandbox filter and `/var` is a symlink to
`/private/var`, so the literal matched nothing and the transport was denied
along with everything else. Both spellings are now admitted.

DNS is denied too. That was not assumed: the probe uses a resolvable public
name, the control resolved it, and the sandboxed child did not. It is recorded
rather than asserted, because the row had no predeclared direction.

**Bounds.** `sandbox-exec` is deprecated by the vendor and is not documented as
a supported security boundary. The result should be read as evidence that the
separation is *expressible at the OS layer*, not as an endorsement of that
tool. It is macOS-only; no Linux or Windows equivalent was measured. And it
bounds raw network egress from the adapter host — it is not a malicious-code
sandbox and must never be described as one.

## S2 — download host verified at connection level

Round 3 recorded `downloadHostVerifiedAtConnectionLevel` as unmet with an exact
reason: `playwright install --dry-run` is the installer describing itself, not
a packet capture. Round 4 puts the broker-owned proxy on the install path and
reads the hosts actually connected to out of the proxy's decision log.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R4-DL-APPROVED` | Approved authorities declared; the three download-override variables unset | Run a real **chromium** install — the browser payload the residual is about, not a smaller stand-in — through the proxy | The install succeeds and every connected authority is approved | 3 approved hosts at connection level — `cdn.playwright.dev`, `playwright.download.prss.microsoft.com` and `storage.googleapis.com`, the last of which the installer's own `--dry-run` never names; no other authority appeared | Pass — `s2/r4-download-host-results.json` |
| `S2R4-DL-CONTROL` | Nothing declared | Same install | The install fails, proving the proxy is on the path rather than bypassed | Install exited non-zero; every CONNECT refused with `tunnel-authority-not-declared` | **Control-valid** — same |

**The measurement found something the installer's self-report does not
contain.** Round 3 derived its approved-host set from
`playwright install --dry-run`, which names `cdn.playwright.dev` and
`playwright.download.prss.microsoft.com`. Running the real **chromium** install
through the proxy with only those two declared fails: the payload redirects
from the CDN to **`storage.googleapis.com`**, the proxy refuses the undeclared
authority, and the install dies with a 403. The dry-run never names that host.

This is the entire argument for measuring at connection level rather than
trusting the installer, and it only appeared once the arm used the real browser
payload — an earlier version of this fixture installed `ffmpeg`, which comes
straight from the CDN and would have reported a clean two-host result. The
approved set is therefore three hosts, one of which is observable only at the
connection point.

**Bound.** A CONNECT tunnel exposes `host:port`, which is the granularity this
check needs, but it is still the proxy reporting on itself rather than a packet
capture. It is a strictly stronger instrument than the installer describing its
own intent, and the control arm shows the proxy is genuinely on the path.

The other half of this residual is unchanged: no vendor signature manifest
ships with the browser payload. Round 3 established that by globbing the
revision directory and matching zero. It is a vendor fact, not something this
round can change.

## S1 — per-attachment authorization

Correction 8 is correct that Playwright exposes no server-side per-attachment
authorization hook. It does not follow that the broker cannot supply one.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S1R4-ATTACH-CONTROL` | The bound endpoint, no relay | Attach twice | Both succeed, reproducing the bearer-credential finding | Both connected | **Control-valid** — `s1/r4-attachment-authorization-results.json` |
| `S1R4-ATTACH-RELAY` | Broker relay in its own `0700` run directory, holding one single-use grant | Attach twice through the relay | First authorised and transparent; second refused | First connected and read the live page title through a native `_Page`; second refused with `attachment-grant-exhausted` | **Bounded** — same |
| `S1R4-ATTACH-UPSTREAM` | Same run | Count connections at the real endpoint | A relay that refuses but still opens an upstream socket would satisfy the decision log alone | The real endpoint saw exactly 1 upstream connection across both attempts | **Prevented** — same |

**Bound.** The relay authorises attachments to *itself*. A same-uid process
that knows the underlying Playwright endpoint path attaches directly and never
meets the relay. This bounds a second consumer and an accidental re-attach, not
a malicious same-user process — the same V1 posture the RFC already states for
consumer identity, neither upgraded nor weakened. Correction 8 is refined, not
withdrawn: the *number of attachments to a broker-owned endpoint* is boundable;
the number of attachments to Playwright's own endpoint is not.

## Linux — the platform row round 3 deferred

Round 3 recorded `S3-LINUX-PROXY-BEHAVIOUR` as "Not tested. No Linux host was
available." A container supplies one. 13 asserted checks on Linux, counting the egress-and-destination driver only;
the S1 lifecycle corpus and the relay fixture report their own totals in the
rows below.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R4-LINUX-PROXY` | Broker-owned proxy as the browser's only egress path | Navigate to declared destinations | The proxy is the connection point, as on macOS | Every destination reached a proxy decision; the public class allowed, all forbidden classes refused | Pass — `s3/r4-linux-results.json` |
| `S3R4-LINUX-PRIVATE-RECEIVE-LOG` | The container's own private address, with a real listener on it | Control arm, then production arm | The private class gets the receive log macOS could not provide | Control delivered to both loopback and private; under the production rule both refused with their own class and the destination received 0 | **Prevented, with a receive log** — same |
| `S3R4-LINUX-RTC-SHIM` | Init-script shim | Peer connection against a UDP probe | The shim behaves as on macOS | Control emitted 2 STUN packets, one per binding; shim emitted 0, every binding refusing with the named `SecurityError` | **Prevented** — same |
| `S3R4-LINUX-WT-PROXY` | Proxy as the only egress path | WebTransport session | The proxy behaves as on macOS | Control 5 non-STUN UDP packets; proxied 0, `rejected:WebTransportError` | **Prevented** — same |
| `S1R4-LINUX-RELAY-REMEDY` | The broker-owned `0700` run directory, on Linux | Run the attachment-authorization fixture inside the container | Whether correction 13's remedy holds on the platform where the platform temp root does not supply confinement | 6 of 6 asserted checks pass, including the ancestor-chain construction guard | **Remedy holds on Linux** — `s1/r4-linux-attachment-authorization-results.json` |
| `S1R4-LINUX-LIFECYCLE` | Round 3's S1 corpus, unchanged, under xvfb | The full lifecycle corpus, twice | Whether the macOS lifecycle result transfers | 12 asserted lifecycle rows on Linux, 11 of 12 pass on Linux, 1 fails on Linux, reproduced across both repeats | **Partial — see below** — `s1/r4-linux-s1-bundled-r*-results.json` |

### The Linux failure is a real finding

`S1-ATTACHMENT-ENDPOINT-CONFINEMENT` fails on Linux, identically in both
repeats. The bind socket's ancestor chain is `0755, 0755, 0755, 1777` and
**no ancestor is current-user-only**. On macOS the row passes because the
per-user temporary root is `0700` at depth 3; the confinement was never a
property of Playwright, it was a property of the macOS temp layout. Linux
`/tmp` is world-writable and sticky, so the same socket sits under
world-traversable directories.

Two counter-facts travel with it, and the conclusion is the conservative
reading rather than the strong one. The same artifact records
`socketIsWorldConnectableByMode: false` — `connect(2)` on a Unix socket needs
write permission, and mode `0755` denies it to other users on both platforms —
and no row measured connectability from a second uid. The container also ran as
root. The row fails a conservative ancestor predicate; it does not demonstrate
cross-user reachability.

Combined with correction 8 — the endpoint is a bearer credential — this says
something the RFC does not currently say: **on Linux the broker must create its
own `0700` run directory and place the endpoint inside it. It cannot inherit
confinement from the platform temporary directory.** The round-4 relay fixture
already does exactly that, which is why its own confinement row passes.

Windows remains untested in every respect.

## Fixture defects corrected during this run

Recorded beside the rows they affected, in round 3's format, because six of
them changed what a row could have detected or what it concluded. The figure
verifier counts this table, so the prose count cannot drift from it.

| Defect | Rows affected | Effect on the conclusion |
| --- | --- | --- |
| The realm probe used `typeof`, which returns `'function'` for the shim as well as for the genuine constructor | Every realm row | The probe could not distinguish a patched realm from a pristine one. Rewritten to probe by **construction**; only then did the cross-origin and worker results become meaningful |
| The switch read-back compared the *requested* switch text against the accepted command line, while the fixture itself merged repeated switch names | `SWITCH-REACHED-BROWSER` for both `--disable-features` arms | The check was measuring the fixture's own merge, not the browser, and reported a false negative. Now compares the **effective** switch and each feature name separately |
| The worker escape never posted a message to the worker, so the control produced no egress | `S3R4-ESCAPE-WORKER` | The control was empty and the shim arm proved nothing. With the message sent, the escape reproduces and the finding changed from "no escape" to a confirmed escape |
| The sandbox profile named the bound socket by its uncanonicalised `/var/...` path | `S2R4-OSB-SANDBOXED` | macOS canonicalises before evaluating the filter, so the literal matched nothing and the transport was denied along with raw egress — indistinguishable from a working denial that also broke the transport |
| The public-class arm requested a port that was never declared, so `origin-not-declared` fired before the class check | `S3R4-DEST-PUBLIC` | The allow arm could not have shown the rule discriminating. Fixed to the declared port |
| The rebinding row asserted `flippedClass === undefined` where the record carries `null` | `S3R4-DEST-REBIND` | A correct finding stated with a predicate that could not pass |
| `page.evaluate` has no default timeout, and an `about:blank` iframe that never fires `load` hung the entire matrix | Whole flag matrix | The first run hung indefinitely rather than failing. Bounded timers added, plus a per-arm watchdog that records a stalled arm as a failed run rather than a missing row |
| The proxy's `close()` waited on CONNECT tunnels that outlive the client process | Download-host arm | The fixture hung at teardown and exited on an unsettled top-level await, producing no results file at all. Tunnel sockets are now tracked and destroyed |
| `execFile('npx', …)` inside an explicitly constructed environment silently resolved nothing | Download-host arm | Replaced with `process.execPath` plus the pinned local CLI |
| **The shim replaced one binding name per interface, and every probe constructed through that same name** | Every WebRTC row | `webkitRTCPeerConnection` is a second binding of the identical interface. It survived the shim and **emitted a real STUN packet**, while every arm still reported "prevented". The shim now replaces bindings by **identity** — every own property of the realm whose value is the genuine constructor — and an enumeration probe asserts no binding survives. **This changed a conclusion**: the first WebRTC closure was overclaimed |
| The download-host arm installed `ffmpeg`, a stand-in, while the residual is about the browser payload | `S2R4-DL-APPROVED` | Re-run against `install chromium`. Defect class (e): measured on a stand-in, reported as the real subject |
| `CONNECT-PHASE-STILL-METHOD-BLIND` read back a `methodVisible: false` literal the fixture had written | `S3R4-METHOD-VISIBILITY` | Derived from the CONNECT request line itself — its method is `CONNECT` and its target carries no path |
| The classifier detected IPv4-mapped IPv6 from the **textual** prefix | `S3R4-DEST-UNIT` | `0:0:0:0:0:ffff:7f00:1` — the canonical expansion of `::ffff:127.0.0.1` — classified `public`. Detection now works off the expanded 8-group form, and NAT64 and 6to4 are covered. A first fix regressed `::1` to `unspecified`; the ordering is now specials-before-embedded |
| `verify-note-figures.py` printed unclaimed figures and exited 0 | Whole note | A reworded sentence silently dropped a figure from coverage — the same failure direction as round 3's first version of this script. Unclaimed figures are now fatal, and the archive digest is derived by hashing the shipped payload instead of an un-manifested summary |
| The relay's confinement row asserted a mode the fixture had just set, using a weaker predicate than the row it claims to remedy | `S1R4-ATTACH-RELAY` | Now applies the S1 corpus's own ancestor-chain predicate |
| Refusals accepted "it failed somehow" | `S2R4-OSB-SANDBOXED`, `S1R4-ATTACH-RELAY` | The sandbox row requires exactly `EPERM`; the relay row correlates the client failure with the relay decision that produced it |
| The alias enumeration ran **after** the shim, and a replaced binding is no longer recognisable as an alias | `S3R4-ALIAS-COVERAGE` | The shim arm could only be asked about the one name it could still see — the single-name blind spot in a new place. The outcome probe now spans the names the **control** enumerated |
| The sandbox DNS probe used an `.invalid` name, which fails to resolve in both arms | `S2R4-OSB-SANDBOXED` | The row could not distinguish containment from an unresolvable name. Switched to a resolvable public name so the control resolves |
| The child host was generated **inside** the evidence tree and removed only on the success path | `S2R4-OSB-*` | An unmanifested file inside the tree is what the archive builder exists to prevent. Generated into a temporary root instead |
| The relay's ancestor predicate required current-user ownership all the way to `/` | `S1R4-ATTACH-RELAY` | No real filesystem satisfies that. Bounded at the confining ancestor, matching the S1 corpus's own semantics |
| The classifier accepted **non-canonical IPv4** spellings | `S3R4-DEST-UNIT`, every production arm | `012.0.0.1` classified `public` while glibc's `inet_aton` resolves it to `10.0.0.1` — the classic SSRF bypass family, and Linux is now in the matrix. Any host that is not strict-form per `net.isIP` is now refused rather than parsed |
| The archive builder's "measured browser version" read a key that does not exist and swallowed the error | `_env/versions.json` | It shipped `"unavailable"` while the note claimed the version was measured — the remedy carrying the defect it was written to catch. It now reads `versionObserved`, sources the macOS figure from a macOS artifact, and **raises** instead of degrading |
| The note's documented verification command exited non-zero | Whole note | Making unclaimed figures fatal broke the two-argument invocation the note prescribed, because two archive-identity figures are claimed only in the archive note. The documented command now passes all three documents |
| `DRY_RUN_HOSTS` was hand-typed, and no arm declared only those hosts | `S2R4-DL-APPROVED` | The "the dry-run omitted a host" claim compared a measurement against a literal the fixture wrote, and the causal sequence in the prose was narrated rather than run. The set is now derived from an actual `--dry-run`, and a third arm declares only those hosts and fails on the omitted authority |
| The Linux shim arm enumerated **zero** bindings and passed vacuously | `S3R4-LINUX-RTC-SHIM` | A shimmed realm cannot enumerate a binding it has already replaced. The macOS fix had been applied there but not on Linux; both now probe the names the control enumerated |
| `openssl` was spawned with the ambient environment and a bare name | Method-policy chain generation | `OPENSSL_CONF` can load a provider at startup, in the process that mints the interception CA. Now an absolute path and an explicit `{PATH, HOME, TMPDIR}` |
| Child-realm shim coverage was asserted by canonical name only | `S3R4-ESCAPE-SAME-REALM-FAMILY` | A realm where the identity replacement silently failed on one binding would still have reported "covered". Child realms are now enumerated by identity |
| `lanProbeEstablished` was written as an unconditional `false` | Whole flag matrix | A host whose firewall admitted the LAN probe would still have published `false`, preserving the loopback caveat falsely. Now derived from the measured packet count |
| `run-all.sh` did not clear its targets before running | macOS suite | A fixture dying before its `writeFileSync` left the previous run's results in place while the driver reported FAILED — the staleness the suite claims to prevent. It now deletes them first, matching `run-linux.sh` |
| The `run-linux.sh` deferral path cleared one target of three | Linux arm | A host without a container runtime kept two stale S1 artifacts while the third became a deferral stub. All three are cleared before the runtime check, and the verifier now reports a deferred arm instead of raising `KeyError` |
| The worker-escape assertion required **exact** UDP equality across two browser launches | `S3R4-ESCAPE-WORKER` | Ordinary QUIC retransmission jitter would have failed the run and read as a browser behaviour change. Both arms must egress; the exact pair is recorded |
| "The real endpoint saw exactly one upstream connection" was counted at the relay | `S1R4-ATTACH-UPSTREAM` | It is the relay reporting on its own egress, not an observation at Playwright's endpoint. The row is renamed to what it measures |
| The builder wrote `round4-evidence.tgz` while the archive ships `evidence.tgz` | Archive identity | A rebuild left two payloads and the verifier hashed the stale one. One filename now, and the archive-note generator reads it |
| `chrome://version` returns `ERR_INVALID_URL` under headless | Command-line read-back | Every arm that reads the accepted command line must run headed. Recorded because a headless read-back would have failed open |

## Sensitive-data disposition

Only synthetic inputs and redacted, bounded outputs are promoted. The archive
contains no browser profile, cookie database, trace, screenshot, download,
credential value, TLS private key, third-party package tree or browser payload.
The method-policy fixture generates its interception chain into a temporary
root outside the evidence tree and deletes it at teardown; the archive builder's
privacy gate fails closed on any PEM body regardless.

Two run-time exposures are recorded rather than omitted. The destination-class
fixture binds a listener on `0.0.0.0` for a few seconds so that one listener
answers on two address classes; it serves only synthetic content on an
ephemeral port. The connection-level download-host arm performs a real install
through the proxy, reaching the three approved Playwright download hosts, one of which — `storage.googleapis.com` — this round discovered at connection level. It is the
same egress `npm ci` and `npx playwright install` already perform.

**Round-2 incident status, carried forward unchanged.** The three exposed
session tokens were rotated by the operator and the SSH agent held no
identities; that closes agent forwarding and those three tokens. The broader
account-level exposure from that unmonitored round-2 run at the operator's uid
with the real `HOME` and no egress monitoring remains **accepted by the
approver, not excluded**. Round 4 introduced no new candidate execution: no
third-party candidate artifact was run in this round.

## Decision impact

- **D2 — browser substrate.** Unchanged. Playwright retained provisionally; S4
  closed on the approver's gate-text disposition, not on new measurement.
- **D4 — connection owns the profile.** Unchanged.
- **D7 — attachment and credential boundary.** Correction 8 refined. A
  broker-owned relay bounds attachment count to a broker-owned endpoint; the
  underlying Playwright endpoint remains a bearer credential for a same-uid
  process. **Separately, method policy reopens D7 from the other side.** A
  broker that terminates TLS to enforce it holds a key that can mint a
  certificate for any origin the profile visits and reads every cookie and
  `Authorization` header in cleartext — it moves inside the credential boundary
  D7's opaque-credential posture was drawn to keep it out of. Correction 12
  records the custody requirements; adopting method policy needs an explicit
  approver disposition on D7, not a construction note.
- **D13 — network posture.** WebRTC and WebTransport move from acceptance
  blockers to controlled channels, with two named controls that the RFC must
  now require together: a context init script and the broker-owned egress
  proxy. Method policy moves from unenforceable to enforceable at a
  *terminating* connection point. The production destination-class rule is
  measured directly instead of inheriting an inverted one. None of these is a
  boundary against admitted native code, and D13's trusted-code claim stands.
- **D16 / delivery.** Unchanged.
- **Adapter-host separation.** Correction 7's missing piece is supplied: an
  OS-level boundary exists that keeps the Playwright transport while denying
  raw egress. It is macOS-only and uses a vendor-deprecated tool.
- **Platform matrix.** Linux moves from untested to measured, and is **not** a
  clean pass: endpoint confinement fails there for a structural reason with a
  named remedy. Windows remains untested.

## Supersession notes

Append-only. Nothing above is rewritten; the RFC's `## Amendments` section is
authoritative where it and this note disagree.

- **2026-08-16 — superseded in part by round 5.** The
  [round-5 note](2026-08-16-experimental-round5.md) supersedes several records
  above, and a reader who stops here will otherwise read them as current:
  - The untested-realm residual is closed. Shared workers, service workers,
    `srcdoc`, `data:` and `blob:` frames and `window.open` popups are all
    measured, on both platforms; the division this note drew holds for every
    one of them.
  - Method-policy trust establishment is no longer untested. It is answered on
    two surfaces — a browser-side SPKI pin and a driver-side CA — neither of
    which writes to an operating-system trust store.
  - The OS-level boundary is no longer `allow default` and no longer macOS-only.
    Round 5 rebuilt it `deny default` and added a Linux network-namespace
    equivalent.
  - The Linux scope bound above records that the arm ran as root with the
    renderer sandbox disabled. Round 5 re-ran it as an unprivileged user with
    the sandbox enabled; the endpoint-confinement row still fails.
  - This note's *Sensitive-data disposition* and `S2R4-DL-APPROVED` row treat
    the platform code signature as an integrity anchor. Round 5 found it does
    **not** verify on the extracted payload, and found a signed SLSA provenance
    statement published beside the download that this round did not look for.
  - The loopback confound this note declared and could not remove is resolved:
    measured off loopback on Linux, the dispositions are unchanged.

- **2026-08-17, round 6.** Three corrections to this note's record:
  - This note's supersession bullet claims "The untested-realm residual **is
    closed**. Shared workers, service workers, `srcdoc`, `data:` and `blob:`
    frames and `window.open` popups are all measured, on both platforms."
    **Both halves are withdrawn.** The `data:` frame was never driven, so five
    realms were measured rather than six, and the residual is not closed — it
    returns as blocker item 7. See correction 16.
  - This note's line "Round 5 **re-ran** it as an unprivileged user with the
    sandbox enabled" asserts an accomplished fact, and the sandbox half of it is
    **false**: no arm in any round ran with Chromium's renderer sandbox on. See
    correction 15.
  - Its opening accounting — "of those nine, four closed outright, three closed
    but left a narrower residual, and two are unchanged", plus one new finding —
    sums to six, and the RFC's enumerated list held **seven** items after this
    round. The enumerated list under the RFC's *Current Experimental state* is
    authoritative over this summary; the summary is left in place as the record
    of what was written.
  - Every measurement in this note was taken with Chromium's renderer sandbox
    **off**. Round 6 read the state back from the browser — `Layer 1 Sandbox:
    None` on Linux, `--no-sandbox` on the macOS command line, which Playwright
    passes by default. No disposition here is withdrawn on that account, but
    none of them speaks to the configuration a production pack would ship.

## Review results

Two full passes of adversarial, security-design and quality/testability review
ran against this evidence — 58 findings in the first, 55 in the second, roughly
two thirds of the second pass new rather than re-raised. **The loop did not
converge**, for the second round running. Six findings changed a conclusion;
they are the rows marked as such in the defect table above, and the RFC's
amendment history names each one. A fifth round should expect to find more.

These reviews validate the record, not the architecture. They do not change any
Experimental exit decision, authorize acceptance, or authorize implementation.
