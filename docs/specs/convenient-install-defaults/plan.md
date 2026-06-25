# Plan: Convenient install defaults

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change adds a single new resolution path in front of the existing
`resolve_catalogue` call, plus three small data/config sources it draws from. The
shape: build the three leaf layers first (the packaged default file, the `source`
config key, and editable detection — all independent), then compose them in a new
`resolve_default_source()` that the `install`/`upgrade` handlers call **only when
`catalogue` is omitted**. The CLI change is the last, thinnest step (flip two
positionals to `nargs="?"`) so the wiring lands on top of a tested resolver. The
riskiest part is **editable detection** (T3): it is the keystone for the
downstream fork and the one place a path-traversal / planted-marker mistake would
matter, so it gets the real-`pip install -e` integration test and the hardened
canonicalize + repo-bounded walk-up. `resolve_catalogue` is left untouched and
unvalidating; all new validation lives in `resolve_default_source()`.

## Constraints

- **ADR-0036** — the four-layer trusted-by-construction chain, editable detection
  as the downstream default, no repo-scoped source, no cwd fall-back, no
  auto-persist, data-file (not constant) packaged default. The plan implements
  exactly these five decisions and adds nothing past them.
- **RFC-0046** — the decision set and the explicit follow-on boundaries
  (`list-packs`/`list-profiles` defaulting and integrity-pinning are out of scope).
- **RFC-0031 / CHARTER Principle 3** — runtime resolution + file reads only; no
  server, index, or daemon; **no new dependency** (stdlib `importlib.metadata`,
  `urllib.request`, `pathlib`, `tomllib`).
- **RFC-0011/0012 + the adapter state-hint** — the adapter resolver and
  `scope.DEFAULT_ADAPTER` are untouched; `source` is purely additive to the
  `[settings]` schema.

## Construction tests

Most construction tests live per-task below. Cross-cutting:

**Integration tests:**
- A real `pip install -e packages/agentbundle` in an isolated venv → editable
  detection resolves to the clone root (T3's keystone; the AC that must be
  exercised against a real install, not a mocked `direct_url.json`).
- End-to-end: a bare `agentbundle install --pack core` (no `--catalogue`) in
  an editable checkout resolves and proceeds via the layer-3 → real catalogue
  path; the same bare invocation with a planted `./` source present is **not**
  influenced by cwd (the no-cwd invariant, exercised at the command boundary).

**Manual verification:**
- Run the built CLI's documented happy path end-to-end: `agentbundle install
  --pack core` with no catalogue arg in (a) an editable checkout and (b) a
  simulated wheel install with a packaged default — record the real stdout/exit
  for each, per the work-loop's "exercise the artifact a user invokes" rule.

## Design (LLD)

### Design decisions

- **One new resolver in front of an unchanged `resolve_catalogue`.** All
  validation and layering lives in `resolve_default_source()`; `resolve_catalogue`
  stays a thin `Path(uri)` / `git+https` fetcher. Rejected: validating inside
  `resolve_catalogue` (would change the explicit-arg path's behaviour and the
  ~13 resolution tests). Traces to: the validation + precedence ACs.
- **Leaf layers are independent; only the composer depends on them.** Lets T1/T2/T3
  proceed in any order and isolates the keystone (T3) for focused review.
  Traces to: the four-layer precedence AC.
- **Data file, not a constant, for layer 4.** A fork re-points by blanking the
  file — zero code edit. Traces to: the packaged-default AC.

### Interfaces & contracts

- `resolve_default_source(explicit: str | None, *, config, dist, packaged) -> str`
  — returns a source URI/path string, or raises a clear `CatalogueError`-style
  error when no layer yields one. Pure over injected env (config reader, the
  distribution metadata handle, the packaged-default reader) so it is unit-testable
  without touching the real filesystem/metadata. Traces to: precedence +
  clear-error ACs.
- CLI: `catalogue` positional → `nargs="?"`, `default=None` on `install`/`upgrade`
  only. `list-packs`/`list-profiles` unchanged. Traces to: the two CLI ACs.
- Config: `source` joins `_KNOWN_KEYS`; `config set/get/unset source` reuse the
  existing `write_setting`/`unset_setting`/`read_user_config` plumbing. Traces to:
  the config round-trip AC.

### Data & schema

- `_data/install-defaults.toml`: `[defaults] source = "git+https://github.com/eugenelim/agent-ready-repo"`.
  Absent/empty ⇒ no layer-4 default. Read through the same bundled-data accessor
  the other `_data/` files use.
- User `[settings].source`: a string URI, user scope only, validated as
  parseable (not host-restricted — see spec Boundaries §Ask first).

### Failure, edge cases & resilience

- No `direct_url.json` (older pip / wheel) → skip layer 3, no error.
- Editable detected, catalogue root not found below the repo boundary → one-line
  stderr diagnostic, defer to layer 4.
- Non-empty / non-localhost `file://` host → reject (do not walk).
- Symlinked intermediate dir → canonicalize first, verify each candidate stays
  under the resolved repo root.
