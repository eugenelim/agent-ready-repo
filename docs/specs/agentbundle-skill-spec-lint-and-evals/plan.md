# Plan: agentbundle skill-spec lint + pack evals

## Tasks

### T1: Fix adapt.py backslash in pending report
**Verification mode**: goal-based
**Depends on**: none
**Done when**: `assert ".claude/skills/foo/SKILL.upstream.md" in user_text` passes on Windows (the path uses forward slashes in the report)

**Approach**: Change line 304 in `commands/adapt.py`:
```python
report_lines.append(f"- `{rel_companion.as_posix()}`: {summary}")
```

---

### T2: Add AGENTBUNDLE_USER_ROOT env var to scope.py + fix test isolation
**Verification mode**: goal-based (Gate A windows test count drops)
**Depends on**: none

**Approach**:
- In `scope.py` `resolve_user_root()`: check `os.environ.get("AGENTBUNDLE_USER_ROOT")` and return `Path(val)` when set (skip expanduser entirely).
- Add `_set_home(monkeypatch, path)` helper to each affected test file. Helper sets `HOME`, `USERPROFILE` (win32), and `AGENTBUNDLE_USER_ROOT` env vars, AND patches `agentbundle.scope.resolve_user_root` directly.
- Affected files: `test_install_adapt_chain.py`, `test_install_dependencies_gate.py`, `test_install_dual_scope.py`, `test_multi_pack_install.py`, `test_recommends_cross_scope.py`, `test_reconcile.py`, `test_shared_prefix_coexistence.py`

---

### T3: Add PyYAML optional extra to agentbundle pyproject.toml
**Verification mode**: goal-based
**Depends on**: none
**Done when**: `pip install 'agentbundle[lint]'` installs PyYAML

