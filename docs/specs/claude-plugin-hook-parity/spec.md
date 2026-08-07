# Spec: Claude-plugin hook parity

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md),
  [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md) (Accepted — the
  plugin-route scope taxonomy and the `allowed-scopes` refusal rail this spec extends)
- **Contract:** `contracts/adapter.toml`, `contracts/adapter.schema.json`,
  `contracts/plugin-manifest.derived.schema.json`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A pack that ships hook bodies and hook wiring gets working hooks on the
Claude-plugin route, the same way it does on the direct Claude adapter — and no
hook runs at a scope the pack forbids.

For `packs/core` specifically, which declares `allowed-scopes = ["repo"]`, that
means hooks work at `--scope project` / `--scope local` and stay refused at the
install default of `--scope user`. That is the correct outcome, not a
shortfall — but it is a user-visible one, so AC17 requires saying it out loud.

Today it does not. The claude-plugins route publishes a plugin whose hook
surface is one synthetic install-marker `SessionStart` entry. The pack's own
hooks are shipped as *inert files*:

```
dist/claude-plugins/core/
├── .claude-plugin/plugin.json    hooks: install-marker SessionStart only
├── .claude/settings.local.json   ← the plugin loader never reads this
└── tools/hooks/{session-start,work-loop-check,pre-pr}.py   ← bodies, unwired
```

Reproduced against the real `packs/core`, not only the fixtures. Claude Code
discovers plugin hooks from `hooks/hooks.json` at the plugin root or from the
manifest's `hooks` field; `.claude/settings.local.json` is a direct-install
destination and inside a plugin directory it is dead weight.

Four separable defects, each sufficient on its own:

1. **Wiring is never compiled.** `build/main.py:585` *assigns* `derived["hooks"]`,
   overwriting rather than merging, and the source manifest schema forbids
   authored hooks outright.
2. **Bodies land at a path the wiring cannot name.** `hook-body` has no
   `plugin-target-path`, so it keeps the repo-scope target `tools/hooks/` and
   the authored command `python tools/hooks/session-start.py` resolves against
   the adopter's working directory, not the plugin root. A verbatim copy of the
   wiring would ship a broken command.
3. **The derived schema cannot express the result.** It admits one event
   (`SessionStart`) under `additionalProperties: false`. `packs/core`'s
   `UserPromptSubmit` entry fails validation before it can be written.
4. **The scope rail does not cover compiled hooks.** RFC-0008 enforces a pack's
   `allowed-scopes` on this route, but the enforcement lives in the
   install-marker writer (`templates/install-marker.py:797,849`) and gates only
   *marker writing*. `packs/core` declares `allowed-scopes = ["repo"]`;
   `claude plugin install` defaults to `--scope user`. Compiling core's hooks
   into the same manifest as sibling entries would have them execute in every
   repo the adopter opens, unrefused, while the marker beside them correctly
   refuses. **This defect does not exist today only because defect 1 exists** —
   closing 1 without closing 4 ships a scope violation.

`packs/core` is the pack this bites: `session-start.py` (knowledge and
orientation injection) and `work-loop-check.py` (the work-loop nudge) are inert
for every adopter who installed core as a Claude plugin.

The out-of-scope note in the `claude-plugins-manifest-correctness` spec —
*"Hook wiring … is out of scope and unchanged"* (AC2) — is the deferral this
spec closes. RFC-0080 named the same area *"a separate, untriggered problem"*;
this spec is what triggers it.

## Boundaries

### Always do

- Fix the generator and the contract, then regenerate. Never hand-edit
  projected output.
- Keep the derived manifest inside what Claude Code documents. ADR-0072
  governs: upstream wins, and a local departure must be *restrictive* — it may
  narrow what we emit, never widen it past what the client accepts.
- Fail loud at build time, naming pack, wiring file, and command.
- Verify with the real `claude` client (2.1.223), not only the hermetic schema.

### Ask first

- Changing what `packs/core` authors — which events it wires, or the
  interpreter its commands invoke. This spec relocates and rewrites *paths*.
- Moving repo-scope hook-wiring off `.claude/settings.local.json`. That is the
  cross-adapter question RFC-0005's `user-merge-json` machinery makes
  tractable; it is **out of scope here and routed to a follow-on RFC**.

### Never do

- Emit a hook the pack did not author. The install-marker entry is the sole
  synthetic hook.
