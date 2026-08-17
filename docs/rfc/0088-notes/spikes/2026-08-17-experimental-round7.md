# 2026-08-17 Experimental rounds 7 and 8

This note records the seventh and eighth RFC-0088 Experimental runs. It is
authoritative over the rounds-5-and-6 headline verdicts where the two disagree.

The filename says `round7` because the RFC, the archive note and the figure
verifier key off it. **Round 8 is not a separate run against new questions: it is
the correction pass over round 7's own evidence base**, triggered by what round
7's review found — and what it found was not in the architecture. It was in round
7's own instruments, four of which were mutation-proven unable to fail. Where
rounds 7 and 8 disagree, **round 8 wins**, and every such disagreement is named
in [Round-8 corrections](#round-8-corrections-what-the-review-falsified) rather
than silently applied. The
[rounds 5 and 6 note](2026-08-16-experimental-round5.md), the
[round-4 note](2026-08-16-experimental-round4.md) and their evidence archives are
preserved unchanged as those runs' audit trails; supersessions are appended
there.

Round 6 left **seven** pre-acceptance blockers. Round 7 measured against three of
them and the subject held up; round 8 then found that several of round 7's own
*claims* about that were not supported by its own instruments. **The count after
round 8 is six**, and one item closes — but not for the reason round 7 gave.

**Round 7's headline was wrong and is withdrawn.** It claimed to be "the first
round in four to close on measurement rather than correct its predecessor". Two
entries in the RFC's own audit trail falsify that — round 4 and round 5 each
recorded "blockers closed on measurement" — and round 7 did correct its
predecessor, reversing round 6's profile-minimum claim and amending five
corrections. What round 7 could honestly claim is narrower: **it is the first
round whose new measurements found no defect in the architecture.** Whether its
closures survive is a question only round 9 can answer, and asserting otherwise
is the inference this evidence base has been punished for five times.

The reason round 7 could measure anything new is that round 6 stopped guessing.
Three of its residuals were phrased as "this was never measured" rather than
"this is how it behaves" — the renderer-sandbox condition, the profile minimum,
and the trust/enforcement composition. Each proved answerable in a single
experiment, and two answers went the design's way.

## What changed, in one paragraph

**The renderer-sandbox condition is removed from the whole evidence base.**
Correction 15 recorded that no arm in any round had run with Chromium's renderer
sandbox on, and that a design intending to ship sandboxed must re-measure. It is
re-measured: `chromiumSandbox: true` works on both platforms, and the egress
rails behave **identically** — same realms egressing, same two worker escapes,
same pair closing everything, byte-for-byte the same packet counts. **The
`data:` realm is measured properly**, and the answer is richer than either
previous round: it is not a WebTransport vector because it is not a secure
context, but it *is* a live WebRTC vector, and the init script covers it. **The
platform code signature is diagnosed**: it is ad-hoc, and extraction is
exonerated. **Trust and method enforcement are composed in one launch** for the
first time. And **three of the OS profile's operation classes turn out not to be
required at all** — a child holding the Playwright transport runs with `signal`,
`mach*` and `ipc*` all denied. Two of those three, `mach*` and `ipc*`, are the
ones that raised round 6's delegated-egress concern, so denying them dissolves it
rather than merely bounding it.

## Reproduction identity and integrity

- Repository ref: `820990de` (the rounds 4-6 promotion, merged)
- Host: macOS 26.5.2 build 25F84, Darwin 25.5.0, arm64
- Node 26.4.0; npm 11.17.0; Python 3.13.13
- Playwright 1.62.0 from the same frozen lock as rounds 3 to 6, installed with
  `npm ci --ignore-scripts`
- Browser channels and versions: bundled Chromium 151.0.7922.34 and system
  Google Chrome 151.0.7922.138 on macOS; bundled Chromium 151.0.7922.34 on Linux
- Linux arm: Ubuntu 24.04.4 LTS, Linux 6.8.0-100-generic arm64, Node v24.18.0,
  via `mcr.microsoft.com/playwright:v1.62.0-noble`. **Every Linux arm in this
  round runs as an unprivileged user (uid 1001), including the namespace
  boundary** — which round 6 could only measure as root.
- **Renderer sandbox: measured BOTH WAYS.** Every sandbox-mode figure in this
  note is read back from the browser, and a run whose observed mode disagrees
  with the requested mode **fails** rather than quietly reporting the other
  configuration. On Linux `chrome://sandbox` reports `Layer 1 Sandbox:
  Namespace` with PID namespaces, network namespaces, Seccomp-BPF, TSYNC and
  Yama ptrace protection all `Yes`; on macOS the read-back is the accepted
  command line with `--no-sandbox` absent.
- Promoted package: [`round7-evidence-archive.md`](round7-evidence-archive.md)

**Measured sandbox states, verbatim from the artifacts.** Listed rather than
paraphrased so the figure verifier can check each one and a reader can see the
raw values instead of a summary sentence:

```
macOS sandbox-off observedActive: false
macOS sandbox-on  observedActive: true
Linux sandbox-off observedActive: false
Linux sandbox-on  observedActive: true
opaque realm RTC bindings constructed: 2
every RTC binding refused under the shim: yes
promoted artifacts carrying an undeclared failing row: none
declared expected failure: S1-ATTACHMENT-ENDPOINT-CONFINEMENT (the platform finding)
without the added capability `unshare -rn` is unavailable
`runningAsRoot: false`
_env/versions.json records: macOS off-arm: OFF (instrument: chrome://version command line); macOS on-arm: ON (instrument: chrome://version command line); Linux off-arm: OFF (instrument: chrome://sandbox); Linux on-arm: ON (instrument: chrome://sandbox). NOTE: the macOS instrument reads the accepted command line and infers the sandbox from the ABSENCE of --no-sandbox; only the Linux chrome://sandbox instrument observes sandbox state directly. Playwright passes --no-sandbox by default; see correction 15.
```

**The two instruments are not equally strong, and the difference matters.** On
Linux `chrome://sandbox` reports sandbox *state*. On macOS there is no such page,
so the read-back checks the accepted command line and infers the sandbox from the
**absence of `--no-sandbox`**. That rules out Playwright's default but does not
observe that the renderer is sandboxed: a sandbox that failed to initialise for
any other reason would still read `true`. The macOS rows in the table below are
marked accordingly, and item 1 carries the asymmetry.

The two macOS values differing is what makes the comparison a comparison: a run
whose observed mode disagrees with its requested mode fails, so neither figure
can silently be the other configuration. The two modes therefore **differed**
rather than being one configuration measured twice.

**Replication.** Every macOS driver and mode ran with **3 repeats per
driver/mode**, and `replication-r7.json` records each run. All ten agreed, all
passed, and each run carries its own nonce — `everyRunHasItsOwnNonce: true` —
which is what makes three recorded runs three *executions* rather than one
result logged three times. Every Linux arm is a single observation.

**Provenance.** All three Linux artifacts report `platform: linux` in their own
provenance blocks, at uid 1001; the runner refuses to copy back an artifact that
does not.

All sites, pages, profiles, certificates and probes were synthetic. No live
account, personal browser profile or real credential was used. Interception key
material is generated into a temporary root outside the evidence tree and
deleted at teardown. The 187 MB browser archive the code-signature arm downloads
is extracted outside the evidence tree and removed; it is never promoted.

## Reproduction procedure

```bash
unset PLAYWRIGHT_DOWNLOAD_HOST PLAYWRIGHT_CDN_MIRROR PLAYWRIGHT_DOWNLOAD_CONNECTION
npm ci --ignore-scripts
npx playwright install chromium
./run-all-r7.sh              # macOS suite; 3 repeats per driver/mode; writes replication-r7.json
./run-linux-r7.sh            # Linux arm, all unprivileged; needs a container runtime
python3 verify-note-figures-r7.py <note.md> <archive-note.md> <rfc.md>
```

Both runners keep round 6's hardening and add to it. `run-all-r7.sh` writes its
replication state to a per-run `mktemp` file rather than a fixed path in the
world-writable temp root, and its summary now records a **per-run nonce** for
each execution — round 6's summary recorded only `(passed, total, verdict)`,
which are identical by construction and so could not distinguish three runs from
one result counted three times. `run-linux-r7.sh` runs every unprivileged arm
before any privileged one, clears root-owned temporary directories between arms,
bounds every driver with `timeout 900`, and refuses to copy an artifact back
unless that artifact's own provenance block says `linux`.

## Current spike state

| Spike | Verdict after round 7 | What closed in round 7 | What remains open |
| --- | --- | --- | --- |
| S1 | **Pass on the named gates (macOS and Linux); one platform row fails on Linux** | Nothing new — S1 was not re-run | Endpoint confinement still fails on Linux against the real `/tmp`; correction 13's remedy confines the *relay* endpoint, not Playwright's own. Windows untested |
| S2 | **Pass on the named gates** | The code signature is diagnosed: ad-hoc, extraction exonerated. The profile minimum is measured, and `mach*`/`ipc*`/`signal` are **not** required even with the transport in use | The DSSE attestation signature is still unverified against a trusted key. `file-read*` breadth is required and has never been composed with the Node permission model. Windows untested |
| S3 | **Pass on the named gates** | The `data:` realm is measured. Trust and method enforcement are composed in one launch. Every rail is re-measured with the renderer sandbox on, on both platforms | One realm this harness cannot drive; restored-profile realms untested. No Linux trust arm. Every control remains a rail against site-controlled egress, not a boundary against admitted native code |
| S4 | **Pass, unchanged** | — | None |
| S5 | **Pass, unchanged** | — | Cross-consumer residue disclosed and accepted |
| S6 | **Pass, unchanged** | — | Convention amendment waits for acceptance |

No result authorizes acceptance or implementation.

## S3 — the renderer sandbox, measured rather than disclosed

Correction 15 withdrew round 5's "sandbox enabled" claim as **false** and
generalised it: Playwright passes `--no-sandbox` by default, so no arm in rounds
3 to 6 ran with Chromium's renderer sandbox on. It also stated the consequence —
sandbox-off makes site content that achieves renderer code execution a same-uid
actor, a class three corrections declare unprotected — and required a design
shipping sandboxed to re-measure.

Re-measuring with a **new** fixture would be a stand-in. The realm driver is
therefore parameterised: the same driver, the same assertions, one launch option
changed, and a check that fails if the observed mode is not the requested one.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R7-SANDBOX-CAPABILITY-LINUX` | The container arm, unprivileged | Launch with `chromiumSandbox: true` and read `chrome://sandbox` | Whether the sandbox can be enabled at all here | `Layer 1 Sandbox: Namespace`; PID namespaces, network namespaces, Seccomp-BPF, TSYNC and Yama ptrace all `Yes` | **The sandbox works** — `s3/r7-linux-realms-sandboxed-results.json` |
| `S3R7-REALMS-SANDBOX-OFF` | The round-6 configuration, as a control | The five-realm matrix | Reproduce round 6, or the comparison has no baseline | Control 5 packets per realm; shim closes the three window realms; both workers escape; pair closes all | **Baseline reproduced** — `s3/r5-untested-realms-results.json` |
| `S3R7-REALMS-SANDBOX-ON-MACOS` | Same driver, `chromiumSandbox: true` | Same | Whether the rails behave differently sandboxed | **identical**, per realm and per arm | **No difference** — `s3/r7-realms-sandboxed-results.json` |
| `S3R7-REALMS-SANDBOX-ON-LINUX` | Same driver, sandbox on, uid 1001 | Same | Whether the platform changes the answer | **Identical** again | **No difference** — `s3/r7-linux-realms-sandboxed-results.json` |

**What this closes, and what it does not.** It closes the re-measurement
requirement: the egress rails do not depend on the sandbox being off, so every
rail figure in rounds 3 to 6 stands in the sandboxed configuration too. It does
**not** retroactively sandbox those rounds' other arms — the S1 lifecycle
corpus, S4 and S5 were not re-run — and it does not change correction 15's
threat-model point, which is about what a design ships rather than about what a
rail measures. A design shipping sandbox-off still accepts the same-uid
consequence.

## S3 — the `data:` realm, and why round 5 could not see it

Round 5 recorded the `data:` iframe as "not an egress vector at all" on a
`SecurityError`. Round 6 withdrew that: the error came from the **parent**, on
cross-origin access to an opaque-origin document, and the realm never executed a
line of probe code.

The mistake was the instrument, not the realm. An opaque-origin frame cannot be
read from its parent by design — but Playwright holds a frame handle and can
evaluate inside it. That is how a zero becomes interpretable: the realm is proved
to have run before its silence is read as anything.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R7-OPAQUE-REALM-RAN` | A `data:` iframe, no controls | Read a marker out of the realm through a Playwright frame handle | Whether the realm executes at all | `ran: 1`, `origin: "null"`, `isSecureContext: false` | **The realm runs** — `s3/r7-opaque-realm-webrtc-results.json` |
| `S3R7-OPAQUE-WEBTRANSPORT` | Same realm | `typeof WebTransport` | Whether the interface is even present | `undefined` — WebTransport requires a secure context | **Not a WebTransport vector, for a measured reason** — same |
| `S3R7-OPAQUE-RTC-CONTROL` | Same realm, no controls | Construct every RTC binding the realm exposes, against its own UDP probe | Whether the realm can egress | **Both** `RTCPeerConnection` and `webkitRTCPeerConnection` constructed, and the probe received STUN | **It IS a live WebRTC vector** — same |
| `S3R7-OPAQUE-RTC-SHIMMED` | Context init script installed | Same | Whether the shim reaches a realm the parent cannot read | Both bindings threw the named `SecurityError`; probe received **0** | **Prevented** — same |
| `S3R7-OPAQUE-REALM-LINUX` | Same driver, uid 1001 | Same | Whether the platform changes the answer | Identical | **Prevented** — `s3/r7-linux-opaque-realm-webrtc-results.json` |
| `S3R7-OPAQUE-REALM-SANDBOXED` | Same driver, sandbox on | Same | Whether the sandbox changes the answer | Identical | **Prevented** — `s3/r7-opaque-realm-webrtc-sandboxed-results.json` |

**Round 5's conclusion was accidentally right for one interface and wrong for
the other.** "Not a vector" holds for WebTransport — but because the interface
is absent in a non-secure context, which nobody had established, and not because
the realm is inert. For WebRTC it was simply wrong: the realm exposes two
bindings, constructs both, and emits STUN. Had the design shipped on round 5's
claim, an opaque-origin frame would have been an uncovered WebRTC path on the
reasoning that it was "not a vector at all". The init script does cover it, so
the outcome is safe — but the claim was not evidence.

**Two realms are still untested rather than covered, for two different
reasons.** A worker created *by* a service worker **was driven and emitted
nothing with no controls installed**, which means either it cannot reach the
network or this harness cannot get code into it — and the round-5 error was
calling the second of those the first. A realm already present in a **restored
profile was not driven at all** in this round: no fixture creates one, so nothing
was measured about it, and saying it "emitted nothing" would repeat exactly the
error this round corrected. Its standing answer is correction 11's requirement
that the runtime register the shim before any document exists and refuse to
attach to a browser started without both controls — a requirement, not a
measurement.

### Two further realms, driven and closed

Correction 16 named four realms as untested. Two of them are measured here, in a
separate driver, and both close — which is why the untested list shrinks to two
rather than to three.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R7-SANDBOXED-IFRAME` | `<iframe sandbox="allow-scripts">` fetching a real document from the origin, no controls | The frame constructs `WebTransport` against its own probe | Whether an opaque-origin *sandboxed* frame can egress | 4 packets — it can | **Capable** — `s3/r7-opaque-realms-results.json` |
| `S3R7-NESTED-CROSS-ORIGIN` | A `srcdoc` frame embedding a second document, two levels deep, no controls | Same | Whether nesting evades the controls | 4 packets — it can | **Capable** — same |
| `S3R7-BOTH-CLOSED-BY-THE-PAIR` | Init script **and** broker-owned proxy | Same | Whether the pair closes both | **0 packets each** | **Prevented** — same |
| `S3R7-SW-SPAWNED-WORKER` | A worker created *by* a service worker, no controls | Same | Whether the realm can be driven at all | **0 packets with no controls installed** — so the realm either cannot reach the network or cannot be reached by this harness | **Untested, not covered** — same |

**One reconciliation the reader needs.** This driver records the `data:` realm as
silent, while the driver in the previous section records it emitting STUN. Both
are correct and they measure different things: this one probes `WebTransport`,
which is **absent** in a non-secure context, so silence is expected; the other
probes `RTCPeerConnection`, which is present, and it egresses. The `data:` realm
is a WebRTC vector and not a WebTransport vector, and each driver saw the half it
probed.

**Coverage bound.** Six realms driven across rounds 4-7 is not "every realm a
site can reach".

## S3 — trust and method policy, composed

Round 4 proved method policy is enforceable at a TLS-terminating connection
point but accepted the interception certificate with `ignoreHTTPSErrors`. Round 5
proved trust is establishable without a trust store but installed no method
policy. Round 6 recorded the gap: no arm had ever run a broker that did both, so
the composition was assumed.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3R7-COMPOSED-CONTROL` | The identical child with **no** CA | Six methods through the context request client | Must fail on TLS, or trust was never required and nothing below is evidence | Every method failed with a certificate error; destination received **0** | **Control-valid** — `s3/r7-trust-and-method-composed-results.json` |
| `S3R7-COMPOSED-WRONG-CA` | An unrelated CA | Same | Must also fail, or the anchor is a blanket acceptance | Failed; destination received **0** | **The anchor is matched** — same |
| `S3R7-COMPOSED` | `NODE_EXTRA_CA_CERTS` **and** a GET/HEAD policy at the terminating proxy, in one launch, no `ignoreHTTPSErrors` | Same | Whether trust and enforcement compose | Allowed two delivered `200`; refused four returned `403`; destination received **only** the allowed methods; the method was visible at the terminating point for all six. 8 of 8 pass | **They compose** — same |
| `S3R7-NO-BLANKET-BYPASS` | The child's own source | Grep it | Whether a bypass crept back in | No `ignoreHTTPSErrors`, no `rejectUnauthorized: false`, no `NODE_TLS_REJECT_UNAUTHORIZED` | **Asserted on the artifact, not on a flag the fixture set** | same |

**Bounds, unchanged by this result.** This composes the **driver** surface,
which is the surface rounds 3 and 4 identified as the method-policy problem. The
browser surface — page navigation under an SPKI pin — is a separate anchor and is
not composed here. `NODE_EXTRA_CA_CERTS` remains issuer-wide for the process and
is inherited by children, so the adapter-host environment allowlist must exclude
it (correction 17). And the terminating broker still reads every cookie and
`Authorization` header in cleartext, which is the D7 disposition and is not a
thing measurement can settle. There is no Linux arm for this composition.

## S2 — the code signature, diagnosed

Round 3 recorded the extracted payload as "Signed" using `codesign -dv`, a
*display* subcommand. Round 5 ran `codesign -v`, found it does not verify, and
withdrew the pass. Round 6 captured Gatekeeper's diagnostic and stopped there,
recording that this is neither evidence of a tampered payload nor of an intact
one and that separating the two needs a comparison against a vendor-extracted
copy no round had run.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R7-EXTRACTION-CONTROL` | The archive from the installer's own `--dry-run` | Extract three ways: Playwright's own install, `ditto -x -k`, `unzip` | All three must yield a bundle, or a "does not verify" is a missing-file result | All three yielded the app bundle | **Control-valid** — `s2/r7-code-signature-diagnosis-results.json` |
| `S2R7-EXTRACTION-EXONERATED` | The three trees | `codesign -v` on each | Whether a metadata-preserving extraction verifies where Playwright's does not | **All three fail identically**, same message | **Extraction is not the cause** — same |
| `S2R7-SIGNATURE-KIND` | The same bundle | `codesign -dvvv` | What the signature *is*, not whether a verifier liked it | `Signature=adhoc`, `flags=0x20002(adhoc,linker-signed)`, `TeamIdentifier=not set`, no `Authority=`, `Sealed Resources=none` | **Ad-hoc: no signing identity at all** — same |

**This is a stronger statement than "does not verify", and it settles the
question in the direction that closes it.** An ad-hoc signature is produced by
the linker and carries no identity: no team, no authority, nothing binding the
bundle to Google. It cannot anchor integrity for anyone, under any extraction,
and a build that controlled its own extraction would gain nothing. Round 3's
"Signed" was wrong one level deeper than round 5 found — not the wrong
subcommand against a real signature, but the right subcommand against a
signature that asserts nothing.

Browser-payload integrity therefore rests on **the digest the build pins
itself**, plus the published SLSA attestation *once its signer identity is
established*. That second half is untouched by this round and remains item 2.

## S2 — the OS profile's real minimum

Round 6 corrected the RFC's description of the `deny default` profile — it
admits the whole `process*`, `mach*`, `ipc*` and `file-read*` classes — and
recorded the honest bound: because no arm ever narrowed the profile, "these
classes must be admitted for Node to execute" states an unmeasured minimum.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R7-MINIMUM-BASELINE` | The round-5/6 profile | Run a trivial Node child under `sandbox-exec` | Must succeed, or every narrower arm fails for an unrelated reason | Ran, artifact written | **Control-valid** — `s2/r7-profile-minimum-results.json` |
| `S2R7-MINIMUM-DROP-ONE` | One class denied at a time | Same | Which classes are actually required | Required: `process`, `sysctl`, `fileRead`. **Not required: `signal`, `mach*`, `ipc*` — three classes** | **The stated minimum was wrong** — same |
| `S2R7-MINIMUM-DERIVED` | Only the required classes | Same | Whether the derived minimum runs | Ran, artifact written | **It does** — same |
| `S2R7-TRANSPORT-UNDER-MINIMAL` | The **full boundary fixture** under `RFC88_PROFILE=minimal`, `mach*`/`ipc*`/`signal` denied | Transport, TCP egress, both DNS paths, inbound bind, artifact write | Whether an adapter host holding the Playwright transport still works | Native `Page` over the transport; TCP `EPERM` with 0 receipts; both DNS paths denied; bind denied; artifact write works. 10 of 10 pass | **The transport does not need them** — `s2/r7-deny-default-minimal-results.json` |

**Round 6's claim is false, and the correction is in the design's favour.**
Three classes are not required, and the two classes that raised the
delegated-egress concern — `mach*` and `ipc*` — are among them, so they need not
be admitted at all and there is nothing to delegate *through*: the delegation
worry dissolves rather than being bounded. The narrowed profile is measured against the
real fixture, not a trivial child, which is the case that matters.

**What remains.** `file-read*` **is** required, and it is unrestricted in this
profile — so an adapter host confined by it can read the live browser profile off
disk, the defeat correction 9 exists to prevent. No arm has composed this profile
with the Node permission model that supplies that confinement. That is the
residual item 6 keeps.

## S2 — the Linux boundary, unprivileged

Round 6 measured the network-namespace boundary as **root** (uid 0) in a
`SYS_ADMIN` container and recorded plainly that this shows the mechanism exists,
not that an unprivileged adapter host can confine itself with it.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2R7-NETNS-UNPRIVILEGED` | `unshare -rn`, launched by uid 1001 with `runningAsRoot: false`; destination bound off loopback | Transport, then raw egress | Whether an unprivileged parent can establish the boundary | Control: transport and egress both work, 1 receipt. Confined: transport survives, raw egress denied, destination received **0**. 8 of 8 | **An unprivileged parent can, inside a SYS_ADMIN container** — `s2/r7-linux-netns-unprivileged-results.json` |

**One field needs stating precisely rather than glossed.** The artifact records
`uid: 1001` for the parent and `childUid: 0` for the confined child. That is
`unshare -r` doing what it is for: it creates a new **user** namespace and maps
the invoking user to root *inside it*. The child's uid 0 is namespace-local. The
process was started by an unprivileged account, which is the question round 6
asked, and reading `childUid: 0` as "still running as root" would invert the
finding.

**Bounds.** A network namespace denies **all** egress rather than a destination
class, so it is the adapter-host boundary and not a replacement for the
broker-owned proxy. It still needs unprivileged user namespaces, which some
distributions restrict. The container was granted `SYS_ADMIN` for round 6's arm
and retains it here, so this shows an unprivileged *user* succeeding, not an
unprivileged *container*. Windows has no measured equivalent.

## Round-8 corrections: what the review falsified

Round 7's review ran four lenses — adversarial, security-design,
quality/testability, and a cold reader given only the RFC and the promoted notes.
All four returned blockers, and the quality pass established its findings by
**mutation testing**: changing an artifact and confirming the control still
reported clean. That is why these are withdrawals rather than opinions.

**Every one is a defect in round 7's instruments or documents. None is in the
architecture.** That distinction is the round's most important output and it cuts
both ways: the subject held up under every new test, and the apparatus that
established it did not.

| # | Round-7 claim or control | What round 8 established | Status |
| --- | --- | --- | --- |
| R8-1 | The figure verifier checked every "N of N pass" figure | It compared the note's own numerator against `total` and **never read `passed`**. Mutation-proven: an artifact at `passed: 3` with a failing check verified clean against a note claiming "8 of 8 pass" | **Withdrawn.** Both numbers now derive separately, plus a blanket fact refusing any promoted artifact with an undeclared failing row |
| R8-2 | `build-archive.py` refused to promote a failing artifact | Its gate accepted any artifact whose `recorded` key was present — and **every fixture writes `recorded` unconditionally**, so it never fired. A mutated 2-of-8 artifact with six failing rows passed it | **Withdrawn.** The gate now fails on any failing row and admits a known negative only when the artifact *declares* it by id; a stale declaration also fails |
| R8-3 | The archive's environment record described the run | `_env/versions.json` said the renderer sandbox was **OFF on both platforms** — in the round headlined "measured both ways" — because the builder read the round-5/6 artifacts. No verifier fact read the file | **Withdrawn.** It reads all four round-7/8 arms and is now covered by a fact |
| R8-4 | The required/not-required operation classes were derived | Only their **count** was. The class *names* were literals in the verifier's own pattern, so an artifact stating `mach` **is** required validated a note stating it is not | **Withdrawn.** Both lists derive from the artifact, compared as sorted sets |
| R8-5 | `round7-docs` scoping protected correct history | It excluded the **RFC entirely**. Mutation-proven: rewriting the RFC's copies of the signature field and the Linux Layer-1 row to wrong values still verified clean (the wrong values are described rather than spelled here, because spelling them would trip the very patterns that now check them) | **Withdrawn.** Unambiguous round-7 literals are now checked against the RFC too; only genuinely colliding patterns stay round-scoped |
| R8-6 | "The destination's independent log records only the allowed methods" | The check filtered the **proxy's own decision log** — itself computed as `ALLOWED_METHODS.has(...)` — and asserted those entries were in `ALLOWED_METHODS`. Literal against itself. The destination's receive log was never read | **Withdrawn and re-measured.** The destination's own log is now the ground truth and records exactly `GET, HEAD` |
| R8-7 | `methodVisible: true` showed the method was visible at the terminating point | A literal the fixture's own proxy stamped on every entry | **Withdrawn.** Replaced with a check that all six methods were **readable** on the tunnelled request line |
| R8-8 | The rails behave identically "on both platforms" with the sandbox on | On Linux only the sandbox-**on** arm had run, so "identical" had no named Linux baseline — and round 6 had caught a fabricated byte-identical Linux artifact on this very driver | **Measured.** The Linux sandbox-off arm now exists: 14/14, uid 1001, `observedActive: false`. The comparison is real on both platforms |
| R8-9 | The Linux namespace boundary is established by an unprivileged parent, so round 6's root caveat is removed | **Confounded.** The container held `--cap-add=SYS_ADMIN`, and Docker's seccomp relaxes its `unshare` argument filter when that capability is present. Re-run with **no added capability**, `unshare -rn` is **unavailable** | **Withdrawn.** Round 6's root caveat is *replaced by a capability caveat*, not removed. That arm's rows now assert the finding |
| R8-10 | "`file-read*` is required and unrestricted" | The `without-fileRead` arm granted nine broad read subpaths **unconditionally**, so dropping the class removed only the unrestricted clause. What was measured was "something outside those nine paths must be readable" | **Re-measured.** The class is now denied outright and the finding survives: `file-read*` genuinely is required |
| R8-11 | The profile-minimum conclusion was asserted | `required.length > 0` cannot fail — `sandbox-exec` cannot exec Node without `(allow process*)`. The conclusion the RFC carries lived only in `recorded` | **Fixed.** `MACH-IPC-AND-SIGNAL-ARE-NOT-REQUIRED` and `FILE-READ-IS-GENUINELY-REQUIRED` are now rows that can go red |
| R8-12 | `everyDriverReplicated` meant every driver ran the repeats | `distinctRunIds == runs` is satisfied at `runs == 1`, and `repeats` was a flattened average, so a driver replicated **once** could sit inside a summary reporting three | **Fixed.** Per-driver repeats are asserted and gate the suite's exit status |
| R8-13 | The unprivileged netns claim was asserted | No row asserted it. The same artifact and the same 7-of-7 would be produced by a root run — round 6's row exactly | **Fixed.** `PARENT-IS-UNPRIVILEGED` is now a row, and the runner's copy-back gate refuses a root artifact for the unprivileged arms |
| R8-14 | Two realms "both emitted nothing with no controls installed" | Only one did. **No round-7 fixture creates a restored-profile realm**, so nothing was measured about it — and claiming otherwise repeats precisely the error round 6 corrected round 5 for | **Withdrawn.** One realm was driven and silent; the other was never driven |
| R8-15 | Correction 16's untested list shrank to two realms | A promoted artifact — `s3/r7-opaque-realms-results.json` — measured the sandboxed iframe and the nested cross-origin frame as capable-and-closed, and was **cited in no scenario row of any note**. The list shrank on evidence nobody could see | **Fixed.** Both realms now have scenario rows citing that artifact |

**The pattern across rounds is now unambiguous.** Round 4's `typeof` probe, round
5's `RFC88_NO_SANDBOX` predicate, round 6's alias check and `everyDriverReplicated`,
round 7's `or True` in the figure verifier — and now four more mutation-proven
controls. **Six consecutive rounds in which the measurement apparatus carried the
defect it was built to detect.** The subject has been getting steadily more
solid; the instruments have not converged, and every conclusion in this evidence
base rests on them.

## Fixture defects corrected during this run

15 fixture defects are recorded here. The figure verifier counts this table, so
the prose count cannot drift from it. Six changed a conclusion and are marked.

**Six of these fifteen are defects in the round's own instruments, found by its
own review**, and four of those six would have let a wrong figure or a failing
artifact through. That is the sixth consecutive round in which the measurement
apparatus carried the defect it was built to detect, and it is the reason this
note does not claim the loop converged.

| Defect | Rows affected | Effect on the conclusion |
| --- | --- | --- |
| The `data:` realm was probed from its **parent**, which cannot read an opaque origin | Every `data:` row | **Conclusion-changing.** Round 5 read the parent's `SecurityError` as the realm refusing to egress. Reaching into the realm through a Playwright frame handle shows it runs, exposes two RTC bindings, and emits STUN — a live vector recorded as "not a vector at all" |
| `run()` returned `stderr: ''` on the success path, and `codesign` writes its report to stderr even when it succeeds | `S2R7-SIGNATURE-KIND` | **Conclusion-changing.** The presence check read an empty string and reported "no signature" for a bundle that plainly carries one, which would have buried the ad-hoc finding entirely. Replaced with `spawnSync`, which preserves both streams on both paths |
| The composed child reported `ignoreHttpsErrorsUsed: false`, a field it set and never changed | `S3R7-NO-BLANKET-BYPASS` | A constant dressed as a measurement — the defect class this evidence base has reproduced in every round. Replaced with a check on the child's **source**, which would fail if the bypass were reintroduced |
| The **code-signature** fixture's original conclusion row was satisfied by a disjunct that could not fail | `S2R7-EXTRACTION-*` | It would have passed whatever the arms showed. Replaced with `EXTRACTION-IS-NOT-THE-CAUSE`, which goes red if a metadata-preserving extraction ever starts verifying. **An earlier version of this row attributed the defect to the profile-minimum fixture and the remedy to this one** — the row itself was wrong, in the table whose subject is wrong rows |
| The profile-minimum fixture asserted `required.length > 0`, which cannot fail on this platform | `S2R7-MINIMUM-*` | `sandbox-exec` cannot exec Node without `(allow process*)`, so at least one class is always required. The conclusion the note and RFC carry — that `mach*`, `ipc*` and `signal` are **not** required — was in `recorded` and asserted nowhere. It is now its own check |
| `verify-note-figures-r7.py` compared each "N of N pass" claim against `total` and never read `passed` | Every pass-count figure | **Conclusion-changing.** Mutation-proven: an artifact at `passed: 3` with a failing check verified clean against a note claiming "8 of 8 pass". Both numbers are now derived separately, and a blanket fact refuses any promoted artifact carrying a failing row |
| `build-archive.py`'s failing-artifact gate accepted any artifact whose `recorded` key was present | Every promoted artifact | **Conclusion-changing.** Every fixture writes `recorded` unconditionally, so the gate never fired and a 2-of-8 artifact with six failing rows would have been promoted. The gate now fails on any failing row, and admits a known negative only when the artifact **declares** it by id |
| `_env/versions.json` described the renderer sandbox as OFF on both platforms | The whole archive's environment record | **Conclusion-changing.** The builder derived it from the round-5/6 sandbox-off artifacts, in the round whose headline is "measured both ways", and no verifier fact read the file. It now reads all four round-7 arms and is covered by a fact |
| The composed arm's "destination received only the allowed methods" compared the **proxy's own decision log** against the policy that produced it | `S3R7-COMPOSED` | Literal against itself: the log was filtered on `decision === 'allowed'`, itself computed as `ALLOWED_METHODS.has(...)`. The destination's independent receive log was never read. It now is, and records exactly `GET, HEAD` |
| `methodVisible: true` was a literal the fixture's proxy stamped on every decision entry | `S3R7-COMPOSED` | Asserting it measured nothing. Replaced with a check that every one of the six methods was **readable** on the tunnelled request line, which is only observable because the broker terminates TLS |
| `createService` had no route hook, so the nested and sandboxed realms were nearly synthesised in the parent | `S3R7-OPAQUE-*` | A realm fetching a document the parent invented is not the realm's own capability. An opt-in `extraRoutes` map was added, consulted only when supplied so every existing caller is byte-identical |
| The round-7 Linux runner dropped the `chown -R pwuser:pwuser /w` round 6 had | Whole Linux arm | `docker cp` runs as root, so `/w` was root-owned and all three unprivileged arms failed with `EACCES` writing their own results. The runner reported three `MISSING ARTIFACT` rows and exited 1 rather than passing silently |
| `-e RFC88_SANDBOX=on` was placed after the container name in the `docker exec` argv | Linux sandboxed realm row | Docker parsed `-e` as the command to run. Caught by the same missing-artifact gate |
| The replication summary recorded only `(passed, total, verdict)` | Every replicated row | Those are identical by construction across repeats, so the summary could not distinguish three executions from one result counted three times. It now records a per-run nonce and asserts they are distinct |
| The figure verifier derived the Linux Layer 1 sandbox value from an expression containing `or True`, so it always yielded `Namespace` whatever the artifact said | `S3R7-SANDBOX-CAPABILITY-LINUX` | **Conclusion-changing.** A hard-coded literal dressed as a derivation, inside the one tool whose job is catching hard-coded literals — it would have validated this round's headline sandbox claim against itself. It now reads the `Layer 1 Sandbox` row out of what `chrome://sandbox` actually printed and falls back to `UNKNOWN` rather than to the expected answer. **This is the fifth consecutive round in which an instrument carried the defect it was built to detect** |

## Sensitive-data disposition

Only synthetic inputs and redacted, bounded outputs are promoted. The archive
contains no browser profile, cookie store, credential value, TLS private key,
third-party tree or browser payload. The privacy gate was exercised in anger
this round: the code-signature arm's diagnostics contain absolute paths under
the operator's home and cache directories, and the promoted artifact carries
`<home>` and `<tmp>` placeholders instead — verified by grepping the promoted
file for `/Users/`, which returns nothing.

Numeric uids are promoted deliberately, on the reasoning recorded in the
rounds-5-and-6 archive note: the Linux uids are container accounts and are
load-bearing for the unprivileged claim, and the macOS uid is the default
first-user id, carrying no name, path, handle or directory identifier.

**Round-2 incident status, carried forward unchanged.** The three exposed session
tokens were rotated and the SSH agent held no identities; that closes agent
forwarding and those three tokens. The broader account-level exposure from that
unmonitored round-2 run remains **accepted by the approver, not excluded**. Round
7 executed no third-party candidate artifact.

## Where the blocker list stands

Round 6 published seven items. Round 7 closes one and shrinks four; the count is
**six**. Nothing is closed on paper and quietly reopened, and nothing is merged
to make the number smaller — collapsing item 6 or 7 into item 1 would shrink the
count while hiding distinct open questions, which is the failure this evidence
base has been correcting for four rounds.

| # | Item | Round-7 disposition |
| --- | --- | --- |
| 1 | Accepted OS/browser support matrix | **Shrinks.** The renderer-sandbox condition is removed: measured on with identical results on both platforms. Windows untested; Linux needs the broker-owned `0700` relay directory and Playwright's own endpoint stays unconfined. **Absorbs item 5's residual** (no Linux trust arm) |
| 2 | Browser-payload integrity | **Sharpened, still open.** The code signature is diagnosed as ad-hoc and is not an anchor under any extraction. The DSSE attestation signature remains unverified against a trusted key. Integrity rests on the pinned digest |
| 3 | Cross-consumer residue | Unchanged; disclosed and accepted |
| 4 | D7 disposition on method policy | Unchanged — an approver decision. Round 7 makes it *more* decidable: the composition is now demonstrated rather than assumed |
| 5 | *(was: method-policy trust)* | **CLOSED.** The composition is measured with a valid control. Its other three bounds are documented mechanism properties, not open questions. The remaining platform gap folds into item 1 |
| 6 | OS-level boundary | **Shrinks.** Delegated egress dissolves — `mach*`/`ipc*` are not required, and the transport works with them denied. Linux netns measured unprivileged. Remaining: `file-read*` breadth, never composed with the Node permission model |
| 7 | Realm coverage | **Shrinks.** The `data:` realm is measured. Remaining: a service-worker-spawned worker this harness cannot drive, and restored-profile realms |

Renumbered, the list is: 1 support matrix · 2 payload integrity · 3 residue ·
4 D7 · 5 OS boundary (`file-read*` composition) · 6 realm coverage.

Mapping to spikes, so the list stays a true union: S1 → 1; S2 → 1, 2, 5;
S3 → 1, 4, 6; S5 → 3. S4 and S6 contribute none.

## Decision impact

- **D7 — "What is the credential primitive?"** Unchanged as a decision, better
  informed as a question: a terminating broker that establishes trust properly
  *and* enforces method policy is now demonstrated, so the approver is ruling on
  a working mechanism rather than a hoped-for one. It still reads every cookie
  and `Authorization` header in cleartext.
- **D13 — "What is the security claim?"** The rails hold with the renderer
  sandbox on, which removes the unstated condition correction 15 exposed. The
  opaque-origin realm is a WebRTC vector the init script covers. Nothing here
  converts a rail into a boundary.
- **D17 — "What blocks a vulnerable embedded runtime dependency?"** The platform
  code signature is definitively not an integrity anchor: ad-hoc, no identity,
  and extraction is exonerated. The clause naming it must not be read as
  offering a second anchor.
- **Adapter-host separation.** The macOS profile is narrower than the RFC
  described and narrower than round 6 believed possible, with the transport
  intact. The Linux boundary is establishable by an unprivileged user. Windows
  remains unmeasured.
- **Platform matrix.** Both supported platforms are now measured in the
  sandboxed configuration. Windows remains untested in every respect.

## Review results

Recorded in the RFC's amendment history.

## Supersession notes

None yet. Round 7 is the current round.
