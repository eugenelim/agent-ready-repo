# Spec: agentbundle-config-subcommand

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0011](../../rfc/0011-pack-allowed-adapters.md), [RFC-0012](../../rfc/0012-repo-scope-per-adapter-projection.md)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

After `pip install agentbundle`, a user can change the default adapter on
their machine without editing source or monkey-patching a constant. They
run `agentbundle config set adapter codex`, and every subsequent
invocation whose adapter resolution today reaches the `scope.DEFAULT_ADAPTER`
fallback now resolves to `codex` instead. Concretely: every site that
calls `_resolve_target_adapter` in `install.py` (lines 335, 424, 547,
1989, 2050) and `upgrade.py` (lines 257, 396) consults the user-configured
value, layered above the constant. The user discovers the feature via
`agentbundle --help` (which lists `config` alongside the other subcommands)
and via a single onboarding doc that also covers the two operations a
fresh PyPI user actually performs (install agentbundle, install a pack).
Existing override paths — the `--adapter` flag at install time, the
state-hint short-circuit on upgrade, downstream catalogue monkey-patching
of `scope.DEFAULT_ADAPTER` — keep working unchanged. The new layer slots
in between the state-hint short-circuit (Step 2) and the contract-version
gate (Step 3), so a *fresh* install honors the configured adapter while
an *upgrade* of an existing pack preserves whatever adapter the original
install used. When the configured adapter is incompatible with the pack
or the scope, the resolver refuses with a clear, actionable message
rather than silently downgrading — the user's intent stays visible.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Thread the loaded user config through call chains as an explicit parameter
  (a `UserConfig` value, or `None`). The resolver `scope.configured_adapter`
  takes `UserConfig | None`; `_resolve_target_adapter` takes
  `user_config: UserConfig | None = None`. Tests assert behavior by
  passing the parameter directly.
- Use the args-attachment dispatch contract: `cli.py:main()` loads the
  user config once and attaches it to `args._user_config` before
  dispatching to the handler. Handlers that need the value read
  `getattr(args, "_user_config", None)` and pass it on. Test handlers
  construct an `argparse.Namespace` with `_user_config=...` explicitly.
  No handler reads user-config from disk on its own.
- Validate `adapter` values against `shipped_adapters_from_contract()`
  at *write* time; refuse unknown values with a one-line error that
  lists the admissible names. Also validate at *load* time and emit a
  one-line stderr warning when an on-disk value is no longer admissible
  (covers adapter-contract drift); the loader returns
  `UserConfig(adapter=None)` in that case so the resolver falls back to
  the constant.
- Fail soft at load time on malformed TOML. A `tomllib.TOMLDecodeError`
  during `read_user_config` emits a one-line stderr warning naming the
  offending file path and the line/column from the exception, and
  returns `UserConfig(adapter=None)`. This keeps `agentbundle --help`
  and `agentbundle config path` working when the user's config file is
  broken — without it, every subcommand including help would fail
  cold. `agentbundle config get adapter` reports the fallback as
  `adapter\t<DEFAULT_ADAPTER>\t(builtin)` after the warning. Out of
  scope: an `agentbundle config repair` action; users can either
  hand-edit or `unset` the file via the path printed by `config path`.
- Use stdlib `tomllib` for reading. Write TOML by hand using the
  one-key-at-a-time pattern already in `agentbundle.config`. Comments
  and formatting are not preserved across `set` and `unset` — same
  contract as `.agentbundle-state.toml`.
- `unset` deletes the file when removing the last key leaves
  `[settings]` empty *and* no other top-level tables are present;
  otherwise the file is rewritten with the remaining content.

### Ask first

- Adding any runtime dependency to `packages/agentbundle/pyproject.toml`
  (today it is `dependencies = []`, intentionally). The user-config-dir
  resolver replaces `platformdirs` with ~25 lines of platform branching;
  any deviation needs sign-off.
- Introducing a new top-level config table beyond `[settings]`, or
  per-repo / per-scope config files. Repo-scope config is explicitly
  out of scope for this spec.
- Adding a second registered setting key beyond `adapter`. The framework
  is generic so adding one is a one-line registry edit, but the
  *decision* to register one is not in this spec's scope.

### Never do

- Read the user config from any module-level global or cache that
  bypasses the args-attachment contract above. The codebase rule
  (confirmed in conversation): "everything should be driven by isolated
  context and config; no monkey-patching for tests."
