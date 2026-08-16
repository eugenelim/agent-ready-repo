# 2026-08-16 Experimental rerun

This note reconciles the second RFC-0088 Experimental run against the RFC's
evidence contract. It is authoritative over the handoff's headline verdicts:
the 65-file received package is preserved unchanged for audit, including its
internal inconsistencies, while the classifications below reflect destination
review.

## Reproduction identity and integrity

- Repository ref: `553aa6b3c2629398dadc843eddb2c8961dd57606`
- Host: macOS 26.5.2 build 25F84, arm64
- Node: 26.4.0; npm: 11.17.0; Python: 3.13.13
- Playwright: 1.62.0; runtime-lock SHA-256:
  `f6934c2a7671a35dd2662736d21447ff3f2cb40e07934572e3866de7517bebe7`
- Browser channels: bundled Chromium 151.0.7922.34 and system Chrome
  151.0.7922.138
- Scanner: Trivy 0.72.0; vulnerability database updated
  2026-08-16T00:59:19Z; database-file SHA-256:
  `d3165081410e0c6c5771d371b3068f6fa8748f4086c7f9545c50685c87b91335`
- Received manifest: 65 regular files; every path was confined and every
  digest verified; the unmanifested `work/` tree was neither read nor executed
  during destination review
- Promoted package:
  [`experimental-rerun-evidence-archive.md`](experimental-rerun-evidence-archive.md)

All browser profiles, accounts, documents, authentication values, routes, and
downloads used by the fixtures were synthetic. The promoted package contains no
browser profile, cookie database, trace, HAR, screenshot, credential value, or
third-party installation tree.

## Current spike state

| Spike | Destination verdict | What advanced | What remains open |
| --- | --- | --- | --- |
| S1 | **Partial** | Real launch, bind, CLI attach, same-context handoff, reconnect, close, crash relaunch, and clean profile reuse passed twice on both macOS arm64 channels | Lifetime-based attachment expiry, a seeded stale-lock decision, and typed ambiguous-lock/crash refusals |
| S2 | **Partial** | The clean lock passed, the controlled vulnerable lock blocked with two High findings, and a real native Page/Context reached the adapter | Compose native Playwright with the separate sanitized child host and parent-owned release validation; finish scanner/database/browser-payload policy |
| S3 | **Partial** | Browser/network channels are now classified; redirect, WebSocket, request-client, download, deadline, proxy, worker, and Service Worker behavior has real evidence | DNS rebinding, WebRTC, WebTransport, allowed redirects/hop bounds, Linux proxy behavior, and trusted-adapter bypasses remain unproved or intentionally unprevented |
| S4 | **Partial under amended D2** | One candidate proved a native Playwright bridge and an authority-widening credential-export surface; the other two have falsifiable inspection exclusions; the approver subsequently adopted the two-stage gate | Re-disposition every exact candidate against the amended inspection bar and execute the common S1/S3 corpus only for candidates that clear it, with a sanitized environment |
| S5 | **Partial** | The prior 21-row pack harness reproduced exactly and the same live session served both consumers | Host-owned candidate display/discard and cross-consumer browser residue/trust require an explicit decision and fixture |
| S6 | **Pass, unchanged** | The opaque browser-session taxonomy remains feasible | Convention work still waits for RFC acceptance |

No result authorizes acceptance or implementation. S1 through S5 remain open
Experimental gates.

## S1 — persistent bind lifecycle

