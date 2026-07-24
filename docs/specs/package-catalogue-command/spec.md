# Spec: Package Catalogue Command

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D1, D5), spec/https-catalogue-channels (channel descriptor schema)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

No tooling exists to produce the Artifactory artifact layout (immutable release archive + mutable channel descriptor JSON) from the catalogue repository. CI publishing is a manual multi-step operation prone to layout errors and non-deterministic archives. This spec adds `agentbundle package-catalogue` — a maintainer/CI-only subcommand that never installs anything — which (1) validates the catalogue's structure, (2) assembles a deterministic `.tar.gz` archive from the content allowlist (`packs/`, `profiles/`, `docs/contracts/`, `README.md`, `LICENSE`, `catalogue-manifest.json`), (3) writes a SHA-256 digest sidecar, and (4) emits a mutable channel descriptor JSON pointing at the immutable archive via a relative URL. Identical inputs (including `SOURCE_DATE_EPOCH`) produce byte-identical archives: paths are sorted, uid/gid/mtime/modes are normalized, and the gzip header modification time is zeroed. The command refuses to overwrite an existing release archive and provides no `--force-overwrite` flag in this implementation.

## Boundaries

### Always do

- Apply the content allowlist strictly: include only regular files (not symlinks, not hard links) recursively under `packs/`, `profiles/`, `docs/contracts/`, the root-level `README.md` and `LICENSE` (when present), and the generated `catalogue-manifest.json`. Every other path is excluded. The RFC-0072 §D5 exclusions for `.git/`, `.github/`, `build/`, `dist/`, `tests/`, state files, credentials, and environment files refer to **repository root-level directories and files** — none of these appears in the allowlist. Files inside an allowlisted directory are included verbatim; pack authoring quality gates are responsible for keeping pack directories free of credentials and sensitive files. The packaging command itself injects no credentials into any output.
- Reject any symlink or hard link found inside the included content before writing any output. Failure names the offending path.
- Reject any included path that resolves outside `--root` after `.` and `..` normalization. Failure names the offending path.
- Validate that each `pack.toml` under `packs/` is parseable using `load_pack_toml` from `agentbundle.config` before writing any output. Failure names the offending file. A `pack.toml` missing the `name` or `version` field is also a validation failure.
- Validate that each `.toml` file under `profiles/` is parseable TOML before writing any output. Failure names the offending file.
- Sort archive members lexicographically by their relative path within the archive before writing the archive.
- Normalize every archive member: uid=0, gid=0, mtime=0; regular file mode 0o644. No member inherits on-disk uid, gid, mtime, or mode.
- The gzip wrapper's header modification time field (bytes 4–7 of the `.tar.gz` output) must be `\x00\x00\x00\x00`. This is the observable reproducibility requirement; the implementation mechanism is in the plan's Design section.
- Build `catalogue-manifest.json` before assembling the archive: compute SHA-256 of each included file's bytes; extract pack name and version from each `pack.toml`; sort `files` by path and `packs` by name; serialize as UTF-8 JSON. Include `catalogue-manifest.json` in the archive but do not list it in its own `files` array. The observable contract is AC12: each `sha256` value in the manifest equals `hashlib.sha256(file_bytes).hexdigest()` for the bytes actually stored in the archive for that file.
- Honor `SOURCE_DATE_EPOCH` when set: use its integer value (seconds since Unix epoch) as the timestamp for `generated_at` in `catalogue-manifest.json`. When unset, use the current UTC time. Archive member mtimes are always 0 regardless of `SOURCE_DATE_EPOCH`.
- Validate `--bundle`, `--release`, and `--channel` against a safe character set before any path construction: only alphanumeric characters, hyphens, dots, and underscores are permitted (`[A-Za-z0-9\-._]+`), and the value must not be `.` or `..` or contain `..` as a component. A value that fails this check is rejected at startup with a clear error naming the flag and the invalid value. No output is written.
- Refuse to overwrite an existing release archive: if the output archive path already exists, exit non-zero and name the conflicting path. No output file is written.
- Write the channel descriptor `artifact` field as a relative URL: `../releases/<release>/catalogue-<release>.tar.gz`. Never use an absolute URL.
- Create output directory hierarchy as needed; do not require the caller to pre-create it.
- Use Python 3.11 stdlib only — `tarfile`, `hashlib`, `json`, `pathlib`, `os`, `gzip`, `io`, `tomllib`. No new runtime dependencies.
- Use `example.test` placeholders in all tests and documentation.

