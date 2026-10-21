# Plan: Packageable blank catalogue from `catalogue init`

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `catalogue_tooling/initialise.py` (`_build_plan` already emits two generated files, `catalogue.toml` and `.claude-plugin/marketplace.json`, through `classify_conflicts`, `_stage_and_verify`, `_commit_files` and `_rollback`); `catalogue_tooling/package.py` (`package_catalogue` already returns `_err(...)` results for every other expected failure); tests `packages/agentbundle/tests/integration/test_catalogue_init.py` and `packages/agentbundle/tests/unit/test_catalogue_tooling_package.py`. Deviation: `classify_conflicts` gains one keep-existing rule for two root agent-guidance paths.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/catalogue-init-packageable/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Init gains two generated files, so the archive marker exists from the first run.
Packaging already collects a root `AGENTS.md`, and the archive verifier already
accepts it, so no packaging or verifier change is needed for the main fix. The
include diagnostic is a separate, independent catch in `package_catalogue`. Docs
and the release surfaces follow the code. The riskiest part is the keep-existing
rule: it must not weaken the conflict guard for any other path.

Review shape: one PR, DEEP, one commit per task. Each task leaves the repository
green.

## Constraints

- `packages/AGENTS.md` owns the cross-package traps and the test-home table: version bump in both `version.py` and `pyproject.toml`, UTF-8 text I/O, and package tests that read no repository path.
- `tools/lint-catalogue-curation-guard.py`: every commit touching `packages/agentbundle/` carries an `Engine-Change-RFC:` trailer. No RFC governs plain init, so the trailer is `n/a — <justification>`; the changelog entry carries the same line.
- `docs/product/AGENTS.md` owns the changelog fragment procedure (`python3 tools/changelog.py new ...`).
- `guides/AGENTS.md`: job-page rules for `create-a-catalogue.md`; `title` equals the H1.
- `tools/test_scaffold_projection.py`: each shipped `AGENTS.md` has a `CLAUDE.md` sibling whose bytes are exactly `@AGENTS.md\n`; the generated root pair follows the same rule.

## Construction tests

**Rule for every acceptance test:** it must fail when the mechanism it checks is
bypassed — AC-0005 runs the real CLI in a subprocess, not the engine functions.

**Integration tests:** none beyond per-task tests.

**Manual verification:** T5's adopter rehearsal.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — `create-a-catalogue.md` | T3 | edited section | `python3 tools/validate_guides.py` green |
| Interface reference (init) — `catalogue-format.md` | T3 | edited Scaffold options | `python3 tools/validate_guides.py` green |
| Command reference (package) — `catalogue-commands.md` | T3 | edited package section | text names the marker and `CAT-PKG-001` |
| Release history — the surfaces in the spec's Release history row | T4 | changelog entry, README-pypi heading, fragment, roster pin | `tests/roster/test_okf_catalogue_discovery.py` green |

## Design (LLD)

### Interfaces & contracts

- `initialise.py` gains `generate_root_agents_md(name: str) -> bytes`, a pure function beside `generate_empty_marketplace`. Its only input is the validated `name` (`_SAFE_NAME_RE`), so no free-text flag reaches Markdown.
- `_build_plan` appends `AGENTS.md` and `CLAUDE.md` as `kind="generated"` after the two existing generated files. `CLAUDE.md` content is the constant `b"@AGENTS.md\n"`.
- `classify_conflicts` keeps a regular, non-symlink root `AGENTS.md` or `CLAUDE.md` as `ALREADY_PRESENT` whatever its content. The symlink and not-a-regular-file checks run first and are unchanged, so AC-0004 falls out of existing code. `_commit_files` already skips `ALREADY_PRESENT`. The rule matches the exact plan paths `AGENTS.md` and `CLAUDE.md`, never a basename, so `packs/AGENTS.md` and its siblings keep the conflict rule. A kept file's `sha256` is the hash of the bytes already read for the comparison; every other entry keeps the planned content's hash.
- `_scan_content`'s include branch gains a fourth `ValueError`: an entry whose first component under `packs/` starts with `_`. That matches the default walk, which prunes `_` directories directly under `packs/`.
- `package_catalogue` wraps its `_scan_content(...)` call in `except ValueError as exc: return _err(f"invalid [catalogue.package].include: {exc}")`. `_scan_content` raises `ValueError` only for the include-entry cases, and the call runs before any write.

