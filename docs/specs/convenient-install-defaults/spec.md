# Spec: Convenient install defaults

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0036, RFC-0046, RFC-0047 (defaults the discovery verbs through the same chain); honours RFC-0031, RFC-0011/0012, RFC-0040 + ADR-0030
- **Contract:** none (CLI behaviour change to an existing command; no new API surface under `contracts/`)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user installing or upgrading packs should not have to spell out a catalogue
source on every command, and a downstream org fork behind an API gateway should
have a source it can actually point at. Today `catalogue` is a required
positional on `install`/`upgrade` with no default: the public PyPI user re-types
the same GitHub URI every time, and the gateway-bound editable fork has *no*
usable source — the resolver is `github.com`-only, the gateway blocks the
internal URL, and a fixed path can't be baked because every machine clones
elsewhere. Success is a bare `agentbundle install --pack X` that resolves a
sensible source with **zero extra command** for both populations — the public
user (→ the packaged GitHub default) and the editable fork (→ its own local
clone, wherever cloned) — while **never** letting a cloned repo or the current
working directory decide where executable code is fetched from. An explicit
`--catalogue` always overrides; a user's own `config set source` overrides
auto-detection.

> **Surface note:** `catalogue` is a **positional** argument, not a `--catalogue`
> flag. Where this spec writes "`--catalogue`" it denotes that positional (the
> shorthand the RFC used); there is no flag to add.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Resolve a default **only** through the four trusted-by-construction layers, in
  order, first-match-wins: `--catalogue` arg › user `[settings].source` ›
  editable detection (PEP 610) › packaged `_data/install-defaults.toml`.
- **Validate** each layer's output in `resolve_default_source()` before handing
  it to `resolve_catalogue` (markers present for a path; parseable URI) —
  `resolve_catalogue` itself does no **path/marker** validation (it rejects a
  `git+ssh://` prefix, but `catalogue.py:72` returns `Path(uri)` for every other
  non-`git+https` value with no existence or marker check).
- Keep an explicit `--catalogue` arg behaving **identically** to today
  (backward compatible); the default path only runs when the arg is omitted.
- Canonicalize (`Path.resolve()`) before walking, and **bound the editable
  walk-up to the enclosing `.git` repository root**, computed before any marker
  test.
- Emit a one-line stderr **diagnostic** when editable is detected but no
  catalogue root is found **between the editable package path and the enclosing
  `.git` root (inclusive)** — the walk is *upward*, the catalogue root is an
  ancestor — then defer to layer 4.

### Ask first

- Adding a **host** allowlist to the `source` validator (beyond the in-scope
  scheme check) — the RFC scopes the network layer as the upstream public default
  and flags integrity work as a separate follow-on; a host allowlist is a
  policy call, not part of this spec. (Scheme validation *is* in scope — see
  Acceptance Criteria.)

### Never do

- **Never** add a repo-scoped / repo-committed `source` layer. The source is a
  code-provenance boundary; the layer is omitted entirely (ADR-0036 D3), not
  gated behind a confirmation.
- **Never** fall back to `.`/cwd, or to any path the user did not explicitly
  supply, configure, or `pip install -e`. The only terminal states are a
  validated source or a clear error.
- **Never** auto-persist a one-off `--catalogue` (or any resolved layer) back to
  config — resolution is stateless; `config set source` is the only write path
  (ADR-0036 D4).
- The discovery verbs `list-packs` / `list-profiles` **default through the same
  chain** (RFC-0047): a bare query resolves via `resolve_catalogue_uri` exactly
  as `install`/`upgrade` do. This is safe — a gateway-bound fork is editable and
  resolves via layer 3, so a bare query never *silently* fetches upstream; only a
  wheel install reaches layer 4, where fetching the upstream catalogue is the
  expected, symmetric-with-install behaviour. (Originally a `Never do` here;
  reopened and decided by RFC-0047.)
- **Never** touch the adapter resolver (`scope.DEFAULT_ADAPTER`, the user-config
  adapter layer) — `source` is added *alongside* `adapter`, nothing else moves.
- **Never** treat the two editable-detection markers (`packs/` +
  `marketplace.json`) as a trust control — they are a forgeable accident-guard;
  the trust comes from the canonicalize + stop-at-first + repo-bounded-ascent
  rules.

## Testing Strategy

- **Layer precedence + validation + the no-cwd / no-repo-source invariants:**
  **TDD**. These are pure resolution logic over a stubbed environment
  (a fake `direct_url.json`, a tmp config, a tmp packaged default) with a
  compressible invariant — the canonical case for red-green-refactor.