### Ask first

- Adding `--force-overwrite` or any flag that bypasses the refuse-to-overwrite check.
- Evaluating pack evals or running LLM judges as a packaging gate (RFC-0072 Open question 2 — recommended: no).
- Including content outside the current allowlist (e.g. `seeds/`, `scripts/`, or custom directories).
- Adding archive formats beyond `.tar.gz`.
- Adding git shell-out to derive `--source-revision` automatically.
- Changing the `catalogue-manifest.json` schema version or field names.
- Changing the relative URL form of the `artifact` field to an absolute URL.

### Never do

- Shell out to `git` — no `subprocess.run(["git", ...])`, `subprocess.Popen`, or `os.system` call. CI supplies the commit via `--source-revision`.
- Include symlinks or hard links as archive members.
- Write `..` segments, absolute paths, or Windows drive-letter paths into archive member names.
- Inject credentials, bearer tokens, API keys, or password-style values into any output file via the packaging command itself (flags, generated metadata, or computed values). The command does not scan or redact archive content — pack content ships verbatim.
- Use an absolute URL for the channel descriptor `artifact` field.
- Introduce a new runtime dependency.

## Testing Strategy

- **TDD for content scan:** unit-test the content-scan helper with a synthetic fixture tree containing files in both allowed and excluded directories; assert the returned paths are exactly the allowlisted regular files, with symlinks absent.
- **TDD for symlink rejection:** fixture with a symlink inside `packs/core/`; assert the validator returns a non-None error string naming the symlink path.
- **TDD for path traversal rejection:** fixture path that resolves outside `--root` after normalization; assert the validator returns an error naming the offending path.
- **TDD for invalid `pack.toml`:** fixture with a non-TOML file at `packs/bad/pack.toml`; assert validation fails naming the pack directory.
- **TDD for missing `pack.toml` field:** fixture with a `pack.toml` lacking `version`; assert validation fails naming the file.
- **TDD for invalid profile TOML:** fixture with a non-TOML `.toml` file under `profiles/`; assert validation fails naming the file.
- **TDD for archive determinism:** build the archive from the same fixture twice with `SOURCE_DATE_EPOCH` fixed; compare `hashlib.sha256(archive_bytes)` of both builds; assert equal. This is the canonical AC8 test.
- **TDD for manifest-archive digest consistency:** build an archive from a fixture file with known bytes; verify that the `sha256` in `catalogue-manifest.json` equals `hashlib.sha256(file_bytes).hexdigest()` for the bytes actually stored in the archive member (extract member, compare). This test would fail if the file were read twice with different bytes. Verifies the single-read contract in AC12.
- **TDD for gzip mtime=0:** read the raw output `.tar.gz` bytes; assert bytes at offset 4–7 are `b'\x00\x00\x00\x00'` (gzip header mtime field).
- **TDD for `SOURCE_DATE_EPOCH`:** set `SOURCE_DATE_EPOCH=1700000000` in the environment; build archive; extract and parse `catalogue-manifest.json` from the archive; assert `generated_at == "2023-11-14T22:13:20+00:00"`.
- **TDD for malformed `SOURCE_DATE_EPOCH`:** set `SOURCE_DATE_EPOCH=not-an-integer` in the environment; run the command; assert exit code non-zero and error message names the invalid value. Verifies AC9's error-path extension (AC30).
- **TDD for `--published-at` default:** run the command without `--published-at`; parse the channel descriptor; assert `published_at` is an ISO-8601 UTC timestamp close to the current time (no microseconds). Verifies AC19's default-path branch.
- **TDD for hard-link rejection (POSIX):** create a hard link inside `packs/core/` using `os.link`; run the command; assert exit code non-zero and error names the path. Verifies AC29.
- **TDD for `generated_at` format consistency:** run the command with and without `SOURCE_DATE_EPOCH`; assert neither `generated_at` value contains a `.` (microsecond component). Verifies AC9 format clause.
- **TDD for `catalogue-manifest.json` schema:** build archive from a fixture with known packs; extract and parse `catalogue-manifest.json`; assert `schema == 1`, all fields present, `files` sorted by path, `packs` sorted by name, each file's `sha256` matches `hashlib.sha256(file_bytes).hexdigest()`.
- **TDD for SHA-256 sidecar:** assert sidecar content equals `hashlib.sha256(archive_bytes).hexdigest() + "\n"`.
- **TDD for refuse-overwrite:** pre-create the archive path with known bytes; run the command; assert exit code non-zero and error names the path; assert the file content is unchanged and no other output files are written.
- **TDD for channel descriptor:** parse the output `<channel>.json`; assert all required fields present with correct values; assert `artifact == "../releases/<release>/catalogue-<release>.tar.gz"`; assert `sha256` matches the sidecar; assert optional fields absent when not provided.
- **TDD for output layout:** after a successful run, assert the three expected output paths exist and no unexpected files are created.
- **Goal-based check for no git shell-out:** `grep -n "import subprocess\|subprocess\.\|os\.system(\|\.Popen(\|import shlex\|shlex\.\|\[.git" commands/package_catalogue.py` returns zero hits (pattern anchored to imports and call sites to avoid prose-comment false positives). Verifies AC23.
- **Goal-based check for no credentials in generated outputs:** after a test run, grep the channel descriptor JSON and sidecar file (the two uncompressed command-generated outputs) for common credential-shaped tokens (`"password"`, `"token"`, `"secret"`, `"api_key"`, `"bearer"`); assert zero hits. The archive is not inspected here (its content is verbatim source). Verifies AC24.
- **Goal-based check for no new runtime dependency:** `pyproject.toml` dependency list unchanged; `package_catalogue.py` imports no non-stdlib module outside the `agentbundle` package. Verifies AC27.

