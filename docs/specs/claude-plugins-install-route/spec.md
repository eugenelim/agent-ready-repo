# Spec: claude-plugins-install-route

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
  (canonical proposal — read first);
  [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (Claude-plugins as a canonical install route);
  [RFC-0003](../../rfc/0003-spec-and-cli.md) (CLI install→adapt chain
  the writer mirrors);
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (scope dimension
  the writer enforces);
  [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (current
  adapter contract v0.3; this spec bumps to v0.4);
  [RFC-0007](../../rfc/0007-user-scope-converter-pack.md) (first
  user-scope pack — makes the user-scope leg of the gap concrete).
  Amends [`docs/specs/adapt-to-project/spec.md`](../adapt-to-project/spec.md)
  (install→adapt chain, marker schema, proactive cache-scan AC) and
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (contract v0.4 bump, per-route conformance cases). Modifies
  [`docs/contracts/adapter.toml`](../../contracts/adapter.toml).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope of "one spec, three coupled deliverables."** RFC-0008's
> Follow-on artifacts list bundles two tightly-coupled build deliverables
> — `F-claude-plugin-derivation` (the build-pipeline change that produces
> the per-pack `.claude-plugin/` shape) and `F-claude-plugin-install-marker`
> (the canonical writer the derived shape ships) — and one paired skill
> amendment (`adapt-to-project` SKILL.md gains the proactive cache-scan
> branch). The three are coupled, not merely co-shipped: the writer
> cannot be authored without the derivation projecting it; the derivation
> has no purpose without the writer; the skill amendment is the mitigation
> that lets the writer accept the upstream `#10997` *passive-case*
> degradation (one-session-late nudge) by closing the *active case* (an
> adopter who proactively runs `/adapt-to-project` in session 1). Shipping
> any of the three without the others produces a partially-broken
> contract surface. Sibling spec amendments to
> `adapt-to-project/spec.md` (3 new ACs) and
> `distribution-adapters/spec.md` (one new AC + Changelog) land in the
> same PR per RFC-0008 §Follow-on artifacts.

## Objective

Close the install→adapt parity gap for Claude-plugins-routed installs.
The adopter who runs `claude plugin install <marketplace>/core` —
whether the marketplace is Anthropic's official one or any compatible
GitHub-marketplace fork — gets the same downstream experience as the
adopter who runs `agentbundle install --pack core`: the core pack's
session-start hook surfaces the *"N pack(s) pending adaptation; run
`/adapt-to-project`"* nudge, the skill consumes the install marker,
and the brownfield repo (or the user-home for user-scope packs) is
adapted to the project. The path-difference between the two install
routes is invisible to the adopter past the install command itself —
no second binary to install, no second README to read, no manual
"now run `/adapt-to-project`" step.

The mechanism is a `SessionStart` hook, derived by `agentbundle build`
into every pack's `.claude-plugin/plugin.json` (every pack in this
catalogue ships through the Claude-plugins route per RFC-0001), that
invokes a canonical
stdlib-Python writer at `packages/agentbundle/templates/install-marker.py`.
The writer detects first-install-or-update via the
`${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`-diff idiom Anthropic
documents, detects the install scope via the adopter's
`enabledPlugins` settings files, enforces `pack.toml` `[pack.install]
allowed-scopes` defence-in-depth, and writes a `[[packs-installed]]`
entry to the scope-correct marker file at
`<repo>/.adapt-install-marker.toml` (project / local scope) or
`~/.agentbundle/.adapt-install-marker.toml` (user scope). The marker
file location and `[[packs-installed]]` shape are unchanged from what
`agentbundle install` writes today; the entry gains an optional
`install-route` field that the read side treats as `"cli"` when absent
(backward-compat with v0.3-era markers). The adapter contract bumps
from v0.3 to v0.4 with a single `install-routes = ["cli",
"claude-plugins"]` array on `[adapter."claude-code"]` and per-route
conformance cases on the suite.

Done means: a fresh `claude plugin install` of any pack that ships
through the Claude-plugins route triggers the writer on
`SessionStart`, drops a marker the existing core nudge reads, and
`/adapt-to-project` runs class-1/2/3/4 normally — with one accepted
caveat documented in the spec: the upstream
[`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
bug delays the first-session nudge by one session on a brand-new
GitHub-marketplace install. The skill amendment in this spec closes
the *active case* of that bug (an adopter who proactively runs
`/adapt-to-project` in session 1) by adding a cache-scan branch; the
passive case (the nudge fires one session late) is accepted as
graceful degradation, not contract failure.

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires
human sign-off before proceeding; *Never do* is a hard rule.

### Always do

- **Map Claude-plugins' three settings-file scopes to the two
  install-marker scopes, but retain the most-specific origin scope
  for adopter-facing messages.** Claude-plugins exposes three opt-in
  surfaces — `local` (`.claude/settings.local.json`), `project`
  (`.claude/settings.json`), `user` (`${HOME}/.claude/settings.json`)
  — per RFC-0008 § Scope mapping. The install-marker layer carries
  two values only — `repo` and `user` — matching `pack.toml`
  `[pack.install] allowed-scopes` per RFC-0004. The writer collapses
  `local` and `project` to **`repo`** for the `allowed-scopes`
  comparison and for the marker-file location; it retains the
  original three-valued `detected_origin ∈ {local, project, user}`
  for any stderr message it emits, so an adopter who opted in at
  `local` sees `local` named in the refusal text rather than the
  ambiguous `repo`. The `install-route` field on the marker entry
  is `"claude-plugins"` regardless of which of the three origin
  scopes fired.
- **Keep the marker contract route-agnostic.** The
  `[[packs-installed]]` schema is identical across `install-route =
  "cli"` and `install-route = "claude-plugins"`; the only difference
  is the field's value. Any future install route (APM is the
  expected next one — see [RFC-0008 §Unresolved questions Q4](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions))
  must land as a third value on the `install-routes` array without
  a further marker schema bump.
- **Write the hash file at `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`
  only after the marker write succeeds.** A partial-write failure
  (disk full; permission denied at `~/.agentbundle/`) must leave no
  false "already adapted" signal — the next session retries the
  marker write. The order is: read existing marker → append → atomic
  rename of marker → write hash file.
- **Emit `installed-at` as a bare TOML offset-datetime literal,
  not a basic string.** The CLI writer at
  `packages/agentbundle/agentbundle/commands/install.py:910-911`
  writes `installed-at = ` followed by an unquoted
  `strftime("%Y-%m-%dT%H:%M:%SZ")` value; `tomllib` round-trips it
  as a `datetime.datetime`. The same CLI writer's defence-in-depth
  loader at lines 866-874 **drops** any entry whose `installed-at`
  is not a `datetime` (a basic-string `"2026-05-24T10:00:00Z"`
  parses to `str`, not `datetime`, and would be silently discarded).
  The Claude-plugins writer MUST emit the same bare-datetime
  shape so a CLI-then-Claude-plugins handoff (or vice versa) does
  not silently drop entries. This is the load-bearing handshake
  with the existing CLI marker schema — see AC7's sub-assertion
  on round-trip preservation.
- **Use `os.replace`-based atomic rename for the marker write** —
  the same primitive `agentbundle install._append_install_marker`
  uses (`packages/agentbundle/agentbundle/commands/install.py:800-934`).
  Two writers racing on the same marker file (the common case when
  multiple Claude-plugin packs ship the same `SessionStart` hook and
  fire in one session) both land an entry; the second writer reads
  the first's appended state before rewriting.
- **Refuse-and-warn on `allowed-scopes` mismatch.** When the detected
  install scope is not in the pack's `[pack.install] allowed-scopes`,
  the writer emits one stderr line in the form
  `install-marker: pack <name> declares allowed-scopes=<...>, detected install scope <detected>; skipping marker write`
  and exits 0. `${CLAUDE_PLUGIN_DATA}` is **not** updated — the next
  session re-checks and re-warns until the adopter reinstalls
  correctly.
- **Refuse-and-fallthrough on no-scope-match.** When every
  scope-detection check misses (plugin appears in no `enabledPlugins`
  list at any scope), the writer exits 0 without writing the marker
  **and without updating `${CLAUDE_PLUGIN_DATA}`**, so the next
  session retries. No partial state lands on disk.
- **Detect first install or update via the dual condition.** The
  writer fires when the hash at
  `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` is missing or differs
  from `sha256(${CLAUDE_PLUGIN_ROOT}/pack.toml)`, **or** the hash
  matches but the scope-correct marker file does not contain a
  `[[packs-installed]]` entry for this pack. The second condition
  covers the reinstall-after-`--keep-data` edge: hash file survives,
  marker entry was long-since consumed, the dual check forces a
  re-fire.
- **Project `pack.toml` into the derived `.claude-plugin/` alongside
  `install-marker.py`.** The writer reads
  `${CLAUDE_PLUGIN_ROOT}/pack.toml` for `name`, `version`, and
  `[pack.install] allowed-scopes`. The build pipeline projects the
  source `pack.toml` verbatim (copy, not transform).
- **Synthesise the `SessionStart` hook entry in the derived
  `plugin.json`.** Each pack's source-tree `plugin.json` declares
  `name` / `version` / `description` only; the build pipeline adds
  the `hooks.SessionStart` array with the canonical command
  `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py" --install-route claude-plugins`
  (the `--install-route` flag was added by T10 of
  `docs/specs/apm-install-route-parity/spec.md` so the canonical
  writer can be dispatched from both routes).
  Existing hand-authored per-pack `plugin.json` files migrate to the
  derived shape — the migration is part of this PR.
- **Ship the writer from one canonical template at
  `packages/agentbundle/templates/install-marker.py`.** Per-pack
  divergence is impossible by construction. Any security fix patches
  in one place and re-projects to every pack via `make build`.
- **Migrate the `adapt-to-project` skill body to scan the
  Claude-plugins cache when invoked proactively.** The skill amendment
  (per RFC-0008 §Unresolved questions Q1 active case) adds a branch
  that walks `~/.claude/plugins/cache/` and
  `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/` for known pack roots
  with no corresponding marker entry; when found, treats them as a
  fresh install and runs class-1/2/3/4 inline. Idempotent against the
  marker-consume path — when both signals are present in one session,
  the skill must not double-adapt.

### Ask first

- **Adding any persistent on-disk artifact beyond those named in
  this spec.** The writer touches three paths only:
  `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` (the hash file), the
  scope-correct `.adapt-install-marker.toml`, and the tempfile-in-
  same-directory the atomic rename uses. Anything else needs review.
- **Changing the dual-detection logic.** The "hash diff OR marker
  entry absent" condition is the contract surface that covers the
  reinstall-after-`--keep-data` edge. Tightening to hash-only would
  re-open that edge silently; loosening to marker-only would re-fire
  on every session.
- **Touching `${CLAUDE_PLUGIN_DATA}` in any state that is not
  "marker-write-just-succeeded".** The write-after-success ordering
  is the spec's robustness rail; bypassing it for a "harmless"
  pre-write breadcrumb re-opens the c-from-Drawbacks failure mode
  (hash file written, marker write failed, next session sees
  pack-manifest-hash match and skips the retry).
- **Adding any field to the `[[packs-installed]]` entry beyond
  `install-route`.** The schema is consumed by the existing core
  pack session-start nudge (unchanged by this spec) and the
  `adapt-to-project` skill (amended by this spec). Any new field has
  two readers to keep in sync.

### Never do

- **Never make the marker contract route-keyed at the file-shape
  level.** `install-route` is a value on an entry; it is not a
  separate file, not a separate table, not a separate schema. The
  *contract* surface remains route-agnostic; only the install-marker
  *case* in the conformance suite is route-keyed.
- **Never write `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` before
  the marker write succeeds.** Order is load-bearing for the
  Drawbacks-c partial-write recovery rail.
- **Never use anything other than `os.replace` for the marker write
  atomic-rename.** Other primitives (`shutil.move`, `rename`) have
  cross-filesystem fallbacks that silently degrade to non-atomic
  copy; the spec rail is strict atomicity.
- **Never add a non-stdlib Python dependency to
  `install-marker.py`.** The writer ships into every Claude-plugin
  cache directory on adopter machines; an `import requests` would
  require either bundling the library (cache size + per-update
  bandwidth cost across the catalogue) or installing it via the
  upstream-Anthropic-recommended `${CLAUDE_PLUGIN_DATA}` `npm
  install`-shaped idiom (`pip install`-shaped equivalent) which adds
  install-time network calls and supply-chain surface. Stdlib-only
  caps both costs at zero. The same rule already binds
  `packages/agentbundle/agentbundle/` (per
  `distribution-adapters/spec.md` Never-do, "No non-stdlib Python
  dependency"); this spec carries the rail forward to the projected
  artifact.
- **Never let per-pack writers diverge.** All `install-marker.py`
  files in every pack's `.claude-plugin/scripts/` are byte-identical
  copies of `packages/agentbundle/templates/install-marker.py`.
  `make build-check` (the self-host drift gate) is amended to assert
  this.
- **Never add a new top-level directory or package.** The new
  template lives under `packages/agentbundle/templates/` (a new
  module-adjacent surface, not a new package — it sits next to
  `packages/agentbundle/agentbundle/` as a peer of `_data/` and
  `tests/`, both of which already exist). The integration tests
  live under
  `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`,
  reusing the existing `tests/integration/` directory.
- **Never ship a fallback writer for the `#10997` passive case.**
  Per [RFC-0008 §Unresolved questions Q1](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions):
  the passive case (one-session-late nudge) is accepted; the active
  case is closed by the skill amendment. Adding a third writer
  (e.g. a hook in `core` that scans the cache pre-emptively) is
  out of scope and would couple a single detector to enumerating
  other packs' adapter-specific cache directories — the
  pack-boundary violation
  [RFC-0008 Alt 3](../../rfc/0008-claude-plugins-install-route-parity.md#alt-3--central-detector-in-core-or-as-a-standalone-shim-plugin)
  explicitly rejects.
- **Never invoke an LLM from the writer.** The writer is a CLI-rail
  primitive — the same *Never invoke an LLM* rail
  [RFC-0003 § Proposal](../../rfc/0003-spec-and-cli.md#proposal)
  pins for `agentbundle adapt`. Writer detects, writes, exits;
  consumption is the skill's job.
- **Never bypass the per-scope path-jail for the marker write.**
  User-scope marker writes route through the same primitive
  `_append_install_marker` does (`safety.write_jailed` with the
  `claude-code` adapter's `allowed-prefixes.user`). The CLI writer
  has this; the new writer must too. A bug in the projected pack's
  source code would otherwise be free to write under `~/.ssh/`.

## Testing Strategy

Three behaviour groups close this spec; each gets one verification
mode per the [`work-loop`](../../../.claude/skills/work-loop/SKILL.md)
taxonomy.

- **Writer logic — TDD.** Pure functions with compressible
  invariants: scope detection (precedence walk across the three
  `enabledPlugins` files; missing-file / malformed-JSON / absent-key
  fall-through), `allowed-scopes` refusal rail, dual-detection
  branch (hash-diff vs. marker-entry-absent), atomic-rename
  semantics (`os.replace` is the only primitive permitted),
  hash-after-marker ordering, two-writers-racing read-modify-write,
  reinstall-after-`--keep-data` edge. Tests live at
  `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
  and exercise the writer in subprocess against a fake
  `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${HOME}` /
  `${CLAUDE_PROJECT_DIR}` quartet — the writer's contract surface
  is its environment plus disk, so the test surface is environment
  plus disk.
- **Build-pipeline derivation — goal-based check.** `agentbundle
  build` against the catalogue's packs produces, for each pack:
  - `dist/claude-plugins/<pack>/.claude-plugin/plugin.json` with
    the synthesised `hooks.SessionStart` block;
  - `dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
    byte-identical to `packages/agentbundle/templates/install-marker.py`;
  - `dist/claude-plugins/<pack>/pack.toml` byte-identical to the
    source `packs/<pack>/pack.toml`.
  The check is a single command + a directory diff against a
  fixture; no internal assertions. Same for `make build-check` (the
  self-host gate): asserts no drift on a clean tree.
- **Live marketplace install — manual QA.** Per [RFC-0008
  §Unresolved questions Q5](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions),
  the close trigger for the RFC is the end-to-end demonstration on
  a real install: `claude plugin install core@<marketplace>`, next
  session writes `<repo>/.adapt-install-marker.toml`, core's nudge
  surfaces, `/adapt-to-project` runs. The matrix rows live at
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` (the
  existing per-repo matrix home; the install→adapt chain is
  authored by the `adapt-to-project` spec and this spec amends
  that chain, so the matrix it already owns is the right home).
  A second row covers `converters` at user scope to close the
  user-scope leg. Both rows record transcript-style evidence; both
  are gated by adopter availability, not by this PR — the rows
  ship with `verification = transcript` and the trigger column
  names the close criterion.

## Acceptance Criteria

- [x] **AC1 (canonical writer ships at the documented path,
      stdlib-only).**
      `packages/agentbundle/templates/install-marker.py` exists
      and contains only standard-library imports. The verification
      is a deterministic allow-list lint in T1's `Tests:`: a
      `grep -E '^(import|from) '` of the writer file produces a
      module set that is a subset of the explicit allow-list
      `{argparse, datetime, hashlib, json, os, pathlib, re, sys,
      tempfile, tomllib}` (any addition requires spec amendment).
      The `argparse` entry was added by T10 of
      `docs/specs/apm-install-route-parity/spec.md` for the
      `--install-route` flag; the `re` entry reconciles the
      enumerated set with the writer-file ground truth
      (`import re as _re`, vendored from the CLI's pack-name /
      pack-version shape rules — present since AC1 first shipped,
      added to the AC's enumeration by the same T10 reconciliation).
      The file's docstring names this spec by path
      (`docs/specs/claude-plugins-install-route/spec.md`). No
      line-count cap is asserted — the contract is the import
      surface and the function-shape contracts pinned in AC2–AC8;
      RFC-0008's ~80-line estimate is design guidance, not a
      verifiable rule.
- [x] **AC2 (scope detection — precedence local → project → user
      with fall-through semantics; origin-scope vs marker-scope
      collapse).** The writer reads, in order:
      `${CLAUDE_PROJECT_DIR}/.claude/settings.local.json`,
      `${CLAUDE_PROJECT_DIR}/.claude/settings.json`,
      `${HOME}/.claude/settings.json`. Missing file, malformed JSON,
      absent `enabledPlugins` key, or `enabledPlugins` present but
      not a JSON array of plugin identifiers are each treated as
      "not opted in at that scope" and fall through. When
      `${CLAUDE_PROJECT_DIR}` is unset, the project / local checks
      are skipped. The writer exposes two values internally: the
      three-valued `detected_origin ∈ {local, project, user}` (for
      adopter-facing stderr) and the two-valued
      `marker_scope ∈ {repo, user}` (used to pick the marker file
      and to compare against `[pack.install] allowed-scopes`).
      `local` and `project` both collapse to `marker_scope = "repo"`;
      `user` collapses to `marker_scope = "user"`. **No-match
      fall-through:** when every check misses, the writer exits 0
      without writing the marker and **without updating
      `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`**. Seven unit
      tests pin: (a) local-only opt-in for a repo-only pack →
      repo-scope marker written, `detected_origin = "local"`,
      `marker_scope = "repo"`; (b) project-only opt-in for a
      repo-only pack → repo-scope marker written,
      `detected_origin = "project"` — this case carries the
      regression guard for the `marker_scope = "repo"` collapse
      rail (a buggy implementation that compared the
      three-valued `detected_origin` against the two-valued
      `allowed-scopes` would refuse this case; the collapse
      must let it pass);
      (c) user-only opt-in for a user-only pack → user-scope
      marker written, `detected_origin = "user"`;
      (d) local + project + user all enabled → most-specific
      wins, `detected_origin = "local"`, `marker_scope = "repo"`;
      (e) malformed local-scope JSON → fall through to project;
      (f) every check misses → exit 0, no marker, no hash-file
      update;
      (g) `${CLAUDE_PROJECT_DIR}` unset + user opt-in for a
      user-only pack → user-scope marker written, project /
      local checks skipped without raising.
- [x] **AC3 (allowed-scopes refusal rail, origin-scope vocabulary
      in stderr).** When the writer's collapsed
      `marker_scope ∈ {repo, user}` is not in the installing pack's
      `[pack.install] allowed-scopes`, it emits exactly one stderr
      line matching the literal grammar `install-marker: pack
      <name> declares allowed-scopes=<list>, detected install
      scope <detected_origin>; skipping marker write` and exits 0.
      The `<detected_origin>` token uses the three-valued vocabulary
      (`local` / `project` / `user`) per the *Always do* scope
      mapping rule above — so an adopter who opted in at `local`
      sees `detected install scope local`, not `repo`. No marker
      is written; `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` is
      **not** updated. Three unit tests pin: (a) a repo-only pack
      enabled at user scope refuses with `detected install scope
      user`; (b) a user-only pack enabled at project scope refuses
      with `detected install scope project`; (c) a user-only pack
      enabled at local scope refuses with `detected install scope
      local` (regression guard on the origin-vocabulary rail). Each
      asserts the exact stderr line, a zero exit, and the absence
      of `pack-manifest-hash` after the refusal.
- [x] **AC4 (atomic marker write).** The marker write at every
      scope uses `os.replace`-based atomic rename: read-modify-
      write into a tempfile in the same directory as the marker
      file, then `os.replace(tempfile, marker_path)`. A unit test
      crashes the writer between the tempfile-write and the
      `os.replace` call (via a `monkeypatch` that raises
      `RuntimeError` after `tempfile.write` and before
      `os.replace`) and asserts: (a) the prior marker file is
      byte-unchanged after the crash; (b) the next writer
      invocation against the same target succeeds and is **not
      confused** by any leftover tempfile (the writer's contract
      is "next-run correctness," not best-effort cleanup; if the
      next run cannot succeed, the rail is broken). The test
      reads back the final marker file via `tomllib` and asserts
      both the pre-crash and post-recovery entries are present
      and well-formed.
- [x] **AC5 (hash file written only after marker write
      succeeds).** When the marker write raises, the writer exits
      non-zero **and does not write
      `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`**. The next
      session's writer invocation, against the same
      `${CLAUDE_PLUGIN_ROOT}/pack.toml`, recomputes the hash,
      finds the previous hash file absent, re-fires detection,
      and successfully writes both. One unit test crashes the
      marker write (via a `monkeypatch` that raises
      `PermissionError` from `os.replace`) and asserts: (a) no
      hash file on disk; (b) re-running the writer against the
      same `${CLAUDE_PLUGIN_ROOT}` produces a marker write and
      then a hash file.
- [x] **AC6 (dual-detection branch).** The writer fires when
      **either** `sha256(${CLAUDE_PLUGIN_ROOT}/pack.toml)` differs
      from the stored hash **or** the scope-correct marker file
      has no `[[packs-installed]]` entry naming this pack. Three
      unit tests pin: (a) cold start (no hash file) → writes; (b)
      `--keep-data` reinstall (hash file present and matches, but
      marker file absent / no entry for this pack) → writes; (c)
      warm cache (hash file matches **and** marker contains an
      entry for this pack) → no write, no stderr, exit 0.
- [x] **AC7 (two-writers-racing read-modify-write; CLI marker
      round-trip preservation).** Two writers invoked sequentially
      against the same marker file (the common case when multiple
      Claude-plugin packs ship the same `SessionStart` hook and
      fire in one session) produce a marker file containing both
      `[[packs-installed]]` entries. One integration test simulates
      this by running the writer twice in subprocess (different
      `${CLAUDE_PLUGIN_ROOT}`, same scope-correct marker target)
      and parses the resulting marker file via `tomllib`; both
      pack names appear in `packs-installed`. **CLI-handoff
      sub-assertion:** a second integration test pre-seeds the
      target marker file with an entry previously written by
      `agentbundle install` (carrying `installed-at` as a bare
      TOML offset-datetime literal, no quotes; produced by
      invoking the actual CLI install path against a fixture pack
      so the shape is canonical, not hand-typed). The new writer
      runs against the seeded file; the resulting marker file
      contains **both** entries; the pre-seeded entry's
      `installed-at` round-trips as a `datetime.datetime` value
      under `tomllib.loads` (not a `str`). This pins the
      Boundaries rail that the Claude-plugins writer's TOML
      emission is byte-compatible with the CLI writer's.
      *Two-process true-concurrency testing is out of scope —
      AC7 asserts sequential-writer correctness against the
      `os.replace` atomicity rail; see Risks.*
- [x] **AC8 (plugin upgrade replaces marker entry).** When
      `/plugin update` bumps a pack version, the next session's
      writer detects the manifest hash changed and re-writes the
      marker by **replacing** the existing entry for the same pack
      name (not stacking). One integration test pre-seeds the
      marker file with a `[[packs-installed]]` entry for `name =
      "core"`, version = "0.1.0", then runs the writer against a
      `${CLAUDE_PLUGIN_ROOT}` whose `pack.toml` declares version
      `0.2.0`; the resulting marker file has exactly one entry
      for `name = "core"` with `version = "0.2.0"`. Per
      [RFC-0008 §Unresolved questions Q3](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions)
      the replace semantics match the CLI route's
      `agentbundle install` overwrite-on-re-install.
- [x] **AC9 (build-pipeline derivation projects three artifacts
      per pack; hook-command shell-exec contract pinned).**
      `agentbundle build` against every pack in `packs/`
      produces, under each pack's
      `dist/claude-plugins/<pack>/.claude-plugin/`:
      (a) `plugin.json` with the synthesised `hooks.SessionStart`
      array containing exactly one entry with `command` equal to
      the literal string `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py" --install-route claude-plugins`
      (when read out of the JSON; the JSON source carries
      `\"` escapes for the embedded quotes) and all source-tree
      fields (`name`, `version`, `description`) preserved. The
      trailing `--install-route claude-plugins` flag was appended
      by T10 of
      `docs/specs/apm-install-route-parity/spec.md` so a single
      canonical writer template can be invoked from both routes;
      the writer's `argparse` rejects the flag's absence at parse
      time, so the build-pipeline and the projected command must
      stay coupled (see RFC-0010 / AC9 / AC10 of that spec).
      **Shell-exec contract.** Claude Code's plugins reference
      documents that hook `command` values run under `/bin/sh
      -c` (POSIX) or the equivalent on Windows; the double-
      quoted form survives spaces in `${CLAUDE_PLUGIN_ROOT}`.
      AC9 sub-assertion: when the command string is passed
      through `shlex.split` after substituting a synthetic
      `CLAUDE_PLUGIN_ROOT` containing a space (e.g.
      `/tmp/with space/root`), it yields exactly the four-token
      list `["python3", "/tmp/with space/root/.claude-plugin/scripts/install-marker.py", "--install-route", "claude-plugins"]`
      — pinning that the quoting actually works and that the
      flag tokens survive the substitution.
      (b) `scripts/install-marker.py` byte-identical to
      `packages/agentbundle/templates/install-marker.py`;
      (c) `pack.toml` byte-identical to
      `packs/<pack>/pack.toml`.
      A goal-based test diffs the produced tree against a
      checked-in fixture. `make build-check` exits zero against
      the migrated tree.
- [x] **AC10 (hand-authored `plugin.json` migration; two-gate
      drift protection).** Each pack's source-tree
      `packs/<pack>/.claude-plugin/plugin.json` declares only
      `name`, `version`, `description` (the fields the build
      pipeline preserves verbatim); the `hooks` block is **not**
      declared at source and is synthesised by the build. Drift
      protection ships as **two** mechanical gates, both wired
      into `make build-check`:
      1. **Schema split.** `docs/contracts/plugin-manifest.schema.json`
         is the source-shape schema and explicitly forbids the
         `hooks` property (via JSON-Schema `not: {required:
         ["hooks"]}` or equivalent). A sibling
         `docs/contracts/plugin-manifest.derived.schema.json`
         accepts the synthesised `hooks` block. The build
         pipeline validates source-tree manifests against the
         source schema and derived-tree manifests against the
         derived schema; a stray `hooks` block in source fails
         the source-schema gate at build time.
      2. **Build-check source-shape assertion.** `make
         build-check` (the self-host drift gate) additionally
         iterates every `packs/*/.claude-plugin/plugin.json` and
         asserts `"hooks" not in json.loads(...)`. The redundant
         check exists because a future schema change could
         silently relax the `not` clause; the in-Python
         assertion is a defence-in-depth rail that cannot be
         silently neutered by a contract edit.
      Both gates fire on every `make build-check` invocation;
      AC20's writer-drift gate runs alongside.
- [x] **AC11 (adapter contract bumps v0.3 → v0.4 with
      `install-routes` array; pack-side `adapter-contract.version`
      pin clarified).** `docs/contracts/adapter.toml`
      declares `[contract] version = "0.4"` and
      `[adapter."claude-code"] install-routes = ["cli",
      "claude-plugins"]`. `docs/contracts/adapter.schema.json`
      accepts the new flat array key on the adapter table.
      Existing adapter blocks (Kiro, Copilot, Codex) carry **no**
      `install-routes` key — the field is optional per-adapter
      and defaults to `["cli"]` on read.
      **Pack-side `[pack.adapter-contract] version` is a
      minimum-supported declaration, not a pin.** Each pack's
      `pack.toml` declares the lowest contract version against
      which the pack is known to project correctly. The
      `install-routes = ["cli", "claude-plugins"]` field is
      consumed by *adapter-side* tooling (conformance suite,
      catalogue indexers); it is **not** read from the pack's
      `pack.toml`. Existing packs declaring
      `[pack.adapter-contract] version = "0.2"` (per
      `packs/core/pack.toml:13` and siblings) continue to ship
      correctly under contract v0.4 without modification — the
      new install-route surface adds capability, it does not
      change the per-primitive projection rules a v0.2 pack
      conforms to. **No pack-side `pack.toml` edits ship in this
      PR**; pack-side version pin updates are scoped to a
      separate future change if and when v0.4-only fields appear
      on the pack manifest.
- [x] **AC12 (marker schema gains optional `install-route` and
      relaxes two existing arrays).** Per RFC-0008
      §*Marker entry fields*: under v0.4 each `[[packs-installed]]`
      entry MAY carry `install-route = "cli" | "claude-plugins"`
      (additive); v0.4 readers MUST treat absence as
      `install-route = "cli"` (backward-compat). `unresolved-markers`
      and `new-companions` become **optional** under v0.4
      (markers absent on a Claude-plugins-written entry; the
      read side scans the projected primitive tree directly when
      absent — the same scan the skill already runs when no
      marker exists at all). The schema amendment lands in
      `docs/specs/adapt-to-project/spec.md` § *.adapt-install-marker.toml
      schema*; the test fixture set adds one v0.3-shaped marker
      and one v0.4-shaped marker; both parse cleanly through the
      core pack session-start nudge and the `adapt-to-project`
      skill.
- [x] **AC13 (CLI route emits `install-route = "cli"`;
      cross-version reader tolerance pinned).**
      `agentbundle install._append_install_marker` is amended to
      emit `install-route = "cli"` on every entry. A regression
      test against an existing CLI install fixture asserts the
      field appears verbatim. The change is additive at the file
      level — v0.3 readers (pre-spec) ignore the field as an
      unknown TOML key; v0.4 readers consume it. Backward-compat
      with markers written before this PR is the AC12 "treat
      absence as cli" rail. **Cross-version reader tolerance
      sub-assertion:** one test loads a v0.4-shape marker
      (`install-route = "claude-plugins"` present) through the
      unchanged v0.3-era `_pack_names_from_marker` helper at
      `packs/core/.apm/hooks/session-start.py:170-179` and
      asserts the returned pack-name list is correct — pinning
      that the existing core session-start hook is not
      destabilised by the new optional field.
- [x] **AC14 (session-start hook reads marker unchanged).**
      `packs/core/.apm/hooks/session-start.py:182-193` (the
      `_emit_adapt_nudge` function) is **byte-unchanged** by this
      spec. A regression test loads a v0.4-shaped marker via the
      hook's existing `_pack_names_from_marker` helper and
      asserts the rendered nudge line is identical to the line
      a v0.3-shaped marker (with the same pack names) produces.
      The hook is route-agnostic by design; this AC pins that
      property as a regression test.
- [x] **AC15 (`adapt-to-project` skill amendment — proactive
      cache-scan branch).** `packs/core/.apm/skills/adapt-to-project/SKILL.md`
      Pre-flight section gains a sixth step (after the existing
      five) that scans `~/.claude/plugins/cache/` and
      `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/` for known
      pack roots (a directory containing `.claude-plugin/plugin.json`
      and `pack.toml`) with **no** `[[packs-installed]]` entry
      at either scope's marker file naming that pack. When found,
      the skill treats the cache-resident pack as a fresh install
      and runs class-1/2/3/4 inline. The branch is **idempotent
      with the marker-consume path**: if a marker entry for the
      same pack is present at either scope, the skill consumes
      the marker entry path (its existing behaviour) and the
      cache-scan does not double-adapt. The behaviour is grep-
      pinned because it is LLM-judgment, not deterministic
      code — there is no programmatic harness that runs the
      skill end-to-end (see AC4 of the parent `adapt-to-project`
      spec on the *(b)* grep verification method for LLM-judgment
      behaviour). Four SKILL.md body greps pin the contract:
      1. body contains the literal heading
         `Proactive cache scan.` (case- and punctuation-sensitive);
      2. body contains the literal path
         `~/.claude/plugins/cache/`;
      3. body contains the literal phrase
         `do not double-adapt`;
      4. body contains the literal phrase `if a marker entry is
         present, do not synthesise a second adaptation` (the
         operative dedupe rule the LLM reads).
      End-to-end verification of the idempotence behaviour ships
      as a manual-QA matrix row under AC19 — `verification =
      transcript`, deferred per the matrix's existing pattern.
- [x] **AC16 (`adapt-to-project` spec amendment — Acceptance
      Criteria).** `docs/specs/adapt-to-project/spec.md` gains
      **three** new Acceptance Criteria (numbered AC24 / AC25 /
      AC26 to extend the existing AC23):
      - **AC24 — read-side fallback contract.** When
        `unresolved-markers` or `new-companions` are absent on a
        `[[packs-installed]]` entry, the skill scans the projected
        primitive tree for `<adapt:NAME>` markers and
        `.upstream.<ext>` companions directly. Pinned by the
        skill-body grep set (AC15 grep #4 names the operative
        dedupe rule) plus the marker-schema round-trip tests
        added in T3 of this plan (a v0.4-shape entry missing both
        fields parses cleanly).
      - **AC25 — proactive cache-scan idempotence (grep-pinned).**
        When both a marker entry and a cache-resident pack root
        are present in one session for the same pack, the skill
        must not double-adapt. Pinned by SKILL.md body greps #3
        and #4 (per AC15). End-to-end verification is the
        manual-QA matrix row added by AC19. There is no
        programmatic skill-execution harness in v1; the spec
        explicitly accepts grep + manual-QA as v1 verification
        for this LLM-judgment behaviour.
      - **AC26 — stale-entry drop-on-read** (per
        [RFC-0008 §Migration path step 5](../../rfc/0008-claude-plugins-install-route-parity.md#migration-path)
        — *"adapt-to-project on read detects 'pack not installed
        at any scope' and silently drops the entry"*). Pinned by
        SKILL.md body grep (one additional literal added in T7).
        Programmatic verification is deferred to the
        Claude-plugins uninstall handling RFC (per
        [RFC-0008 §Unresolved questions Q2](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions))
        — explicitly forward-referenced.
      The three ACs land as `[ ]` entries; their implementation
      is in the plan below.
- [x] **AC17 (`distribution-adapters` spec amendment —
      conformance suite cases).** `docs/specs/distribution-adapters/spec.md`
      § *Recipe set* and § *Acceptance Criteria* gain references
      to the v0.4 contract bump (one line in the Changelog naming
      this spec; one new AC pinning that the conformance suite
      ships a *marker presence* and a *scope refusal* case per
      declared install route; the existing recipe-set table is
      unchanged). The Claude-plugins *marker presence* case is
      asserted on **session 2 or later** until upstream
      [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
      ships a fix — per RFC-0008 §*Conformance cases added*. The
      fixture-set additions live under
      `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
      (this spec's owned test file) and are referenced from the
      sibling spec by path.
- [x] **AC18 (integration tests cover the five RFC-named
      scenarios with explicit test names).**
      `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
      exists and contains tests pinning the five scenarios named
      in [RFC-0008 §Follow-on artifacts](../../rfc/0008-claude-plugins-install-route-parity.md#follow-on-artifacts)
      under *F-claude-plugin-install-marker*. The tests are named
      explicitly so a reviewer can grep the file and confirm
      coverage without manual cross-mapping:
      (a) first-install marker write at each origin scope —
        `test_first_install_local_scope`,
        `test_first_install_project_scope`,
        `test_first_install_user_scope`;
      (b) no-write-on-warm-cache — `test_warm_cache_skips_write`;
      (c) scope refusal — `test_refuse_repo_only_pack_at_user_scope`,
        `test_refuse_user_only_pack_at_project_scope`,
        `test_refuse_user_only_pack_at_local_scope`;
      (d) plugin upgrade replace —
        `test_plugin_upgrade_replaces_entry`;
      (e) reinstall-after-`--keep-data` —
        `test_reinstall_after_keep_data_uninstall`.
      Each test runs the writer in subprocess against a
      fixture-controlled environment quartet
      (`${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`,
      `${HOME}`, `${CLAUDE_PROJECT_DIR}`) and asserts the marker
      file's `tomllib`-parsed shape. Some of these tests overlap
      with AC2 / AC3 / AC6 / AC8 unit assertions; that is
      intentional — the AC18 tests are the **end-to-end** view
      named in RFC-0008 §Follow-on artifacts, exercising the
      writer against the same environment quartet a real
      Claude-plugins install presents.
- [x] **AC19 (manual-QA matrix gains three rows; close-trigger
      rows pinned).** `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
      gains three rows:
      (a) `claude-plugins install of core at project scope —
      marker write + nudge fire + /adapt-to-project class-1`
      (RFC-0008 Q5 first demonstration);
      (b) `claude-plugins install of converters at user scope
      — marker write + nudge fire + /adapt-to-project
      class-1/2/3/4` (RFC-0008 Q5 user-scope leg);
      (c) `proactive cache scan idempotence — marker entry
      present, no double-adapt` (the end-to-end pin for AC25,
      since the LLM-judgment behaviour has no programmatic
      harness in v1).
      All three rows record `verification = transcript`; each
      names its close trigger explicitly. The rows ship in this
      PR; the transcript artifacts are deferred to follow-up
      per the matrix convention (AC19 itself is a structural
      gate on the matrix shape, not on the live transcripts).
- [x] **AC20 (self-host drift gate covers the projected
      writer at two axes).** `make build-check` is amended to
      assert two things at every invocation:
      (a) **Template-to-projection drift:** every
      `dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
      is byte-identical to
      `packages/agentbundle/templates/install-marker.py`. A
      red-team fixture mutates one byte in a derived copy; the
      gate fails.
      (b) **Vendored helper parity:** the writer template's
      vendored `_emit_basic_string` function (the basic-string-
      emit primitive copied from `agentbundle.config._emit_basic_string`
      to keep the writer stdlib-only) produces byte-identical
      output to the source primitive across a fixed corpus of
      attack-shaped inputs (control characters, embedded `"`
      and `\`, the empty string, a multi-byte unicode
      character). A red-team fixture mutates the vendored
      function (e.g., strips the control-char refusal); the
      gate fails. This rail closes the otherwise-untracked
      drift surface noted in iteration-2 Concern 4 — the
      vendored helper is security-load-bearing (it prevents
      TOML-injection from adversarial pack metadata), and the
      drift check must therefore be mechanical, not
      author-discipline.
      Both axes bind the "per-pack divergence impossible by
      construction" rail to mechanical drift tests.

## Changelog

- 2026-05-24: initial draft against RFC-0008.
- 2026-05-24: pre-EXECUTE adversarial-review reconciliation —
  (i) added a Boundaries Always-do bullet pinning the
  Claude-plugins-three-scopes → install-marker-two-scopes
  collapse rule and the origin-scope-retained-for-stderr
  vocabulary (Blocker 1); (ii) added Always-do bullet pinning
  `installed-at` as a bare TOML offset-datetime literal
  (Blocker 3); (iii) repointed manual-QA matrix references to
  the existing home at `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
  (Blocker 2); (iv) demoted the proactive cache-scan idempotence
  verification from an integration-test ask to a grep-pinned
  body assertion + manual-QA matrix row (Blocker 4 — there is
  no programmatic skill-execution harness in v1); (v) split
  `plugin-manifest.schema.json` into source-shape (forbids
  `hooks`) and derived-shape (accepts `hooks`) schemas and
  wired the source-shape assertion into `make build-check`
  (Blocker 5); (vi) tightened AC2 with the project-scope-on-
  repo-only-pack regression guard and the `${CLAUDE_PROJECT_DIR}`-unset
  case (Concerns 6, 7); (vii) AC3 stderr vocabulary pinned to
  three-valued origin (Concern 7); (viii) AC4 wording
  tightened from best-effort cleanup to next-run correctness
  (Nit 18); (ix) AC7 gained CLI-handoff datetime-round-trip
  sub-assertion (Blocker 3); (x) AC9 gained shell-exec
  contract sub-assertion via `shlex.split` (Concern 10);
  (xi) AC13 gained cross-version reader tolerance assertion
  (Concern 11); (xii) AC1 dropped the arbitrary 150-line cap
  (Concern 12); (xiii) AC11 clarified pack-side
  `adapter-contract.version` as minimum-supported (Concern 13);
  (xiv) AC16 / AC18 / AC19 surfaced explicit AC numbers and
  test names (Concerns 8, 14); (xv) `one spec, two artifacts`
  framing widened to `one spec, three coupled deliverables`
  (Concern 15); (xvi) Nits 16-17 absorbed (every-pack-via-route
  prose; grep literal sharpened to `Proactive cache scan.`
  punctuation-sensitive form).
- 2026-05-24: pre-EXECUTE adversarial-review iteration 2
  reconciliation — AC20 now pins **two** axes of drift
  protection on the writer template (template-to-projection
  byte-identity **and** vendored `_emit_basic_string` parity
  across an attack-shaped input corpus, closing iteration-2
  Concern 4); AC2 collapsed from eight to seven unit tests
  with the regression-guard intent folded into case (b)
  (iteration-2 Nit 5).
- 2026-05-25: AC1 allow-list reconciled with writer ground truth
  (`re` added, listed alongside the pre-existing `argparse`); AC9
  hook-command literal and `shlex.split` expected-token list
  extended with `--install-route claude-plugins`; §Proposal
  synthesised-hook description bumped to match. All per T10 of
  `docs/specs/apm-install-route-parity/spec.md` — both specs
  reconcile to the same post-edit module set and the same
  projected hook command.
- 2026-05-31: Status reconciled to Shipped; ACs checked against
  the merged implementation (retroactive — implementation landed
  in prior PRs). All 20 ACs verified satisfied against the current
  working tree (writer template, integration/hook tests green,
  contract at v0.8 with `install-routes` including
  `"claude-plugins"`, schemas, skill amendment, and sibling-spec
  amendments all present); no deferrals.
