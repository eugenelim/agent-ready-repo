# Spec: apm-install-route-parity

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0010](../../rfc/0010-apm-install-route-parity.md)
  (canonical proposal — read first);
  [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
  (immediate precedent — same writer pattern, contract v0.4 from
  which this spec bumps to v0.5);
  [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (APM as a canonical install route; intentional `.apm/` layout
  convergence);
  [RFC-0003](../../rfc/0003-spec-and-cli.md) (CLI install→adapt
  chain; *Never invoke an LLM* rail this writer respects);
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (raised this
  gap; scope dimension the writer enforces; corrects an inherited
  default-scope assumption);
  [RFC-0007](../../rfc/0007-user-scope-converter-pack.md) (first
  user-scope pack — makes the user-scope leg of the gap concrete).
  Amends
  [`docs/specs/claude-plugins-install-route/spec.md`](../claude-plugins-install-route/spec.md)
  (AC1 import allow-list grows by `argparse`; AC9 hook command gains
  `--install-route claude-plugins` argument),
  [`docs/specs/adapt-to-project/spec.md`](../adapt-to-project/spec.md)
  (proactive cache scan extends to `apm_modules/`; new AC for
  APM-route stale-entry drop-on-mismatch), and
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (`per-pack-apm-package` recipe documents the install-marker
  artifact derivation; conformance suite gains APM-route cases;
  contract v0.4 → v0.5 bump recorded). Modifies
  [`docs/contracts/adapter.toml`](../../contracts/adapter.toml).

> **Spec contract:** this document defines what "done" means. The
> implementing PR must match this spec, or update it. Verification
> must be derivable from it.

> **Scope of "one spec, five coupled deliverables."** RFC-0010's
> Follow-on artifacts list bundles five deliverables that cannot
> ship independently — `F-apm-derivation` (build-pipeline projects
> the per-pack `.apm/hooks/install-marker.{json,py}` artifacts),
> `F-apm-install-marker` (integration tests for the projected
> writer at the APM route), the paired skill amendment on
> `adapt-to-project` (proactive cache scan extends to
> `apm_modules/`), the writer-template change (the data-directory
> portability shim and the `--install-route` CLI flag, both landed
> on the existing
> `packages/agentbundle/templates/install-marker.py` rather than
> as a sibling template), and the precedent-spec amendment
> (`claude-plugins-install-route`'s AC1 import allow-list and AC9
> hook command both track the new flag and need an in-PR edit).
> Shipping any of the five without the others produces a
> partially-broken contract surface:
> the derivation has nothing to
> project without the template change; the template change is
> dead code without the derivation; the integration tests have
> nothing to assert against without both; the skill amendment is
> the read-side closure of the chain; the precedent-spec edit
> is what keeps the spec graph internally consistent (the
> claude-plugins-route writer's import allow-list and hook command
> *do* change shape — pretending otherwise leaves the precedent
> spec aspirational against the post-PR writer). Sibling spec
> amendments to `claude-plugins-install-route/spec.md` (two AC
> edits + Changelog), `adapt-to-project/spec.md` (1 new AC + skill
> body edit + Changelog), and `distribution-adapters/spec.md` (1
> new AC + recipe-row edit + Changelog) land in the same PR per
> RFC-0010 §Follow-on artifacts.

## Objective

Close the install→adapt parity gap for APM-routed installs. The
adopter who declares an `agent-ready-repo` pack in their `apm.yml`
and runs `apm install <source>/<pack>` (or `apm install -g
<source>/<pack>` for user-scope) gets the same downstream
experience as the adopter who runs `agentbundle install --pack
<pack>` (CLI route) or `claude plugin install <marketplace>/<pack>`
(Claude-plugins route): on the next session of a HookIntegrator-
covered target tool (Claude Code, Copilot, Cursor, Gemini), a
`SessionStart` hook fires the canonical install-marker writer; the
writer detects first install or update, writes a
`[[packs-installed]]` entry to the scope-correct
`.adapt-install-marker.toml`, the existing core session-start
nudge surfaces *"N pack(s) pending adaptation; run
`/adapt-to-project`"*, and the brownfield repo (or user-home for
user-scope packs) is adapted to the project. The path-difference
between the three install routes is invisible to the adopter past
the install command itself.

The mechanism is a `SessionStart` hook declared in each pack's
`.apm/hooks/install-marker.json`, derived by `agentbundle build`
into `dist/apm/<pack>/.apm/hooks/`, that invokes the same
canonical writer at `packages/agentbundle/templates/install-marker.py`
RFC-0008 introduced. The writer template gains two additive
changes — both landed on the existing file, not a fork:

1. **A required `--install-route {claude-plugins,apm}` CLI flag**
   (parsed by `argparse` with `required=True`) whose value is
   written verbatim to the marker entry's `install-route` field.
   The build pipeline bakes the flag into the projected hook
   `command` at projection time for both routes (T4); the writer
   does no runtime route-sniffing. The flag is *required* — no
   default — so a future implementer who accidentally drops it
   from the projected `install-marker.json` is caught fast by
   `argparse`'s parse error rather than silently mis-routing.
   `"cli"` is *not* a valid choice: the CLI route uses
   `agentbundle install._append_install_marker` directly and never
   invokes this template. Existing markers emitted by the v0.4-era
   claude-plugins writer (which hard-coded
   `install-route = "claude-plugins"`) remain valid; readers treat
   absent values as `"cli"` per `claude-plugins-install-route` AC12.
2. **A data-directory resolution shim.** The writer's hash file
   currently lives at `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`.
   Under APM at non-Claude-Code targets, `${CLAUDE_PLUGIN_DATA}` is
   unset; APM rewrites the hook command's `${CLAUDE_PLUGIN_ROOT}`
   reference to the per-target equivalent token (`${PLUGIN_ROOT}`,
   `${CURSOR_PLUGIN_ROOT}`, …) per
   [APM's hooks-and-commands authoring page](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/),
   but offers no per-target data-directory token. The shim
   resolves data-directory in fixed precedence:
   `${CLAUDE_PLUGIN_DATA}` if set, else `${PLUGIN_ROOT}/.data` if
   `${PLUGIN_ROOT}` is set, else `${CURSOR_PLUGIN_ROOT}/.data` if
   set, else exit 0 (no marker write, no hash file write — same
   no-partial-state rail RFC-0008 §Proposal step 1 established).

Scope detection under APM is by **projected-hook path inspection**,
not by `enabledPlugins` file walk: when `--install-route apm` is
passed, the writer reads its own resolved path
(`pathlib.Path(__file__).resolve()`) and checks containment under
`pathlib.Path.cwd()` (project scope) or `pathlib.Path(home).resolve()`
(user scope). Containment under cwd → marker at
`<repo>/.adapt-install-marker.toml`; containment under `$HOME` →
marker at `~/.agentbundle/.adapt-install-marker.toml`; containment
under neither → exit 0 without writing (the no-match
fall-through rail). `[pack.install] allowed-scopes` enforcement is
unchanged from the claude-plugins-route writer — defence-in-depth
against a pack's projected location not matching its declared
scopes.

Coverage is **four of seven** APM compile targets. APM's
HookIntegrator projects `SessionStart` to Claude Code, Copilot,
Cursor, and Gemini per
[DeepWiki § 6.4](https://deepwiki.com/microsoft/apm/6.4-hook-integration);
the remaining three — Codex (AGENTS.md-driven, no hook surface),
OpenCode (*silently skips* hooks per APM's own docs), and Windsurf
(hook story undocumented) — silently lack the chain. The adopter
fallback for the no-hook three is the documented manual gesture
`agentbundle adapt --scope <project|user>` after install — the
same gesture that already serves CLI-route adopters and adopters
who disable hooks for safety.

Done means: a fresh `apm install` of any pack that ships through
the APM route, into a HookIntegrator-covered target tool, triggers
the writer on `SessionStart`, drops a marker the existing core
nudge reads, and `/adapt-to-project` runs class-1/2/3/4 normally
— with two accepted caveats documented per RFC-0010 § Drawbacks:
(a) the upstream
[anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
bug delays the first-session nudge by one session at Claude Code
targets; the proactive cache-scan branch (already on the
`adapt-to-project` skill from RFC-0008 / the
`claude-plugins-install-route` spec) closes the active case for
session 1 by extending its cache walk to `apm_modules/`; (b) three
APM targets (Codex, OpenCode, Windsurf) silently lack the chain
and require the manual `agentbundle adapt` fallback — not a
regression against today (today they get no adaptation either),
but an honest disclosure documented in the conformance suite and
per-pack READMEs.

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires
human sign-off before proceeding; *Never do* is a hard rule.

> **Boundary-rail inheritance.** This spec inherits the
> following rails verbatim from
> [`claude-plugins-install-route/spec.md` § Boundaries](../claude-plugins-install-route/spec.md#boundaries),
> with the precedent's pinning AC named so a reader can grep
> directly: marker-contract route-agnosticism (cp-AC12),
> atomic-write via `os.replace` (cp-AC4), hash-after-marker
> ordering (cp-AC5), stdlib-only writer (cp-AC1),
> per-pack-divergence-impossible (cp-AC20 a/b),
> no-LLM-in-writer (cp-§Boundaries Never-do), per-scope
> path-jail (cp-§Boundaries Never-do), two-writers-racing
> read-modify-write (cp-AC7), dual hash-or-entry detection
> (cp-AC6).
> The bullets below name only the *load-bearing additions* for
> this spec — the route-flag dispatch, the data-directory
> portability shim, the projected-path scope detection, the
> four-of-seven coverage disclosure, the `apm_modules/` skill
> walk, the no-`[pack.install.apm]`-table rail, and the
> no-`${CLAUDE_PROJECT_DIR}` rail. Each "inherited" bullet still
> binds; an implementer who would otherwise re-derive the
> precedent's reasoning should re-read the precedent.

### Always do

- **Land the route flag and portability shim on the existing
  canonical writer template.** All edits to writer logic happen in
  `packages/agentbundle/templates/install-marker.py`; per-pack
  divergence is impossible by construction. No fork, no
  per-route sibling file, no `.apm/`-specific template under
  `packages/agentbundle/templates/`. The drift gate (AC14) binds
  this as a mechanical rule, not author discipline.
- **Treat the `--install-route` flag value as authoritative; emit
  it verbatim on the `[[packs-installed]]` entry.** No runtime
  route-sniffing. The flag is parsed by `argparse` with
  `choices = {"claude-plugins", "apm"}` and `required=True`. An
  unrecognised value (e.g. a typo, or a future route the build
  wasn't taught about) fails fast at parse time with a non-zero
  exit; **flag absence also fails fast** — the build pipeline
  always passes the flag explicitly for every route this spec
  ships, and the required-flag rail is what catches a future
  implementer who accidentally omits it from a projected
  `install-marker.json`. The CLI route uses
  `agentbundle install._append_install_marker` directly, never
  the template; `"cli"` is therefore not an admitted choice.
- **Resolve the data directory in fixed precedence order.**
  `${CLAUDE_PLUGIN_DATA}` if set and non-empty → use directly;
  else `${PLUGIN_ROOT}` if set and non-empty →
  `${PLUGIN_ROOT}/.data`; else `${CURSOR_PLUGIN_ROOT}` if set and
  non-empty → `${CURSOR_PLUGIN_ROOT}/.data`; else exit 0 without
  writing the marker (no-partial-state rail). The resolved data
  directory MUST be created (`pathlib.Path.mkdir(parents=True,
  exist_ok=True)`) before the hash file is written; APM-projected
  `.data/` subdirectories do not exist at first hook invocation.
- **Detect scope by writer's own projected path when
  `--install-route apm`.** Read
  `pathlib.Path(__file__).resolve()`; check
  `_is_within(writer_path, pathlib.Path.cwd().resolve())` →
  `marker_scope = "repo"`; else
  `_is_within(writer_path, pathlib.Path(home).resolve())` →
  `marker_scope = "user"`; else exit 0 (no marker, no hash file
  write). Containment is enforced via `pathlib.Path.is_relative_to`
  (Python 3.9+) or its `parents`-based equivalent on the writer's
  stdlib-only constraint. Symlinks are resolved on both sides
  before comparison to avoid a writer that lives under a symlinked
  cache directory failing the containment check.
- **Detect scope by `enabledPlugins` walk only when
  `--install-route claude-plugins`.** The existing
  `_detect_origin` machinery from
  `claude-plugins-install-route/spec.md` AC2 stays the
  authoritative path for that route; the APM route gets the
  projected-path mechanism above. The two scope-detection paths
  are mutually exclusive at runtime, selected by the flag value.
  `--install-route cli` does not invoke either path — the CLI
  writer at
  `packages/agentbundle/agentbundle/commands/install.py:_append_install_marker`
  has its own scope handling and never invokes the template.
- **Keep the marker contract route-agnostic.** The
  `[[packs-installed]]` schema is identical across
  `install-route = "cli"`, `"claude-plugins"`, and `"apm"`; the
  only difference is the field's value. Any future install route
  lands as a fourth value on the `install-routes` array without
  a further marker schema bump. RFC-0008's marker-contract
  Always-do rail carries forward verbatim.
- **Bump the projected claude-plugins hook command to pass the
  flag.** `agentbundle build`'s claude-plugins derivation
  (currently emitting `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"`)
  is amended to emit `python3
  "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"
  --install-route claude-plugins`. **Writer-template and
  `install-marker.json` refreshes are coupled at projection
  time.** Three load-bearing links: (a) the existing
  `templates/install-marker.py` ≡ `_data/install-marker.py`
  parity unit test (precedent rail; ensures the wheel-shipped
  `_data/` copy tracks author edits to `templates/`); (b)
  `_data/install-marker.py` and the
  `_SESSION_START_COMMAND` literal in `build/main.py` co-
  ship in the same agentbundle wheel — they cannot drift
  within a single wheel; (c) AC16 (a)'s `dist/` ≡
  `templates/` drift gate transitively catches a stale
  `_data/` (because `dist/` is sourced from `_data/`).
  `make build` always emits both artifacts together from
  these canonical sources; an adopter's cache cannot hold
  the post-PR writer template alongside a pre-PR
  `install-marker.json` because both are re-projected in
  lockstep on every build, and the self-host drift gate
  (AC16 + `claude-plugins-install-route` AC20) refuses to
  pass on any mismatch. There is no back-compat default on
  the writer — `--install-route` is `required=True` — so an
  adopter who somehow ends up with a refreshed writer
  template and a stale `command` field (no flag) gets a
  fast-failing `argparse` error on the next session rather
  than a silent mis-route. The required-flag rail is the
  spec's chosen failure mode.
- **Project both `install-marker.json` and `install-marker.py`
  into `dist/apm/<pack>/.apm/hooks/` from canonical sources.**
  The `install-marker.py` is byte-identical to the template; the
  `install-marker.json` is synthesised by the build from a fixed
  shape (see AC7 for the JSON contract). `pack.toml` is also
  projected into `dist/apm/<pack>/` per
  `distribution-adapters/spec.md`'s `per-pack-apm-package`
  recipe — the writer needs it to read `[pack.install]
  allowed-scopes` at runtime.
- **Disclose the four-of-seven coverage matrix in the
  conformance suite and per-pack READMEs.** The conformance
  suite enumerates the four covered HookIntegrator targets
  (Claude Code, Copilot, Cursor, Gemini) and the three uncovered
  targets (Codex, OpenCode, Windsurf) with the
  `agentbundle adapt` manual-fallback gesture per target. The
  uncovered three are not regressions; today they get no
  adaptation either. Per-pack READMEs ship the same
  one-paragraph disclosure pattern RFC-0008's claude-plugins
  README disclosure already established.
- **Extend the `adapt-to-project` skill's proactive cache-scan
  branch to walk APM caches.** RFC-0008 / the
  `claude-plugins-install-route` spec already gave the skill a
  branch that scans `~/.claude/plugins/cache/` and
  `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/`. This spec
  extends that branch to also walk `apm_modules/` (project scope)
  and `~/.apm/apm_modules/` (user scope) for pack roots with no
  `[[packs-installed]]` entry. APM's `apm_modules/` layout is
  stable, APM-owned, and consistent across packs — the
  pack-boundary objection RFC-0008 Alt 3 raised against a central
  detector does not apply when the cache directory is
  installer-owned rather than per-pack-projected. The skill body
  is amended; the contract is grep-pinned per the
  existing AC15 pattern.
- **Pin all sibling-spec edits as in-PR amendments, not separate
  PRs.** RFC-0010 §Follow-on artifacts names the three sibling
  spec edits (`adapt-to-project` AC + skill body;
  `distribution-adapters` AC + recipe row + Changelog;
  `claude-plugins-install-route` AC1 import allow-list + AC9 hook
  command) as land-in-this-PR amendments. Splitting them re-opens
  the partial-contract-surface failure mode the
  "one spec, four coupled deliverables" framing exists to close.

### Ask first

- **Adding any persistent on-disk artifact beyond those named in
  this spec.** The APM-route writer touches three paths only: the
  resolved-data-directory hash file (`<data>/pack-manifest-hash`),
  the scope-correct `.adapt-install-marker.toml`, and the
  tempfile-in-same-directory the atomic rename uses. Anything
  else needs review.
- **Changing the data-directory resolution precedence.** The
  fixed order (`${CLAUDE_PLUGIN_DATA}` →
  `${PLUGIN_ROOT}/.data` → `${CURSOR_PLUGIN_ROOT}/.data` →
  exit-0) is the spec's portability rail. Reordering — or
  adding a fourth fallback — needs human sign-off because the
  precedence is what makes the writer's data-directory location
  predictable per target tool.
- **Touching APM's HookIntegrator contract surface.** Our writer
  is a normal APM-shaped hook (a JSON file under `.apm/hooks/`
  keyed by `SessionStart`); it does not require APM to publish
  anything and does not foreclose a future contribution path.
  Any change that depends on APM-internal symbols, vendored APM
  code, or undocumented HookIntegrator behaviour is out of
  bounds without review.
- **Adding any field to the `[[packs-installed]]` entry beyond
  `install-route`.** Same rail as `claude-plugins-install-route`
  / RFC-0008. The schema has two readers (the core session-start
  nudge and the `adapt-to-project` skill); any new field has two
  readers to keep in sync.

### Never do

- **Never fork the canonical writer template.** All routes share
  `packages/agentbundle/templates/install-marker.py`. A
  per-route fork would re-introduce the per-pack divergence
  failure mode the `templates/` rail exists to close.
- **Never add a `[pack.install.apm]` table to `pack.toml`.**
  RFC-0010 §Pack-level declarations explicitly forbids this; the
  APM-side wiring is fully derived by `agentbundle build` from
  fields `pack.toml` already declares. A new `pack.toml` table
  is a new contract axis with read-side cost on every consumer.
- **Never make the marker contract route-keyed at the file-shape
  level.** `install-route = "apm"` is a value on an entry; not a
  separate file, not a separate table, not a separate schema.
  The *contract* surface remains route-agnostic; only the
  conformance suite's install-marker *case* is route-keyed.
  Same rail as RFC-0008 / `claude-plugins-install-route`.
- **Never add a non-stdlib Python dependency to the writer
  template.** The same rail RFC-0008 /
  `claude-plugins-install-route` AC1 already binds: the writer
  ships into every APM cache directory on every adopter machine;
  an `import requests` would require either bundling the library
  (cache size + per-update bandwidth cost across the catalogue)
  or installing it via APM's `apm_modules/` cache layout (adds
  install-time network calls and supply-chain surface).
  Stdlib-only caps both costs at zero. `argparse` is stdlib;
  AC1's import allow-list grows by one entry to admit it.
- **Never let per-pack writers diverge.** All
  `install-marker.py` files in every pack's
  `dist/apm/<pack>/.apm/hooks/` are byte-identical copies of
  `packages/agentbundle/templates/install-marker.py`.
  `make build-check` (the self-host drift gate) is amended to
  assert this at the APM projection alongside the existing
  claude-plugins projection. The vendored `_emit_basic_string`
  parity check (`claude-plugins-install-route` AC20 axis b)
  continues to bind — the same vendored helper is
  security-load-bearing for both routes.
- **Never invoke an LLM from the writer.** The writer is a
  CLI-rail primitive — the same *Never invoke an LLM* rail
  [RFC-0003 §Proposal](../../rfc/0003-spec-and-cli.md#proposal)
  pins for `agentbundle adapt` and RFC-0008's writer. Writer
  detects, writes, exits; consumption is the skill's job.
- **Never bypass the per-scope path-jail for the marker write.**
  User-scope marker writes route through the same primitive the
  CLI writer's `_append_install_marker` uses (`safety.write_jailed`
  with the `claude-code` adapter's `allowed-prefixes.user`). The
  CLI writer has this; the claude-plugins writer has this; the
  APM-route writer inherits it from the shared template. A bug
  in the projected pack's source code (a `pack.toml` field that
  somehow steers the marker path) would otherwise be free to
  write under `~/.ssh/`.
- **Never ship per-target hook JSON files.** APM's
  HookIntegrator projects a single authored hook to every
  supported target. Shipping
  `install-marker-claude.json`/`install-marker-copilot.json`/…
  duplicates the installer's per-target rewrite work. One
  authored hook, four projections, one writer template — that's
  the design.
- **Never add a new top-level directory or package.** The
  template lives under
  `packages/agentbundle/templates/install-marker.py` (already
  in place from RFC-0008). The integration tests live under
  `packages/agentbundle/tests/integration/test_apm_install_route.py`
  (existing `tests/integration/` directory). The build-side
  derivation amends the existing
  `packages/agentbundle/agentbundle/build/` machinery.
- **Never claim coverage on the three no-hook APM targets.**
  Codex, OpenCode, and Windsurf adopters use the documented
  manual `agentbundle adapt` gesture. The conformance suite
  enumerates the four covered targets and explicitly excludes
  the three uncovered ones. Adding "coverage" via a runtime
  detector that polls `apm_modules/` would re-open the
  pack-boundary objection in a different guise (the detector
  would need to enumerate per-pack cache directories rather
  than rely on APM's installer-owned layout). The skill-side
  proactive cache scan (Always-do bullet above) is the closest
  approximation — and it's a read-side closure of the gap, not a
  claim of write-side hook coverage.
- **Never depend on `${CLAUDE_PROJECT_DIR}` under
  `--install-route apm`.** APM does not export
  `${CLAUDE_PROJECT_DIR}`; the projected hook runs with whatever
  cwd the target tool launched it under. Scope detection under
  `apm` is by writer's own path (Always-do bullet above), not by
  `${CLAUDE_PROJECT_DIR}`. The variable is consumed only under
  `--install-route claude-plugins`.

## Testing Strategy

Three behaviour groups close this spec; each gets one verification
mode per the [`work-loop`](../../../.claude/skills/work-loop/SKILL.md)
taxonomy.

- **Writer template additions — TDD.** Pure-ish functions with
  compressible invariants: `--install-route` argparse with the
  two-value `choices = {"claude-plugins", "apm"}`, `required=True`,
  no default — flag absence and invalid-choice both fail fast at
  `argparse` parse time; data-directory resolution precedence
  (`${CLAUDE_PLUGIN_DATA}` → `${PLUGIN_ROOT}/.data` →
  `${CURSOR_PLUGIN_ROOT}/.data` → exit-0); APM scope detection by
  projected-hook path inspection (`cwd` containment → repo;
  `$HOME` containment → user; neither → exit-0; symlink
  resolution on both sides before comparison); `allowed-scopes`
  refusal under the APM scope-detection path; route-flag-driven
  branch selection between APM and claude-plugins scope
  detection. Tests live at
  `packages/agentbundle/tests/integration/test_apm_install_route.py`
  and exercise the writer in subprocess against a fixture-
  controlled environment quintet —
  `${CLAUDE_PLUGIN_DATA}` /
  `${PLUGIN_ROOT}` / `${CURSOR_PLUGIN_ROOT}` / `${HOME}` plus the
  writer's own projected location — because the writer's
  contract surface under APM is environment + disk + own-path,
  and the test surface mirrors that.
- **Build-pipeline APM derivation — goal-based check.**
  `agentbundle build` against the catalogue's packs produces, for
  each pack:
  - `dist/apm/<pack>/.apm/hooks/install-marker.json` with the
    synthesised `SessionStart` block carrying the canonical
    command `python3
    "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"
    --install-route apm` (verbatim string when read out of JSON);
  - `dist/apm/<pack>/.apm/hooks/install-marker.py` byte-identical
    to `packages/agentbundle/templates/install-marker.py`;
  - `dist/apm/<pack>/pack.toml` byte-identical to the source
    `packs/<pack>/pack.toml`.
  Plus the matching `dist/claude-plugins/<pack>/.claude-plugin/plugin.json`
  hook command bumps to `python3
  "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"
  --install-route claude-plugins`. The check is a single command
  + a directory diff against a fixture; no internal assertions.
  Same for `make build-check` (the self-host gate): asserts no
  drift on a clean tree at both the APM and claude-plugins
  projections.
- **Live APM install — manual QA.** Per
  [RFC-0010 §Unresolved questions Q6](../../rfc/0010-apm-install-route-parity.md#unresolved-questions),
  the close trigger for the RFC is the end-to-end demonstration
  on a real install: `apm install agent-ready-repo/core`, next
  session of a HookIntegrator-covered target tool writes
  `<repo>/.adapt-install-marker.toml`, core's nudge surfaces,
  `/adapt-to-project` runs. The matrix rows live at
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` (the
  install→adapt chain's existing matrix home). A second row
  covers `converters` at user scope (`apm install -g
  agent-ready-repo/converters`) to close the user-scope leg. A
  third row records the per-target characterisation matrix
  RFC-0010 §Drawbacks names as a follow-on-research item —
  whether the writer fires on session 1 vs. session N at each
  of Copilot, Cursor, Gemini (Claude Code's session-1 quirk is
  already characterised via RFC-0008). All three rows record
  transcript-style evidence; all three are gated by adopter
  availability, not by this PR — the rows ship with
  `verification = transcript` and the trigger column names the
  close criterion.

## Acceptance Criteria

- [x] **AC1 (writer template stays stdlib-only with a one-entry
      growth in the import allow-list to admit `argparse`).**
      `packages/agentbundle/templates/install-marker.py` continues
      to import only standard-library modules. Ground truth at
      spec time (confirmed by `grep -nE '^(import|from) '
      packages/agentbundle/templates/install-marker.py`): the
      pre-edit module set is `{datetime, hashlib, json, os,
      pathlib, sys, tempfile, tomllib, re}` (the `from datetime
      import timezone` line does not add a module; `import re as
      _re` admits `re`). The post-edit module set required by
      this spec is exactly `{argparse, datetime, hashlib, json,
      os, pathlib, re, sys, tempfile, tomllib}` — one entry
      added (`argparse`), no other change. Any addition beyond
      `argparse` is a spec amendment. The precedent-spec
      `claude-plugins-install-route` AC1 (which enumerated a
      smaller allow-list that did not yet match the writer-file
      ground truth) gets an in-PR Changelog-recorded amendment in
      this PR's T10 — both specs reconcile to the same post-edit
      set. The docstring edit (naming this spec alongside the
      precedent spec) is *not* part of AC1's contract surface; it
      lands as a T1-Approach authoring task and is not separately
      gate-tested.
- [x] **AC2 (`--install-route` flag parsed by `argparse`;
      required; two-valued choices).** The writer parses
      `argparse.ArgumentParser().add_argument("--install-route",
      choices=["claude-plugins", "apm"], required=True)`. Four
      unit tests pin: (a) `--install-route claude-plugins` → marker
      records `install-route = "claude-plugins"`; (b)
      `--install-route apm` → marker records
      `install-route = "apm"`; (c) `--install-route foo` (any
      non-choice value) → writer exits non-zero, `argparse`'s
      usage message on stderr, no marker write, no hash file
      update; (d) the flag omitted entirely → writer exits
      non-zero, `argparse`'s "required" error on stderr, no
      marker write, no hash file update. The required-flag rail
      is what catches a build-pipeline regression that emits an
      `install-marker.json` without the flag in the `command`
      field — see AC7 / AC8 / T9's drift gate. `"cli"` is not a
      valid choice: the CLI route uses
      `_append_install_marker` directly and never invokes this
      template.
- [x] **AC3 (data-directory resolution precedence).** Under
      `--install-route apm`, the writer resolves the data
      directory as: `${CLAUDE_PLUGIN_DATA}` if set and non-empty
      → that path; else `${PLUGIN_ROOT}` set and non-empty →
      `${PLUGIN_ROOT}/.data`; else `${CURSOR_PLUGIN_ROOT}` set
      and non-empty → `${CURSOR_PLUGIN_ROOT}/.data`; else exit 0
      without writing the marker (no-partial-state rail).
      Whichever path is resolved is created
      (`mkdir(parents=True, exist_ok=True)`) before the hash
      file is written. Seven unit tests pin: (a) only
      `${CLAUDE_PLUGIN_DATA}` set → resolved path equals it; (b)
      only `${PLUGIN_ROOT}` set (e.g. Cursor or Gemini target;
      `${CLAUDE_PLUGIN_DATA}` unset) → resolved path equals
      `${PLUGIN_ROOT}/.data`; (c) only `${CURSOR_PLUGIN_ROOT}`
      set → resolved path equals `${CURSOR_PLUGIN_ROOT}/.data`;
      (d) all four tokens unset → exit 0, no marker, no hash
      file write, no directory creation; (e) the resolved data
      directory is created when it does not yet exist (a fresh
      APM install lands `.data/` as a subdirectory of the
      projected pack root, which APM does not pre-create);
      (f) **precedence pin — all three tokens set
      simultaneously** → resolved path equals
      `${CLAUDE_PLUGIN_DATA}` (not `${PLUGIN_ROOT}/.data`, not
      `${CURSOR_PLUGIN_ROOT}/.data`). A buggy reversed-precedence
      implementation (`cpr_data or cpd or pr/.data`) would pass
      cases (a)–(e) but fail (f); (g) **precedence pin —
      `${PLUGIN_ROOT}` and `${CURSOR_PLUGIN_ROOT}` both set,
      `${CLAUDE_PLUGIN_DATA}` unset** → resolved path equals
      `${PLUGIN_ROOT}/.data`. Cases (f) and (g) together force
      every adjacent pair of the precedence chain to be
      verified.
      Empty-string values (e.g. `PLUGIN_ROOT=""`) are treated
      as unset.
- [x] **AC4 (APM scope detection by projected-hook path).** Under
      `--install-route apm`, the writer reads
      `pathlib.Path(__file__).resolve()` and determines scope by
      containment: if the writer's resolved path is contained in
      `pathlib.Path.cwd().resolve()` → `marker_scope = "repo"`,
      marker path is `<cwd>/.adapt-install-marker.toml`; else if
      contained in `pathlib.Path(home).resolve()` →
      `marker_scope = "user"`, marker path is
      `<home>/.agentbundle/.adapt-install-marker.toml`; else
      exit 0 without writing (no-match fall-through; same
      no-partial-state rail). Symlinks are resolved on both
      sides via `.resolve()` before comparison. Five unit tests
      pin: (a) writer projected under cwd, where **cwd is itself
      nested under `$HOME`** so both containment checks would
      succeed in the abstract and the first-branch-wins rule
      must pick repo. Fixture: `home = ${tmp_path}/home`,
      `cwd = ${tmp_path}/home/proj`, writer projected at
      `${tmp_path}/home/proj/apm_modules/<pack>/` →
      `marker_scope = "repo"`, marker at
      `${tmp_path}/home/proj/.adapt-install-marker.toml`.
      The nested-home structure is load-bearing — a buggy
      implementation that checked home before cwd would
      silently flip this to user; (b) writer
      projected under `$HOME` (fixture
      `${HOME}/.apm/apm_modules/<pack>/`) →
      `marker_scope = "user"`, marker at
      `${HOME}/.agentbundle/.adapt-install-marker.toml`; (c)
      writer projected under neither (a path that's not under
      cwd nor `$HOME`) → exit 0 without writing; (d) writer
      reached via a symlink (`${tmp_path}/repo/cache-link` →
      `${tmp_path}/repo/apm_modules/<pack>/`) → `.resolve()` on
      both sides yields containment, scope is `repo` (the
      symlink-resolution regression guard); (e)
      **Home-branch coverage when writer is outside cwd but
      under `$HOME`.** Fixture: `home = ${tmp_path}/home`,
      `cwd = ${tmp_path}/home/proj`, writer projected at
      `${tmp_path}/home/.apm/apm_modules/<pack>/`. Writer is NOT
      under cwd (cwd-containment fails for both check orders);
      home-containment matches. Expected:
      `marker_scope = "user"`. This case asserts that the
      home-detection branch fires when the cwd branch doesn't —
      orthogonal to case (a)'s precedence guard but
      load-bearing for the "user-scope install via APM-at-user"
      path (`apm install -g`).
      *Precedence-guard ownership lives in case (a):* when
      both containment checks would succeed in the abstract,
      case (a)'s nested-home fixture forces the order to
      resolve, and a buggy home-first impl would flip case
      (a)'s expected `"repo"` to `"user"`. Case (e) is not
      the precedence test.
- [x] **AC5 (`allowed-scopes` refusal rail unchanged under APM
      scope detection).** When the APM-detected `marker_scope`
      is not in the installing pack's `[pack.install]
      allowed-scopes`, the writer emits the same stderr line
      RFC-0008 / `claude-plugins-install-route` AC3 grammars
      pinned: `install-marker: pack <name> declares
      allowed-scopes=<list>, detected install scope <detected>;
      skipping marker write` and exits 0. Under the APM route,
      `<detected>` is one of `repo` or `user` (the APM scope
      detection has no three-valued origin equivalent to
      `claude-plugins`'s `local`/`project`/`user`). Two unit
      tests pin: (a) repo-only pack with writer projected under
      `$HOME` → refuses with `detected install scope user`,
      exit 0, no marker, no hash file; (b) user-only pack with
      writer projected under cwd → refuses with `detected
      install scope repo`, exit 0, no marker, no hash file.
- [x] **AC6 (route-flag-driven branch selection between APM and
      claude-plugins scope detection).** Under `--install-route
      claude-plugins`, the writer takes the existing
      `_detect_origin`-based path (precedence walk across
      `enabledPlugins` files; documented per
      `claude-plugins-install-route` AC2). Under `--install-route
      apm`, the writer takes the projected-path inspection path
      (AC4). The two paths are mutually exclusive at runtime;
      one unit test pins each direction: (a) with the flag set
      to `claude-plugins` and `${CLAUDE_PROJECT_DIR}` plus an
      `enabledPlugins` file set up, the writer takes the
      `_detect_origin` path and ignores the projected-hook-path
      mechanism; (b) with the flag set to `apm` and an
      `enabledPlugins` file present but the writer projected
      under cwd, the writer takes the projected-path mechanism
      and ignores `enabledPlugins`. AC6's purpose is to pin
      that no scope-detection code is "shared" silently between
      routes — the flag is the dispatch.
- [x] **AC7 (`install-marker.json` synthesised shape).** The
      build pipeline emits, under each pack's
      `dist/apm/<pack>/.apm/hooks/install-marker.json`, JSON of
      this exact shape (formatting-modulo, but the structure and
      values are pinned):
      ```json
      {
        "hooks": {
          "SessionStart": [
            {
              "hooks": [
                {
                  "type": "command",
                  "command": "python3 \"${PLUGIN_ROOT}/.apm/hooks/install-marker.py\" --install-route apm",
                  "timeout": 10
                }
              ]
            }
          ]
        }
      }
      ```
      One goal-based test loads each emitted file with
      `json.loads` and asserts
      `obj["hooks"]["SessionStart"][0]["hooks"][0]["command"]`
      equals (when read out of JSON) the literal string
      `python3 "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"
      --install-route apm`. A `shlex.split` sub-assertion (after
      substituting a synthetic `PLUGIN_ROOT` containing a
      space, e.g. `/tmp/with space/root`) yields exactly the
      four-token list `["python3", "/tmp/with
      space/root/.apm/hooks/install-marker.py",
      "--install-route", "apm"]` — pinning that the quoting
      survives spaces in `${PLUGIN_ROOT}`. The `timeout` field
      mirrors RFC-0010 §Pack-level declarations' JSON example
      (value: 10 seconds).
- [x] **AC8 (claude-plugins-side hook command bumps to pass
      `--install-route claude-plugins`).** `agentbundle build`'s
      claude-plugins derivation, currently emitting
      `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"`,
      is amended to emit
      `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py" --install-route claude-plugins`.
      One goal-based test asserts the literal string after
      synthesis. The `claude-plugins-install-route` spec's AC9
      (which pinned the original literal) gets an in-PR amend
      to track the new literal — landed by plan task T10.
- [x] **AC9 (adapter contract bumps v0.4 → v0.5 with `"apm"`
      appended to `install-routes`).** `docs/contracts/adapter.toml`
      declares `[contract] version = "0.5"` and
      `[adapter."claude-code"] install-routes = ["cli",
      "claude-plugins", "apm"]`. `docs/contracts/adapter.schema.json`
      accepts `"apm"` as a new enum value on the
      `install-routes` items. The `install-routes` array stays
      on `[adapter."claude-code"]` for this spec's purposes per
      RFC-0010 §Contract impact — APM is a route the bundle
      ships *through*, and the bundle's target adapter is still
      Claude Code (and its peers). RFC-0010 §Unresolved questions
      Q3 records the case for adding the array to other
      adapters; out of scope for this spec. **Positive
      assertions** (one unit test each): contract version is
      `"0.5"`; `install-routes` value is `["cli",
      "claude-plugins", "apm"]`; schema accepts the new enum
      value. **Regression guard** (one unit test): the other
      adapter blocks (Kiro, Copilot, Codex) continue to carry
      no `install-routes` key — the field is optional per-adapter
      per `claude-plugins-install-route` AC11 and the default
      stays `["cli"]` on read; this PR must not silently extend
      the field's surface to those adapters.
- [x] **AC10 (marker schema gains `"apm"` as permitted
      `install-route` value; v0.3-era markers continue to parse
      cleanly).** Under v0.5 each `[[packs-installed]]` entry MAY
      carry `install-route ∈ {"cli", "claude-plugins", "apm"}`
      (additive); v0.4 readers MUST treat absence as
      `install-route = "cli"` (back-compat carries from
      `claude-plugins-install-route` AC12). The schema
      amendment lands in
      `docs/specs/adapt-to-project/spec.md` § *.adapt-install-marker.toml
      schema* (existing schema block already documents the
      optional `install-route` field per
      `claude-plugins-install-route` AC12; this spec extends the
      permitted-values list by one). A fixture-set test loads
      one v0.3-shaped marker (no `install-route` field at all;
      absence-defaults-to-`"cli"` back-compat rail per
      `claude-plugins-install-route` AC12), one v0.4-shaped
      marker with `install-route = "claude-plugins"`, and one
      v0.5-shaped marker with `install-route = "apm"`; all three
      parse cleanly through the core pack session-start nudge's
      `_pack_names_from_marker` helper at
      `packs/core/.apm/hooks/session-start.py` (the test
      grep-locates the function by symbol name rather than
      line range, so refactors of the hook body don't rot
      this AC).
- [x] **AC11 (build-pipeline APM derivation projects three
      artifacts per pack).** `agentbundle build` against every
      pack in `packs/` produces, under each pack's
      `dist/apm/<pack>/`:
      (a) `.apm/hooks/install-marker.json` per AC7's
      synthesised shape;
      (b) `.apm/hooks/install-marker.py` byte-identical to
      `packages/agentbundle/templates/install-marker.py`;
      (c) `pack.toml` byte-identical to
      `packs/<pack>/pack.toml`.
      A goal-based test diffs the produced tree against a
      checked-in fixture. `make build-check` exits zero against
      the post-migration tree at the APM projection.
- [x] **AC12 (integration tests cover the five RFC-0010-named
      scenarios with explicit test names).**
      `packages/agentbundle/tests/integration/test_apm_install_route.py`
      exists and contains tests pinning the five scenarios
      named in [RFC-0010 §Follow-on artifacts](../../rfc/0010-apm-install-route-parity.md#follow-on-artifacts)
      under *F-apm-install-marker*. The tests are named
      explicitly so a reviewer can grep the file and confirm
      coverage without manual cross-mapping:
      (a) first-install marker write at project scope —
        `test_first_install_end_to_end_core_project_scope`
        (RFC-0010 Q6 close-trigger 1);
      (b) first-install marker write at user scope —
        `test_first_install_end_to_end_converters_user_scope`
        (RFC-0010 Q6 close-trigger 2);
      (c) scope refusal — `test_refuse_repo_only_pack_at_user_scope`,
        `test_refuse_user_only_pack_at_project_scope`;
      (d) lockfile-replay marker replace on upgrade —
        `test_lockfile_replay_replaces_entry`;
      (e) per-target characterisation (Claude Code only) —
        `test_per_target_characterisation_claude_code`. The
        one HookIntegrator-covered target whose data-directory
        token (`${CLAUDE_PLUGIN_DATA}`) and first-session
        semantics are characterised at spec time (via RFC-0008
        / `claude-plugins-install-route` prior work). The
        other three HookIntegrator-covered targets (Copilot,
        Cursor, Gemini) are *not* covered by AC12 integration
        tests — their per-target tokens are unconfirmed at PR
        time, and a skipped-in-CI test is not honest coverage.
        Their first-firing behaviour ships as AC17's per-target
        manual-QA matrix row (`verification = transcript`)
        instead, gated on adopter-availability rather than on
        this PR.
      Each test runs the writer in subprocess against a
      fixture-controlled environment quintet
      (`${CLAUDE_PLUGIN_DATA}`, `${PLUGIN_ROOT}`,
      `${CURSOR_PLUGIN_ROOT}`, `${HOME}`, plus the writer's
      own projected location) and asserts the marker file's
      `tomllib`-parsed shape.
- [x] **AC13 (`adapt-to-project` skill body extends proactive
      cache scan to walk APM caches).**
      `packs/core/.apm/skills/adapt-to-project/SKILL.md`
      Pre-flight section's proactive cache-scan step (added by
      `claude-plugins-install-route` T6) gains two additional
      cache directories: `./apm_modules/` (project scope) and
      `~/.apm/apm_modules/` (user scope). The branch is
      idempotent with the marker-consume path on the same rail
      `claude-plugins-install-route` AC25 already binds — if a
      marker entry for the same pack is present at either
      scope, the skill consumes the marker entry path and the
      cache-scan does not double-adapt. The behaviour is
      grep-pinned per the existing AC15 / AC25 pattern. Three
      SKILL.md body greps pin the contract:
      1. body contains the literal path `./apm_modules/`;
      2. body contains the literal path `~/.apm/apm_modules/`;
      3. body contains the literal phrase `APM cache scan`
         (case- and punctuation-sensitive — the operative
         heading the LLM reads).
      End-to-end verification of the idempotence behaviour
      under the APM cache extension ships as a manual-QA matrix
      row under AC15.
- [x] **AC14 (`adapt-to-project` spec amendment — APM-route
      stale-entry drop-on-mismatch AC).**
      `docs/specs/adapt-to-project/spec.md` gains one new
      Acceptance Criterion (numbered AC27, extending the
      `claude-plugins-install-route` spec's AC24–AC26):
      - **AC27 — APM-route stale-entry drop-on-read.** When a
        `[[packs-installed]]` entry's pack has
        `install-route = "apm"` and the pack is no longer
        present in any cache directory under `apm_modules/`
        (`./apm_modules/` at project scope or
        `~/.apm/apm_modules/` at user scope) and not recorded
        in any scope's state file, the skill silently drops
        the entry on read — same rail
        `claude-plugins-install-route` AC26 binds for the
        claude-plugins route. Pinned by SKILL.md body grep
        (one additional literal added per AC13). Programmatic
        verification is deferred to a future APM uninstall
        handling RFC, mirroring
        `claude-plugins-install-route` AC26's forward
        reference. A Changelog entry on the parent
        `adapt-to-project` spec names this spec by path.
- [x] **AC15 (`distribution-adapters` spec amendment — APM-route
      conformance cases and recipe-row documentation).**
      `docs/specs/distribution-adapters/spec.md` § *Recipe set*
      table extends the existing `per-pack-apm-package` row's
      content (or adds a per-route note alongside the existing
      row) to name the install-marker artifact derivation;
      § *Acceptance Criteria* gains one new AC pinning that the
      conformance suite ships a *marker presence* and a *scope
      refusal* case for the APM route alongside the existing
      claude-plugins cases, with the fixtures living in
      `packages/agentbundle/tests/integration/test_apm_install_route.py`
      (this spec's owned test file) and referenced by path from
      the sibling spec. **Conformance coverage is route-keyed AND
      partially target-deferred at the APM route.**
      Mechanically-asserted in this PR: one *marker presence*
      case at the Claude Code target and one *scope refusal*
      case at the same target. The *marker presence* test
      asserts on the first observed-firing session at Claude
      Code under APM — today that is session 2 or later
      because the `#10997` first-session-quirk applies to
      `SessionStart` at Claude Code regardless of route (CLI,
      claude-plugins, or APM). When `#10997` ships a fix
      upstream, the test's expected first-firing session
      collapses to 1; the test fixture's observed-firing
      number is the contract, not a hard-coded "session 2."
      **Deferred via AC17's manual-QA matrix:** *marker
      presence* at Copilot, Cursor, and Gemini — their
      per-target first-firing sessions are not characterised
      at PR time and the conformance suite would assert
      against unknown ground truth (the `#10997` caveat does
      *not* automatically apply to them; that bug is
      Claude-Code-specific). AC15 closes when the spec's
      amended text names the one-Claude-Code + three-deferred
      shape; transcript arrival on AC17's matrix rows is the
      close criterion for the three deferred targets, not a
      blocker on this PR. One Changelog line
      names this spec by path. The contract version bump
      (v0.4 → v0.5) is recorded in
      `distribution-adapters/spec.md`'s Changelog alongside the
      existing v0.3 → v0.4 entry.
- [x] **AC16 (self-host drift gate covers the APM-projected
      writer at the same two axes the claude-plugins gate
      covers).** `make build-check` is amended to assert at every
      invocation, for every pack's
      `dist/apm/<pack>/.apm/hooks/install-marker.py`:
      (a) **Template-to-projection drift:** byte-identical to
      `packages/agentbundle/templates/install-marker.py`. A
      red-team fixture mutates one byte in a derived APM copy;
      the gate fails with a one-line stderr naming the
      diverged pack and path.
      (b) **Vendored helper parity:** the writer template's
      vendored `_emit_basic_string` function continues to
      produce byte-identical output to the source primitive
      across the attack-shaped input corpus defined by
      `claude-plugins-install-route` AC20 (b). The check runs
      once per build-check invocation regardless of route — the
      vendored helper is shared across routes; the check
      covers it for the APM-projected writer transitively. No
      route-specific corpus extension is required.
      The existing claude-plugins drift gate
      (`claude-plugins-install-route` AC20) continues to bind;
      this AC extends its surface to the APM projection in the
      same `make build-check` invocation.
- [ ] **AC17** (deferred: apm-install-route-parity) (manual-QA, transcript pending — see matrix rows 32-34) (manual-QA matrix rows for RFC-0010 close triggers
      and the per-target characterisation matrix).**
      `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
      gains three rows:
      (a) `apm install of core at project scope — marker write
      + nudge fire + /adapt-to-project class-1` (RFC-0010 Q6
      first demonstration);
      (b) `apm install -g of converters at user scope — marker
      write + nudge fire + /adapt-to-project class-1/2/3/4`
      (RFC-0010 Q6 user-scope leg);
      (c) `APM per-target characterisation — first-firing
      session at Copilot, Cursor, Gemini` (RFC-0010 §Drawbacks
      *APM-target hook-firing matrix uncharacterised*; closes
      the matrix once an adopter for each target produces a
      transcript).
      All three rows record `verification = transcript`; each
      names its close trigger explicitly. **AC17 closes when
      the three rows exist with `verification = transcript`
      and a named close trigger**; transcript arrival is
      RFC-0010 §Unresolved questions Q6's close trigger for the
      RFC itself, not for this spec. Per the matrix's existing
      `verification = transcript` deferral pattern, the
      transcript artifacts land in follow-ups.
- [x] **AC18 (per-pack README disclosure for the three no-hook
      APM targets — `packs/core/README.md` as required floor).**
      `packs/core/README.md` (created if absent) carries a
      one-paragraph disclosure under a heading like *Install
      routes and adaptation*. The paragraph contains, verbatim:
      (a) the four HookIntegrator-covered target names —
      `Claude Code`, `Copilot`, `Cursor`, `Gemini`; (b) the
      three uncovered target names — `Codex`, `OpenCode`,
      `Windsurf`; (c) the manual-fallback gesture string —
      `agentbundle adapt --scope` (the trailing `<project|user>`
      placeholder follows verbatim per RFC-0008's analogous
      claude-plugins disclosure pattern). One goal-based test
      asserts all three substring sets appear within the same
      paragraph (a single `grep -c` against the file is
      sufficient — the four-targets + three-targets +
      fallback-gesture surface is what readers actually read,
      not a structural Markdown shape). Other packs
      (`converters`, plus any future APM-routed pack) ship the
      same disclosure in follow-up PRs — implementer's
      judgement, not gated by AC18. `packs/core/README.md`
      is the required floor because RFC-0010 §Unresolved
      questions Q6 names `core` as the first-consumer pack.

## Changelog

- 2026-05-25: initial draft against RFC-0010.
- 2026-05-25: pre-EXECUTE adversarial-review reconciliation —
  (i) `--install-route` flag becomes `required=True` with
  two-valued `choices = {"claude-plugins", "apm"}` (the prior
  default-`claude-plugins` rail was a coin-flip back-compat;
  the required-flag rail fails fast on build-pipeline omission
  — Concerns 5, 6); (ii) AC1 allow-list pinned against the
  writer-file ground truth (pre-edit `{datetime, hashlib, json,
  os, pathlib, sys, tempfile, tomllib, re}`; post-edit adds
  `argparse`) with no "or whatever the writer says" escape
  hatch — Blocker 4; (iii) AC4 (e) rewritten as the genuinely
  load-bearing first-branch-wins precedence guard (writer
  under `$HOME` but not under cwd, with cwd nested under
  `$HOME` → `marker_scope = "user"`) — Blocker 1, Concern 7;
  (iv) AC12 (e) shrunk to one Claude Code characterisation
  test; Copilot/Cursor/Gemini deferred to AC17 manual-QA
  rather than skipped-in-CI — Concern 8; (v) AC9 split into
  positive assertions + regression guard for other-adapter
  no-change — Concern 14; (vi) AC15 conformance text states
  the one-Claude-Code + three-deferred shape and ties deferrals
  to AC17 — Concern 10; (vii) AC17 close criterion pinned to
  "three rows exist" (transcripts are RFC-0010 Q6's trigger,
  not this spec's) — Nit 19; (viii) AC18 floor pinned to
  `packs/core/README.md` with the three required substring sets
  — Nit 18; (ix) scope statement corrected from "four coupled
  deliverables" to five (the precedent-spec amendment is the
  fifth) — Nit 15; (x) Boundary-rail inheritance callout added
  so the spec-unique rails are not buried in the inherited bulk
  — Concern 11; (xi) AC1 docstring-edit requirement demoted
  from contract-surface to T1-Approach authoring detail
  — Concern 12.
- 2026-05-25: pre-EXECUTE adversarial-review iteration 2
  reconciliation — (i) Always-do "bump the projected
  claude-plugins hook command" bullet rewritten: the
  iteration-1 "back-compat via writer default" claim was
  factually false after Concern 5+6's flag became `required`;
  replaced with the writer-template + `install-marker.json`
  refresh-coupled-by-`make build` rail and the explicit
  fast-fail-on-mismatch story — Blocker 2; (ii) AC15
  *marker presence* caveat reframed: "first observed-firing
  session at Claude Code under APM — today session 2 or
  later because the `#10997` first-session-quirk applies to
  `SessionStart` at Claude Code regardless of route" — the
  caveat is target-specific, not route-deferred, and does
  not inherit to Copilot/Cursor/Gemini — Blocker 3;
  (iii) AC4 case (a) fixture rewritten with nested home
  structure (`home = .../home`, `cwd = .../home/proj`,
  writer at `cwd/apm_modules/<pack>/`) so the first-
  branch-wins rule is realised by the test, not just
  asserted by the spec text — Concern 7; (iv) Boundary-rail
  inheritance callout names the precedent's pinning ACs
  per inherited rail (cp-AC1, cp-AC4, cp-AC5, cp-AC6,
  cp-AC7, cp-AC12, cp-AC20, plus the two §Boundaries
  Never-do rails) — Concern 9; (v) AC10's brittle line-
  range reference dropped in favour of grep-by-symbol
  — Concern 11.
- 2026-05-25: pre-EXECUTE adversarial-review iteration 3
  reconciliation — (i) AC4 case (e) re-labelled from
  "first-branch-wins precedence guard" to "home-branch
  coverage when writer is outside cwd"; iteration-2 had
  the precedence semantics backwards (case (e)'s fixture
  yields the same result under both check orders; case
  (a)'s nested-home fixture is the actual precedence test).
  Plan-test docstring updated to match — Concern 1; (ii)
  AC3 gained cases (f) and (g) as explicit precedence
  pins with multiple data-dir tokens set simultaneously,
  closing the "reversed-precedence bug passes (a)–(e)" gap;
  unit-test count grows from five to seven — Concern 2;
  (iii) AC8 test re-homed:
  `test_claude_plugins_hook_command_now_passes_flag` belongs
  in `test_build_derivation_claude_plugins.py` (precedent
  spec's test file), not the APM file — Concern 3; (iv)
  the "coupled by `make build`" narrative in the Always-do
  "Bump the projected claude-plugins hook command" bullet
  rewritten to name the three load-bearing links:
  `templates/` ≡ `_data/` parity unit test (existing),
  `_data/` + `_SESSION_START_COMMAND` co-shipping in the
  wheel, AC16(a)'s `dist/` ≡ `templates/` drift gate
  — Nit 4; (v) T5 task title names the test-count math
  (five RFC-0010 scenarios → six tests; scope-refusal
  scenario gets two tests one-per-direction) — Nit 5;
  (vi) T8 gained
  `test_distribution_adapters_names_apm_test_file_by_path`
  pinning that the sibling spec carries the literal path
  to the APM test file — Nit 6.
- 2026-05-25: pre-EXECUTE adversarial-review iteration 4
  reconciliation — (i) Testing Strategy bullet for the
  writer template rewritten: `--install-route` is two-value
  `choices = {"claude-plugins", "apm"}`, `required=True`, no
  default; iteration-1's required-flag flip had left a stale
  "three-value choices and default-claude-plugins back-compat"
  prose in the canonical Testing Strategy paragraph an
  implementer reads first — Concern 1; (ii) AC10 fixture-set
  test wording made the v0.3-shape (absent `install-route`)
  case explicit alongside v0.4 / v0.5, and the plan's T3
  Tests list gained
  `test_v03_shaped_marker_without_install_route_field_parses_as_cli`
  so the absence-defaults-to-`"cli"` back-compat rail is
  tested in this PR rather than tacitly inherited — Concern 3.
- 2026-05-25: T1–T12 implementation landed via work-loop. Writer
  template gained `--install-route` argparse, data-directory shim,
  APM scope detection; contract bumped v0.4 → v0.5; build pipeline
  derives `dist/apm/<pack>/.apm/hooks/install-marker.{json,py}` and
  `pack.toml`; claude-plugins-route hook command bumped to pass
  `--install-route claude-plugins`; self-host drift gate extended
  to the APM projection; sibling specs amended in-PR
  (`claude-plugins-install-route`, `adapt-to-project`,
  `distribution-adapters`); manual-QA matrix gained three RFC-0010
  Q6 / spec AC17 rows; `packs/core/README.md` ships the
  four-of-seven HookIntegrator-coverage disclosure. Live-install
  transcripts (AC17 rows 32-34) remain `verification = transcript`
  deferred per the matrix's existing pattern; flipping the status
  to *Shipped* on the mechanical close-criterion side (AC1–AC16,
  AC18). Status: Approved → Shipped.
