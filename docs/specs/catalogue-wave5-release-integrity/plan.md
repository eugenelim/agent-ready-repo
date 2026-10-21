# Plan: Catalogue Wave 5 — release integrity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0076 D8; `packages/agentbundle/DESIGN.md` § Catalogue packaging engine; analogous production paths `catalogue_tooling/package.py` (`package_catalogue`, the staged-placement sequence) and `commands/catalogue_verify.py` (JSON envelope on stdout, human output on stderr); their tests `packages/agentbundle/tests/unit/test_catalogue_tooling_package.py`, `test_catalogue_tooling_archive.py` and `test_package_catalogue.py`. Deviation: the spec's Exit-code convention section.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

The change extends the existing package pipeline in place. Unit digests come
first, because verification, comparison and the docs all read them. The shared
derivation lives in `archive.py` so the producer (`package.py`), the verifier
and the comparison compute one function. The refusal and `--force` work is
independent of digests but shares `package.py`, so it lands second. The
comparison lands last and reuses both. The riskiest part is the comparison
reading an untrusted prior archive; it goes through the existing
`verify_archive` safety pipeline before any manifest field is used.

Review shape: one PR, DEEP, one commit per task. Each task leaves the
repository green.

## Constraints

- RFC-0076 D8 fixes the three behaviours, exit 2 for the refusal, and the first-party ban on `--force`.
- `packages/AGENTS.md`: version bump in both `version.py` and `pyproject.toml`; UTF-8 text I/O; no subprocess shell-outs.
- `packages/AGENTS.md` test table: engine behaviour tests live in `packages/agentbundle/tests/unit/` against fixtures; nothing there reads a repository path.
- Existing source-scan guards in `test_package_catalogue.py` forbid `subprocess`/git use and non-stdlib imports in `package.py`.
- `test_package_catalogue_install_flags_rejected` pins that the deprecated `package-catalogue` command rejects `--force`; that command stays unchanged.
- `tools/lint-catalogue-curation-guard.py` refuses a change under `packages/agentbundle/` without the `Engine-Change-RFC:` marker: every commit touching that tree carries the trailer `Engine-Change-RFC: RFC-0076`, and the T6 changelog entry carries the same line.
- `docs/product/AGENTS.md` owns the product changelog fragment procedure (`python3 tools/changelog.py new ...`).

## Construction tests

**Rule for every acceptance test:** it must fail when the mechanism it checks is bypassed. A planted input goes where no existing code path already neutralises it — verify messages format paths with `!r`, so an AC-0022 plant uses text that reaches a printed line unescaped, such as the prior `bundle` or a pack name; an injected failure goes on the path the criterion names — AC-0024 patches the prior-side derivation, not the producer's `unit_digest` call. Exact patch points are settled in EXECUTE under this rule.

**Integration tests:** none beyond per-task tests.

**Manual verification:** T7's adopter rehearsal.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface reference (CI) — `catalogue-ci-contract.md` and scaffold copy | T6 | edited section and exit-code table | `cmp` of both copies clean |
| Command reference — `docs/guides/reference/catalogue-commands.md` | T6 | refreshed flag table | flags equal `--help` |
| Archive reference — `docs/guides/reference/catalogue-archive.md` | T6 | manifest section | the spec's Archive reference closeout condition |
| Maintainer design — `packages/agentbundle/DESIGN.md` | T6 | staging sequence | matches shipped order |
| Release history — the surfaces in the spec's Release history row | T6 | changelog entry, README-pypi heading, fragment, roster pin | `tests/roster/test_okf_catalogue_discovery.py` green |
| Decision rationale — RFC-0076 OQ3 checklist | T6 | checked item linking the spec | link resolves |
| Product intent — intent Decomposition, workspace entry | T6 | edited intent and `workspace.toml` | `workspace-status` canonical |

## Design (LLD)

### Data & schema