Owned by: T1, T2.

### Behavior & rules

- The root `AGENTS.md` says what the catalogue is, that `_` directories are templates, which three files to read next, and the verify/lint/package commands. It states that `catalogue package` ships it as the archive marker, so an author does not delete it.
- A kept existing root `AGENTS.md` already satisfies the archive marker, because packaging ships whatever regular file is there.

Owned by: T1.

## Tasks

### T1: Init writes and keeps the root agent-guidance files; a blank catalogue packages

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/initialise.py, packages/agentbundle/tests/integration/test_catalogue_init_packageable.py, packages/agentbundle/tests/integration/test_catalogue_init.py

**Tests:**
- New file `packages/agentbundle/tests/integration/test_catalogue_init_packageable.py` covers AC-0001 to AC-0005. EXECUTE adds the AC-0002, AC-0003 and AC-0004 cases after the stub's red is proven.
- `test_dogfood_no_host_files_leaked` in `test_catalogue_init.py` adds `AGENTS.md` and `CLAUDE.md` to its generated-path set; it is the shipped assertion this change moves.
- The new file also checks that a changed nested `packs/AGENTS.md` and a changed `profiles/CLAUDE.md` each still give `CAT-INIT-007` with no file written, so the keep-existing rule cannot widen past the root.

  ```stub path=packages/agentbundle/tests/integration/test_catalogue_init_packageable.py run="python -m pytest -q {path}" red-exit=1
  """A blank catalogue from `catalogue init` packages and verifies with no hand edits."""

  from __future__ import annotations

  import os
  import subprocess
  import sys
  import tarfile
  from pathlib import Path

  PACKAGE_ROOT = Path(__file__).resolve().parents[2]


  def _cli(*args: str) -> subprocess.CompletedProcess[str]:
      env = os.environ.copy()
      env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(PACKAGE_ROOT), env.get("PYTHONPATH")]))
      env["PYTHONIOENCODING"] = "utf-8"
      return subprocess.run(
          [sys.executable, "-m", "agentbundle", *args],
          env=env,
          capture_output=True,
          text=True,
          encoding="utf-8",
      )


  def test_init_creates_root_agents_md_and_claude_shim(tmp_path: Path) -> None:
      from agentbundle.catalogue_tooling.initialise import init_catalogue
      from agentbundle.catalogue_tooling.results import FileAction

      target = tmp_path / "cat"
      result = init_catalogue(target=target, name="demo-cat")

      assert result.ok, result.diagnostics
      assert (target / "AGENTS.md").is_file()
      assert (target / "CLAUDE.md").read_bytes() == b"@AGENTS.md\n"
      actions = {fp.path: fp.action for fp in result.files}
      assert actions["AGENTS.md"] == FileAction.CREATE
      assert actions["CLAUDE.md"] == FileAction.CREATE


  def test_blank_catalogue_inits_verifies_packages_and_verifies_archive(tmp_path: Path) -> None:
      cat = tmp_path / "cat"
      out = tmp_path / "out"

      steps = [
          ("catalogue", "init", str(cat), "--name", "demo-cat"),
          ("catalogue", "verify", "--root", str(cat)),
          (
              "catalogue", "package", "--root", str(cat), "--bundle", "demo",
              "--release", "0.1.0", "--channel", "stable", "--output", str(out),
          ),
      ]
      for step in steps:
          proc = _cli(*step)
          assert proc.returncode == 0, (step, proc.stdout, proc.stderr)

      archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
      sidecar = archive.with_name(archive.name + ".sha256")
      proc = _cli("catalogue", "verify", "--archive", str(archive), "--sha256-file", str(sidecar))
      assert proc.returncode == 0, (proc.stdout, proc.stderr)

      with tarfile.open(archive, "r:gz") as tf:
          names = tf.getnames()
      assert "AGENTS.md" in names
      assert not [n for n in names if n.startswith(("packs/_example/", "profiles/_example/"))]
  ```

  Red validated from a `git archive HEAD` scratch copy: exit 1, both tests fail — no root `AGENTS.md`, and `catalogue package` exits 1 with `no catalogue marker found`.

**Done when:** `python -m pytest -q packages/agentbundle/tests/integration/test_catalogue_init_packageable.py packages/agentbundle/tests/integration/test_catalogue_init.py packages/agentbundle/tests/unit/test_catalogue_tooling_init.py` is green.

