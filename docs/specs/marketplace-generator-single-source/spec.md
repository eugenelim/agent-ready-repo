# Spec: marketplace generator single source

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0072, ADR-0079
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The branch this repository's Claude-plugin marketplace advertises is the branch
the publisher pushes to and the branch the publish ruleset protects — and a gate
fails the moment those stop agreeing. An adopter who runs `claude plugin
marketplace add eugenelim/agent-ready-repo` therefore resolves pack contents from
a protected ref, which ADR-0072 names as a precondition of its own decision, not
an optimisation. A maintainer who runs `make build` and then `make build-check`
gets a green drift check instead of an unsatisfiable `CAT-V-014`.

The branch value is stated more than once by construction — the catalogue schema
requires the key and ADR-0072 pins the constant — so this spec does not claim to
reduce it to one statement. It makes divergence loud. The one duplicate that *can*
be removed without changing behaviour is removed (AC4).

## Boundaries

### Always do

- Treat `build/main.py`'s `_DIST_BRANCH` as the value ADR-0072 pins, and
  `catalogue.toml`'s `claude-plugin-branch` as a restatement the schema requires.
- Anchor the branch to the *protected* ref and to the *published artifact*, not
  merely to the publisher's copy of the name.
- Read every anchor with a parser and fail closed: a source that is missing,
  unparseable, or whose symbol cannot be resolved uniquely is a failure, never a
  skip.
- Take the resolved value from a fresh isolated interpreter and its provenance from
  the finder, never from the running process or from a module attribute. If the
  resolved-value layer cannot prove it read the tree under audit, it fails — it never
  degrades to a skip, because a silent skip is how a layer comes to validate a
  sibling checkout without anyone noticing.
- Keep the Makefile `test` target and `build-check.yml`'s parallel pytest list
  identical, following `tools/test_contract_parity.py`'s precedent.

### Ask first

- Changing the published marketplace `description` an adopter reads.
- Changing which branch is advertised, published to, or protected.
- Changing what an adopter's own `make build-self` emits into their root
  `.claude-plugin/marketplace.json`.

### Never do

- Let `catalogue.toml`'s `claude-plugin-branch` diverge from the branch ADR-0072
  pins without a superseding ADR.
- Advertise a `source.ref` that is not the ref the publish ruleset protects —
  branch integrity is the compensating control ADR-0072 rests on, so an
  unprotected advertised branch voids the decision rather than degrading it.
- Silence `CAT-V-014` by narrowing the drift check's comparison scope.
- Change `derive_projectable_subset`'s public signature, or add a module-level
  import from `build/` into `catalogue_tooling/`.
- Widen the personal data reaching the published manifest. Pack maintainer
  addresses stay role or `@users.noreply.github.com` addresses; this change must
  not introduce a path by which a real address reaches it.

## Testing Strategy

One mode per acceptance criterion. Criteria are numbered explicitly below so every
`ACn` reference resolves mechanically.

- **AC1, AC2 — goal-based check.** A parsed read of `catalogue.toml` compared against
  the other statements of the same value; no behaviour to drive.
