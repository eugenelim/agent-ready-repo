# Playwright contract and browser landscape survey

> Discipline: applied practitioner-pattern survey

**Topic:** Current browser interfaces that could support a local,
authenticated, read-only-intent website-adapter runtime.
**Checked:** 2026-08-14
**Purpose:** Ground RFC-0088's browser ownership, handoff, dependency, and
build-versus-adopt decisions in current official contracts.

**Confidence legend:** **high** means a current official primary contract
directly supports the claim; **moderate** means the conclusion composes several
documented primitives or uses an architectural analogy; **low** means sources
conflict or the fact is historical. Confidence describes source support only,
not local spike validation or RFC acceptance.

## Findings

### One package currently exposes the required interfaces

The current Playwright release notes document direct library use plus bundled
CLI and MCP entry points. They also document browser binding so a launched
browser can be reached from the CLI, MCP, or another Playwright client. The
proposed foundation uses the library and CLI surfaces; it does not expose an MCP
server merely because the dependency also contains one. [high]

Sources: [release notes](https://playwright.dev/docs/release-notes),
[library](https://playwright.dev/docs/next/library),
[Browser API](https://playwright.dev/docs/next/api/class-browser).

The official API page labels `browser.bind()` as added in v1.59, while the
release page presents browser binding as new in v1.62. That historical detail
is inconsistent across official pages and is not load-bearing. RFC-0088 states
only the current contract. [high on current availability; low on introduction
version]

### The static persistent-browser chain exists

`launchPersistentContext(userDataDir)` returns the only persistent context for
that browser. `BrowserContext.browser()` returns its owning browser for normal
browser contexts. `browser.bind()` makes that browser attachable. The CLI can
attach to a Playwright endpoint, and its dashboard supports visual observation
and user control. [high]

Sources: [BrowserType API](https://playwright.dev/docs/api/class-browsertype),
[BrowserContext API](https://playwright.dev/docs/api/class-browsercontext),
[CLI attach](https://playwright.dev/agent-cli/commands/attach),
[sessions and dashboard](https://playwright.dev/agent-cli/sessions).

These primitives do not prove the combined operational lifecycle. Owner crash,
user browser close, reconnect, profile-lock recovery, default-context identity,
and system-browser behavior remain spike work. [high]

### Profile ownership is exclusive

Playwright documents that browsers do not permit multiple instances with the
same user-data directory and warns against automating a normal personal Chrome
profile. `web-pilot` must therefore own dedicated per-connection profiles and
fail closed on ambiguous ownership. [high]

Source: [BrowserType API](https://playwright.dev/docs/api/class-browsertype).

### Context request clients share authentication and remain powerful

`browserContext.request` and `page.request` return a context-associated
`APIRequestContext` that shares the browser context's cookie jar and updates it
from response cookies. The same API exposes GET, POST, PUT, PATCH, and DELETE.
It is useful for authenticated same-origin reads but confirms that native
adapters cannot be technically proven read-only in process. [high]

Sources: [APIRequestContext](https://playwright.dev/docs/next/api/class-apirequestcontext),
[API testing](https://playwright.dev/docs/next/api-testing).

### Routing is a safety rail, not isolation

`BrowserContext.route()` does not intercept page requests already handled by a
Service Worker; Playwright recommends blocking Service Workers when routing is
used for interception. Current Service Worker support can observe and route
some worker-owned network requests, but updated worker scripts still have a
known routing limitation. Page-level routes, route removal, WebSockets,
redirects, direct request-client calls, and raw Node egress need explicit spike
coverage. [high]

Sources: [BrowserContext routing](https://playwright.dev/docs/api/class-browsercontext#browser-context-route),
[Service Workers](https://playwright.dev/docs/service-workers),
[network guide](https://playwright.dev/docs/network).

## Browser ownership options

| Model | Handoff | Deterministic modules | Main cost | Decision |
| --- | --- | --- | --- | --- |
| Provider-local scripts | Provider-specific | Strong | Duplicated profiles and controls | Reject |
| CLI only | Strong | Weak module-loader fit | Command surface becomes production ABI | Reject |
| Library only | Headed browser | Strong | No standard dashboard attachment | Insufficient |
| Library broker + bound CLI | Same live context | Strong | IPC, leases, liveness, recovery | Recommend subject to spike |
| Remote browser | Remote live view | Strong | Authenticated state leaves device | Future opt-in |
| Do nothing | Existing behavior | Provider-specific | Duplication grows per provider | Reject |

## Native page plus domain context

Playwright fixtures and page-object guidance pass native `Page` objects into
typed helpers. The durable adapter shape is therefore a native pinned `Page`
and `BrowserContext` plus only the missing product semantics: connection and
resource aliases, cancellation, confined artifacts, redacted logging,
checkpoints, behavior metadata, and exact job/grant context. A facade that
mirrors locators, navigation, requests, and events would create a second
Playwright compatibility surface. [high]

Sources: [fixtures](https://playwright.dev/docs/test-fixtures),
[authentication](https://playwright.dev/docs/auth).

## Build-versus-adopt checkpoint

The adoption question is not whether another project launches browsers. A
replacement must own a dedicated local profile, support user handoff into the
same live session, load deterministic immutable adapters, expose a stable local
process contract, preserve local artifacts, recover from crashes, and state an
honest trusted-versus-restricted execution model. No surveyed browser tool is
assumed to meet that whole boundary; Experimental spike S4 must re-check the
landscape before implementation. [moderate]

S4 is reproducible rather than an open-ended web search: its note records the
date, queries/source locations, inclusion criteria, every candidate meeting
those criteria, the exact primary contract/version inspected, and a matrix of
the responsibilities above. A negative result is valid only when every included
candidate has a falsifiable rejection row; popularity or a summary assertion is
not evidence.

## Dependency recommendation

Use one exact, lockfile-pinned direct production dependency—`playwright`—in the
unpublished runtime. Necessary build-only tooling must be separately approved,
exact-pinned, scanned, and absent from the shipped artifact. Do not add crawler frameworks, model-driven browser frameworks,
stealth/CAPTCHA plugins, standalone MCP packages, or remote-browser SDKs in the
first release. Any additional production package requires a revised accepted
decision. [high]

## Known unknowns

- Persistent system-browser bind and dashboard behavior across crash/reconnect.
- Whether target sites remain functional with Service Workers blocked.
- Cross-platform named-pipe/socket and process-identity behavior.
- Whether a mature local-first broker can replace meaningful custom lifecycle code before implementation.
- Which sites rely on memory-only or session-only authentication that cannot survive restart.