Common precondition: exact Playwright 1.62.0, a fresh generated profile, a
synthetic page, and one of the two recorded browser channels. Every row ran
twice on each channel unless its result says otherwise.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S1-PERSISTENT-LAUNCH` | Fresh profile | Launch headed persistent context | One context and default page | One page on each channel | Pass — `s1/s1-*-results.json` |
| `S1-OWNING-BROWSER` | Live context | Call `context.browser()` | Connected owner | Connected owner and exact browser version | Pass — same |
| `S1-BIND` | Connected owner | Bind browser | Nonempty local endpoint | User-temporary Unix socket | Pass — same |
| `S1-CLI-DASHBOARD-ATTACH` | Bound browser | Attach named CLI session and evaluate | Same page is visible | Synthetic title returned; attached CLI could enumerate the synthetic cookie | Pass with credential-equivalence finding — same |
| `S1-ATTACH-OWNER-RESPONSIVENESS` | Bound owner | Block owner event loop and attach | Timeout rather than false liveness | Operating-system timeout | Pass; broker responsiveness becomes a requirement — same |
| `S1-DEFAULT-CONTEXT` | Attached client | Read page state and cookie jar | Same live context | Same title, ephemeral state, cookie, and one context | Pass — same |
| `S1-USER-TAKEOVER-RETURN` | Attached page | Mutate page interactively, then resume owner work | Both sides observe changes | Human edit and deterministic resume observed | Pass — same |
| `S1-DISCONNECT-RECONNECT` | Live owner | Disconnect then attach a second client | Owner/context survive | Page state survived reconnection | Pass — same |
| `S1-ATTACHMENT-EXPIRY` | Bound browser | Call `unbind()`, then reconnect | Lifetime expiry with typed refusal | Any reconnect error satisfied the fixture; no timer expired | **Weak, not the required scenario** — same |
| `S1-AMBIGUOUS-LOCK` | Live profile owner | Start a second owner | Recognized typed refusal | Informative browser error, but fixture accepted any thrown message | Partial — same |
| `S1-BROWSER-CLOSE` | Connected browser | Close browser | Deterministic disconnect | Disconnect event and false connection state | Pass — same |
| `S1-CLEAN-SHUTDOWN` | Durable synthetic cookie | Close and reopen | Profile reusable; durable state survives | Reopen succeeded and durable cookie remained | Pass — same |
| `S1-OWNER-CRASH` | Live owner and durable state | Kill owner, relaunch | Recovery or recognized typed refusal | Relaunch and durable state succeeded; predicate also accepted generic crash text | Pass for relaunch, weak for typed refusal — same |
| `S1-STALE-LOCK` | Owner was killed | Check/recover stale ownership | Seeded dead-owner lock is recovered; ambiguous state refused | No lock was created or observed; row duplicated crash relaunch | **Not exercised** — same |

S1 cannot select a support matrix yet. A rerun must seed both stale and
ambiguous/live ownership artifacts, inspect links without following them,
assert typed recover/refuse outcomes, and exercise actual attachment lifetime
expiry and forced detachment.

## S2 — artifact host and dependency gate

The 2026-08-15 artifact-layout, non-executing inspection, install-script,
native-addon, symlink, permission-seatbelt, and provenance rows remain valid.
This table covers the new evidence.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S2-SCANNER-CLEAN` | Frozen two-package runtime lock and current DB | Run High/Critical blocking scan | Exit 0 after parsing packages | Exit 0; exactly Playwright and Playwright Core parsed; no finding | Pass — `s2/scanner-runs.txt`, `scanner-findings-summary.txt` |
| `S2-SCANNER-CONTROLLED-VULNERABLE` | Lock pins a controlled vulnerable package | Run same blocking scan | Exit 1 with a finding | Exit 1; two High findings | Pass — same plus `trivy-vulnerable.json` |
| `S2-SCANNER-FAIL-CLOSED` | Empty cache and updates disabled | Run scan | Infrastructure failure cannot appear clean | Exit 1 and no result file | Pass — `scanner-failclosed-check.txt` |
| `S2-ADAPTER-NO-BUNDLED-PLAYWRIGHT-STATIC` | Self-contained candidate | Inspect imports and artifact tree | No Playwright copy | No import/reference or nested dependency tree | Pass — `s2/s2-native-results.json` |
| `S2-HOST-SUPPLIED-PLAYWRIGHT` | Real browser in the host process | Import adapter and supply Page/Context | Adapter uses host-native objects | Native Page/Context returned real title and two DOM rows | Pass for native-object feasibility — same |
| `S2-SINGLE-PLAYWRIGHT-COPY` | In-process adapter with no imports | Inspect CommonJS cache | Detect a second copy | One host root observed, but an ESM-bundled copy is invisible to this check | Weak; static artifact inspection carries the rule — same |
| `S2-SANITIZED-ENVIRONMENT` | Adapter imported into host process | Ask for an unexported value | Adapter cannot reach parent environment | Value was never placed in the environment; adapter shared `process.env` | **Vacuous** — same and `s2/native-host.mjs` |
| `S2-OUTPUT-VALIDATION` | Strict closed Draft 2020-12 schema | Validate valid, malformed, extra-field, and secret-shaped payloads | Only closed valid outputs release | Eight unit cases behaved correctly, including two exfiltration-shaped extras | Pass as schema unit evidence; not integrated release evidence — `schema-validation-*` |