- The unit digest rule is AC-0001. File digests already exist in `files[]`, so a unit digest is computable from `files[]` alone, which is what makes the prior-archive derivation in AC-0015 possible.
- A pack's unit path is `packs/<dir>`, where `<dir>` is the parent of the captured `packs/<dir>/pack.toml`. A profile's unit path is the file `profiles/<name>.toml`. Whether a unit path is a file or a directory is decided by whether `files[]` holds that exact path.
- Profile detection narrows from any `profiles/**/*.toml` to `len(parts) == 2`. Nested `.toml` files stay in `files[]`.
- Why AC-0004 keeps `schema` at `2`: `_check_manifest_schema` accepts only 1 or 2, so a bump would make every older CLI reject new archives, and no reader parses `packs[]` contents or `profiles`.
- AC-0018's shape check runs inside `_check_manifest_schema`, and `verify_archive` returns after it on any `CAT-V-ARC-019`, before `_check_all_manifest_digests`, `_check_no_undeclared_members` or any digest check reads an entry. CAT-V-ARC-018 and the comparison therefore only ever read well-typed entries.
- Excluded files (AC-0003) never reach `file_bytes`, because `_scan_content` prunes them; the digest needs no exclusion rule of its own.

Owned by: T1, T2.

### Interfaces & contracts

- `catalogue_tooling/archive.py` gains a public `unit_digest(file_digests: Mapping[str, str], unit_path: str) -> str | None` implementing AC-0001: `None` when the path has no member file. `package.py` imports it; `archive.py` must not import `package.py`.
- `archive.py` gains a public `read_verified_manifest(archive: Path) -> tuple[dict | None, VerifyResult]`. It refuses a path that is not a regular file (AC-0023), runs `verify_archive`, and only when that passes returns the parsed manifest through the same member checks and `_parse_manifest`. No extraction to disk. The handler wraps the whole prior-archive read and comparison in one `except Exception` that becomes a `CAT-PKG-001` diagnostic naming the exception type (AC-0024); this boundary catch is the backstop, and AC-0018's shape checks are what make the ordinary malformed cases produce specific codes.
- `PackageResult` gains `comparison: dict | None = None` (default-factory pattern as in `InitResult`). The refusal diagnostic uses code `CAT-PKG-002`; every other package failure keeps `CAT-PKG-001`. The handler maps `CAT-PKG-002` to exit 2 by code, never by message text.
- `package_source_flavour` gains `force: bool = False`, which the handler passes from `--force`, and `SourcePackageResult` gains `refused: bool = False` for the same exit-code mapping.
- `cli.py` adds `--force` (store_true), `--compare PATH` and `--format {table,json}` (default `table`, matching other catalogue commands) to `catalogue package` only, and builds that subparser with `allow_abbrev=False` (AC-0020). `--fo` and `--for` are already ambiguous with `--format`; `--forc` is not.
- The handler reads the three new attributes with `getattr(args, name, default)`, so callers that build a `Namespace` without them — `test_channel_with_flavor_source_exits_2` among them — keep working unchanged.
- Stderr lines for engine diagnostics are `<code>: <message>` (AC-0014). `CAT-V-ARC-018` and `CAT-V-ARC-019` messages name the offending entry's `name` when it is a string.
- JSON envelope keys follow `commands/catalogue_verify.py`; `diagnostics` items are `dataclasses.asdict(d)`. Output uses `json.dumps(..., indent=2, sort_keys=True)`. The JSON shapes are AC-0013 and AC-0021.

Owned by: T1, T2, T3, T4.

### State & control flow

Runtime packaging order:

1. Validate flag values. The handler rejects `--compare` or `--format json` with `--flavor source` (exit 2) before calling the engine.
2. If the archive exists and `force` is false, refuse with `CAT-PKG-002`.
3. `verify_catalogue(root)`.
4. If `compare` is set, `read_verified_manifest(prior)`; failure returns `CAT-PKG-001` with the verify diagnostics.
5. Scan, snapshot, build the manifest with unit digests.
6. If `compare` is set, compute the comparison from the new manifest and the prior manifest; an underivable prior unit returns `CAT-PKG-001`.
7. Stage the archive and sidecar and self-verify. Place the archive with one helper, `_place_archive(staged: Path, dest: Path, *, force: bool)`, shared by both flavours: with `force`, `os.replace`; without it, `os.link(staged, dest)` then unlink the staged file. `FileExistsError` removes the staged files and returns `CAT-PKG-002` (AC-0019). Where hard links are unsupported (`OSError` other than `FileExistsError`), copy the staged bytes into `open(dest, "xb")` with `shutil.copyfileobj`; `FileExistsError` there is handled the same way, and any other failure after the exclusive create removes only the file this run created. Then place the sidecar with `os.replace` and write the channel descriptor.

