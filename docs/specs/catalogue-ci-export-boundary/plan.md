# Plan: catalogue-ci-export-boundary

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Source-of-truth path

The export-catalogue skill is a projected primitive. All edits go to:

```
packs/catalogue-curation/.apm/skills/export-catalogue/
```

After code or doc changes, run `make build-self` to project to `.claude/` and
`.agents/`. The build-check gate verifies projection parity.

## Constraints

- Do not modify existing `verify()` behavior or its call signature.
- Do not touch `test_export_verify.py` or `test_integration_export.py`.
- All new files land in `packs/catalogue-curation/.apm/skills/export-catalogue/scripts/`.

## Risks

- `Violation` reuse: CI boundary findings use `anchor` values `"ci_path"` and
  `"ci_badge_url"`, distinct from identity anchors `url/email/slug/owner`.
  No existing caller pattern-matches on anchor name; adding new values is safe.
- Dot-directory check could over-flag if a legitimate dot-directory (not
  `.claude`, `.agents`, `.github`) is in the export target. Mitigated by: the
  check fires in the step 10 verify pass — non-CI dot-directories should not
  appear in the target by construction.

## Tasks

### Task 1 — Write red stubs in `test_export_ci_boundary.py`

**Mode:** TDD (red phase)
**Depends on:** none

