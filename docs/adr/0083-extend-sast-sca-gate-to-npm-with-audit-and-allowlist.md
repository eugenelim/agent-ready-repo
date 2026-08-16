# ADR-0083: Extend the SAST/SCA gate to npm with `npm audit` + a reasoned allowlist

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-08-16
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** extends ADR-0017 (Bandit + pip-audit + Semgrep as the repo's SAST/SCA gate) to a second ecosystem; the implementing spec `docs/specs/npm-sca-gate/`

## Context

ADR-0017 adopted Bandit + pip-audit + Semgrep and named the result the repo's
"SAST/SCA gate". The SCA half is `pip-audit`, and it is thorough: every
third-party pin in `tools/requirements.txt`, every `packs/**/requirements.txt`,
both PEP 517 build-system tables, the SAST tooling's own requirements, and
`credbroker`'s optional `[crypto]` extra.

It audits no JavaScript, because there was none in the tree when ADR-0017 was
written. There is now:

- `web/` — the marketing site, approved by RFC-0061, first Node toolchain in the
  repo.
- `docs-site/` — the Starlight docs site.

Both commit a `package-lock.json`, and both ship their resolved trees into built
output. `spec/docs-site-design-refresh` (AC9) made this materially worse in a way
worth naming: it replaced mermaid's runtime CDN `<script>` with a bundled
`mermaid@11.16.1` dependency. That was the right call for the CDN-call boundary
it was solving, and it vendored mermaid's entire transitive tree into shipped
output. That spec recorded the consequence honestly as a deferral
(`docs-site-npm-sca-gap`) rather than pretending it was covered.

The gap was not theoretical. At the time this ADR was written, both lockfiles
carried two unremediated **high**-severity advisories (`js-yaml`
GHSA-5p4m-2wfm-xmqj, `nanoid` GHSA-2v37-7h3g-55p8) and `web/` additionally
carried a moderate `postcss` advisory. Nothing in the repo would have said so.
That is precisely the class of finding ADR-0017 § Context names as its reason
for existing: the org's Snyk scan reports it, and the maintainer cannot see that
scan's output.

## Decision

**Add `npm audit` as a fourth scanner on the existing `make sast` gate, invoked
through a thin stdlib wrapper (`tools/audit-npm.py`) that carries a reasoned
advisory allowlist.**

### Why a leg on `make sast` rather than a new workflow

`make sast` is chained into `make build-check`, which is what `build-check.yml`
runs — and `build-check.yml` is the **one** workflow inside
`tools/lint-ci-parity.py`'s `WORKFLOW_SCOPE`. A gate added there is locally
reproducible and drift-checked by construction.

The alternatives all forfeit that. A job in `ci-security.yml` or a new workflow
file lands outside parity scope, which is the exact defect
`spec/local-gate-ci-parity` was written to close: a CI step with no local
counterpart and nothing detecting the divergence. Putting npm SCA anywhere other
than the gate already named "SCA" would also leave a reader reconciling two
coverage stories by hand.

One consequence has to be wired deliberately: **both lockfiles are added to the
Makefile's `SAST_CONFIG`.** `build-check.yml` computes SAST relevance from
`SAST_DIRS` + `SAST_CONFIG` against the PR's changed files and sets
`SKIP_SAST=1` when nothing matches. Neither `docs-site/` nor `web/` is under
`SAST_DIRS`, so without this a dependency-bump PR — a diff whose only changed
file is a lockfile — would skip the one gate written to check it.

### Why `npm audit` rather than Dependabot or Snyk Open Source

| Option | Blocks a merge? | Cost | Verdict |
|---|---|---|---|
| **`npm audit`** | Yes — it is a gate | Zero: ships with npm, already on every runner and contributor machine | **Chosen** |
| Dependabot | No — it opens bump PRs | Free, but changes team PR volume and review workload | Deferred (`npm-dependabot-wiring`); complementary, not a substitute |
| Snyk Open Source | Yes | Needs an account and a token in CI | Rejected: ADR-0017 already rejected tool choices requiring org-scan access the maintainer does not have |

Dependabot and `npm audit` answer different questions — "should we bump?" versus
"may this merge?" — so choosing the gate first is not a rejection of Dependabot,
only an ordering. Adopting it remains open as a backlog item, deliberately left
to the repo owner because it changes how much review the team absorbs per week.

### Why a wrapper rather than two `npm audit` lines in the recipe

`npm audit` has **no per-advisory ignore**. Its only lever is `--audit-level`,
which is repo-wide and coarse: the escape hatch for a single unfixable
transitive advisory is to stop gating an entire severity band.

That matters here specifically because suppressions are the observed steady state
of this control in this repo, not a hypothesis. The sibling `pip-audit` leg runs
today with four live `--ignore-vuln` entries (Semgrep's hard-pinned `mcp` and
`click` transitive CVEs), each carrying a written diagnosis and an unblock
condition. A gate shipped without an escape hatch would wedge every merge the
first time a no-fix-available advisory lands — and the hatch would then be
designed under exactly the pressure that produces a bad one.

So `tools/npm-audit-allowlist.toml` ships **empty**, and every entry must carry
`id`, a non-blank `reason`, and a non-blank `unblocked_when`. A missing or blank
field is a tool error, not a silent pass: an allowlist that decays into an
undocumented mute list is worse than no allowlist.

### Why the verdict is read from the payload, not the exit code

`npm audit` exits non-zero for *both* "found advisories" and "could not reach the
registry". Reading the exit code alone would make a network outage, a proxy
returning an HTML error page, or a corporate MITM indistinguishable from a clean
tree — a gate that fails **open** exactly when the environment is degraded.

So a "clean" verdict is reachable only from a parsed payload carrying
`auditReportVersion`. Everything else — npm absent, unparseable output, an
`error` key, an unrecognised schema, or zero lockfiles discovered — exits 2, the
distinct tool-error code. `tools/test-audit-npm.py` pins those paths against
fixtures, because a live run against a healthy registry never reaches them.

### Threshold and scope

Blocking at **`moderate`** and above. The first draft of this decision said
`high`, on the reasoning that it matched Bandit's medium/medium tuning and that
tightening could come later. Implementation reversed it on evidence: remediating
`web/`'s moderate `postcss` advisory left both lockfiles clean at `moderate`, so
the bar could be raised for free. A threshold is cheapest to raise while you are
already above it; deferring guarantees the tightening lands on a day when
something is failing it. `low` and `info` stay ungated.

Lockfiles are **discovered** by walking the tree, not listed, so a third npm
project cannot be added without the gate noticing.

### Why a canary probe — reading the payload is not sufficient

The rule above ("clean requires `auditReportVersion`") is necessary and **not
sufficient**, which we measured rather than argued.

Pointed at a local stub that answers the bulk-advisory endpoint with HTTP 200
and an empty body, `npm audit` returns:

```json
{ "auditReportVersion": 2, "vulnerabilities": {},
  "metadata": { "dependencies": { "total": 573, "...": "..." } } }
```

No `error` key. A correct report version. A full and entirely plausible
dependency count — because **npm computes `metadata.dependencies` locally from
the lockfile and never receives it from the registry.** The payload is
byte-identical to a genuinely clean audit. No inspection of it can tell the two
apart, which also rules out the obvious cross-check (comparing the audited
dependency count against the lockfile's package count); that number is local
knowledge and stays correct while the advisory data is missing entirely.

The threat is mundane: an internal npm mirror — Artifactory, Nexus, Verdaccio —
whose advisory endpoint is unimplemented, misconfigured, or silently degraded.
ADR-0017 § Context establishes that this repo lives alongside an org-managed
scanning estate, so a non-default registry is a realistic configuration rather
than a hypothetical one.

So the gate audits a **canary** first: a throwaway lockfile pinning
`lodash@4.17.11`, whose critical prototype-pollution advisory
(GHSA-jf85-cpcp-j695) has been published for years. If the endpoint does not
report it, the endpoint is not reporting anything, and the run is a tool error
rather than a pass.

This is the same argument the `sast` recipe already makes for
`tools/test-semgrep-argv-boundary.py`: a scan that is silent when it works and
silent when it has been broken into a no-op cannot tell you which one happened,
so something known-positive has to be run through it.

## Consequences

**Positive:**
- The gate's name and its coverage now agree. Both dependency ecosystems in the
  tree are scanned by the same `make sast` invocation, locally and in CI.
- Three real advisories were found and fixed on arrival — all transitive patch
  bumps that left both `package.json` files untouched.
- The escape hatch exists before it is needed, so the first suppression is a
  reviewed diff with a written unblock condition rather than an emergency
  `--audit-level` downgrade.
- No new dependency: `npm` is already required to build either site, and the
  wrapper is pure stdlib, preserving ADR-0017's dev/CI-only-tooling posture.

**Negative:**
- `make sast` gains another network-bound leg. ADR-0017 already accepted this
  trade for Semgrep's registry fetches and pip-audit's index resolution;
  `SKIP_SAST=1` remains the documented offline path.
- The advisory database moves independently of the repo, so a previously green
  gate can redden with no diff. Identical to the `pip-audit` and Semgrep legs;
  the allowlist is the response.
- `npm` becomes a hard requirement of `make sast` on a machine that previously
  needed only Python. Guarded explicitly with an install hint rather than
  skipped silently — a skipped SCA leg that still prints green is the failure
  mode this whole gate exists to avoid.

**Neutral / to revisit:**
- **Tightening to `low`.** Not taken. `moderate` is the floor that maps most
  nearly onto Bandit's `medium`; going lower would gate advisory noise that the
  Python half of the same gate deliberately ignores.
- **The canary pin is a maintenance item.** If GHSA-jf85-cpcp-j695 is ever
  withdrawn, the probe goes silent and the gate wedges closed — loudly, with an
  error naming the fix (repin the canary). Failing closed on a withdrawn
  advisory is the correct direction for the error to point, but it is a real
  future interrupt and is recorded here so it is diagnosable at a glance.
- **The allowlist's `unblocked_when` is prose the gate never reads.** ADR-0017's
  `.snyk` policy carries a machine-checked `expires`; mirroring that here would
  stop a suppression rotting indefinitely. Deliberately not built while the
  allowlist is empty — there is nothing to expire yet.
- **Dependabot** (`npm-dependabot-wiring`) — complementary automation, left to
  the repo owner.
- **Machine enforcement of the `allowScripts` install-script invariant**
  (`npm-allowscripts-enforcement`). Both `AGENTS.md` files document it as prose
  and nothing checks it. Deliberately not built here: `web/`'s lockfile already
  carries `playwright/node_modules/fsevents@2.3.2` outside its `allowScripts`
  keys, so the gate would land CI red on arrival. That divergence needs a
  disposition before the check can exist. Note the distinction — SCA scans for
  *known CVEs*; `allowScripts` governs *arbitrary code execution at install
  time*. Neither substitutes for the other.
- **JavaScript SAST** (`sast-javascript-coverage`) remains open. SCA and SAST are
  different lenses; this ADR adds only the first for npm.