- Register the same hook twice. Authored wiring lands in exactly one place.
- Widen `additionalProperties: false` on a manifest schema to make a new shape
  validate.
- Change the direct, self-host, or APM routes' *projections*.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

### Precondition — satisfied

ADR-0072 records branch protection on `claude-plugins-dist` as a precondition
of publishing live code to adopters. It did not exist. It was applied before
this spec's approval: force-push denied, deletion denied, admins exempt for
recovery, no PR requirement (the branch is machine-published and
`publish_claude_plugins.py:119` is a plain fast-forward push, so CI is
unaffected).

## Decision — where compiled hooks land

Claude Code accepts plugin hooks in `hooks/hooks.json` at the plugin root or
inline in the manifest's `hooks` field. Hooks from every source *accumulate* —
"a plugin's or skill's copy of the same handler stays separate" — so emitting
to both would register each authored hook twice.

**Chosen: inline in the manifest**, merged with the install-marker entry. It is
the mechanism already shipping and already real-client-verified on this route;
one registration site makes double-fire structurally impossible; the pre-write
and post-write validation at `build/main.py:616,625` already guards it.

Rejected: **`hooks/hooks.json`** — better-documented and checked by name by
`claude plugin validate`, but it splits the hook surface across two files whose
combination rule the docs state only as "own merge rules".

Not weighed and now recorded: **exec form** (`args` array) instead of
shell form. AC4 uses shell form because the pack-authored `command` is a single
string and `args` would require pack authors to restructure their wiring; the
quoting discipline AC4 mandates is what makes shell form safe.

## Acceptance Criteria

- [ ] **AC1 — Authored wiring reaches the manifest.** For every pack shipping
  `.apm/hook-wiring/*.toml`, the derived `<pack>/.claude-plugin/plugin.json`
  `hooks` object contains every authored event and entry. Asserted on
  `packs/core`: `UserPromptSubmit` present, and `SessionStart` carrying both the
  authored `session-start.py` entry and the install-marker entry.

- [ ] **AC2 — Merge, not overwrite, in both directions.** The install-marker
  entry is present whether or not the pack authors `SessionStart`; authored
  `SessionStart` entries survive the merge. A pack with no `hook-wiring/`
  produces a manifest byte-identical to today's.

- [ ] **AC3 — Bodies at a plugin-root path.** On the claude-plugins route
  `hook-body` projects to `<pack>/hooks/<name>.{sh,py}` via a new
  `plugin-target-path`; `<pack>/tools/hooks/` is not emitted. The direct route's
  `tools/hooks/` target is unchanged.

- [ ] **AC4 — Commands resolve against the plugin root, by positional splice.**
  Rewriting replaces each occurrence of `<repo-hook-prefix><name>` **in place in
  the original command string** with a double-quoted
  `"${CLAUDE_PLUGIN_ROOT}/<plugin-hook-prefix><name>"`, leaving every other byte
  — operators, pipes, redirections, surrounding arguments — untouched. An
  optional leading `./` is absorbed. `packs/core`'s wiring compiles to
  `python "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py"`.

  Two mechanisms are **forbidden**, each having been shown to corrupt the
  command:
  - `str.replace` on the prefix (the gemini/cursor/copilot precedent) cannot
    emit the closing quote; the half-quoted result re-pairs quotes across a
    `&&` and silently turns two commands into one.
  - `shlex.split` + rejoin destroys shell operators, and `shlex.quote` emits
    **single** quotes, inside which `sh` does not expand `${CLAUDE_PLUGIN_ROOT}`
    at all — verified: the hook would resolve to a literal directory named
    `${CLAUDE_PLUGIN_ROOT}`.

  Double quotes are required, not incidental: they are what makes the variable
  expand while still surviving a space in the install path.

  **Verification is execution, not shape.** The emitted command is run through
  `sh -c` with `CLAUDE_PLUGIN_ROOT` set to a path containing both a space and a
  `$`, and the hook's observed `argv` must show the path as exactly one
  argument. A `shlex.split`-based round-trip assertion is not acceptable
  evidence — it returns one token for the broken single-quoted form too, so it
  cannot fail.

