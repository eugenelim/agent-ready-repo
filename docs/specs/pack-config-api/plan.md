# Plan: pack-config-api

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

All work is inside `packages/agentbundle`. The dependency graph has two roots: `make_pack_dir` in `safety.py` (T1) and `PackRootConflict` + `pack_dir` in `config.py` (T2) are independent; both unblock `load_pack_config` (T3). `oplog.py` (T4) depends only on `pack_dir` (T2). CLI commands (T5, T6) depend on the API modules they wrap. Guide and `packs/AGENTS.md` (T7, T8) are documentation-only and depend on the API being stable. T2 has a cross-spec dependency on `spec:catalogue-pack-defaults/T5` for `PackState.user_root`.

Security-reviewer pass runs after gates (lint/typecheck/tests) pass, before merge.

## Constraints

- RFC-0074: `pack_name` slug validation, reserved slugs, `user-dir` home-confinement, `_MAX_ENTRY = 4096` practical cap (not PIPE_BUF).
- ADR-0058: `pack_dir` resolution order: (1) `home=` kwarg, (2) state rows, (3) `user_state_path(home).parent` fallback.
- ADR-0059: `load_pack_config` shallow-merges baked layer + user layer; malformed user layer → warning + baked layer only.
- `oplog clear` always requires `--yes` — no TTY exception.

## Construction tests

**Cross-cutting:**
- Concurrency test: two threads each call `write_entry("test-pack", "install", src="x")` 1000 times; `ops.jsonl` is valid JSONL with exactly 2000 lines.
- End-to-end smoke: set up a tmp home dir, run `agentbundle pack-config set test-pack key val`, run `agentbundle pack-config show test-pack`, assert `(user override)` label appears.

## Tasks

### T1: Add `safety.make_pack_dir(base, pack_name)` to `agentbundle/safety.py`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/safety.py`

**Tests:**
- `make_pack_dir(home / ".agentbundle", "atlassian")` → creates `~/.agentbundle/atlassian/` with mode 0o700.
- `make_pack_dir(base, "../evil")` → raises `ValueError` (slug grammar).
- `make_pack_dir(base, "bin")` → raises `ValueError` (reserved slug).
- `make_pack_dir(base, "atlassian")` when `base` resolves outside `Path.home()` → raises `OSError`.
- `make_pack_dir(base, "atlassian")` when `<base>/atlassian` is a pre-existing symlink → raises `OSError`.
- `make_pack_dir(base, "atlassian")` called twice → idempotent, no error.

**Approach:**
- Validate `pack_name` against `^[a-z0-9][a-z0-9-]*$`; raise `ValueError` if not matched.
- Check against reserved slug frozenset; raise `ValueError` if matched.
- Resolve `base` and confirm it is under `Path.home()`; raise `OSError` if not.
- `mkdir(exist_ok=True, mode=0o700)`; then `lstat` the result and refuse if it is a symlink or non-directory (same pattern as `user_state_path`).

**Done when:** All T1 tests pass; no `chmod` on pre-existing directories.

---

### T2: Add `PackRootConflict` and `pack_dir()` to `agentbundle/config.py`

**Depends on:** T1, spec:catalogue-pack-defaults/T5

**Touches:** `packages/agentbundle/agentbundle/config.py`

**Tests:**
- No state rows → `pack_dir("atlassian")` returns `~/.agentbundle/atlassian/`.
- All rows agree on `user-root = "~/custom"` → returns `~/custom/atlassian/`.
- Two rows disagree → raises `PackRootConflict`; message names both paths and adapter names.
- `pack_dir("atlassian", home=Path("/tmp/h"))` resolves `~/custom` relative to `/tmp/h`.
- Idempotent: calling `pack_dir` twice on a non-existent pack dir creates it on first call, no-ops on second.

**Approach:**
- Add `class PackRootConflict(ValueError): ...` with fields `pack_name`, `paths`, `adapters`.
- Implement `pack_dir` using the three-step resolution (rows → fallback) per ADR-0058.
- Call `safety.make_pack_dir(base, pack_name)` to create the directory.

**Done when:** All T2 tests pass; `PackRootConflict` is exported from `agentbundle.config`.

---

### T3: Add `load_pack_config()` to `agentbundle/config.py`

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/config.py`

**Tests:**
- Baked defaults present, no user `config.toml` → returns baked values.
- User `config.toml` present, key collision → user value wins.
- Both absent → returns `{}`.
- Malformed user `config.toml` → returns baked layer + emits `RuntimeWarning`.
- `load_pack_config("atlassian", path=custom_path)` → reads from `custom_path`.

**Approach:**
- Layer 1: read `_data/install-defaults.toml [pack-defaults.<pack>]` via `importlib.resources`.
- Layer 2: read `<pack_dir(pack_name)>/config.toml`; on `tomllib.TOMLDecodeError` emit `warnings.warn(..., RuntimeWarning)` and use `{}` for this layer.
- Shallow merge: `{**layer1, **layer2}`.

**Done when:** All T3 tests pass; `load_pack_config` is exported from `agentbundle.config`.

---

### T4: Create `agentbundle/oplog.py` with `write_entry()` and `_append_line()`

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/oplog.py` (new file)

