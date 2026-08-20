# Plan: catalogue-ci-contract-guide

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Write one new guide (`guides/_shared/reference/catalogue-ci-contract.md`), add
three discovery hooks (README link, agentbundle.md paragraph, catalogue-format.md
cross-reference), two link-only references in AGENTS.md files, and a contract
test file that verifies the guide's claims against HEAD CLI behaviour. All tasks
except T7 are documentation edits with goal-based or visual/manual QA; T7 is TDD
against the existing fixture infrastructure.

Order: T1 (guide) first so every cross-reference target exists before we add the
links; T2–T6 (link placements) immediately after, each independent of each other
but each depends on T1 being committed; T7 (tests) can run concurrently with T2–T6
since it only reads the CLI, not the guide.

## Constraints

- `packs/AGENTS.md` cap is 150 lines (currently 142). T6 may add at most 1 line.
- `AGENTS.local.md` cap is 250 lines (currently 174). T5 is unconstrained in practice.
- Guide must be adopter-clean: no RFC/ADR/spec citations, no internal paths.
- `catalogue package --format json` must NOT appear in the guide or tests.
- `guides/_shared/reference/` is the correct location (Diátaxis: reference quadrant,
  cross-pack catalogue tooling).

## Construction tests (cross-cutting)

T7 adds `packages/agentbundle/tests/unit/test_catalogue_ci_contract.py`. The
existing `test_catalogue_tooling_foundation.py` has a helper that returns a
valid fixture catalogue root; T7 imports it rather than duplicating fixture setup.
The contract tests exercise the CLI via subprocess (same pattern as the foundation
tests) to avoid mock-shape divergence from real CLI behaviour.

Manual QA (T1): after writing the guide, run `agentbundle catalogue lint --root .
--format json` and `agentbundle catalogue verify --root . --format json` against
the working catalogue and confirm the JSON structure and exit codes match what the
guide claims. Record stdout in the PR's *How to verify* section.

## Design (LLD)

No new code modules. The agentbundle CLI is unchanged. The test file follows the
subprocess invocation pattern established in
`packages/agentbundle/tests/unit/test_catalogue_tooling_foundation.py` lines 1–60.

### Fixture catalogue for T7

`test_catalogue_tooling_foundation.py` exposes a private constant `_REPO_ROOT`
(line 487) — not a pytest fixture, and `_`-prefixed. T7 defines its own fixture:

```python
@pytest.fixture
def working_catalogue_root():
    return Path(__file__).resolve().parents[4]  # same derivation as _REPO_ROOT
```

For the "exits 1 on errors" branch, T7 creates a `tmp_path` directory with a
`catalogue.toml` containing invalid TOML or missing required fields. The
autouse `_isolate_user_config_dir` fixture in `conftest.py` redirects `HOME` and
`XDG_CONFIG_HOME` to a sandbox; T7's subprocess calls inherit this env, which is
harmless as long as every invocation passes `--root` explicitly.

### Guide structure

```
# Catalogue CI contract
(frontmatter)

## Overview  ← one-paragraph orientation

## Responsibility boundary  ← table: party / owns / never does

## CI lifecycle phases
### Phase 1: Tool acquisition
### Phase 2: Change validation
### Phase 3: Release packaging
### Phase 4: Publication
### Phase 5: Post-publication verification
### Phase 6: Evidence retention

## Exit codes  ← AC7 table

## Secrets and network calls  ← AC9

## Command reference
### catalogue lint
### catalogue verify
### catalogue package

## See also  ← AC10
```

## Tasks

### T1: Write `guides/_shared/reference/catalogue-ci-contract.md`

**Depends on:** none

**Verification mode:** visual/manual QA

**Touches:** `guides/_shared/reference/catalogue-ci-contract.md` (new)

**Tests:**
- No stub (visual/manual QA). After writing: run
  `agentbundle catalogue lint --root . --format json` and confirm stdout parses as
  JSON with `ok: true`; run `agentbundle catalogue verify --root . --format json`
  and confirm same. Record both in the PR's *How to verify* block.
