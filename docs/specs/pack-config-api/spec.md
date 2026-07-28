# Spec: pack-config-api

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0074, ADR-0058, ADR-0059
- **Shipped in:** agentbundle 0.21.0
- **Contract:** none (internal Python API + CLI subcommands; no external network API)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Give pack scripts (Python or shell scripts shipped inside a pack) a stable, cross-catalogue Python API to resolve their user-scope directory (`pack_dir`), read a merged configuration dict (`load_pack_config`), and append structured operation entries to a JSONL log (`write_entry`). Expose these capabilities to users and pack authors via two new CLI subcommand groups: `agentbundle pack-config` and `agentbundle oplog`. Ship a canonical pack-author reference guide at `guides/_shared/reference/pack-config-api.md`.

This spec depends on `catalogue-pack-defaults` (specifically `spec:catalogue-pack-defaults/T5` for `PackState.user_root` and `spec:catalogue-pack-defaults/T6` for install-time writes).

## Boundaries

### Always do

- Validate `pack_name` against slug grammar `^[a-z0-9][a-z0-9-]*$` in `pack_dir` and `write_entry`; raise `ValueError` on failure before any I/O.
- Enforce the reserved-slug list (`bin`, `state`, `credentials`, `state.toml`) in `pack_dir`; raise `ValueError`.
- Create pack directories with mode `0o700` via `safety.make_pack_dir`.
- Reject any resolved base outside the user's home directory in `make_pack_dir`.
- Guard against symlink traversal and TOCTOU in `make_pack_dir` (reuse the pattern from `user_state_path`).
- Emit `RuntimeWarning` on partial `os.write` in `_append_line` (POSIX path).
- Route `security-reviewer` on this spec — `make_pack_dir` crosses a path-confinement and file-I/O security boundary.

### Ask first

- Adding a new reserved slug.
- Changing the entry-size cap (`_MAX_ENTRY = 4096`).
- Changing the `oplog clear` confirmation requirement.

### Never do

- Store secrets or credentials in `config.toml` or `ops.jsonl` — these are plaintext files.
- Read `config.toml` under a file lock (read-only, eventual consistency is correct).
- Use `PIPE_BUF` as the atomicity bound for regular-file appends — the correct primitive is the POSIX inode lock; the 4096-byte cap is a practical limit, not a kernel-enforced atomicity bound.

## Testing Strategy

- **TDD** for `pack_dir` resolution (all three steps: row agreement, PackRootConflict, fallback), `load_pack_config` cascade and fail-soft, `write_entry` entry shape + reserved key check + size enforcement, `_append_line` POSIX and Windows paths.
- **Goal-based check** for CLI commands: subprocess invocations against a tmp state dir; assert stdout and exit codes.
- **TDD** for `make_pack_dir` security invariants: symlink pre-creation, outside-home base, reserved slugs, slug grammar.

## Acceptance Criteria

**`pack_dir`**
- [x] `pack_dir("atlassian")` with no state rows returns `~/.agentbundle/atlassian/` (created, mode 0o700).
- [x] `pack_dir("atlassian")` with agreeing state rows returns the `user-root` path expanded relative to home.
- [x] `pack_dir("atlassian")` with disagreeing state rows raises `PackRootConflict`; exception message names both conflicting paths.
- [x] `pack_dir("../evil")` raises `ValueError` (slug grammar violation).
- [x] `pack_dir("bin")` raises `ValueError` (reserved slug).
- [x] `pack_dir("atlassian", home=Path("/tmp/testhome"))` resolves relative to `/tmp/testhome`.

**`make_pack_dir`**
- [x] Pre-existing symlink at `<base>/<pack>` is detected and raises `OSError`.
- [x] Base resolving outside `Path.home()` raises `OSError`.

**`load_pack_config`**
- [x] Returns baked `[pack-defaults.atlassian]` values when no user `config.toml` exists.
- [x] User `config.toml` values override baked values on key collision (shallow merge).
- [x] Returns `{}` when both baked and user layers are absent.
- [x] Returns baked layer + emits `RuntimeWarning` on malformed user `config.toml` (TOML decode error and UnicodeDecodeError).
- [x] `load_pack_config("atlassian", path=custom_path)` reads config from `custom_path`.

**`write_entry`**
- [x] Appends a valid JSONL line to `<pack_dir>/ops.jsonl`; `ts` is the last key.
- [x] `dst=None` → `dst` key absent from the emitted entry.
- [x] `extra={"ts": "…"}` raises `ValueError` before any I/O (reserved key).
- [x] Base fields exceeding 4096 bytes raise `EntryTooLargeError` before any I/O.
- [x] Extra fields causing oversize → entry emitted with `"_truncated": true`; truncated entry itself fits within `_MAX_ENTRY`.
- [x] Concurrent writes from two processes produce non-interleaved complete JSONL lines (POSIX local filesystem; tested with two threads writing 1000 entries each, `ops.jsonl` parses as valid JSONL with correct total line count).

**CLI — `pack-config`**
- [x] `agentbundle pack-config show atlassian` prints baked values labeled `(baked default)` and user values labeled `(user override)`.
- [x] `agentbundle pack-config set atlassian key value` writes to user `config.toml`; subsequent `show` reflects the new value as `(user override)`.
- [x] `agentbundle pack-config get atlassian key` prints the effective value; exits 1 when key absent.
- [x] `agentbundle pack-config unset atlassian key` removes the key from user `config.toml`.

**CLI — `oplog`**
- [x] `agentbundle oplog show atlassian` prints the last 50 entries (or all entries when fewer than 50).
- [x] `agentbundle oplog show atlassian --since=<ISO>` prints only entries with `ts ≥ ISO`.
- [x] `agentbundle oplog clear atlassian --yes` truncates `ops.jsonl`; subsequent `show` returns no entries.
- [x] `agentbundle oplog clear atlassian` (without `--yes`) exits non-zero with a message requiring `--yes`.

**Reference guide**
- [x] `guides/_shared/reference/pack-config-api.md` exists and documents `pack_dir`, `load_pack_config`, `write_entry`, `[pack-defaults.*]` in `catalogue.toml`, and the `pack-config` / `oplog` CLI commands.
- [x] `packs/AGENTS.md` contains a section directing pack authors to `guides/_shared/reference/pack-config-api.md` for config and oplog authoring.

## Assumptions

- Technical: POSIX `O_APPEND` single-write to a regular file is atomic under the inode lock (Linux `i_rwsem`, macOS vnode lock) for writes bounded to `_MAX_ENTRY = 4096` bytes on local filesystems (source: adversarial reviewer spike 2026-07-28; not PIPE_BUF-bounded).
- Technical: `spec:catalogue-pack-defaults/T5` (`PackState.user_root`) and `spec:catalogue-pack-defaults/T6` (install writes `user-root`) ship before this spec's T1 (source: dependency declared in plan.md).
- Technical: `safety.make_pack_dir` can reuse the `lstat`-based symlink guard already in `user_state_path` — same pattern, different path (source: reading `safety.py:619-650`).
- Process: `security-reviewer` runs on the diff for this spec's PR before merge, specifically for `make_pack_dir` path confinement and the `_append_line` POSIX I/O path.