- All layers empty → clear error naming all three recovery paths; **never** cwd.
- Stale persisted source → recover with `config unset source` (named in the error).

### Quality attributes (NFRs)

- **Security (code-provenance boundary):** no repo-scoped source, no cwd
  fall-back — enforced as negative ACs and re-checked by the mandatory
  `security-reviewer` pass (path-and-file + supply-chain + config-misconfig
  lenses). The layer-4 network residual (unauthenticated TOFU against `main`) is
  documented and handed to the integrity-pinning follow-on, not silently widened.
  Traces to: the no-cwd / no-repo-source negative ACs and the deferred-followon AC.

## Tasks

### T1: Packaged `_data/install-defaults.toml` (layer 4)

**Depends on:** none

**Tests:**
- Goal-based: the file ships in the wheel and reads back via the existing
  bundled-data accessor with `[defaults].source` == the upstream GitHub URL.
- Unit: an absent/empty file yields `None` (no layer-4 default) — the private-fork
  case.

**Approach:**
- Add `agentbundle/_data/install-defaults.toml` with the `[defaults] source` key.
- Add a small reader (mirroring how `adapter.toml`/schemas are read) returning the
  source string or `None`.

**Done when:** the bundled-data accessor returns the upstream URL from a built
wheel, and `None` from a blanked file. Verifies the packaged-default AC.

### T2: `source` key in the user `[settings]` schema + validator (layer 2 plumbing)

**Depends on:** none

**Tests:**
- Unit: `source` is in `_KNOWN_KEYS`; `config set source <uri>` writes it,
  `config get source` reads it back, `config unset source` removes it
  (extend `test_config_cmd.py` / `test_user_config_io.py`).
- Unit (read-back — closes the write-only gap): a file with `[settings] source =
  "<uri>"` is parsed by `read_user_config` onto `UserConfig.source`, and
  `resolve_default_source` consumes it as layer 2.
- Unit: `config get source` reports provenance `file` when set, `unset` when
  absent (no builtin constant for `source`).
- Unit (independent fail-soft): a malformed/non-string `source` value leaves a
  valid `adapter` intact — `read_user_config` drops only the bad field, mirroring
  the existing `adapter` fail-soft.
- Unit: an unknown key is still refused; a malformed `source` value (empty /
  whitespace) is rejected by `_validate_key_value` (parseable-only — **no scheme
  gate, no host allowlist**; `config set source http://…` is accepted-but-inert).
- Regression: `adapter` validation and the config-cascade tests stay green.

**Approach:**
- Add `"source"` to `_KNOWN_KEYS`, the `UserConfig` dataclass, **and the
  `read_user_config` parse path** (fail-soft on a non-string value, mirroring
  `adapter`). Add a `source` branch to `_validate_key_value` (parseable / non-empty
  only) and to `_effective_value` in `commands/config.py` (`file` vs `unset`
  provenance). User scope only. The scheme gate is **not** here — it is in
  `resolve_default_source` (T4).

**Done when:** `config set/get/unset source` round-trips, `read_user_config`
surfaces `source`, and the adapter path is untouched. Verifies the config-key AC.

### T3: Editable detection (layer 3) — the keystone

**Depends on:** none

**Tests:**
- Integration (keystone): a real `pip install -e packages/agentbundle` in an
  isolated venv → detection reads the real `direct_url.json` and walks to the
  real clone root (the dir with `packs/` + `.claude-plugin/marketplace.json`).
  **Not** a mocked record.
