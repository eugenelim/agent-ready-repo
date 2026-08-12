# Spec: Claude-plugin route — hook parity

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (scope is a per-pack default + allowance), [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md), [ADR-0079](../../adr/0079-executable-plugin-branch-publisher-identity.md), [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
- **Contract:** `contracts/adapter.toml`, `contracts/adapter.schema.json`, `contracts/plugin-manifest.derived.schema.json`
- **Shape:** integration
- **Spike:** resolved 2026-08-10 against Claude Code 2.1.226. The strict
  validator matrix, runtime-loader probe, and sanitized transcripts are in
  `plan.md`; the input manifests are the `spike-*.json` files beside this spec.
- **Depends on:** [`../claude-plugin-route-scope/spec.md`](../claude-plugin-route-scope/spec.md),
  which split out the scope filter and the docs fix — those were shippable and
  survived rounds 4 and 5 unchallenged. Scope correctness must land first: it
  determines which packs the compiler ever runs for.

> **Split note (2026-08-07).** Scope correctness (the publish filter) and the
> documentation fix moved to the sibling spec above and are no longer criteria
> here. What remains is the hook compiler.
>
> **Spike decisions (2026-08-10, Claude Code 2.1.226):**
>
> - **Keep marker emission unconditional.** Both an empty `hooks` object and the
>   synthetic `SessionStart` entry pass strict validation. The client exposes no
>   marker-reader semantic, and a `[pack.install] marker-reader` flag would make
>   every manifest depend on marketplace composition for one hypothetical
>   caller. Preserve the already-shipped marker entry in every published pack.
> - **Reject instruction-injection and permission-control events.** Strict validation accepts
>   all 31 documented events. The installed runtime shows `PreToolUse` and
>   `PermissionRequest` can allow or deny a tool call, `PermissionDenied` can
>   request a retry, and `Setup` supplies additional context rather than a
>   permission decision. Supplying context before the adopter invokes a skill is
>   still an instruction-injection surface, so authored plugin hooks reject all
>   four. Marketplace entries can carry inline hooks, but
>   those are executable components appended to `plugin.json`, not disclosure
>   metadata, so copying the hook block there would double-register it.
> - **Use an exact invocation grammar.** The client accepts `python3 -c`, shell
>   operators, substitutions, backticks, and newlines even under `--strict`.
>   The compiler accepts one interpreter token, one shipped hook-body path, and
>   no other tokens. This deletes the quote-aware splice problem instead of
>   trying a fourth shell rewriter.
> - **Validate at the shared ingestion boundary.** `agentbundle validate` accepted
>   a Claude-shaped command carrying `;`, confirming the direct-route residual.
>   The same neutral validator must run in the shipped validate/install path and
>   in the repository lint. Valid direct-route output remains byte-identical;
>   invalid third-party wiring now fails before `merge_json`.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**A pack that ships hook bodies and hook wiring gets working hooks on the
Claude-plugin route.** Today the route publishes them inert: wiring lands in
`<pack>/.claude/settings.local.json` (a direct-install destination the plugin
loader never reads) and bodies land at `<pack>/tools/hooks/`, named by a command
relative to the adopter's working directory rather than the plugin root.
`build/main.py` *assigns* `derived["hooks"]` rather than merging, and the derived
schema admits one event.

> **Scope, docs, and the publish filter are not this spec.** They are
> [`../claude-plugin-route-scope/spec.md`](../claude-plugin-route-scope/spec.md),
> which must land first — it determines which packs the compiler ever runs for.
> That spec's filter excludes every repo-only pack, and `packs/core` is the only
> pack shipping `.apm/hook-wiring/` today, so **this spec activates no hook on
> any currently-published pack.** It makes the route correct for the next
> user-capable pack that ships hooks, and for the install→adapt chain's
> user-scope path.

## Boundaries

### Always do

- Fix the generator and the contract; never hand-edit projected output.
- Keep the derived manifest inside what Claude Code documents (ADR-0072:
  upstream wins; a local departure must be *restrictive*).
- Fail loud at build time, naming pack, wiring file, and command.
- Verify with the real `claude` client (2.1.226).
- Land and verify AC35 before any authored hook is published.

### Ask first

- Changing the interpreter a pack's hook commands invoke (`python` vs `python3`;
  bare `python` is absent on stock macOS). Pre-existing on every route.

### Never do

- **Change any pack's `default-scope` or `allowed-scopes`.** If a pack's reach
  is wrong, that requires a separate owner-approved spec and PR. It is not a
  lever this spec pulls.