- **Editable detection against a real `pip install -e`:** **manual QA exercised
  by an integration test**. The keystone the RFC de-risked by spike; verify it
  against a *real* editable install in an isolated venv (the artifact a user
  actually runs), reading the real `direct_url.json` and walking to the real
  clone root — not a mock of the metadata.
- **CLI wiring (`catalogue` optional on all four source verbs — `install`,
  `upgrade`, `list-packs`, `list-profiles`, per RFC-0047):** **goal-based
  check** — argparse accepts a bare `install --pack X` and a bare
  `list-packs`/`list-profiles`; verify by invoking the parser, no production
  test file beyond the per-task assertions.
- **`config set/unset/get source` round-trip (the literal write→read→remove):**
  **goal-based check** exercised by the existing config-command test shape
  (`test_config_cmd.py`, `test_user_config_io.py`).
- **The layer-2 read-back invariant** — `read_user_config` parses
  `[settings].source` onto `UserConfig.source` and `resolve_default_source`
  consumes it, plus independent fail-soft (a malformed `source` does not drop a
  valid `adapter`): **TDD**, alongside the precedence/validation invariants — it
  is a load-bearing invariant, not an artifact one-liner.
- **Packaging (`_data/install-defaults.toml` ships in the wheel):** **goal-based
  check** — read it back through the same bundled-data accessor the other
  `_data/` files use.

These verification modes are the *altitude* of each check; the editable-detection
behaviour only proves out across the install boundary, so it is named at
**integration** surface.

## Acceptance Criteria

- [x] `catalogue` is `nargs="?"` (default `None`) on the `install` and `upgrade`
  subparsers (`cli.py:247`, `:400`); an explicit `--catalogue`/positional value
  passes through to `resolve_catalogue` unchanged.
- [x] `catalogue` is also `nargs="?"` (default `None`) on `list-packs`
  (`cli.py:197`) and `list-profiles` (`cli.py:205`) — RFC-0047. When omitted,
  each handler resolves via `resolve_catalogue_uri(args)` (the same four-layer
  chain) before `resolve_catalogue`; an explicit positional passes through
  unchanged. Pinned by a test that a bare `list-packs`/`list-profiles` resolves
  the default (and the explicit-arg path is unchanged).
- [x] When `catalogue` is omitted on `install`/`upgrade`, the handler calls a
  shared `resolve_default_source()` whose result feeds `resolve_catalogue`. The
  shared call site is `commands/_common.resolve_catalogue_uri(args)`, used at
  **all three** resolve sites — `install.run` (single-pack), `install._run_profile`
  (`install --profile`), and `upgrade.run` — so a bare `install --profile X` (no
  catalogue) resolves through the default chain too, not just `install --pack X`.
  Pinned by a test that a bare `install --profile X` reaches `resolve_default_source`.
- [x] The **fourth** `args.catalogue` consumer — the `install._offer_upgrade`
  synthetic-namespace hand-off (`install.py:1739`, `ns.catalogue = args.catalogue`)
  — carries the **already-resolved** `catalogue_uri` from `install.run`, **not**
  `args.catalogue` (which is `None` on a bare install) and **not** a second
  independent resolution. So a bare `install` that triggers the upgrade offer
  hands the concrete resolved URI to `upgrade.run`, with no double-detection and
  no divergence risk. Pinned by a test.
- [x] `resolve_default_source()` resolves the four layers highest-first,
  first-match-wins: (1) `--catalogue` arg, (2) user `[settings].source`,
  (3) editable detection, (4) packaged `_data/install-defaults.toml`. Layer 2
  outranks layer 3 (an explicit `config set source` beats auto-detection).
- [x] Each layer's output is **validated** in `resolve_default_source()` before
  use, via an exact, allowlist discriminator (no parser-differential gap):
  1. a value beginning with the literal `git+https://` (case-sensitive, matching
     `catalogue.py`'s own `startswith` sink) is **accepted** (the one URL form
     `resolve_catalogue` fetches);
  2. else a value matching `^[A-Za-z]:[\\/]` (a Windows **drive path**, e.g.
     `C:\repo` / `C:/repo`) is the **local-path** branch;
  3. else a value whose `urllib.parse.urlsplit(value).scheme` is **non-empty**
     (any other scheme — `file://`, `file:/` single-slash, `http://`,
     `git+ssh://`, a mis-cased `GIT+HTTPS://`) is **rejected**;
  4. else (schemeless: `/abs/path`, `./rel`, `rel`) it is the **local-path**
     branch.
  A **local-path** source is accepted **iff both markers are present** at its
  `Path.resolve()`'d location; a rejected/invalid layer is **skipped**, never
  passed to the unvalidated `resolve_catalogue`. This is distinct from the
  deferred host allowlist (a policy call on an *accepted* `git+https` host).