- [ ] **AC5 — Fail closed on an unrewritable or dangling command.** Two
  predicates, each stated at the depth that makes it checkable:
  (a) **basename scan over the whole command** — if any whitespace- or
  `=`-delimited fragment contains the basename of a hook body the pack ships and
  the command does not carry `${CLAUDE_PLUGIN_ROOT}`, raise. A basename scan,
  not token equality: `--script=tools/hooks/x.py` and a path nested inside
  `sh -c "python tools/hooks/x.py"` are not standalone tokens, and publishing
  either with a relative path is the failure class ADR-0072 exists to prevent.
  (b) **confinement, not existence** — each rewritten
  `${CLAUDE_PLUGIN_ROOT}/<prefix><name>` must correspond to a path that, after
  `resolve()`, is `relative_to` the pack's hook-body source directory. A bare
  `exists()` check would accept a `..`-bearing or symlinked name.

- [ ] **AC6 — Only `command` hooks are published.** A hook object whose `type`
  is not `"command"` raises with the same locating detail.

  This is the house convention for every adapter that *transforms* wiring:
  `copilot` (`projections/copilot_hooks_json.py:119`) and `gemini`
  (`adapters/gemini.py:406`) both raise on this condition; `cursor`
  (`adapters/cursor.py:332`) is the fail-open outlier that drops with a stderr
  log. This route transforms, so it joins the fail-closed cohort, and takes the
  raise over the drop because a dropped hook on a *published* artifact is
  invisible to the adopter. `claude-code` (direct) and `codex` pass
  non-`command` types through unvalidated — both use the shared verbatim
  `merge-json` projection and rewrite nothing. That inconsistency is real and
  out of scope; see `Deferred` in the PR description.

- [ ] **AC7 — Event names validated in the compiler, not the schema.** The
  compiler holds the documented Claude Code event set and raises on an unknown
  event, naming pack, wiring file, and event.

  The schema validates *shape* only, via `hooks: {additionalProperties:
  <entry-array schema>}`. This is deliberate: `build/validate.py` supports
  neither `$ref` nor `propertyNames`, so a closed event enum in the schema
  would mean 31 longhand copies of one subschema kept byte-identical across two
  mirrored files. One compiler-side frozenset is one source of truth, and it
  produces a locating error message where the schema would produce
  `$.hooks: additional property 'X' not allowed`.

  **Widening procedure:** an event joins the set only when it is present in
  Claude Code's published hook documentation at a named client version **and**
  an AC13 real-client run is recorded. Widening is mirror maintenance, never a
  local extension.

- [ ] **AC8 — Compiled hooks obey the pack's `allowed-scopes`, and workspace
  files can only narrow.** Every compiled hook command resolves the effective
  Claude-plugins scope and no-ops with a one-line stderr warning when that scope
  is outside the pack's `allowed-scopes` — the same rail
  `templates/install-marker.py` applies to the marker, now repaired by #890 to
  read the object form the client actually writes.

  **Trust invariant:** the permit is resolved from **adopter-controlled state
  only** — `$HOME` settings plus the pack's own install record under the
  adopter's plugin cache. Files under `${CLAUDE_PROJECT_DIR}` may *narrow* the
  resolved scope; they may never grant one. RFC-0008's `local → project → user`
  precedence is correct for deciding where to write a marker and backwards for
  deciding whether to execute: it ranks the least-trusted file highest, so a
  cloned hostile repo committing `.claude/settings.json` with
  `{"enabledPlugins": {"core@agent-ready-repo": true}}` would otherwise grant
  itself execution and pipe its own `docs/knowledge/patterns.jsonl` into model
  context.

  **Three-valued, and undetermined refuses.** The resolution returns
  `allowed` / `denied` / `undetermined`; only `allowed` runs the body. Unset
  `CLAUDE_PROJECT_DIR`, unset `HOME`, a malformed or unreadable settings file,
  and an empty `allowed-scopes` all resolve `undetermined`. For a marker write
  "undetermined" can safely mean *don't write*; for an execution decision it
  must mean *don't run*, and the fall-through must not be inherited unexamined.

  Asserted by exercising real settings files at each scope — including a
  hostile repo-committed `.claude/settings.json` that must not cause a hook to
  run — not by mocking the resolver.

- [ ] **AC9 — Bounded hook cost.** The compiler raises, with the AC5 locating
  detail, on: a `timeout` outside 1–60s (60 is Claude Code's documented default
  for command hooks; a lower ceiling is a local *restriction*, permitted under
  ADR-0072); more than 8 entries per event or 32 compiled hooks per pack; and a
  `matcher` whose **shape** is unbounded — anchored literals and alternations
  over tool names are admitted, nested unbounded quantifiers are not.

  A length cap is explicitly *not* the control for matcher cost: catastrophic
  backtracking is a complexity property, not a length one — `(a+)+$` is seven
  characters and burns the adopter's client. None of these bounds is expressible
  in the schema (`build/validate.py` has no numeric or length keywords), so all
  three live in the compiler.