The handler renders output at one exit point: every return after argument parsing passes through the function that writes the JSON envelope or the stderr lines.

Steps 2, 4 and 6 all happen before the first write, which is what makes AC-0008, AC-0014, AC-0016 and AC-0023 hold. The self-verify hook `_verify_archive_fn` runs between staging and placement, which is the seam AC-0019's test uses to create the archive mid-run.

Source packaging adds the same step 2 check on `catalogue-source-<release>.tar.gz` before `release_dir.mkdir`, then writes its archive bytes to a `.tmp` beside the destination and places it with `_place_archive` before writing its sidecar and manifest.

Owned by: T3, T4.

### Behavior & rules

- Comparison keys units by name. Prior unit digests are always derived with `unit_digest` from the prior's verified `files[]`; a declared prior digest is never read. The prior path is the entry's `path` when present, else `packs/<name>` or `profiles/<name>.toml`. Pack directory names equal `[pack].name` by `catalogue lint` rule CAT-L004, which is what makes the fallback sound for archives built from linted catalogues; AC-0016 fails closed when it is not.
- A prior `profiles[]` item may be a plain string (name only) or an object.
- Human output: a header line naming the prior bundle and release, then `added`, `removed` and `changed` lines per unit kind, then the unchanged counts. A changed pack with equal versions carries `content changed, version unchanged`. Every stderr line built from prior-archive text — comparison lines, verification diagnostic messages and unit names — passes through one escaping helper before printing (AC-0022).
- A schema-1 prior without a `profiles` key compares as having no profiles.

Owned by: T4.

### Failure, edge cases & resilience

- `verify_archive` reads the manifest member without a per-member size cap; the archive-level expanded-size cap (2 GB) bounds it. `--compare` inherits that bound unchanged.
- `--force` with no existing archive behaves as a normal run.
- The spec's Accepted limits section lists the failure modes this design does not guard.

Owned by: T3, T4.

## Tasks

### T1: Manifest unit digests are produced and pinned

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/package.py, packages/agentbundle/agentbundle/catalogue_tooling/archive.py, packages/agentbundle/tests/unit/test_catalogue_unit_digests.py