- Introduce an `AGENTBUNDLE_*` environment variable as a third
  resolution layer. The codebase has no such precedent and the CLI
  flag already covers per-invocation overrides. (`XDG_CONFIG_HOME`,
  `HOME`, `APPDATA` — read by the path resolver — are *not* override
  layers; they are platform-standard pointers to *where the file lives*.)
- Mutate the historical-data defaults at `PackState.adapter`'s field
  default in `config.py` (currently line 133) or the `raw_adapter`
  fallback in the state reader (currently line 236). Those
  `"claude-code"` literals are read-time defaults for v0.2-vintage
  state-file rows and are deliberately pinned, not the runtime
  resolution hook.
- Preserve unknown content under any top-level table other than
  `[settings]` when writing. The writer refuses with a one-line
  "future setting table not yet supported" error if it sees one.
  Documented in *Risks* (plan.md).
- Add the new reference page under any pack's `seeds/` tree.
  `docs/guides/**/*.md` is in `EXCLUDED_PATTERNS` — native to this
  repo, not projected. New pages land directly.
- Add a structural temptation: a generic "Setting" abstraction class
  per registered key, a "ConfigStore" service-locator, or a settings
  module hierarchy. One registry dict + four action functions covers
  every case in scope.

## Testing Strategy

| Behavior                                                                                                            | Mode             | Why                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------ |
| User-config-dir path resolution per platform                                                                        | TDD              | Pure function over `(sys.platform, env, home)` → `Path`. Compressible invariants, branch coverage matters.         |
| `configured_adapter()` known-by-contract sanity check                                                                | TDD              | Pure function over `(user_config,)` → `str | None`. Reports the configured adapter when known by the bundled contract; scope and pack enforcement live in the resolver. |
| `set` / `get` / `unset` / `path` subaction behavior                                                                  | TDD              | Each is a small function with a clear input/output contract; file mutations are observable.                         |
| Validation refuses unknown adapter values at write; warns and falls back at load                                    | TDD              | Two surfaces, both pure logic; warning text is a checkable string.                                                 |
| `_resolve_target_adapter` consults `user_config` at every fallback site (install + upgrade)                          | TDD              | The seven call sites are mechanical; the function is pure given its inputs. AST static check covers AC15(c).        |
| `_resolve_target_adapter` raises with the AC14 message when the configured adapter is not in pack `allowed_adapters` | TDD              | The pack-incompatibility refusal contract. Substring-asserts on the message body so a future wording shift fails.   |
| `_resolve_target_adapter` raises with the AC13 message when the configured adapter is not admissible at `scope`      | TDD              | The scope-incapable refusal contract (Copilot at user scope is the canonical case).                                 |
| Pre-flight runs only when `state_adapter is None` — upgrades preserve their existing adapter                          | TDD              | Load-bearing invariant; without it, upgrades would mis-blame user-config for state-pin mismatches.                  |
| `install.run` and `upgrade.run` attach the loaded user-config and pass it to the resolver                            | TDD              | Handler-level wiring; testable by constructing an `argparse.Namespace` with `_user_config` set.                    |
| End-to-end cascade: `set adapter codex` then the in-process resolver call returns `codex`                            | Goal-based check | Tmp HOME via fixture; write file; load; call `_resolve_target_adapter(..., user_config=loaded)` and assert result. |
| `agentbundle --help` and `agentbundle config --help` list the new surface                                            | Goal-based check | Run the parser's `format_help()`, grep the output.                                                                 |
| Test isolation: no test reads or writes the developer's real user-config-dir                                        | Goal-based check | A conftest autouse fixture redirects `HOME`/`XDG_CONFIG_HOME`/`APPDATA` to a per-test sandbox. Subprocess tests inherit the env. |

Manual QA is not needed; every behavior above is mechanically verifiable.

## Acceptance Criteria

1. **AC1.** `agentbundle config --help` prints help text listing the four
   actions: `get`, `set`, `unset`, `path`.
2. **AC2.** `agentbundle --help` lists `config` in argparse's `subcommands:`
   block, with a one-line description.
3. **AC3.** `agentbundle config path` prints the absolute path the CLI
   would read or write. Exits 0 whether or not the file exists.