**Tests:**
- `write_entry("atlassian", "install", src="s")` → `ops.jsonl` contains one valid JSON object with keys `action`, `src`, `ts` (last); no `dst` key.
- `write_entry(..., dst="d")` → `dst` key present.
- `write_entry(..., extra={"ts": "x"})` → raises `ValueError` before any I/O.
- `write_entry(..., extra={"k": "v" * 5000})` → entry emitted with `"_truncated": true`; base fields present.
- Base fields alone > 4096 bytes → raises `EntryTooLargeError` before any I/O.
- Concurrency test (see Construction tests above).
- `_append_line` partial-write path: monkeypatched `os.write` returning `n < len(line)` → `RuntimeWarning` emitted.

**Approach:**
- Implement `_append_line(path, line)` with POSIX `os.open(O_WRONLY|O_CREAT|O_APPEND)` + single `os.write`; Windows path uses `statelock`.
- `write_entry` builds the payload dict, captures `ts` last, serializes to JSON bytes + `b"\n"`, calls `_append_line`.
- `EntryTooLargeError(actual: int, limit: int)` raised when `len(line) > _MAX_ENTRY` before the `os.open` call.

**Done when:** All T4 tests pass; `write_entry`, `EntryTooLargeError` exported from `agentbundle.oplog`.

---

### T5: Create `agentbundle/commands/pack_config_cmd.py`

**Depends on:** T3

**Touches:** `packages/agentbundle/agentbundle/commands/pack_config_cmd.py` (new file)

**Tests:**
- `pack-config show atlassian` on a fixture with baked and user values → stdout contains `(baked default)` and `(user override)` labels.
- `pack-config set atlassian key val` → `config.toml` updated; subsequent `show` reflects the change.
- `pack-config get atlassian missing-key` → exits 1.
- `pack-config unset atlassian key` → key removed from `config.toml`.

**Approach:**
- `get`: call `load_pack_config`; look up key; print or exit 1.
- `set`: read `config.toml` (or create it); write key; save via `tomllib` + manual serializer (stdlib only).
- `unset`: read `config.toml`; delete key; save.
- `show`: call `load_pack_config`; call `_load_baked_only`; for each key, compare baked vs effective to label.

**Done when:** All T5 tests pass; commands wired in T7.

---

### T6: Create `agentbundle/commands/oplog_cmd.py`

**Depends on:** T4

**Touches:** `packages/agentbundle/agentbundle/commands/oplog_cmd.py` (new file)

**Tests:**
- `oplog show atlassian` on a 60-entry log → prints last 50 entries.
- `oplog show atlassian --since=<ISO>` → prints only entries with `ts >= ISO`.
- `oplog clear atlassian --yes` → `ops.jsonl` is empty; exits 0.
- `oplog clear atlassian` (no `--yes`) → exits non-zero; `ops.jsonl` unchanged.

**Approach:**
- `show`: open `ops.jsonl`, read all lines, skip non-JSON fragments (handle partial-write corruption gracefully), apply `--since` filter, tail to last 50.
- `clear`: require `--yes`; truncate file to 0 bytes.

**Done when:** All T6 tests pass; commands wired in T7.

---

### T7: Register new CLI commands in `agentbundle/cli.py`

**Depends on:** T5, T6

**Touches:** `packages/agentbundle/agentbundle/cli.py`

**Tests:**
- `agentbundle pack-config --help` exits 0 and lists `get`, `set`, `unset`, `show`.
- `agentbundle oplog --help` exits 0 and lists `show`, `clear`.

**Approach:**
- Add two new subcommand groups to the CLI parser, following the pattern of existing command registration.

**Done when:** All T7 tests pass; `agentbundle pack-config` and `agentbundle oplog` are reachable from the installed CLI.

---

### T8: Write `guides/_shared/reference/pack-config-api.md` and update `packs/AGENTS.md`

**Depends on:** T3, T4, T5, T6

**Touches:** `guides/_shared/reference/pack-config-api.md` (new), `packs/AGENTS.md`

**Tests:**
- `guides/_shared/reference/pack-config-api.md` exists.
- `packs/AGENTS.md` contains a reference to `pack-config-api.md`.

**Approach:**
- Write the reference guide covering: `pack_dir`, `load_pack_config`, `write_entry`, `[pack-defaults.*]` in `catalogue.toml`, and `agentbundle pack-config` / `agentbundle oplog` CLI commands.
- Add a "Pack config and operation log" section to `packs/AGENTS.md` linking to the guide.

**Done when:** Both files exist with complete content; `packs/AGENTS.md` section is present.

---

## Rollout

Pure Python library + CLI addition. No database migrations, no feature flags. Ships as a single PR. The `catalogue-pack-defaults` spec must be merged first (the `PackState.user_root` field written at install time is what `pack_dir` reads in step 2 of its resolution). Security-reviewer pass required before merge.

## Risks

- Concurrent-write test may be flaky if the test runner restricts thread scheduling. Mitigate: use `time.sleep(0)` to yield between writes; assert line count only (not order).
- `importlib.resources` path for `_data/install-defaults.toml` differs between editable install and installed package — use the same two-path fallback already in `catalogue_tooling/config.py`.

## Changelog

- 2026-07-28: initial plan