D17 now has a viable scanner and threshold, but the acceptance policy must also
set database freshness, verify or pin the database source, disable silent
ignore files, emit a nonblocking full-severity inventory, distinguish findings
from scanner failure, and verify the separately downloaded browser revision.
S2 remains open until one separate child receives native Playwright, runs under
an explicit environment allowlist and intended Node restrictions, and returns
valid/invalid outputs to parent-owned validation and finalization.

## S3 — safety-rail limits

Common precondition: fresh generated browser profiles and a purpose-built
loopback service. The service receive log is independent ground truth for
whether traffic left the browser.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S3-CONTEXT-VS-PAGE-ROUTE-PRECEDENCE` | Broker context route installed | Adapter adds a page route | Broker rail remains authoritative | Page route won; undeclared server received one request | Not prevented — `s3-browser-network-results.json` |
| `S3-ROUTE-REMOVAL` | Broker route installed | Adapter calls `context.unroute` | Rail cannot be removed | Undeclared server received one request | Not prevented — same |
| `S3-PAGE-FETCH` | Undeclared origin | Page fetches | Abort before egress | Fetch failed; server received zero | Prevented — same |
| `S3-WORKER-FETCH` | Undeclared origin | Dedicated worker fetches | Abort before egress | Fetch failed; server received zero | Prevented — same |
| `S3-WEBSOCKET` | HTTP route only | Page opens undeclared WebSocket | Handshake blocked | Connection opened; server received upgrade | Not prevented by HTTP route — same |
| `S3-REDIRECT` | First hop allowed; target undeclared | Fetch/navigation receives 302 | Revalidate target before egress | Target fetched; events observed it afterward | Detected after the fact — same and `redirect-probe.txt` |
| `S3-REQUEST-CLIENT-METHODS` | Context-associated request client | Issue GET, HEAD, POST, PUT, PATCH, DELETE | Same origin/method rail applies | All methods reached server without route interception | Not prevented — same |
| `S3-RAW-NODE-EGRESS` | Adapter has raw Node network access | Call `node:http` | Browser rail observes/refuses | Server reached with no browser observation | Unobservable to browser policy — same |
| `S3-DOWNLOAD-CONFINEMENT` | Host-generated job root | Download, then try traversal and symlink-root cases | Commit only beneath real confined root | Real download committed; strengthened probe refused both escape cases and created no escape file | Prevented in strengthened probe — `download-confinement-*` |
| `S3-CANCELLATION-DEADLINE` | Server delays 30 seconds | Host cancels at 3 seconds | Typed failure and no release | Deadline fired near 3 seconds; no result released | Prevented in construction fixture — `s3-browser-network-results.json` |
| `S3-SERVICE-WORKER-BLOCKED` | `serviceWorkers: block` | Register worker | Host surfaces blocked posture | No registration or script request; API silently returned undefined | Prevented, but host signal still required — `sw-block-*` |
| `S3-SERVICE-WORKER-ALLOWED` | Service workers allowed | Worker initiates undeclared fetch | Route sees worker egress | Route aborted; server received zero | Prevented for worker-initiated egress — same |
| `S3-DNS-REBINDING` | Synthetic hostname maps to loopback | Navigate through hostname | Policy observes resolved address | Policy saw hostname only; request reached loopback | Unobservable at route layer — `s3-browser-network-results.json` |
| `S3-BROWSER-PROXY` | Explicit broker proxy | Browser requests origin | All egress crosses proxy | Proxy received one; origin received no direct request | Prevented/observed — same |
| `S3-INHERITED-PROXY` | Proxy variables in macOS launch environment | Browser requests origin | No silent inherited proxy | Environment proxy received zero | Prevented on this macOS host only — same |
| `S3-MITIGATE-REDIRECT` | Route owns fetch | Fetch with `maxRedirects: 0`, inspect `Location` | Undeclared target stays untouched | Target received zero | Mitigation feasibility pass — `mitigation-probe.txt` |
| `S3-MITIGATE-REQUEST-CLIENT` | Host wrapper | Request undeclared origin or mutation method | Wrapper refuses before request | Typed refusals; servers received zero | Mitigation feasibility pass, rail only — same |
| `S3-MITIGATE-WEBSOCKET` | WebSocket route installed before pages | Open declared and undeclared sockets | Apply destination policy to handshake | Undeclared socket closed and zero upgrades; declared connected | Mitigation feasibility pass — `ws-mitigation-probe.txt` |

The redirect mitigation is proven only for a denied first redirect. Allowed
redirect chains, hop bounds, per-hop method/destination checks, WebRTC,
WebTransport, page requests served by a Service Worker, Linux proxy behavior,
and a DNS-pinning or equivalent egress control remain open. A wrapped request
client prevents mistakes but cannot be a boundary because native Page/Context
objects expose the raw request client. Page-route precedence, route removal,
and raw Node egress confirm the trusted-code claim.

## S4 — substitution candidates

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S4-PLAYWRIGHT` | Exact 1.62.0 runtime | Run S1/S3 directly | Native ABI with bounded owner | Native fixture and lifecycle evidence available | Retained provisional substrate — S1/S3 evidence |
| `S4-AGENT-BROWSER-NATIVE` | Exact candidate 0.34.0, synthetic profile | Connect through reported CDP endpoint | Determine native-object compatibility | `connectOverCDP` returned native Page/Context for driven page | Prior ABI rejection falsified — `s4/s4-agent-browser-results.json` |
| `S4-AGENT-BROWSER-AUTHORITY` | Synthetic cookie | Invoke candidate cookie-read surface | No credential-export surface | Cookie name and value were printed | Reject on authority — `authority-export-probe-output.txt` |
| `S4-OPENCHROME` | Exact candidate 1.12.9 installed without scripts | Inspect and invoke bounded help surfaces | Candidate fits endpoint/dependency/authority boundary | Fixed unauthenticated debugging port, credential vault, native addon, self-update, non-Playwright substrate | Inspection exclusion only; D2 execution unmet — `s4-candidate-matrix.md` |
| `S4-OPENDEVBROWSER` | Exact candidate 0.0.40 installed without scripts | Inspect and invoke bounded help surfaces | Candidate fits single-runtime/authority boundary | Second Playwright Core version plus desktop, daemon, extension, and plugin authority | Inspection exclusion only; D2 execution unmet — same |
| `S4-SANITIZED-CANDIDATE-EXECUTION` | Third-party candidate commands | Spawn with explicit environment allowlist | No inherited credential-class environment | The recorded run inherited the originating environment | **Fail; security incident and mandatory rerun** — `environment-exposure-disclosure.md` |

