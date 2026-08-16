# S5 — Cross-pack provider vertical

**Result:** Partial — pack/grant vertical passed; same-browser row blocked by S1.
**Run date:** 2026-08-15
**Decision owner:** RFC-0088 owner

## Reproduction identity

- Repository ref: `573c7dd9d52a547ca10d584bf042851c50c88072`
- Host: macOS 26.5.2, arm64
- Python: 3.13.13
- AgentBundle: 0.35.0, adapter contract 0.18
- Fixture packs: `web-pilot@1.0.0`, `example-provider-a@1.0.0`,
  `example-provider-b@1.0.0`
- Result SHA-256:
  `5f8d1a93fd083a37f4638665ebd3f6342513b01f14d34ba322361a81158cbdfc`
- Temporary fixture root: `/private/tmp/rfc0087-web-pilot.goTDdp`
- Reconstructable synthetic source:
  [`experimental-fixture-source-archive.md`](experimental-fixture-source-archive.md)

## Reproduction procedure

The synthetic catalogue is under `s5/catalogue/`; rendered distributions are
under `s5/rendered-all/`; isolated user installation state is under
`s5/user-root-final/`.

```bash
SPIKE_ROOT=/private/tmp/rfc0087-web-pilot-replay
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle validate "$SPIKE_ROOT/s5/catalogue/packs/web-pilot" --strict
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle validate "$SPIKE_ROOT/s5/catalogue/packs/example-provider-a" --strict
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle validate "$SPIKE_ROOT/s5/catalogue/packs/example-provider-b" --strict
cd "$REPO_ROOT" \
  && env AGENTBUNDLE_USER_ROOT="$SPIKE_ROOT/s5/missing-root" PYTHONPATH=packages/agentbundle python3 -m agentbundle install "$SPIKE_ROOT/s5/catalogue" --pack example-provider-a --scope user --adapter codex --yes
cd "$REPO_ROOT" \
  && env AGENTBUNDLE_USER_ROOT="$SPIKE_ROOT/s5/user-root-final" PYTHONPATH=packages/agentbundle python3 -m agentbundle install "$SPIKE_ROOT/s5/catalogue" --pack web-pilot --scope user --adapter codex --yes
cd "$REPO_ROOT" \
  && env AGENTBUNDLE_USER_ROOT="$SPIKE_ROOT/s5/user-root-final" PYTHONPATH=packages/agentbundle python3 -m agentbundle install "$SPIKE_ROOT/s5/catalogue" --pack example-provider-a --scope user --adapter codex --yes
cd "$REPO_ROOT" \
  && env AGENTBUNDLE_USER_ROOT="$SPIKE_ROOT/s5/user-root-final" PYTHONPATH=packages/agentbundle python3 -m agentbundle install "$SPIKE_ROOT/s5/catalogue" --pack example-provider-b --scope user --adapter codex --yes
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle render "$SPIKE_ROOT/s5/catalogue/packs/web-pilot" --output "$SPIKE_ROOT/s5/rendered-all/web-pilot"
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle render "$SPIKE_ROOT/s5/catalogue/packs/example-provider-a" --output "$SPIKE_ROOT/s5/rendered-all/example-provider-a"
cd "$REPO_ROOT" \
  && env PYTHONPATH=packages/agentbundle python3 -m agentbundle render "$SPIKE_ROOT/s5/catalogue/packs/example-provider-b" --output "$SPIKE_ROOT/s5/rendered-all/example-provider-b"
cd "$SPIKE_ROOT" \
  && python3 s5/harness.py
```

The missing-dependency command is expected to exit one. The validations,
foundation/provider installs, explicit renders, and harness are expected to
exit zero.

The bounded validation/dependency observations were:

```text
web-pilot strict validation: exit 0
example-provider-a strict validation: exit 0
example-provider-b strict validation: exit 0
each validator emitted: --strict conformance fixtures not present — skipping
provider-a install into empty root: exit 1
install: pack 'example-provider-a' requires 'web-pilot' (version ^1.0); install web-pilot first
```

These inline observations are the evidence for the first two matrix rows; no
unreferenced transcript artifact is implied. The reconstructable source archive
plus the commands above regenerate the catalogue, rendered/install trees, job
files, and bounded result JSON without relying on the original random temporary
directory.

## Scenario matrix

