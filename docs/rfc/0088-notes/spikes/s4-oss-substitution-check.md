# S4 — Reproducible open-source substitution check

**Result:** Blocked — bounded inventory recorded; executable conformance unavailable.
**Survey date:** 2026-08-15
**Decision owner:** RFC-0088 approver

## Reproduction identity and search procedure

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2, arm64
- Search surface: public web search restricted to official project sites,
  official documentation, and project-owned GitHub repositories/releases
- Search strings:
  - `local-first browser automation daemon persistent profiles dashboard open source GitHub 2026`
  - `browser automation CLI persistent profiles dashboard daemon GitHub releases 2026`
  - `PinchTab releases profiles dashboard daemon`
  - `agent-browser releases persistent profiles daemon dashboard`
  - `OpenChrome releases profile broker auto elect CLI dashboard MCP`
  - `OpenDevBrowser releases daemon profile dashboard`
  - `Browsertrix releases local authenticated profile Kubernetes crawler`
- Search cutoff: 2026-08-15

Inclusion required all of: open source; a local or self-hosted executable; a
tagged version that can be pinned; persistent profile ownership; visible human
handoff; deterministic non-model browser control; and active release evidence
within the prior twelve months. Hosted-only services, model-first frameworks,
archival crawlers, extension-only tools, and projects without one pin-able
runtime version were excluded.

Official sources checked:

