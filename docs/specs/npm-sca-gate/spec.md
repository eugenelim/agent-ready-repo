# Spec: npm-sca-gate

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017, ADR-0083

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**The repo's SCA gate covers one of its two dependency ecosystems, and nothing
says so.**

`make sast` is ADR-0017's SAST/SCA gate. It is chained into `make build-check`
and therefore into `build-check.yml`, the required CI check. Its SCA leg is
`pip-audit`, run over `tools/requirements.txt`, every `packs/**/requirements.txt`,
the two PEP 517 build-system tables, `tools/requirements-sast.txt`, and
`credbroker`'s `[crypto]` extra. Every Python dependency in the tree is audited.

The repo also has two npm projects — `docs-site/` and `web/` — each with a
committed `package-lock.json`. **Neither is scanned by anything.** No
`npm audit` runs in any workflow or `make` target; `.github/dependabot.yml` does
not exist. The gate's name says SCA; its coverage is Python-only, and ADR-0017
never states the limit because npm was not in the tree when it was written.

Two facts make this live rather than theoretical:

1. **The unscanned surface is shipped code, and it is net-new.** `docs-site`
   previously loaded mermaid from a CDN. `spec/docs-site-design-refresh` (AC9)
   bundled `mermaid@11.16.1` instead, which vendors its entire transitive tree
   into built output. That spec recorded the resulting gap as a deferral —
   `workspace.toml [backlog].open` slug `docs-site-npm-sca-gap` — and
   `docs-site/AGENTS.md` carries a matching **Known gap** note. This spec
   discharges that deferral.