**Approach**: Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
lint = ["pyyaml>=6.0"]
```

---

### T4: Create agentbundle/catalogue_tooling/skill_spec_lint.py
**Verification mode**: TDD
**Depends on**: T3

**Approach**: Port all check logic from `tools/lint-skill-spec.py` into a Python module:
- `SkillSpecDiagnostic` dataclass (code, severity, path, message, line, remediation)
- `lint_skill_spec(root: Path, pack: str | None) -> list[SkillSpecDiagnostic]`
- All check helpers: `_check_description_source`, `parse_frontmatter`, `check_frontmatter`, `check_body`, `check_layout`, `check_evals_json`, `check_eval_queries`
- Keep PyYAML import inside the public function so it raises `ImportError` gracefully
- Use forward slashes in all diagnostic paths (`.as_posix()`)

---

### T5: Integrate --deep into catalogue lint
**Verification mode**: goal-based
**Depends on**: T4

**Approach**:
- In `catalogue_tooling/lint.py`: add `deep: bool = False` param to `lint_catalogue()`; when True, import and call `skill_spec_lint.lint_skill_spec()` per pack; merge diagnostics
- In `commands/catalogue_lint.py`: pass `args.deep` to `lint_catalogue()`
- In `cli.py`: add `--deep` flag to `catalogue lint` parser; add it to `lint packs` alias parser too
- Exit 2 when `--deep` and PyYAML not installed; exit 1 on errors

---

### T6: Port test-lint-skill-spec.py to pytest
**Verification mode**: TDD
**Depends on**: T4

**Approach**:
- New file: `packages/agentbundle/tests/unit/test_catalogue_skill_spec_lint.py`
- Port all tree-A (error), tree-B (clean), tree-C (warn-only), tree-D/E/F cases from `tools/test-lint-skill-spec.py`
- Call `skill_spec_lint.lint_skill_spec(root, None)` directly (no subprocess)
- `tmp_path` for fixture trees
- Skip entire module when PyYAML not installed (`pytest.importorskip("yaml")`)

---

### T7: Create agentbundle/commands/pack_evals.py
**Verification mode**: goal-based
**Depends on**: none

**Approach**:
- Move `tools/run-pack-evals.py` content into `packages/agentbundle/agentbundle/commands/pack_evals.py`
- Remove `REPO_ROOT` hardcoded path; add `--catalogue-root` arg defaulting to `"."` (same as other commands)
- Rename `main()` to `run(args)` matching agentbundle command convention
- Add `argparse` subparser registration via CLI

---

### T8: Register pack evals run in CLI
**Verification mode**: goal-based
**Depends on**: T7

**Approach**:
- In `cli.py`: add `pack` top-level subcommand group (like `catalogue`)
- Add `pack evals run` subcommand with same flags as `run-pack-evals.py`'s argparse
- Wire via `_lazy("pack_evals")`

---

### T9: Rewire CI
**Verification mode**: goal-based
**Depends on**: T5, T8

**Approach**:
- `.github/workflows/docs.yml` `lint-skill-spec` job: replace `pip install -r tools/requirements.txt` + `python tools/lint-skill-spec.py` + `python tools/test-lint-skill-spec.py` with: install agentbundle from source with `[lint]` extra, then `agentbundle catalogue lint --root . --deep`
- `.github/workflows/pack-evals.yml`: replace `python tools/run-pack-evals.py --pack "$pack"` with `agentbundle pack evals run --pack "$pack"`

---

### T10: Remove tools/ scripts + update tooling
**Verification mode**: goal-based
**Depends on**: T9

**Approach**:
- Delete `tools/lint-skill-spec.py`, `tools/test-lint-skill-spec.py`, `tools/run-pack-evals.py`
- In `tools/test-all.py`: remove `("lint-skill-spec", ...)` entry
- In `tools/test-pack-evals-workflow.py`: update CI step assertion to check for `agentbundle pack evals run` instead of `run-pack-evals.py`

---

### T12: Slim AGENTS.local.md; consolidate skill/pack guidance into packs/AGENTS.md
**Verification mode**: goal-based
**Depends on**: T5 (packs/AGENTS.md already updated with lint --deep guidance)

**Approach**:
- `AGENTS.local.md` becomes a brief 20–30 line context-setter: "This is a pack catalogue. Pack and skill development guidance lives in [packs/AGENTS.md](packs/AGENTS.md)."
- Remove from AGENTS.local.md anything that IS skill/pack development guidance:
  - "Self-hosting drift — edit the source, not the projection" (already in packs/AGENTS.md)
  - "Agents project to multiple adapters — not Claude Code only" (move to packs/AGENTS.md)
  - "Shipped pack content carries no internal-governance citations" (already in packs/AGENTS.md)
  - The `tools/lint-*` references in "Adopter-facing materials ship" (updating these anyway post-migration)
- Keep in AGENTS.local.md:
  - The brief role statement + pointer to packs/AGENTS.md
  - Adopter-mindset principle (design against adopter's projected state)
  - House style for internal docs
  - AGENTS.md line caps (CI enforcement, repo-specific)
  - `docs/guides/` organization
  - Install-test coverage rule (agentbundle package testing)
  - New tool scripts: Python not bash
  - Windows/cross-OS compatibility (applies to all repo code)
  - Release coupling

---

### T13: Create packages/AGENTS.md for Python package development rules
**Verification mode**: goal-based
**Depends on**: T12

**Approach**:
- Create `packages/AGENTS.md` with Python-package-specific rules extracted from AGENTS.local.md:
  - Windows/cross-OS compatibility rules (encoding, symlinks, POSIX assertions, paths, subprocess)
  - Install-test coverage rule (parametrize over shipped adapters)
  - Release coupling (when agentbundle needs a version bump and PyPI release)
  - Test conventions (editable installs, conftest patterns)
- Remove those sections from AGENTS.local.md (they move here)

---

### T11: Update docs and version
**Verification mode**: goal-based
**Depends on**: T5, T8

**Approach**:
- `packs/AGENTS.md`: replace `python3 tools/lint-skill-spec.py` guidance with `agentbundle catalogue lint --root . --deep`; add note about `pip install 'agentbundle[lint]'`
- `packages/agentbundle/version.py` + `pyproject.toml`: bump `0.16.2` → `0.17.0`
- `packages/agentbundle/README.md`: document `catalogue lint --deep` and `pack evals run`
- `docs/product/changelog.md`: add `[agentbundle][0.17.0]` section
- Run `FORCE=1 make build-self` (CAT-V-015 drift check)
