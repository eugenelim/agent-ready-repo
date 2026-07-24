# Plan: Catalogue Tooling — CI Gates

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Seven independent tasks, all depend on Wave 1-5 being shipped. Tasks 1-7
(one per gate A-G) can be written in parallel since they touch different workflow
files. Gate H is a modification to the existing release workflow. Gate I is
documentation only. Execute in parallel; merge sequentially.

## Constraints

- ini-005 brief Bucket 13.
- All gates use example.test values only. No real endpoints, credentials, or tokens.
- Gate A must use `python -m pytest` autodiscovery — no manual test list.
- Gate E network isolation uses Python mocking if real namespacing unavailable in CI.
- New GitHub Actions jobs must not introduce new pinned Actions beyond those
  already in the workflow (no new TOFU; SHA-pin any new Action).

## Construction tests

- `test_gate_a_job_exists`: parse relevant workflow YAML; assert job ID
  `agentbundle-tests` present with matrix entries for ubuntu/3.11, ubuntu/3.12, windows/3.11.
- `test_gate_b_job_exists`: assert `external-catalogue-smoke` job present.
- `test_gate_g_path_sensitivity`: unit test for the release-impact script logic:
  mock a diff touching `agentbundle/catalogue_tooling/foo.py`; assert triggers.
  Mock a diff touching only `packs/core/pack.toml`; assert does not trigger.
- `test_gate_i_template_no_real_credentials`: grep Gate I documentation for
  known production URL patterns; assert zero hits.

## Design (LLD)

### Gate A workflow snippet

```yaml
jobs:
  agentbundle-tests:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.11", "3.12"]
        exclude:
          - os: windows-latest
            python: "3.12"   # windows+3.12 can be added when CI capacity permits
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-python@<sha>
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -e packages/agentbundle
      - run: python -m pytest
        working-directory: packages/agentbundle
```

### Gate B workflow snippet

```yaml
  external-catalogue-smoke:
    runs-on: ubuntu-latest
    steps:
      - ... build wheel and install in isolation ...
      - name: Create external catalogue
        run: |
          mkdir -p /tmp/ext-cat/packs/sample-pack/.apm/skills/hello
          # write minimal pack.toml, plugin.json, marketplace.json, SKILL.md, catalogue.toml
      - name: Run portable commands
        run: |
          agentbundle catalogue lint --root /tmp/ext-cat
          agentbundle catalogue verify --root /tmp/ext-cat
          agentbundle catalogue build --root /tmp/ext-cat --output /tmp/ext-dist
          agentbundle catalogue package --root /tmp/ext-cat --bundle smoke \
            --release 1970.01.01.0 --channel stable --output /tmp/ext-pkg
          agentbundle catalogue verify --archive /tmp/ext-pkg/catalogues/smoke/releases/1970.01.01.0/catalogue-1970.01.01.0.tar.gz
```

### Gate G release-impact script design

```python
# tools/repo/check_release_impact.py
RELEASE_IMPACTING_PATHS = [
    "packages/agentbundle/agentbundle/catalogue_tooling/",
    "packages/agentbundle/agentbundle/cli.py",
    "packages/agentbundle/agentbundle/_data/catalogue.schema.json",
    "packages/agentbundle/agentbundle/_data/",
    "docs/contracts/",
]
NON_IMPACTING_PATHS = [
    "catalogue.toml", "packs/", "profiles/",
    "tools/catalogue/", "tools/repo/", "web/", "site/",
]
# Diff PR against merge base; if any changed file starts with RELEASE_IMPACTING_PATHS
# and the PR does NOT contain a changelog fragment or version bump → exit 1.
```

### Gate E network isolation approach

Use a `monkeypatch` fixture or a `responses` library mock (already used elsewhere in
the test suite for HTTPS catalogue tests). The key invariant: after `verify_archive`
+ `extract` + `list-packs`, assert that `agentbundle.https_catalogue` was not
called (mock it to raise `AssertionError` if invoked).

---

## Tasks