- Change what `packs/core` authors — events, interpreters, or hook bodies.
- Emit a hook the pack did not author, or register one twice.
- Grant a user, team, repository role, administrator role, deploy key, or the
  generic GitHub Actions app bypass access to the executable dist branch.
- Put the publisher-app credential in a repository- or organization-level
  secret; it belongs only to the protected publish environment.
- Widen `additionalProperties: false` on a manifest schema to make a new shape
  validate.
- Change valid direct, self-host, or APM route projections. The shared
  validation boundary may reject wiring that those routes previously copied
  verbatim.
- Add a third-party dependency (`pyproject.toml` `dependencies = []`).

### Blocking precondition — publisher-only branch integrity

ADR-0072 records branch integrity on `claude-plugins-dist` as a precondition for
publishing executable content. Force-push and deletion denial protect history,
not the branch tip: an ordinary fast-forward push can still replace every hook
body. Authored-hook publication therefore remains blocked until AC35 lands.

The control is deliberately not a bypass for the repository's generic GitHub
Actions app. Every workflow `GITHUB_TOKEN` is an installation token for that
same app, so such a bypass would let any present or future workflow with
`contents: write` update the executable branch. Instead:

- an installed, repository-scoped publisher GitHub App has repository Contents
  read/write and no other write permission;
- an active branch ruleset targets exactly
  `refs/heads/claude-plugins-dist`, restricts updates and deletion, blocks force
  pushes, and names that publisher app as its **only** always-bypass actor;
- the publish job's ordinary `GITHUB_TOKEN` is read-only and checkout does not
  persist it; the job mints a short-lived publisher-app token only after the
  `claude-plugin-publish` environment's required reviewer approves the job;
- the environment admits deployments from `main` only and stores the app ID and
  private key. No credential value or transformed derivative is logged or
  committed.

The ruleset and protected environment are repository settings, not files. A
sanitized API snapshot plus negative ordinary-push and positive publisher-app
push evidence are required artifacts; configuration prose alone does not
satisfy the precondition.

## Decision — where compiled hooks land

Claude Code accepts plugin hooks in `hooks/hooks.json` or inline in the
manifest's `hooks` field, and hooks from every source *accumulate* — so emitting
both would register each hook twice.

**Chosen: inline in the manifest**, merged with the install-marker entry. It is
the mechanism already shipping and real-client-verified on this route; one
registration site makes double-fire structurally impossible; the pre- and
post-write validation in `build/main.py` already guards it.

Rejected: `hooks/hooks.json` — accepted by the 2.1.226 strict validator when
referenced from the manifest, but it splits the surface across two files. The
runtime accumulates hook sources, so a second registration site raises the risk
of a double fire.

Not chosen, recorded: exec form (`args` array). The pack-authored `command` is a
single string; `args` would require pack authors to restructure their wiring.
The exact invocation grammar below makes the retained shell form bounded.

## Decision — command and event boundary

The publishable command is deliberately smaller than Claude Code's accepted
shape:

```
<interpreter> <repo-hook-path>
```

`<interpreter>` is `python`, `python3`, `sh`, or `bash`. The hook-body suffix
must match the interpreter family (`.py` for Python, `.sh` for the shell), the
path must name exactly one shipped body under the contract's `hook-body`
source-path, and no leading interpreter flag or trailing argument is allowed.
After validation the compiler emits the interpreter plus one double-quoted
`${CLAUDE_PLUGIN_ROOT}` path. A future pack that genuinely needs arguments can
widen this grammar with a real caller and an execution test.

The compiler holds two event sets. `KNOWN_EVENTS` mirrors every event accepted
by the named client version. `PUBLISHABLE_EVENTS` removes `Setup`,
`PreToolUse`, `PermissionRequest`, and `PermissionDenied`. The three permission
events can grant or deny a tool call or cause a denied call to be retried;
`Setup` can inject instructions or other context before the adopter invokes a
skill. Unknown events and known-but-unpublishable events both fail loud with
different messages.

## Decision — disclosure and marker behavior

The synthetic install-marker `SessionStart` entry remains first in every
published manifest. No marker-reader flag is added, and output does not depend
on which other packs happen to be published.

