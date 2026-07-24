# Plan: Package Catalogue Command

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four tasks building from pure-logic helpers to CLI integration. First, a content-scan and pre-package-validation helper that walks the allowlisted paths, rejects symlinks and path-traversal violations, and validates each `pack.toml` and profile `.toml` before any output is written. Second, the deterministic archive builder: a two-pass algorithm that computes file SHA-256 digests on the first pass, generates `catalogue-manifest.json`, then writes the final sorted, metadata-normalized `.tar.gz` with the gzip header mtime zeroed. Third, the channel descriptor writer — small and self-contained; depends on neither the archive builder nor the validator. Fourth, the `package_catalogue.py` command module that wires all helpers, plus the subcommand registration in `cli.py`.

## Constraints

- RFC-0072 D5: required/optional flags, output layout, content allowlist, deterministic archive properties, `catalogue-manifest.json` schema.
- spec/https-catalogue-channels: channel descriptor schema must match what the installer expects; `artifact` is a relative URL.
- RFC-0031 Principle 3: stdlib-only, no new runtime dependency.
- Security: no git shell-out; no credentials in output; symlinks and traversal rejected before any write.

## Construction tests

**Integration test:** `test_package_catalogue_end_to_end` — run `package_catalogue.run(args)` against a local fixture catalogue (one valid pack, `profiles/` directory, `README.md`, `LICENSE`); assert all three output files created; read and validate the channel descriptor JSON; extract and parse `catalogue-manifest.json` from the archive; verify `sha256` field in descriptor matches sidecar content; verify `files` list contains expected entries with correct SHA-256 values. This test spans T1–T4 and is the canonical AC3/AC8 verification.

## Design (LLD)

### Design decisions

