# Plan: agentbundle-config-subcommand

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three slices, bottom-up:

1. **`agentbundle.user_config` IO module.** Path resolver (`platform`,
   `env`, `home` as explicit parameters), `UserConfig` dataclass,
   read / write / unset primitives. Stdlib only. Comments and
   formatting are not preserved across writes — the contract matches
   `.agentbundle-state.toml`. The writer fails loud on non-`[settings]`
   top-level tables ("future setting table not yet supported"). The
   reader validates the on-disk `adapter` value against
   `shipped_adapters_from_contract()`; an invalid value is surfaced
   via a one-line stderr warning and the loader returns
   `UserConfig(adapter=None)` so the resolver falls back to the
   constant.
2. **`scope.configured_adapter(user_config)` + a pre-flight block in
   `_resolve_target_adapter`.** A scope-agnostic, pack-agnostic
   reporter returns `user_config.adapter` if it's in
   `shipped_adapters_from_contract()`, else `None`.
   `_resolve_target_adapter` gets a new
   `user_config: UserConfig | None = None` keyword arg (default
   `None` keeps existing tests green). A new **pre-flight block is
   inserted between Step 2 and Step 3** (only when
   `state_adapter is None`) that reads the reporter and either
   returns the candidate (admissible at scope and in pack
   `allowed_adapters`) or raises `_AdapterResolutionRefused` with
   the AC13 or AC14 message. **Steps 3, 4, 4b, 5 are untouched** —
   for users who never ran `agentbundle config set`, every
   downstream behavior matches today exactly. All seven call sites —
   five in `install.py`, two in `upgrade.py` — thread `user_config`
   through.
3. **CLI surface.** New subparser `config` in `cli.py:_build_parser()`
   with `{get,set,unset,path}` actions. `cli.py:main()` reads the
   user config once via `load_user_config()` and attaches it to
   `args._user_config` before dispatching. `install.run` and
   `upgrade.run` read `args._user_config` and pass it down to
   `_resolve_target_adapter`. Tests construct a Namespace with
   `_user_config=...` directly.

The risky parts are not file IO or CLI plumbing. They are:

- **Pre-flight insertion point.** The pre-flight must run strictly
  between Step 2 (state-hint) and Step 3 (contract-version gate),
  *and only when `state_adapter is None`*. Insertion above Step 2
  would override existing-install adapters on upgrade. Insertion
  below Step 4 would re-introduce the candidate-vs-`allowed_adapters`
  membership-check trap an earlier reviewer pass caught.
- **Test isolation** — every developer machine that has
  `~/.config/agentbundle/config.toml` would otherwise drift test
  results. The conftest fixture redirects `HOME`/`XDG_CONFIG_HOME`/
  `APPDATA` per-test; subprocess tests inherit the env.

## Constraints

- **RFC-0011** — `pack-allowed-adapters` introduced `DEFAULT_ADAPTER`.
  User-config cannot bypass pack `allowed-adapters`; the membership
  invariant is load-bearing.
- **RFC-0012** — `repo-scope-per-adapter-projection` widened
  `DEFAULT_ADAPTER` to cover both scopes and sanctioned downstream
  monkey-patching. This plan preserves both.
- **AGENTS.md § *Check before acting*** — new deps must be recorded.
  This plan adds none.
- **`docs/guides/**/*.md` is in `EXCLUDED_PATTERNS`** —
  `self_host.py:311`. The new reference doc lands directly.

## Construction tests

Per-task tests live under each Task below. Cross-cutting:

- **End-to-end cascade — subprocess** (T5a): `agentbundle config set
  adapter codex` then `agentbundle config get adapter` reports
  `codex\tcodex\t(file)`; `unset` then `get` reports
  `adapter\tclaude-code\t(builtin)`.
- **End-to-end cascade — in-process resolver** (T5b): after the same
  `set`, an in-process call to `_resolve_target_adapter` with
  `user_config=load_user_config()` (and `state_adapter=None` so the
  pre-flight fires) returns `"codex"`. This exercises the actual
  resolver path, not just the `configured_adapter` self-report.
- **`--help` audit** (T4): `_build_parser().format_help()` contains
  the literal `config`; the `config` subparser's help contains
  `get`, `set`, `unset`, `path`.

**Manual verification:** none.

## Tasks

### T1: User-config IO module green

**Depends on:** none

**Verification mode:** TDD.

**Spec mapping:** AC3, AC4, AC8 (write-time validation), AC10
(unset semantics), AC19 (no new deps), portions of *Always do*.

**Tests (write before code):**
- `tests/unit/test_user_config_path.py` — `_user_config_path(platform=…,
  env=…, home=…)`:
  - macOS → `~/Library/Application Support/agentbundle/config.toml`.
  - Linux with `XDG_CONFIG_HOME` unset → `~/.config/agentbundle/config.toml`.
  - Linux with `XDG_CONFIG_HOME=/custom` → `/custom/agentbundle/config.toml`.
  - Windows with `APPDATA=C:\Users\X\AppData\Roaming` →
    `…/agentbundle/config.toml`.
  - Windows with `APPDATA` unset → `~/AppData/Roaming/agentbundle/config.toml`.