- Unit: missing `direct_url.json` → `None`, no error.
- Unit: `dir_info.editable == false` → `None`.
- Unit: a non-empty / non-localhost `file://` host → rejected.
- Unit: `.git` as a **regular file** (worktree gitdir pointer) is recognized as
  the repo boundary, not only `.git` as a directory.
- Unit: a `packs/` + `marketplace.json` pair planted in a parent **above** the
  `.git` root is **not** matched (repo-bounded ascent); a pair in an intermediate
  dir *inside* the clone stops the walk at first match (accident-guard residual,
  documented).
- Unit: the **catalogue-root == git-root** case resolves (closed-interval bound —
  the `.git`-root dir itself is a legal match), not falls through to layer 4.
- Unit: the matched root is a **canonicalized descendant-or-equal** of
  `Path.resolve()` of the parsed editable URL — a `..`/symlink in the recorded
  URL cannot make the match escape the clone.
- Unit: a symlinked intermediate dir is canonicalized before the under-root check.

**Approach:**
- Read `importlib.metadata.distribution("agentbundle").read_text("direct_url.json")`;
  parse JSON; gate on `dir_info.editable`.
- Parse the `file://` url with `urllib.request.url2pathname` + percent-decode;
  reject a non-empty/non-localhost host.
- `Path.resolve()`; compute the enclosing `.git` root (file or dir); walk up over
  canonicalized ancestors to the first with both markers, never above the repo
  root.
- Return the catalogue root, or `None` (with the stderr diagnostic when editable
  was detected but no root found below the boundary).

The keystone integration test is `tests/integration/test_editable_source_detection.py`;
it builds its **own** throwaway venv (`python -m venv`) + `pip install -e
packages/agentbundle`, reads the real `direct_url.json`, and is **wired into CI
explicitly** in `build-check.yml` (not picked up by `make build-check`).

**Done when:** the keystone integration test passes against a real editable
install and every negative/hardening unit test is green. Verifies the editable
detection, walk-up-bound, `.git`-as-file, `file://`-host, and
fall-back-with-diagnostic ACs.

### T4: `resolve_default_source()` — compose the four layers

**Depends on:** T1, T2, T3

**Tests:**
- Unit: precedence — with all four layers populated, layer 1 wins; remove it,
  layer 2 wins; remove it, layer 3; remove it, layer 4 (table-driven).
- Unit: layer 2 outranks layer 3 (explicit config beats auto-detection).
- Unit: an invalid layer output (bad-marker path / unparseable URI) is **skipped**,
  not passed to `resolve_catalogue`.
- Unit (scheme validation — table-driven, the parser-differential cases): accept
  `git+https://…` and a schemeless local path with markers (`/abs`, `./rel`,
  `rel`) and a Windows drive path with markers (`C:\repo`); **reject** `file://`,
  `file:/` (single-slash), `http://`, `https://`, `git+ssh://`, and a mis-cased
  `GIT+HTTPS://` — only the literal-`git+https://` and schemeless/drive local-path
  branches pass. Distinct from the deferred host allowlist.
- Unit: all layers empty → the clear error naming all three recovery paths.
- Unit (negative invariants): a planted `./` cwd source is never consulted; there
  is no repo-scoped layer to consult.
- Unit/integration (no-write): the user config file is **byte-unchanged** after a
  bare `install` resolves through layers 2/3/4, and on the editable-deferred and
  all-layers-empty paths — a future regression that persisted the resolved source
  fails here.

**Approach:**
- Compose layers 1→4, first non-`None` validated result wins; validate path
  sources (markers present) and URI sources (parseable) before returning.
- Raise the clear `no catalogue source: …` error on exhaustion.

**Done when:** the precedence table, validation-skip, negative-invariant, and
clear-error tests are all green. Verifies the precedence + validation + no-cwd +
clear-error ACs.

### T5: CLI wiring — optional `catalogue` on install/upgrade

**Depends on:** T4

**Tests:**
- Goal-based: argparse accepts a bare `install --pack X`, a bare `install
  --profile Y`, and a bare `upgrade` (no catalogue); `list-packs` /
  `list-profiles` still reject a bare invocation.
- Unit: an explicit positional `catalogue` passes through unchanged (the default
  chain does not run — layer 1 short-circuits).
- Integration: a bare `install --pack core` in an editable checkout resolves via
  layer 3 and proceeds (end-to-end happy path); the same is unaffected by a
  planted `./` source (no-cwd, at the command boundary).
