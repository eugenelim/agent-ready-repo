# 2026-08-17 Experimental rounds 7, 8 and 9

This note records the seventh, eighth and ninth RFC-0088 Experimental runs. It is
authoritative over the rounds-5-and-6 headline verdicts where the two disagree.

**Round 9 measured a different subject from every round before it.** Rounds 3 to 8
measured the architecture, and each found that the previous round's *instruments*
had carried a defect. Six rounds of that is a pattern about the apparatus rather
than about the design, so round 9 turned the instruments on themselves and asked
one question: **can the controls fail?** It changes no S1-S6 verdict and adds no
blocker — its finding is a property of the evidence, and it belongs to Decision A,
which already asks the approver to weigh the subject and the apparatus separately.
Round 9 gives that decision a number for the first time.

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

**Figures round 9 brought under coverage.** Four figures quoted in this note
rested on artifact fields no control could fail on. They are checked now — but
not by a block listing them here. An earlier draft *did* add such a block, and it
was the wrong remedy twice over: one of its four lines asserted something false
(see **Provenance** below), and another existed only to give a regex a string to
match, so editing the real claim it was supposed to guard left the verifier
green. Each figure is now checked where a reader actually meets it — the uid
multiset under **Provenance**, the Chromium versions in the reproduction identity
above, the signature readings in S2's table — and the corresponding fact matches
that text rather than a restatement of it.

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

**Provenance.** All **11** Linux artifacts report `platform: linux` in their own
provenance blocks — the count grew when round 8 added the sandbox-off arm and the
no-capability probe, and an earlier draft still said three. The runner refuses to
copy back an artifact whose own provenance does not say `linux`.

Across the whole Linux corpus, **Linux artifacts report uid 0,1001** — not a
single value. Ten run as the unprivileged container account; one, round 5's
`s2/r5-linux-os-boundary-results.json`, genuinely runs as root. The
*this-round* claim in the reproduction identity above is the narrower one and it
holds: every round-7 Linux arm is uid 1001. The distinction is recorded because
a round-9 draft of this note flattened it into "every Linux artifact reports uid
1001" while an artifact reporting uid 0 sat in the same directory — and the fact
that was supposed to guard the claim read a hand-written list of three files that
happened to exclude it (R9-8).

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

**Round 9's own reproduction.** Round 9 measures the apparatus, so its identity is
the *corpus and the controls* rather than a browser and a platform: the 23-artifact
architectural corpus (`s1/`, `s2/`, `s3/`) as promoted in this archive, against
`build-archive.py` and `verify-note-figures-r7.py` as promoted in it. Both round-9
tools are manifested members and run from a reconstruction:

```bash
export RFC88_REPO=<repository root>
# 3959 single-field mutations over the 23-artifact corpus; ~35 min. Exact rather
# than "~4,000": the figure verifier checks every occurrence of this figure, and a
# rounded restatement in a procedure comment is still a second, unchecked copy of a
# number the round is about. Writes s9/r9-mutation-coverage-results.json
python3 r9-mutation-harness.py <note.md> <archive-note.md> <rfc.md>
# seconds. Writes s9/r9-claim-accounting-results.json
python3 r9-claim-accounting.py <note.md> <archive-note.md> <rfc.md>
./r9-promote.sh   # build -> regenerate the archive note -> sync the RFC digest -> verify
./r9-gates.sh     # every repo gate in one pass, reporting all results rather than the first failure
```

The harness exits 0 regardless: its finding is the report, not a pass. It refuses
to run if the controls already object to the unmutated tree, because a baseline
that is already failing cannot measure what the controls catch.

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