- `tests/unit/test_user_config_io.py`:
  - `read_user_config(path)` on a missing file returns
    `UserConfig(adapter=None)`; no warning.
  - `read_user_config(path)` on a file with `[settings]\nadapter =
    "codex"\n` returns `UserConfig(adapter="codex")`.
  - `read_user_config(path)` on a malformed TOML file (e.g. an
    unterminated string) emits a one-line stderr warning naming the
    offending path and the `tomllib.TOMLDecodeError` line/column,
    and returns `UserConfig(adapter=None)`. *Does not raise* — the
    rationale is in *Always do* (fail soft at load to keep
    `--help` and `config path` working). Subprocess test:
    `agentbundle --help` exits 0 against a malformed config file
    in the sandbox.
  - `read_user_config(path)` on a file whose `adapter` value is not
    in `shipped_adapters_from_contract()` emits a one-line stderr
    warning listing the admissible names AND returns
    `UserConfig(adapter=None)`.
  - `write_setting(path, "adapter", "codex")` on a missing file creates
    the parent directory and writes the expected bytes; idempotent on
    a second call with the same value.
  - `write_setting(path, "adapter", "not-a-real-adapter")` raises with
    a message listing admissible names; file not created.
  - `write_setting(path, "adapter", "codex")` against a file
    containing an unknown top-level table (e.g. `[future]\nx = 1\n`)
    raises with the literal message containing `"future setting
    table not yet supported"`; the original file is *not* mutated.
  - `write_setting(path, "adapter", "codex")` against a file
    containing a non-string value under `[settings]` (e.g.
    `[settings]\ntags = ["a","b"]\n` or `count = 3`) raises with the
    same `"future setting type not yet supported"` message; the
    original file is *not* mutated. Same guard covers `unset_setting`.
  - `write_setting(path, "adapter", "codex")` against a file
    containing a nested table under `[settings]` (e.g.
    `[settings.future]\nx = 1\n`, which `tomllib` parses as
    `settings = {"future": {"x": 1}}`) raises the same fail-loud
    message — the dict-valued entry is non-string and the guard
    fires.
  - `unset_setting(path, "adapter")` on a file containing only
    `[settings]\nadapter = "codex"\n` deletes the file.
  - `unset_setting(path, "adapter")` on a file with an additional
    `[settings]\nadapter = "codex"\nother = "x"\n` rewrites the file
    with `[settings]\nother = "x"\n` (preserving the unknown
    `[settings]` key).
  - `unset_setting(path, "adapter")` on a file containing an unknown
    top-level table raises the same fail-loud message.
  - `unset_setting(path, "adapter")` on a file with a non-string
    value under `[settings]` (e.g. `[settings]\ntags =
    ["a","b"]\nadapter = "codex"\n`) raises the same fail-loud
    message; the file is not mutated. (Mirrors `write_setting`'s
    guard — AC10 promises both writers refuse.)
  - `unset_setting(path, "adapter")` on a file that doesn't contain
    `adapter` is a no-op; exits 0.

**Approach:**
- Create `packages/agentbundle/agentbundle/user_config.py`. Use
  `from __future__ import annotations` so string-typed annotations
  resolve lazily.
- Define `@dataclass(frozen=True) class UserConfig: adapter: str | None`.
- Define `_user_config_path(*, platform=None, env=None, home=None) -> Path`.
  Default arg resolution: `platform = platform or sys.platform`;
  `env = env if env is not None else os.environ`;
  `home = home if home is not None else Path.home()`. Branches: macOS
  → `home / "Library" / "Application Support" / "agentbundle" /
  "config.toml"`; Linux → `Path(env.get("XDG_CONFIG_HOME") or
  home / ".config") / "agentbundle" / "config.toml"`; Windows →
  `Path(env.get("APPDATA") or home / "AppData" / "Roaming") /
  "agentbundle" / "config.toml"`.
- Define `read_user_config(path: Path) -> UserConfig`. Parse with
  `tomllib`. Validate `adapter` value if present; warn-and-null on
  invalid. Return.
- Define `load_user_config() -> UserConfig`. Convenience:
  `read_user_config(_user_config_path())`.
- Define `write_setting(path: Path, key: str, value: str)`. Validate
  key against `_KNOWN_KEYS = {"adapter"}`. For `adapter`, validate
  value against `shipped_adapters_from_contract()`. If the existing
  file has any non-`[settings]` top-level table, raise. Otherwise
  parse, mutate `[settings][key] = value`, emit `[settings]` with
  the sorted keys, one `key = "value"` line each.
- Define `unset_setting(path: Path, key: str)`. Same fail-loud guard.
  After removal, if `[settings]` is empty AND the parsed dict has no
  other top-level tables, `path.unlink()`; otherwise rewrite.
- The emitter is a hand-rolled "for k in sorted(settings):
  out.append(f'{k} = {_quote_basic_string(v)}')" — `_quote_basic_string`
  mirrors the helper at `agentbundle.config:383-416`.