Claude Code 2.1.226 accepts inline hooks on marketplace entries, but treats them
as executable hook components and appends them to `plugin.json`. They cannot be
used as metadata-only disclosure without registering every hook twice. A pack
with authored wiring has its generated marketplace description append a
deterministic authored-hook inventory. Each entry names the event, matcher (or
`*`), effective timeout, interpreter, and plugin-relative body path, plus the
total authored-entry count. The marketplace entry continues to omit the
executable `hooks` key.

## Decision — shared validation boundary

Hook wiring is validated before any adapter projects or merges it. The shipped
`agentbundle validate` and install/render paths call the same neutral rules as
the repository's pack lint and the plugin compiler. Adapter-specific shapes
remain scoped: Kiro's lowercase event vocabulary and Claude's flat user-scope
shape are skipped by the plugin compiler, then validated by their existing
owners. This change does not rewrite a valid direct-route command; it stops an
invalid one before it reaches `merge_json`.

## Acceptance Criteria

> **Moved.** Scope correctness and the documentation/site fix now live in `../claude-plugin-route-scope/spec.md` as its
> one-predicate-three-writers, site-gating, and prose-docs criteria. They
> are not restated here; that spec must land first.

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

- [ ] **AC10 — Commands resolve against the plugin root after exact-shape
  validation.** An authored command must contain exactly two shell tokens: one
  interpreter from `python`, `python3`, `sh`, or `bash`, followed by one relative
  path naming a shipped hook body. An optional leading `./` on the path is
  absorbed. Python interpreters require a `.py` body; shell interpreters require
  `.sh`. Interpreter flags, trailing arguments, environment assignments,
  absolute paths, operators, redirections, substitutions, and additional hook
  paths all raise.

  The compiler emits
  `<interpreter> "${CLAUDE_PLUGIN_ROOT}/<plugin-hook-prefix><name>"`. It does
  not preserve or rewrite a general shell program.

  **Verification is execution.** The emitted command runs through `sh -c` with
  `CLAUDE_PLUGIN_ROOT` set to a path containing a space and a `$`, and the hook's
  observed `argv` must show the path as exactly one argument. A tokenization-only
  assertion is not acceptable evidence.

- [ ] **AC11 — Fail closed on a dangling or non-confined hook path.** The one
  path token must resolve to a regular, non-symlink file under the pack's
  hook-body source directory and its basename must match exactly one body the
  pack ships. `resolve()` plus `relative_to()` proves confinement; `exists()`
  alone is insufficient. A path through another directory, a missing body, a
  symlink, or a command that names zero or multiple bodies raises. `OSError` and
  `RuntimeError` from resolution or stat are converted to the same locating
  validation error; neither a traceback nor an aborted multi-pack lint is an
  acceptable result.

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

- [ ] **AC14 — Known and publishable event names are separate; the schema
  validates shape.** The compiler holds the documented event set and raises on
  an unknown event, naming pack, file, and event. It separately rejects
  `Setup`, `PreToolUse`, `PermissionRequest`, and `PermissionDenied` as known
  but unpublishable instruction-injection or permission-control events. The
  schema uses
  `hooks: {additionalProperties: <entry-array schema>}` — `build/validate.py`
  supports neither `$ref` nor `propertyNames`, so a closed enum there would mean
  one longhand copy per documented event across two mirrored files.

  **Per-adapter scoping:** `.apm/hook-wiring/` is shared by every adapter.
  Kiro's lowercase `agent-event-vocabulary` (`agentSpawn`, `userPromptSubmit`, …)
  and the flat user-scope Claude shape (top-level `command`, no `type`) are
  contract-supported and must be **skipped, not raised on** — this compiler
  validates only entries in the Claude PascalCase nested shape.

  **Widening procedure:** an event joins `KNOWN_EVENTS` only when the named
  client version accepts it and an AC18 real-client run is recorded. Moving any
  known-but-unpublishable event, including `Setup`, into `PUBLISHABLE_EVENTS`
  additionally requires adopter-visible consent and disclosure plus a
  real-client verification; pack-owner consent alone is not enough.

- [ ] **AC15 — Bounded hook cost.** The compiler raises on a `timeout` outside
  1–60s (60 is Claude Code's documented default; a lower ceiling is a
  *restriction*, permitted under ADR-0072) and on a `matcher` that does not
  satisfy AC31's canonical bare-literal-alternation grammar.

  A pack may compile at most 16 authored hook entries total and at most four
  entries for any one event. The synthetic install-marker entry does not count
  toward either authored limit. Both limits are enforced before manifest
  emission and have boundary tests at limit and limit-plus-one. The runtime
  launches hook commands in parallel, so a timeout ceiling without a fan-out
  ceiling is not a cost bound.

  An allowlist grammar, not a shape heuristic: deciding "nested unbounded
  quantifiers" needs a regex AST, `agentbundle` is stdlib-only, and a textual
  heuristic is evaded by `(?:a+)+` and `(a|ab)*$`. A bypassable check that reads
  as a control is worse than none.

