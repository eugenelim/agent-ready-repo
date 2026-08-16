# S1 — Persistent bind lifecycle

**Result:** Blocked — Experimental exit is closed.
**Run date:** 2026-08-15
**Decision owner:** RFC-0088 approver

## Reproduction identity

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2 (build 25F84), arm64
- Node: 26.4.0; npm: 11.17.0
- Playwright: 1.62.0
- Bundled channel: Chrome for Testing 151.0.7922.34, revision 1234
- System channel: stable Chrome 151.0.7922.138
- `playwright` registry tarball SHA-512:
  `675e1d1b7d3976068bbba7e80754d741a805896f097d250851a52e3da290e8db413ca1753ffa9772a7e1e9ce8afe270fa9dcb7ec99a36e20577fa24d83a4b297`
- `playwright-core` registry tarball SHA-512:
  `9ec351caad2bdb3b06f007111d692773d4110395c2b9e0bb81632bb3e1b1dad9599fd85c97ccee75f874d258493d8d4313b36667a6c3b13f60db27b2f265e58c`
- Temporary fixture root: `/private/tmp/rfc0087-web-pilot.goTDdp`
- Reconstructable synthetic source:
  [`experimental-fixture-source-archive.md`](experimental-fixture-source-archive.md)
- Result digests: bundled lifecycle
  `7f1c96c48b6d7b35fe9c403dcebd2f801471cb15950a6b464d2d3c90b33a614e`;
  system channel
  `1aeb77cfa8a94705db3992828cc1f64634c80670683c0e685fe73b687d022676`

The browser-control runtime tool was absent. The npm registry was denied even
after approval, so the exact registry tarballs were recovered from the local
npm content-addressed cache and verified against their recorded integrity
digests. Both required browser binaries were already installed locally.

## Reproduction procedure

The executed fixture files are `s1-lifecycle.mjs` and
`s1-system-channel.mjs` beneath the temporary root. The actual commands were:

```bash
SPIKE_ROOT=/private/tmp/rfc0087-web-pilot-replay
cd "$SPIKE_ROOT" \
  && npm ci --ignore-scripts
cd "$SPIKE_ROOT" \
  && node node_modules/playwright/cli.js install chromium
cd "$SPIKE_ROOT" \
  && node node_modules/playwright/cli.js --version
cd "$SPIKE_ROOT" \
  && env DEBUG=pw:browser node s1-lifecycle.mjs
cd "$SPIKE_ROOT" \
  && env DEBUG=pw:browser node s1-system-channel.mjs
```

Expected exit status was zero for both lifecycle fixtures. Both returned
nonzero after browser launch failed. Optional cleanup is deliberately deferred
while the RFC remains Experimental; after evidence review, verify the exact
temporary root before removing it.

## Scenario matrix

| Scenario ID | Precondition | Stimulus | Expected observable | Actual bounded observable | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S1-PERSISTENT-LAUNCH-BUNDLED | Cached bundled channel and generated profile | `launchPersistentContext` | One persistent context | Browser exited before context creation; Chromium reported a Mach-port rendezvous permission denial and Playwright reported a closed target | Blocked | `s1-lifecycle-results.json` |
| S1-OWNING-BROWSER | Persistent context exists | `context.browser()` | Owning browser returned | Not reached | Blocked | Same result |
| S1-BIND | Owning browser exists | `browser.bind(title)` | Local endpoint returned | Not reached | Blocked | Same result |
| S1-CLI-DASHBOARD-ATTACH | Bound browser exists | Bundled `cli attach` and dashboard | CLI attaches to same context | Not reached; CLI command presence was confirmed only by `cli --help` | Blocked | Same result |
| S1-DEFAULT-CONTEXT | Native client attached | Inspect page and cookie jar | Same live page/context visible | Not reached | Blocked | Same result |
| S1-DISCONNECT-RECONNECT | First client attached | Close client and reconnect | Owner and context survive | Not reached | Blocked | Same result |
| S1-ATTACHMENT-EXPIRY | Browser bound | `unbind`, then reconnect | New attachment refused | Not reached | Blocked | Same result |
| S1-BROWSER-CLOSE | Owner running | Close browser | Deterministic disconnected state | Not reached | Blocked | Same result |
| S1-OWNER-CRASH | Owner and browser running | Terminate owner | Deterministic recovery or typed refusal | Not reached | Blocked | Same result |
| S1-STALE-AMBIGUOUS-LOCK | Profile has stale/ambiguous state | Relaunch owner | Recover only proven stale state; otherwise refuse | Not reached | Blocked | Same result |
| S1-CLEAN-SHUTDOWN | Owner and browser running | Close through owner | Profile can be reopened | Not reached | Blocked | Same result |
| S1-PERSISTENT-LAUNCH-SYSTEM | Stable system channel and generated profile | `launchPersistentContext` with exact executable | One persistent context | Browser exited with `SIGABRT` before context creation; the environment also denied Playwright's cleanup signal | Blocked | `s1-system-results.json` |

## Sensitive-data disposition

Only generated profiles, a synthetic cookie name/value, and an inert local
page were used. No existing browser profile, credential, website, request, or
user data was read. The promoted note contains bounded error classes and
versions only; raw launch logs and generated profiles remain in the temporary
root and outside the repository.

## Decision impact

- D2 remains unproven operationally. Official Playwright 1.62 documentation
  confirms `browser.bind`, bundled CLI attachment, and the dashboard, but that
  contract evidence cannot replace this lifecycle run.
- No initial OS/browser support row is accepted. macOS arm64 with both bundled
  Chromium and the tested system channel is deferred pending a run outside the
  enterprise Mach-port restriction.
- S1 must be rerun in an environment that can launch Chromium and expose the
  dashboard. Targeted architecture, security, and quality review is required
  after that evidence lands.
## 2026-08-16 rerun

This run's conclusion is superseded by the
[2026-08-16 Experimental rerun](2026-08-16-experimental-rerun.md#s1--persistent-bind-lifecycle).
The current verdict is **Partial**: real browser lifecycle coverage now passes,
but attachment expiry, seeded stale-lock recovery, and typed ownership
predicates remain open.