**Approach (stub: true):** Create
`packs/catalogue-curation/.apm/skills/export-catalogue/scripts/test_export_ci_boundary.py`
importing `export_verify as V`. Add the eight test functions from AC7 with
`tmp_path` fixtures, a `_tree(tmp, files)` helper, and each assertion calling
`V.check_ci_boundary(root)` (which doesn't exist yet). Each function carries
`# STUB: AC7` so Task 4 can identify it. Tests fail with `AttributeError` on
`V.check_ci_boundary`.

Eight tests: `test_ci_contract_guide_eligible`, `test_github_workflow_flagged`,
`test_github_adapter_path_passes`, `test_ci_root_file_flagged`,
`test_unknown_provider_flagged`, `test_badge_url_in_guide_flagged`,
`test_badge_url_outside_guides_flagged`, `test_clean_export_passes`.

**Done when:** `pytest scripts/test_export_ci_boundary.py` from the `scripts/`
directory exits non-zero; all eight tests collected.

---

### Task 2 — Update `SKILL.md` (strip, guide eligibility, verify scope)

**Mode:** visual/manual QA
**Depends on:** none
**Path:** `packs/catalogue-curation/.apm/skills/export-catalogue/SKILL.md`

**Approach:**
1. Step 3 (Strip): replace "release workflows" with the explicit scoped list and
   positive allowlist statement from AC1. Name `.github/workflows/` (not the
   `.github/` root), `.gitlab-ci.yml`, `Jenkinsfile`, `.travis.yml`, badges,
   no-credentials clause.
2. Step 6 (Stage transportable guides): add AC2's sentence naming
   `catalogue-ci-contract.md` as eligible with the CI-neutrality principle.
3. Step 10 (Verify, fail-closed): add `check_ci_boundary()` as an additional
   check.

**Done when:**
- `grep -n "workflows\|check_ci_boundary\|positive allowlist" SKILL.md` returns
  hits in the three correct sections (steps 3, 6, 10).
- Manual read confirms step 3 explicitly names `.github/workflows/` (with
  `/workflows/`) and does NOT exclude a bare `.github/` root — the scoping is
  the key correctness boundary; grep alone cannot verify it.
- File has no RFC/ADR/spec citations.

---

### Task 3 — Update `transform-manifest.md` (STRIP and GUIDES sections)

**Mode:** visual/manual QA
**Depends on:** none
**Path:** `packs/catalogue-curation/.apm/skills/export-catalogue/references/transform-manifest.md`

**Approach:**
1. Section 1 (STRIP): replace/extend the "release workflows" line with the
   explicit exclusion list from AC4 and the positive allowlist statement.
   Name `.github/workflows/` precisely (not the root), `.gitlab-ci.yml`,
   `Jenkinsfile`, badges, no-credentials clause.
2. Section 4 (GUIDES): add the `guides/_shared/reference/catalogue-ci-contract.md`
   eligibility statement and CI-neutrality guidance from AC5.

**Done when:**
- `grep -n "catalogue-ci-contract\|positive allowlist\|no credentials"
  transform-manifest.md` returns expected hits.
- Manual read confirms section 1 scopes to `.github/workflows/` not bare
  `.github/`.
- File has no RFC/ADR/spec citations.

---

### Task 4 — Implement `check_ci_boundary` in `export_verify.py`

**Mode:** TDD (green phase)
**Depends on:** Task 1 (red stubs collected)
**Path:** `packs/catalogue-curation/.apm/skills/export-catalogue/scripts/export_verify.py`

**Tests:** all eight stubs from `test_export_ci_boundary.py` (AC7).

**Implementation:**

Add to `export_verify.py`: move `import re` into the existing top-level import
block (alongside `from pathlib import Path`); add the constants and the function
after the existing `verify` function:

```python
# In the top import block (beside existing imports):
import re

# After the existing `verify` function — constants then function:

# GitHub Actions badge URL pattern (owner+repo+/actions/workflows/).
_BADGE_RE = re.compile(
    r"https?://[^)\s]*github[^)\s]*/[^)\s]+/[^)\s]+/actions/workflows/",
    re.IGNORECASE,
)

# Dot-directories that adapters legitimately project into export targets.
# .github is included because .github/workflows/ is caught by Check 1's early
# continue, and .github/skills|agents|hooks|instructions/ are legitimate
# Copilot adapter projection paths.
_ALLOWED_DOT_DIRS = frozenset({".claude", ".agents", ".github"})

# Known root-level CI config file names (not directories; no leading dot).
_CI_ROOT_FILES = frozenset({".gitlab-ci.yml", ".travis.yml", "Jenkinsfile"})

# No prefix constant — use path parts for cross-platform correctness (Windows uses \).


def check_ci_boundary(target: Path) -> list[Violation]:
    """Check for CI implementation files in the export output.

    Returns Violations for:
    - Files under .github/workflows/ (GitHub Actions; path-parts check, not string prefix)
    - Root-level known CI config files (.gitlab-ci.yml, Jenkinsfile, .travis.yml)
    - Files under a dot-directory not in _ALLOWED_DOT_DIRS (structural
      unknown-provider detection — len(parts) > 1 guard skips root dotfiles)
    - Files whose content contains a GitHub Actions badge URL (all text files)

    Does NOT flag .github/skills/, .github/agents/, .github/hooks/, or
    .github/instructions/ — these are legitimate Copilot adapter projection paths.
    """
    target = Path(target)
    violations: list[Violation] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file() or _skip_by_ext(p):
            continue
        rel = str(p.relative_to(target))
        parts = Path(rel).parts
        root = parts[0] if parts else ""

        # Check 1: .github/workflows/ by path parts — cross-platform.
        # str(p.relative_to(target)) is \-separated on Windows; parts[] is safe.
        if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "workflows":
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 2: known root-level CI config files.
        if root in _CI_ROOT_FILES:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 3: files *under* dot-directories not in the projected-tool allowlist.
        # len(parts) > 1 guard: root-level dotfiles (.gitignore, .editorconfig)
        # are not CI suspects; only files inside an unknown dot-directory are.
        if len(parts) > 1 and root.startswith(".") and root not in _ALLOWED_DOT_DIRS:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 4: GitHub Actions badge URL in any text file.
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _BADGE_RE.search(content)
        if m:
            lineno = content[: m.start()].count("\n") + 1
            violations.append(Violation(rel, "ci_badge_url", lineno))

    return violations
```

**Why this design:**
- Check 1 uses `parts[0] == ".github" and parts[1] == "workflows"` — cross-platform.
  `.github/skills/core/SKILL.md` has `parts[1] == "skills"` → no match → falls
  through to Check 3 where `.github` IS in `_ALLOWED_DOT_DIRS` → passes.
- Check 2 catches known root-level CI filenames (no dot-directory — `Jenkinsfile`,
  `.gitlab-ci.yml`, `.travis.yml`).
- Check 3 uses `len(parts) > 1` so root-level dotfiles (`.gitignore`) are not
  flagged; `.ci/step.yml` has root `.ci` (starts with `.`, not in `_ALLOWED_DOT_DIRS`,
  len > 1) → flagged as `ci_path`.
- Check 4 covers all text files (not guides-only) per AC6.

**Done when:** `pytest scripts/test_export_ci_boundary.py` exits 0 (all eight pass).

---

### Task 5 — Project and verify

**Mode:** goal-based
**Depends on:** Tasks 2, 3, 4

**Approach:**
1. From repo root: `make build-self` — projects the updated `.apm/` source to
   `.claude/` and `.agents/`.
2. Confirm three-copy parity: the updated `export_verify.py` and
   `SKILL.md` appear in all three trees with the same content.

**Done when:**
- `make build-self` exits 0.
- `diff packs/catalogue-curation/.apm/skills/export-catalogue/scripts/export_verify.py \
  .claude/skills/export-catalogue/scripts/export_verify.py` exits 0.

---

## Post-task GATES

After all tasks and `make build-self` complete:

```bash
make build-check                                             # parity + lint gate
# From the export-catalogue scripts/ directory:
python3 -m pytest scripts/test_export_ci_boundary.py -v    # new tests (AC7)
python3 -m pytest scripts/test_export_verify.py -v         # regression (AC8)
python3 -m pytest scripts/test_integration_export.py -v    # regression (AC8)
```

All pass → GATES green.

Run `scripts/lint-spec-status.py` (work-loop sibling) at DECIDE to check
spec metadata invariants.
