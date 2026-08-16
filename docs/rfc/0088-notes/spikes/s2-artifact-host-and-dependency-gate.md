# S2 — Artifact, host, and Node dependency gate

**Result:** Partial — artifact/host construction passed; dependency gate blocked.
**Run date:** 2026-08-15
**Decision owner:** RFC-0088 owner with the repository security owner

## Reproduction identity

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2, arm64
- Node: 26.4.0; npm: 11.17.0
- Playwright: 1.62.0; exact runtime lock digest:
  `f6934c2a7671a35dd2662736d21447ff3f2cb40e07934572e3866de7517bebe7`
- Trivy: 0.72.0; check-bundle digest:
  `sha256:1583562f8b90ed2a071b99f0e5ffff6b57e4ceb6ca3e4796577b4e6a339eb74c`
- Candidate archive SHA-256:
  `bc4e406f869e7471dd07839e176fdee01f0b1b597bef9c8ebecfe168a7a2a8b3`
- Result SHA-256:
  `a21bb3a615dde1b474e77ee823bbb9d93e740123b42b16dc536f12c9cdd1e589`
- Temporary fixture root: `/private/tmp/rfc0087-web-pilot.goTDdp`
- Reconstructable synthetic source:
  [`experimental-fixture-source-archive.md`](experimental-fixture-source-archive.md)

The lockfile was reconstructed from the two verified registry tarball records
because npm's registry resolver was denied. It is adequate for this throwaway
inspection but is not a substitute for the frozen lockfile an accepted pack
would generate with the approved package manager.

## Reproduction procedure

```bash
SPIKE_ROOT=/private/tmp/rfc0087-web-pilot-replay
cd "$SPIKE_ROOT" \
  && node s2/generate-symlink-fixture.mjs
cd "$SPIKE_ROOT" \
  && node s2/host.mjs
cd "$SPIKE_ROOT/s2" \
  && env NPM_CONFIG_CACHE="$SPIKE_ROOT/npm-cache" npm pack ./adapter-package --ignore-scripts --pack-destination .
cd "$SPIKE_ROOT" \
  && tar -tzf s2/example-service-synthetic-read-adapter-1.0.0.tgz
cd "$SPIKE_ROOT" \
  && trivy fs --cache-dir "$SPIKE_ROOT/trivy-cache" --scanners vuln --exit-code 1 --severity HIGH,CRITICAL --format json --output s2/trivy-clean.json package-lock.json
cd "$SPIKE_ROOT" \
  && trivy fs --cache-dir "$SPIKE_ROOT/trivy-cache" --scanners vuln --exit-code 1 --severity HIGH,CRITICAL --format json --output s2/trivy-vulnerable.json s2/vulnerable-lock/package-lock.json
```

The symlink generator recreates the deliberate rejection fixture only inside
the fresh replay root; the evidence archive itself contains no links. The host
and package commands were expected to exit zero and did. The first
scanner command is expected to exit zero for the runtime lock; the second is
expected to exit one with a High/Critical finding for the controlled vulnerable
lock. In this run scanner initialization failed before either scan because its
database could not be downloaded; the same failure survived approval.

## Scenario matrix

| Scenario ID | Precondition | Stimulus | Expected observable | Actual bounded observable | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S2-NONEXEC-INSPECTION | Separate JSON manifest and ESM entry point | Inspect paths and metadata without import | Manifest accepted | Adapter ID read; entry point not imported | Pass | `s2-results.json` |
| S2-PLAIN-ESM | Self-contained ESM, no runtime imports | Load in constrained host | Behavior executes with host fixture | Host-supplied page marker observed | Pass | Same result |
| S2-PACKAGE-ARCHIVE | Exact local source tree | `npm pack --ignore-scripts` | Immutable archive with only declared files | Three declared files; SHA-256 recorded | Pass | Candidate archive |
| S2-BUNDLED-ESM | Single self-contained compiled module | Inspect import surface | No bundled Playwright or second dependency tree | Module has no imports and receives the page through the host fixture | Pass with S1 caveat | `dist/adapter.mjs` |
| S2-INSTALL-SCRIPT | Candidate contains `postinstall` | Non-executing inspection | Refuse | `install-script-refused` | Pass | `s2-results.json` |
| S2-NATIVE-ADDON | Candidate contains `.node` | Non-executing inspection | Refuse | `native-addon-refused` | Pass | Same result |
| S2-SYMLINK | Candidate contains a symlink | Non-executing inspection | Refuse | `symlink-refused` | Pass | Same result |
| S2-HOST-SUPPLIED-PLAYWRIGHT | Adapter has no Playwright import | Execute with host-owned native object | Exact native object reaches adapter | A synthetic host marker reached the adapter; real native Playwright object was blocked by S1 | Partial | Same result + S1 note |
| S2-SANITIZED-ENVIRONMENT | Host environment omits secret fixture | Execute behavior | Adapter cannot observe secret | `secretVisible: false` | Pass | `s2-results.json` |
| S2-OUTPUT-VALIDATION | Malformed record ID | Validate before release | Reject | Invalid output evaluated false | Pass | Same result |
| S2-PERMISSION-SEATBELT | Node `--permission`, only entrypoint readable | Attempt file read, child process, and network | Deny each | All returned `ERR_ACCESS_DENIED` | Pass, defense in depth only | Same result |
| S2-SOURCE-VERIFIED | Clean commit-shaped provenance | Evaluate admission metadata | Verified state | `verified` | Pass | Same result |
| S2-SOURCE-UNVERIFIED | Archive digest plus explicit unverified approval | Evaluate admission metadata | Distinct explicit state | `explicit-unverified` | Pass | Same result |
| S2-SCANNER-CLEAN | Runtime lockfile | Trivy High/Critical blocking scan | Exit 0 | Vulnerability DB unavailable; mirror returned Forbidden | Blocked | Scanner stderr |
| S2-SCANNER-CONTROLLED-VULNERABLE | Controlled vulnerable lock | Same scan | Exit 1 with a finding | Not reached because DB initialization failed | Blocked | `s2/vulnerable-lock/package-lock.json` |

## Sensitive-data disposition

All manifests, modules, provenance, paths, outputs, and vulnerability fixtures
are synthetic. The environment probe used only a synthetic marker. No package
credentials or configuration files were inspected. Raw scanner state remains
outside the repository.

## Decision impact

- The smallest viable artifact is a self-contained ESM file inside an immutable
  archive. The spike found no need for bundler tooling; this remains contingent
  on a real native Playwright host run after S1.
- Node's Permission Model is confirmed only as a useful seat belt. Its official
  contract expressly disclaims protection from malicious code, so D13 is
  unchanged.
- D17 fails. No scanner or blocking policy can be selected from this run, and
  the first implementation specification remains forbidden. Rerun S2 where a
  maintained vulnerability database is available, require a controlled
  vulnerable-fixture failure, then send the decision-changing result through
  security and quality review.
## 2026-08-16 rerun

This run's conclusion is superseded by the
[2026-08-16 Experimental rerun](2026-08-16-experimental-rerun.md#s2--artifact-host-and-dependency-gate).
The current verdict is **Partial**: the dependency scanner and native object
path are viable, but the child-process environment boundary and parent-owned
output validation were not exercised end to end.