On S1's remaining row, one figure the RFC's item 1 leans on is worth stating
precisely rather than by reference: in the Linux remedy fixture the broker-owned
directory **supplies confinement at depth 1 on Linux**, immediately above the
socket. Round 3 recorded depth 3 for the same shape, which was the macOS platform
temp root, not this directory — the two are different levels of different chains
and only the Linux one is a control the design would own. Both the mode and the
depth are now derived from the fixture's recorded ancestor chain.

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
| `S3R8-REALMS-SANDBOX-OFF-LINUX` | Same driver, sandbox **off**, uid 1001 — the Linux baseline round 7 did not have | The five-realm matrix | Without it, "identical on Linux" has no named baseline on that platform | 14 of 14, `observedActive: false`; same per-realm counts as the macOS off arm | **Baseline established** — `s3/r7-linux-realms-sandboxoff-results.json` |
| `S3R7-REALMS-SANDBOX-ON-LINUX` | Same driver, sandbox on, uid 1001 | Same | Whether the platform changes the answer | **Identical** to the Linux off arm above, per realm and per arm | **No difference** — `s3/r7-linux-realms-sandboxed-results.json` |

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

The reading is not one arm's: **all three arms report `Signature=adhoc`**, and
**all three report flags `adhoc,linker-signed`**. That agreement is what makes
the conclusion a property of the bundle rather than of how it was unpacked —
`unzip` discarding metadata and `ditto` preserving it reach the same answer. Both
strings are derived from all three arms of the artifact, so an arm that disagreed
would change them.

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

**Every one of these fifteen is a defect in round 7's instruments or documents,
not in the architecture** — and that is a claim about *this table*, not about the
round. Round 7 did surface an architecture-relevant finding, from its own derived
minimum: `sysctl*` admits `kern.procargs2`, so a confined adapter host can read
the interception pin off the browser's argv. That is a property of the design's
confinement story, it is carried in blocker item 5, and it is not an instrument
defect. The honest form of the distinction is therefore: **the new measurements
found no defect in the architecture, they created one new exposure by narrowing
the profile, and every defect in the round's own machinery was in the machinery.**

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

## Round 9 — measuring whether the controls can fail

Every one of the six historical instrument defects was found the same way: a
reviewer changed an artifact by hand and noticed the control still reported clean.
That is a mechanical procedure, so round 9 automated it, and built a second
control from the opposite direction to cross-check the first.

### Instrument 1 — the mutation harness

