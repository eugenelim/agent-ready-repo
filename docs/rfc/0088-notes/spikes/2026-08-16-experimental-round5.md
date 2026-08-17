# Experimental rounds 5 (2026-08-16) and 6 (2026-08-17)

This note records the fifth and sixth RFC-0088 Experimental runs. It is
authoritative over the round-4 headline verdicts where the two disagree. The
[round-4 note](2026-08-16-experimental-round4.md) and its
[evidence archive](round4-evidence-archive.md) are preserved unchanged as that
run's audit trail; the supersessions are appended there.

The filename says `round5` because the RFC, the archive note and the figure
verifier all key off it. Round 6 is not a separate run against new questions: it
is the correction pass over round 5's own evidence base, triggered by the 64
findings round 5's review returned. Where round 5 and round 6 disagree, **round
6 wins**, and every such disagreement is named in
[Round-6 corrections](#round-6-corrections-what-the-review-falsified) rather
than silently applied.

Round 4 left seven pre-acceptance blockers. Round 5 measured three of them
closed. Round 6 re-measured and found that count too generous. The partition, which the
RFC's *Accounting* block states once and this note does not restate
differently: **two** of round 5's three closures were not real (realm coverage
returns as item 7 because a realm was never driven; the trust closure returns as
item 5, narrowed rather than reversed), **one** residual was in round 5's
artifacts but not its prose (item 6), and **one** carried item was amended in
place rather than added to (item 1, which absorbs the renderer-sandbox
withdrawal). **The honest list after round 6 is seven items
again** — not the four round 5 published. The accounting is in
[Where the blocker list actually stands](#where-the-blocker-list-actually-stands).

**One round-5 artifact was not a measurement at all.** The file promoted as the
Linux realm result was byte-identical to its macOS twin — the runner copies the
working tree into the container, so a driver that died before writing left the
macOS file at the path the runner copied back from. Three reviewers found it
independently. It is stated here, in the opening, rather than only in the
correction table, because a fabricated cross-platform result that survived
promotion is the most serious thing this evidence base has produced. Round 6
re-measured it, added a provenance block to every results file, made the runner
pre-delete container-side paths, and made the archive builder refuse two results
files sharing a digest. **Round 4's archive was re-audited for the same defect
and has no duplicate result digests**; rounds 1 to 3 promoted no cross-platform
pair.

## What changed, in one paragraph

Five of the six realms round 4 could not reach are now driven, on both platforms
— the sixth, the `data:` frame, was never driven and round 5's claim to have
cleared it is withdrawn. The init script covers every *window* realm it was
tested against — `srcdoc`, `blob:` and
a `window.open` popup — while shared workers and service workers escape it
precisely as the dedicated Worker did, and the broker-owned proxy closes all of
them. The OS-level boundary is rebuilt in the production shape the RFC asked
for, `deny default` rather than `allow default`, and given a Linux equivalent.
Method policy's trust establishment is answered on both of its two surfaces
without writing to any trust store — and the mechanism turns out to suppress
certificate errors rather than validate, which is a weaker property than
"trusts one key". Linux is re-measured as an unprivileged user, which removes
one of round 4's two caveats. **The other caveat is not removed: it is
confirmed.** Reading the accepted command line back from the browser shows
Playwright passes `--no-sandbox` by default, so every arm in every round of this
evidence base ran with Chromium's renderer sandbox off. Every macOS disposition
**this note makes** is replicated three times; every Linux disposition except the
S1 corpus is a single observation; and the rounds 3 and 4 dispositions this note
leaves standing — including the whole macOS S1 lifecycle corpus and all of S4 and
S5 — remain **unreplicated**, exactly as those rounds recorded.

## Reproduction identity and integrity

- Repository ref: `328138e5`, with the round-4 promotion applied
- Host: macOS 26.5.2 build 25F84, Darwin 25.5.0, arm64
- Node 26.4.0; npm 11.17.0; Python 3.13.13
- Playwright 1.62.0 from the same frozen lock as rounds 3 and 4, installed with
  `npm ci --ignore-scripts`; the promoted `_env/versions.json` carries the tool
  versions this run measured
- Browser channels and versions: **bundled Chromium 151.0.7922.34** and
  **system Google Chrome 151.0.7922.138** on macOS; **bundled Chromium
  151.0.7922.34** on Linux, read from `browser.version()` during this run. The
  macOS bundled figure is carried from round 4's measurement against the same
  frozen lock and was not re-measured here — `_env/versions.json` records that
  scoping rather than restating the number as freshly measured
- Linux arm: Ubuntu 24.04.4 LTS, Linux 6.8.0-100-generic arm64, Node v24.18.0,
  via `mcr.microsoft.com/playwright:v1.62.0-noble`. Run as an unprivileged user
  (uid 1001) — one of the two things round 4's Linux arm could not claim. The
  other is **not** claimed: see the sandbox row below. One arm is a further
  exception and says so: the network-namespace boundary runs as **root** (uid 0,
  child uid 0), because the container was granted `SYS_ADMIN` for it.
- **Renderer sandbox: OFF, on both platforms, in every arm.** This is read back
  from the browser, not from the flag the fixture passed. On Linux
  `chrome://sandbox` reports `Layer 1 Sandbox: None`, with PID namespaces,
  network namespaces, Seccomp-BPF and Yama ptrace protection all `No`; on macOS
  the `chrome://version` command line carries `--no-sandbox`. Playwright passes
  it by default. Round 5 claimed the opposite; see
  [correction R6-1](#round-6-corrections-what-the-review-falsified).
- Promoted package: [`round5-evidence-archive.md`](round5-evidence-archive.md)

**Replication.** Every macOS driver ran **3 times**, and `replication.json`
records each run's result. All 4 agreed across every run — and "replicated" now
means what it says: round 5's `everyDriverReplicated` was computed from
*agreement alone*, so three identical failures would have satisfied it, and a
driver that crashed before writing on every repeat dropped out of the summary
entirely, silently shrinking both the driver count and the repeat count. It now
requires the expected number of drivers to have produced results **and** every
run to have passed **and** every run to agree, with `driversExpected`,
`driversRecorded` and `everyRunPassed` all recorded separately. The Linux S1
lifecycle corpus ran twice — two runs of the same corpus, not two channels. **Every other Linux arm is n=1** — the realm
driver, the egress driver, the namespace boundary and the attachment-authorization
remedy each ran once, so round 4's single-observation disclosure is removed for
macOS and still stands for most of Linux.

All sites, pages, profiles, certificates and probes were synthetic. No live
account, personal browser profile or real credential was used. Interception key
material is generated into a temporary root outside the evidence tree and
deleted at teardown.

## Reproduction procedure

```bash
unset PLAYWRIGHT_DOWNLOAD_HOST PLAYWRIGHT_CDN_MIRROR PLAYWRIGHT_DOWNLOAD_CONNECTION
npm ci --ignore-scripts
npx playwright install chromium
./run-all.sh                 # macOS suite; 3 repeats per driver; writes replication.json
./run-linux.sh               # Linux arm; needs a container runtime
python3 verify-note-figures.py <note.md> <archive-note.md> <rfc.md>
```

`run-all.sh` deletes its targets first and regenerates every promoted macOS
artifact. `run-linux.sh` does the same for the Linux artifacts, refuses to start
if its container name is already in use, deletes container-side result paths
before each driver runs, exits **non-zero** when no container runtime exists
rather than recording a silent deferral, and writes a `missing` marker rather
than aborting when a driver produces no results file. Each driver exits non-zero
when a row it asserts fails.

Four build-time gates exist because each one catches a defect this evidence base
actually shipped:

- **Duplicate results digests** are refused — two results files with one digest
  is one file wearing two names (R6-3).
- **A results file with no `provenance` block** is refused, so a claim about a
  platform cannot rest on an artifact that does not say which platform produced
  it.
- **A deferral or missing-artifact marker at a member path** is refused. Both
  are valid JSON and `is_file()` accepted them, so a Linux arm that never ran
  would have produced a clean archive with a fresh digest.
- **An import a manifested driver needs that is not itself a member** is
  refused. Round 6 shipped an archive whose three most important drivers could
  not run from a reconstruction because `s1/provenance.mjs` was missing.

`run-linux.sh` additionally refuses to copy a container artifact back unless
that artifact's own provenance says `linux` — the check that would have caught
R6-3 where it happened rather than at archive time.

**Network access is required** for `npm ci`, `npx playwright install`, the
vendor-integrity probe and the Linux image pull.

## Current spike state

| Spike | Verdict after round 6 | What closed | What remains open |
| --- | --- | --- | --- |
| S1 | **Pass on the named gates (macOS and Linux); one platform row fails on Linux** | Linux is re-measured as an unprivileged user. Correction 13's remedy — a broker-owned `0700` run directory — passes on Linux as non-root | Endpoint confinement still fails on Linux, now reproduced against the platform's real `/tmp` rather than a harness-created directory. Windows untested. Every arm ran with the renderer sandbox off |
| S2 | **Pass on the named gates** | The OS-level boundary is rebuilt `deny default` and given a Linux equivalent. Both DNS paths and inbound bind are denied while the transport survives | An integrity anchor **is** published beside the download, but its DSSE signature is not verified against a trusted key here; the platform code signature does **not** verify on the extracted payload; egress delegated through the channels the profile must admit is unmeasured; the Linux row was measured as root |
| S3 | **Pass on the named gates** | Five previously untested realms are measured on both platforms. Method-policy trust establishment is answered on both of its surfaces without writing to a trust store | The `data:` realm was never driven. Realm coverage is not exhaustive. Trust is macOS-only, and trust and enforcement were never composed in one launch. The D7 approver disposition on method policy is unresolved. Windows untested. Every control remains a rail against site-controlled egress, not a boundary against admitted native code |
| S4 | **Pass, unchanged** | — | None |
| S5 | **Pass, unchanged** | — | Cross-consumer residue disclosed and accepted |
| S6 | **Pass, unchanged** | — | Convention amendment waits for acceptance |

No result authorizes acceptance or implementation.

## S3 — the realms round 4 could not reach

Round 4 closed the WebRTC and WebTransport blockers across four window realms
and one dedicated Worker, and recorded the rest as untested with their coverage
resting on the proxy alone — "reasoning rather than measurement". Six realms
were named; **five are driven here and one is not**. Each driven realm gets its
own UDP probe port, so a packet count names a realm rather than a launch, and
each reports its own constructor outcome, because zero packets is only
interpretable when the realm is known to have run.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R5-REALM-CONTROL` | No shim, no proxy | Each driven realm constructs `WebTransport` against its own probe | Which realms can egress at all; a realm that cannot is untestable | 5 of 5 egressed, 5 packets each: shared worker, service worker, `srcdoc` iframe, `blob:` iframe, popup | **Control-valid** — `s3/r5-untested-realms-results.json` |
| `S3R5-REALM-SHIM-WINDOW` | Context init script only | Same | Whether the shim reaches window realms it was never measured against | `srcdoc`, `blob:` and the popup all threw the named `SecurityError` and emitted **0** packets. The popup reported its own refusal to the origin's receive log | **Covered** — same |
| `S3R5-REALM-SHIM-WORKERS` | Same arm | Same | Whether shared and service workers behave like the dedicated Worker | Both reported `constructed` and emitted **5** packets each — unchanged from the control. The shim does not enter either realm | **Escape confirmed** — same |
| `S3R5-REALM-PAIR` | Init script **and** broker-owned proxy | Same | Whether the pair correction 11 mandates closes every driven realm | **Every realm 0 packets**, including both worker escapes | **Prevented** — same |
| `S3R5-REALM-LINUX` | The same driver, on Linux, non-root, renderer sandbox off | Same | Whether the platform changes the answer | Identical: the same five realms egress, the same two escape the shim, the pair closes all of them. 13 of 13, n=1 | **Prevented** — `s3/r5-linux-untested-realms-results.json` |

The result confirms correction 11's structure for the realms it reaches. The
division it drew — the init script covers JavaScript window realms, the proxy
covers what sits below them — holds for all five driven realms. Two details
matter, and the first is a correction to round 5:

- **The `data:` realm is untested, not cleared.** Round 5 reported that a
  `data:` iframe "threw `SecurityError` unprompted" and called it "not an egress
  vector". That `SecurityError` was raised in the **parent**, on cross-origin
  access to the opaque-origin frame — the realm never ran a line of probe code,
  so nothing was measured about what it can do. It is carried as untested in
  blocker item 7.
- **A service worker outlives its page.** That was the sharpest reason the
  untested-realm residual mattered, and the proxy closing it is what settles
  that part of the residual; the shim never would have.

**Coverage bound.** Five realms driven is not "every realm a site can reach".
Sandboxed iframes (`<iframe sandbox>`), nested cross-origin frames, workers
created *by* a service worker, and realms already present in a restored profile
are all untested. Round 5's claim of exhaustive realm coverage is withdrawn.

## S3 — method-policy trust establishment

Round 4 proved method policy is enforceable once the broker terminates TLS, but
accepted the interception certificate with `ignoreHTTPSErrors` — a blanket
"trust anything" no production broker can ship. The residual asked for a
profile-scoped CA, and correction 12 added that such a thing is not uniformly
achievable because Chromium on Linux reads a shared per-user NSS database.

There turn out to be **two trust surfaces, not one**, and conflating them is why
a first version of this fixture failed every arm identically. Playwright's
context-associated request client — the exact client rounds 3 and 4 identified
as the method-policy problem — performs its TLS in the **driver process**, not
in the browser.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R5-TRUST-BROWSER-CONTROL` | No trust mechanism | Navigate to the interception certificate | Must FAIL, or the certificate was already trusted and nothing below means anything | Navigation failed; destination received 0 | **Control-valid** — `s3/r5-mitm-trust-results.json` |
| `S3R5-TRUST-BROWSER-PINNED` | `--ignore-certificate-errors-spki-list` carrying our key's SPKI hash | Same | The navigation succeeds | 200, body `trusted-ok`, 1 receipt, within 8 asserted checks in the trust arm | **Trust established** — same |
| `S3R5-TRUST-BROWSER-WRONG-KEY` | The same switch carrying a **different** key's hash | Same | Must fail, or the switch is a blanket bypass rather than a pin | Failed; destination received 0 | **It is keyed to one SPKI** — same |
| `S3R5-TRUST-SURFACE-SPLIT` | The same launch that succeeded above | Use the **context request client** instead of a navigation | Whether a browser switch reaches the driver's TLS | The navigation succeeds and the request client **fails on the identical certificate** | **Two surfaces, two anchors** — same |
| `S3R5-TRUST-PIN-SCOPE` | The pinned key, but a certificate carrying the **wrong name** for it | Navigate to it under the same pin | Whether the switch trusts a *key* or suppresses *errors* for that key | Accepted: 200, 1 receipt. A name mismatch is not enforced for a pinned key | **Asserted: it suppresses errors; it does not validate** — same |
| `S3R5-TRUST-DRIVER` | `NODE_EXTRA_CA_CERTS` in the broker process; then a wrong CA | Request through the client | Trust established for the driver, and scoped | No trust: fails, 0 receipts. Correct CA: 200, 1 receipt. Wrong CA: fails, 0 receipts | **Trust established; scoped to the process, not the destination** — same |

**This answers the residual with something narrower than it asked for — and the
mechanism must be described accurately.** An SPKI pin scopes to one public key
rather than an issuer, lasts one launch rather than the life of a profile, and
writes to no trust store at all. What it does *not* do is validate: a
certificate carrying the pinned key but the **wrong name** is also accepted,
measured above. The switch *suppresses certificate errors* for connections
presenting that key. That is still tightly bounded — reaching it requires the
broker's own private key — but "trusts exactly one key" would overstate it, and
a broker relying on this must not rely on name checking for pinned connections.

**Four bounds, three of which round 5 did not carry.**

- The pin travels on the command line, so it is readable by any process that can
  read the browser's argv on the same host — the same same-uid posture the RFC
  already states.
- **The driver anchor is issuer-wide.** `NODE_EXTRA_CA_CERTS` adds a CA to the
  *whole Node process*, so it is scoped to the broker process but not to the
  interception destination: any connection that process makes will accept any
  certificate that CA issues. The "and scoped" in the row above means
  process-scoped, and nothing narrower.
- **Trust and enforcement were never composed.** Round 4 measured method
  enforcement with `ignoreHTTPSErrors`; round 5 measured trust establishment
  without method policy. No arm in any round has run a terminating broker that
  both establishes trust properly *and* refuses a method. That composition is
  assumed, not measured.
- **No Linux arm.** Every trust row is macOS-only. Correction 12's NSS caveat
  concerned Linux specifically; it does not *arise* for the SPKI pin because no
  store is written, but that reasoning has not been checked against a Linux
  browser.

Establishing trust does not narrow what the terminating broker then sees:
correction 12's custody requirements for decrypted request material stand
unchanged, and the D7 disposition is still required.

## S2 — the OS-level boundary, in the production shape

Correction 14 recorded round 4's boundary honestly: `allow default` plus a
targeted `deny network-outbound`, with `network-bind` unconditional, and "a
production profile should start from `deny default`".

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R5-DENY-DEFAULT-CONTROL` | Unconfined child | Transport, TCP egress, DNS, bind, artifact write | All succeed, or the confined arm proves nothing | Transport up; egress 200 with 1 receipt; DNS resolved; bind succeeded, across 10 asserted checks in the deny-default arm | **Control-valid** — `s2/r5-deny-default-boundary-results.json` |
| `S2R5-DENY-DEFAULT-CONFINED` | `(deny default)` plus only what the host needs, re-admitting **only** the bound Unix socket | Same | Transport survives; every network path denied; artifacts still writable | Native `Page` over the transport; TCP `EPERM` with 0 receipts; `resolve4` `ECONNREFUSED`; `getaddrinfo` `ENOTFOUND`; bind denied; artifact write still succeeded | **Separation achieved in the production shape** — same |
| `S2R5-LINUX-BOUNDARY` | Linux, `unshare -rn`: a new user namespace plus an empty network namespace; destination bound **off loopback**; **running as root** in a `SYS_ADMIN` container | Same pair | Whether Linux has an equivalent at all | Transport survives; raw egress denied; the off-loopback destination received **0**. 7 of 7, n=1 | **Linux equivalent exists** — `s2/r5-linux-os-boundary-results.json` |

Under `deny default` the network denials need no explicit rule — they are the
default, which is the whole difference from round 4's shape. The two DNS paths
the security review named as the concrete unmeasured class are both denied and
both **asserted**, including `getaddrinfo`, which macOS proxies through a system
daemon.

**Bounds.** `sandbox-exec` remains vendor-deprecated and undocumented as a
security boundary; this is evidence the separation is expressible at the OS
layer, not an endorsement of the tool. `file-read*` is broad in the profile
because Node and Playwright must be readable — this bounds network reach, not
filesystem reach. **The profile must also admit `mach-lookup` and
`ipc-posix-shm` for Node to execute at all, and egress delegated through those
channels to an already-running system service was not probed** — the two DNS
paths were, which is the class the review named, but the general delegation
question is open. The Linux mechanism denies **all** egress rather than a
destination class, so it is the adapter-host boundary and not a replacement for
the broker-owned proxy. It also needs unprivileged user namespaces, which some
distributions restrict; the container needed `SYS_ADMIN` because Docker's
default seccomp profile blocks `unshare(CLONE_NEWNET)`; **and the arm ran as
root**, so it does not show an unprivileged adapter host confining itself.
Windows has no measured equivalent.

## S2 — vendor integrity: an anchor that exists, and one that does not verify

Round 3 established that no signature manifest ships **inside** the browser
payload, by globbing the installed revision directory. Nobody had asked the
other question: whether the vendor publishes an anchor **beside** the download.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R5-ANCHOR-CONTROL` | The download URL taken from `playwright install --dry-run`, redirects followed | HEAD the archive | The archive resolves, or every 404 below is just an unreachable host | Final status 200, 187,406,357 bytes | **Control-valid** — `s2/r5-vendor-integrity-results.json` |
| `S2R5-ANCHOR-PROBE` | 9 candidate anchor locations beside the archive | HEAD each, following redirects | Whether any anchor is published | 8 404. One **200**: `chrome-mac-arm64.zip.intoto.jsonl`, 5,201 bytes | **An anchor is published** — same |
| `S2R5-ANCHOR-BINDS` | That anchor, and the archive bytes | Fetch both; hash the archive; compare to the statement's subject digest | Whether the anchor binds this artifact or merely exists | DSSE envelope, `application/vnd.in-toto+json`, predicate `https://slsa.dev/provenance/v0.2`, 1 signature; the subject `sha256` **matches** the fetched archive | **It binds** — same |
| `S2R5-CODE-SIGNATURE` | The installed payload | `codesign -dv` (display) and `codesign -v` (verify), plus a Gatekeeper assessment, with the full diagnostic captured | Whether the anchor round 3 recorded actually validates | Signature **present**; verification **fails**; Gatekeeper rejects with "code has no resources but signature indicates they must be present" | **Present but does not verify** — same |
| `S2R5-IN-PAYLOAD` | The installed revision directory | Re-glob for `*.sig`, `*.asc`, `*.sha256`, `CHECKSUMS*`, `SHA256SUMS*`, `*.sigstore` | Round 3's finding, re-verified | Zero matches | **Unchanged** — same |

Two results pulling in opposite directions, and the RFC needs both.

**The residual was too pessimistic in one direction.** A signed SLSA provenance
statement is published beside the download and binds the artifact by digest.
Round 3 could not have found it, because it looked only inside the installed
payload. A build can verify the payload it downloads against a signed statement.

**And too optimistic in another.** Round 3's `S2-PLATFORM-CODE-SIGNATURE` row
recorded "Signed" using `codesign -dv`, which *displays* signing information
rather than validating it. Under `codesign -v` the extracted payload does not
verify, and Gatekeeper rejects it. The RFC's stated integrity position — digest
pinning **plus** the platform code signature — therefore rests on digest pinning
and the newly-found attestation, not on the code signature.

**Bounds.** The DSSE envelope's signature is not verified against a trusted key
here; doing so requires establishing the signer's identity, which this round did
not do. What is established is that a signed statement exists and that its
subject digest matches the bytes served. The in-toto subject name is `_` rather
than the archive filename, so the binding is by digest alone. **The
code-signature failure is not diagnosed.** The Gatekeeper message points at
resources missing relative to the signature, which is consistent with Playwright
extracting the archive in a way that does not preserve the signed bundle — it is
*not* evidence of a tampered payload, and it is also not evidence of an intact
one. Distinguishing "extraction broke the seal" from "the seal was never valid"
needs a comparison against a vendor-extracted copy, which this round did not do.
The result is macOS-specific and describes the payload after Playwright extracts
it.

## S1 — Linux without one of round 4's two caveats

Item 1 said acceptance would be admitting Linux on evidence gathered as root
with the renderer sandbox off. It is now non-root. It is **still** sandbox-off,
and round 6 established that this is true of every arm on every platform.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S1R5-LINUX-IDENTITY` | The Linux arm as configured | Read the process identity, and read the sandbox state back **from the browser** | Whatever it actually got — asserted, not asked for | uid 1001, `runningAsRoot: false`. `chrome://sandbox`: `Layer 1 Sandbox: None`, `rendererSandboxActive: false` | Pass — the read-back succeeded; **the state it read is sandbox-off** — `s3/r5-linux-results.json` |
| `S1R5-LINUX-CONFINEMENT` | Round 3's S1 corpus, unchanged, twice, as an unprivileged user, walking ancestors to `/` | The full lifecycle corpus | Whether the confinement failure was an artefact of running as root | 11 of 12 pass, twice; `S1-ATTACHMENT-ENDPOINT-CONFINEMENT` still fails. ancestor modes `0755, 0755, 0755, 1777, 0755` — depth 3 is the platform's real `/tmp`, not owned by the current user — `confinedByAncestorDepth: null`, `ownedByCurrentUserThroughout: false` | **Fails as an ordinary user, against the real platform temp root** — `s1/r5-linux-s1-bundled-r*-results.json` |
| `S1R5-LINUX-REMEDY` | Correction 13's broker-owned `0700` run directory, on Linux, non-root | The attachment-authorization fixture | Whether the remedy holds where the platform temp root does not supply confinement | 6 of 6 pass, n=1 | **Remedy holds for the relay endpoint only** — `s1/r5-linux-attachment-authorization-results.json` |
| `S3R5-LINUX-OFF-LOOPBACK` | A UDP probe on the container's private address | The egress arms | Whether round 3's loopback confound was hiding anything | Control 2 STUN packets and 5 non-STUN UDP; proxied 2 STUN and **0** non-STUN | **Confound resolved, and now asserted rather than recorded** — `s3/r5-linux-results.json` |

Two of these matter beyond their rows. The confinement failure **strengthens
under correction**: round 5 walked only four ancestors and ran under a
harness-created `TMPDIR`, so it measured a directory the harness had made.
Round 6 removed the depth cap and the override, and the chain now reaches the
platform's real `/tmp` at mode `1777` and `/` above it, with no confining
ancestor anywhere and the chain not owned by the current user throughout. The
finding is a property of the platform temporary root, which is exactly what the
RFC needs it to be. And the off-loopback probe resolves round 3's confound — the
loopback probe was not hiding anything. The proxy stops WebTransport and does
not stop WebRTC, off loopback exactly as on it, which is why the shim is the
control that matters for WebRTC.

## Round-6 corrections: what the review falsified

Round 5's review returned 64 findings across three reviewers. These are the ones
that changed a published conclusion rather than tightening a test. Each is a
withdrawal of something round 5 asserted.

| # | Round-5 claim | What round 6 measured | Status |
| --- | --- | --- | --- |
| R6-1 | "Linux is re-measured with Chromium's renderer sandbox **enabled**", asserted from `RFC88_NO_SANDBOX !== '1'` | That predicate reads a value the fixture set moments earlier. Read back from the browser, `chrome://sandbox` reports `Layer 1 Sandbox: None` on Linux and the macOS command line carries `--no-sandbox`: Playwright passes it by default | **False, withdrawn.** One of round 4's two Linux caveats is not removed. It now applies to macOS too |
| R6-2 | "Six realms measured"; the `data:` iframe "is not an egress vector" | The `SecurityError` came from the **parent's** cross-origin access to an opaque-origin frame. The realm never executed probe code | **Withdrawn.** Five realms driven; `data:` is untested |
| R6-3 | The Linux realm artifact, promoted as a Linux measurement | It was byte-identical to its macOS twin (SHA `5bbcf6d4…`). The runner copies the working tree in, so a driver that dies before writing leaves the macOS file where the runner copies back from | **Withdrawn and re-measured.** Every results file now carries a provenance block with platform, uid and a per-run nonce; the runner pre-deletes container-side paths; the archive builder refuses two results files with one digest |
| R6-4 | The Linux confinement chain, reported as four `0755` ancestors and nothing above them | The walk was capped at depth 4 under a harness-created `TMPDIR`, so it never reached `/tmp`. Uncapped and un-overridden, the chain reaches `/tmp` at `1777` and `/`, still unconfined | **Finding survives, measurement corrected.** It is now about the platform, which is what the RFC claims |
| R6-5 | `NO-OS-TRUST-STORE-WRITE` and `RENDERER-SANDBOX-ENABLED` counted among passing checks | Neither can fail: the first asserts a store the fixture never writes to, the second re-reads a fixture variable | **Removed from the pass totals**, and the pin-scope row was promoted from `recorded` to asserted in its place, so the trust arm now asserts 8 checks — none of them the two that could not fail |
| R6-6 | The two DNS denials described in prose as measured | They were recorded, not asserted — a row that cannot fail the run | **Now asserted.** Deny-default is 10 checks, not 8 |
| R6-7 | The alias-union fix from round 4 | Reintroduced in round 5's new `r5-linux.mjs`, which enumerated RTC bindings *after* the shim — where a replaced binding is no longer recognisable — narrowing the probe to one name | **Fixed in `r5-linux.mjs` only, and round 6's own review caught the other half:** `r5-untested-realms.mjs` had the same defect in `NO-ALIAS-SURVIVES-THE-SHIM`, whose `names.length > 0` guard could not fail because the one name matching by identity always survives enumeration. The artifact showed it plainly — the control enumerated `{RTCPeerConnection, webkitRTCPeerConnection}` and the shimmed arm enumerated only `{RTCPeerConnection}`. Both drivers now union with the control's names and require more than one. **This is the second time a remedy for this class shipped carrying the class** |
| R6-8 | `run-linux.sh` recorded a deferral and exited 0 when no runtime was present | A driver exiting 0 regardless of outcome is the failure mode this evidence base has repeated in every round | **Exits 1** and clears all six targets |

| R6-9 | `NO-ALIAS-SURVIVES-THE-SHIM` on macOS, counted in the realm arm's pass total | Its `names.length > 0` guard could not fail: a shimmed realm cannot *enumerate* a binding it has already replaced, so only the canonical name — which matches by identity — ever appeared, and the alias that motivated the whole check was silently out of scope. `r5-linux.mjs` had been fixed; this driver had not | **Fixed, and the corrected check first went red.** The shimmed arm now *constructs* every name the control enumerated rather than enumerating its own. That turned the row red — `webkitRTCPeerConnection` was genuinely unaccounted for on macOS — and green again once measured properly: it throws the named `SecurityError`. A companion check asserts the control saw more than one RTC binding, so a union of one cannot pass |

Two further findings did not change a conclusion but change how a conclusion may
be *used*: the SPKI pin suppresses errors rather than validating (folded into
the trust section above), and `NODE_EXTRA_CA_CERTS` is issuer-wide for the
process (same).

## Fixture defects corrected during this run

20 fixture defects are recorded here, in rounds 3 and 4's format, covering both
rounds: the nine round 5 corrected and eleven more from round 6. The figure
verifier counts this table, so the prose count cannot drift from it — and it
caught this very sentence claiming 18 against a 17-row table. The **nine**
defects that changed a *published conclusion* are listed separately as R6-1 to
R6-9 in the section above and are **not** repeated here; they are a different
cut of the same run, not additional rows, so 17 and 9 are counts of two
different things rather than a total and a subtotal.

| Defect | Rows affected | Effect on the conclusion |
| --- | --- | --- |
| The trust fixture resolved a synthetic hostname that only the **browser's** resolver knows, so all three arms failed on `getaddrinfo ENOTFOUND` | Every trust row | The control "passed" for the wrong reason entirely — a DNS failure reading as a TLS rejection. Switched to an IP SAN addressed by literal |
| The browser arms used the context request client, whose TLS happens in the driver | `S3R5-TRUST-BROWSER-*` | A browser launch switch cannot reach it, so the pinned arm failed and the mechanism looked broken. Browser arms now navigate; the driver surface is measured separately, and the split is asserted |
| The vendor-integrity fixture guessed the archive path and revision and 404'd its own control | `S2R5-ANCHOR-*` | Every candidate "absent" result was unreadable. The URL is now taken from `playwright install --dry-run` |
| Anchor probes treated any non-200 as absent, and the CDN answers every path with a 307 | `S2R5-ANCHOR-PROBE` | The no-anchor-published check passed on redirects alone. Redirects are now followed and the final status recorded — which is how the published attestation was found |
| The code-signature row asked `codesign -dv` | `S2R5-CODE-SIGNATURE` | Display is not verification. Adding `codesign -v` changed the finding: the signature does not validate |
| The code-signature row recorded a verdict without the verifier's diagnostic output | `S2R5-CODE-SIGNATURE` | "Does not verify" with no reason cannot be distinguished from a broken invocation. The full `codesign` and `spctl` output is now captured and bounded |
| The `deny default` profile omitted the canonicalised temporary paths | `S2R5-DENY-DEFAULT-CONFINED` | Artifact writes were denied for a path-spelling reason, not a policy one — the same `/var` → `/private/var` canonicalisation that bit round 4 |
| The Linux runner aborted on the first failed `docker cp` under `set -e` | Whole Linux arm | One driver that produced no output hid every later Linux result. Missing artifacts now write a `missing` marker and the arm continues |
| The realm driver launched headed inside a container with no display | Linux realm rows | All three arms launch-failed and the driver reported 0 of 2 with empty details. Now run under xvfb, and a launch failure is itself an asserted check |
| Three browser launches in close succession segfaulted Chromium on this host | Realm arms | An arm that never launched would have been recorded as a realm result. Arms are spaced, a launch is retried once, and `ALL-ARMS-LAUNCHED` fails the run |
| Two concurrent runner invocations shared one container name | Whole Linux arm | Artifacts went missing and one corpus truncated to 5 of 5, which read as fixture defects rather than as a collision. The runner now refuses to start if the name is in use |
| The sandbox read-back tried `chrome://sandbox` and `chrome://version` on the same page | Sandbox rows | The failed first navigation left the page unable to load the second, so the read-back reported "unavailable" on a platform where it works. A fresh page per instrument |
| The first sandbox read-back derived its verdict from a summary phrase | Sandbox rows | It produced `adequatelySandboxed: true` alongside `Layer 1 Sandbox: None` — a self-contradicting pair. The verdict is now derived from the Layer 1 row |
| The S1 corpus guard asserted only the failing set | Linux S1 rows | A run that asserted 5 rows instead of 12 satisfied it. It now asserts 12 asserted and 11 passed |
| The figure verifier exited 0 when a derived figure was claimed nowhere | Every figure | A reworded sentence silently dropped a figure out of coverage. Unclaimed figures are now fatal |
| The figure verifier matched claim patterns across the whole RFC | Every figure | With four rounds of figures accumulated, a round-5 pattern collided with a correct round-3 sentence. Patterns are now round-scoped |
| An inserted comment contained unescaped backticks inside a template literal | `S2R5-LINUX-BOUNDARY` child | The generated child script did not parse, and the arm read as a boundary denial rather than a syntax error |
| The off-loopback IP-handling arm was a **fourth launch with options byte-identical to the proxied arm**, and its numbers were published as a separate result | `S3R5-LINUX-OFF-LOOPBACK` | It measured the same thing twice and reported it as corroboration. The duplicate launch is removed, the proxied arm's own numbers are the record, and the figure is now asserted rather than recorded — the R6-6 gap, still standing in this driver |
| The Linux runner ran the **root** namespace arm before the unprivileged arms in the same container | Whole Linux S1 arm | Playwright's per-run temp directory name is deterministic, so the root arm created `/tmp/pw-<hash>` and the S1 corpus — running as uid 1001 — then failed with `EACCES` binding its socket inside a root-owned directory. It aborted five scenarios deep and reported `asserted 5, passed 5` with a `fatal`, which reads as a clean 5-of-5 run unless you open the artifact. The root arm now runs **last**, and root-owned temp directories are cleared before each unprivileged arm so ordering is not the only protection. The harness had accidentally reproduced the very finding the RFC makes: the platform temporary root supplies no confinement between accounts |
| The S1 driver wrote a complete results file and then **never exited** | Whole Linux S1 arm | It held an open handle for 56 minutes on 12 seconds of CPU, and `\|\| true` meant the runner could not tell a non-exiting driver from a slow one. The driver now exits once stdout has drained — a bare `process.exit()` would discard the pending write, which round 3 recorded — and every container driver runs under `timeout 900`, so a driver that never exits fails its arm instead of stalling the run |

## Where the blocker list actually stands

Round 5 published a four-item list. Round 6 finds that understated, and the
honest count is **seven**. Nothing was closed on paper and then quietly
reopened: two round-5 closures rested on findings R6-1 and R6-2 above, and two
residuals existed in round 5's evidence without appearing in its prose.

| # | Item | Origin |
| --- | --- | --- |
| 1 | Accepted OS/browser support matrix — Linux only with a broker-owned `0700` run directory; Windows untested; **and every arm in every round ran with the renderer sandbox off** | Carried, amended by R6-1 |
| 2 | Browser-payload integrity: the attestation is unverified against a trusted key, and the code signature does not verify and is undiagnosed | Carried, reshaped in round 5 |
| 3 | Three of eight cross-consumer residue classes survive teardown | Carried, unchanged |
| 4 | D7 disposition on method policy — an approver decision | Carried, narrowed |
| 5 | Method-policy trust is macOS-only, was never composed with method enforcement in one launch, and both anchors are destination-unscoped | Closure was not real — narrowed, not reversed |
| 6 | The OS boundary's delegated-egress path is unmeasured, and the Linux row was measured as root | Round-5 residual, unpublished until now |
| 7 | Realm coverage is five realms, and is not exhaustive: `data:`, sandboxed iframes, nested frames, service-worker-spawned workers and restored-profile realms are untested | R6-2 |

Mapping to spikes, so the list stays a true union: S1 → 1; S2 → 1, 2, 6;
S3 → 1, 4, 5, 7; S5 → 3. S4 and S6 contribute none.

## Sensitive-data disposition

Only synthetic inputs and redacted, bounded outputs are promoted. The archive
contains no browser profile, cookie store, credential value, TLS private key,
third-party tree or browser payload. The trust fixture generates its key
material into a temporary root outside the evidence tree and removes it on
process exit.

Two run-time exposures are recorded rather than omitted. The vendor-integrity
fixture downloads the 187 MB browser archive from the vendor CDN in order to
hash it — the same egress `npx playwright install` already performs. The Linux
container is granted `SYS_ADMIN` for the network-namespace row; it runs only
this evidence and is removed on exit.

**Round-2 incident status, carried forward unchanged.** The three exposed
session tokens were rotated and the SSH agent held no identities; that closes
agent forwarding and those three tokens. The broader account-level exposure from
that unmonitored round-2 run remains **accepted by the approver, not excluded**.
Rounds 5 and 6 executed no third-party candidate artifact.

## Decision impact

- **D7 — "What is the credential primitive?" (`auth: browser-session`).** Correction 13's remedy is now
  measured on Linux as a non-root user, against the platform's real temporary
  root. The credential-boundary consequence of method policy is unchanged and
  still needs an approver disposition.
- **D13 — "What is the security claim?" (adapters are exact-digest trusted code with defence in depth).** Correction 11's structure is confirmed for the five
  realms driven, on both platforms. Method policy's trust establishment no
  longer requires a trust store, but the mechanism suppresses errors rather than
  validating. Nothing here converts a rail into a boundary — and the renderer
  sandbox, which is the one process-level boundary Chromium supplies for free,
  was off in every measurement this evidence base contains.
- **D17 — "What blocks a vulnerable embedded runtime dependency?" (a Node lockfile scanner wired into `build-check`).** Two changes in opposite
  directions: a signed provenance attestation is published beside the browser
  payload and binds it by digest; and the platform code signature the RFC relied
  on does not verify on the extracted payload, for an undiagnosed reason.
- **Adapter-host separation.** The boundary exists in the production profile
  shape on macOS and has a Linux equivalent measured as root. Delegated egress
  through the channels the profile must admit is unmeasured. Windows remains
  unmeasured.
- **Platform matrix.** Linux is measured as an unprivileged user, and admitting
  it requires the broker-owned `0700` run directory. Windows remains untested in
  every respect. No platform has been measured with the renderer sandbox on.

## Review results

Recorded in the RFC's amendment history. **The loop has not converged across
rounds 3, 4, 5 and 6**, and round 6 is the clearest case rather than the
weakest.

Round 6's own corrections were put through the same four-lens pass its
predecessors were — adversarial, security-design, quality/testability, and a
cold reader given only the RFC and the promoted notes. All four returned
blockers, and their findings converged:

| What the pass found | Reviewers who found it independently |
| --- | --- |
| The promoted archive was not import-closed — `s1/provenance.mjs`, the module carrying round 6's central remedy, was not a member, so three manifested drivers could not run from a reconstruction | adversarial, quality |
| "Every results file now carries a provenance block" was **false**: 4 of 10 did, and the three Linux S1 files — the ones produced by the very `docker cp` path that created the R6-3 stand-in — carried none | adversarial, quality, security |
| The four promoted macOS artifacts predated the round-6 fixture fixes, so a manifested driver and its manifested result could not both be current | adversarial, quality |
| The code-signature row asserted a type check the fixture guarantees, so the finding it is quoted for had no predicate that could detect its own negation | adversarial, quality |
| `S3R5-TRUST-PIN-SCOPE` was `recorded`, not asserted — and it is the sole basis for deleting a normative requirement from correction 12 | adversarial, quality, security |
| `run-linux.sh`, a manifested member, still asserted the withdrawn sandbox claim in its own comments | adversarial, security |
| Three browser-surface trust refusals were inferred from a bare `ok === false`, which a launch crash satisfies | adversarial, quality |
| `PAIR-ARM-REALMS-ACTUALLY-RAN` was satisfied by key presence, so two realms' zeros were not backed by evidence the realm ran | adversarial, quality |
| The published archive's own reconstruction script carried a stale expected digest, so the published verification procedure failed on the archive it shipped with | cold reader |

Two findings are worse than the rest, and both are recurrences rather than new
defects:

- **`NO-ALIAS-SURVIVES-THE-SHIM` carried the defect its own remedy exists to
  catch** (R6-9). Round 4 found a single-name shim leaking a real STUN packet.
  Round 5 reintroduced it in a new file. Round 6 fixed that file — and left the
  identical defect standing in the macOS driver, in a check whose entire purpose
  is to detect it, counted in a pass total. **That is the second consecutive
  round in which a remedy for this class shipped carrying the class.**
- **The provenance remedy was not applied where the defect actually bit.** R6-3
  was a macOS artifact promoted as a Linux measurement, produced by the
  container copy-back path. The fix stamped provenance into four files and left
  the three copy-back artifacts — including the one Decision B turns on —
  carrying nothing that says which platform produced them.

Everything in the table above is fixed, re-measured and re-verified in this
note's current figures. That is not a claim of convergence: it is the fourth
consecutive round where the corrections themselves needed correcting, and the
honest reading is that this evidence base's defect rate has not yet fallen to a
level where a clean pass would mean much. A seventh round should expect to find
more.

These reviews validate the record, not the architecture. They do not change any
Experimental exit decision, authorize acceptance, or authorize implementation.

## Supersession notes

- **2026-08-16, round 6.** Round 5's claims that Linux ran with the renderer
  sandbox enabled, that six realms were measured, and that the `data:` realm is
  not an egress vector are **withdrawn** — see
  [Round-6 corrections](#round-6-corrections-what-the-review-falsified). Round
  5's four-item blocker list is superseded by the seven-item list above. Round
  5's Linux realm artifact was a promoted macOS file and has been re-measured.