## Acceptance Criteria

- [ ] AC1: `agentbundle package-catalogue --help` exits 0 and the captured stdout contains each of the five required flag strings (`--root`, `--bundle`, `--release`, `--channel`, `--output`) and each of the three optional flag strings (`--source-revision`, `--minimum-agentbundle-version`, `--published-at`). Verified by asserting each string appears in the captured help text, not only by asserting exit 0.
- [ ] AC2: Omitting any one required flag (`--root`, `--bundle`, `--release`, `--channel`, `--output`) produces a non-zero exit code and a captured stderr message containing the name of the missing flag. All optional flags may be absent without error.
- [ ] AC3: On a structurally valid catalogue root, the command writes exactly three output files under the output hierarchy and creates no other files:
  - `<output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`
  - `<output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256`
  - `<output>/catalogues/<bundle>/channels/<channel>.json`
- [ ] AC4: The archive contains only regular files (no symlinks, no hard links, no device files, no FIFOs) from the content allowlist: all regular files recursively under `packs/`, `profiles/` (if present), `docs/contracts/` (if present), root-level `README.md` (if present), root-level `LICENSE` (if present), and `catalogue-manifest.json`. Files from `.git/`, `.github/`, `build/`, `dist/`, `tests/`, and all other paths not in the allowlist are absent.
- [ ] AC5: Archive members are ordered by their relative path within the archive in lexicographic (byte-order) sort. Two invocations of the command on identical inputs produce members in the same order.
- [ ] AC6: Every archive member has uid=0, gid=0, mtime=0 in its tar header. Regular file members have mode 0o644. No member inherits on-disk metadata.
- [ ] AC7: The gzip wrapper's header modification time field (bytes at offset 4–7 of the `.tar.gz` file) equals `b'\x00\x00\x00\x00'`. Verified by reading the raw archive bytes.
- [ ] AC8: Building the archive twice from identical inputs — same fixture directory, same flags, `SOURCE_DATE_EPOCH` held fixed across both calls — produces byte-identical archives. Verified by comparing `hashlib.sha256(archive_bytes)` across both builds.
- [ ] AC9: `SOURCE_DATE_EPOCH` is honored: when the environment variable is set to an integer N, `catalogue-manifest.json`'s `generated_at` field equals the ISO-8601 UTC representation of Unix timestamp N. When unset, `generated_at` is the current UTC time at command invocation. In both cases, `generated_at` uses second-level precision (no microsecond component). A non-integer `SOURCE_DATE_EPOCH` value causes the command to exit non-zero with a clear error naming the invalid value. Archive member mtimes are always 0 regardless of `SOURCE_DATE_EPOCH`.
- [ ] AC10: The SHA-256 sidecar contains exactly `hashlib.sha256(archive_bytes).hexdigest() + "\n"` — 64 lowercase hexadecimal characters followed by a single newline, no other content.
- [ ] AC11: `catalogue-manifest.json` embedded in the archive has the schema: `{"schema": 1, "bundle": "<bundle>", "release": "<release>", "source_revision": "<str or null>", "generated_at": "<ISO-8601>", "files": [{"path": "<relative posix path>", "sha256": "<64hex>"}], "packs": [{"name": "<name>", "version": "<version>"}]}`. `source_revision` is the `--source-revision` value when provided; `null` when omitted.
- [ ] AC12: Each `sha256` value in `catalogue-manifest.json`'s `files` array is computed from the same bytes written into the archive for that file (files are read once; the same in-memory bytes are used for both digest computation and archive assembly). `catalogue-manifest.json` is not listed in its own `files` array.
- [ ] AC13: `catalogue-manifest.json`'s `files` array is sorted by `path` in lexicographic order. The `packs` array is sorted by `name` in lexicographic order.
- [ ] AC14: The `packs` list in `catalogue-manifest.json` is populated from the same bytes archived for each `pack.toml` (not from a second independent disk read). Each entry has `name` and `version` sourced from `pack.toml`'s `[pack]` table. A `pack.toml` that is not valid TOML, or that is missing `name` or `version`, causes the command to exit non-zero before writing any output; the error names the offending file. Verified by a test that checks `packs[].version` in the manifest equals the `version` in the archived `pack.toml` member bytes.
- [ ] AC15: A `.toml` file under `profiles/` that is not valid TOML causes the command to exit non-zero before writing any output. The error names the offending file.
- [ ] AC16: Any symlink found anywhere in the included content — at the top-level allowlisted directories themselves (`packs/`, `profiles/`, `docs/contracts/`), at intermediate path components of those directories (`docs/`), inside those directories (file or directory symlinks), or at the root-level `README.md`/`LICENSE` paths — causes the command to exit non-zero before writing any output. The error names the offending path. Root-level file symlinks are detected by explicit `is_symlink()` checks; top-level and intermediate directory symlinks are detected by explicit `is_symlink()` checks on each candidate path before walking it.
- [ ] AC17: Any included path that resolves outside `--root` after normalization causes the command to exit non-zero before writing any output. The error names the offending path.
- [ ] AC18: If the output archive path (`<output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`) already exists, the command exits non-zero with a clear error naming the path. No output files are written or modified. No `--force-overwrite` flag exists in this implementation.
- [ ] AC19: The channel descriptor JSON has the following fields: `schema` (integer 1), `kind` (`"agentbundle-catalogue"`), `bundle` (from `--bundle`), `channel` (from `--channel`), `release` (from `--release`), `artifact` (relative URL — see AC20), `sha256` (64 lowercase hex, equal to the archive SHA-256 digest), `published_at` (`--published-at` value when provided, else current UTC ISO-8601). Optional fields `source_revision` and `minimum_agentbundle_version` are present only when the corresponding flags are provided.
- [ ] AC20: The `artifact` field in the channel descriptor is always the relative URL `"../releases/<release>/catalogue-<release>.tar.gz"`. An absolute URL is never written.
- [ ] AC21: The `sha256` field in the channel descriptor equals the SHA-256 hex digest of the archive bytes, identical to the content of the `.sha256` sidecar file (without the trailing newline). Verified by comparing the channel descriptor's `sha256` value against `hashlib.sha256(archive_bytes).hexdigest()`.
- [ ] AC22: No archive member has a path containing `..`, starting with `/`, or starting with a Windows drive-letter pattern (`[A-Za-z]:`). This is enforced at archive-assembly time by an explicit `raise` (not an `assert`) so that the check cannot be stripped by Python's `-O` optimization flag. Verified by a unit test that directly passes a crafted member name containing `..` to `_build_archive` and asserts the exception is raised.
- [ ] AC23: No `subprocess` import, `subprocess.` call, `os.system(` call, `.Popen(` call, `import shlex`, `shlex.` call, or `["git"` literal appears in `commands/package_catalogue.py`. Verified by a pattern-anchored grep returning zero hits (see T5 goal-based check).
- [ ] AC24: The packaging command does not inject credentials, bearer tokens, API keys, or password-style values into the channel descriptor or SHA-256 sidecar (the two uncompressed output files the command itself generates). Verified by a goal-based grep of the channel descriptor JSON and sidecar file for common credential-shaped tokens. The archive's compressed content reflects the source repository verbatim; pack authoring gates own credential hygiene for pack content.
- [ ] AC25: `agentbundle package-catalogue` is a registered subcommand in `cli.py`. It does not accept `--scope`, `--force`, or `--adapter`; each of those flags, passed alongside all required flags, causes the CLI to exit non-zero. Verified by invoking `cli.main` (observable behavior, not parser structure inspection). Parametrized over all three rejected flags.
- [ ] AC26: The output directory hierarchy is created by the command if it does not exist; the caller is not required to pre-create any directories.
- [ ] AC27: No new runtime dependency is introduced. `package_catalogue.py` imports only Python 3.11 stdlib modules and other modules already present in `packages/agentbundle/`. Verified by `pyproject.toml` dependency list and import-level grep.
- [ ] AC28: All existing agentbundle tests pass after the change with no modifications to the tests themselves.
- [ ] AC29: (POSIX only) Any hard link found inside the included content causes the command to exit non-zero before writing any output. The error names the offending path. Verified by creating a hard link with `os.link` inside `packs/core/` and asserting non-zero exit; test is skipped on Windows where `st_nlink > 1` is not a reliable hard-link signal.
- [ ] AC30: A non-integer (or non-empty, non-None) `SOURCE_DATE_EPOCH` environment variable value causes the command to exit non-zero with a clear error message naming the invalid value. No output files are written. An empty string `SOURCE_DATE_EPOCH=""` is treated as unset (falls back to `datetime.now()`); only a non-empty, non-integer value triggers this error.
- [ ] AC31: A `--root` directory that lacks a `packs/` subdirectory causes the command to exit non-zero before writing any output. The error names the missing directory.
- [ ] AC32: `--bundle`, `--release`, and `--channel` flag values are validated at startup. A value that (a) contains any character outside `[A-Za-z0-9\-._]`, (b) equals `.` or `..`, or (c) contains `..` as a component causes the command to exit non-zero with a clear error naming the flag and value. No output is written. Verified by parametrized tests for each of the three flags with values `"../../x"` (slash-containing) and `".."` (dot-dot without slash — passes the regex but must still be rejected).