- Unit: a bare `install --profile X` reaches `resolve_default_source` at the
  `_run_profile` site (not just the `--pack` path).
- Regression: `test_resolve_user_scope_target_adapter.py` and the ~13 adapter
  resolution tests stay green.

**Approach:**
- New shared helper `commands/_common.resolve_catalogue_uri(args) -> str`: gathers
  `config_source` from `args._user_config` and calls
  `resolve_default_source(args.catalogue, config_source=…)` **unconditionally**
  (layer 1 returns an explicit arg verbatim before any metadata/bundle read, so
  the default chain runs only when the positional is omitted).
- `cli.py`: `install` (`:247`) and `upgrade` (`:400`) catalogue → `nargs="?"`,
  `default=None`. `list-packs` (`:197`) / `list-profiles` (`:205`) unchanged.
- All **three** resolve sites — `install.run` (`:116`), `install._run_profile`
  (`:3727`), `upgrade.run` (`:94`) — replace `catalogue_uri = args.catalogue`
  with `catalogue_uri = resolve_catalogue_uri(args)`.
- The **fourth** consumer, `install._offer_upgrade` (`:1739`), currently copies
  `ns.catalogue = args.catalogue` into the synthetic namespace it hands to
  `upgrade.run`. Thread the **already-resolved** `catalogue_uri` from `install.run`
  into the hand-off (pass it as a parameter or set `ns.catalogue = catalogue_uri`)
  so the upgrade offer carries the concrete URI rather than re-resolving (which on
  a bare install would otherwise pass `None` and double-detect). Test: a bare
  `install` that triggers the upgrade offer resolves once and hands the concrete
  URI down.
- CI: wire the keystone integration test (and the new unit tests, if not already
  swept) into `build-check.yml` explicitly — `make build-check` runs no pytest.

**Done when:** a bare `install`/`upgrade` resolves and runs end-to-end, the
discovery verbs still require a catalogue, and the explicit-arg path is byte-for-
byte unchanged. Verifies the two CLI ACs and the end-to-end happy-path.

## Rollout

- **Delivery:** big-bang, fully backward compatible — an explicit `--catalogue`
  behaves identically; the only new behaviour is on the previously-erroring
  no-arg case. No flag, no migration. Reversible by reverting the PR.
- **Infrastructure:** none (Principle 3 — runtime resolution + file reads).
- **External-system integration:** none new; layer 4 reuses the existing
  unauthenticated `git+https` GitHub fetch.
- **Deployment sequencing:** none — single PR, no ordering dependency. The
  `_data/install-defaults.toml` ships in the same wheel as the resolver that
  reads it.

## Risks

- **Editable-detection traversal mistakes** (the keystone) — mitigated by the
  real-`pip install -e` integration test, the canonicalize + repo-bounded ascent,
  and the mandatory `security-reviewer` pass.
- **Accidental cwd / repo-source regression** in a later refactor — mitigated by
  the explicit negative ACs and tests, which fail loudly if a cwd/repo layer is
  reintroduced.
- **Layer-4 network residual** (unauthenticated TOFU against `main`) — known and
  scoped to the upstream public default; integrity-pinning is a named follow-on,
  not silently widened here.

## Changelog

- 2026-06-25: initial plan (authored alongside spec + ADR-0036 from RFC-0046).
- 2026-06-25 (implementation): corrected the editable-detection **confinement
  AC** directionality. The package has no repo-root `pyproject.toml` (it lives at
  `packages/agentbundle/`), so `pip install -e packages/agentbundle` records that
  subdir as the editable URL and the catalogue/`.git` root is an **ancestor** of
  it — reached by walking *up*. The original AC's "candidate is a descendant-or-
  equal of the editable URL" was directionally inverted (it would fail the
  documented keystone test); rewritten to confine candidates to the closed
  interval [resolved `.git` root … resolved editable path], all canonicalized.
  Security intent (no escape via symlink/`..`, no match above the repo) is
  unchanged. New module: `agentbundle/source_defaults.py` holds T1/T3/T4; the
  args→inputs adapter is `commands/_common.resolve_catalogue_uri(args)`, which
  calls `resolve_default_source(args.catalogue, …)` unconditionally (layer 1
  short-circuits an explicit arg, so the default chain runs only when omitted).