- [x] **Confinement asymmetry is deliberate, not an oversight:** the
  canonicalize + repo-bounded-ascent confinement applies **only** to layer 3
  (auto-detected). Layers 2 and 4 path sources are validated for **marker
  presence only** — no confinement — because they are trusted-by-construction
  (the user typed `config set source`, or the distribution shipped the file),
  per ADR-0036 D1. The layer-3 keystone is the only place a path the user did
  *not* assert is consulted, so it alone earns the confinement check.
- [x] Editable detection reads
  `importlib.metadata.distribution("agentbundle").read_text("direct_url.json")`;
  it activates **only** when the record is present **and**
  `dir_info.editable == true`. A missing record (older pip, or a wheel install)
  falls through to layer 4 with no error.
- [x] Editable detection parses the `file://` `url` with the standard parser
  (`urllib.request.url2pathname` + percent-decoding) and **rejects** a
  non-empty / non-localhost `file://` host.
- [x] Editable detection **canonicalizes** the path (`Path.resolve()`) and walks
  up over canonicalized ancestors to the **first** one containing both `packs/`
  and `.claude-plugin/marketplace.json`, verifying each candidate stays under
  the resolved repository root.
- [x] Confinement to the clone is enforced on **canonicalized** paths, not
  assumed: the editable `file://` URL is `Path.resolve()`'d **first** (collapsing
  any symlink or `..`), the `.git` root is the nearest canonicalized ancestor of
  that resolved path, and **every candidate is a canonicalized ancestor-or-equal
  of the resolved editable path *and* a descendant-or-equal of the resolved
  `.git` root** — so the matched catalogue root always stays *inside* the clone
  the user `pip install -e`'d (the "inside the clone" precondition the
  forgeable-marker residual rests on). The walk is **upward**: because the
  package lives at `packages/agentbundle/` (no repo-root `pyproject.toml`), the
  recorded editable URL is that subdir and the catalogue root is an **ancestor**
  of it, reached by ascending — bounded above by the `.git` root.
- [x] The walk-up ascent is **bounded by the enclosing `.git` repository root**
  (nearest ancestor with a `.git` file *or* directory), computed before any
  marker test — a `packs/` + `marketplace.json` pair planted in a shared parent
  *above* the clone is never matched.
- [x] The bound is a **closed interval**: the `.git`-root directory **itself** is
  a legal marker-match candidate (the catalogue root coincides with the git root,
  so the only valid match sits *at* the boundary). The catalogue-root == git-root
  case resolves rather than falling through to layer 4.