## Assumptions

- Technical: `load_pack_toml` at `agentbundle/config.py:81` is the correct function for reading `pack.toml`; it raises `ConfigError` on a missing or malformed file. Pack name is at `pack_data["pack"]["name"]`; pack version is at `pack_data["pack"]["version"]`. Both are strings; the implementing PR verifies the field path against `install.py:885` (`pack_version = pack_toml.get("pack", {}).get("version", "0.0.0")`). (source: config.py and install.py code inspection)
- Technical: `gzip.GzipFile(fileobj=buf, mode="wb", mtime=0)` writes the gzip header with the 4-byte mtime field at offset 4 set to `\x00\x00\x00\x00`. Python's `gzip.open` does not expose `mtime`; `gzip.GzipFile` is required for reproducible output. (source: Python 3.11 stdlib `gzip` module)
- Technical: `tarfile.TarInfo` fields `uid`, `gid`, `mtime`, and `mode` are set directly before calling `tarfile.addfile(info, fileobj)`. `tarfile.add()` inherits from-disk metadata and cannot be used here. (source: Python 3.11 stdlib `tarfile` module)
- Technical: Lexicographic sort of POSIX relative paths uses Python's `sorted()` on strings. Deterministic across invocations and Python versions for the same input set. (source: Python language spec)
- Technical: `tomllib` (Python 3.11 stdlib) is used to validate profile `.toml` files, consistent with the rest of the codebase. (source: config.py, validate.py)
- Technical: Python 3.11 stdlib-only constraint. (source: `pyproject.toml`; RFC-0072)
- Technical: The `profiles/` and `docs/contracts/` directories may be absent from a given catalogue root. The command treats absent allowlisted directories as empty — no files included, no error. `packs/` absence is a validation error (there is nothing to package).
- Technical: Every direct subdirectory of `packs/` is treated as a pack directory and must contain a valid `pack.toml`. A `packs/` subdirectory lacking a `pack.toml` (or with an unparseable one) is a validation error, not a skip. Auxiliary or shared subdirectories under `packs/` are not a supported layout in this implementation.
- Technical: `"output"` and `"root"` are already in `_PATH_BEARING_ATTRS` in `cli.py` (confirmed: lines 47 and 49); no change to that set is needed for the new subcommand.
- Process: RFC-0072 is Accepted; D5 ratifies `agentbundle package-catalogue` as a new CLI surface. (source: RFC-0072 status)
- Product: Pack evals are not a packaging gate — this is the recommended answer to RFC-0072 Open question 2. No AC covers eval execution. (source: RFC-0072 § Open questions)
- Contract: `published_at` (always) and `source_revision` (when flagged) are written into the channel descriptor. `spec/https-catalogue-channels` does not currently include an explicit "extra descriptor fields are ignored" AC — the tolerance is assumed from the natural behavior of required-field-only validation. When the urljoin follow-on PR amends that spec, it should also add this AC so the tolerance is contract-backed.
- Contract: The relative `artifact` URL (`../releases/<release>/catalogue-<release>.tar.gz`) in the channel descriptor is resolved by the consumer installer relative to the channel descriptor's own URL using standard URL relative-reference resolution. `spec/https-catalogue-channels` does not currently contain an AC requiring the installer to apply `urljoin` before its same-origin/HTTPS checks — if it runs `urlsplit(artifact)` first on a relative URL, it misclassifies it (empty scheme). This is a cross-spec gap; a follow-on must add an AC to `spec/https-catalogue-channels` requiring relative `artifact` URLs to be resolved via `urljoin(descriptor_url, artifact)` before validation. No integration test spanning this boundary is authored here.
- Contract: `--minimum-agentbundle-version` is accepted as free-form text and written verbatim into the channel descriptor. Format validation (semver MAJOR.MINOR.PATCH) is enforced by the consumer (`spec/https-catalogue-channels` AC35/AC36) at install time, not by this command. A malformed value causes every installer to reject the channel descriptor — this is deliberate reliance on consumer-side validation rather than adding a semver parser at the producer. A follow-on can add producer-side validation if the consumer rejection UX proves insufficient.
- Process: The maintainer-facing how-to guide (noted in RFC-0072 § Affected surface as `docs/guides/`) and the changelog entry for this new public CLI surface are out of scope for this spec. They are deferred to `spec/artifactory-publishing-workflow` and `spec/agentbundle-enterprise-distribution-release` respectively, per the ini-004 work queue. The `cli.py` module docstring's subcommand inventory is updated in the same PR as this implementation (T4).