**Done when:**
- All tests in `tests/unit/test_user_config_path.py` and
  `tests/unit/test_user_config_io.py` pass.
- `lint` and `typecheck` gates are clean.
- `git diff packages/agentbundle/pyproject.toml` is empty (AC19).

---

### T2: Conftest isolation fixture in place

**Depends on:** T1

**Verification mode:** Goal-based check.

**Spec mapping:** AC17.

**Tests (write before code):**
- `tests/unit/test_user_config_isolation.py`:
  - Under the fixture, `_user_config_path()` called with defaults
    returns a path under the per-test tmp_path (not under the
    developer's real home).
  - The same path, when opened for write inside the test, lands
    inside the sandbox.

**Approach:**
- Add or extend `packages/agentbundle/tests/conftest.py`:
  ```python
  @pytest.fixture(autouse=True)
  def _isolate_user_config_dir(tmp_path, monkeypatch):
      """Env-based sandbox for the user-config-dir resolver.

      Note: this redirects HOME/XDG_CONFIG_HOME/APPDATA env vars
      but does NOT monkey-patch Path.home(). The existing
      `fake_home` fixture in test_resolve_user_scope_target_adapter.py
      stubs Path.home() independently; the two compose because the
      user-config resolver reads from env first (Linux honors
      XDG_CONFIG_HOME over home; macOS uses home via Path.home()).
      Tests that need Path.home() under their control should use
      `fake_home`; tests that need the user-config file under
      their control rely on this fixture's env redirect.
      """
      sandbox = tmp_path / "user-config-sandbox"
      sandbox.mkdir()
      monkeypatch.setenv("HOME", str(sandbox))
      monkeypatch.setenv("XDG_CONFIG_HOME", str(sandbox / ".config"))
      monkeypatch.setenv("APPDATA", str(sandbox / "AppData" / "Roaming"))
      yield sandbox
  ```
- No production code change.

**Done when:**
- The isolation tests pass.
- Full existing suite passes — the fixture is additive and benign for
  every test that doesn't touch the user-config-dir.

---

### T3: `configured_adapter` resolver + `_resolve_target_adapter` threading

**Depends on:** T1

**Verification mode:** TDD.

**Spec mapping:** AC11, AC12, AC13, AC14, AC16.

**Tests (write before code):**
- `tests/unit/test_configured_adapter.py`. Signature:
  `configured_adapter(user_config: UserConfig | None) -> str | None`.
  Scope-agnostic, pack-agnostic — reports "what did the user
  configure, if anything known by the contract."
  - `configured_adapter(None)` returns `None`.
  - `configured_adapter(UserConfig(adapter=None))` returns `None`.
  - `configured_adapter(UserConfig(adapter="codex"))` returns
    `"codex"` (codex is in `shipped_adapters_from_contract()`).
  - `configured_adapter(UserConfig(adapter="copilot"))` returns
    `"copilot"` (copilot is shipped, even though it's repo-only;
    scope-capability is the resolver's job, not this function's).
  - `configured_adapter(UserConfig(adapter="not-a-real-adapter"))`
    returns `None` (defense in depth; the loader is the primary
    refusal point and emits the warning there).
- `tests/unit/test_resolve_target_adapter_user_config.py`. Tests
  use the existing `fake_home` fixture (from
  `test_resolve_user_scope_target_adapter.py`) to control
  `Path.home()` and create real probe-detectable directories.
  No `_probes` test seam, no monkeypatch of resolver internals.

  **Pre-flight returns when user-config is admissible:**
  - `_resolve_target_adapter(pack_dir, scope="user",
    allowed_adapters=["codex","claude-code"],
    contract_version="0.7",
    user_config=UserConfig(adapter="codex"))` returns `"codex"`.
    The pre-flight returns before Step 4 runs.
  - Same with `scope="repo"` (and `allowed_adapters=["codex"]`)
    returns `"codex"`.
  - `_resolve_target_adapter(pack_dir, scope="user",
    allowed_adapters=None, contract_version=None,
    user_config=UserConfig(adapter="codex"))` returns `"codex"`
    (no `allowed_adapters` filter, scope-admissible — pre-flight
    returns; Step 5 doesn't run).

  **User-config wins over user-scope probe.** Under `fake_home`,
  create `.claude/` so the claude-code probe would otherwise
  match. Call with `scope="user"`,
  `allowed_adapters=["codex","claude-code"]`,
  `contract_version="0.7"`,
  `user_config=UserConfig(adapter="codex")` → returns `"codex"`.
  The pre-flight returns before the probe runs.

  **Probe still wins when user has no configured adapter.**
  Under `fake_home`, create `.claude/`. Call with `user_config=None`
  (and again with `user_config=UserConfig(adapter=None)`) and
  otherwise the same kwargs. Result: `"claude-code"`. Load-bearing
  regression — the pre-flight is a no-op when nothing is
  configured, preserving every existing probe test.

  **Pre-flight refuses scope-incapable configured adapter
  (AC13).** `_resolve_target_adapter(pack_dir, scope="user",
  allowed_adapters=None, contract_version=None,
  user_config=UserConfig(adapter="copilot"))` raises
  `_AdapterResolutionRefused`. The message contains, as separate
  substring assertions: `"not supported at user scope"`,
  `"copilot"`, `"Adapters supported at user scope:"` (the
  sorted-list preamble — verifies the user gets to see which
  adapters they *can* use), and all four escape-hatch tokens:
  `"--scope"`, `"--adapter"`,
  `"agentbundle config set adapter"`,
  `"agentbundle config unset adapter"`. Asserting `--scope`
  explicitly prevents the canonical "I configured copilot for
  repo scope and stumbled into a user-scope command" remedy from
  being silently dropped by a future refactor.

  **Pre-flight refuses pack-incompatible configured adapter
  (AC14).** Call with `scope="user"`,
  `allowed_adapters=["claude-code"]`, `contract_version="0.7"`,
  `user_config=UserConfig(adapter="codex")` raises
  `_AdapterResolutionRefused`. The message contains
  `"not supported with your configured adapter"`, the literal
  `"codex"`, the pack-name token, the literal `"claude-code"`
  (the supported set), and the three escape-hatch strings.

  **Step 1 (`--adapter` flag) still beats user-config.** Call
  with `adapter="claude-code"` *and*
  `user_config=UserConfig(adapter="codex")`, with
  `allowed_adapters=["claude-code"]`. Returns `"claude-code"` —
  Step 1 returns before the pre-flight runs. (Important: a user
  who has configured codex can still install a claude-code-only
  pack by passing `--adapter claude-code` per-invocation, without
  reconfiguring.)

  **Step 2 (state-hint) still beats user-config.** Call with
  `state_adapter="kiro"`, `user_config=UserConfig(adapter="codex")`,
  `allowed_adapters=["kiro","codex"]`. Returns `"kiro"` — Step 2's
  short-circuit beats the pre-flight; on `upgrade`, the existing
  install's adapter sticks, the user-config doesn't force a
  destructive re-layout.

  **state_adapter set but inadmissible: pre-flight skips, existing
  fall-through preserved.** Setup: under `fake_home`, **do not
  create any `.claude/` / `.codex/` / `.kiro/` markers** so the
  Step 4 user-scope probe finds nothing (the assertion below
  depends on this). Call with `state_adapter="claude-code"`,
  `allowed_adapters=["kiro"]`, `contract_version="0.7"`,
  `user_config=UserConfig(adapter="codex")`, `scope="user"`. Step 2's
  membership check fails (claude-code not in allowed_adapters), so
  Step 2 falls through. Because `state_adapter is not None`, the
  pre-flight skips entirely — **no AC14 raise**. Step 3+ runs as
  today: Step 4 user-scope probe (none match) → `DEFAULT_ADAPTER`
  not in allowed → `allowed_adapters[0]` = `"kiro"`. Returns
  `"kiro"`. `upgrade.py`'s existing cross-adapter refusal then
  compares this against the state-pinned `"claude-code"` and raises
  *its* refusal — preserving the "state-pin mismatch is upgrade.py's
  problem, not user-config's" semantics.

  **Existing tests at**
  `tests/unit/test_resolve_user_scope_target_adapter.py:160, 176, 534,
  581, 593` must pass *without any edit* — the new keyword arg has a
  default of `None`, and `configured_adapter(None)` honors the
  monkey-patched constant.

**Approach:**
- In `packages/agentbundle/agentbundle/scope.py`, add (with
  `from __future__ import annotations` at top of file if not
  already present):
  ```python
  def configured_adapter(
      user_config: "UserConfig | None",
  ) -> str | None:
      """Report the user-configured adapter when set and known.

      Returns `user_config.adapter` when set and present in
      `shipped_adapters_from_contract()` (a basic known-by-
      contract sanity check, defense in depth — the loader is
      the user-facing diagnostic on contract drift). Returns
      None otherwise.

      Scope-agnostic and pack-agnostic. Scope-capability and
      pack-`allowed_adapters` enforcement live in
      `_resolve_target_adapter`'s pre-flight (AC12), not here.
      """
      if user_config is None or user_config.adapter is None:
          return None
      if user_config.adapter not in shipped_adapters_from_contract():
          return None
      return user_config.adapter
  ```
  No runtime import of `UserConfig` from `user_config.py` — the
  annotation is a string under `from __future__ import annotations`.
- In `packages/agentbundle/agentbundle/commands/install.py`:
  - Add `user_config: "UserConfig | None" = None` as a keyword arg
    to `_resolve_target_adapter` (after the existing keyword args).
  - **Insert a user-config pre-flight block between Step 2 and
    Step 3+4** (around line 2319, immediately before the
    contract-version gate). Step 0 / Step 1 / Step 2 are
    untouched. The pre-flight runs only when `state_adapter is
    None` — preserves the upgrade-path invariant that existing
    installs don't get re-layered by user-config (and prevents
    AC14 from mis-blaming user-config for a state-pin mismatch).
    ```python
    # Step 2.5 — user-config pre-flight.
    # If the user configured a known adapter AND this is a fresh
    # install (no state hint), either return the candidate (when
    # admissible at scope and pack-allowed) or refuse with a
    # clear message. If user_config is None, the candidate isn't
    # known by the contract, or state_adapter is set, the
    # pre-flight is a no-op and the existing probe /
    # DEFAULT_ADAPTER fallbacks run as today.
    candidate = configured_adapter(user_config) if state_adapter is None else None
    if candidate is not None:
        admissible_at_scope = (
            user_capable if scope == "user" else shipped
        )
        if candidate not in admissible_at_scope:
            raise _AdapterResolutionRefused(
                f"{command_name}: configured adapter "
                f"{candidate!r} is not supported at {scope} "
                f"scope. Adapters supported at {scope} scope: "
                f"{sorted(admissible_at_scope)}. To proceed: "
                f"invoke the command at a different scope "
                f"(e.g. --scope repo) where {candidate!r} is "
                f"supported, or pass --adapter <name> for a "
                f"per-install override, or run `agentbundle "
                f"config set adapter <name>` to change the "
                f"default, or `agentbundle config unset adapter` "
                f"to clear it."
            )
        if allowed_adapters is not None and candidate not in allowed_adapters:
            raise _AdapterResolutionRefused(
                f"{command_name}: pack {pack_name!r} is not "
                f"supported with your configured adapter "
                f"{candidate!r}. The pack supports: "
                f"{sorted(allowed_adapters)}. To proceed: pass "
                f"--adapter <name> for a per-install override, "
                f"or run `agentbundle config set adapter "
                f"<name>` to change the default, or "
                f"`agentbundle config unset adapter` to clear "
                f"it."
            )
        return candidate
    ```
    The existing `shipped`, `user_capable`, `command_name`, and
    `pack_name` locals are already in scope at the insertion
    point — `shipped` and `user_capable` are computed at lines
    2244-2245; `command_name` is a function parameter; `pack_name`
    is set at line 2243.
  - **Steps 3, 4, 4b, 5 are unchanged** — when the pre-flight
    falls through (`user_config` is None or the adapter wasn't
    recognised), the existing probe / `DEFAULT_ADAPTER` /
    `allowed_adapters[0]` logic runs as today. This is the
    load-bearing "preserve probe-by-default" path. **No edits
    to lines 2338, 2339, 2357, 2365** are required.
- In `packages/agentbundle/agentbundle/commands/upgrade.py`:
  - Update the two call sites at lines 257, 396 to pass
    `user_config=user_config` (with `user_config` threaded from
    `upgrade.run`).
- In both `install.run` and `upgrade.run`, read `args._user_config`
  via `getattr(args, "_user_config", None)` at function start and
  thread to every `_resolve_target_adapter` invocation in that file.

**Done when:**
- All tests in `test_configured_adapter.py` and
  `test_resolve_target_adapter_user_config.py` pass.
- The five legacy monkeypatch tests at
  `tests/unit/test_resolve_user_scope_target_adapter.py:160, 176, 534,
  581, 593` pass *without modification*.
- `lint`, `typecheck`, `test` gates clean.

---

### T4: `agentbundle config` CLI subcommand

**Depends on:** T1, T3

**Verification mode:** TDD.

**Spec mapping:** AC1, AC2, AC5, AC6, AC7, AC8, AC9, AC10, AC17
(subprocess sandbox verification).

**Tests (write before code):**
- `tests/unit/test_config_cmd.py` — in-process tests against the
  handler `agentbundle.commands.config.run(args)`:
  - `path` prints the resolved path (under the isolation sandbox);
    exits 0.
  - `get` with no key on a missing file prints
    `adapter\t<DEFAULT_ADAPTER>\t(builtin)`; exits 0.
  - `get adapter` on a file with `adapter = "codex"` prints
    `adapter\tcodex\t(file)`; exits 0.
  - `get adapter` on a file with an invalid value (after the
    loader's warning) prints
    `adapter\t<DEFAULT_ADAPTER>\t(builtin)` and a stderr line
    naming the invalid value; exits 0.
  - `get unknown-key` exits non-zero; message lists `adapter`.
  - `set adapter codex` creates the file, exits 0; second call same
    value is a no-op exit 0.
  - `set adapter not-a-real-adapter` exits non-zero; admissible names
    listed; file not created.
  - `set unknown-key value` exits non-zero; file not created.
  - `unset adapter` on a file with only `adapter` deletes the file;
    second call is a no-op exit 0.
  - `unset adapter` on a file with another preserved key keeps the
    file and preserves the other key.
- `tests/unit/test_cli_help_lists_config.py`:
  - `"config"` appears as a subparser key. Walk `parser._actions`
    for the first `argparse._SubParsersAction` instance, then read
    its `.choices` dict — one level of private-API fragility
    instead of the three-deep `parser._subparsers._group_actions[0].choices`
    chain (which has reshuffled across CPython versions).
  - The `config` subparser's positional `action` argument has
    `choices == ("get", "set", "unset", "path")`. Walk its
    `_actions` to find the positional with `dest == "config_action"`
    and read `.choices`.
- Subprocess sandbox verification (moved here from T2 per reviewer
  Nit 15):
  - `subprocess.run([sys.executable, "-m", "agentbundle", "config",
    "path"])` inherits the test's `HOME`/`XDG_CONFIG_HOME`/`APPDATA`
    env (from the conftest fixture); its stdout reports a path under
    the per-test tmp_path.

**Approach:**
- Add `packages/agentbundle/agentbundle/commands/config.py`:
  - `_ACTIONS = {"get": _do_get, "set": _do_set, "unset": _do_unset,
    "path": _do_path}` — registry dispatch.
  - `_KNOWN_KEYS = ("adapter",)` — registered settings keys.
  - `def run(args: argparse.Namespace) -> int` — looks up
    `_ACTIONS[args.config_action]` and invokes it.
  - Each `_do_*` reads `args` for its inputs, writes to stdout/stderr,
    returns an int exit code.
- In `cli.py:_build_parser()`, add the `config` subparser between
  `init-state` and `reconcile`:
  ```python
  sp_config = subparsers.add_parser(
      "config",
      help="Get or set adapter-scoped user settings.",
      epilog=(
          "User-config overrides scope.DEFAULT_ADAPTER. CLI flags "
          "(e.g. install --adapter) still override user-config "
          "per invocation."
      ),
  )
  sp_config.add_argument(
      "config_action", choices=("get", "set", "unset", "path"))
  sp_config.add_argument("key", nargs="?")
  sp_config.add_argument("value", nargs="?")
  sp_config.set_defaults(func=_lazy("config"))
  ```
- In `cli.py:main()`, after `_normalise_path_separators(args)`, add:
  ```python
  from agentbundle.user_config import load_user_config
  args._user_config = load_user_config()
  ```
  `load_user_config` is fail-soft (T1 contract): a malformed
  TOML file emits a stderr warning and returns
  `UserConfig(adapter=None)`. No try/except needed here.
  Handlers that consume the value read
  `getattr(args, "_user_config", None)`. **Test the malformed
  path:** subprocess test in T4's test file writes a malformed
  config under the sandbox, runs `agentbundle --help`, asserts
  exit 0 and a warning line on stderr.

**Done when:**
- All new tests pass.
- Manual smoke: at a real shell (inside an isolated tmp HOME),
  `agentbundle config path`, `set adapter codex`, `get adapter`,
  `unset adapter` round-trip correctly.

---

### T5: End-to-end cascade integration tests

**Depends on:** T1, T2, T3, T4

**Verification mode:** Goal-based check.

**Spec mapping:** AC15, AC20.

**Tests (write before code):**
- `tests/integration/test_config_cascade.py`:
  - **T5a — subprocess flow:** `agentbundle config path` →
    captures path; `config get adapter` → `(builtin)`; `config set
    adapter codex` → exits 0; `config get adapter` →
    `adapter\tcodex\t(file)`; `config unset adapter` → exits 0,
    file deleted; `config get adapter` → `(builtin)`.
  - **T5b — in-process resolver:** Inside the fixture's sandbox,
    write a real `[settings]\nadapter = "codex"\n` to the path
    returned by `_user_config_path()`; call
    `from agentbundle.user_config import load_user_config` and
    `from agentbundle.commands.install import _resolve_target_adapter`;
    invoke with kwargs in the exact order of the function
    signature at `install.py:2173-2182` —
    `_resolve_target_adapter(pack_dir, scope="user", adapter=None,
    allowed_adapters=None, contract_version="0.7",
    state_adapter=None, command_name="test",
    user_config=load_user_config())`. Assert result is `"codex"`.
    This is *not* a tautology: `_resolve_target_adapter` is the
    function `install.run` and `upgrade.run` actually call, not
    the `configured_adapter` self-report.
  - **T5c — `upgrade.py` and `install.py` thread `user_config`
    through every `_resolve_target_adapter` call site.** Static
    AST check, no monkeypatch. Matches both bare-name and
    qualified-attribute call shapes; asserts the total call count:
    ```python
    import ast
    from pathlib import Path
    import agentbundle
    AGENTBUNDLE = Path(agentbundle.__file__).parent
    EXPECTED = 7  # 5 in install.py, 2 in upgrade.py
    found = 0
    for src in [AGENTBUNDLE / "commands" / "install.py",
                AGENTBUNDLE / "commands" / "upgrade.py"]:
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = None
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target != "_resolve_target_adapter":
                continue
            found += 1
            kw_names = [kw.arg for kw in node.keywords]
            assert "user_config" in kw_names, (
                f"{src.name}:{node.lineno} calls "
                f"_resolve_target_adapter with keywords {kw_names}; "
                f"missing 'user_config'"
            )
    assert found == EXPECTED, (
        f"expected {EXPECTED} _resolve_target_adapter call sites "
        f"across install.py + upgrade.py, found {found} — a call "
        f"site was added or removed without updating EXPECTED"
    )
    ```
    Walks every call site (5 in install.py, 2 in upgrade.py); each
    must pass `user_config=` as a keyword arg, and the count must
    match. The test fails loud with the exact file/line and the
    keyword shape so a future failure prints the call's signature.

**Approach:**
- Use `subprocess.run([sys.executable, "-m", "agentbundle", …])` for
  T5a. Each step's stdout asserted against the expected one-line
  format. No mocking.
- Use direct function calls for T5b, T5c. Minimal kwargs (the
  function's full signature is documented at `install.py:2173`).

**Done when:**
- All three tests pass.
- The full
  `packages/agentbundle/tests/` and
  `packages/agentbundle/agentbundle/build/tests/` suites pass.

---

### T6: Reference doc + cross-link

**Depends on:** T4

**Verification mode:** Goal-based check.

**Spec mapping:** AC18.

**Tests (write before code):**
- `tests/unit/test_docs_agentbundle_reference.py`:
  - File `docs/guides/_shared/reference/agentbundle.md` exists.
  - Contains the three section headings for "Install agentbundle",
    "Install a pack", "Configure the default adapter" (or the chosen
    H2 wording — pin in the test).
  - `docs/guides/_shared/reference/README.md` links to it (relative
    `./agentbundle.md`).
  - Forward-link from "Install agentbundle" section points to
    `docs/guides/_shared/how-to/install-agentbundle-from-clone.md` (verified
    to exist).

**Approach:**
- Author `docs/guides/_shared/reference/agentbundle.md`:
  - **§ 1 — Install agentbundle.** `pip install agentbundle` once
    on PyPI; until then, `pip install -e .` from a clone with a
    forward-link to the existing
    `docs/guides/_shared/how-to/install-agentbundle-from-clone.md`.
  - **§ 2 — Install a pack.** Two-line example using
    `agentbundle install <catalogue-uri>`.
  - **§ 3 — Configure the default adapter.** All four sub-actions
    (`get`, `set`, `unset`, `path`) with example shell invocations
    and a one-paragraph explanation of the cascade: CLI flag >
    user-config > `scope.DEFAULT_ADAPTER` (and a note that
    downstream catalogues may monkey-patch the constant for
    enterprise rebrands; user-config wins over that).
- Append the new page under `docs/guides/_shared/reference/README.md`'s
  index.

**Done when:**
- The doc audit test passes.
- A human read matches the user's framing: "generic agentbundle
  page with some basics — install agentbundle, install of packs,
  configure adapter with user config."

## Rollout

Additive feature; no migration, no flag, no rollout staging. Ships
in the next release.

## Risks

- **Membership-check trap (resolved).** The pre-flight architecture
  removes the trap entirely — there is no rewrite to Steps 4 / 4b /
  5. User-config is consulted in its own block, validated against
  scope and `allowed_adapters`, and either returns or raises. The
  existing Step 4 cascade is untouched.
- **TOML round-trip fidelity (mitigated by fail-loud).** Preserving
  comments and arbitrary unknown content is non-trivial without
  `tomli_w`. The writer fails loud if it sees any non-`[settings]`
  top-level table; comments inside `[settings]` are lost on
  rewrite. AC10 documents this.
- **Adapter contract drift on disk.** A user-configured value can go
  stale across a contract bump. The loader emits a one-line stderr
  warning and falls back to `DEFAULT_ADAPTER`; `get adapter` reports
  the fallback annotated `(builtin)` after the warning. This trades
  a silent rollback for a visible one.
- **Tests on developer machines that already have a config file.**
  The conftest fixture redirects `HOME`/`XDG_CONFIG_HOME`/`APPDATA`
  per test, so the real file is invisible to the suite. Verified by
  the explicit isolation test at T2.

## Changelog

- 2026-05-28: Initial plan.
- 2026-05-28: Pre-EXECUTE adversarial review pass 6. No blockers;
  test-spec polish only. AC13 substring assertion extended to
  include `--scope`, the sorted-list preamble, and all four escape
  hatches (previous version asserted only three, a regression in
  the `--scope` hint would have slipped through). New T1 test:
  `unset_setting` refuses non-string `[settings]` values (mirrors
  the existing `write_setting` test; AC10 promised both writers).
  T3 state_adapter-inadmissible test pins "no probe markers under
  `fake_home`" so a future paragraph-copy doesn't bias the probe.
- 2026-05-28: Pre-EXECUTE adversarial review pass 5 follow-up.
  Stale Approach prose (slice 2 + Risky parts bullet) rewritten to
  describe the pre-flight architecture rather than the deleted
  candidate-first rewrite. Pre-flight guarded by
  `state_adapter is None` — upgrades preserve their existing-install
  adapter; user-config doesn't mis-blame state-pin mismatches.
  AC13 message gains a `--scope` escape-hatch hint. AC11 wording on
  the contract-drift guard rephrased. New test:
  state_adapter-inadmissible + user_config falls through to existing
  upgrade.py refusal (no AC14). Testing Strategy table updated.
- 2026-05-28: Pre-EXECUTE adversarial review pass 5 (user-directed
  fail-loud redesign). Behavioural change: when user-config sets an
  adapter that isn't admissible at scope OR isn't in a pack's
  `allowed_adapters`, `_resolve_target_adapter` now **raises
  `_AdapterResolutionRefused` with a clear "pack X is not supported
  with your configured adapter Y" message**, instead of silently
  downgrading. Architectural simplification: a pre-flight block
  between Step 2 and Step 3+4 handles all user-config logic;
  Steps 3, 4, 4b, 5 are untouched. `configured_adapter` is now
  scope-agnostic — just a known-by-contract sanity check.
  Resolver-internals concerns dissolve: no `_probes` test seam
  (tests use the existing `fake_home` + filesystem pattern), no
  Step 4 candidate-first rewrite, no membership-check trap. New
  ACs: AC13 (scope-incapable refusal message), AC14
  (pack-incompatibility refusal message); existing AC13–AC18
  renumbered to AC15–AC20.
- 2026-05-28: Pre-EXECUTE adversarial review pass 4. Real bug caught:
  the pass-3 candidate-first rewrite would have broken every existing
  probe test, because `configured_adapter(None, scope="user")`
  returned `DEFAULT_ADAPTER` which then matched first in
  `allowed_adapters` and short-circuited the probe loop. Fix:
  `configured_adapter` now returns `str | None` — `None` means "no
  user-configured value", `str` means "user actively configured
  this". The Step 4 precedence-(i) check now reads `if candidate is
  not None and candidate in allowed_adapters`, which preserves the
  probe-by-default behavior. Step 4b/5 read
  `configured_adapter(...) or DEFAULT_ADAPTER`. Added a load-bearing
  regression test ("Probe still wins when user has no configured
  adapter"). Other fixes: `read_user_config` now fail-soft on
  malformed TOML (warn-and-null), so `agentbundle --help` works
  against a broken config file; `_probes` test seam added to
  `_resolve_target_adapter` as the chosen DI mechanism for
  probe-stub tests (no resolver monkey-patch); empty
  `allowed_adapters` AC removed from scope (pre-existing pre-PR
  behavior — punted with explicit out-of-scope assumption);
  `configured_adapter` purity wording softened to
  "side-effect-free w.r.t. caller state"; AST error message dropped
  the trailing `=`; conftest fixture documents the `fake_home`
  interaction.
- 2026-05-28: Pre-EXECUTE adversarial review pass 3. Real bugs
  caught: `configured_adapter` was scope-blind so a user setting
  adapter=copilot would leak Copilot at user scope despite RFC-0012's
  repo-only constraint — added `scope:` kwarg and per-scope
  admissibility check (`user_scope_capable_adapters_from_contract`
  at user scope, `shipped_adapters_from_contract` at repo scope);
  Step 4 user-scope probe used to short-circuit before user-config —
  reordered so user-config wins over probe, probe still wins over
  constant; `allowed_adapters=[]` crashed Step 4 with `IndexError`
  — added explicit Step 0 raise. AST walk in T5c now matches both
  `ast.Name` and `ast.Attribute` call shapes, pins the expected
  count == 7, and includes the keyword shape in failure messages.
  Help-audit walks `_actions` for `_SubParsersAction` instead of the
  three-deep private chain. T5b kwarg order matches the function
  signature. Writer fail-loud now explicitly tested against nested
  table `[settings.future]`. `configured_adapter` docstring
  separates primary `None`-handling from defense-in-depth
  invalid-value branch.
- 2026-05-28: Pre-EXECUTE adversarial review pass 2. Fixes: pin
  `contract_version="0.7"` on Step 4 / Step 4b membership-invariant
  tests (without it those tests fall to Step 5 and don't exercise
  the `allowed_adapters` check the rewrite is supposed to guard);
  add a separate Step 4b test (`scope="repo"`, no `allowed_adapters`);
  redesign T5c as an AST-based static check that walks every
  `_resolve_target_adapter` call site in install.py and upgrade.py
  and asserts `user_config=` is passed — no monkeypatch, no fragile
  fixture; tighten the help-audit test to assert structurally via
  the subparsers `choices` dict; extend the writer fail-loud guard
  to refuse non-string values under `[settings]` (AC10 promise was
  silently broken for arrays / inline tables / numerics); pin T5b's
  full kwargs list rather than `...`.
- 2026-05-28: Pre-EXECUTE adversarial review pass 1. Major rework:
  function rename to `_resolve_target_adapter`; expand T3 to cover
  the upgrade.py call sites; pin the candidate-first rewrite for
  `_resolve_target_adapter` (fixes membership-check bug); pin
  args-attachment dispatch contract for `_user_config`; pin
  fail-loud writer for non-`[settings]` top-level tables; loader
  warns and nulls on invalid on-disk adapter; AC15 weakened to
  sandboxing-only and the bypass-detection promise dropped;
  output format pinned to `<key>\t<value>\t(<provenance>)`;
  T5 split into subprocess + in-process resolver + upgrade
  coverage; subprocess sandbox verification moved from T2 to T4;
  `from __future__ import annotations` used to avoid the
  scope/user_config import cycle; forward-link to the existing
  install-from-clone how-to verified.
