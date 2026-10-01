# ADR-0131: A pip-audit advisory suppression is a governed allowlist entry, and its retirement is enforced

- **Status:** Accepted
- **Date:** 2026-09-29
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** ADR-0133 D6
- **Related:** ADR-0017 (D8 — pip-audit is the SCA gate), ADR-0083 (the npm
  advisory allowlist this mirrors), ADR-0084 (a quiet scanner becomes a gate
  through a wrapper with a self-test), ADR-0102 (the sibling Semgrep exclusion
  vehicle, whose unenforced retirement trigger this record's Confirmation
  answers), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** A `pip-audit` advisory may be accepted rather than fixed, but
  only as an entry in `tools/pip-audit-allowlist.toml` carrying `id`,
  `package`, `fixed_in`, `reason` and `unblocked_when`. Bare `--ignore-vuln`
  flags are no longer a vehicle on the direct SAST manifest.
- **Because:** A flag keeps its reasoning in a Makefile comment, where nothing
  checks that the reasoning is still true or that the acceptance has outlived
  its cause. ADR-0102 names that exact weakness on the Semgrep leg and accepts
  it there; the cost that forced the acceptance there does not apply here.
- **Applies to:** every advisory suppressed on `tools/requirements-sast.txt`.
- **Tradeoff accepted:** three files and a 39-scenario self-test instead of a flag,
  plus a gate that deliberately reddens when upstream fixes the problem —
  because the alternative failure, an acceptance quietly outliving its cause,
  produces no signal at all.
- **Revisit if:** (1) Semgrep permits `PyJWT>=2.14.0` and the allowlist empties,
  at which point the vehicle stays but carries nothing; (2) an entry is proposed
  for a package other than `pyjwt`; or (3) the reachability finding below is
  falsified by an upstream release.

## Context

Semgrep declares `pyjwt[crypto]~=2.13.0`. That excludes PyJWT 2.14.0, which
fixes all ten currently-published PyJWT advisories. Nothing in this repository
can reach 2.14.0 while the pin stands: a direct pin or a constraints entry
produces an unsatisfiable resolve, not a remediation. Semgrep 1.178.0 — the
latest release as of 2026-09-29 — still declares it.

The leg carried one of the ten as `--ignore-vuln CVE-2026-102274`. Nine more
arrived, `gate-sast` went red on every pull request including unrelated ones,
and the obvious move — eight more flags — would have multiplied a vehicle that
cannot fail.

## Decision

- **D1:** A suppression is an entry in `tools/pip-audit-allowlist.toml`. A
  missing or blank required field is exit 2, not a skipped entry.
- **D2:** `allowed_packages` bounds the vehicle. An entry naming a package
  outside it is exit 2, so widening is its own visible edit.
- **D3:** Matching is on the advisory's primary `id` plus the PEP 503
  canonicalised package. Aliases are not a match path: an acceptance must not
  grow to cover a future advisory that merely lists an accepted one as an alias.
- **D4:** Retirement is enforced, not documented. When an entry's advisory stops
  being reported *and* the package resolves at or above `fixed_in`, the gate
  exits 2 and says to remove the entry.
- **D5:** Retirement is claimed only on positive evidence. If the package is
  absent from the report, or resolves below `fixed_in`, or the versions cannot
  be compared, the gate still exits 2 but explicitly withholds the remove
  instruction. A degraded feed, a withdrawn advisory and a truncated resolve all
  look identical at the entry level, and only one of them justifies deleting a
  written record.
- **D6:** `fixed_in` is cross-checked against the advisory's own `fix_versions`
  while the advisory is visible, so an unreachable value cannot suppress today
  and never retire.
- **D7:** The wrapper does not pass `--strict`. pip-audit 2.10.1 calls
  `_fatal()` on the first skipped dependency inside the audit loop
  (`_cli.py:555-558`), exiting before any formatter runs; under `--strict` the
  skipped dependency never reaches the JSON where this gate can name it.

## What this repository is accepting

