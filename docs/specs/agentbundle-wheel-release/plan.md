# Plan: agentbundle-wheel-release

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the
> spec, this document is allowed to change as you learn. When it
> changes substantially (a different approach, not just a re-ordering),
> note why in the changelog at the bottom.

## Approach

Six small tasks land in **PR-A** (T1-T6): tighten `pyproject.toml`
metadata, add the release workflow with three jobs (build-and-smoke,
publish-pypi gated by Trusted Publisher OIDC, publish-artifactory
auto-skipped when its secret is absent), and amend RFC-0003 §F-cli-dist
to record what shipped. PR-A is shippable end-to-end against PyPI
without any corp coordination — Artifactory ships dormant, activates
when the secret lands.

Between PR-A and PR-B sits one **out-of-band step**: configure the
PyPI Pending Publisher (~10 min: PyPI account + 2FA + add pending
publisher naming the repo, workflow file, and environment). Then push
tag `agentbundle-v0.1.0`. The first publish gesture verifies AC13
end-to-end on a real registry.

**PR-B** (T7) is the README route-3 update — lands only after PyPI
publish succeeded, so the README claim "`pip install agentbundle`" is
true the moment it lands. This is the only ordering constraint the
plan enforces by sequencing rather than by code.

The riskiest part is the OIDC handshake between GitHub Actions and
PyPI: four configuration values (project name, repo owner/name,
workflow filename, environment) must match exactly on both sides or
the publish fails closed. The first manual gesture is where this
surfaces; the spec's tag/version assertion is what catches it before
the OIDC step runs (so the failure mode is "asserted-version mismatch"
or "OIDC denied", never "wrong version published").

## Constraints

- [RFC-0003 §Distribution + §F-cli-dist](../../rfc/0003-spec-and-cli.md)
  — canonical proposal; this plan amends §F-cli-dist with what shipped.