- [ ] **AC16 — A route-eligible pack with wiring but no source manifest raises.**
  `build/main.py` gates manifest synthesis on `plugin.json` existing; a
  user-capable pack with wiring must raise naming the pack rather than silently
  drop its hooks. A repo-only pack remains outside the route and keeps its
  established direct-route behavior.

- [ ] **AC17 — No dead artifact.** The route emits no `<pack>/.claude/`.

### Verification and hygiene

- [ ] **AC18 — Real-client verification.** Against Claude Code 2.1.226,
  `claude plugin validate --strict` passes on a
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
  schema (the projection-array item has no `additionalProperties: false`). Every
  living document stating the version is updated from T2's grep-derived sweep;
  T2 is the canonical inventory rather than a duplicated filename list here.

- [ ] **AC22 — Plugin-publication ingestion gate.** `agentbundle validate`
  applies the restricted rules to a route-qualified pack, and every consumer
  that derives the `per-pack-claude-plugin` recipe reaches the same compiler
  before it can emit that plugin. `build/lint_packs.py` separately dry-runs the
  compiler for every wiring pack and converts each raise into a finding rather
  than aborting the sweep. Direct adapter dispatch does not apply publication
  policy: repo installs, self-host projection, Copilot, Kiro, and flat Claude
  user-scope shapes remain owned by their existing validators and keep their
  established bytes.

- [ ] **AC23 — Frozen specs superseded by errata, not edited.**
  `docs/specs/wire-session-start-hook/spec.md` is `Status: Shipped` and pins the
  `claude-plugins/<pack>/.claude/settings.local.json` layout throughout. It
  receives an erratum recording that AC17 supersedes that layout and that its
  subject pack (`core`) no longer publishes to this route at all. The body is not
  edited. Its Approver-signed 2026-08-08 erratum already records both facts, so
  this change verifies rather than duplicates it.

  `docs/specs/claude-plugins-manifest-correctness/spec.md` is also Shipped; its
  deferred AC10 says deriving reserved plugin-root names from `PRIMITIVE_DIRS`
  would over-reserve `hooks/` because hooks were not projected components. This
  change makes `hooks/` a projected plugin-root component, so that header
  receives an Approver-signed erratum naming this spec. The same erratum records
  that AC35 closes its dated statement that dist-branch protection is still an
  unmet merge precondition. Its body and plan remain historical.

  `docs/specs/claude-plugin-route-scope/spec.md` is Shipped and defers
  unrestricted ordinary pushes as an open residual; ADR-0072 is Accepted and
  says branch integrity is an unmet precondition. After AC35 is live, each
  receives an Approver-signed erratum recording the dedicated-app ruleset and
  protected-environment control. Their frozen bodies remain historical.

### Round-4 additions


- [ ] **AC26 — Rail B's consent gesture is part of the qualifying shape.**
  `build/scope_rails.py:check_hooks` refuses a pack declaring `"user"` while
  carrying `.apm/hooks/` or `.apm/hook-wiring/` unless it also sets
  `[pack.install] user-scope-hooks = true`. AC7's fixture and AC18's subject pack
  therefore declare both `allowed-scopes ∋ "user"` and that flag; without it they
  fail `agentbundle validate`. They also declare the current
  `[pack.adapter-contract].version`, and an assertion against the production
  route predicate proves the fixture is classified as user-capable; a fixture
  that omits the consent flag is refused. The flag is the author's explicit "yes, my hooks
  land on the adopter's machine outside per-project isolation" — exactly the
  consent this route needs.

- [ ] **AC28 — The command allowlist cannot be bypassed with a safe-looking
  interpreter.** The exact two-token grammar rejects `python3 -c`, `python -m`,
  `sh -c`, environment assignments, trailing arguments, and every shell
  metacharacter fixture accepted by the real client. A denylist is not an
  alternative: the 2.1.226 strict validator accepted
  `python3 -c "exec('print(1)')"` without any shell operator.

- [ ] **AC29 — The source-path token is exact, not basename-shaped.**
  `vendor/tools/hooks/x.py`, `tools/hooks/../hooks/x.py`, an absolute path, and
  a same-basename file outside the hook-body source directory all raise. A
  symlink under the source directory also raises rather than materializing or
  executing its target.