4. **AC4.** Path resolution honors platform conventions: macOS →
   `~/Library/Application Support/agentbundle/config.toml`; Linux →
   `${XDG_CONFIG_HOME:-~/.config}/agentbundle/config.toml`; Windows →
   `%APPDATA%/agentbundle/config.toml` (and `~/AppData/Roaming/...`
   when `APPDATA` is unset). Verified by unit tests that pass
   `platform`, `env`, and `home` as explicit parameters to a pure
   function.
5. **AC5.** `agentbundle config get` with no key prints every known key
   under `[settings]` and its effective value with provenance, one
   line per key. **Output format:** `<key>\t<value>\t(<provenance>)`
   where provenance is `file`, `file-invalid`, or `builtin`. Exits 0.
6. **AC6.** `agentbundle config get adapter` prints the effective adapter
   in the same one-line format as AC5. Exits 0.
7. **AC7.** `agentbundle config get <unknown-key>` exits non-zero with
   a message naming the known keys. No file is created.
8. **AC8.** `agentbundle config set adapter <name>` validates `<name>`
   against `shipped_adapters_from_contract()`; on success, writes the
   file (creating the parent directory if missing) and exits 0. On
   refusal, exits non-zero, prints a message listing the admissible
   names, and writes nothing.
9. **AC9.** `agentbundle config set <unknown-key> <value>` exits non-zero
   without writing.
10. **AC10.** `agentbundle config unset adapter` removes the key. If
    `[settings]` is empty after removal and the file contains no other
    top-level tables, the file is deleted; otherwise the file is
    rewritten with the remaining `[settings]` entries (which are
    string-valued by contract — see below). Comments and formatting
    are not preserved — same contract as `.agentbundle-state.toml`.
    Either way, exits 0. Unsetting a missing key exits 0 (idempotent).
    **Writer scope:** the writer refuses to operate on a file that
    contains (a) any non-`[settings]` top-level table, or (b) any
    non-string value under `[settings]`. Both cases raise with a
    "future setting type not yet supported" message and the original
    file is not mutated. AC10's "rewritten with the remaining content"
    promise covers `[settings]` entries of shape `key = "string"` only.