- [x] A real `pip install -e packages/agentbundle` in a **throwaway venv the test
  builds itself** (`python -m venv`, not the ambient editable record) resolves,
  via editable detection, to the clone root (the dir holding `packs/` +
  `.claude-plugin/marketplace.json`) — verified end-to-end, not against a mocked
  `direct_url.json`. The test is
  `tests/integration/test_editable_source_detection.py`; because `make
  build-check` runs no pytest, it is **wired into CI explicitly** in
  `build-check.yml` (per the repo's per-path test-wiring convention) or it never
  gates. (the construction-test keystone)
- [x] The `.git` repo-boundary detection recognizes `.git` as a **regular file**
  (the git-worktree / submodule gitdir pointer), not only a directory — pinned by
  a unit test, since the keystone itself runs in a Conductor worktree where `.git`
  is a file.
- [x] When editable is detected but **no** catalogue root is found between the
  editable package path and the enclosing `.git` root inclusive (e.g. a sparse
  checkout missing `packs/`), the resolver emits a
  one-line diagnostic on **stderr** (not stdout) whose text contains the
  substrings `editable install detected` and `deferring to packaged default`,
  then **returns the layer-4 source** (resolution continues) — never silent,
  never a hard error on a default, never the cwd. Pinned by a goal-based check
  asserting the stream, the substrings, and that layer 4 is returned.
- [x] **No resolution layer ever *implicitly* resolves from `.`/cwd**, and **no
  repo-scoped `source` layer exists** — asserted as explicit negative criteria (a
  planted cwd source / repo-root source is not consulted). The forbidden thing is
  an *implicit* cwd fallback (the resolver inventing `.` when no layer yielded a
  source). A **user-asserted** relative path — an explicit `catalogue` positional,
  or `config set source ./rel` — is the user's own input and *is* honoured
  (resolved cwd-relative via `Path.resolve()`), per the trust-boundary carve-out;
  that is not the resolver consulting cwd on its own.
- [x] When **no** layer yields a source, the command errors clearly with text
  naming all three recovery paths (the user-facing text names the real surface —
  a trailing catalogue argument — not the `--catalogue` shorthand this spec uses
  elsewhere, since no such flag exists):
  `no catalogue source: pass a catalogue argument, run 'agentbundle config set source …', or pip install -e the catalogue`.
- [x] Resolution writes nothing on **any** path — a one-off `--catalogue` (or any
  auto-resolved layer) does **not** persist to the user config (no
  write-on-install), including the editable-detected-but-deferred (diagnostic) and
  all-layers-empty (error) paths.
- [x] `source` is added to `_KNOWN_KEYS`, the `UserConfig` dataclass, **and the
  `read_user_config` loader** (`user_config.py`) alongside `adapter`, **user scope
  only** — so a value written by `config set source` is actually parsed back onto
  `UserConfig.source` and consumed by layer 2 (a read-back test proves resolution
  consumes it, closing the write-only gap). `config set source <uri>`, `config
  get source`, and `config unset source` round-trip. `config get source` is wired
  through a `source` branch in `_effective_value`: a value present in the file
  reports provenance `file`; absent reports provenance `unset` (there is **no**
  builtin constant for `source` — the layer-4 packaged default is not a config
  value). The unset path is named in the all-layers-empty diagnostic.
- [x] The write-time `config set source` validation is **parseable-only** (it
  does *not* scheme-gate); the scheme gate lives in `resolve_default_source()`.
  So `config set source http://…` is **accepted-but-inert** — it persists, then
  is rejected (and skipped) at resolution. This split is intentional (the value
  can be set, then rejected with a diagnostic), not a drift between the two
  checks.
- [x] A new packaged `_data/install-defaults.toml` ships in the wheel via the
  existing `[tool.setuptools.package-data]` `agentbundle = ["_data/*"]` wiring,
  declaring
  `[defaults] source = "git+https://github.com/eugenelim/agent-ready-repo"`;
  an absent or empty file means no layer-4 default (the private-fork pattern).
- [x] The adapter resolver is unchanged: the ~13 adapter default-resolution tests
  and `tests/unit/test_resolve_user_scope_target_adapter.py` stay green.
- [ ] Integrity-pinning for the layer-4 `git+https` fetch is out of scope here (deferred: convenient-install-defaults-followons).
  The integrity follow-on's finish line is named, not open-ended: **resolve `main`
  to a pinned commit SHA and verify the fetched archive digest** (not merely "add
  pinning"). (`list-packs`/`list-profiles` defaulting, previously deferred here,
  is now **implemented** under RFC-0047 — see the discovery-verb AC above.)

## Assumptions

- Technical: `pip install -e` records an absolute `file://` URL with
  `dir_info.editable == true` per PEP 610, and the catalogue root is locatable by
  a repo-bounded walk-up from the recorded editable-package path (source: RFC-0046
  §Evidence spike; PEP 610).
- Security: `direct_url.json` (in the venv's `*.dist-info/`, outside the clone) is
  the layer-3 trust anchor and is **user-writable** — at the same trust level as
  the clone itself. Its tampering is an **accepted residual**: anything running as
  the user can already redirect their own install, and layers 1–3 are "local
  trust" precisely on that basis. Named here so it is in-the-accepted-residual,
  not silently assumed unwritable (source: probe — `dist-info` is user-writable;
  RFC-0046 §Risks trust model).
- Technical: `resolve_catalogue` accepts a local path but performs **no**
  existence/marker validation — so `resolve_default_source()` must validate
  before calling it (source: probe `catalogue.py:55-72`, confirmed 2026-06-25).
- Technical: the user config file is OS-conventional, **not** a fixed
  `~/.config/...` path — `~/Library/Application Support/agentbundle/config.toml`
  (macOS), `%APPDATA%/agentbundle/config.toml` (Windows),
  `$XDG_CONFIG_HOME` / `~/.config/agentbundle/config.toml` (Linux); the `source`
  key joins the same `[settings]` table as `adapter` (source: probe
  `user_config.py:35,56-79`, confirmed 2026-06-25 — corrects the RFC prose's
  `~/.config` shorthand).
- Technical: `_data/*` is already packaged by `pyproject.toml`'s
  `[tool.setuptools.package-data]`, so a new `install-defaults.toml` is picked up
  with no packaging change (source: probe `pyproject.toml`, confirmed 2026-06-25).
- Technical: the catalogue root coincides with the git root (the `packs/` +
  `marketplace.json` markers sit at the `.git` directory); a catalogue nested in a
  larger repo or vendored as a submodule is out of scope for editable detection
  and falls through to layer 4 (source: RFC-0046 §Key assumptions).
- Process: implementation lands as a **separate PR**; this PR delivers only the
  ADR + spec + plan (source: user direction 2026-06-25; RFC-0046 §Follow-on
  artifacts).