- [ ] **AC30 — The lint dry-runs the full compiler, on every wiring pack.**
  AC22's shared validators exclude AC10's splice and AC11's completeness and
  confinement checks — and the sibling spec's build-time filter guarantees a repo-only pack
  never reaches the compiler, so `packs/core`'s wiring, the only real wiring in the tree, would be
  the one wiring those checks never run against. The lint therefore dry-runs
  `compile_plugin_hooks` against **every** pack shipping `.apm/hook-wiring/`,
  publishable or not, converting each raise to a finding.

- [ ] **AC31 — Matcher grammar drops the anchors.**
  `^[A-Za-z0-9_-]+(\|[A-Za-z0-9_-]+)*$` — bare literal alternations only.
  `^Bash|Edit$` parses as `(^Bash)|(Edit$)`, which matches `BashTool` and
  `MyEdit` and misses `EditFile`, firing a hook on tools it was not scoped to.
  AC14's widening procedure applies to this grammar too.

- [ ] **AC33 — Marker emission remains unconditional and pack-local.** Every
  published plugin retains the synthetic `SessionStart` install-marker entry,
  first in the merged array. No marker-reader declaration is added and adding or
  removing another published pack cannot change this pack's manifest.

- [ ] **AC34 — Authored-hook disclosure is complete metadata, not a second
  registration.** A pack with authored wiring has its generated marketplace
  description end with a deterministic inventory naming the authored-entry
  count and, for every entry, event, matcher (or `*`), effective timeout,
  interpreter, and plugin-relative body path. The pre-existing synthetic marker
  alone does not change descriptions. Before installation, the real client's
  install surface displays that complete inventory; if it does not, authored
  hooks remain unpublished and the criterion fails. The explicit install
  gesture after that disclosure is the adopter acknowledgement.

  The marketplace entry continues to omit the executable `hooks` key. A
  real-client fixture proves that putting inline hooks in both places is an
  executable append surface, not safe disclosure metadata; an integration
  assertion proves each hook appears only once in the plugin manifest.

- [x] **AC35 — Only the reviewed publisher can update executable plugin
  content.** Before authored hooks can publish, all of the following are true:

  1. An active branch ruleset targets exactly
     `refs/heads/claude-plugins-dist`, restricts updates and deletion, blocks
     force pushes, and has exactly one always-bypass actor: the dedicated,
     repository-scoped publisher GitHub App. No user, team, role, deploy key,
     administrator class, or generic GitHub Actions app bypasses it.
  2. The app has repository Contents read/write and no other write permission.
     Its installation is scoped to this repository.
  3. `.github/workflows/publish-claude-plugins.yml` declares only
     `contents: read` for `GITHUB_TOKEN`, checks out with
     `persist-credentials: false`, references the protected
     `claude-plugin-publish` environment, and mints a repository-scoped,
     short-lived app token only after environment approval. Every external
     `uses:` action in the workflow is pinned to a full commit SHA, not only the
     token-minting action. Only the final publish step receives the token. The
     build and publish stay in one job; any future cross-job artifact handoff
     must verify a producer-recorded digest before the token-bearing push.
  4. The environment accepts `main` only, requires the repository owner's
     approval, stores the app ID/private key as environment-scoped values, and
     does not permit protection-rule bypass. The secrets never appear in a
     command, remote URL, committed artifact, or log; Git authentication is
     supplied to subprocesses through a non-printed environment mapping.
  5. A construction test fails if another workflow references the protected
     environment or its app values, invokes the dist publisher, names
     `claude-plugins-dist` as a push target, or otherwise combines write
     permission with that branch; the publisher
     loses its environment or non-persisted checkout, the token action is not
     commit-pinned, any other external action is not commit-pinned, the token
     reaches an earlier step, or the publisher script prints authentication
     material.
  6. Owner-run rollout evidence records a sanitized ruleset/environment API
     snapshot, an ordinary fast-forward update rejected by the ruleset, and the
     same canary update accepted with the publisher-app token. The sanitized
     evidence is committed at
     `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` and is
     checked against the independently authored desired-state file by the
     pure-stdlib `tools/lint-claude-plugin-publish-control.py`. The canary is
     exercised before the active ruleset is retargeted to the live branch; the
     live branch is never mutated as a negative test. Mutating the evidence's
     bypass actor, exact target, environment branch/reviewer policy, or either
     canary result makes the lint fail.

  The compiler may merge before the settings rollout, because no published pack
  currently ships hooks, but the feature cannot be marked Shipped and a
  hook-bearing user-capable pack cannot publish until all six items pass.
  Until they do, the workflow holds the interim publisher identity required by
  AC36 — merging the compiler early must not strand publication.