11. **AC11.** A new function `scope.configured_adapter(user_config:
    "UserConfig | None") -> str | None` returns
    `user_config.adapter` when it is set *and* in
    `shipped_adapters_from_contract()` (the contract-drift guard:
    an adapter dropped from `shipped` since the user wrote their
    config returns `None` here and falls through to the constant —
    same fail-soft as the loader's on-disk validation); returns
    `None` otherwise. The function is scope-agnostic and
    pack-agnostic — it reports "what did the user configure, if
    anything sensible" only. Scope-capability and
    pack-`allowed_adapters` enforcement is the *resolver's* job
    (AC12), not this function's. The `None` return lets callers
    distinguish "user actively configured a value" from "no
    user-config; existing behavior". Side-effect-free w.r.t.
    caller state; reads the bundled adapter contract via the
    existing helpers. (`UserConfig` is referenced as a
    forward-declared annotation via `from __future__ import
    annotations` — no runtime import from `scope.py` into
    `user_config.py`, avoiding the cycle.)
12. **AC12.** Every call site of `_resolve_target_adapter` —
    `install.py:335, 424, 547, 1989, 2050` and `upgrade.py:257,
    396` — threads a `user_config: UserConfig | None` argument
    (verified by a static AST check, AC15(c)). Inside
    `_resolve_target_adapter`, a **user-config pre-flight block**
    runs between the existing Step 2 (state-hint short-circuit)
    and Step 3+4 (contract-version gate), **only when
    `state_adapter is None`**. The `state_adapter is None` guard
    preserves the upgrade-doesn't-rewrite-existing-install
    invariant: if a state file already pins an adapter (admissible
    or not), the existing Step 2 / Step 3+ + `upgrade.py`'s
    cross-adapter refusal handle it; user-config doesn't fire its
    "pack not supported with your configured adapter" refusal for
    what is actually a state-pin mismatch. The pre-flight reads
    `candidate = configured_adapter(user_config)` and:

    - If `candidate is None`, the pre-flight does nothing — Steps
      3, 4, 4b, 5 run as today (with the trivial rewrite below).
      This is the load-bearing "preserve probe-by-default" path:
      users who never ran `agentbundle config set` see existing
      behavior.
    - If `candidate` is set but not admissible at scope (e.g.
      `candidate == "copilot"` and `scope == "user"`), the
      pre-flight raises `_AdapterResolutionRefused`. See AC13
      for the exact message.
    - If `candidate` is set and admissible at scope, but
      `allowed_adapters is not None` and `candidate not in
      allowed_adapters`, the pre-flight raises
      `_AdapterResolutionRefused`. See AC14 for the exact
      message.
    - If `candidate` is set, admissible at scope, and (when
      `allowed_adapters` is supplied) in `allowed_adapters`, the
      pre-flight **returns** `candidate` immediately. Steps 3, 4,
      4b, 5 do not run.

    **Trivial rewrite for Steps 4b and 5** when the pre-flight
    didn't return: both today do `return DEFAULT_ADAPTER`; that
    stays exactly as it is. Step 4 also stays as it is — the
    pre-flight already filtered out user-config, so Step 4's
    existing probe / `DEFAULT_ADAPTER` / `allowed_adapters[0]`
    cascade is unchanged. **Step 0 / Step 1 / Step 2 are untouched.**
    `scope.DEFAULT_ADAPTER` remains exported and importable for
    downstream catalogue monkey-patching.
13. **AC13 (scope-incapable refusal message).** When the
    pre-flight raises because the configured adapter isn't
    admissible at `scope`, the message reads:
    ```
    <command_name>: configured adapter '<candidate>' is not
    supported at <scope> scope. Adapters supported at <scope>
    scope: <sorted list>. To proceed: invoke the command at a
    different scope (e.g. --scope repo) where '<candidate>' is
    supported, or pass --adapter <name> for a per-install
    override, or run `agentbundle config set adapter <name>` to
    change the default, or `agentbundle config unset adapter` to
    clear it.
    ```
    The user reads this and sees four escape hatches — the
    `--scope` hint matters because the user may have configured a
    repo-only adapter (e.g. `copilot`) deliberately for repo-scope
    installs and stumbled into a user-scope command.
14. **AC14 (pack-incompatibility refusal message).** When the
    pre-flight raises because the pack doesn't support the
    configured adapter, the message reads:
    ```
    <command_name>: pack <pack_name> is not supported with your
    configured adapter '<candidate>'. The pack supports: <sorted
    allowed_adapters list>. To proceed: pass --adapter <name> for
    a per-install override, or run `agentbundle config set
    adapter <name>` to change the default, or `agentbundle config
    unset adapter` to clear it.
    ```
    "Is not supported" rather than "silently downgraded" — the
    user's intent is preserved and the pack is the thing that
    "isn't supported", not their config.
15. **AC15.** The end-to-end cascade has three integration tests, all
    using the conftest isolation sandbox:
    - **(a) Subprocess test.** A `subprocess.run` of `agentbundle
      config set adapter codex` followed by `agentbundle config get
      adapter` reports `codex\tcodex\t(file)`; followed by
      `agentbundle config unset adapter` then `get adapter` reports
      `adapter\t<DEFAULT_ADAPTER>\t(builtin)`.
    - **(b) In-process resolver test.** After `set adapter codex`
      writes a real file under the sandbox, an in-process call to
      `_resolve_target_adapter(pack_dir, scope="user",
      contract_version="0.7", user_config=load_user_config())`
      returns `"codex"`. This test uses the *resolver function under
      test*, not just the `configured_adapter` self-report, so the
      integration is genuine and not a tautology.
    - **(c) AST static check.** A test walks
      `install.py` and `upgrade.py`, finds every call to
      `_resolve_target_adapter` (matching both `ast.Name` and
      `ast.Attribute` shapes), asserts each has `user_config=` in
      its `keywords`, and asserts the total call count equals 7 —
      five in install.py, two in upgrade.py. Per-callsite assertion
      messages include the file:line and the keyword names actually
      present so a future failure prints the call's shape.
16. **AC16.** Every existing test in `packages/agentbundle/tests/`
    (CLI / integration) and `packages/agentbundle/agentbundle/build/tests/`
    (adapter / contract) continues to pass. In particular the five
    monkeypatch-of-`DEFAULT_ADAPTER` tests at
    `tests/unit/test_resolve_user_scope_target_adapter.py:160, 176,
    534, 581, 593` pass without edit, because `user_config=None`
    is the default and Steps 3/4/4b/5 are unchanged.
17. **AC17.** A new autouse function-scoped fixture in
    `packages/agentbundle/tests/conftest.py` sets `HOME`,
    `XDG_CONFIG_HOME`, and `APPDATA` to a per-test sandbox via
    `monkeypatch.setenv`. The fixture's contract is narrow and exact:
    *no test reads or writes the developer's real user-config-dir*.
    Bypass-detection is not claimed — the goal is sandboxing, not
    enforcement of parameter-injection style in production code. A
    deliberate sandbox-verification test demonstrates the fixture by
    calling the path resolver with defaults and asserting the result
    lies inside the per-test tmp_path.
18. **AC18.** A new reference page lands at
    `docs/guides/reference/agentbundle.md` covering, in this order:
    `pip install agentbundle` (with a working forward-link to the
    existing `docs/guides/how-to/install-agentbundle-from-clone.md`),
    installing a pack, and configuring the default adapter via the new
    subcommand. Cross-linked from `docs/guides/reference/README.md`.
19. **AC19.** Zero new runtime dependencies in
    `packages/agentbundle/pyproject.toml`. The diff to that file is
    empty (or limited to comments / formatting).
20. **AC20.** Gates pass: lint, typecheck, and the project's full test
    command (covering both
    `packages/agentbundle/tests/` and
    `packages/agentbundle/agentbundle/build/tests/`) all exit 0 on the
    final commit.

## Assumptions

- **Technical**: Python ≥ 3.11; `tomllib` is stdlib. (source:
  `packages/agentbundle/pyproject.toml:9`)
- **Technical**: `packages/agentbundle` has zero runtime dependencies and
  the spec must preserve that. (source:
  `packages/agentbundle/pyproject.toml:10`)
- **Technical**: `DEFAULT_ADAPTER` is consumed at runtime *only* in
  `install.py` (lines 2237 import, 2338, 2339, 2357, 2365). No other
  `commands/*.py` reads it. (source: repo grep,
  `grep -rn DEFAULT_ADAPTER packages/agentbundle/agentbundle/commands/`
  returns matches only in `install.py`.)
- **Technical**: The resolution helper is `_resolve_target_adapter`
  (defined at `install.py:2173`); the legacy file name
  `test_resolve_user_scope_target_adapter.py` predates RFC-0012's
  rename and was not renamed for git-blame continuity. Tests inside it
  import `_resolve_target_adapter`. (source: repo grep)
- **Technical**: `_resolve_target_adapter` is called from seven sites:
  `install.py:335, 424, 547, 1989, 2050` and `upgrade.py:257, 396`.
  No other call sites. (source: repo grep,
  `grep -rn _resolve_target_adapter packages/agentbundle/agentbundle/commands/`)
- **Technical**: `config.py:133` (`PackState.adapter` field default) and
  `config.py:236` (`raw_adapter` fallback in the state reader) carry
  `"claude-code"` literals that are historical-data defaults for
  v0.2-vintage state-file rows, deliberately pinned, *not* runtime
  hooks. (source: file read, comments in-situ)
- **Technical**: Existing tests monkeypatch `DEFAULT_ADAPTER` directly
  (`tests/unit/test_resolve_user_scope_target_adapter.py:160, 176, 534,
  581, 593`) to exercise the documented downstream-catalogue
  monkey-patch path. They keep passing because `configured_adapter(None)`
  returns the constant — the new resolver is additive. (source: repo
  grep)
- **Technical**: `docs/guides/**/*.md` is in `EXCLUDED_PATTERNS` in
  `self_host.py:311` — native to this repo, not pack-projected. New
  reference page lands directly. (source:
  `packages/agentbundle/agentbundle/build/self_host.py:311`)
- **Technical**: The CLI dispatch is `mod.run(args)` with a single
  `argparse.Namespace` positional (`cli.py:407`). Threading
  `user_config` to handlers happens by attaching it to the namespace
  as `args._user_config` in `cli.py:main()` before `args.func(args)`
  is called. (source: `cli.py:395-447`)
- **Process**: New deps must be recorded in package `AGENTS.md` or an
  ADR. This spec adds zero deps, so no ADR is required. (source: root
  `AGENTS.md` § *Check before acting*)
- **Process**: RFC-0011 and RFC-0012 exist and govern the
  `DEFAULT_ADAPTER` contract; this spec layers on top without changing
  that contract. (source: `docs/rfc/0011-*.md`, `docs/rfc/0012-*.md`)
- **Process**: Additive CLI subcommands do not require an RFC. (source:
  grep of `docs/CONVENTIONS.md`; no rule found)
- **Product**: User-config wins over a downstream-catalogue-monkey-patched
  `DEFAULT_ADAPTER`. Local user agency principle; lockdown would be a
  separate RFC. (source: user confirmation 2026-05-28)
- **Product**: Resolver name is `scope.configured_adapter()`. (source:
  user confirmation 2026-05-28)
- **Product**: Test isolation is via parameter injection at the
  resolver and env-redirect at subprocess boundaries; no monkeypatch
  of resolver internals. (source: user confirmation 2026-05-28)
- **Product**: One new reference page covers install agentbundle, install
  pack, and configure adapter. `--help` is part of the documented
  surface. (source: user confirmation 2026-05-28)
- **Product**: `unset` deletes the file only if no other settings remain.
  (source: user confirmation 2026-05-28)

## Changelog

- 2026-05-31: Status reconciled to Shipped (retroactive). Implementation landed in a prior PR: the `agentbundle config {get,set,unset,path}` subcommand (`commands/config.py`, wired in `cli.py`), the `scope.configured_adapter` reporter, the `_resolve_target_adapter` pre-flight block, the fail-soft TOML loader, the autouse HOME/XDG/APPDATA conftest fixture, and the `docs/guides/reference/agentbundle.md` page. ACs use a non-checkbox format; verified against the merged tree. No deferrals.
- 2026-05-28: Initial draft.
- 2026-05-28: Pre-EXECUTE adversarial review pass 5 (user-directed
  fail-loud redesign). Behavioural change: when user-config sets an
  adapter that isn't admissible at scope OR isn't in a pack's
  `allowed_adapters`, `_resolve_target_adapter` now **raises with
  a clear "pack X is not supported with your configured adapter Y"
  message** (new AC13, AC14) instead of silently downgrading.
  Architectural simplification: a pre-flight block between Step 2
  and Step 3+4 handles all user-config logic; Steps 3, 4, 4b, 5 are
  untouched. `configured_adapter` is now scope-agnostic — just a
  known-by-contract sanity check. AC numbering: AC13 + AC14 added;
  former AC13–AC18 renumbered to AC15–AC20. AC16 wording
  simplified — existing tests pass because `user_config=None` is
  the default and the unchanged Steps 3+ run as today.
- 2026-05-28: Pre-EXECUTE adversarial review pass 4. AC11 shape
  changed: `configured_adapter` now returns `str | None` rather
  than `str`. The `None` return is load-bearing — it lets callers
  distinguish "user configured something" from "no user-config",
  which preserves the existing probe-by-default behavior in
  `_resolve_target_adapter`. AC12 wiring updated accordingly:
  precedence-(i) now reads `if candidate is not None and candidate
  in allowed_adapters`. *Always do* adds the fail-soft malformed-TOML
  contract — so `agentbundle --help` keeps working against a broken
  config file. Empty-`allowed_adapters` AC removed (pre-existing
  behavior, punted). See plan changelog for the rest.
- 2026-05-28: Pre-EXECUTE adversarial review pass 3. AC11 widened
  to `configured_adapter(user_config, *, scope: str)` so user-scope
  cannot return a repo-only adapter even when user-config requests
  one. AC12 pins precedence — configured candidate beats probe;
  probe beats constant; `allowed_adapters=[]` raises at Step 0
  before any fallback runs. AC13 gains a third sub-test (c): AST
  static check walks both `ast.Name` and `ast.Attribute` call
  shapes and asserts the call count is exactly 7. See plan
  changelog for the rest.
- 2026-05-28: Pre-EXECUTE adversarial review pass 2. AC10 tightened
  to clarify the writer refuses non-string values under `[settings]`
  in addition to non-`[settings]` top-level tables; "rewritten with
  the remaining content" promise now scoped to `key = "string"` shape
  only. Plan-side fixes: test-suite `contract_version` pinning,
  Step 4b coverage added, T5c redesigned as AST static check, help
  audit moved to structural assertion. See plan changelog.
- 2026-05-28: Pre-EXECUTE adversarial review pass 1. Fixes:
  function rename to `_resolve_target_adapter`; expand AC12 to all
  seven call sites including `upgrade.py`; pin args-attachment dispatch
  contract; weaken AC15 to sandboxing-only; pin fail-loud writer for
  non-`[settings]` tables; warn-and-fallback on invalid on-disk
  adapter; rewrite resolver logic so user-config cannot bypass
  `allowed_adapters`; document `unset` comment-loss; widen test
  coverage to both test roots; cite by symbol + parenthesized line;
  pin output format.