### T2: A bad include entry reports `CAT-PKG-001`

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/package.py, packages/agentbundle/tests/unit/test_catalogue_package_include_diagnostic.py

**Tests:**
- New file `packages/agentbundle/tests/unit/test_catalogue_package_include_diagnostic.py` covers AC-0006. The stub drives the not-under-`packs/` case through `package_catalogue`; EXECUTE adds the missing-entry, build-residue and `packs/_example` cases and a CLI subprocess case for the no-traceback clause.

  ```stub path=packages/agentbundle/tests/unit/test_catalogue_package_include_diagnostic.py run="python -m pytest -q {path}" red-exit=1
  """An invalid [catalogue.package].include entry is a CAT-PKG-001 diagnostic, not a traceback."""

  from __future__ import annotations

  from pathlib import Path


  def _blank_catalogue(tmp_path: Path) -> Path:
      from agentbundle.catalogue_tooling.initialise import init_catalogue

      root = tmp_path / "cat"
      assert init_catalogue(target=root, name="demo-cat").ok
      return root


  def test_include_entry_outside_packs_is_a_diagnostic(tmp_path: Path) -> None:
      from agentbundle.catalogue_tooling.package import package_catalogue

      root = _blank_catalogue(tmp_path)
      toml = root / "catalogue.toml"
      toml.write_text(
          toml.read_text(encoding="utf-8").replace("include  = []", 'include  = ["AGENTS.md"]'),
          encoding="utf-8",
      )
      out = tmp_path / "out"

      result = package_catalogue(
          root=root, bundle="demo", release="0.1.0", channel="stable", output=out,
      )

      assert not result.ok
      assert [d.code for d in result.diagnostics] == ["CAT-PKG-001"]
      assert "AGENTS.md" in result.diagnostics[0].message
      assert not out.exists()
  ```

  Red validated from a `git archive HEAD` scratch copy: exit 1 — `package_catalogue` raises `ValueError: pack_include entry 'AGENTS.md' must start with 'packs/'`.

**Done when:** `python -m pytest -q packages/agentbundle/tests/unit/test_catalogue_package_include_diagnostic.py packages/agentbundle/tests/unit/test_catalogue_tooling_package.py packages/agentbundle/tests/unit/test_package_catalogue.py` is green.

### T3: Guides describe the root files and the include diagnostic

**Depends on:** T1, T2

**Touches:** guides/_shared/how-to/create-a-catalogue.md, guides/_shared/reference/catalogue-format.md, docs/guides/reference/catalogue-commands.md

**Tests:**
- no stub (goal-based). `python3 tools/validate_guides.py`, `python3 tools/check-guide-index.py` and `python3 tools/lint-guide-titles.py` pass.

**Done when:** the three guide commands exit 0 and each edited section carries the evidence named in the spec's Durable Outputs row.

### T4: Release 0.53.1 surfaces move together

**Depends on:** T1, T2

**Touches:** packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md, packages/agentbundle/README-pypi.md, docs/product/changelog.d/*, tests/roster/test_okf_catalogue_discovery.py

**Tests:**
- no stub (goal-based). `tests/roster/test_okf_catalogue_discovery.py` pins `expected = "0.53.1"` against `version.py`, `pyproject.toml`, the README-pypi heading and the changelog heading.

**Done when:** `python -m pytest -q tests/roster/test_okf_catalogue_discovery.py` is green and `python3 tools/changelog.py validate` exits 0.

### T5: Adopter rehearsal

**Depends on:** T1, T2

**Tests:**
- no stub (manual QA). In a temporary directory outside the repository, with `PYTHONPATH=<worktree>/packages/agentbundle`, run `catalogue init`, `catalogue verify --root`, `catalogue package` and `catalogue verify --archive --sha256-file` with no hand edits; then set `include = ["AGENTS.md"]` and re-run `catalogue package`.

**Done when:** the verification ledger records each command, its exit code (0, 0, 0, 0, then 1) and the `CAT-PKG-001` line.

## Rollout

Ships in the next `agentbundle` patch release. A catalogue created by an earlier
release does not gain the root files by re-running init: its `catalogue.toml`
carries an older `minimum-agentbundle-version`, so init reports `CAT-INIT-007`
and writes nothing. Rollback is reverting the release.

## Risks

- A catalogue that already relied on init refusing an existing root `AGENTS.md` now gets it kept instead; no such reliance exists, because init never planned that path before.

## Changelog
