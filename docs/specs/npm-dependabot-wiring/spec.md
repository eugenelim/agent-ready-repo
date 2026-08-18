# Spec: npm-dependabot-wiring

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — one new `.github/dependabot.yml`. No code, no gate, no
  interface. It changes what GitHub *opens*, not what merges.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. Two were checked. (1) New
dependency: none — Dependabot is a GitHub service, nothing is added to a manifest or a
lockfile. (2) Security boundary: the file grants no permission and touches no token;
the SCA gate that blocks merges is unchanged. Lean fill: Objective + Acceptance
Criteria + Boundaries + Assumptions. -->

## Objective

`tools/audit-npm.py` blocks a merge on a known npm advisory, but nothing opened the
bump PRs — remediation was hand-driven (`npm audit fix --package-lock-only`) and only
happened when someone went looking. ADR-0083 chose the gate first and recorded
Dependabot as **complementary, not a substitute**: the two answer different questions,
"may this merge?" versus "should we bump?".

It was deferred to the repo owner, explicitly on volume grounds rather than technical
ones — "it changes how much review the team absorbs per week". The owner has now asked
for it, so the work is to wire it at the lowest volume that still delivers the bumps.

## Acceptance Criteria

- [x] **AC1 — both npm projects are covered.** `.github/dependabot.yml` is schema
  version 2 and declares one `npm` ecosystem entry per project directory:
  `/docs-site` and `/web`. Both ship committed lockfiles, which is what makes a
  lockfile-only bump PR meaningful.

- [x] **AC2 — the volume the owner was asked about is bounded.** The settings are
  chosen against the one stated objection, not left at defaults:

  | Setting | Value | Why |
  | --- | --- | --- |
  | `schedule.interval` | `weekly` | not daily |
  | `groups.*.update-types` | `minor`, `patch` | a quiet week is **one** PR per project, not nine |
  | majors | ungrouped | they are the ones that need reading individually |
  | `open-pull-requests-limit` | `5` | a burst cannot flood the queue |

- [x] **AC3 — nothing about the merge gate changes.** `tools/audit-npm.py` still runs
  as a leg of `make sast` and still blocks on a known advisory. This file adds no
  permission, no token, and no workflow. ADR-0083's choice of `npm audit` as the gate
  stands; this is the complement it named.

- [x] **AC4 — the config is valid, and verified as such.** It parses as YAML, declares
  `version: 2`, and each entry resolves to a directory that actually contains a
  `package.json`. Verified by parsing, since nothing in CI validates
  `.github/dependabot.yml` — `actionlint` and `zizmor` lint *workflows*, and this is
  not one.

- [x] **AC5 — the deferral's dangling references are recorded, not silently created.**
  Closing this slug leaves four prose references pointing at it from **frozen**
  documents: `docs/adr/0083-…md:72` and `:201`, and
  `docs/specs/npm-sca-gate/spec.md:203` and `:263`.

  They are deliberately **not** corrected here. CONVENTIONS freezes an ADR body, the
  shipped `new-adr` template moves only the Status line, and the `## Errata` convention
  is RFC-scoped — there is no licensed shape for "this accepted deferral has since been
  discharged". Inventing one in this PR would be a governance change smuggled into a
  config file.

  `lint-spec-status` is clean: these are prose mentions, not `(deferred: <slug>)`
  anchors, so no invariant depends on the slug surviving. The instance is appended to
  the open `adr-errata-convention` entry instead, with the observation that its shape
  differs from ADR-0071's — that one names a **deleted file** (wrong on its face),
  these name a **resolved deferral** (true when written, still true as history). Which
  of those actually needs annotating is the decision that entry owes.

## Boundaries

**Never do**

- Add a `pip` ecosystem entry. `sast-requirements-not-audited` carries an explicit
  audit-vs-Dependabot decision for the Python side ("Decide which, then do one —
  doing both duplicates the noise"). Adding pip here pre-empts it.
- Add a `github-actions` ecosystem entry. Every action in this repo is already
  SHA-pinned, and enabling it is its own volume decision nobody has taken.
- Weaken, replace, or reroute `tools/audit-npm.py`. Dependabot does not gate.
- Edit ADR-0083 or `docs/specs/npm-sca-gate/spec.md`. Both are frozen (AC5).

## Assumptions

1. **Dependabot is enabled for the repository.** The config is inert until it is; if
   the service is off, this file is a no-op rather than an error, so nothing here
   fails closed on the owner's account settings.
2. **Grouped minor/patch bumps are the right default.** If a grouped PR ever proves
   hard to review, splitting a group is a one-line change to this file — the cheap
   direction to be wrong in, which is why it is the starting point.
3. **Both lockfiles stay committed.** `docs-site/package-lock.json` and
   `web/package-lock.json` are already in `SAST_CONFIG`, so their removal would
   surface elsewhere first.
