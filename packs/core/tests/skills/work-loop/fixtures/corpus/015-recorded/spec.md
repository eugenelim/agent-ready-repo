# Spec: agentbundle-wheel-release

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0003](../../rfc/0003-spec-and-cli.md) §Distribution
  + §F-cli-dist (canonical proposal). Amends RFC-0003 §F-cli-dist
  (path #2 Shipped, paths #1 and #3 Deferred with one-line reasons).
  Builds on [`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md)
  (declares the `agentbundle` CLI artifact this spec publishes) and
  [`docs/specs/skill-secrets/spec.md`](../skill-secrets/spec.md) §AC3
  + §AC4c (AC3 defines `load_credentials`'s signature; AC4c pins
  reachability from an installed wheel via the same `python -c "from
  agentbundle.credentials import load_credentials"` smoke this spec
  runs in CI). Precedent: PR #124 (merged 2026-05-26) made the
  runtime-dep visible across all four install routes; this spec
  closes the residual friction for routes 1-3 by publishing
  `agentbundle` to a registry.

> **Spec contract:** this document defines what "done" means. The
> implementing PR must match this spec, or update it. Verification
> must be derivable from it.

## Objective

An adopter who runs `pip install agentbundle` from a clean Python 3.11+
interpreter — on the public internet against PyPI, or behind a corporate
network against an Artifactory-mirrored repository — gets the same
runtime library that `pip install -e packages/agentbundle/` produces
from a clone today. After install, `from agentbundle.credentials import
load_credentials` resolves, the `agentbundle` console script is on
PATH, and every credentialed skill (`jira`, `figma`,
`confluence-publisher`, `confluence-crawler`, `jira-align`, plus the
worked example) runs without a `ModuleNotFoundError`.

Done means **RFC-0003 §Distribution path #2 (PyPI variant) is live**:
a tag push of `agentbundle-v<X.Y.Z>` against `main` builds a wheel, runs
an in-CI smoke check, and uploads to PyPI via Trusted Publisher OIDC —
no long-lived API token in GitHub secrets, no manual `twine upload`
from a developer machine. The corporate Artifactory variant of path
#2 ships as the same workflow with a second publish job that activates
when the deploying org configures an `ARTIFACTORY_TOKEN` secret; the
PyPI leg is shippable end-to-end on its own, the Artifactory leg
unblocks corp adopters once their out-of-band token issuance completes.
Paths #1 (zipapp via GitHub Releases) and #3 (Homebrew formula) stay
Deferred — separate specs if and when they earn their slot.

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires human
sign-off before proceeding; *Never do* is a hard rule, even under time
pressure.

### Always do

- Use **Trusted Publisher OIDC** for the PyPI publish job — no API
  token in GitHub secrets, no `password:` field in the publish action.
- **Assert pyproject version matches the pushed tag's `X.Y.Z`** before
  any publish step runs. Mismatch must fail the workflow with a clear
  error annotation, not silently publish the pyproject version against
  a different tag.
- **Run the in-CI smoke check** (`python -m build` → install the built
  wheel into a fresh venv → `python -c "from agentbundle.credentials
  import load_credentials"` exits 0) **before** any publish job runs.
  The smoke check is the gate, not a follow-up.
- **One wheel artifact, two upload targets.** Both publish jobs upload
  the same `dist/agentbundle-*.whl` and `dist/agentbundle-*.tar.gz`
  that the build job produced. No per-target rebuild.
- **Keep the wheel pure-Python** — `agentbundle` has no compiled
  extensions today, and the install-cheaply property is what makes
  this distribution model work.
- **Sequence README route-3 update after first successful PyPI
  publish.** The route-3 README claim "`pip install agentbundle`" must
  be true at the moment it lands; the claim cannot precede the publish.
- **Package-local README is a stub, not duplicate prose.**
  `packages/agentbundle/README.md` (created per T1 to satisfy
  setuptools's `readme` field) contains a short paragraph naming the
  runtime library + a link to the top-level repo README — never a
  duplicate of the top-level prose.

### Ask first

- Pushing any tag whose `X.Y.Z` would set `X >= 1` (i.e., `agentbundle-v1.0.0`
  or higher). The pre-1.0 stability contract changes at 1.0; refuse to
  push without explicit human sign-off recorded in the PR body.
- Renaming the package on PyPI after first publish. PyPI deletions and
  renames are sticky; surface to a human before attempting.
- Switching the build backend away from setuptools (to hatch, flit,
  poetry, etc.).
- Changing the workflow's tag-pattern shape (currently `agentbundle-v*`)
  — affects every downstream tagging convention.

### Never do

- Ship a wheel that hasn't passed the in-CI smoke check. The gate runs
  on the *built artifact*, not on a re-install of the source tree.
- Hard-code a PyPI API token in the workflow file or in `secrets.*`.
  Trusted Publisher OIDC is the only allowed PyPI auth path.
- **Add a runtime dependency to the `agentbundle` wheel** — `[project]
  dependencies` stays `[]`. (Structural Never do: keeps the install
  cheap and the constrained-network story intact. A runtime dep means
  an ADR + a new spec, not a metadata edit.)
- Publish from a branch other than `main`. Tags must point to commits
  on `main`.
- Skip the tag-vs-pyproject version assertion (Always do #2). Disabling
  the check is a hard refuse.
- Publish before the PyPI account + Pending Publisher are configured —
  the OIDC handshake fails closed, but the workflow shouldn't be tagged
  against a known-unconfigured publisher.
- **Add a second new workflow file, or modify
  `.github/workflows/build-check.yml`.** This spec's CI surface is
  exactly `.github/workflows/release-agentbundle.yml`. New CI surface
  beyond that file is out of scope; a sibling workflow earns its slot
  via a separate RFC + spec.

## Testing Strategy

This spec mixes two modes from the `work-loop` skill's catalogue:

- **Goal-based check** — for every behaviour that has a deterministic,
  one-liner verifier. `pyproject.toml` metadata correctness (`twine
  check dist/*` exits 0); workflow shape (`actionlint` or YAML lint);
  tag-vs-version assertion (run against a deliberately-mismatched tag
  in a draft branch — step fails; against a matching tag — step
  passes); wheel smoke (the in-CI install + import step itself).
  Goal-based covers the majority of this spec because the work is
  configuration and YAML — there's no logic with a compressible
  invariant that TDD would help with.
- **Visual / manual QA** — for the end-to-end first publish. The OIDC
  handshake between GitHub Actions and PyPI is not unit-testable from
  this repo; the verification is a recorded gesture (push the tag,
  watch the workflow, install from PyPI into a clean venv). One manual
  pass per registry (PyPI; Artifactory when the corp token lands).

TDD doesn't earn its keep here — no behavioural logic with a
compressible invariant. The closest thing to logic is the tag/version
assertion, and that's a 3-line shell or Python check whose contract is
already in the AC and is more usefully verified by goal-based testing
against a real workflow run than by an isolated unit test.

## Acceptance Criteria

**Metadata + build.**

- [x] AC1. `packages/agentbundle/pyproject.toml` declares `authors`,
  `license = { text = "Apache-2.0 OR MIT" }`, `readme` (dynamic or
  file, pointing at content that renders on PyPI), `urls` covering
  `Homepage`, `Source`, and `Documentation`, and `classifiers` covering
  development status, Python 3.11+, OS-independent, and the dual
  license.
- [x] AC2. `cd packages/agentbundle && python -m build` produces
  `dist/agentbundle-<version>-py3-none-any.whl` and
  `dist/agentbundle-<version>.tar.gz`.
- [x] AC3. `twine check dist/*` exits 0 with zero warnings.
  **Empirical baseline (2026-05-26, pre-T1):** `twine check` exits 0
  but emits exactly two warnings — `long_description missing` and
  `long_description_content_type missing`. Both close when T1 adds the
  `readme` field (setuptools derives both `long_description` and its
  content type from the `readme` source). Verifier:
  `twine check dist/* 2>&1 | grep -c WARNING` reports `0`.

**Workflow shape.**

- [x] AC4. `.github/workflows/release-agentbundle.yml` exists with
  three jobs: `build-and-smoke`, `publish-pypi`, `publish-artifactory`.
- [x] AC5. `build-and-smoke` runs on (a) `push: tags: ['agentbundle-v*']`
  and (b) `pull_request` touching `packages/agentbundle/**` or the
  workflow file itself.
- [x] AC6. `build-and-smoke` builds the wheel + sdist, runs `twine
  check dist/*`, installs the built wheel into a fresh venv, and runs
  an import smoke against the CLI entrypoint (`python -c "from
  agentbundle.cli import main"`) plus `agentbundle --help` on PATH.
  Any step failing fails the job. *(Originally `from
  agentbundle.credentials import load_credentials`; that module was
  removed in `agentbundle 0.2.0` — owned by another spec, see §Out of
  scope — and the workflow was updated to the CLI-entrypoint smoke.)*
- [x] AC7. `build-and-smoke` includes a tag/version-assertion step
  gated on `github.ref_type == 'tag'` that fails the workflow with a
  GitHub error annotation when the tag's `X.Y.Z` does not match the
  pyproject `version`. A second tag-gated step asserts the tag points
  to a commit reachable from `origin/main` (`git merge-base
  --is-ancestor`); both fail closed before any publish job runs, so
  the §Never do "tags must point to commits on main" boundary is
  enforced mechanically, not by maintainer discipline.
- [x] AC8. `publish-pypi` runs only on tag push, depends on
  `build-and-smoke`, uses `pypa/gh-action-pypi-publish@release/v1`
  with `permissions: id-token: write` and no `password:` field —
  Trusted Publisher OIDC, no secret.
- [x] AC9. `publish-artifactory` runs only on tag push (`if:
  github.ref_type == 'tag'`), depends on `build-and-smoke`, and uses a
  step-level guard that flips `configured=true` **only when all three
  Artifactory secrets are non-empty** (`ARTIFACTORY_URL`,
  `ARTIFACTORY_USER`, `ARTIFACTORY_TOKEN`); partial configuration
  emits a `::warning::` and refuses to publish (avoids sending
  credentials to a default endpoint). On PR events the job is not
  scheduled at all; on tag events without the full secret triple every
  step after the guard reports `Skipped` at step level, the job overall
  reports `Success`, and the workflow run is not marked Failed (PyPI
  leg unaffected by corp-side coordination).

**Cross-doc consistency.**

- [x] AC10. RFC-0003 §F-cli-dist Amendments record: path #2 PyPI
  variant live (link to this spec); path #2 Artifactory variant
  workflow scaffolded, untested against a real Artifactory deployment,
  awaiting first-firing verification per AC14 (activates per-fork when
  the corp configures the GH secrets); paths #1 (zipapp via GH Releases)
  and #3 (Homebrew) Deferred with one-line reasons each — #1 because
  the release-artifact pipeline isn't built; #3 because Homebrew doesn't
  satisfy the corporate-network constraint in RFC-0001 §Corporate-network
  discipline.
- [x] AC11. After first successful PyPI publish, README §Install
  route 3 replaces the current headline phrase ``once you've
  pip-installed `agentbundle` (see route 4)`` with a headline that
  names `pip install agentbundle` directly, and the trailing
  paragraph preserves the route's distinction from route 4 (remote
  `git+https://` catalogue source vs. local clone). Verifiable by
  `grep -F "once you've pip-installed" README.md` exiting 1 (legacy
  phrase removed) and `grep -F 'pip install agentbundle' README.md`
  exiting 0 (replacement present). **Verified-at-AC-creation
  (2026-05-26):** `README.md:53` reads ``**Reference CLI**
  ([RFC-0003](docs/rfc/0003-spec-and-cli.md)) — once you've
  pip-installed `agentbundle` (see route 4):``. If this anchor moves
  or its content changes between PR-A merge and PR-B's land, T7 must
  re-anchor before merging. This AC lands in a separate PR sequenced
  **after** the first successful publish.
- [x] AC12. `docs/specs/README.md` lists `agentbundle-wheel-release`
  under the active spec index.

**End-to-end (manual QA, one pass per registry).**

- [x] AC13. **PyPI first-publish gesture** (recorded 2026-06-07,
  `agentbundle-v0.2.0`). Pushed tag `agentbundle-v0.2.0` (matching
  pyproject `version`) on `main`. The workflow run showed
  `build-and-smoke` and `publish-pypi` succeeded (Artifactory job
  green-skipped — corp syncs from GitHub, secrets intentionally
  unset). From a clean venv on a different machine: `pip install
  agentbundle` resolved to the just-published version and `agentbundle
  --help` exited 0. **Smoke updated:** the original `python -c "from
  agentbundle.credentials import load_credentials"` no longer applies —
  `agentbundle 0.2.0` removed that module (owned by the
  credential-broker-contract spec; see §Out of scope), and the
  in-CI smoke (AC6) was already updated to `from agentbundle.cli
  import main`.
- [ ] AC14. (deferred: artifactory-first-publish-gesture) **Artifactory first-publish gesture (deferred, gated on
  out-of-band).** When the corp issues an Artifactory token and
  configures `ARTIFACTORY_URL`/`ARTIFACTORY_USER`/`ARTIFACTORY_TOKEN`
  GitHub secrets, the next tag push runs `publish-artifactory` to
  completion and the wheel becomes installable via `pip install
  agentbundle --index-url <art-url>`. Verification reuses AC13's
  smoke check shape against the Artifactory URL.

## Out of scope

- Homebrew formula (RFC-0003 path #3); zipapp via GitHub Releases
  (RFC-0003 path #1) — separate specs if/when they earn the slot.
- Changes to `agentbundle.credentials` exports or any per-skill code
  (owned by `docs/specs/skill-secrets/spec.md`).
- Restructuring the four-route README §Install section (PR #124 owns
  that shape; route 3 gets a content edit, not a structural one).
- The corp Artifactory infrastructure-side approval, token issuance,
  and secret rotation (out-of-band; the workflow ships ready to use
  whatever the corp configures).
- Auto-bumping `agentbundle`'s pyproject version. Manual edits in
  release PRs, asserted against the tag.
- Auto-detecting whether the pushed tag was created by an authorized
  user. GitHub branch/tag protection rules cover this orthogonally.

## Changelog

- 2026-05-31: Status reconciled to Shipped; ACs checked against the
  merged implementation (retroactive). Publish-dependent ACs deferred
  pending first release.
- 2026-05-26 (credential-broker-contract T15 cross-impact): the smoke
  gate at AC5/AC7 historically used `python -c "from agentbundle.credentials
  import load_credentials"` as the proof-of-installation. With
  credential-broker-contract T15 removing `agentbundle.credentials`
  from the wheel (0.2.0), the smoke check moves to a current export
  — `python -c "from agentbundle.cli import main"`. The CI workflow
  at `.github/workflows/release-agentbundle.yml` reflects the new
  smoke; any reviewer encountering the prior wording in this spec
  reads it as historical, not contract-binding.
- 2026-05-26: initial spec.
- 2026-05-26: AC3 sharpened with empirical pre-T1 baseline (2 twine
  warnings) + a `grep -c WARNING == 0` verifier. No contract change —
  the post-T1 state ("zero warnings") is unchanged; the baseline
  notation makes the verifier mechanical.
- 2026-05-26: pre-EXECUTE adversarial review pass — AC9 wording
  sharpened to match step-level-skip reality (job reports Success,
  skipped steps render as Skipped, run not Failed); AC10 "shipped
  dormant" → "scaffolded, untested against a real Artifactory
  deployment, awaiting AC14"; AC11 carries a verified-at-creation
  README.md:53 anchor so drift before T7 lands surfaces explicitly.
  No contract change to the underlying behaviour.
- 2026-05-26: post-implementation security-review pass — AC7 grows a
  branch-ancestry assertion (mechanically enforces §Never do "tags
  must point to commits on main"); AC9 widened so the step-level
  guard requires all three Artifactory secrets non-empty
  (`ARTIFACTORY_URL`/`USER`/`TOKEN`) — partial config emits
  `::warning::` and skips, closing a credential-misrouting trap where
  a token-only setup would have shipped to twine's default endpoint.
- 2026-06-07: PR-B (T7) lands — README route 3 names `pip install
  agentbundle` directly now that `agentbundle-v0.2.0` published to
  PyPI. AC11 + AC13 checked. First publish was `0.2.0`, not the
  plan's `0.1.0` — the version moved while PR-A → PR-B sat (the
  credential-broker-contract release bumped it and removed the
  `agentbundle.credentials` module). AC13's verification smoke updated
  from the removed `load_credentials` import to `agentbundle --help`;
  the credentials module's removal is owned by another spec (see §Out
  of scope), so this spec only corrects the cross-reference it checks,
  it does not re-own the rename. AC14 (Artifactory) stays deferred —
  corp syncs the wheel from GitHub/PyPI, secrets intentionally unset.