- **AC3–AC7 — TDD.** Multi-way equality across the places a single fact is stated, and
  the reader's own contract, are compressible invariants. Written as a compiling red
  stub before the fix, per `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff*.
- **AC8 — TDD, demonstrated red, automated.** Each anchor and each failure mode has a
  probe asserting the check fails. An equality assertion over many sources that has
  never been seen red may be comparing something to itself, and a probe log that ran
  once protects nothing.
- **AC9 — TDD.** The wiring is asserted by the gate itself, not by a grep: the gate
  requires its own path to be in both pytest lists and the lists to match.
  `tools/lint-ci-parity.py` is *not* coverage here — its own docstring says it does
  not catch a gate added inside a step that already carries a disposition.
- **AC10 — goal-based check, demonstrated red.** Exercised end-to-end through the real
  commands, with the pre-fix divergence recorded so the fix is shown to address the
  reported symptom rather than coinciding with its absence.
- **AC11, AC12 — goal-based check.**

## Acceptance Criteria

- [x] **AC1.** `catalogue.toml` `[catalogue.build].claude-plugin-branch` is
      `claude-plugins-dist`.
- [x] **AC2.** `catalogue.toml` `[catalogue.build].marketplace-description` is the text
      published in the committed `.claude-plugin/marketplace.json`, so no
      adopter-visible description changes.
- [x] **AC3.** A parity check asserts the advertised branch is identical across the five
      places the build and publish path read it:
      `.github/claude-plugin-publish-control.json` `branch.target` (less its
      `refs/heads/` prefix), `tools/catalogue/publish_claude_plugins.py`'s
      publish-branch constant, `packages/agentbundle/agentbundle/build/main.py`'s
      `_DIST_BRANCH`, `catalogue.toml`'s `claude-plugin-branch`, and every
      `plugins[].source.ref` in the committed `.claude-plugin/marketplace.json`, every
      entry of which pins `ref` and carries no `sha`. It also pins `branch.target` and
      `repo` to the literals ADR-0072 fixes — `branch` is separately pinned by
      `tools/lint-claude-plugin-publish-control.py:302-312`, but `repo` is pinned by no
      PR-time gate, since `--subject "$GITHUB_REPOSITORY"` is passed only by
      `publish-claude-plugins.yml`.
      (Other in-tree restatements exist — the evidence-capture target, workflow step
      names, test fixtures — and are pinned to `branch.target` by *nothing*. They are
      non-egress, which is why the anchor set is the five that reach an adopter.)
- [x] **AC4.** The check asserts every `plugins[].source.url` is identical and equals
      `https://github.com/<repo>.git`, and every `plugins[].source.path` equals that
      entry's own `name`. Branch protection is scoped to a repository and `path`
      selects which subtree is fetched and executed, so ref parity alone delivers
      none of the property ADR-0072 rests on. This closes the committed manifest; the
      artifact adopters resolve on the dist route is rebuilt from `packs/*/pack.toml`
      at publish time, and a `[pack.links].repository` sweep is caught by **CAT-V-015**
      (`verify.py:1485-1509`, inside required `gate-main`), which reports self-host
      drift and then forces a regeneration this check rejects. That composition is the
      link — CAT-V-015 returns `[]` when `.adapt-discovery.toml` is absent, tracked as
      `output-drift-silent-without-dist`'s sibling condition.
- [x] **AC5.** The marketplace description is stated in **four** places, and the check
      asserts all four agree: `build/main.py`'s `_MARKETPLACE_DESCRIPTION`,
      `catalogue.toml`'s `marketplace-description`, the committed
      `.claude-plugin/marketplace.json`, and `build/self_host.py`'s
      `_aggregate_marketplace` `description` default — which is the one that actually
      writes the committed root marketplace, so an edit there alone would ship a
      description nothing else states. That default must be a string literal (a computed
      default cannot be anchored), and no caller may pass `description=`, which would
      escape the anchor entirely.

      Reducing four to three by having `self_host.py` import the constant is the better
      change and is **deliberately not made here**: `packages/agentbundle/` is a
      protected tree, so `tools/lint-catalogue-curation-guard.py` requires an
      `Engine-Change-RFC:` trailer and `AGENTS.local.md` additionally requires a version
      bump. Turning a config-drift fix into an engine release is the wrong trade.
      Registered as `marketplace-description-fourth-statement-in-self-host`. Anchoring
      catches divergence, not the duplication itself — that limit is the reason the slug
      exists.
- [x] **AC6.** For the two constants in `build/main.py` the check compares the
      **resolved value**, read in a fresh isolated child interpreter
      (`-I --check-hash-based-pycs always`, `sys.path` set explicitly to the tree under
      audit). In-process resolution is not trusted: `sys.modules` is the real authority
      behind an import, any module-scope statement in any module of the same pytest
      command can pre-fill it, and a forged `__file__` then satisfies an
      attribute-based provenance claim. Provenance therefore comes from the finder
      (`importlib.util.find_spec(...).origin`), not from the module, and the check
      additionally refuses a module-scope binding of `__file__` in the audited file.
      Each constant must be of type exactly `str`, not a subclass, and comparisons use
      `str.__eq__`. The publisher's constant is **not** resolved this way — the gate
      will not exec a `tools` script by path — and is covered by AC7 only; that
      residual is `marketplace-publisher-branch-layer-2-only`.