- [ ] **AC10 — A pack with wiring but no source manifest raises.**
  `build/main.py:571` gates manifest synthesis on `plugin.json` existing. A
  pack shipping `.apm/hook-wiring/` with no `.claude-plugin/plugin.json` must
  raise naming the pack, not silently drop its hooks once `hook-wiring`
  resolves to `dropped`.

- [ ] **AC11 — No dead artifact.** The claude-plugins route emits no
  `<pack>/.claude/` directory.

- [ ] **AC12 — Idempotent and order-stable.** Warm and cold rebuilds produce
  byte-identical `plugin.json`. Within an event: the install-marker entry first,
  then authored entries in sorted wiring-filename order.

  Marker-first is for **determinism**, not suppression-resistance. Claude Code
  documents matching hooks running in parallel, so ordering does not protect the
  marker from a pack hook that blocks or exits non-zero; AC13 records the
  observed execution model rather than assuming one.

- [ ] **AC13 — Real-client verification, on the exact hook set.**
  `claude plugin validate` passes on the built `core` plugin, and
  `claude plugin details` reports the **exact** registered hook set — event
  names, entry count, and command strings — with no extra or missing
  registration. Plus one observed side effect of an authored hook firing, and
  the observed execution model for AC12. Registration alone does not discharge
  this AC: a hook whose command points at a nonexistent path registers fine,
  which is the failure class ADR-0072 exists to prevent. The same test asserts
  AC17's documented hook enumeration against the compiled `hooks` block, so
  prose and artifact cannot drift. Transcripts recorded in `plan.md`.

- [ ] **AC14 — Other routes unchanged; every changed consumer named.**
  `build/self_host.py` (direct via `project_packs`), `commands/pack_evals.py`,
  and the APM recipe emit output byte-identical to pre-change.

  **Five consumers run the `per-pack-claude-plugin` recipe via `render_pack` and
  therefore change by design:** `commands/render.py`, `commands/install.py
  --emit-install-routes`, `commands/upgrade.py`, `commands/diff.py`, and
  `commands/validate.py`. Each is asserted for its *expected* new output, not
  for byte-identity. `upgrade` and `diff` will additionally see the old
  `tools/hooks/` and `.claude/` paths as orphans; that is stated, not silently
  absorbed.

  Carve-out: `templates/install-marker.py` and the guard of AC19 are pinned by
  byte-drift gates whose *content* changes here. AC19 governs their mirrors.

- [ ] **AC15 — Pack-source gate.** `build/lint_packs.py` validates every
  `.apm/hook-wiring/*.toml` at authoring time — event key in the known set,
  `type = "command"`, `command` a string, bounds per AC9 — so a pack author
  learns at lint time rather than at build time. The blessed pack-source gate
  currently has no hook rule at all (zero occurrences of `hook` in 553 lines).

- [ ] **AC16 — Contract bumped and mirrored.** `contracts/adapter.toml` bumps
  `[contract].version`, declares `plugin-target-path` on `hook-body` and
  `plugin-mode` on `hook-wiring`, and stays byte-identical to
  `packages/agentbundle/agentbundle/_data/adapter.toml`.
  `contracts/adapter.schema.json` constrains `plugin-mode`'s **value** to the
  same enum as `mode`; a misspelled *key* is not caught by the schema — the
  projection-array item has no `additionalProperties: false` — and is caught
  instead by the value assertion in the contract task's done-when. Living docs
  stating the contract version are updated in the same PR:
  `docs/architecture/overview.md`, `pack-layout.md`, `agentbundle.md`, and
  `packages/agentbundle/DESIGN.md` (two occurrences).

- [ ] **AC17 — Adopter-facing disclosure, including what does *not* run.**
  `packs/core`'s README and the plugin `description` enumerate the hooks the
  plugin registers, the events they bind, and what each reads. The
  `[Unreleased]` changelog entry names this as a behavioural change, not a bug
  fix.

  It states plainly that `packs/core` declares `allowed-scopes = ["repo"]` while
  `claude plugin install` defaults to `--scope user`, so **at the default scope
  core's hooks are refused-and-warned and do not run**; working hooks require
  `--scope project` or `--scope local`. Adopters are told how to re-scope.