2. **Both lockfiles carry unremediated high-severity advisories today.**
   Observed at spec time via `npm audit`:

   | Project | Package | Installed | Severity | Advisory |
   |---|---|---|---|---|
   | both | `js-yaml` | 4.3.0 | high | [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj) — quadratic CPU in `!!omap` resolution |
   | both | `nanoid` | 3.3.16 | high | [GHSA-2v37-7h3g-55p8](https://github.com/advisories/GHSA-2v37-7h3g-55p8) — custom generators loop forever when `size` is 0 |
   | `web/` | `postcss` | 8.5.19 | moderate | attacker-controlled `sourceMappingURL` reads arbitrary `.map` files when `from` is unset |

   All three are **transitive**; all three have fixes available as patch bumps
   that leave both `package.json` files untouched.

   None is exploitable in this repo's usage, and that is checked rather than
   assumed: reading each lockfile's dependency edges, `js-yaml` is reached only
   through `astro` / `@astrojs/starlight` / `@astrojs/internal-helpers`,
   `nanoid` only through `postcss`, and `postcss` only through `vite` and
   `@expressive-code/core`. Every one of them is **build-time toolchain, not a
   shipped page bundle** — notably *not* pulled in by the bundled `mermaid`.
   Combined with the absence of attacker-controlled YAML input, any `nanoid`
   custom generator, or PostCSS invocation on untrusted CSS, this is lockfile
   hygiene rather than an incident, and needs no changelog `Security` entry.

   It is nonetheless exactly the class of finding the org's Snyk Open Source
   scan reports, which ADR-0017 § Context names as the reason the gate exists at
   all.

The deeper defect is (1), not (2). Bumping three transitive pins fixes today's
findings and nothing else; the next advisory lands with the same silence. The
gate is the deliverable.

## Boundaries

### Always do

- Extend the **existing** ADR-0017 gate (`make sast`), rather than adding a new
  workflow or a new job. `make sast` is already chained into `build-check` and
  `build-check.yml`, and `build-check.yml` is the one workflow inside
  `tools/lint-ci-parity.py`'s scope — so a leg added there is locally
  reproducible and drift-checked by construction. `ci-security.yml` is
  explicitly out of parity scope and is the wrong home for that reason.
- Cover **both** npm projects. `docs-site-npm-sca-gap` names `docs-site` because
  that is where the deferral was recorded, but the gap is repo-wide and `web/`
  carries the same advisories.
- Discover lockfiles from the tree, not from a hardcoded list, so a third npm
  project cannot be added without the gate noticing.
- Carry an **allowlist** with a documented reason and unblock condition per
  entry, mirroring the `--ignore-vuln` suppressions the `pip-audit` leg already
  runs with. Ship it empty.
- Prove the gate before trusting it: a self-test asserting the parser and the
  allowlist logic runs immediately before the live audit inside `make sast`,
  the same pattern `tools/test-audit-requirements.py` already establishes.
- Keep the tool pure-stdlib Python (root `AGENTS.md` § *New tool scripts:
  Python, not bash*).

### Never do

- Never run `npm audit fix` — or any mutation — from the gate. A gate reports;
  remediation lands in a PR a human reviews.
- Never install `node_modules` to audit. `--package-lock-only` reads the
  committed lockfile, which is the artifact under audit.
- Never let an absent `npm` silently pass the gate.
- Never widen the threshold below `high` to make a finding go away; use the
  allowlist, which forces a written reason.

## Acceptance Criteria

- [x] **AC1 (gate exists and is discovered, not listed).** `tools/audit-npm.py`
      walks the repo for `package-lock.json` files, excluding `node_modules/`,
      and audits each at `--audit-level=moderate` with `--package-lock-only`. It
      exits 0 when every project is clean, 1 on any non-allowlisted advisory at
      or above `high`, and 2 on a tool error. The three exit codes are
      distinguishable, matching `tools/test-all.py`'s precedent that "failed"
      and "never ran" are different facts.
- [x] **AC1a (the gate fails closed).** Exit 0 is reachable **only** from an
      `npm audit` run that produced a parseable report with an
      `auditReportVersion`. Every other outcome — npm absent, non-zero exit with
      no parseable JSON, a payload carrying an `error` key (the shape
      `npm audit` returns when it cannot reach the registry), unrecognised
      report schema, or no lockfile discovered at all — is exit 2 with the cause
      named on stderr. This is the AC the rest of the gate rests on: a
      registry outage or a proxy returning HTML must never be indistinguishable
      from "no vulnerabilities", and `npm audit` uses a non-zero exit for both
      "found advisories" and "could not run", so the distinction has to be made
      from the payload rather than the exit code.
- [x] **AC1b (a positive control, because the payload cannot prove coverage).**
      Before auditing any project lockfile, the gate audits a **canary** — a
      throwaway lockfile pinning a package version with a permanent published
      advisory (`lodash@4.17.11`, GHSA-jf85-cpcp-j695). If that audit reports no
      advisory for the canary, the run is a tool error (exit 2), not a pass.

      This exists because AC1a is necessary but **not sufficient**, which was
      measured rather than assumed. Against a local stub returning HTTP 200 with
      an empty advisory body, `npm audit` emits `auditReportVersion: 2`,
      `vulnerabilities: {}`, **no** `error` key, and a complete, plausible
      `metadata.dependencies` block (573 deps) — the last because npm computes
      dependency counts locally from the lockfile and never receives them from
      the registry. The payload is byte-identical to a genuinely clean audit, so
      no amount of payload inspection can separate them. Only a known-positive
      can. The relevant threat is mundane rather than exotic: an internal npm
      mirror whose advisory endpoint is unimplemented or misconfigured.
- [x] **AC2 (chained into the existing gate, both directions).** `make sast`
      runs `tools/test-audit-npm.py` then `tools/audit-npm.py`, positioned with
      the other SCA legs. Both npm lockfiles are added to the `SAST_CONFIG`
      variable, so `build-check.yml`'s SAST-relevance predicate treats a
      lockfile-only diff as SAST-relevant — without this, a PR that bumps only a
      lockfile sets `SKIP_SAST=1` and the gate never runs on the exact diff it
      exists to catch.
- [x] **AC3 (allowlist).** An advisory may be suppressed only by its GHSA/CVE ID
      in a committed allowlist, and only with a `reason` and an `unblocked_when`
      string. An entry missing either field is a tool error (exit 2), not a
      silent pass. Every applied suppression is printed. The allowlist ships
      **empty** — it is the escape hatch, not a starting position.
- [x] **AC4 (self-test proves the gate, not just the plumbing).**
      `tools/test-audit-npm.py` asserts, against synthetic `npm audit` JSON
      fixtures: a clean report passes; a `high` finding fails; a `critical`
      finding fails; a `moderate` finding does not fail; an allowlisted `high`
      passes and is reported; an allowlist entry missing `reason` or
      `unblocked_when` is a tool error; **a payload carrying an `error` key is a
      tool error, not a pass**; **a payload with no `auditReportVersion` is a
      tool error, not a pass**; **a package at blocking severity carrying no
      `via` advisories is a tool error, not a pass** (while the same shape at a
      non-blocking severity still passes, so the guard does not over-fire); a
      lockfile under `node_modules/` is not discovered; and a symlinked
      *directory* is pruned for loop safety while a symlinked *lockfile* is
      still discovered. The emphasised cases are AC1a's fail-closed paths — a
      live run against a healthy registry never reaches them, so a fixture is
      the only thing that can prove them. It is registered in
      `tools/test-all.py`'s `TESTS`, so it runs in the umbrella suite rather
      than only when someone remembers.

      It additionally covers AC1b: the canary reads as live when the endpoint
      answers and **not** live against the silent-mirror payload — and asserts
      that the same silent-mirror payload *passes* `evaluate()`, which is the
      whole justification for the canary existing, written as an executable
      claim rather than a comment.
- [x] **AC5 (today's findings remediated).** `docs-site/package-lock.json` and
      `web/package-lock.json` are updated so `npm audit --audit-level=moderate`
      reports zero vulnerabilities in each. Both `package.json` files are
      **unchanged** — the fixes are transitive. `web/`'s moderate `postcss`
      advisory is fixed in the same pass because the same `npm audit fix`
      resolves it; it is not left behind to make a later `--audit-level=moderate`
      tightening harder. The set of `"hasInstallScript": true` entries is
      **byte-identical to the pre-change baseline** in both lockfiles — stated
      against the baseline, not against `allowScripts`, because
      `web/package-lock.json` already carries a third such entry
      (`playwright/node_modules/fsevents@2.3.2`) that sits outside
      `web/package.json`'s `allowScripts` keys. That entry is **pre-existing and
      untouched**; an AC phrased as "within `allowScripts`" would be false on
      arrival and unverifiable. Closing that pre-existing divergence is
      `npm-allowscripts-enforcement` (deferred, see § Assumptions).
- [x] **AC6 (documentation drift closed).** `docs-site/AGENTS.md`'s **Known gap**
      paragraph — which names `docs-site-npm-sca-gap` and states no SCA scanner
      is wired repo-wide — is replaced by a statement of what now runs.
      `web/AGENTS.md` gains the equivalent supply-chain paragraph it currently
      lacks entirely. Both files stay ≤ 150 lines (CI-enforced subdirectory cap).
- [x] **AC7 (the decision is recorded).** ADR-0083 records extending ADR-0017's
      SAST/SCA gate to the npm ecosystem: why `npm audit` over Dependabot or
      Snyk Open Source, why an allowlist wrapper over two bare Makefile lines,
      and the accepted consequences (network dependency at gate time; no
      per-advisory ignore in `npm audit` itself, hence the wrapper). ADR-0017
      gains a `Related:` pointer so a reader arriving at the Python-only gate
      finds the npm extension.
- [x] **AC8 (backlog reconciled).** `docs-site-npm-sca-gap` is removed from
      `workspace.toml [backlog].open`. The two deferrals this spec declines are
      recorded there with cold-start-sufficient comments:
      `npm-dependabot-wiring` and `npm-allowscripts-enforcement`.
- [x] **AC9 (gates green).** `make ci` passes locally, and `build-check.yml`
      passes on the PR with the SAST leg actually running (not `SKIP_SAST=1`).

      **Stated residual — this PR does not exercise AC2's predicate.** The diff
      touches `tools/`, which is already in `SAST_DIRS`, so `build-check.yml`
      routes to `skip_sast=false` for this PR whether or not the `SAST_CONFIG`
      addition landed. A green SAST leg here therefore proves the gate runs; it
      does **not** prove the lockfile predicate works. The first real test of
      that predicate is the next PR whose diff is lockfile-only. What *is*
      verifiable now is the assertion in AC2 — `make -s print-sast-config` names
      both lockfiles — and that is the check AC2 is written against. Recording
      the residual rather than letting a green check imply more than it proves
      is the same discipline `tools/lint-ci-parity.py` applies to its own
      `roster-residual-hidden-gate-in-known-step`.

## Testing Strategy

| AC | Mode | Mechanism |
|---|---|---|
| AC1, AC1a, AC3, AC4 | TDD | `tools/test-audit-npm.py` against synthetic `npm audit` JSON fixtures — no network, no npm, deterministic |
| AC1b | Manual QA (adversarial) | Stand up a local stub answering the bulk-advisory endpoint with HTTP 200 and an empty body, point `npm_config_registry` at it, and run the gate: it must exit **2** naming the silent endpoint, not 0. Re-run against the real registry: exit 0 with the canary confirmed. Both observed and recorded in the PR — the fixture half is covered by the row above |
| AC2 | Goal-based | `make sast` reaches the leg; `make -s print-sast-config` names both lockfiles |
| AC5 | Goal-based + manual QA | `npm audit --audit-level=moderate` in each project reports 0; `git diff` shows both `package.json` untouched; install-script audit re-run over both lockfiles |
| AC6, AC7, AC8 | Goal-based | `tools/lint-agents-md.py` line caps; `lint-spec-status.py` deferral-anchor resolution |
| AC9 | Manual QA | `make ci` observed green locally; CI observed green on the PR |

The self-test is the load-bearing one. A gate whose only proof is "it exited 0
on a clean tree" cannot distinguish working from broken-into-a-no-op — the same
reasoning the `sast` recipe already applies to `tools/test-semgrep-argv-boundary.py`
and `tools/test-audit-requirements.py`.

## Assumptions

- **The human approval gates are pre-authorised.** The user directed this work
  to run autonomously through PR and merge. That standing authorisation is taken
  as the `spec-approved` and `plan-approved` signals; it is recorded here rather
  than left implicit.
- **Specialist reviewer subagents are unavailable in this session** (operator
  configuration). The `adversarial-reviewer` and `security-reviewer` passes run
  as inline self-review against the `security-checklists` `supply-chain` and
  `config-misconfig` modules, and are recorded as **named skips** — not silent
  ones — in the PR.
- `npm` is present on GitHub's `ubuntu-latest` runners (Node is preinstalled) and
  on contributor machines that already build either site. The gate fails loudly
  rather than skipping when it is absent, so this assumption is checked at run
  time rather than trusted.
- **Auditing at `moderate`.** This spec originally set the threshold at `high`
  to match the existing gate's tuning (Bandit runs `--severity-level medium
  --confidence-level medium`) and deferred any tightening. That was reversed
  during implementation, on evidence: fixing `web/`'s moderate `postcss`
  advisory left **both lockfiles clean at `moderate`**, so raising the bar cost
  nothing. The cheapest moment to raise a bar is while you are already above it
  — deferring means tightening on a day when there *is* a moderate finding,
  which turns a one-word diff into an argument. `low` and `info` remain
  ungated; `moderate` is also the level Bandit's `medium` most nearly
  corresponds to, so the gate is now *more* consistent with ADR-0017's tuning,
  not less.
- **Deferred (recorded in `[backlog].open`; AC8 verifies presence at ship
  time):** Dependabot wiring for automated bump PRs — deferral slug
  `npm-dependabot-wiring`. Machine enforcement of the `allowScripts`
  install-script invariant that both `AGENTS.md` files document as prose —
  deferral slug `npm-allowscripts-enforcement`.

## Out of scope

- **Dependabot.** Wiring it changes the team's PR volume and review workload —
  a repo-owner decision, not one this loop should impose. It is also a different
  control: Dependabot proposes bumps, it does not block a merge.
- **`packs/converters/**/package.json`.** Those two skills declare npm
  dependencies but commit no lockfile, so `npm audit` has nothing to read. Their
  supply-chain integrity is a distinct concern already owned by
  `[backlog].open` slug `pack-evals-npm-lockfile-integrity`.
- **JavaScript SAST.** Giving shipped JS dataflow/pattern coverage is a separate
  control with its own triage cost, already owned by `[backlog].open` slug
  `sast-javascript-coverage`. SCA (known-CVE dependency scanning) and SAST
  (source pattern analysis) are different lenses; this spec adds only the first.
- **`ci-security.yml`.** Left untouched; see § Boundaries for why `make sast` is
  the correct home.
