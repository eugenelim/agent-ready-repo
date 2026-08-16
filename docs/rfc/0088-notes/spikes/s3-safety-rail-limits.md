# S3 — Safety-rail limits

**Result:** Partial — local file/data rails passed; browser/network corpus blocked.
**Run date:** 2026-08-15
**Decision owner:** RFC-0088 owner with security reviewer

## Reproduction identity

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2, arm64
- Node: 26.4.0; Playwright: 1.62.0
- Result SHA-256:
  `588096d3ae1c1332c99dab91a97abe06a19f9d69d0de817d011ae5ab28c36681`
- Temporary fixture root: `/private/tmp/rfc0087-web-pilot.goTDdp`
- Reconstructable synthetic source:
  [`experimental-fixture-source-archive.md`](experimental-fixture-source-archive.md)

## Reproduction procedure

```bash
SPIKE_ROOT=/private/tmp/rfc0087-web-pilot-replay
cd "$SPIKE_ROOT" \
  && node s3/safety.mjs
cd "$SPIKE_ROOT" \
  && node s2/host.mjs
cd "$SPIKE_ROOT" \
  && env DEBUG=pw:browser node s1-lifecycle.mjs
```

The first two fixtures were expected to exit zero and did. The browser fixture
was expected to exit zero but failed before a browser context existed, so every
browser-dependent row below remains blocked rather than inferred from API
documentation.

## Scenario matrix

| Scenario ID | Precondition | Stimulus | Expected observable | Actual bounded observable | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S3-PAGE-ROUTE-PRECEDENCE | Live browser context | Page route precedes owner route | Prevent or classify | Not reached | Blocked | S1 note |
| S3-ROUTE-REMOVAL | Live browser context | Adapter removes routes | Detect/prevent or classify | Not reached | Blocked | S1 note |
| S3-SERVICE-WORKER | Live browser context | Service Worker request | Block or classify bypass | Not reached | Blocked | S1 note |
| S3-PAGE-FETCH | Live browser page | In-page request | Enforce origin/method/DNS policy | Not reached | Blocked | S1 note |
| S3-WORKER-FETCH | Live worker | Worker request | Enforce or classify bypass | Not reached | Blocked | S1 note |
| S3-WEBSOCKET | Live browser page | Open WebSocket | Enforce or classify bypass | Not reached | Blocked | S1 note |
| S3-REDIRECT | Synthetic server and live browser | Redirect across policy boundary | Revalidate destination | Loopback listener and browser launch were policy-denied | Blocked | S1 launch and loopback errors |
| S3-DNS-REBINDING | Controlled resolver and live browser | Address changes after validation | Revalidate each connection | No controlled resolver/browser available | Blocked | Environment capability result |
| S3-BROWSER-PROXY | Live browser | Configure proxy route | Prevent bypass or classify | Not reached | Blocked | S1 note |
| S3-INHERITED-PROXY | Sanitized host | Supply proxy environment | Browser does not inherit unapproved proxy | Not reached | Blocked | S1 note |
| S3-REQUEST-CLIENT-METHODS | Live context request client | Exercise every HTTP method | Exact method policy or explicit unobservable class | Not reached | Blocked | S1 note |
| S3-RAW-NODE-EGRESS | Node child under Permission Model | File, child, network attempts | Deny ordinary accidental paths | All three returned `ERR_ACCESS_DENIED` | Pass as seat belt only | `s2-results.json` |
| S3-PATH-TRAVERSAL | Generated artifact root | `../../outside.txt` | Refuse before write | `lexical-escape` | Pass | `s3-results.json` |
| S3-SYMLINK-ESCAPE | Generated symlink to sibling directory | Resolve target | Refuse after resolution | `resolved-escape` | Pass | Same result |
| S3-LOGGING | Nested credential-shaped fields | Redact event | Remove recursively | Both fields became `[REDACTED]` | Pass | Same result |
| S3-DOWNLOAD | Synthetic PDF metadata | Validate size, magic, generated name | Accept valid bounded file | 18 bytes, `%PDF-` | Pass | Same result |
| S3-BYTE-QUOTA | 18-byte artifact; maximum 8 | Enforce limit | Typed refusal | `resource-limit-exceeded:bytes` | Pass | Same result |
| S3-ITEM-QUOTA | Two items; maximum one | Enforce limit | Typed refusal | `resource-limit-exceeded:items` | Pass | Same result |
| S3-PAGE-QUOTA | Three pages; maximum two | Enforce limit | Typed refusal | `resource-limit-exceeded:pages` | Pass | Same result |
| S3-RETRY-QUOTA | One retry; maximum zero | Enforce limit | Typed refusal | `resource-limit-exceeded:retries` | Pass | Same result |
| S3-RETENTION | Old and recent synthetic records | Apply age and count rules | Retain newest eligible record only | One recent record retained | Pass | Same result |
| S3-PROTOCOL-STDOUT-QUOTA | Oversized synthetic result | Serialize against a 16-byte test ceiling | Refuse without partial JSON | `resource-limit-exceeded:result-bytes` | Pass | Same result |
| S3-PROTOCOL-STDERR-QUOTA | Oversized synthetic failure | Serialize against a 16-byte test ceiling | Replace only at a schema boundary | `resource-limit-exceeded:failure-bytes` | Pass | Same result |
| S3-COMMITTED-ARTIFACT-QUOTA | Fifty committed synthetic artifacts | Attempt one additional commit | Refuse and preserve all prior entries | `resource-limit-exceeded:artifact-quota`; before and after counts remained 50 | Pass | Same result |
| S3-DIAGNOSTICS-QUOTA | Synthetic capture exceeds its test ceiling | Apply diagnostic byte limit | Preserve the original typed failure, mark truncation, and release no handle | Original failure retained; `diagnosticsTruncated: true`; handle absent | Pass | Same result |
| S3-QUARANTINE-QUOTA | Twenty synthetic staging entries | Attempt one additional entry | Refuse without evicting an active/rollback target | `resource-limit-exceeded:storage-quota`; before and after counts remained 20 | Pass | Same result |
| S3-QUARANTINE-RETENTION | Expired inactive, active, and rollback entries | Apply seven-day cleanup rule | Remove only expired inactive entry | Active and rollback entries retained | Pass | Same result |
| S3-ACTIVE-PROFILE-QUOTA | Generated nine-byte profile marker; eight-byte test ceiling | Check before simulated launch | Refuse and do not delete profile state | `resource-limit-exceeded:profile-bytes`; marker remained | Pass | Same result |
| S3-TWO-PHASE-FAILURE | Staged artifact | Inject failure before rename | No final artifact | Final absent | Pass | Same result |
| S3-TWO-PHASE-COMMIT | Validated staged artifact | Rename to final | Exact bytes committed | 18-byte final artifact | Pass | Same result |

## Sensitive-data disposition

Only generated files, synthetic secret-shaped strings, and inert payloads were
used. No external network request completed. The repository receives no raw
diagnostic or filesystem path beyond the approved temporary-root placeholder.

## Decision impact

The local path, protocol, artifact, diagnostics, quarantine, profile-quota,
retention, download, and commit shapes are constructible under the synthetic
fixture's deliberately tiny ceilings. Those unit-level checks do not validate
the proposed production values or establish the central browser claim. S3 therefore
preserves D13 exactly: capable adapters remain trusted code, and the browser
rails are not called enforced read-only. Rerun the entire browser/network
corpus after S1 clears; security review must classify each channel as prevent,
detect-after-the-fact, or cannot observe.