- [x] **AC7.** The check requires each anchored symbol to be bound exactly once, at
      module scope, to a string literal, so the emitted value stays reviewable in a
      diff rather than computed. A module holding an anchored symbol — including
      `self_host.py`'s imported `_MARKETPLACE_DESCRIPTION` — may not rebind it with a
      dynamic construct (`globals()`, `vars()`, `locals()`, `sys.modules[...]`,
      `__dict__[...]`, `setattr(`, `exec(`). Each of these is a hard failure naming its
      source: zero bindings; more than one binding of any kind (`Assign`, `AnnAssign`,
      `AugAssign`, `NamedExpr`, `for` target, `with ... as`, comprehension target,
      `import`/`from ... import ... as`/`import *`, `def`, `class`, `except ... as`,
      `match`/`case` capture, `del`, a `global` statement, a `globals()[...]` write); a
      non-literal value (`BinOp`, `os.environ.get(...)`); an unparseable, unreadable,
      missing, or symlinked file; a `branch.target` without a `refs/heads/` prefix or
      whose remainder is empty or not git-ref-safe; an empty or non-list `plugins`
      array; an entry whose `name` is missing, whose `source.source` is not
      `git-subdir`, or that carries an unexpected key; and a malformed entry missing
      `source`, `ref`, or `url`. An annotated assignment is *accepted*. `resolve` is
      refused for any root but the live tree, since the resolved-value layer reads the
      tree under audit and not a fixture. This layer is supplementary: a gap in it is
      not a bypass, because AC6 compares what is actually resolved.
- [x] **AC8.** An automated mutation suite runs in CI with one probe per anchor and one
      per *behavioural* failure mode AC7 enumerates, each driving the check's single
      `check_envelope_parity(root)` entry point so a probe exercises the real gate
      rather than restating its arithmetic. Each materialises **only the anchor paths**
      into a fixture by content copy — never the live worktree, and never a copy that
      could follow a symlink into it — and asserts the check fails naming the mutated
      source. Because a fixture cannot exercise AC6, the suite additionally injects a
      module into `sys.modules` to prove the exact-type refusal and the provenance
      refusal each fire. A positive control asserts the unmutated fixture passes.
- [x] **AC9.** The parity check is run by a gate: named in the Makefile `test` target
      and in the `build-check.yml` step carrying the parallel pytest list — and the
      check itself asserts both lists name the gate's own file and name the same files
      as each other, since set equality alone holds vacuously if neither names it.
- [x] **AC10.** `rm -rf dist && make build && SKIP_SAST=1 make build-check` exits 0 and
      reports no `CAT-V-014`; and with `catalogue.toml`'s branch reverted to `main` the
      same recipe reports `CAT-V-014` again. Both runs are recorded in `notes/`,
      including the pre-fix `source.ref` divergence between what `make build` writes
      and what the verifier's fresh build produces.
- [x] **AC11.** `make ci` passes.
- [x] **AC12.** `docs/specs/README.md` carries a row for this spec whose Status token
      equals the spec's own `**Status:**`; `docs/product/changelog.md` records the
      corrected advertised branch, naming the audience it serves — forks whose own
      `build-self` reads this `catalogue.toml`; on ship `spec.md` reads `Shipped`,
      `plan.md` reads `Done`, and every criterion is `[x]` or carries a
      `(deferred: <slug>)` marker; and every slug named in `spec.md` or `plan.md`
      resolves to a `workspace.toml [backlog].open` entry following the convention
      there — defect, fix, why deferred rather than bundled, and an `Unblocks when:`
      line.

## Assumptions

- Technical: `claude-plugins-dist` is the correct advertised branch and `main` is
  wrong. ADR-0072 § *Accepted residual — a mutable `ref`* decides that
  `git-subdir` pins `ref` to `claude-plugins-dist` rather than a `sha`, and states
  that branch protection on that branch "is a precondition of this decision, not
  an optimisation". Independently, `origin/claude-plugins-dist` carries the pack
  directories at its top level, matching the emitted `source.path`, while `main`
  carries them under `packs/` — so `ref: main` with `path: architect` resolves to
  nothing. (source: `docs/adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md:125-135`;
  `git ls-tree --name-only origin/claude-plugins-dist` probe 2026-08-17)
- Technical: the mutable-`ref` posture is compensated by branch integrity, not
  manifest integrity — the ruleset and publisher-App identity declared in
  `.github/claude-plugin-publish-control.json` (ADR-0079). **No gate in this
  repository reads GitHub.** `tools/lint-claude-plugin-publish-control.py`
  compares that desired-state file against hardcoded literals (`:302-312`) and
  against a hand-committed capture,
  `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`, whose
  `observed_at` need only be a non-empty string (`:448-450`); the desired file
  itself records `live_branch_negative_tested: false`. So the residual is: the
  ruleset could be removed in repository settings with zero commits and every
  gate, including this one, would stay green. AC3's `branch.target` anchor
  forecloses the cheap variant — a two-file PR that moves the config and the
  publisher constant together — which is what it is for. Confirming the live
  ruleset is a repository-settings read, not a source check, and is registered as
  `publish-control-evidence-freshness-unbounded`. (source:
  `tools/lint-claude-plugin-publish-control.py:302-312,448-450`;
  `.github/claude-plugin-publish-control.json:37`)