`r9-mutation-harness.py` perturbs **every scalar leaf** of every promoted results
file, one at a time, and records whether either control objects: the archive
promotion gates in `build-archive.py`, or the figure check in
`verify-note-figures-r7.py`.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S9-HARNESS-SELF-TEST` | A field a control provably reads (`checks[0].ok`), and an invented key nothing reads | Mutate each; ask whether any control objects | The guarded one must be caught and the unguarded one must not, or the harness cannot discriminate | Guarded: caught by both. Unguarded: caught by neither — **after a fix; see R9-1** | **Control-valid** — `s9/r9-mutation-coverage-results.json` |
| `S9-MUTATION-COVERAGE` | The 23-artifact architectural corpus (s1/s2/s3; the round-9 meta-artifacts are excluded, see R9-5) | 3959 single-field mutations | What fraction of artifact fields any control can fail on | **357 caught, 3602 not — 9.0% guarded.** 38 by the gate alone, 130 by the verifier alone, 189 by both, and the three-way split accounts for every caught field: yes | **Measured** — same |
| `S9-CLAIMS-ON-UNGUARDED-FIELDS` | The unguarded set, cross-referenced against the promoted prose | Does a note quote the value of a field no control can fail on? | The actionable residual | **146 unguarded artifact fields back 52 distinct claim values** | **Measured, upper bound** — `s9/r9-unguarded-claims-results.json` |

**8.7% is not 8.7% of claims, and the note will not let that elide.** Most
promoted detail is context rather than claim — bounded diagnostic strings, per-arm
timing, nested `detail` objects a reader never cites. A field nothing reads is
only a defect when something *claims* it. The 147 figure is likewise an
**upper bound**: the test asks only whether a field's value appears somewhere in
the prose, and values like `linux` or `refused` appear for many reasons. **The triage from 147 to five was done by hand, by the author, and that
is worth naming.** This section argues two paragraphs earlier that claims must be
extracted mechanically "because a hand-written list of claims carries the same
author-blindness as a hand-written list of facts" — and then applies exactly that
method to decide which of the 147 matter. There is no mechanical test
for "load-bearing", the five below were chosen because a note quotes them in a
load-bearing sentence, and the 142 set aside are listed in full in
`s9/r9-unguarded-claims-results.json` so a reviewer can disagree with the triage
rather than take it on trust. The five:

- **`provenance.uid` on all but one Linux artifact.** The entire
  unprivileged-execution claim rested on a single artifact's uid; mutating any
  other went unnoticed.
- **Two of the three code-signature extraction arms.** The finding is that all
  three fail *identically*, and only the `playwright` arm was read by any fact.
- **The observed Chromium version**, quoted in the reproduction identity.
- **The deny-default refusal code** and **correction 13's `0700` mode**.

Facts were added for each of these, and a second pass added facts for round 9's
own figures — the corpus size, the mutation count, caught and uncaught, the
percentage, the three-way attribution split and both claim counts — which nothing
had checked, in the round whose subject is figures resting on unguarded fields.

**The percentage moved, and the movement is not a result.** It has read 8.2%, then
8.7%, now 9.0%. Those three numbers do not describe an evidence base getting
better: the denominator is the same corpus and the numerator is *whatever the
current control set happens to notice*, so adding a fact raises it by construction
and fixing a fact that could not fail (R9-9, R9-8) raises it again. Reading the
series as progress would be the same error as reading a test suite's pass rate as
code quality while adding tests. The figure is a snapshot of one control set
against one corpus, and only comparable across rounds if the controls are
unchanged — which is exactly what round 9 changed. What is comparable is the
direction of the residual: **the controls guard verdicts, not the evidence behind
them**, and that has not changed at all.

That also bounds what the added facts bought: they close the named claims, and the
rest of the unguarded surface stays unguarded and is now *recorded* rather than
unknown.

### Instrument 2 — claim accounting, from the other end

`verify-note-figures-r7.py` asks: for each fact I derive, is it claimed? That
direction **cannot see a claim it has no fact for**, which is where two round-7
defects lived — a promoted artifact cited in no scenario row, and the RFC's "16 of
18 checks" that no control has ever read.

`r9-claim-accounting.py` asks the inverse: **for each quantitative claim in the
prose, is there an artifact value accounting for it?** Claims are extracted
mechanically rather than from a hand-written list, because a hand-written list of
claims carries the same author-blindness as a hand-written list of facts.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S9-CLAIM-ACCOUNTING` | The round-7/8 note and archive note | Extract every `N of M`, counted quantity, backticked `key: value`, and identifier; match each against the flattened artifact corpus | Which prose claims cannot be traced to evidence | **Deterministic as of this round, and every remaining unaccounted claim is an extraction artifact rather than an unsupported measurement**: figures inside corrections rows describing the tool's own past defects, one literal example, one value the artifact stores in another representation, and the archive's own byte sizes — which cannot be in the corpus, because they describe the archive that contains it. The counts are deliberately not restated here; they are computed from this prose, so a count quoted in the text it measures changes by being quoted | **Traceable, by a method with a different blind spot** — `s9/r9-claim-accounting-results.json` |
| `S9-EXCLUSIONS-ARE-NAMED` | Every excluded claim | Is each exclusion reasoned, or is the list a loophole? | An exclusion class with no stated reason is how a control stops checking things quietly | **Six classes are defined, not the four an earlier draft of this row named — and most of them never fire.** The four it did name (dates, years, round numbers, and the literals `0` and `1`) account for almost nothing in the current run. Nearly every exclusion comes from a class the row named nowhere: scenario-row labels coined by the notes. A sixth covers described literals that are not check ids. The per-class shares are deliberately not restated here — they are computed from this prose and move when it changes | **Corrected.** Every class and its share are derived from the skip records themselves and printed rather than suppressed, so a class doing all the work cannot hide behind a summary listing four regexes — `s9/r9-claim-accounting-results.json` |
| `S9-IDENTIFIER-EXISTENCE` | The identifiers these documents name as checks | Does an artifact carry that id? | A note naming a check that does not exist is the round-7 defect-table bug | **Not clean — the earlier "none absent" was computed over five of forty identifiers.** The skip rule excluded thirty-five, and thirty-three of those have no artifact row at all: the check reported clean because it excluded everything capable of failing it. Those thirty-three are a prose convention — the evidence file each row cites is real — but the row-to-artifact-row mapping for them is editorial, checked by reading | **Bound now stated, not hidden.** The tool emits the excluded labels and its own coverage, so the residual of five is readable as a residual of five — `s9/r9-claim-accounting-results.json` |

