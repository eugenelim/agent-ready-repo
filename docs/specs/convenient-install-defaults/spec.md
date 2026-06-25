# Spec: Convenient install defaults

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0036, RFC-0046; honours RFC-0031, RFC-0011/0012, RFC-0040 + ADR-0030
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

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Resolve a default **only** through the four trusted-by-construction layers, in
  order, first-match-wins: `--catalogue` arg › user `[settings].source` ›
  editable detection (PEP 610) › packaged `_data/install-defaults.toml`.
- **Validate** each layer's output in `resolve_default_source()` before handing
  it to `resolve_catalogue` (markers present for a path; parseable URI) —
  `resolve_catalogue` itself does no validation (`catalogue.py:72` returns
  `Path(uri)` unconditionally).
- Keep an explicit `--catalogue` arg behaving **identically** to today
  (backward compatible); the default path only runs when the arg is omitted.
- Canonicalize (`Path.resolve()`) before walking, and **bound the editable
  walk-up to the enclosing `.git` repository root**, computed before any marker
  test.
- Emit a one-line stderr **diagnostic** when editable is detected but no
  catalogue root is found at/below the repo boundary, then defer to layer 4.

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
- **Never** default the catalogue on the discovery verbs `list-packs` /
  `list-profiles` — they keep requiring an explicit catalogue (follow-on).
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
- **CLI wiring (`catalogue` optional on `install`/`upgrade`, still required on
  `list-packs`/`list-profiles`):** **goal-based check** — argparse accepts a
  bare `install --pack X` and rejects a bare `list-packs`; verify by invoking
  the parser, no production test file beyond the per-task assertions.
- **`config set/unset/get source` round-trip:** **goal-based check** exercised by
  the existing config-command test shape (`test_config_cmd.py`,
  `test_user_config_io.py`).
- **Packaging (`_data/install-defaults.toml` ships in the wheel):** **goal-based
  check** — read it back through the same bundled-data accessor the other
  `_data/` files use.

These verification modes are the *altitude* of each check; the editable-detection
behaviour only proves out across the install boundary, so it is named at
**integration** surface.

## Acceptance Criteria

- [ ] `catalogue` is `nargs="?"` (default `None`) on the `install` and `upgrade`
  subparsers (`cli.py:247`, `:400`); an explicit `--catalogue`/positional value
  passes through to `resolve_catalogue` unchanged.
- [ ] `catalogue` **remains a required positional** on `list-packs` (`cli.py:197`)
  and `list-profiles` (`cli.py:205`); a bare invocation of either errors.
- [ ] When `catalogue` is omitted on `install`/`upgrade`, the handler calls a
  shared `resolve_default_source()` whose result feeds `resolve_catalogue`.
- [ ] `resolve_default_source()` resolves the four layers highest-first,
  first-match-wins: (1) `--catalogue` arg, (2) user `[settings].source`,
  (3) editable detection, (4) packaged `_data/install-defaults.toml`. Layer 2
  outranks layer 3 (an explicit `config set source` beats auto-detection).
- [ ] Each layer's output is **validated** before use — a path source has both
  markers present; a URI source is parseable **and uses only a scheme
  `resolve_catalogue` understands** (`git+https` or a local path), so a `file://`,
  `http://`, or other-scheme source (set via `config set source` or baked into a
  forked `install-defaults.toml`) is **rejected**, distinct from the deferred
  host allowlist. The discriminator is explicit: a **schemeless** local path
  (`/abs/path`, `./rel`) is the local-path branch and is accepted; the gate
  rejects a URL that carries a scheme other than `git+https`. An invalid layer is
  skipped, not passed to the unvalidated `resolve_catalogue`.
- [ ] Editable detection reads
  `importlib.metadata.distribution("agentbundle").read_text("direct_url.json")`;
  it activates **only** when the record is present **and**
  `dir_info.editable == true`. A missing record (older pip, or a wheel install)
  falls through to layer 4 with no error.
- [ ] Editable detection parses the `file://` `url` with the standard parser
  (`urllib.request.url2pathname` + percent-decoding) and **rejects** a
  non-empty / non-localhost `file://` host.
- [ ] Editable detection **canonicalizes** the path (`Path.resolve()`) and walks
  up over canonicalized ancestors to the **first** one containing both `packs/`
  and `.claude-plugin/marketplace.json`, verifying each candidate stays under
  the resolved repository root.
- [ ] The repository root and every candidate are **canonicalized descendants-or-
  equal of `Path.resolve()` of the parsed editable `file://` URL** — so a symlink
  or `..` in the recorded URL cannot make the matched root resolve *outside* the
  clone the user `pip install -e`'d (the "inside the clone" precondition the
  forgeable-marker residual rests on is enforced, not assumed).
- [ ] The walk-up ascent is **bounded by the enclosing `.git` repository root**
  (nearest ancestor with a `.git` file *or* directory), computed before any
  marker test — a `packs/` + `marketplace.json` pair planted in a shared parent
  *above* the clone is never matched.
- [ ] The bound is a **closed interval**: the `.git`-root directory **itself** is
  a legal marker-match candidate (the catalogue root coincides with the git root,
  so the only valid match sits *at* the boundary). The catalogue-root == git-root
  case resolves rather than falling through to layer 4.
- [ ] A real `pip install -e packages/agentbundle` in an isolated venv resolves,
  via editable detection, to the clone root (the dir holding `packs/` +
  `.claude-plugin/marketplace.json`) — verified end-to-end, not against a mocked
  `direct_url.json`. (the construction-test keystone)
- [ ] When editable is detected but **no** catalogue root is found at/below the
  repo boundary (e.g. a sparse checkout missing `packs/`), the resolver emits a
  one-line stderr diagnostic naming what happened and defers to layer 4 — never
  silent, never a hard error on a default, never the cwd.
- [ ] **No resolution layer ever resolves from `.`/cwd**, and **no repo-scoped
  `source` layer exists** — asserted as explicit negative criteria (a planted
  cwd source / repo-root source is not consulted).
- [ ] When **no** layer yields a source, the command errors clearly with text
  naming all three recovery paths:
  `no catalogue source: pass --catalogue, run 'agentbundle config set source …', or pip install -e the catalogue`.
- [ ] Resolution writes nothing on **any** path — a one-off `--catalogue` (or any
  auto-resolved layer) does **not** persist to the user config (no
  write-on-install), including the editable-detected-but-deferred (diagnostic) and
  all-layers-empty (error) paths.
- [ ] `source` is added to `_KNOWN_KEYS` and the user `[settings]` schema
  (`user_config.py`) alongside `adapter`, **user scope only**; `config set
  source <uri>`, `config get source`, and `config unset source` round-trip, and
  the unset path is named in the all-layers-empty diagnostic.
- [ ] A new packaged `_data/install-defaults.toml` ships in the wheel via the
  existing `[tool.setuptools.package-data]` `agentbundle = ["_data/*"]` wiring,
  declaring
  `[defaults] source = "git+https://github.com/eugenelim/agent-ready-repo"`;
  an absent or empty file means no layer-4 default (the private-fork pattern).
- [ ] The adapter resolver is unchanged: the ~13 adapter default-resolution tests
  and `tests/unit/test_resolve_user_scope_target_adapter.py` stay green.
- [ ] Integrity-pinning for the layer-4 `git+https` fetch, and default resolution
  for `list-packs`/`list-profiles`, are **not** implemented here (deferred:
  convenient-install-defaults-followons).

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