Ten PyJWT 2.13.0 advisories, all fixed in 2.14.0, all unreachable by the
`make sast` invocation. Seven are key-confusion or signature-forgery bugs, two
are availability bugs, one is a revocation bypass. The per-advisory reasoning
lives in `tools/pip-audit-allowlist.toml` beside each entry, not here, so it
cannot drift from the thing it governs.

| Advisory | Class | Entry point it needs |
| --- | --- | --- |
| CVE-2026-102268 (CVSS v3.1 CRITICAL, `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`) | PEM-detection bypass → HMAC forgery | `HMACAlgorithm.prepare_key` |
| CVE-2026-102266 | empty `oct` JWK accepted as HMAC key | `HMACAlgorithm.from_jwk` |
| CVE-2026-102271 | DER public key as HMAC secret | `HMACAlgorithm.prepare_key` |
| CVE-2026-102272 | BOM-prefixed JWK as HMAC secret | `HMACAlgorithm.prepare_key` |
| CVE-2026-102273 | public JWK container as HMAC secret | `HMACAlgorithm.prepare_key` |
| CVE-2026-102267 | unrevalidated JWKS redirect | `PyJWKClient` construction |
| CVE-2026-101917 | JWKS fetch amplification on unknown `kid` | `PyJWKClient` construction |
| CVE-2026-102269 | non-canonical signature segment → revocation bypass | `jwt.decode` + a revocation list |
| CVE-2026-102265 | uncaught `RecursionError` on a nested header | `jwt.decode` |
| CVE-2026-102274 | malformed RSA JWK aborts the whole set | `PyJWKSet` construction |

**Owner of retirement:** repository maintainers. The gate is the reminder — D4
makes the trigger fire without anyone remembering it.

## The reachability finding, and how to re-verify it

Verified by hand on **2026-09-29**. Two distributions in the audited closure
import PyJWT:

| File | PyJWT use | Reached only by |
| --- | --- | --- |
| `semgrep/mcp/utilities/token_verifier.py` | `jwt.PyJWKClient(...)`, `jwt.decode(...)` | `make_token_verifier` → `setup_mcp_server` (`semgrep/commands/mcp.py`), i.e. the `semgrep mcp` subcommand |
| `mcp/client/auth/extensions/client_credentials.py` | `jwt.encode(...)` | private-key-JWT client authentication against an OAuth token endpoint |

`make sast` runs `tools/run-semgrep-gate.py` with `--config` flags and source
paths. It starts no MCP server and performs no OAuth client authentication, so
neither site executes. `semgrep`'s CLI does *import* the first module at
start-up, because it registers every subcommand — but no advisory above fires at
import; each needs a token, a JWK/JWKS, or a client construction.

Reproduce the file set with the command below. It walks only the two
distributions this finding covers, because an unscoped `site-packages` sweep
returns whatever else the reader happens to have installed — run here, it
returned a third file belonging to an unrelated distribution. It reads the
**installed** tree, which the versions below distinguish from the resolved one:

```bash
python3 - <<'EOF'
import pathlib, re, importlib.util
for dist in ("semgrep", "mcp"):
    root = pathlib.Path(importlib.util.find_spec(dist).origin).parent
    for path in sorted(root.rglob("*.py")):
        if re.search(r"^\s*(import jwt|from jwt)", path.read_text(errors="ignore"), re.M):
            print(path.relative_to(root.parent))
EOF
```

**Versions.** Walked: `semgrep` 1.175.0, `mcp` 1.29.0, `pyjwt` 2.13.0.
Resolved by `pip-audit -r` in the same run: `semgrep` **1.178.0**, `mcp` 1.29.0,
`pyjwt` 2.13.0. The semgrep delta is expected and is not a defect —
`tools/requirements-sast.txt` pins a range, `pip-audit -r` always resolves the
newest version it allows, and `tools/check-semgrep-version.py` keeps the
installed one inside that range. It is recorded because the walk and the
advisory set describe different trees, and a reader must be able to see that.