**The residual, and why it is a residual rather than a defect list.** Every claim
the tool cannot account for is an extraction artifact, not an unsupported
measurement, and they fall into three kinds:

- **Figures inside corrections rows** — "16 of 18", "28 of 30" — where this note is
  *describing* an earlier defect's numbers rather than asserting a measurement. To a
  regular expression, prose that talks about a figure is indistinguishable from
  prose that asserts one.
- **A literal example**, the `` `key: value` `` shape quoted while explaining the
  extractor.
- **The archive's own byte sizes**, which cannot appear in the corpus because they
  describe the archive that contains the corpus. That one is a structural limit of
  measuring claims against artifacts, not a gap to close, and no amount of fixing
  will remove it.

One earlier residual entry *was* a real disagreement and is now closed: the note
quoted codesign's raw `flags=0x20002(adhoc,linker-signed)` token, the artifact
stored exactly that string, and the extractor stripped the `flags=` prefix before
comparing — so prose and artifact agreed while the tool reported a gap between them.
The extractor now offers both renderings of a keyed claim and accounts for it if
either matches. Fixing that surfaced a second defect immediately: offering two
renderings tripled the residual, because the tool counted the alternatives as
separate claims. An instrument that reports more findings for learning a new way to
state the same one is measuring itself.

The counts are deliberately not quoted in this section. They are computed from this
prose, so a count stated here changes by being stated — the reason an earlier draft
of this paragraph contradicted the split stated above it, saying "all six" were
meta-commentary and then listing four. They live in
`s9/r9-claim-accounting-results.json`.

The meta-commentary could be silenced with an exclusion for "figures quoted while
describing an instrument". It is not, deliberately: an exclusion class broad enough
to cover meta-commentary is broad enough for a future round to hide a real claim
behind, and this evidence base has now been corrected 21 times in one round
for controls that stopped checking things quietly. The residual stays visible and is
classified here in prose instead.

**What the second instrument does and does not establish.** It is *not*
corroboration of the first, and an earlier draft of this section said it was. The
two tools measure different quantities: instrument 1 measures what fraction of
artifact fields a control reads; instrument 2 measures what fraction of prose
claims trace to an artifact value. Neither is a check on the other's answer, so
neither can confirm it. What instrument 2 establishes is narrower and still
useful: **the prose claims in these documents are traceable to evidence**, checked
by a method with a different blind spot from the forward verifier's — which is how
it found three gaps the forward verifier structurally cannot see.

Two limitations round 9 cannot remove from inside: both tools share an author, and
the second was designed *after* the first's failure modes were known. Genuine
independence would need a second author.

## Round-9 corrections