At the time of this run, D2 remained a hard execute-all gate. The approver later
adopted the RFC amendment's two-stage inspection-then-execution rule. Candidate
bridging is not endorsement: the observed loopback CDP endpoint is an
unauthenticated credential-equivalent control channel. Every future candidate
execution must first pass dependency scanning and use an explicit environment
allowlist. Existing candidate evidence must be re-dispositioned against the
amended inspection bar rather than being silently converted to a pass.

## S5 — cross-pack vertical

Common precondition: the previously promoted three-pack fixture and exact grant
tuples, plus a real browser against a synthetic service whose protected paths
return 401 without the validation-created session cookie.

| Scenario | Precondition | Stimulus | Expected observable | Actual bounded observable | Result and evidence |
| --- | --- | --- | --- | --- | --- |
| `S5-PACK-HARNESS` | Three synthetic packs | Rerun 21 projection/dependency/grant rows | Exact prior result | All 21 passed; SHA-256 `5f8d1a93fd083a37f4638665ebd3f6342513b01f14d34ba322361a81158cbdfc` | Pass — `s5/s5-pack-harness-*` |
| `S5-VALIDATION-ONLY-OPERATIONS` | Validation authorization | Authenticate, resolve identity, health | Only fixed validation operations | Only those three operations ran | Pass — `s5/s5-same-browser-results.json` |
| `S5-VALIDATION-SURFACE-ABSENCE` | Validation fixture | Inspect own properties | No behavior/artifact/log/checkpoint/resource/release surface | Only page, context, signal, job, connection present | Pass — same |
| `S5-MIXED-VALIDATION` | Mixed job fields | Submit job | Refuse before launch/traffic | Typed refusal, zero launch and traffic | Pass — same |
| `S5-SAME-BROWSER-HANDOFF` | Validation created a session-only cookie | Both consumers read protected paths | Same live session reaches both | Both succeeded; a relaunch would have lost the cookie | Pass for same-session handoff — same |
| `S5-AUTHENTICATED-STATE-REUSED` | Existing live session | Invoke both consumers | No reauthentication | Both protected operations succeeded | Pass — same |
| `S5-RESULT-POLICY-ISOLATION` | Two exact result policies | Execute summary and artifact-only grants | Only allowed delivery shape releases | Summary versus opaque handle observed | Pass as construction evidence — same |
| `S5-IDENTITY-MISMATCH` | Wrong consumer identity | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-GRANT-PAIR-MISMATCH` | Consumer/grant pair differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-UNGRANTED-RESOURCE` | Resource absent from scope | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-SENSITIVITY-MISMATCH` | Sensitivity differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-RESULT-POLICY-MISMATCH` | Result policy differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-NARROWER-POLICY-NO-AMENDMENT` | Job narrows policy without amended grant | Invoke grant | Exact match required | Typed refusal; zero traffic/launch | Pass — same |
| `S5-SCHEMA-MISMATCH` | Schema digest differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-DIGEST-MISMATCH` | Adapter digest differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-BEHAVIOR-MISMATCH` | Behavior differs | Invoke grant | Refuse before browser | Typed refusal; zero traffic/launch | Pass — same |
| `S5-INDEPENDENT-UPGRADE` | A activates v2; B retains v1 | Execute both | Independent grant selection | Both versions executed in one live context | Pass for selection; exposes residue risk — same |
| `S5-FOUNDATION-DISABLED` | Foundation disabled | Invoke consumer | Typed failure; no fallback | Typed failure, zero launch and traffic | Pass — same |
| `S5-CANDIDATE-DISPLAY-DISCARD` | Identity candidates exist | Render host-owned confirmation and reject one | Only confirmed bindings persist; rejected evidence discarded | Harness checked absence only; no render/reject transition occurred | **Not exercised** — `s5/harness.py` |
| `S5-CROSS-CONSUMER-RESIDUE` | Two admitted digests share connection context | A leaves a route/init/global/socket; B executes | Defined teardown/isolation or explicit connection-wide trust | Both consumers received the same Page; no residue probe ran | **Not exercised; architecture decision required** — `s5/s5-same-browser.mjs` |

S5 proves exact-grant constructibility and the same-live-session subrow, but not
in-browser isolation. Until a residue contract is chosen and tested, admitting
one native adapter extends trust to every consumer sharing that connection's
browser. Fresh pages and best-effort teardown may reduce accidental residue but
cannot isolate context-level state from trusted native code.

## Test-conduct incident

The S4 candidate commands inherited a live SSH-agent socket and three live
session-token variables. There is no evidence of misuse and no credential value
is preserved, but exposure is exposure. The operator must rotate the affected
session tokens and review the SSH-agent identities externally. The corrected
fixture uses an explicit environment allowlist; it was not rerun, so the S4
sanitized-execution row remains failed.

## Decision impact

- **D2:** retain Playwright provisionally, correct the native-ABI rationale,
  and apply the approver-adopted two-stage inspection-then-execution gate. S1
  and S4 remain open.
- **D5/D13:** exact grants isolate invocation and release, not shared-browser
  residue. Record connection-wide native-adapter trust until a stronger
  isolation design is proven.
- **D7:** an attached dashboard/repair session is credential-equivalent. Its
  lifetime and stdio require controls beyond establishment authorization.
- **D13:** redirect, WebSocket, request-client, DNS, and raw Node evidence
  narrows the safety-rail claim without changing the trusted-code verdict.
- **D17:** a blocking scanner is feasible, but the scanner database, waiver,
  full-severity inventory, browser-payload, and infrastructure-failure rules
  remain acceptance criteria.

## Destination review results

- **Adversarial architecture review:** one broken S4 supersession anchor was
  found and fixed; at that review point the verdicts accurately kept S1, S2,
  S3, and S5 partial and S4 blocked pending the approver disposition recorded
  below.
- **Security-design review:** clean after carrying the inherited-environment
  incident, attachment credential equivalence, site-controlled egress gaps,
  request-client limits, and cross-consumer residue risk as open gates instead
  of pass claims.
- **Quality/testability review:** clean for evidence promotion; the weak,
  vacuous, unit-only, and not-exercised rows are explicitly classified and do
  not close their parent spikes.
- **Cold-reader review:** clean after the S4 anchor fix; the note now states
  the current spike state, decision impact, incident, and then-open approver
  decision without relying on the handoff prose.

These reviews validate the record, not the architecture. They do not change any
Experimental exit decision, authorize acceptance, or authorize implementation.
S1 through S5 remain open.

## Approver disposition after review

On 2026-08-16, the RFC approver accepted the recommended two-stage S4 gate.
This changes D2's evaluation method, not the underlying candidate evidence or
the RFC lifecycle. S4 is Partial until every exact candidate has a reviewed,
falsifiable inspection disposition and every candidate that clears inspection
passes the common S1/S3 corpus with scanned dependencies, an explicit
environment allowlist, and a fresh synthetic profile.