### T1: Gate A — complete AgentBundle test discovery

**Verification mode:** Goal-based check

**Tests:**
- `test_gate_a_job_exists`

**Approach:** Edit the main CI workflow to add (or replace any partial)
`agentbundle-tests` job with full matrix and `python -m pytest` autodiscovery.
SHA-pin any new Actions used. Run locally to confirm discovery count.

**Depends on:** all Wave 1-4 specs shipped (new tests must be discoverable)

---

### T2: Gate B — external catalogue portability

**Verification mode:** Goal-based check

**Tests:**
- `test_gate_b_job_exists`

**Approach:** Add `external-catalogue-smoke` job. Script creates a minimal
external catalogue fixture (inline bash or a Python helper script). Runs all
5 portable commands. No Makefile, no tools/ copied.

**Depends on:** T1

---

### T3: Gate C — enterprise distribution

**Verification mode:** Goal-based check

**Tests:**
- `test_gate_c_job_exists`
- `test_gate_c_no_real_creds`: parse the job YAML; assert no production URL.

**Approach:** Add `enterprise-agentbundle-distribution` job. Uses a `tmp_catalogue.toml`
written inline by the job. Builds wheel + zipapp. Scans with grep for
`AGENTBUNDLE_HTTP_BEARER_TOKEN`, `bearer token`, production domain patterns — fails
if found. Uses `example.test` domain throughout.

**Depends on:** T1

---

### T4: Gate D — real catalogue artifact

**Verification mode:** Goal-based check

**Tests:** - `test_gate_d_job_exists`

**Approach:** Add `catalogue-artifact-smoke` job. Packages twice with same
`SOURCE_DATE_EPOCH`. Compares archive bytes with `sha256sum`. Confirms three
required files. Verifies + extracts + list-packs.

**Depends on:** T1

---

### T5: Gate E — disconnected flow

**Verification mode:** Goal-based check

**Tests:** - `test_gate_e_job_exists`

**Approach:** Add `catalogue-disconnected-smoke` job. After packaging (from Gate D),
run verify + extract + list-packs with `AGENTBUNDLE_OFFLINE_ONLY=1` env var
that makes `https_catalogue.py` raise if invoked (or mock the HTTP module at
Python level). Assert no network calls.

**Depends on:** T4

---

### T6: Gate F — repository rewiring

**Verification mode:** Goal-based check

**Tests:** - `test_gate_f_job_exists`

**Approach:** Add `catalogue-repo-rewire` job. Reuses the tests from
spec/catalogue-tooling-rewire's test suite (already written). Confirm shims,
Makefile targets, no portable logic in tools/.

**Depends on:** spec/catalogue-tooling-rewire shipped

---

### T7: Gate G — release impact

**Verification mode:** TDD

**Tests:**
- `test_gate_g_path_sensitivity` (unit test the script logic, not the job)
- `test_gate_g_job_exists`

**Approach:** Write `tools/repo/check_release_impact.py`. Add to CI as a
required check on all PRs. Gate passes when: no release-impacting paths changed,
OR when a changelog fragment / version bump is present in the diff.

**Depends on:** T1

---

### T8: Gate H — release workflow

**Verification mode:** Goal-based check

**Tests:** - Assert release workflow YAML contains all required pre-publish steps.

**Approach:** Edit the existing release/publish workflow to require jobs A-E and
Gate C before PyPI publication. Add sync-defaults --check as a pre-publish step.

**Depends on:** T1-T5

---

### T9: Gate I — Artifactory publication template

**Verification mode:** Goal-based check

**Tests:** - `test_gate_i_template_no_real_credentials`

**Approach:** Add or update a documentation file or commented workflow template
showing the 6-step publication sequence (verify → package → upload archive →
upload sidecar → verify upload → upload channel descriptor last). Uses
example.test values. Credentials come from CI secret store, not hard-coded.

**Depends on:** spec/catalogue-tooling-package-enhanced shipped (to confirm
the actual output paths)

## Changelog