| # | Round-9 claim or control | What was established | Status |
| --- | --- | --- | --- |
| R9-1 | The mutation harness measures whether the controls guard a field | **It measured the archive digest instead.** Any artifact change alters the digest, which the note claims, so an invented key that nothing reads was reported as *caught*. The harness would have reported near-total coverage for a reason unrelated to guarding | **Withdrawn and fixed** before any result was trusted. Archive-identity facts are excluded from the caught/uncaught decision, and the self-test that found it now ships with the harness |
| R9-2 | The claim extractor finds claims | Its first version compared the **key name** of `` `key: value` `` against artifact *values*, and a field name is never a value: 28 of 30 "unaccounted" results were that flaw | **Fixed.** Value side only |
| R9-3 | Counted quantities are extracted correctly | A comma-formatted byte figure such as the archive's own size yielded a claim of its last three digits, because the number pattern could start mid-number. (An earlier version of this row quoted `122,390`, an archive size from a superseded rebuild that matches no current figure — an unaccountable number in the corrections table of the tool whose job is accounting for numbers) | **Fixed** with a digit boundary, and comma-formatted values are normalised before comparison |
| R9-4 | Quoted source is a claim | `` `decision === 'allowed'` `` and `` `runs == 1` `` are explanations of how a control works, not claims about measured values. Matching them produced a residual made of JavaScript operators | **Fixed.** Code spans are excluded |
| R9-5 | The coverage figure describes the evidence corpus | It counted the harness's **own output** in `s9/` — fields no control reads and none should — inflating the denominator and reporting 6.8% where the architectural corpus is 8.7%. This is the citation the corpus precondition points at | **Fixed.** `s9/` is excluded from the corpus, and exempted from the fixture gates because tool output has no browser, uid or per-run nonce to carry |
| R9-6 | Round 9's evidence was promoted | **It was not.** The first archive built for this round contained no `s9/` artifact and neither round-9 tool, so the 8.7% figure rested on evidence no reconstruction could produce — the same evidence-nobody-can-see class as R8-15. Found by the round-9 review, not by round 9 | **Fixed.** Both tools and all three artifacts are manifested members; the archive carries all three |
| R9-7 | The helper scripts were promotable | `r9-gates.sh` hardcoded the repository root under a home directory, and the privacy gate **refused the build** — correctly. The one gate nobody had questioned was the one that worked | **Fixed.** Both helpers take `RFC88_REPO` from the environment |
| R9-8 | "All **11** Linux artifacts report `platform: linux`" was checked | **It was checked against a hand-written list of three of them** — a claim measured on a stand-in, which is round 3's named failure mode surviving into the round built to find it. The eight it omitted included `s2/r5-linux-os-boundary-results.json`, the one Linux artifact that genuinely runs as root, which is how this note came to state "every Linux artifact reports uid 1001" with a uid-0 artifact in the same directory | **Fixed.** The set is derived from the filename convention and the count with it. It is deliberately *not* derived from the `platform` field, which would make "they all say linux" unfailable; the uid claim is split into a this-round scope (1001) and a full-corpus multiset (0,1001), and both are stated in the text |
| R9-9 | The bundled-Chromium version is under coverage | The fact's pattern required the version to be followed by markdown bold — `([\d.]+)\*\*` — which nothing in the reproduction identity is. **The only text it could match was a line added to this note for the regex**, so editing the real version claim left the verifier green. Proven by mutation, not by inspection | **Fixed.** The pattern matches the real claim in the reproduction identity, the line written for the regex is deleted, and mutating the version now fails the run |
| R9-10 | Round 9's own remedy block brought four figures under coverage | **The block was the defect it was written to fix.** Four lines were placed in this note to give four regexes something to match; one of them asserted something false (R9-8), and a figure restated for a checker is not a figure a reader relies on. This is the eighth consecutive round in which a remedy carried the shape it was built to catch | **Withdrawn.** The block is deleted and each figure is checked where a reader actually meets it — the uid multiset under **Provenance**, the versions in the reproduction identity, the signature readings in S2's table |
| R9-11 | The claim-accounting residual is a measurement | Its corpus glob `s?/*results.json` matched `s9/`, **its own output**, so the tool's report of a claim counted as an artifact accounting for that claim. The residual therefore shrank on every rerun: 53, then 48, then 53 unaccounted on byte-identical inputs | **Fixed.** `s9/` is excluded from both the value corpus and the identifier corpus. A control that reads its own verdict is the tautological fixture this round is forbidden to score as a pass |
| R9-12 | Correction 13's `0700` mode is now checked | The first version of that fact pointed at `s2/r7-relay-directory-mode-results.json`, **which does not exist**, behind an `if is_file()` guard — so it silently checked nothing and the suite stayed green. Caught in the same pass that wrote it, before promotion | **Fixed.** The guard is gone and the mode and depth are derived from the Linux remedy fixture's recorded ancestor chain. That also corrects a figure inherited from round 3: on Linux the confining level is **depth 1**, not the depth 3 round 3 recorded for the macOS platform temp root — different levels of different chains, and only the Linux one is a control the design would own |
| R9-13 | The privacy sweep guards the promoted documents | Two holes. Its placeholder exemption tested the **first occurrence anywhere in the file** of an eight-character hit (`/Users/` plus one letter), so a single `/Users/someuser` exempted every `/Users/s…` in that file and a real name sharing a first letter with a placeholder went unreported. And **every sweep stripped the base64 payload before scanning**, which is the route by which an organisation identifier reached a manifested archive member unseen | **Fixed and negative-tested in four directions.** Exemptions are anchored to the match position, the sweep decodes the payload and scans each member, it fails rather than passes when it matches zero files, and the organisation terms come from the environment so the detector does not carry the string it detects |
| R9-14 | Each promoted artifact can be traced to the driver that produced it | **No artifact records its own producer** — all 26 declare a `provenance` block without a driver or script field, so the artifact-to-driver mapping exists only in the runner scripts and cannot be checked automatically | **Recorded as a bounded limit, not fixed.** Adding the field means re-running every arm, and hand-writing it into finished artifacts would be fabrication. The gap is narrower than it reads: every non-library driver member is invoked by a runner script that is itself a member, so the reconstruction path is complete in the direction that matters — a reconstruction reproduces the corpus, it just cannot attribute one file to one driver without reading the runners |
| R9-15 | The identifier-existence check found no absent check id | **It excluded everything that could have failed it.** Its skip rule covered thirty-five of the forty identifiers these documents name, and thirty-three of the thirty-five have no artifact row — so "none absent" described a five-identifier sample, reported as though it described all forty. Nothing was fabricated; the bound was simply invisible | **Fixed.** The tool now emits the excluded labels and states its own coverage in the artifact, and the note row reports the residual as the five-identifier residual it is. This is the strongest can-not-fail predicate the nine rounds have produced, and it was in round 9's own control set |
| R9-16 | The exclusion list was four reasoned classes | **Six, and the shares were the opposite of what the row implied.** Three of the four named classes — dates, years, round numbers — fire zero times. The unnamed fifth class, scenario-row labels coined by the notes, does roughly four fifths of the excluding, and a sixth covers described literals. `exclusionsApplied` listed the four regexes and was suppressed from stdout, so the summary a reader checks omitted the class that mattered | **Fixed.** Every class and its share are derived from the skip records and printed. The accounting totals are deliberately *not* quoted in this note: they are computed from the prose, so a figure quoted here changes by being quoted |
| R9-17 | The accounting residual was a stable measurement | It was not reproducible: 53, 48, then 53 unaccounted claims on byte-identical inputs, because the tool read its own previous output (R9-11) | **Fixed and demonstrated.** Three consecutive runs on identical inputs now return identical figures across all five reported counts. A control whose output moves without its input moving cannot support a claim either way |
| R9-18 | The archive's privacy gate and the privacy sweep can coexist | **The gate refused the build, correctly, because the sweep carries the placeholder names it exempts** — `/Users/someuser`, `/Users/realperson` — and a synthetic address. Adding an exemption then made the *exemption table* a member carrying those literals, so `build-archive.py` failed on its own table: the same recursion that let an organisation identifier reach a manifested member (R9-13), running the other way | **Fixed without widening the gate.** The literals are defined once and referenced by all three detector files, still literal by literal rather than a whole-file pass. Negative-tested: a realistic name or address added to any of the three exempted files — including the file holding the exemption table — still fails the build, nine probes of nine caught |
| R9-19 | The accounting residual named two real traceability gaps | One of them was **the tool disagreeing with itself**, not the evidence disagreeing with the prose. The note quoted codesign's raw `flags=0x20002(adhoc,linker-signed)` token and the artifact stored exactly that string — but the extractor stripped the `key=` prefix before comparing, so it compared `0x20002(...)` against a corpus holding `flags=0x20002(...)`. Prose and artifact agreed; the tool reported a gap. A round-9 draft had recorded this as *fixed by storing the raw token*, which was already true and was not the problem | **Fixed in the extractor**, which now offers both renderings of a keyed claim and accounts for it if either matches |
| R9-20 | Offering both renderings fixed R9-19 | **It tripled the residual instead** — from 6 to 27 — because the tool counted the two renderings of one claim as two claims, so every keyed claim that failed to match failed twice. An instrument that reports more findings because it learned a second way to state the same one is measuring itself. Found immediately, by rerunning rather than by reasoning about the change | **Fixed.** Renderings are alternatives: accounted if any matches, unaccounted once if none does. The residual returned to 6, and every entry in it is an extraction artifact rather than an unsupported measurement |
| R9-21 | Each round-9 helper had one authoritative copy | Two of them did not. `r9-defect-count.py` existed both in the evidence root and in a scratch directory, and a `cp` from scratch **silently overwrote a just-applied fix with the older copy** — the control then ran, printed two passes, and omitted the third check entirely without saying so. Caught only because the expected output line was missing | **Fixed.** The scratch copies are deleted; the evidence root is the single authority for every manifested helper. A control with two copies is a control where the untested one can win, which is the same failure as the privacy sweep's inline duplicate (R9-13) |

