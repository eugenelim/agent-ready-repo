# S6 — Browser-session credentialed-skill taxonomy

**Result:** Pass for prototype feasibility; production convention remains unchanged.
**Run date:** 2026-08-15
**Decision owner:** Credentialed-skill convention owner after RFC acceptance

## Reproduction identity

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2, arm64
- Python: 3.13.13
- AgentBundle: 0.35.0, adapter contract 0.18
- Prototype result SHA-256:
  `817bc644e581d56f8d127d29f01f044f53f66eb669db79df6b2eff1fd9ec2eac`
- Temporary fixture root: `/private/tmp/rfc0087-web-pilot.goTDdp`
- Reconstructable synthetic source:
  [`experimental-fixture-source-archive.md`](experimental-fixture-source-archive.md)

The current production verifier and catalogue linter still admit exactly
`env`, `cli`, `creds`, and `sso-cookie`. This spike copied their relevant
frontmatter/AST shape into a temporary prototype and added
`browser-session`; it did not edit repository lint or conventions.

## Reproduction procedure

```bash
SPIKE_ROOT=/private/tmp/rfc0087-web-pilot-replay
cd "$SPIKE_ROOT" \
  && python3 s6/prototype_lint.py
```

Expected and observed exit status: zero. Fixtures live under
`s6/fixtures/<scenario>/` in the temporary root.

## Scenario matrix

| Scenario ID | Precondition/stimulus | Expected observable | Actual bounded observable | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| S6-ACCEPTED | `auth: browser-session`; exact home-relative root-bin path; opaque job-file argument | Clean | No findings | Pass | `s6-results.json` |
| S6-COOKIE-IMPORT | Import cookie resolver | Reject | `credential-or-browser-import` | Pass | Same result |
| S6-CREDENTIAL-ARGV | Declare `--token` | Reject | `credential-shaped-argv` | Pass | Same result |
| S6-STDOUT | Put `token` in printed payload | Reject | `credential-shaped-payload:token` | Pass | Same result |
| S6-STDERR | Put `cookie` in stderr payload | Reject | `credential-shaped-payload:cookie` | Pass | Same result |
| S6-JOB-JSON | Put `storage_state` in job object | Reject | `credential-shaped-payload:storage_state` | Pass | Same result |
| S6-DIAGNOSTICS | Put `authorization` in diagnostic event | Reject | `credential-shaped-payload:authorization` | Pass | Same result |
| S6-MODEL-RESULT | Put `passkey` in result object | Reject | `credential-shaped-payload:passkey` | Pass | Same result |
| S6-STORAGE-STATE | Put storage state in another result channel | Reject | Same credential-shaped finding | Pass | Same result |
| S6-AUTH-HEADER | Put authenticated headers in a result | Reject | `credential-shaped-payload:authenticated_headers` | Pass | Same result |

The prototype also requires `subprocess.run`, rejects broader process APIs,
rejects Playwright imports in the consumer, and requires the exact projected
launcher expression `Path.home() / ".agentbundle" / "bin" / "web-pilot.py"`.

## Sensitive-data disposition

Every credential-shaped value is the string `synthetic`. The fixtures were
parsed but not invoked against a browser, credential broker, or model. No
credential or protected configuration was read.

## Decision impact

D7 is feasible without reusing `sso-cookie` or adding a credential-export
path. Acceptance still requires a separate convention amendment and production
tests. The prototype's literal-key detection is intentionally conservative and
is not itself production-quality dataflow analysis; the later amendment must
integrate with both current auth allowlists and the catalogue AST pass, retain
the positive fixture, and keep every negative channel fixture.