- [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  §Corporate-network discipline — the constraint that motivates the
  Artifactory leg coexisting with the PyPI leg.
- [PR #124](../../../README.md#install) — predecessor: made the
  runtime-dep visible across all four routes. This plan does **not**
  restructure the four-route section; only route 3's headline + tail
  get a content edit, post-publish, in PR-B.
- The repo already pins Python 3.11 in `.github/workflows/build-check.yml`
  (line 25) — match.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`
subsections). Cross-cutting tests:

**Integration tests:**

- *Workflow-on-PR.* PR-A's own CI run on this branch must execute
  `release-agentbundle.yml`'s `build-and-smoke` job against the
  pyproject metadata changes — this is the integration test that
  proves T1's metadata + T2's workflow + T3's version-assertion +
  T6's wheel-smoke step compose correctly before any tag is pushed.
- *Skipped-Artifactory job.* PR-A's CI must show `publish-artifactory`
  as Skipped (not Failed) when no `ARTIFACTORY_TOKEN` secret is set —
  the boundary between PyPI-shippable-alone and Artifactory-gated.

**Manual verification:**

- *PyPI first publish* (AC13) — recorded gesture in PR-A's body when
  merged and tagged. Single-pass: push tag → workflow green → fresh
  venv on another machine → `pip install agentbundle` resolves →
  smoke + a credentialed-skill `--help` exit 0.
- *Artifactory first publish* (AC14) — recorded only when the corp
  token lands. Out-of-band against PR-A's ship.

**Baseline empirically verified (2026-05-26, pre-spec-commit):**

- `cd packages/agentbundle && python -m build` succeeds against the
  current pyproject; produces `agentbundle-0.1.0-py3-none-any.whl` +
  `agentbundle-0.1.0.tar.gz`. *Validates T1 scope: setuptools backend
  works as-is, pure-Python wheel shape confirmed, no migration needed.*
- `twine check dist/*` exits 0 with exactly 2 warnings
  (`long_description missing`, `long_description_content_type
  missing`). *Validates T1's metadata-tightening scope is exactly what
  AC3 promises to close.*
- Fresh `venv` + `pip install dist/agentbundle-0.1.0-py3-none-any.whl`
  + `python -c "from agentbundle.credentials import load_credentials"`
  exits 0; `agentbundle --help` works. *Validates AC6's smoke step
  shape against the current source, before any spec-driven changes.*
- `Requires-Dist: (none)` in the built wheel's METADATA. *Validates
  §Boundaries §Never do #3 ("`[project] dependencies` stays `[]`") as
  the current state, not aspiration.*
- PyPI `agentbundle` name still unclaimed (`https://pypi.org/simple/agentbundle/` → 404).
  Trusted Publisher action repo + PyPI Pending Publisher docs both
  reachable (200). *Validates Rollout Phase B's preconditions.*

## Tasks

### T1: pyproject metadata renders cleanly on PyPI

**Depends on:** none

**Tests:**

- AC1 — `pyproject.toml` declares `authors`, `license`, `readme`,
  `urls`, `classifiers`.
- AC2 — `cd packages/agentbundle && python -m build` produces both
  `.whl` and `.tar.gz`. Empirically confirmed pre-T1 (2026-05-26):
  filename today is `agentbundle-0.1.0-py3-none-any.whl` and
  `agentbundle-0.1.0.tar.gz`; the `py3-none-any` shape (pure-Python,
  any-platform) is what AC2's filename pattern asserts.
- AC3 — `twine check dist/* 2>&1 | grep -c WARNING` reports `0`.
  Pre-T1 baseline is `2` (the two warnings named in AC3); the
  `readme` field added in T1 closes both.
- Goal-based: `python -c "import tomllib; m = tomllib.load(open(
  'packages/agentbundle/pyproject.toml', 'rb'))['project']; assert
  set(m) >= {'authors', 'license', 'readme', 'urls', 'classifiers'}"`
  exits 0.

**Approach:**

- Edit `packages/agentbundle/pyproject.toml` to add:
  - `authors = [{ name = "eugenelim", email = "eugenelim@users.noreply.github.com" }]`
  - `license = { text = "Apache-2.0 OR MIT" }` (matches repo dual-license)
  - `readme = "README.md"` — pin the choice up front by creating a
    short `packages/agentbundle/README.md` (per §Boundaries §Always do:
    stub paragraph naming the runtime library and linking to the
    top-level repo README, never a duplicate of the top-level prose).
    Parent-relative `readme` paths via `tool.setuptools.dynamic` are
    flaky across setuptools versions and would leave the choice
    in-loop; pinning the stub here keeps the spec a contract, not a
    coin-flip.
  - `urls = { Homepage = "https://github.com/eugenelim/agent-ready-repo",
    Source = "https://github.com/eugenelim/agent-ready-repo",
    Documentation = "https://github.com/eugenelim/agent-ready-repo/blob/main/docs/guides/how-to/install-agentbundle-from-clone.md" }`
  - `classifiers = ["Development Status :: 4 - Beta", "License :: OSI
    Approved :: Apache Software License", "License :: OSI Approved ::
    MIT License", "Operating System :: OS Independent", "Programming
    Language :: Python :: 3.11", "Programming Language :: Python :: 3.12"]`
- Run `pip install build twine && python -m build` locally; verify
  `twine check dist/*` clean.

**Done when:** `twine check dist/*` exits 0 with no warnings; the
rendered `.whl`'s `METADATA` file (extract with `unzip -p
dist/agentbundle-*.whl agentbundle-*.dist-info/METADATA`) contains
every field above.

---

### T2: build-and-smoke workflow runs on every PR touching the package

**Depends on:** T1

**Tests:**

- AC4 — workflow file exists with the three jobs declared.
- AC5 — `build-and-smoke` triggers on the two configured events.
- AC6 — wheel build + `twine check` + clean-venv install + smoke
  import all run as steps, and any failing step fails the job.
- Goal-based: this PR's CI run shows `build-and-smoke` succeeded.

**Approach:**

- New file `.github/workflows/release-agentbundle.yml`. Header:
  ```yaml
  name: release-agentbundle
  on:
    push:
      tags: ['agentbundle-v*']
    pull_request:
      paths:
        - 'packages/agentbundle/**'
        - '.github/workflows/release-agentbundle.yml'
  ```
- One job, `build-and-smoke`: `runs-on: ubuntu-latest`,
  `timeout-minutes: 5`. Steps: `actions/checkout@v4`,
  `actions/setup-python@v5` with `python-version: "3.11"`, `pip
  install build twine`, `python -m build` (run with cwd =
  `packages/agentbundle/`), `twine check packages/agentbundle/dist/*`,
  fresh-venv install: `python -m venv /tmp/smokevenv && /tmp/smokevenv/bin/pip
  install packages/agentbundle/dist/*.whl && /tmp/smokevenv/bin/python
  -c "from agentbundle.credentials import load_credentials"`.
- Upload `packages/agentbundle/dist/` as a workflow artifact
  (`actions/upload-artifact@v4`) so T4 and T5 can download instead of
  rebuilding — single-source-of-bytes.

**Done when:** This PR's CI shows `release-agentbundle / build-and-smoke`
green; the workflow artifact `dist` appears on the run summary page.

---

### T3: tag/version assertion fails closed on mismatch and non-`X.Y.Z` suffixes

**Depends on:** T2

**Tests:**

- AC7 — step gated on `github.ref_type == 'tag'`, fails with
  `::error::` annotation on mismatch.
- Manual goal-based test in PR-A's body: push a draft tag
  `agentbundle-v9.9.9` to a throwaway branch with pyproject at
  `0.1.0`; confirm the workflow run fails the assertion step. Push
  matching tag, confirm pass. Delete throwaway tag and branch.

**Approach:**

- Add an assertion step inside `build-and-smoke`, before the build
  step, gated `if: github.ref_type == 'tag'`. Pure-Python (stdlib
  only, matches the package's no-runtime-deps norm), ~15 lines:
  ```yaml
  - name: Assert tag matches pyproject version
    if: github.ref_type == 'tag'
    run: |
      python3 - <<'PY'
      import os, re, sys, tomllib
      tag = os.environ["GITHUB_REF_NAME"]
      m = re.fullmatch(r"agentbundle-v(\d+\.\d+\.\d+)", tag)
      if not m:
          print(f"::error::tag {tag!r} does not match agentbundle-vX.Y.Z (pre-release / build-metadata suffixes refused by this spec)", file=sys.stderr)
          sys.exit(1)
      tag_ver = m.group(1)
      with open("packages/agentbundle/pyproject.toml", "rb") as f:
          pp_ver = tomllib.load(f)["project"]["version"]
      if tag_ver != pp_ver:
          print(f"::error::tag {tag} declares version {tag_ver} but pyproject.toml has {pp_ver}", file=sys.stderr)
          sys.exit(1)
      PY
  ```
- The regex `agentbundle-v\d+\.\d+\.\d+` is stricter than the
  trigger glob `agentbundle-v*` (which matches pre-release tags like
  `agentbundle-v0.1.0-rc1`); the trigger spends a runner-minute on
  those, the assertion fails them closed before any publish.

**Done when:** Manual mismatched-tag test fails the step with the
expected error message; matching-tag test passes. Document the test
run links in PR-A's body.

---

### T4: publish-pypi via Trusted Publisher OIDC

**Depends on:** T3

**Tests:**

- AC8 — job declared with `permissions: id-token: write`, uses
  `pypa/gh-action-pypi-publish@release/v1`, no `password:` field.
- Goal-based: `actionlint` (or `yamllint`) on the workflow file exits
  0; reviewer can read the OIDC config and verify the four
  configuration values (project, repo, workflow file, environment) the
  PyPI side will need to match.

**Approach:**

- Add job `publish-pypi` to `release-agentbundle.yml`:
  ```yaml
  publish-pypi:
    needs: [build-and-smoke]
    if: github.ref_type == 'tag'
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/
  ```
- The `environment: pypi` line is the configuration value the PyPI
  Pending Publisher form needs to match exactly (see §Risks #1 for
  the configuration-mismatch failure mode this guards against).
  Document the four values explicitly in PR-A's body so the human
  setting up Pending Publisher can copy them.

**Done when:** YAML lints clean; PR-A body lists the four
configuration values; reviewer confirms no `password:` field anywhere
in the workflow.

---

### T5: publish-artifactory soft-skipped via step-level guard when secret absent

**Depends on:** T3

**Tests:**

- AC9 — job is not scheduled on PR events (gated on
  `github.ref_type == 'tag'`); on tag events without the secret the
  job runs but every step after the guard is skipped at step level.
- Goal-based: PR-A's CI run shows `publish-artifactory` absent from
  the job graph entirely (PR event); tag-push tests against a draft
  branch (without the secret) show the job complete with only the
  guard step having run.

**Approach:**

- Use a **step-level guard** rather than a separate preflight job —
  fewer runners spun up, AC9's "skipped" semantics map cleanly to
  step-level skip:
  ```yaml
  publish-artifactory:
    needs: [build-and-smoke]
    if: github.ref_type == 'tag'
    runs-on: ubuntu-latest
    steps:
      - id: guard
        name: Check Artifactory secret presence
        run: |
          if [ -n "${{ secrets.ARTIFACTORY_TOKEN }}" ]; then
            echo "configured=true" >> "$GITHUB_OUTPUT"
          else
            echo "configured=false" >> "$GITHUB_OUTPUT"
            echo "::notice::ARTIFACTORY_TOKEN not set; skipping Artifactory publish."
          fi
      - if: steps.guard.outputs.configured == 'true'
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - if: steps.guard.outputs.configured == 'true'
        run: pip install twine
      - if: steps.guard.outputs.configured == 'true'
        run: |
          twine upload \
            --repository-url "${{ secrets.ARTIFACTORY_URL }}" \
            --username "${{ secrets.ARTIFACTORY_USER }}" \
            --password "${{ secrets.ARTIFACTORY_TOKEN }}" \
            dist/*
  ```
- GitHub Actions does not permit `secrets.X` in job-level `if:`
  expressions, which is why the guard is a step rather than a
  job-level condition. The step always runs (its cost is a single
  shell `if`); the upload steps are step-skipped when the secret is
  absent. On fork-PR runs `secrets.ARTIFACTORY_TOKEN` evaluates to
  empty regardless of repo configuration — same skip path.
- The three Artifactory secrets (`ARTIFACTORY_URL`, `ARTIFACTORY_USER`,
  `ARTIFACTORY_TOKEN`) are documented under Rollout below as the
  out-of-band setup the corp adopter does. The workflow refers to them
  by name; an adopter forking this repo for their own corp use can
  set them in their fork's secrets without touching the workflow.

**Done when:** PR-A's CI shows the job not scheduled on PR events;
manual tag-push test against a draft branch (Rollout Phase C, before
the real release tag) shows the job complete with the upload steps
skipped at step level; YAML lints clean.

---

### T6: RFC-0003 §F-cli-dist Amendment

**Depends on:** T1 (so scope of "what shipped" is settled)

**Tests:**

- AC10 — Amendments table records: path #2 PyPI variant live (link
  to this spec); path #2 Artifactory variant workflow shipped dormant
  (activates per-fork when the corp configures the GH secrets); paths
  #1 + #3 Deferred with one-line reasons.
- Goal-based: `python3 tools/lint-agents-md.py` and any other lint
  the repo runs on `docs/rfc/` pass.

**Approach:**

- Edit `docs/rfc/0003-spec-and-cli.md`:
  - Under §Follow-on artifacts §F-cli-dist (currently lines 445-449),
    add an inline status note that path #2 is now governed by this
    spec.
  - Under §Amendments (currently at the bottom, line 466+), add a
    dated entry:
    ```markdown
    - 2026-MM-DD: §F-cli-dist path-status update via
      `docs/specs/agentbundle-wheel-release/spec.md`. Path #2 (pip
      install) ships in two variants: PyPI (live; Trusted Publisher
      OIDC) and Artifactory (workflow exists, activates per-fork when
      the corp configures the GH secrets). Paths #1 (zipapp via GitHub
      Releases) and #3 (Homebrew) remain Deferred — #1 because the
      release-artifact pipeline isn't built; #3 because Homebrew
      doesn't satisfy the corporate-network constraint in
      RFC-0001 §Corporate-network discipline.
    ```

**Done when:** RFC-0003 Amendments section names the path-#2 ship
and the path-#1/#3 deferrals; `lint-agents-md.py` exits 0;
`make build-check` exits 0 (RFC files are hand-authored, not
projected — no drift expected).

---

### T7: README route 3 says `pip install agentbundle` directly

**Depends on:** T1, T2, T3, T4, T6, **and first successful PyPI publish (out-of-band)**

**Tests:**

- AC11 — README §Install route 3 headline names `pip install
  agentbundle` directly; the trailing paragraph preserves the route's
  distinction (remote `git+https://` catalogue source vs. local
  clone).
- Goal-based grep gates: `grep -F "once you've pip-installed"
  README.md` exits 1 (legacy phrase removed — distinct enough to
  current route 3 that this is the right anchor); `grep -F 'pip
  install agentbundle' README.md` exits 0 (replacement present);
  the four-route block intact: `grep -c '^\*\*' README.md` reports
  a count consistent with PR #124's four-route shape (no routes
  added or removed).
- Manual end-to-end test in PR-B's body: on a clean venv on a
  different machine, run `pip install agentbundle` → `agentbundle
  install --pack core git+https://github.com/eugenelim/agent-ready-repo`
  → confirm both commands succeed without ever cloning the catalogue.

**Approach:**

- Edit `README.md` route 3 only. Headline becomes something like:
  ```
  **Reference CLI** ([RFC-0003](docs/rfc/0003-spec-and-cli.md)) — `pip install agentbundle`, then:
  ```
- Trailing paragraph collapses to one sentence: the route's
  distinction is the remote `git+https://` catalogue source — no
  clone needed. Drop the "RFC-0003 §F-cli-dist isn't shipped yet"
  hedge (it just shipped).
- Do **not** touch routes 1, 2, 4 or the four-route section's shape.

**Done when:** The clean-venv manual gesture above succeeds end-to-end;
adversarial-reviewer pass on the diff returns clean; PR-B's CI passes.

---

## Rollout

Three phases, sequenced. Phases B and C are gated on out-of-band
human action; the spec's code work (Phase A) is shippable independently.

**Phase A — PR-A merges (T1-T6, no out-of-band dependency).**

- Workflow file ships dormant until a tag is pushed.
- `publish-artifactory` skipped on every run until an adopter
  configures the secrets.
- `publish-pypi` requires Pending Publisher (Phase B) before any tag
  push will succeed; tag pushes before Phase B fail with an OIDC
  permission error, which is recoverable (delete the tag, redo).

**Phase B — out-of-band PyPI account + Pending Publisher (≈10 min).**

- Create PyPI account at <https://pypi.org/account/register/>; enable
  2FA.
- PyPI → Your account → Publishing → "Add a pending publisher". Form
  values **must** match the workflow exactly:
  - PyPI Project Name: `agentbundle`
  - Owner: `eugenelim`
  - Repository name: `agent-ready-repo`
  - Workflow filename: `release-agentbundle.yml`
  - Environment name: `pypi`
- GitHub repo Settings → Environments → New environment → name it
  `pypi`. (Optional: require manual approval before deploys; not
  required for OIDC but recommended.)

**Phase C — first PyPI publish + PR-B (T7).**

- On `main`, bump `packages/agentbundle/pyproject.toml`'s `version`
  to `0.1.0` if not already; commit; push.
- `git tag agentbundle-v0.1.0 && git push origin agentbundle-v0.1.0`.
- Watch the workflow run. Both `build-and-smoke` and `publish-pypi`
  must succeed. (`publish-artifactory` skipped unless the corp added
  its three secrets in this repo's environment.)
- Smoke: on a clean machine, `python3 -m venv /tmp/v && /tmp/v/bin/pip
  install agentbundle && /tmp/v/bin/python -c "from
  agentbundle.credentials import load_credentials"`.
- Open PR-B (T7). Merge once CI passes.

**Phase D — (deferred, optional, per corp adopter) Artifactory
activation.**

- The corp adopter forks this repo or sets the three secrets directly:
  `ARTIFACTORY_URL`, `ARTIFACTORY_USER`, `ARTIFACTORY_TOKEN`.
- Next tag push runs `publish-artifactory` automatically.
- Verification per AC14.

## Risks

- **Pending Publisher config mismatch.** Any of the four PyPI form
  values diverging from the workflow → OIDC handshake fails closed,
  publish refuses. **Mitigation:** PR-A's body lists the four values
  verbatim; T4's `environment: pypi` is the single declaration the
  human form must mirror.
- **GitHub `pypi` environment doesn't exist when first tag is pushed.**
  If PR-A merges and someone tags before Phase B's "Settings →
  Environments → New environment" step runs, the workflow refuses
  to start `publish-pypi` with an "environment not found" error
  rather than an OIDC error. The tag is "burnt" — re-pushing it
  requires `git tag -d` + force-push, and PyPI's monotonic-version
  rule risks the version number if the same tag is reused after a
  partial publish. **Mitigation:** Phase B's checklist gates the
  Environment creation explicitly before any tag; PR-A's body names
  this as the first manual step after merge.
- **PyPI account deletion, banning, or Trusted Publisher revocation
  mid-flight.** PyPI ops can remove a project name, ban an account,
  or revoke the Pending Publisher between Phase B success and the
  first tag push — or after the first publish (project deletion is
  sticky and version numbers cannot be reused). **Mitigation:**
  Phase B documents that the PyPI account belongs to the project's
  maintainer (eugenelim); revocation is an Ask-first event that
  surfaces to a human, not a "delete tag and retry" recovery.
- **Tag pushed against wrong commit / mismatched version.**
  **Mitigation:** T3 assertion fails the workflow before publish runs;
  the package version on PyPI cannot be deleted/overwritten so the
  cost of a wrong publish is a permanent skipped version number, not a
  bad release.
- **PyPI version 0.1.0 already published by a squatter mid-flight.**
  **Mitigation:** Phase B claims the name before any tag push — name
  is reserved by the Pending Publisher config the moment it's
  submitted on PyPI's side. Pre-checked this turn: the name is free.
- **Artifactory step-level guard subtly wrong.** GitHub Actions has
  surprising quoting rules around shell expansion of `secrets.X`
  inside `run:` blocks. **Mitigation:** T5's step-level-guard idiom
  is the documented pattern; verify the Skipped step-level behaviour
  explicitly on PR-A's first CI run before merging.
- **The corp Artifactory upload semantics differ subtly per
  deployment.** **Mitigation:** Phase D is per-fork; the workflow we
  ship is a starting point, not a guarantee.

## Changelog

- 2026-05-26: initial plan.
- 2026-05-26: empirical baseline added under §Construction tests +
  AC2/AC3 Tests bullets sharpened with the exact pre-T1 wheel
  filename and twine warning count. No spec-contract change — the
  baseline confirms T1's scope matches reality (the two warnings
  `readme` closes are exactly the two `twine check` flags today).