- [ ] **AC18 — Frozen spec superseded by erratum, not edited.**
  `docs/specs/wire-session-start-hook/spec.md` is `Status: Shipped` and
  therefore frozen; it pins
  `claude-plugins/<pack>/.claude/settings.local.json` in three places. It
  receives an erratum recording that AC11 supersedes that layout. The spec body
  is not edited.

- [ ] **AC19 — The guard is a governed artifact.** The scope guard runs from
  inside the plugin, so it ships as a projected file like
  `install-marker.py`. Its projected path is declared, it has a byte-identical
  `agentbundle/_data/` mirror, and it is added to the same `build/self_host.py`
  drift gates that pin the install-marker template — all three of them. It must
  not become a fourth uncontrolled copy of security-relevant code, and it must
  not `import` from `agentbundle`, which is unavailable in the plugin cache.

- [ ] **AC20 — The published artifact is validated at publish time.**
  `tools/catalogue/publish_claude_plugins.py` re-validates each `plugin.json`
  against the derived schema *and* the compiler's event set before pushing to
  `claude-plugins-dist`. Today the compiler and the schema both run inside the
  same build function, so they are never independent gates, and the publish step
  validates no manifest at all — a manifest reaching the branch by any route
  other than a clean build passes every check that exists.

- [ ] **AC21 — `plugin-target-path` resolves through the blessed helper.**
  `adapters/claude_code.py:_resolve_target` exists to confine a contract-owned
  target path, and its docstring already names `plugin-target-path` and the
  `shutil.rmtree` hazard — but `_project_direct_file` joins `target_prefix` onto
  the output root with no confinement. Adding a second contract-owned path key
  on the unconfined path extends an existing bypass; this change routes
  `_project_direct_file` through `_resolve_target`.

## Testing Strategy

- **Unit** — the compiler: merge-with-install-marker in both directions;
  marker-first ordering; token rewriting incl. multi-occurrence, leading `./`,
  trailing arguments, and a space-bearing root; `shlex.split` round-trip; each
  fail-closed raise (AC5 both sides, AC6, AC7, AC9); empty block when no
  `hook-wiring/`.
- **Scope** — AC8 at both scopes, driving the real writer's resolution path
  rather than a mock seam.
- **Schema** — accepts a compiled multi-event block with and without `matcher`;
  rejects a non-`command` type, an unknown key in a hook object, and an unknown
  key in an event entry (AC7's shape half).
- **Integration** — build the fixture packs; assert manifest hooks, `hooks/`
  bodies, absence of `.claude/` and `tools/hooks/`, byte-identical warm/cold
  rebuild, and the AC10 raise.
- **Regression** — a non-plugins build still emits `.claude/settings.local.json`
  and `tools/hooks/` (AC14).
- **Manual QA** — the real client, per AC13.

## Assumptions

- **Documented Claude Code hook events at 2.1.223** (`code.claude.com/docs/en/
  plugins-reference`, read 2026-08-07) — the normative set for AC7:
  `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`,
  `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`,
  `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`,
  `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`,
  `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`,
  `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`,
  `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`,
  `ElicitationResult`, `SessionEnd`.
- `hooks/` at the plugin root is a safe home for hook *bodies*: Claude Code
  discovers `hooks/hooks.json` by exact name, not by globbing `hooks/*`. AC13's
  exact-set assertion is what would catch this being wrong.
- Pack-authored commands reference hook bodies through the contract's
  repo-scope prefix. AC5 is the guard for when they do not.
- Pack-authored `command` strings are trusted input whose only gate before
  AC15 is PR review.

## Deferred

- Repo-scope hook-wiring moving from `.claude/settings.local.json` to the
  shared `.claude/settings.json` via RFC-0005's existing `user-merge-json`
  mode, so `claude-code` stops being the only adapter that hides repo-scope
  hooks from teammates. Cross-adapter and contract-versioned — **follow-on RFC**.
- `claude-code` (direct) and `codex` accepting non-`command` hook types
  unvalidated.
- Stale on-disk relpaths for adopters who ran `--emit-install-routes` before
  this change: `claude-plugins/<pack>/tools/hooks/*` and
  `.claude/settings.local.json` remain in their state file with no projection
  behind them. Not handled here; `upgrade`/`uninstall` behaviour unchanged.
- A per-pack content hash in the marketplace entry, so an installed plugin is
  traceable to the commit that produced it while `ref` stays mutable.