- **Single file-read per content file:** all included files are read once by `_read_content_files` (returns `{posix_relative_path: bytes}`). The same in-memory bytes are passed to both `_compute_file_digests` (for `catalogue-manifest.json` digest values) and `_build_archive` (for archive member data). This guarantees that the SHA-256 values in the manifest match the bytes actually stored in the archive; two independent reads could disagree if a file changed between them.
- **Two-pass archive build:** `_read_content_files` reads all files (pass one), `_generate_manifest` builds the manifest JSON with those digests, `_build_archive` assembles the archive (pass two using the already-read bytes + manifest). This avoids the chicken-and-egg problem (the manifest needs digests; the archive needs the manifest) without streaming complexity. `catalogue-manifest.json` is not listed in its own `files` array — that would be a circular self-reference and would require a fixed-point computation.
- **Explicit raise in `_build_archive`, not `assert`:** path safety checks (no `..`, no leading `/`) in `_build_archive` use `if`/`raise ValueError`, not `assert`. Python's `-O` flag strips `assert` statements, which would silently disable a security invariant. The test `test_build_archive_rejects_traversal_member_name` directly passes a crafted `".."` member name to `_build_archive` (bypassing the pre-package validator) and asserts the explicit exception is raised.
- **`gzip.GzipFile` with `mtime=0`, not `gzip.open`:** `gzip.open` does not expose the `mtime` parameter; it uses the current time by default, breaking reproducibility. `gzip.GzipFile(fileobj=buf, mode="wb", mtime=0)` writes the gzip header with the 4-byte mtime field zeroed. The tarfile is written into a `BytesIO` buffer wrapped in a `gzip.GzipFile`; the complete compressed bytes are returned from `_build_archive`.
- **`tarfile.GNU_FORMAT`, not `DEFAULT_FORMAT` (PAX):** Python 3.8+ defaults to `tarfile.PAX_FORMAT`. PAX writes toolchain-dependent PAX extended headers for member names and timestamps, producing archives that differ across Python versions even with all metadata normalized. `tarfile.GNU_FORMAT` avoids PAX headers: GNU format handles long paths (> 100 chars — beyond USTAR's limit) via `././@LongLink` entries, which are stable across Python versions. Pinning the format is load-bearing for the byte-identical cross-toolchain guarantee in AC8.
- **Member-by-member `TarInfo` + `addfile`, not `tarfile.add`:** `tarfile.add()` inherits on-disk uid, gid, mtime, and mode; reproducibility requires constructing a `TarInfo` for each member with hardcoded zero metadata and normalized mode. Only regular file members are written (no explicit directory members); the archive hierarchy is implied by member paths, which is sufficient for standard tar extraction.
- **Content scan returns regular files only; validation also walks for symlinks:** `_scan_content` returns only non-symlink regular files (using `p.is_file() and not p.is_symlink()`). `_validate_content` performs a separate recursive walk of each allowlisted directory to catch symlinks to directories or other symlink-shaped entries that `_scan_content` would silently skip. This keeps the two responsibilities separate.
- **In-memory archive assembly:** the entire archive is assembled in a `BytesIO` buffer before writing to disk. This allows computing the SHA-256 of the complete bytes before any file is written, enabling the atomic refuse-to-overwrite check. For typical catalogue sizes this is acceptable; a future spec can add streaming output if needed.
- **`load_pack_toml` from `agentbundle.config` for pack metadata:** single source of truth for `pack.toml` parsing; already imported by the install and upgrade paths. Pack name: `pack_data["pack"]["name"]`; pack version: `pack_data["pack"]["version"]`. Missing keys are surfaced as pre-package validation errors, not runtime crashes.

### Data & schema

`catalogue-manifest.json` (embedded in archive):
```json
{
  "schema": 1,
  "bundle": "<str>",
  "release": "<str>",
  "source_revision": "<str | null>",
  "generated_at": "<ISO-8601 UTC>",
  "files": [
    {"path": "<relative posix path>", "sha256": "<64 lowercase hex>"}
  ],
  "packs": [
    {"name": "<str>", "version": "<str>"}
  ]
}
```
`catalogue-manifest.json` is included in the archive but is not listed in its own `files` array.

Channel descriptor JSON (written to `channels/<channel>.json`):
```json
{
  "schema": 1,
  "kind": "agentbundle-catalogue",
  "bundle": "<str>",
  "channel": "<str>",
  "release": "<str>",
  "artifact": "../releases/<release>/catalogue-<release>.tar.gz",
  "sha256": "<64 lowercase hex>",
  "published_at": "<ISO-8601>",
  "source_revision": "<str, when --source-revision provided>",
  "minimum_agentbundle_version": "<semver, when --minimum-agentbundle-version provided>"
}
```
Optional fields (`source_revision`, `minimum_agentbundle_version`) are omitted when not provided.

### Interfaces & contracts

- `_scan_content(root: Path) -> list[Path]` — returns sorted list of absolute `Path` objects of regular (non-symlink) files from the allowlist. Does not walk symlinked directories.
- `_validate_content(root: Path, content_paths: list[Path]) -> str | None` — returns an error string on any violation (symlink in allowlisted paths, hard link, path traversal outside root, invalid `pack.toml`, missing pack name/version, invalid profile TOML); returns `None` on success.
- `_read_content_files(root: Path, paths: list[Path]) -> dict[str, bytes]` — reads all files at once; returns `{posix_relative_path: bytes}`. Single read per file; bytes reused for both digest and archive.
- `_compute_file_digests(file_bytes: dict[str, bytes]) -> dict[str, str]` — returns `{posix_relative_path: sha256_hex}` computed from the in-memory bytes. Does not read from disk. Does not include `catalogue-manifest.json`.
- `_generate_manifest(*, bundle: str, release: str, source_revision: str | None, generated_at: str, file_digests: dict[str, str], packs_metadata: list[dict]) -> bytes` — returns UTF-8 JSON bytes.
- `_build_archive(file_bytes: dict[str, bytes], manifest_bytes: bytes) -> bytes` — returns complete deterministic `.tar.gz` bytes. Takes the already-read file bytes dict, not file paths.
- `_write_channel_descriptor(path: Path, *, bundle: str, channel: str, release: str, sha256_hex: str, published_at: str, source_revision: str | None, minimum_agentbundle_version: str | None) -> None` — writes the channel descriptor JSON to `path`, creating parent directories.
- `run(args) -> int` — command entry point, dispatched by `cli.py`.

### Behavior & rules

`run()` execution order:
1. Resolve `root = Path(args.root).resolve()`, `output = Path(args.output).resolve()`. Validate `args.bundle`, `args.release`, and `args.channel`: for each, check `re.fullmatch(r"[A-Za-z0-9\-._]+", value) and value not in (".", "..") and ".." not in value.split(".")` — if any fails, print error to stderr naming the flag and value, return 1. No output is written. (Note: `..` passes the `fullmatch` since `.` is in the charset; the explicit `.`/`..` check is required.)
2. Compute `archive_path = output / "catalogues" / bundle / "releases" / release / f"catalogue-{release}.tar.gz"`.
3. **Refuse-to-overwrite check:** if `archive_path.exists()`, print error to stderr naming the path, return 1. No output is written.
4. Scan content: `content_paths = _scan_content(root)`.
5. Validate: `err = _validate_content(root, content_paths)` — if non-None, print to stderr, return 1.
6. **Read all file bytes once:** `file_bytes = _read_content_files(root, content_paths)`.
7. Compute file digests: `digests = _compute_file_digests(file_bytes)` (uses bytes already in memory).
8. Extract pack metadata: iterate `file_bytes` for keys matching `"packs/<name>/pack.toml"` where `<name>` is exactly one path segment (key contains exactly two forward slashes: one after `"packs"` and one before `"pack.toml"`). Parse each with `tomllib.loads(file_bytes[key].decode("utf-8"))` — uses the already-read bytes, not a second disk read. Extract `pack_data["pack"]["name"]` and `pack_data["pack"]["version"]`. This enumeration matches exactly the same set that `_validate_content` validated (direct subdirectory `pack.toml` files only), preventing a nested `packs/core/example/pack.toml` from reaching an unhandled `KeyError`.
9. Determine `generated_at`: `val = os.environ.get("SOURCE_DATE_EPOCH")`. If `val` is `None` or `val == ""` → use `datetime.now(timezone.utc).replace(microsecond=0).isoformat()` (empty string is treated as unset, consistent with common reproducible-builds convention). If `val` is non-empty and not a valid integer → `print(f"error: SOURCE_DATE_EPOCH is not a valid integer: {val!r}", file=sys.stderr); return 1`. Otherwise → `datetime.fromtimestamp(int(val), tz=timezone.utc).replace(microsecond=0).isoformat()`. Both non-error paths produce second-level precision, no microseconds.
9b. Determine `published_at`: `published_at = args.published_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()`. Passed to `_write_channel_descriptor`.
10. Generate manifest bytes: `_generate_manifest(...)`.
11. Build archive bytes: `_build_archive(file_bytes, manifest_bytes)` (reuses already-read bytes).
12. Compute `sha256_hex = hashlib.sha256(archive_bytes).hexdigest()`.
13. Create output directories: `archive_path.parent.mkdir(parents=True, exist_ok=True)` and `(output / "catalogues" / bundle / "channels").mkdir(parents=True, exist_ok=True)`.
14. Write sidecar to `archive_path.parent / (archive_path.name + ".sha256")`. Content: `sha256_hex + "\n"`. (Written before the archive so a failure here leaves no archive to trigger a subsequent refuse-to-overwrite.)
15. Write channel descriptor: `_write_channel_descriptor(output / "catalogues" / bundle / "channels" / f"{channel}.json", ...)`.
16. Write archive to `archive_path` **last**. This ordering is intentional: writing the archive after the sidecar and descriptor ensures that if either write fails, no archive exists on disk, so the subsequent refuse-to-overwrite check (step 3) does not self-lock re-runs. The sidecar and descriptor are mutable outputs with no refuse-to-overwrite guard and are safely overwritten on re-run.

`_build_archive` algorithm:
1. Build `(member_name, data)` list from `file_bytes` dict items. Append `("catalogue-manifest.json", manifest_bytes)`.
2. Sort list by `member_name` lexicographically.
3. Open `buf = io.BytesIO()`. Wrap: `gz = gzip.GzipFile(fileobj=buf, mode="wb", mtime=0)`. Open tarfile: `tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT)`. `GNU_FORMAT` is pinned explicitly — PAX format (`DEFAULT_FORMAT`) emits toolchain-dependent PAX extended headers that vary across Python versions, breaking byte-identical archives across toolchains. GNU format handles long member paths (> 100 chars) via `././@LongLink` entries without PAX headers.
4. For each `(member_name, data)`:
   - **Explicit path safety check (not assert):** `if member_name.startswith("/") or ".." in member_name.split("/") or (len(member_name) >= 2 and member_name[1] == ":"): raise ValueError(f"unsafe archive member name: {member_name!r}")`.
   - Construct `info = tarfile.TarInfo(name=member_name)`; set `info.type = tarfile.REGTYPE`, `info.size = len(data)`, `info.uid = 0`, `info.gid = 0`, `info.mtime = 0`, `info.mode = 0o644`; call `tar.addfile(info, io.BytesIO(data))`.
5. `tar.close()`, `gz.close()`. Return `buf.getvalue()`.

### Failure, edge cases & resilience

- `packs/` absent from `--root`: `_scan_content` returns a list with no pack entries; `_validate_content` checks that `root / "packs"` is a directory and returns an error when it is absent. Failure before any output.
- `profiles/` or `docs/contracts/` absent: `_scan_content` skips absent allowlisted directories silently. No error.
- `README.md` or `LICENSE` absent at root: skipped silently. No error.
- Hard-link detection: `p.stat().st_nlink > 1` on a regular file (not symlink) indicates a hard link on POSIX. `_validate_content` applies this check only to `p.is_file() and not p.is_symlink()` entries from `_scan_content`. On macOS and Linux, directories have `st_nlink >= 2` (the `.` entry plus the directory's own name); regular files with `st_nlink == 1` are non-hard-linked; `st_nlink > 1` is the hard-link signal for regular files.
- `SOURCE_DATE_EPOCH` malformed (non-empty, non-integer): `val = os.environ.get("SOURCE_DATE_EPOCH"); if val:` try `int(val)`, catch `ValueError` → exit non-zero with error naming the invalid value. An empty `SOURCE_DATE_EPOCH=""` (`not val`) is treated as unset — falls back to `datetime.now(timezone.utc)`. Consistent with step 9 above.
- Refuse-to-overwrite fires before archive assembly (step 3 above), so no computation is wasted on a failing run.
- Write order prevents self-locking for sidecar/descriptor failures: the archive is written last (step 16). A failure at step 14 (sidecar) or 15 (descriptor) leaves no archive on disk; subsequent re-runs pass the step-3 check and overwrite the mutable sidecar and descriptor cleanly. A failure or crash during the archive write at step 16 can leave a partial archive file that triggers the refuse-to-overwrite check on re-runs; recovery requires manually deleting the partial file. This limitation is accepted for the first implementation; a future PR can add atomic write (temp path + `os.replace`) to eliminate this residual case.

## Tasks

### T1: Implement `_scan_content` and `_validate_content`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/commands/package_catalogue.py` (new file)

**Tests (TDD — stub before production code):**
- `test_scan_content_includes_allowlisted_files`: fixture tree with files in `packs/`, `profiles/`, `docs/contracts/`, `README.md`, `LICENSE`, and also `build/`, `tests/`, `.git/`; assert returned paths include only the allowlisted regular files; assert `build/`, `tests/`, `.git/` entries absent. Verifies AC4.
- `test_scan_content_excludes_symlinks`: fixture with a symlink inside `packs/core/`; assert the symlink path is absent from the returned list.
- `test_scan_content_returns_sorted_paths`: fixture with files in multiple allowlisted directories; assert returned list equals `sorted(returned_list)`.
- `test_scan_content_absent_optional_dir`: fixture with `packs/` only (no `profiles/` or `docs/contracts/`); assert succeeds and returns only `packs/` files.
- `test_validate_content_symlink_file_rejected`: fixture with a symlink to a file inside `packs/core/`; assert `_validate_content` returns a non-None string containing the symlink path.
- `test_validate_content_symlink_dir_rejected`: fixture with a symlinked subdirectory inside `packs/core/` (e.g. `packs/core/subdir` is a symlink to a real directory); assert `_validate_content` returns a non-None string. Verifies the separate directory-walk catches symlinked directories specifically.
- `test_validate_content_top_level_dir_symlink_rejected`: fixture where `packs/` at `--root` is a symlink to an actual directory; assert `_validate_content` returns a non-None string naming the path. Verifies AC16 top-level-dir clause.
- `test_validate_content_intermediate_dir_symlink_rejected`: fixture where `docs/` at `--root` is a symlink to an actual directory containing a `contracts/` subdirectory; assert `_validate_content` returns a non-None string naming `docs/`. Verifies AC16 intermediate-dir clause.
- `test_validate_content_root_file_symlink_rejected`: fixture where `README.md` at `--root` is a symlink; assert `_validate_content` returns a non-None string naming the path. Verifies AC16 root-file clause.
- `test_validate_content_hardlink_rejected` (POSIX only, `@pytest.mark.skipif(sys.platform == "win32", ...)`): fixture with a hard link inside `packs/core/` (created via `os.link`); assert `_validate_content` returns a non-None string naming the path. Verifies AC29.
- `test_validate_content_traversal_rejected`: mock a `content_path` whose `resolve()` returns a path outside `root` (intentionally synthetic — a real regular non-symlink file under `root` cannot resolve outside it; this guard is belt-and-suspenders defense-in-depth); assert returns error naming the path.
- `test_validate_content_invalid_pack_toml_rejected`: fixture with a non-TOML file at `packs/bad/pack.toml`; assert returns error naming the pack directory.
- `test_validate_content_pack_toml_missing_version_rejected`: fixture with a `pack.toml` lacking the `version` key; assert returns error.
- `test_validate_content_invalid_profile_toml_rejected`: fixture with a non-TOML `.toml` file at `profiles/bad.toml`; assert returns error naming the file.
- `test_validate_content_valid_catalogue_returns_none`: fixture with one valid pack and a valid profile; assert `_validate_content` returns `None`.
- `test_validate_content_missing_packs_dir_rejected`: fixture root with no `packs/` directory; assert returns error.

**Approach:**
- `_scan_content(root: Path) -> list[Path]`:
  - Allowlisted dirs: `[root / "packs", root / "profiles", root / "docs" / "contracts"]`.
  - Allowlisted roots: `[root / "README.md", root / "LICENSE"]`.
  - For each allowlisted dir that `is_dir()` and `not is_symlink()`: walk recursively (do not follow symlinks — use `p.iterdir()` recursively or `os.walk(top, followlinks=False)`); collect `p` where `p.is_file() and not p.is_symlink()`.
  - For each allowlisted root path: include if `p.exists() and p.is_file() and not p.is_symlink()`.
  - Return `sorted(collected, key=lambda p: p.relative_to(root).as_posix())`.
- `_validate_content(root: Path, content_paths: list[Path]) -> str | None`:
  - **Top-level and intermediate directory symlink check first:** for each of `[root / "packs", root / "profiles", root / "docs", root / "docs" / "contracts"]`: if `p.exists() and p.is_symlink()` → return error naming the path. Including `root / "docs"` prevents a symlinked intermediate directory from passing the leaf check undetected. This check runs before `is_dir()` so a symlink to a non-directory reports a symlink error (not a misleading "missing packs" error). Verifies AC16 top-level-dir and intermediate-dir clauses.
  - Check `(root / "packs").is_dir()` — return error if absent. (Runs after the symlink check, so `packs/` that is a symlink is caught above before reaching this check.)
  - **Root-level file symlink check:** for each of `[root / "README.md", root / "LICENSE"]`: if `p.exists() and p.is_symlink()` → return error naming the path. Verifies AC16 root-file clause.
  - **Allowlisted directory symlink walk:** for each allowlisted dir (`packs/`, `profiles/`, `docs/contracts/`) where `is_dir() and not is_symlink()`: walk recursively using `os.walk(top, followlinks=False)` and iterate entries in `dirs` and `files`; for each entry, check `os.path.islink(full_path)` → return error naming the path. Using `os.walk` with `followlinks=False` means symlinked subdirectories appear in `dirs` and `os.path.islink` detects them.
  - For each path in `content_paths`: check `path.stat().st_nlink > 1` (regular file hard link on POSIX) → return error naming the path.
  - For each path in `content_paths`: `try: path.resolve().relative_to(root) except ValueError: return error`. (Belt-and-suspenders defense-in-depth. A symlinked intermediate directory — e.g. `root/docs` → external path — is the primary real-input trigger; the explicit symlink checks above close this path before the traversal guard is reached. For a genuine non-symlink regular file under root the guard is unreachable. The test is intentionally synthetic (mock) since the intermediate-dir symlink case is now caught earlier — see Risks.)
  - For each direct subdirectory of `root / "packs"` that `is_dir() and not is_symlink()`: attempt `load_pack_toml(pack_dir / "pack.toml")`; catch `ConfigError` → return error. Then check `pack_data["pack"]["name"]` and `pack_data["pack"]["version"]` exist; catch `KeyError` → return error.
  - For each `.toml` file under `root / "profiles"` (if dir exists): attempt `tomllib.loads(f.read_text("utf-8"))`; catch `tomllib.TOMLDecodeError` → return error.
  - Return `None` on success.

**Done when:** all T1 tests above pass; `_scan_content` and `_validate_content` are defined in `package_catalogue.py`.

---

### T2: Implement `_compute_file_digests`, `_generate_manifest`, and `_build_archive`

**Depends on:** T1 (shares file)

**Touches:** `packages/agentbundle/agentbundle/commands/package_catalogue.py`

**Tests (TDD):**
- `test_compute_file_digests_values`: create two files with known bytes; build a `{posix_path: bytes}` dict; assert `_compute_file_digests` returns `{posix_path: sha256_hex}` with values matching `hashlib.sha256(file_bytes).hexdigest()`. (AC12's single-read contract — same bytes in manifest and archive — is verified end-to-end by `test_package_catalogue_manifest_digest_matches_archived_bytes` in T4.)
- `test_compute_file_digests_keys_are_posix_relative`: assert all keys use forward slashes and are relative to root (no leading slash).
- `test_read_content_files_single_read`: confirm `_read_content_files` returns a dict with the same keys as `_scan_content` produces for the same fixture, and each value is the file's bytes. (This test documents the single-read contract; the AC12 manifest-archive consistency test in T4 verifies the end-to-end behavior.)
- `test_generate_manifest_required_fields`: call `_generate_manifest` with known inputs; parse output JSON; assert `schema == 1`, `bundle`, `release`, `source_revision`, `generated_at`, `files`, and `packs` all present.
- `test_generate_manifest_source_revision_null`: call with `source_revision=None`; parse JSON; assert `"source_revision": null`.
- `test_generate_manifest_source_revision_string`: call with `source_revision="abc123"`; parse JSON; assert `"source_revision": "abc123"`.
- `test_generate_manifest_files_sorted`: call with files in unsorted order; parse JSON; assert `files` list is sorted by `path`.
- `test_generate_manifest_packs_sorted`: call with packs in unsorted order; parse JSON; assert `packs` list is sorted by `name`.
- `test_generate_manifest_no_self_reference`: parse `files`; assert no entry has `path == "catalogue-manifest.json"`. Verifies AC12.
- `test_build_archive_deterministic`: call `_build_archive` twice with identical inputs; assert both return identical bytes. Verifies AC8.
- `test_build_archive_gzip_mtime_zero`: call `_build_archive`; assert bytes at offset 4–7 of the result are `b'\x00\x00\x00\x00'`. Verifies AC7.
- `test_build_archive_members_sorted`: open result as tarfile; extract member names; assert names equal `sorted(names)`. Verifies AC5.
- `test_build_archive_member_metadata_files`: open result as tarfile; for each member, assert `uid == 0`, `gid == 0`, `mtime == 0`, `mode == 0o644`. Verifies AC6.
- `test_build_archive_contains_manifest`: open result as tarfile; assert member named `"catalogue-manifest.json"` exists and content parses as JSON with `schema == 1`. Verifies AC11.
- `test_build_archive_rejects_traversal_member_name`: call `_build_archive({"../evil": b"x"}, b"{}")` directly; assert `ValueError` is raised. Verifies AC22 (explicit raise, not assert).
- `test_build_archive_rejects_absolute_member_name`: call `_build_archive({"/etc/passwd": b"x"}, b"{}")` directly; assert `ValueError` is raised. Verifies AC22.
- `test_build_archive_rejects_drive_letter_member_name`: call `_build_archive({"C:evil": b"x"}, b"{}")` directly; assert `ValueError` is raised. Verifies AC22 Windows drive-letter clause.
- `test_generate_manifest_accepts_fixed_generated_at`: call `_generate_manifest` with `generated_at="2023-11-14T22:13:20+00:00"`; parse JSON; assert `generated_at == "2023-11-14T22:13:20+00:00"`. (`_generate_manifest` takes `generated_at` as a pre-computed string; SOURCE_DATE_EPOCH parsing happens in `run()` and is tested in T4.)

**Approach:**
- `_read_content_files(root, paths) -> dict[str, bytes]`:
  - For each `p` in `paths`: `data = p.read_bytes()`; key = `p.relative_to(root).as_posix()`. Return the dict.
- `_compute_file_digests(file_bytes: dict[str, bytes]) -> dict[str, str]`:
  - For each `(key, data)` in `file_bytes.items()`: compute `hashlib.sha256(data).hexdigest()`; return `{key: digest}`.
- `_generate_manifest(*, bundle, release, source_revision, generated_at, file_digests, packs_metadata) -> bytes`:
  - Build dict per schema; `files = sorted([{"path": k, "sha256": v} for k, v in file_digests.items()], key=lambda x: x["path"])`; `packs = sorted(packs_metadata, key=lambda x: x["name"])`.
  - Return `json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")` — `indent=2` for human readability (consistent with other JSON outputs in the codebase); `ensure_ascii=False` preserves non-ASCII pack names. This serialization form is pinned; do not vary between invocations.
- `_build_archive(file_bytes: dict[str, bytes], manifest_bytes: bytes) -> bytes`:
  - Build `members = list(file_bytes.items())` (already `{posix_relative_path: bytes}`).
  - Append `("catalogue-manifest.json", manifest_bytes)`.
  - Sort `members` by member name.
  - For each `(name, data)`: explicit path safety check per `_build_archive` algorithm above (raises `ValueError` — not assert).
  - `buf = io.BytesIO()`. Open `gz = gzip.GzipFile(fileobj=buf, mode="wb", mtime=0)`. Open `tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT)`.
  - For each `(name, data)`: `info = tarfile.TarInfo(name=name)`; `info.type = tarfile.REGTYPE`; `info.size = len(data)`; `info.uid = 0`; `info.gid = 0`; `info.mtime = 0`; `info.mode = 0o644`; `tar.addfile(info, io.BytesIO(data))`.
  - `tar.close()`, `gz.close()`. Return `buf.getvalue()`.

**Done when:** all T2 tests above pass; `_build_archive` returns deterministic gzip-compressed tar bytes.

---

### T3: Implement `_write_channel_descriptor`

**Depends on:** none (independent of T1 and T2)

**Touches:** `packages/agentbundle/agentbundle/commands/package_catalogue.py`

**Tests (TDD):**
- `test_write_channel_descriptor_required_fields`: call with all required args; parse output JSON; assert all required fields present with correct values; assert `schema == 1`; assert `kind == "agentbundle-catalogue"`.
- `test_write_channel_descriptor_relative_artifact_url`: assert `descriptor["artifact"] == "../releases/0.13.0/catalogue-0.13.0.tar.gz"` when `release == "0.13.0"`. Verifies AC20.
- `test_write_channel_descriptor_optional_fields_absent`: call without `source_revision` and `minimum_agentbundle_version`; assert both keys absent from JSON. Verifies AC19.
- `test_write_channel_descriptor_optional_fields_present`: call with both optional args; assert both appear in JSON with correct values.
- `test_write_channel_descriptor_creates_parent_dirs`: pass a path whose parent dirs don't exist; assert `_write_channel_descriptor` creates them and writes the file. Verifies AC26.
- `test_write_channel_descriptor_sha256_matches_sidecar`: assert `descriptor["sha256"] == sha256_hex` (the value passed as argument). Verifies AC21.

**Approach:**
- `_write_channel_descriptor(path, *, bundle, channel, release, sha256_hex, published_at, source_revision, minimum_agentbundle_version) -> None`:
  - Build required fields dict.
  - `artifact = f"../releases/{release}/catalogue-{release}.tar.gz"`.
  - Add optional fields: `if source_revision is not None: descriptor["source_revision"] = source_revision`; same for `minimum_agentbundle_version`.
  - `path.parent.mkdir(parents=True, exist_ok=True)`.
  - `path.write_text(json.dumps(descriptor, indent=2, ensure_ascii=False), encoding="utf-8")`.

**Done when:** all T3 tests above pass; `_write_channel_descriptor` produces a channel descriptor with a relative `artifact` URL.

---

### T4: Implement `run()` in `package_catalogue.py` and register subcommand in `cli.py`

**Depends on:** T1, T2, T3

**Touches:** `packages/agentbundle/agentbundle/commands/package_catalogue.py`, `packages/agentbundle/agentbundle/cli.py`

**Tests:**
- `test_package_catalogue_end_to_end` (integration): run `package_catalogue.run(args)` against a fixture catalogue that includes both allowlisted content (one valid pack with `pack.toml`, one valid profile, `README.md`, `LICENSE`) and excluded directories (`build/`, `tests/`, `.git/`); assert all three output files created at the exact expected paths; collect all files written under `--output` using `[p for p in output_dir.rglob("*") if p.is_file()]` and assert the count is exactly 3 (no spurious extras); open archive and extract member names; assert allowlisted entries present and all entries from `build/`, `tests/`, `.git/` absent; parse channel descriptor; assert all required fields; parse `catalogue-manifest.json`; assert `files` list contains expected entries with correct SHA-256 values; assert `packs` list contains the fixture pack. Verifies AC3, AC4, AC11, AC19, AC20.
- `test_package_catalogue_refuse_overwrite` (integration): pre-create the archive path with known bytes; run the command; assert exit code 1; assert error message names the path; assert archive file content unchanged; assert sidecar and descriptor absent. Verifies AC18.
- `test_package_catalogue_archive_reproducible` (integration): run twice with `SOURCE_DATE_EPOCH` fixed; assert `hashlib.sha256(archive_bytes_1) == hashlib.sha256(archive_bytes_2)`. Verifies AC8.
- `test_package_catalogue_sidecar_format` (integration): run; read sidecar; assert content equals `hashlib.sha256(archive_bytes).hexdigest() + "\n"`. Verifies AC10.
- `test_package_catalogue_source_date_epoch_in_manifest` (integration): run with `SOURCE_DATE_EPOCH=1700000000`; extract and parse `catalogue-manifest.json` from archive; assert `generated_at == "2023-11-14T22:13:20+00:00"`. Verifies AC9.
- `test_package_catalogue_generated_at_no_microseconds` (integration): run without `SOURCE_DATE_EPOCH`; extract and parse `catalogue-manifest.json` from archive; assert `generated_at` does not contain a `.` character (no microsecond component). Verifies AC9 format clause for the unset-epoch path.
- `test_package_catalogue_cli_help`: call `cli.main(["package-catalogue", "--help"])` with `sys.stdout` captured; assert `SystemExit(0)` and assert each of the eight flag strings (`--root`, `--bundle`, `--release`, `--channel`, `--output`, `--source-revision`, `--minimum-agentbundle-version`, `--published-at`) appears in the captured output. Verifies AC1.
- `test_package_catalogue_missing_required_flag` (parametrized — drop each required flag in turn): for each required flag (`--root`, `--bundle`, `--release`, `--channel`, `--output`), call `cli.main` with all other required flags present but that one absent; capture stderr; assert `SystemExit` with non-zero code and assert the captured stderr contains the missing flag string. Verifies AC2.
- `test_package_catalogue_install_flags_rejected` (parametrized over `["--scope", "repo"]`, `["--force"]`, `["--adapter", "claude-code"]`): for each flag pair, call `cli.main(["package-catalogue", "--root", ".", "--bundle", "b", "--release", "r", "--channel", "c", "--output", ".", *flag_pair])`; assert `SystemExit` with non-zero code. Verifies AC25 observable behavior for all three flagged cases (note: `--force` reaches rejection via `_REWRITE_FLAGS` in `_VerbAwareParser`; `--adapter` via argparse's default unrecognized-argument path).
- `test_package_catalogue_sha256_in_descriptor_matches_sidecar` (integration): run; read sidecar; read channel descriptor; assert `descriptor["sha256"] == sidecar_content.strip()`. Verifies AC21.
- `test_package_catalogue_malformed_source_date_epoch`: monkeypatch `os.environ["SOURCE_DATE_EPOCH"] = "not-an-integer"`; run; assert exit code 1 and error message contains "SOURCE_DATE_EPOCH" and "not-an-integer". Verifies AC30.
- `test_package_catalogue_empty_source_date_epoch_treated_as_unset`: monkeypatch `os.environ["SOURCE_DATE_EPOCH"] = ""`; run; assert exit code 0; parse channel descriptor; assert `generated_at` is a valid ISO-8601 UTC timestamp (not an error). Verifies AC30 empty-equals-unset branch.
- `test_package_catalogue_published_at_default` (integration): run without `--published-at`; parse channel descriptor; assert `published_at` is a valid ISO-8601 UTC timestamp and does not contain a `.` microsecond component. Verifies AC19 default-path branch.
- `test_package_catalogue_manifest_digest_matches_archived_bytes` (integration): run against a fixture; for one known file, extract its bytes from the archive member and compute `hashlib.sha256(member_bytes).hexdigest()`; assert it equals the `sha256` in `catalogue-manifest.json`'s `files` list for that file. Verifies AC12 single-read consistency.
- `test_package_catalogue_packs_version_matches_archived_pack_toml` (integration): run against a fixture with a pack at a known version; extract the `packs/<name>/pack.toml` archive member; parse it; assert `packs[].version` in `catalogue-manifest.json` equals the version in the extracted pack.toml bytes. Verifies AC14 same-bytes contract.
- `test_package_catalogue_hardlink_rejected` (POSIX only, integration): create a hard link inside `packs/core/` using `os.link`; run; assert exit code 1. Verifies AC29.
- `test_package_catalogue_flag_traversal_rejected` (parametrized over `--bundle`, `--release`, `--channel` each with values `"../../x"` and `".."`): for each flag+value combination, call `run(args)` with that value; assert exit code 1 and error names the flag. Verifies AC32 for both slash-containing traversal and dot-dot-only forms.

**Approach:**
- `run(args) -> int` in `package_catalogue.py`:
  - Resolve `root`, compute `output`, derive path variables per the Behavior & rules section.
  - Refuse-to-overwrite check first (step 3).
  - Scan, validate, compute digests, extract pack metadata, determine `generated_at`, generate manifest, build archive, compute SHA-256.
  - `archive_sidecar_path = archive_path.parent / (archive_path.name + ".sha256")`.
  - Create directories, write three output files.
  - Return 0.
- `cli.py` registration (after the `reconcile` subparser):
  ```python
  sp = subparsers.add_parser(
      "package-catalogue",
      help="Package a catalogue repository into an Artifactory artifact layout (maintainer/CI only).",
  )
  sp.add_argument("--root", required=True, help="Catalogue repository root directory.")
  sp.add_argument("--bundle", required=True, help="Bundle name (e.g. engineering).")
  sp.add_argument("--release", required=True, help="Release tag (e.g. 0.13.0).")
  sp.add_argument("--channel", required=True, help="Channel name (e.g. stable).")
  sp.add_argument("--output", required=True, help="Output root directory.")
  sp.add_argument("--source-revision", default=None, help="Git commit or tag (CI supplies this; no git shell-out).")
  sp.add_argument("--minimum-agentbundle-version", default=None, help="Minimum agentbundle version for the channel descriptor.")
  sp.add_argument("--published-at", default=None, help="Publication timestamp for the channel descriptor (ISO-8601).")
  sp.set_defaults(func=_lazy("package_catalogue"))
  ```
  - `"output"` and `"root"` are already in `_PATH_BEARING_ATTRS`; no change to that set needed.
  - `_REWRITE_FLAGS = ("--scope", "--force", "--force-merge")` (cli.py:70) and `parser_class=_VerbAwareParser` (cli.py:189) together ensure `--scope` and `--force` are rejected via `_VerbAwareParser.error` on every subparser including `package-catalogue`. `--adapter` is rejected by argparse's default unrecognized-argument path since it is not registered for this subparser. These are verified mechanisms; the AC25 parametrized test provides observable confirmation.
  - Append `package-catalogue` to the `cli.py` module docstring's subcommand inventory (lines 4–8). The docstring already omits some shipped subcommands (`list-installed`, `show`); fixing those pre-existing omissions is out of scope for this PR. The append prevents the new subcommand from being entirely absent.

**Done when:** integration tests pass; `agentbundle package-catalogue --help` lists all eight flags; all ACs satisfied end-to-end.

---

### T5: Full test suite pass and goal-based checks

**Depends on:** T1, T2, T3, T4

**Touches:** none (verification only)

**Tests:**
- `python -m pytest packages/agentbundle/ -x` passes.
- Goal-based: `grep -n "import subprocess\|subprocess\.\|os\.system(\|\.Popen(\|import shlex\|shlex\.\|\[.git" packages/agentbundle/agentbundle/commands/package_catalogue.py` returns zero hits. Pattern anchored to imports and call sites to avoid false positives from prose comments. Verifies AC23.
- Goal-based: after a test run, grep the channel descriptor JSON and the SHA-256 sidecar file (the two uncompressed command-generated outputs) for common credential-shaped tokens (`"password"`, `"token"`, `"secret"`, `"api_key"`, `"bearer"`); assert zero hits. Verifies AC24.
- Goal-based: diff `pyproject.toml` against `origin/main`; assert no new dependencies added. Verifies AC27.

**Approach:**
- Run full test suite.
- If failures: distinguish pre-existing failures from regressions caused by this change. Any new failure is a blocker.

**Done when:** pytest exits 0 and all goal-based checks pass. Verifies AC28.

## Rollout

New subcommand — additive, no behavior change to any existing subcommand or installed state. No state schema change. Ships as part of ini-004 agentbundle release (minor version bump in `spec/agentbundle-enterprise-distribution-release`). The changelog entry for this new public CLI surface and the maintainer-facing how-to guide (noted in RFC-0072 § Affected surface) are deferred to `spec/artifactory-publishing-workflow` and `spec/agentbundle-enterprise-distribution-release` per the ini-004 work queue; this spec covers only the command implementation.

**Pre-ship prerequisite — consumer spec gap:** AC20 of this spec and spec/https-catalogue-channels are currently mutually incompatible: this spec emits only relative `artifact` URLs (Never-do: absolute URL), but `spec/https-catalogue-channels` has no AC requiring the installer to resolve a relative `artifact` via `urljoin(descriptor_url, artifact)` before its same-origin/HTTPS checks. Before shipping this command to production (where an installer would consume its output), `spec/https-catalogue-channels` must be amended to add: (a) an AC requiring relative `artifact` URLs to be resolved via `urljoin` before scheme/host/port validation; (b) an AC or explicit toleration note for extra descriptor fields (`published_at`, `source_revision`). Track as a follow-on PR to `spec/https-catalogue-channels`. This command can be built and tested in isolation without that AC; the gap matters only when the packager and installer are run end-to-end.

## Risks

- **In-memory archive assembly:** the entire archive is assembled in a `BytesIO` buffer. Large catalogues with many packs could consume significant RAM. Acceptable for the first implementation given typical catalogue sizes; a streaming approach is a follow-on if needed.
- **`tarfile.TarInfo.mode` with type bits:** `tarfile.TarInfo.mode` stores just the permission bits by default when `type` is set; some versions also require `info.type = tarfile.REGTYPE` explicitly. The `test_build_archive_member_metadata_files` test confirms the written mode is as expected.
- **Hard-link detection on POSIX:** `st_nlink > 1` on a regular file correctly detects hard links on Linux and macOS. On Windows, `st_nlink` is always 1; hard-link detection is POSIX-only. AC29 and the test are both marked POSIX-only. The `test_validate_content_hardlink_rejected` and `test_package_catalogue_hardlink_rejected` tests use `@pytest.mark.skipif(sys.platform == "win32", reason="st_nlink hard-link detection is POSIX-only")`.
- **`SOURCE_DATE_EPOCH` precision:** `datetime.fromtimestamp(int(epoch), tz=timezone.utc).replace(microsecond=0).isoformat()` produces `"2023-11-14T22:13:20+00:00"` (no microseconds). The `.replace(microsecond=0)` call is also applied to the `datetime.now()` path to keep both branches format-consistent. The test fixture verifies the exact string.
- **Traversal guard is belt-and-suspenders:** `_validate_content`'s path-traversal check (`path.resolve().relative_to(root)`) is unreachable for a genuine non-symlink regular file under `root`. The primary real-input trigger (a symlinked intermediate directory such as `root/docs`) is now caught first by the explicit `is_symlink()` checks on top-level and intermediate directory paths. The traversal guard remains for defense-in-depth against edge cases not covered by the explicit checks. Its test is intentionally synthetic (mock); the intermediate-dir symlink real-input path is tested by `test_validate_content_intermediate_dir_symlink_rejected`.
- **Ordering of `catalogue-manifest.json` in the sorted member list:** `"catalogue-manifest.json"` (starts with `c` = 0x63) sorts after `"LICENSE"` (L = 0x4C) and `"README.md"` (R = 0x52) but before `"docs/"` (d = 0x64) and `"packs/"` (p = 0x70). The determinism test confirms the order is stable.

## Changelog

- 2026-07-24: initial plan
- 2026-07-24: second adversarial review — added single-read design decision + `_read_content_files` interface; replaced `assert` with explicit `raise` in `_build_archive` + added `test_build_archive_rejects_traversal_member_name`; added AC29 (hard-link, POSIX) and AC30 (malformed SOURCE_DATE_EPOCH); updated AC25 test to observable CLI (not parser introspection); fixed `0o100644`/`0o644` inconsistency to `0o644`; added `datetime.replace(microsecond=0)` for format consistency; added tests for `--published-at` default, hardlink observable behavior, malformed epoch, manifest-archive digest consistency; added cli.py docstring update to T4; noted changelog/guide deferral in Rollout
- 2026-07-24: third adversarial review — added root-file symlink check to `_validate_content` + `test_validate_content_root_file_symlink_rejected`; added `test_validate_content_symlink_dir_rejected` for symlinked subdirectories; fixed pack metadata extraction to use in-memory `file_bytes` bytes (not second disk read) + added `test_package_catalogue_packs_version_matches_archived_pack_toml`; added step 9b `published_at` default computation to run() execution order; parametrized `test_package_catalogue_install_flags_rejected` over --scope/--force/--adapter; pinned `_generate_manifest` serialization to `json.dumps(indent=2, ensure_ascii=False)`; noted traversal guard is belt-and-suspenders in Risks; clarified env-file exclusion applies only at repo root level in spec Boundaries
- 2026-07-24: fourth adversarial review — added top-level allowlisted directory symlink check to `_validate_content` + `test_validate_content_top_level_dir_symlink_rejected`; reordered run() steps 14-16 to write archive last (prevents self-locking from partial write failures); fixed `_PATH_BEARING_ATTRS` line citation in spec Assumptions (47 not 48); softened T4 docstring note to not claim the inventory is otherwise complete; added `published_at` producer-emitted / consumer-ignored cross-spec note to spec Assumptions
- 2026-07-24: fifth adversarial review — added `test_build_archive_rejects_drive_letter_member_name` (AC22 drive-letter clause); documented partial-archive-write residual self-lock in Risks/Failure; added `packs/` subdir constraint to spec Assumptions; dropped overclaimed AC12 label from `test_compute_file_digests_values`; moved top-level dir `is_symlink()` check before `is_dir()` to report correct error for symlink-to-non-dir; added excluded dirs to end-to-end fixture and asserted archive member exclusion (AC4)
- 2026-07-24: sixth adversarial review — added "exactly three output files" assertion to end-to-end test (AC3); added `root/docs` to top-level symlink check list + `test_validate_content_intermediate_dir_symlink_rejected`; corrected traversal-guard "unreachable" rationale (primary real-input now caught by explicit symlink checks); documented `--minimum-agentbundle-version` reliance on consumer-side semver validation in spec Assumptions; added AC31 (missing packs/ dir exits non-zero)
- 2026-07-24: seventh adversarial review — added AC24 credential grep to T5 goal-based checks; moved SOURCE_DATE_EPOCH tests from T2 to T4 (T2's `_generate_manifest` takes pre-computed string; added `test_package_catalogue_generated_at_no_microseconds` to T4); dropped construction-detail sentences from spec Boundaries ("read once", "no running hash") — observable contract is AC12
- 2026-07-24: eighth adversarial review — fixed rglob count to filter files only (`p.is_file()`); tightened AC23 grep to import/call-site patterns to avoid prose-comment false positives; pinned `tarfile.GNU_FORMAT` to prevent PAX toolchain-dependent headers (AC8 reproducibility); added GNU_FORMAT design decision to plan; replaced gzip-mechanism Boundary clause with observable (bytes 4–7 = zero)
- 2026-07-24: ninth adversarial review — added AC32 + run() step 1 validation for --bundle/--release/--channel safe-charset guard (prevents path traversal via flag values); added relative-artifact-URL resolution assumption; clarified empty SOURCE_DATE_EPOCH="" treated as unset (AC30 updated); added `test_package_catalogue_empty_source_date_epoch_treated_as_unset` and `test_package_catalogue_flag_traversal_rejected`; cited _REWRITE_FLAGS line in plan approach; corrected failure-snippet to guarded form
- 2026-07-24: tenth adversarial review — added explicit `..` and `.` rejection to AC32 and step 1 (regex passes `..`); parametrized `test_package_catalogue_flag_traversal_rejected` to include `".."` value; documented relative-artifact-URL consumer spec gap (follow-on must add urljoin AC to spec/https-catalogue-channels); unified SOURCE_DATE_EPOCH guard method to `int(val)` try/except (not `isdigit()`); added `datetime.now(timezone.utc)` to failure-section reference
- 2026-07-24: eleventh adversarial review — added pre-ship prerequisite to Rollout (consumer spec gap: urljoin AC + extra-fields toleration AC must be tracked in spec/https-catalogue-channels before production use); updated extra-fields toleration note in Assumptions; dropped construction symbols from AC14 (pack_data key path) and AC25 (_lazy/_build_parser) — kept observable clause