| Scenario ID | Stimulus | Expected observable | Actual bounded observable | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| S5-VALIDATE-THREE-PACKS | Strictly validate all pack manifests | All accepted under current schema and destination category vocabulary | All accepted with `integrations`; only the expected absence-of-conformance-fixtures message remained | Pass | Inline bounded observations above |
| S5-DEPENDENCY-ABSENT | Install provider into empty user root | Fail before write | Exit 1 naming required `web-pilot ^1.0` | Pass | Inline bounded observation above |
| S5-D16-ROOT-BIN | Install foundation through Codex user adapter | Python launcher reaches `.agentbundle/bin/` | Installed at exact current rail | Pass | Installed tree |
| S5-D16-PAYLOAD | Render/install setup skill | Node package and lockfile remain inside skill | Source/render/install SHA-256 values identical | Pass | S5-SOURCE-RENDER-INSTALL-2 |
| S5-STABLE-LAUNCHER-ONLY | Scan provider scripts | No projection, sibling-skill, Node, or Playwright import | No forbidden token found | Pass | S5-NO-CROSS-PACK-IMPORT |
| S5-VALIDATION | Submit validation-only job | No browser launch or provider data | Bounded confirmation-required result; launch delta zero | Pass | `s5-results.json` |
| S5-CANDIDATE-DISCARD | Resolve synthetic identity candidate | Host-only value discarded | Confirmation file absent; provider result contains no correlation value | Pass | Same result |
| S5-MIXED-VALIDATION | Add behavior to validation job | Reject before launch | `mixed-authorization-surface`; delta zero | Pass | Same result |
| S5-SUMMARY-POSITIVE | Exact provider-A grant | Bounded summary; one simulated launch | Count-only summary; delta one | Pass | Same result |
| S5-ARTIFACT-POSITIVE | Exact provider-B grant | Opaque handle; one simulated launch | Handle only, `released: false`; delta one | Pass | Same result |
| S5-IDENTITY-MISMATCH | Swap declared consumer identity | Reject before launch | `consumer-not-authorized`; delta zero | Pass | Same result |
| S5-GRANT-PAIR-MISMATCH | Pair provider A job with grant B | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-UNGRANTED-RESOURCE | Change resource-scope digest | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-SENSITIVITY-MISMATCH | Change sensitivity | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-RESULT-POLICY-MISMATCH | Change result policy | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-NARROWER-POLICY-NO-AMENDMENT | Claim narrower policy without grant amendment | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-SCHEMA-MISMATCH | Change output schema digest | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-DIGEST-MISMATCH | Change adapter digest without matching grant | Reject before launch | Same typed failure; delta zero | Pass | Same result |
| S5-INDEPENDENT-UPGRADE-A | Use separately approved adapter-v2 grant for provider A | Pass without changing provider B | Summary passes; delta one | Pass | Same result |
| S5-INDEPENDENT-OLD-B | Reuse provider B's adapter-v1 grant | Old digest remains usable | Artifact result passes; delta one | Pass | Same result |
| S5-SOURCE-RENDER-INSTALL-1 | Hash root-bin source/render/install | Byte-identical | All three SHA-256 values `4dee7fea…c1145` | Pass | Same result |
| S5-SOURCE-RENDER-INSTALL-2 | Hash lock source/render/install | Byte-identical | All three SHA-256 values `f782aedd…3829` | Pass | Same result |
| S5-SOURCE-UNVERIFIED-APPROVAL | Inspect unverified-source record | Explicit, digest-bound state | `sourceVerified: false`, `explicitApproval: true` | Pass | Same result |
| S5-SAME-BROWSER-HANDOFF | Execute validation then behavior in same live browser | Same context preserved | Browser could not launch under S1 | Blocked | S1 note |

## Sensitive-data disposition

All pack names, grants, resources, identities, results, artifacts, and
provenance are synthetic. `AGENTBUNDLE_USER_ROOT` confined installation to the
approved temporary directory. No real user-scope state or browser profile was
read or written. Only bounded JSON results and hashes are promoted.

## Decision impact

S5 confirms D16: the present complete-skill projection plus Python
`adapter-root-bins` rail delivers the embedded runtime payload and stable
launcher without a new primitive. It also validates the exact grant tuple and
the validation/behavior split in a throwaway construction harness. S5 cannot
exit until the same-browser row runs after S1; the current result does not prove
malicious same-user caller isolation.