- [Playwright 1.62 release notes](https://playwright.dev/docs/release-notes)
- [Playwright CLI repository and session contract](https://github.com/microsoft/playwright-cli)
- [PinchTab repository](https://github.com/pinchtab/pinchtab) and
  [v0.15.0 release](https://github.com/pinchtab/pinchtab/releases/tag/v0.15.0)
- [agent-browser repository](https://github.com/vercel-labs/agent-browser) and
  [0.33.1 changelog](https://github.com/vercel-labs/agent-browser/blob/main/CHANGELOG.md)
- [OpenChrome repository](https://github.com/shaun0927/openchrome) and
  [v1.12.9 release](https://github.com/shaun0927/openchrome/releases/tag/v1.12.9)
- [OpenDevBrowser repository](https://github.com/freshtechbro/opendevbrowser) and
  [v0.0.40 release](https://github.com/freshtechbro/opendevbrowser/releases/tag/v0.0.40)
- [Browsertrix repository](https://github.com/webrecorder/browsertrix) and
  [v1.22.8 release](https://github.com/webrecorder/browsertrix/releases/tag/v1.22.8)

The search is reproducible and bounded by the named strings and cutoff; it is
not a claim that no other project exists. OpenChrome and OpenDevBrowser both
have pin-able current releases and meet the paper inclusion criteria, so they
are candidates below rather than unnamed exclusions. Browsertrix 1.22.8 is the
only inspected exclusion: its project-owned description and deployment release
define a Kubernetes-oriented archival crawling service, not a local
single-user authenticated-session owner. That is an inclusion-criterion result,
not a quality judgment.

## Candidate matrix

| Scenario ID | Candidate/version | Profile and handoff | Deterministic adapter fit | Crash/attachment/local containment | Dependency/update posture | Result |
| --- | --- | --- | --- | --- | --- | --- |
| S4-PLAYWRIGHT-1.62 | Bundled library + CLI | Persistent contexts, named binding, dashboard/manual takeover are official | Exact native Playwright objects match the proposed adapter ABI | Binding/unbinding exists; RFC-specific ownership, grants, crash recovery, and artifact policy remain custom | One exact npm dependency; current RFC choice | Retain as substrate; runtime conformance blocked by S1 |
| S4-PINCHTAB-0.15.0 | Server + per-browser bridge; headed profiles and dashboard | Strong operator handoff | HTTP/CLI/MCP action surface does not supply the proposed native Playwright execution fixture | Owns daemon/profile orchestration, but adds a privileged control plane and broad mutating actions | Additional Go binary and separate release/security lifecycle | Reject substitution unless a future adapter-host bridge passes the same authority tests; not executed here |
| S4-AGENT-BROWSER-0.33.1 | Rust client/daemon; persistent profiles and dashboard | Strong handoff and explicit idle lifecycle | Direct Chrome DevTools Protocol daemon replaces rather than supplies native Playwright objects; broad commands, state export, plugins, and optional model/cloud surfaces widen authority | Removes meaningful daemon and recovery code; current changelog adds idle cleanup and restore validation | Additional Rust binary with fast independent release cadence | Credible replacement candidate, but cannot be adopted without executable contract/security conformance |
| S4-OPENCHROME-1.12.9 | One direct Chrome/CDP owner per profile with broker clients; current release adds live broker validation and half-zombie recovery | Strong shared-profile ownership and human-visible Chrome | Host-neutral MCP/CLI surface does not supply the proposed native Playwright fixture and includes broad browser actions plus memory/evidence features | Removes material owner election, stale metadata, and crash-recovery code but introduces an MCP/CDP control plane | Additional npm runtime and independent broker/update/security lifecycle | Credible lifecycle substitution candidate; must pass the same authority, state-export, and native-fixture tests |
| S4-OPENDEVBROWSER-0.0.40 | Local daemon, managed persistent profiles, extension relay, and headed sessions | Strong handoff through managed or extension-backed modes | Broad CLI/tool CDP and extension surface includes interaction, cookie, export, desktop-observation, plugin, and auto-start paths beyond the RFC boundary | Removes daemon/profile/reconnect work but adds extension relay, background auto-start, multiple endpoints, and a much wider filesystem/config surface | Additional npm package, extension assets, install-time reconciliation, and separate release cadence | Credible lifecycle candidate but authority is wider on paper; executable containment and exact-version packaging tests are mandatory |

### Falsifiable exclusion

| Inspected project/version | Primary evidence | Failed inclusion criterion | Revisit trigger |
| --- | --- | --- | --- |
| Browsertrix 1.22.8 | Project README and exact Helm release above | Cloud-native web-archiving crawler/orchestrator; not a local single-user authenticated-session owner | A separately versioned local session component demonstrates the S1/S3 contract without the Kubernetes/archive product surface |

## Required-scenario disposition

| Scenario ID | Expected evidence | Actual bounded evidence | Result |
| --- | --- | --- | --- |
| S4-DATED-INVENTORY | Bounded current candidate set, exact queries, and cutoff | Recorded above without a completeness claim | Pass |
| S4-OFFICIAL-CONTRACTS | Primary version and contract evidence | Recorded above | Pass |
| S4-SAME-PROFILE-OWNERSHIP | Run each candidate against one generated profile | Browser execution unavailable | Blocked |
| S4-HUMAN-HANDOFF | Observe live same-session takeover | Browser/dashboard tool unavailable | Blocked |
| S4-DETERMINISTIC-ADAPTER | Execute the same immutable adapter fixture | Native-Playwright mismatch not bridged or tested | Blocked |
| S4-CRASH-RECOVERY | Kill owner and verify deterministic recovery/refusal | Browser execution unavailable | Blocked |
| S4-ATTACHMENT-LIFETIME | Attach, detach, expire, reconnect | Browser execution unavailable | Blocked |
| S4-LOCAL-CONTAINMENT | Run network/file/auth corpus | Candidate binaries not admitted or installed | Blocked |
| S4-DEPENDENCY-UPDATE | Name exact pinned artifact and update surface | Contract comparison recorded | Pass |

## Sensitive-data disposition

This was public product-contract research only. No candidate was installed, no
browser profile was opened, and no authenticated data or local configuration
was inspected.

## Decision impact

The thin Playwright broker remains the provisional recommendation because no
candidate passed the required conformance scenarios. This is not a positive S4
exit result. `agent-browser`, OpenChrome, and OpenDevBrowser have matured enough
to be load-bearing candidates and must be included in the rerun; that is a
material update to the imported survey. If any can supply the native adapter
fixture and exact connection/grant boundary without enabling its state export,
cookie, plugin, model, cloud, desktop-observation, or broad action surfaces, the
broker decision must be reopened before acceptance.
## 2026-08-16 rerun

This run's conclusion is superseded by the
[2026-08-16 Experimental rerun](2026-08-16-experimental-rerun.md#s4--substitution-candidates).
At the time of the rerun, the verdict was **Blocked against D2 as written**.
The current `agent-browser` candidate can bridge to native Playwright objects,
correcting the earlier ABI-fit rationale; its broader authenticated-session
authority is the evidence-based rejection reason. The approver subsequently
adopted the two-stage gate, so the authoritative current verdict is **Partial
under amended D2** until every candidate has a reviewed inspection disposition
and every candidate that clears inspection passes the common corpus under the
required execution controls.