- Technical: the branch value must be stated in more than one place. The catalogue
  schema lists `claude-plugin-branch` under `[catalogue.build]`'s `required`, so
  `catalogue.toml` cannot omit it; ADR-0072 pins the constant. Where one home is
  impossible, the repository's established control is a parity gate —
  `tools/test_contract_parity.py` for the `contracts/` ↔ `_data/` twins, and the
  four byte-identical copies of the risk-triggers block. (source:
  `packages/agentbundle/agentbundle/_data/catalogue.schema.json:99,110`;
  `tools/test_contract_parity.py`)
- Technical: `dist/` is gitignored and `build-check` runs `catalogue-verify` before
  `catalogue-build`, so a `dist/` left by a prior `make build-check` already
  agrees with a fresh build and would let AC7 pass vacuously, while a `dist/`
  predating the fix would make it fail for the right reason at the wrong time.
  (source: `.gitignore:79`; `tools/repo/build_gate_chain.py:219-227`)
- Technical: neither layer bounds a rebind that happens *after* import — a function
  that mutates the module global while the build runs. Bounding that needs a
  different instrument (a runtime assertion inside the build, or a semgrep rule over
  the two anchor modules). The dynamic-rebinding refusal above is a tripwire for the
  static case, not a proof. Registered as
  `marketplace-envelope-post-import-rebind-unbounded`. Related and separately
  registered: the publisher's `BRANCH` — the actual `git push origin HEAD:{BRANCH}`
  target — is covered by the literal layer only, because the gate will not exec a
  `tools` script by path to read a constant out of it. The precise residual is that a
  tripwire-escaping rebind there would (a) silently stop the protected ref receiving
  updates while adopters resolve stale pack content, and (b) land a complete built
  pack tree on an arbitrary unprotected branch under the publisher app's repo-wide
  `contents: write`. Registered as `marketplace-publisher-branch-layer-2-only`.
  (source: `publish_claude_plugins.py:235,252,306`; four review rounds
  on the static reader; the resolved-value layer is what closed the enumerable forms)
- Process: unifying where the two values are *resolved* — making `catalogue.toml`
  the authority rather than a gated restatement — is deliberately out of scope,
  on evidence rather than diff-size preference. The full argument is in
  [`plan.md` § Approach](plan.md#approach); the conclusion is that it would miss
  six shipped entrypoints, override an ADR-pinned value from a data file, and
  change what an adopter's own `make build-self` advertises. Registered as
  `marketplace-envelope-config-authority`.
- Process: `_step_output_drift` returning `[]` when `dist/` is absent — which is
  CI's state, and the reason this defect was invisible in CI — is out of scope.
  Changing it alters the required-check contract for every PR. The parity gate is
  the mitigation: it runs under `make ci` and needs no `dist/` on disk, so the
  invariant is gated where the drift check is not. Registered as
  `output-drift-silent-without-dist`. (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:1300-1315`)
- Technical: `.claude-plugin/marketplace.json` on the published branch already
  carries the constant's description text, and `publish-claude-plugins.yml:71`
  publishes a `make build` tree — i.e. the constants path — so correcting
  `catalogue.toml` changes no published byte. (source: `git show
  origin/claude-plugins-dist:marketplace.json` probe 2026-08-17)
- Technical: the deferral of git-ref-shape validation is scoped to the *schemas*,
  not to this value. An earlier draft justified it as "the parity gate closes the
  reachable path here"; that was false — a parity gate checks equality, not shape.
  AC5 now validates the shape of `branch.target`'s remainder directly, and
  `marketplace-ref-not-git-ref-validated` is narrowed to what remains: the
  `marketplace-entry.schema.json` twins declare `ref` *and* `sha` as bare
  `"type": "string"` while `url` and `path` carry patterns, and that schema is an
  **ingress** validator — `catalogue_tooling/archive.py:288-317` validates a
  marketplace extracted from a tarball, and `verify.py:1252` an arbitrary root.
  (source: `archive.py:288-317`; `verify.py:1252`;
  `contracts/marketplace-entry.schema.json`)