**Envelope.** This finding covers the `make sast` invocation and nothing else.
A contributor who installed `tools/requirements-sast.txt` and runs `semgrep mcp`
from that same install is *outside* it: that path does construct a
`PyJWKClient` and does decode tokens, and this repository's tooling will no
longer report these ten advisories to them.

## Consequences

The Python and npm SCA legs now share a shape, and the header comment in
`tools/npm-audit-allowlist.toml` that pointed at this leg's `--ignore-vuln`
flags as the weaker sibling has been corrected. `docs/adr/0083`'s "four live
`--ignore-vuln` entries" sentence is left as written: the count was already
wrong before this change (one flag remained), and amending an accepted ADR is
its own governance act rather than a side effect of this one.

**Revisit if:** (1) a Semgrep release permits `PyJWT>=2.14.0`, which empties the
allowlist and leaves the vehicle carrying nothing; (2) an entry is proposed for a
package other than `pyjwt`, which requires widening `allowed_packages` and is a
decision in its own right; (3) the reachability finding recorded above is
falsified by an upstream release, at which point the acceptances lose their
grounds rather than their trigger; or (4) this repository adopts CODEOWNERS or
equivalent review routing, which would close residual 3.

## Residuals

Three, recorded rather than implied.

1. **No check verifies the reachability finding.** An earlier draft specified a
   mechanical evidence pin over the file set importing `jwt`. It was removed
   after review showed the oracle could not perform the comparison the criterion
   claimed — a call-path change inside an already-approved file moves no file
   set, and the walk's natural scope missed the `mcp` call site entirely. A
   proxy that cannot see the failure it names is worse than an absent check,
   because it manufactures assurance. Re-verification is a human obligation at
   the Revisit-if triggers above, using the command in this record.
2. **The audited floor does not see the transitive closure.** The gate asserts
   the manifest's direct requirements (`bandit`, `pip-audit`, `semgrep`) are
   present and audited. A resolve that keeps all three but loses a transitive
   package carrying an advisory reads as clean. A closure-wide expected-name set
   would churn on every upstream release — the failure the removed pin already
   demonstrated. Registered as `sca-hardening-uneven-across-pip-audit-invocations`.
3. **Reviewer attention is the only anchor on the allowlist file.** One diff
   supplies both an entry and its justification, and `gate-sast` runs the pull
   request's own copy. `allowed_packages` bounds which dependency an entry may
   name, which makes widening visible, but it bounds a typo rather than an
   author. This repository has no CODEOWNERS file; `CONTRIBUTING.md:263-278`
   lists CODEOWNERS-driven review routing among above-Profile-C measures to
   adopt "when the friction of *not* having them exceeds the friction of
   adopting them — not as a precaution". That is conditional sizing guidance,
   not a decision to decline, so introducing it remains open and is simply
   outside this change.

## Confirmation

- **Mode:** enforced, with a `none` residual on the reachability half.
- **Signal:** `tools/run-pip-audit-gate.py` exits 2 on a malformed entry, an
  out-of-bounds package, a `fixed_in` the feed does not publish, a skipped
  dependency, a resolve below the manifest, and a retired entry. 39 scenarios in
  `tools/test-run-pip-audit-gate.py` — 85 assertions, which is the count the
  runner prints — assert the exit code, and the message wherever the message is
  what tells a contributor what to do,
  and run ahead of the live audit in the recipe. Three mutations were run and
  each reddened the cases it was predicted to: neutering the partition reddens
  the blocking cases, neutering the stale detector reddens all four retirement
  branches, and switching the version comparison to string ordering reddens the
  `2.9.0` vs `2.14.0` case — that last one would otherwise instruct a maintainer
  to delete a written risk acceptance.
- **Residual:** the reachability finding itself is not mechanically checked.
  Recorded as a visible `none` rather than omitted, because a reader would
  reasonably expect the evidence behind ten accepted advisories to be enforced,
  and it is not. This is the same shape of gap ADR-0102 records, reached by a
  deliberate decision rather than by omission: the mechanism was specified,
  reviewed, found to be a proxy for a property it could not observe, and
  removed.
- **Owner:** repository maintainers.