**R9-1 is the seventh consecutive round in which an instrument carried the defect
it was built to detect — and the first in which the instrument's own self-test
caught it rather than a reviewer.** The self-test took thirty seconds; the broken
run had already spent forty-four minutes producing numbers that meant nothing.
That is the cheapest lesson in this evidence base: **apply the discipline to the
measuring instrument, not only to the measured subject.**

**R9-8 to R9-18 came from a second pass that took the controls themselves as the
subject, and it is the more uncomfortable half of this round.** The first pass
found instruments that measured the wrong thing. The second found instruments
that measured *nothing* and reported clean: an identifier check whose skip rule
excluded every identifier capable of failing it, a fact matching only a line
written to satisfy its own regex, a fact pointing at an artifact that does not
exist behind a file-exists guard, and a privacy exemption that generalised from
one placeholder to every account name sharing its first letter. None of these
would appear in a coverage percentage, because each one *is* a control — they
raise the measured coverage while guarding nothing. **A coverage figure counts
controls; it cannot tell you whether they can fail.** That is why every control
added or changed in this round was mutation-tested individually, and why the
one-line result of each of those tests is recorded above rather than summarised
as a pass.

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

| # | Item | Disposition after rounds 7-9 |
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
- **Platform matrix.** The S3 egress rails are measured sandboxed on both
  platforms. The S1 corpus, S4, S5 and five other S3 rail drivers are not, and that
  is a residual of item 1. Windows remains untested in every respect.