- Confirm `agentbundle catalogue package --help` — verify `--format` flag does
  NOT appear in help output, confirming the guide's omission is accurate.

**Approach:**
- Frontmatter: `title`, `summary`, `pack: _shared`, `kind: reference`, `status: stable`.
- Write the responsibility-boundary table first — it is the load-bearing concept
  every reader needs before any command detail.
- Document each phase with portable, provider-neutral commands (no YAML blocks).
- Exit codes section: 0/1/2 with the `catalogue package`-returns-1 note.
- Secrets section: three bullets (AgentBundle CLI never reads secrets / never
  issues network calls / TLS + credentials are Organization CI's responsibility).
- Command reference: lint + verify with `--format json` JSON schema; package with
  full flag list and output layout, explicit no-`--format json`.
- See also: two links (agentbundle.md, catalogue-format.md).
- No internal governance citations anywhere.

**Done when:** file exists, frontmatter parses, manual QA run recorded, guide has
all sections from AC1–AC10.

---

### T2: Update `guides/_shared/README.md` — Reference link

**Depends on:** T1

**Verification mode:** goal-based

**Touches:** `guides/_shared/README.md`

**Tests:**
- `grep "catalogue-ci-contract" guides/_shared/README.md` exits 0.

**Approach:**
- Add one entry in the `## Reference` section:
  `- [Catalogue CI contract](reference/catalogue-ci-contract.md) — ...`

**Done when:** grep passes.

---

### T3: Update `guides/_shared/reference/agentbundle.md` — Catalogue CI paragraph

**Depends on:** T1

**Verification mode:** goal-based

**Touches:** `guides/_shared/reference/agentbundle.md`

**Tests:**
- `grep "catalogue-ci-contract" guides/_shared/reference/agentbundle.md` exits 0.

**Approach:**
- Add a short `## Catalogue CI` section after the existing subcommand list
  (before or after `## Preview before applying`) with 2–3 sentences explaining
  that `catalogue lint`, `catalogue verify`, and `catalogue package` are the
  portable CI commands, and point to the CI contract guide for the full pipeline
  contract.

**Done when:** grep passes; agentbundle.md still reads coherently end-to-end.

---

### T4: Update `guides/_reference/catalogue-format.md` — Validation cross-reference <!-- Moved 2026-08-18 by spec/guide-metadata-completion to `guides/_shared/reference/catalogue-format.md`; the public route is unchanged. -->

**Depends on:** T1

**Verification mode:** goal-based

**Touches:** `guides/_reference/catalogue-format.md`

**Tests:**
- `grep "catalogue-ci-contract" guides/_reference/catalogue-format.md` exits 0.

**Approach:**
- In the `## Validation` section, after the existing `agentbundle catalogue verify`
  block, add one sentence: "For CI pipeline patterns using these commands, see the
  [Catalogue CI contract](../_shared/reference/catalogue-ci-contract.md)."

**Done when:** grep passes.

---

### T5: Update `AGENTS.local.md` — link-only CI reference

**Depends on:** T1

**Verification mode:** goal-based

**Touches:** `AGENTS.local.md`

**Tests:**
- `grep "catalogue-ci-contract" AGENTS.local.md` exits 0.
- `wc -l AGENTS.local.md | awk '{print $1}'` ≤ 250.

**Approach:**
- In the CI pipeline context section (or create a brief "Catalogue CI" bullet in
  the cross-references at the top), add one line linking to the guide. No content
  duplication — link only.

**Done when:** grep passes; line count ≤ 250.

---

### T6: Update `packs/AGENTS.md` — link-only CI reference

**Depends on:** T1

**Verification mode:** goal-based

**Touches:** `packs/AGENTS.md`

**Tests:**
- `grep "catalogue-ci-contract" packs/AGENTS.md` exits 0.
- `wc -l packs/AGENTS.md | awk '{print $1}'` ≤ 150.

**Approach:**
- In the `## Primary workflow (any catalogue)` section, after the `make build-check`
  block, add one sentence linking to the CI contract guide for CI pipeline
  orchestration beyond the dev-loop commands.

**Done when:** grep passes; line count ≤ 150.

---

### T7: Add command-contract tests

**Depends on:** none

**Verification mode:** TDD

**Touches:** `packages/agentbundle/tests/unit/test_catalogue_ci_contract.py` (new)

**Tests (these ARE the deliverable for this task):**

```python
import json, subprocess, sys
from pathlib import Path
import pytest

@pytest.fixture
def working_catalogue_root():
    return Path(__file__).resolve().parents[4]  # repo root = catalogue root

# AC16: lint --format json stdout parses as JSON with required keys
def test_catalogue_lint_json_output_parses(working_catalogue_root):
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "lint",
         "--root", str(working_catalogue_root), "--format", "json"],
        capture_output=True, text=True, encoding="utf-8"
    )
    doc = json.loads(result.stdout)  # raw stdout — no strip; proves AC18 too
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc

# AC17: verify --format json stdout parses as JSON with required keys
def test_catalogue_verify_json_output_parses(working_catalogue_root):
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "verify",
         "--root", str(working_catalogue_root), "--format", "json"],
        capture_output=True, text=True, encoding="utf-8"
    )
    doc = json.loads(result.stdout)
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc

# AC18: covered implicitly — json.loads on raw (unstripped) stdout

# AC19a: clean catalogue → exit 0
def test_catalogue_lint_exits_0_on_clean(working_catalogue_root): ...
def test_catalogue_verify_exits_0_on_clean(working_catalogue_root): ...

# AC19b: invalid catalogue → exit 1
# Use tmp_path with a catalogue.toml that is missing required fields
def test_catalogue_lint_exits_1_on_errors(tmp_path): ...
def test_catalogue_verify_exits_1_on_errors(tmp_path): ...

# AC20: package exit 0 + output layout
# No --pack flag; supply required flags: --bundle, --release, --channel, --output
def test_catalogue_package_exits_0_and_layout(working_catalogue_root, tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "package",
         "--root", str(working_catalogue_root),
         "--bundle", "test-bundle",
         "--release", "0.0.1-ci",
         "--channel", "stable",
         "--output", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0
    base = tmp_path / "catalogues" / "test-bundle" / "releases" / "0.0.1-ci"
    assert (base / "catalogue-0.0.1-ci.tar.gz").exists()
    assert (base / "catalogue-0.0.1-ci.tar.gz.sha256").exists()
    assert (tmp_path / "catalogues" / "test-bundle" / "channels" / "stable.json").exists()

# AC21: package exits 2 on missing required flags
def test_catalogue_package_exits_2_on_missing_flags():
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "package"],
        capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 2
```

**Approach:**
- Define `working_catalogue_root` fixture inline (not imported from foundation).
- For invalid-catalogue tests: write `[catalogue]\nname = "x"` to `tmp_path/catalogue.toml`
  (missing `version`, `schema`, `packs/`) — lint should exit 1.
- `_isolate_user_config_dir` autouse fixture in conftest.py sets sandbox `HOME`;
  subprocess calls inherit this env; pass `--root` explicitly on every call so
  no command silently reads user config from the sandbox.

**Done when:** all six test functions pass under
`python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_ci_contract.py -q`.

---

### T8: Gates

**Depends on:** T1–T7

**Verification mode:** goal-based

**Touches:** nothing (read-only gates)

**Tests:** none (this task IS the test run)

**Approach:**
```bash
python3 tools/lint-ruff.py
python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_ci_contract.py -q
python3 -m pytest packages/agentbundle/tests/ -q   # regression check
python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .
```

**Done when:** all four commands exit 0.

## Changelog

- 2026-07-28: Initial plan authored.