- [x] **AC36 — The publisher identity matches the provisioning state.** The
  workflow authenticates with the identity that actually exists, and a
  construction test refuses any other pairing. Concretely:

  1. Provisioning state is read offline from one signal: whether
     `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`
     exists. No test or lint may reach the network to decide it.
  2. **Unprovisioned** (no evidence file) — the workflow publishes with the
     generic Actions app: `contents: write`, no `claude-plugin-publish`
     environment reference, no app-token-minting action, and no reference to
     the app ID or private key. This is an interim state, not the end state.
  3. **Provisioned** (evidence file present) — every AC35 clause-3 and clause-4
     requirement applies unchanged, and the interim shape is forbidden.
  4. The two states are mutually exclusive and jointly exhaustive: the lint and
     the construction test fail when the workflow is in App-token shape without
     evidence, and equally when evidence exists but the workflow still holds the
     interim identity. Neither direction may be satisfied by deleting the check.
  5. Full-SHA pinning of every external `uses:` action, the publication-control
     lint step, and the cross-workflow construction gate of AC35 clause 5 hold
     in **both** states; they are not conditioned on provisioning.
  6. **No internal identifier enters the repository.** The evidence artifact
     records no App ID, installation ID, ruleset ID, account ID, or node ID. The
     three-way identity agreement of AC35 clause 6 is computed against live
     state at capture time and committed as a single asserted boolean. The lint
     walks the artifact and fails on any forbidden identifier key, so a future
     capture change cannot quietly reintroduce one.

  This criterion exists because the App-token step merged ahead of its
  credentials, leaving publication broken on `main` while every gate stayed
  green. A workflow that cannot authenticate is a failure the suite must name.

## Testing Strategy

- **Unit** — the
  compiler's merge, ordering, exact invocation grammar, path confinement,
  publishable-event split, basename validation, and each fail-closed raise;
  per-adapter skip for Kiro and flat-shape wiring.
- **Execution** — AC10's `sh -c` assertion with a space-and-`$` root.
- **Schema** — accepts a compiled multi-event block with and without `matcher`;
  rejects a non-`command` type and unknown keys.
- **Integration** — build the fixture packs; manifest hooks, `hooks/` bodies, absence of `.claude/` and `tools/hooks/`,
  byte-identical warm/cold rebuild, and the AC16 raise.
- **Regression** — a valid non-plugins build still emits
  `.claude/settings.local.json` and `tools/hooks/` byte-identically, including a
  direct-route command outside the publication grammar; a malicious
  Claude-shaped command fails `agentbundle validate` plus a parameterized
  command-level artifact covering all six AC20 consumers that derive the plugin
  recipe before plugin emission (AC20, AC22).
- **Publication control** — offline workflow construction test plus owner-run
  live ruleset/environment snapshots and canary pushes under the ordinary and
  dedicated-app identities (AC35). Mutating the ruleset bypass actor or workflow
  token boundary must turn the corresponding artifact red.
- **Manual QA** — the real client, per AC18.

## Assumptions

- **Claude Code hook events accepted by `claude plugin validate --strict` at
  2.1.226** (driven 2026-08-10), the normative known set for AC14:
  `SessionStart`, `Setup`,
  `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`,
  `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`,
  `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`,
  `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`,
  `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`,
  `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`,
  `Elicitation`, `ElicitationResult`, `SessionEnd`. The snapshot lives at
  `packages/agentbundle/tests/build_pipeline/fixtures/claude-code-2.1.226-hook-events.json`
  so the engine test can bind to it in a checkout and a staged source
  distribution, and a future widening can diff against it.
- `hooks/` at the plugin root is safe for hook *bodies*: Claude Code discovers
  `hooks/hooks.json` by exact name, not by globbing. AC18's exact-set assertion
  is what catches this being wrong.
- Pack-authored `command` strings are untrusted catalogue input. The shipped
  validate/install boundary and the repository lint enforce the same grammar.

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
  traceable to the commit that produced it while `ref` stays mutable. AC35
  controls who may update the ref; it does not make the ref immutable or give an
  adopter an independently verifiable content digest.