**Tests:**
- AC-0001, AC-0002: the stub below, then exact `packs[]` and `profiles[]` values for a fixture with sibling packs `core` and `core2` (neither digest covers the other's files) and a profile set with a nested `profiles/sub/x.toml` that produces no entry; `unit_digest` returns `None` for a path with no member file.
- AC-0003: a fixture adds `packs/core/__pycache__/m.pyc`, `packs/core/.DS_Store`, `packs/_draft/pack.toml` and `profiles/_draft/x.toml`; every digest equals the clean run's.
- AC-0004: the produced manifest's `schema` equals `2`.

  ```stub path=packages/agentbundle/tests/unit/test_catalogue_unit_digests.py run="python -m pytest -q {path}" red-exit=1
  """Wave 5 unit digests in catalogue-manifest.json (AC-0001, AC-0002)."""

  from __future__ import annotations

  import hashlib
  import json
  import tarfile
  from pathlib import Path

  from agentbundle.catalogue_tooling.package import package_catalogue

  from tests.unit.test_catalogue_tooling_package import _make_catalogue


  def _manifest(output: Path) -> dict:
      archive = (
          output / "catalogues" / "engineering" / "releases" / "0.1.0"
          / "catalogue-0.1.0.tar.gz"
      )
      with tarfile.open(archive) as tf:
          member = tf.extractfile("catalogue-manifest.json")
          assert member is not None
          return json.loads(member.read().decode("utf-8"))


  def _expected(files: dict[str, bytes]) -> str:
      preimage = "".join(
          f"{hashlib.sha256(data).hexdigest()}  {rel}\n"
          for rel, data in sorted(files.items())
      )
      return "sha256:" + hashlib.sha256(preimage.encode("utf-8")).hexdigest()


  def test_pack_and_profile_entries_carry_path_and_digest(tmp_path: Path) -> None:
      root = _make_catalogue(tmp_path)
      output = tmp_path / "out"
      result = package_catalogue(
          root, "engineering", "0.1.0", "stable", output,
          generated_at="2026-01-01T00:00:00+00:00",
      )
      assert result.ok, result.diagnostics
      manifest = _manifest(output)
      pack_dir = root / "packs" / "core"
      pack_files = {
          p.relative_to(pack_dir).as_posix(): p.read_bytes()
          for p in pack_dir.rglob("*")
          if p.is_file()
      }
      assert manifest["packs"] == [{
          "name": "core",
          "version": "0.1.0",
          "path": "packs/core",
          "digest": _expected(pack_files),
      }]
      profile = root / "profiles" / "default.toml"
      assert manifest["profiles"] == [{
          "name": "default",
          "path": "profiles/default.toml",
          "digest": _expected({"default.toml": profile.read_bytes()}),
      }]
  ```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_unit_digests.py packages/agentbundle/tests/unit/test_catalogue_tooling_package.py packages/agentbundle/tests/unit/test_package_catalogue.py -q` passes.

### T2: Archive verification checks declared unit digests

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/archive.py, packages/agentbundle/tests/unit/test_catalogue_archive_unit_digests.py

**Tests:**
- AC-0005: the stub below, then a profile entry with a wrong digest and a pack entry whose `path` names no file each yield one `CAT-V-ARC-018`.
- AC-0006: a schema-2 manifest with `packs[]` entries of `{name, version}` and `profiles` as strings, and a schema-1 manifest with no `profiles` key, verify with neither code; a T1-produced archive verifies clean.
- AC-0018: one parametrized test over malformed manifests, one case per shape AC-0018 lists — top level a list; a `files[]` item a string; a `files[]` `sha256` a number; `profiles` an object; a `packs[]` item a string; a `packs[]` object without `name`; a pack `version` a number; a `profiles[]` item a number; a profile object without `name`; a `path` a number; a `digest` a number; a `digest` with no `path` — each yields `CAT-V-ARC-019` and `verify_archive` returns normally.

  ```stub path=packages/agentbundle/tests/unit/test_catalogue_archive_unit_digests.py run="python -m pytest -q {path}" red-exit=1
  """Wave 5 unit digest verification in verify_archive (AC-0005)."""

  from __future__ import annotations

  import hashlib
  import io
  import json
  import tarfile
  from pathlib import Path

  from agentbundle.catalogue_tooling.archive import verify_archive


  def _archive(tmp_path: Path, digest: str) -> Path:
      files = {
          "AGENTS.md": b"# AGENTS\n",
          "packs/core/pack.toml": b'[pack]\nname = "core"\nversion = "0.1.0"\n',
      }
      manifest = {
          "schema": 2,
          "bundle": "test",
          "release": "0.1.0",
          "generated_at": "2026-07-24T00:00:00Z",
          "source_revision": None,
          "files": [
              {"path": k, "sha256": hashlib.sha256(v).hexdigest()}
              for k, v in sorted(files.items())
          ],
          "packs": [{
              "name": "core", "version": "0.1.0", "path": "packs/core", "digest": digest,
          }],
          "profiles": [],
      }
      members = {**files, "catalogue-manifest.json": json.dumps(manifest).encode("utf-8")}
      path = tmp_path / "test.tar.gz"
      with tarfile.open(path, "w:gz") as tf:
          for name, data in sorted(members.items()):
              info = tarfile.TarInfo(name=name)
              info.size = len(data)
              tf.addfile(info, io.BytesIO(data))
      return path


  def test_mismatched_pack_digest_reports_cat_v_arc_018(tmp_path: Path) -> None:
      result = verify_archive(_archive(tmp_path, "sha256:" + "0" * 64))
      assert not result.ok
      assert "CAT-V-ARC-018" in {d.code for d in result.diagnostics}
  ```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_archive_unit_digests.py packages/agentbundle/tests/unit/test_catalogue_tooling_archive.py -q` passes.

**Approach:**
- AC-0018's checks sit in `_check_manifest_schema`, so packaging's staged self-verify enforces them on every new archive too.

### T3: Existing releases refuse with exit 2 unless forced

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/package.py, packages/agentbundle/agentbundle/catalogue_tooling/results.py, packages/agentbundle/agentbundle/commands/catalogue_package.py, packages/agentbundle/agentbundle/cli.py, packages/agentbundle/tests/unit/test_catalogue_package_refusal.py

**Tests:**
- AC-0007: the stub below, then the source flavour with an existing `catalogue-source-0.1.0.tar.gz`; both print the archive path on stderr (`capsys`).
- AC-0008: for both flavours, a sorted list of `(relative path, sha256)` for every file under `--output` is equal before and after the refused run.
- AC-0009: for both flavours, `--force` exits 0; the sidecar equals the SHA-256 of the archive bytes; the archived manifest's file digest for `packs/core/SKILL.md` matches the edited content; no `*.tmp` file exists under `--output`.
- AC-0019: `package_catalogue` with `_verify_archive_fn` replaced by a wrapper that writes `b"racer"` to the archive path and then calls the real `verify_archive`; the run returns `CAT-PKG-002`, `run` maps it to 2, the archive holds `b"racer"`, and no `*.tmp` exists under `--output`.
- AC-0019 (source flavour and the fallback): `_place_archive(staged, dest, force=False)` with `dest` already present raises the refusal and leaves `dest` and no staged file; the same with `os.link` monkeypatched to raise `PermissionError` takes the `open("xb")` path with the same result; with `os.link` patched to raise `PermissionError` and the copy patched to fail after the create, `dest` does not exist afterwards. For the source flavour end to end, `run` with `_place_archive` wrapped to write `b"racer"` to the destination before delegating returns 2, the archive holds `b"racer"`, and no `*.tmp` exists under `--output`.
- AC-0020: `_build_parser().parse_args([... "catalogue", "package", ..., "--forc"])` raises `SystemExit` with code 2.
- The deprecated-shim tests in `test_package_catalogue.py` and `test_channel_with_flavor_source_exits_2` stay green unchanged.

  ```stub path=packages/agentbundle/tests/unit/test_catalogue_package_refusal.py run="python -m pytest -q {path}" red-exit=1
  """Wave 5 same-version refusal (AC-0007)."""

  from __future__ import annotations

  from pathlib import Path
  from types import SimpleNamespace

  from agentbundle.commands.catalogue_package import run

  from tests.unit.test_catalogue_tooling_package import _make_catalogue


  def _make_args(root: Path, output: Path, **overrides: object) -> SimpleNamespace:
      values: dict[str, object] = {
          "root": str(root), "output": str(output), "bundle": "engineering",
          "release": "0.1.0", "channel": "stable", "source_revision": None,
          "minimum_agentbundle_version": None, "published_at": None,
          "flavor": "runtime", "force": False, "compare": None, "format": "table",
      }
      values.update(overrides)
      return SimpleNamespace(**values)


  def test_existing_runtime_archive_refuses_with_exit_2(tmp_path: Path) -> None:
      root = _make_catalogue(tmp_path)
      output = tmp_path / "out"
      archive = (
          output / "catalogues" / "engineering" / "releases" / "0.1.0"
          / "catalogue-0.1.0.tar.gz"
      )
      archive.parent.mkdir(parents=True)
      archive.write_bytes(b"existing")
      args = _make_args(
          root, output, flavor="runtime", force=False, compare=None, format="table",
      )
      assert run(args) == 2
  ```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_package_refusal.py packages/agentbundle/tests/unit/test_package_catalogue.py packages/agentbundle/tests/unit/test_catalogue_ci_contract.py packages/agentbundle/tests/unit/test_catalogue_init_cli_self_hosted.py -q` passes.

### T4: Release comparison in human and JSON output

**Depends on:** T1, T2, T3

**Touches:** packages/agentbundle/agentbundle/catalogue_tooling/package.py, packages/agentbundle/agentbundle/catalogue_tooling/archive.py, packages/agentbundle/agentbundle/catalogue_tooling/results.py, packages/agentbundle/agentbundle/commands/catalogue_package.py, packages/agentbundle/agentbundle/cli.py, packages/agentbundle/tests/unit/test_catalogue_package_compare.py

**Tests:**
- AC-0013: the stub below, then a fixture pair with one added pack, one removed pack, one changed pack, one unchanged pack, one added profile and one changed profile asserts the whole `comparison` object, and `json.loads` of the whole stdout succeeds with `--format json` and no `--compare`.
- AC-0011: the same fixture pair in table format; stderr contains each added, removed and changed name under its kind and the unchanged counts `1` (packs) and `0` (profiles).
- AC-0012: the changed pack keeps its version; its stderr line carries `content changed, version unchanged`.
- AC-0014: a prior archive with one `files[]` digest flipped makes `run` return 1, prints a stderr line starting `CAT-V-ARC-`, and leaves `--output` absent.
- AC-0015: a prior archive built by `_write_archive` with a hand-made pre-Wave-5 manifest (`{name, version}` packs, string profiles) over identical content reports both units unchanged.
- AC-0016: the same legacy prior with a pack named `core` whose files sit under `packs/other/` makes `run` return 1, names `core` on stderr, and leaves `--output` absent.
- AC-0017: `--flavor source` with `--compare x` and, separately, with `--format json` returns 2, leaves stdout empty and leaves `--output` absent.
- AC-0021: with `--format json`, three runs — a refusal (exit 2), a flipped-digest prior (exit 1) and an underivable prior unit (exit 1) — each leave stdout that `json.loads` parses to one object with `ok` false, the expected code in `diagnostics`, and no `comparison` key.
- AC-0022: four separate runs, each with one prior carrying `\x1b[2J` and `\n` in one place — a pack name shown in the comparison (prior verifies cleanly); the prior `bundle` shown in the comparison header (prior verifies cleanly); a pack name in an entry whose declared digest mismatches, which the `CAT-V-ARC-018` message names; and an underivable unit name (AC-0016). In each run stderr contains no `\x1b` character and the planted text appears escaped.
- AC-0024: with `unit_digest` monkeypatched to raise `RuntimeError`, `run` returns 1 without raising, stderr names `RuntimeError`, and `--output` is absent.
- AC-0023: `--compare` naming a missing path, a directory, and a file of random bytes each make `run` return 1 and leave `--output` absent.
- A schema-1 prior with no `profiles` key compares as having no profiles: every current profile reports added.

  ```stub path=packages/agentbundle/tests/unit/test_catalogue_package_compare.py run="python -m pytest -q {path}" red-exit=1
  """Wave 5 release comparison (AC-0013)."""

  from __future__ import annotations

  import json
  from pathlib import Path
  from types import SimpleNamespace

  import pytest
  from agentbundle.commands.catalogue_package import run

  from tests.unit.test_catalogue_tooling_package import _make_catalogue


  def _make_args(root: Path, output: Path, **overrides: object) -> SimpleNamespace:
      values: dict[str, object] = {
          "root": str(root), "output": str(output), "bundle": "engineering",
          "release": "0.1.0", "channel": "stable", "source_revision": None,
          "minimum_agentbundle_version": None, "published_at": None,
          "flavor": "runtime", "force": False, "compare": None, "format": "table",
      }
      values.update(overrides)
      return SimpleNamespace(**values)


  def test_compare_json_reports_changed_pack(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      root = _make_catalogue(tmp_path)
      prior_out = tmp_path / "prior"
      first = _make_args(
          root, prior_out, flavor="runtime", force=False, compare=None, format="table",
      )
      assert run(first) == 0
      prior = (
          prior_out / "catalogues" / "engineering" / "releases" / "0.1.0"
          / "catalogue-0.1.0.tar.gz"
      )
      (root / "packs" / "core" / "SKILL.md").write_text(
          "# skill changed\n", encoding="utf-8", newline="\n"
      )
      capsys.readouterr()
      second = _make_args(
          root, tmp_path / "next", release="0.2.0", flavor="runtime",
          force=False, compare=str(prior), format="json",
      )
      assert run(second) == 0
      payload = json.loads(capsys.readouterr().out)
      changed = payload["comparison"]["packs"]["changed"]
      assert [item["name"] for item in changed] == ["core"]
      assert changed[0]["version"] == {"from": "0.1.0", "to": "0.1.0"}
  ```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_package_compare.py packages/agentbundle/tests/unit/test_catalogue_package_refusal.py packages/agentbundle/tests/unit/test_catalogue_tooling_package.py -q` passes.

### T5: First-party CI never forces a release

**Depends on:** none

**Touches:** tools/test_catalogue_tooling_rewire.py

**Tests:**
- AC-0010: no stub (goal-based). A new test reads `Makefile` and every `.github/workflows/*.yml`, joins backslash-continued lines, collapses whitespace runs, and asserts no logical line containing `catalogue package` contains `--force`. Its predicate is a module-level function that a second test drives with three planted texts — `agentbundle catalogue package --force` on one line, `--force` on a continuation line after `catalogue package \`, and a break between `catalogue \` and an indented `package --force` — and asserts the predicate reports all three.

**Done when:** `python3 -m pytest tools/test_catalogue_tooling_rewire.py -q` passes.

### T6: Durable outputs describe the shipped contract

**Depends on:** T1, T2, T3, T4, T5

**Touches:** guides/_shared/reference/catalogue-ci-contract.md, packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-ci-contract.md, docs/guides/reference/catalogue-commands.md, docs/guides/reference/catalogue-archive.md, packages/agentbundle/DESIGN.md, packages/agentbundle/CHANGELOG.md, packages/agentbundle/README-pypi.md, packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml, docs/product/changelog.d/*.md, tests/roster/test_okf_catalogue_discovery.py, docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md, docs/product/intents/catalogue-wave5-release-integrity.md, workspace.toml

**Tests:**
- No stub (goal-based). Every Durable Outputs row in the spec reaches its closeout condition.

**Done when:** `cmp` of the two `catalogue-ci-contract.md` copies is clean, `make lint-ruff lint-mypy` passes, and `python3 -m pytest tools/test_catalogue_tooling_docs.py tools/test_changelog.py packages/agentbundle/tests/unit/test_version.py tests/roster/test_okf_catalogue_discovery.py -q` passes.

### T7: Adopter rehearsal on the built CLI

**Depends on:** T6

**Tests:**
- No stub (manual QA). In a temporary directory outside the repository, scaffold a catalogue with `agentbundle catalogue init`, then: package `0.1.0`; edit one pack's skill without a version bump; package `0.2.0 --compare` the first archive in table and JSON form; re-package `0.2.0` (expect exit 2); re-package with `--force` (expect 0); `catalogue verify --archive` the result with its sidecar (expect 0). Record each command, exit code and the comparison output in the verification ledger.

**Done when:** every command's observed exit code matches the expected one in the ledger, and the comparison lists the edited pack with the `content changed, version unchanged` marker.

## Rollout

- **Delivery:** ships in the agentbundle release named in the spec's Release history row. The exit-code change, the abbreviation rejection and the `profiles` shape change are breaking for some callers; the changelog says so. Archives from older CLIs still verify (AC-0006) and compare (AC-0015), within the spec's Accepted limits.
- **Infrastructure, external systems:** none.
- **Deployment sequencing:** none; old CLIs accept new manifests because `schema` stays 2.

## Risks

- A downstream script that parses `profiles` as strings breaks. None exists in this repository; the changelog names the shape change.
- The publish workflow's fresh output directory means the refusal never fires there; the guard in T5 is what enforces the `--force` ban.

## Changelog

- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