- **Round 9 — how much of this evidence a machine can defend.** No D-decision
  changes, because round 9 measured the apparatus rather than the architecture.
  What changes is the confidence attached to every other row above: the controls
  can fail on 8.7% of artifact fields, and 147
  distinct published claims rest on fields no control can fail on. Owner: the RFC
  owner, re-measured every subsequent round. This is the input to Decision A and
  it applies as a discount across all six spikes rather than to any one of them.

## Review results

Recorded in the RFC's amendment history, and summarised here because rounds 3 to 6
each published a finding count and rounds 7 to 9 had not.

| Round | Lenses run | Outcome |
| --- | --- | --- |
| 7 | adversarial, security-design, quality, cold reader | All four returned blockers. The quality pass established its findings by **mutation testing** and proved four controls unable to fail |
| 8 | — (round 8 *is* the response to round 7's review) | Fixed 15 defects, of which six changed a conclusion |
| 9 | adversarial, quality, cold reader | All three returned blockers. The cold reader found that **round 9's own evidence was unpromoted** and that three round-8 withdrawals were still live text in the authoritative section. The security lens was not run: round 9 measures the apparatus and makes no new claim about a security boundary |

**The loop has not converged, across rounds 3 to 9.** Round 9 changes the character
of the finding rather than the finding itself: for the first time the defects were
in the *measuring* apparatus rather than the architecture, four of seven were caught
by the instrument's own self-test before its output was trusted, and the coverage
figure now explains why the previous six rounds went the way they did.

These reviews validate the record, not the architecture. They do not change any
Experimental exit decision, authorize acceptance, or authorize implementation.

## Supersession notes

Round 9 is the current round; nothing supersedes it yet. Within this note, **round
8 supersedes round 7 and round 9 supersedes both** where they disagree, and every
such disagreement is enumerated in *Round-8 corrections* and *Round-9
corrections* rather than applied silently.

Appended to earlier notes by this promotion: the rounds-5-and-6 note carries a
2026-08-17 entry recording the six-item list, the profile-minimum reversal, the
unprivileged-but-capability-dependent netns row, and the `data:` realm result.
