# PLAN record — assumption trio, declined patterns, disposition

## Assumption trio

**Files I will touch**
- `catalogue.toml` (two values under `[catalogue.build]`)
- `packages/agentbundle/agentbundle/build/main.py` (resolution helper; `cmd_build`)
- `packages/agentbundle/agentbundle/build/self_host.py` (`run_self_host`, `_aggregate_marketplace` default)
- `packages/agentbundle/agentbundle/catalogue_tooling/build.py` (drop the duplicate override)
- `packages/agentbundle/agentbundle/build/__init__.py` (`_cmd_build_shim` sets the root)
- Tests: `tests/integration/test_marketplace_entry_validation.py`,
  `tests/integration/test_marketplace_manifest_regression.py`

**What tests demonstrate "done"**
- The emitted `source.ref` equals the publisher's branch constant (new unit test).
- `cmd_build` and `build_catalogue` emit byte-identical `marketplace.json` (new integration test).
- `SKIP_SAST=1 make build-check` exits 0 with `dist/` on disk.
- `git diff --exit-code .claude-plugin/marketplace.json` is empty after `make build-self`.
- `make ci` passes.

**What I am not changing**
- The publish branch itself, `publish-claude-plugins.yml`, or any of the three
  publish tools that pin `claude-plugins-dist`.
- The published `description` text an adopter reads.
- `_step_output_drift`'s dist-absent early return.
- `derive_projectable_subset`'s signature.
- `toml_emit.py`'s adopter-scaffold default of `claude-plugin-branch = "main"`.
- Items C–F of the handoff brief.

## Declined-pattern register

| Tempted to | Declined because |
| --- | --- |
| Make `_step_output_drift` fail when `dist/` is absent, so CI catches this class | Changes the required-check contract for every PR; a deliberate decision of its own, not a ride-along. T3's byte-equality test gates the invariant under `make ci` instead. |
| Replace the module-global monkey-patch with a config object threaded through the build pipeline | Correct but a large refactor of the shipped engine; single-source is achievable without touching `derive_projectable_subset`'s public signature. |
| Add `--marketplace-description` / `--claude-plugin-branch` CLI flags | No second caller needs to differ. `catalogue.toml` is already the config surface. |
| Repoint `make build` at `agentbundle catalogue build --root .` and call it done | Smaller, and it would clear the diagnostic — but it leaves the deprecated shipped entrypoint baking this repo's values into an adopter's marketplace. Recorded as a follow-up in the plan's Risks. |
| Fix `toml_emit.py`'s hardcoded `"main"` scaffold default while in the area | That default is the adopter-scaffold's choice, not this repo's value; a different decision with different evidence. |
| Bundle item F's spec-index Status lint | Explicitly out of scope; the user scoped this session to A and B. |
| Bump `marketplace-description` to something better-written while editing the line | Changes adopter-visible text under cover of a drift fix. Spec's "Ask first" boundary. |

## Resolve-vs-surface disposition record

Opened at PLAN; closed at DECIDE.

| # | Question | Disposition | Basis |
| --- | --- | --- | --- |
| 1 | Is `claude-plugins-dist` or `main` the correct `source.ref`? | **Resolved** | `git ls-tree origin/claude-plugins-dist` shows top-level pack dirs matching the emitted `source.path`; `main` carries them under `packs/`. Three publish tools pin `claude-plugins-dist`. `main` is a dangling fetch. |
| 2 | Which description text wins as the single source? | **Resolved** | The one already committed in `.claude-plugin/marketplace.json` and therefore already published. Choosing the other text would change adopter-visible copy inside a drift fix. |
| 3 | Where does the single resolution site live? | **Resolved** | Inside `cmd_build`, opt-in via an explicit `catalogue_root`. Both real entrypoints pass through `cmd_build`; opt-in keeps existing direct callers on today's behaviour. |
| 4 | Does the fix extend to `self_host.py`'s third copy of the description literal? | **Resolved** | Yes — same concern, same value, removable without a signature change. Leaving it means the root and `dist/` marketplaces can describe the catalogue differently. |
| 5 | Should `make build` move off the deprecated entrypoint? | **Surfaced** (deferred) | Needs a decision about `--packs-dir`, which `agentbundle catalogue build` does not accept. Recorded in the plan's Risks; will be registered in `[backlog].open` at DECIDE if still open. |
| 6 | Should `_step_output_drift` fire in CI? | **Surfaced** (out of scope) | Named in the handoff brief as context. Changing it alters the required-check contract; belongs to its own spec. |

---

# Revision after pre-EXECUTE review (2026-08-17)

The design changed. `adversarial-reviewer` returned 8 blockers and
`security-reviewer` 2; three findings were design-determining and I verified each
myself before acting on it.

## What changed and why

| Finding | Verified how | Effect |
| --- | --- | --- |
| `render_pack_to_dir` / `render_packs_to_dir` call `run_recipe` directly, so `install`, `upgrade`, `render`, `diff`, `init_state`, `validate --strict` reach the marketplace writers without passing through `cmd_build` | Read `render.py:78,125` | The original AC ("no build entrypoint reaches the writers without passing through the one resolution site") was false as designed. Killed the `cmd_build` resolution site. |
| ADR-0072 pins `ref` to `claude-plugins-dist` and states branch protection on it is "a precondition of this decision, not an optimisation" | Read `docs/adr/0072-…:125-135` | A data file must not silently override an ADR-pinned value. Turned `Constrained by: none` into `ADR-0072, ADR-0079` and added a Never-do rail. |
| `toml_emit.py` scaffolds an adopter's `claude-plugin-branch` as `"main"` | Read `toml_emit.py:100` | Making config authoritative would make an adopter's own `build-self` advertise `ref: main` + `path: <pack>`, which does not exist on a tree with packs under `packs/`. An adopter-facing regression inside a drift fix. |
| AC3 anchored the branch to the *publisher's constant*, not the *protected* ref | Read `.github/claude-plugin-publish-control.json` | A two-line PR moving both copies together would keep the check green while moving the distribution to an unprotected branch. Added `branch.target` as a fourth anchor. |
| The byte-equality AC compared `cmd_build(catalogue_root=…)` against `build_catalogue` — the same code through a wrapper — and post-fix both agree whether or not the refactor lands | Reasoned from the plan's own T1 | A control that cannot fail. Respecified through the real argv entrypoints as subprocesses, and added the seven-probe falsifiability requirement. |
| `_aggregate_marketplace`'s `description: str = _MARKETPLACE_DESCRIPTION` would freeze a copy at `def` time | Python default-argument semantics | Moot under the new design; recorded in the plan so the follow-up does not repeat it. |
| `make build-self` returns 2 without writing on a dirty tree, so the `git diff --exit-code` AC was vacuous | Read `self_host.py:1257-1263` | AC dropped — the new design touches no writer, so the root marketplace is unchanged by construction. |
| `build-check` runs `catalogue-verify` before `catalogue-build`, and `dist/` is gitignored | Read `tools/repo/build_gate_chain.py:219-227`, `.gitignore:79` | AC6's recipe now starts with `rm -rf dist`; without it the check passes or fails for reasons unrelated to the change. |
| `Contract: contracts/catalogue` is not a real path and would trip `lint-spec-status`'s dangling-reference invariant | Reviewer citation, accepted | Set to `none`; the new design touches no contract file. |
| Assumption claimed `config.py` imports only stdlib; it imports `agentbundle.build.validate` and `agentbundle.source_defaults` function-locally | Reviewer citation | Assumption deleted — the new design needs no cross-package import at all. |

## Findings I did not accept as stated

- **"`stub: true` declared but no stub materialised."** Correct as a process
  finding. Rather than materialise a stub for a design I was about to discard, T1
  now records `stub: draft (uncompiled)` and writes the check red-first inside the
  task, which is the same discipline without a throwaway artifact.
- **Tighten `ref` to a git-ref-safe pattern in both `marketplace-entry.schema.json`
  twins.** The finding is right; the remedy is a published-contract tightening with
  adopter blast radius, and after T1 the value is pinned to a literal by the parity
  gate. Deferred as `marketplace-ref-not-git-ref-validated` rather than bundled.
- **Add `minLength: 1` to `claude-plugin-branch`.** Same reasoning — deferred as
  `catalogue-branch-empty-falls-back-to-upstream-constant`. Note the fail-open is
  real: `catalogue_tooling/build.py:106`'s truthiness guard leaves an adopter with
  an empty value publishing *our* branch name.

## Revised declined-pattern register

Supersedes the table above where they conflict.

| Tempted to | Declined because |
| --- | --- |
| Make `catalogue.toml` the resolution authority (the handoff brief's suggested direction) | Three verified reasons: it misses six shipped entrypoints, it overrides an ADR-pinned value from a data file, and it changes adopter `build-self` output. Deferred as a scoped follow-up, not abandoned. |
| Fix all six `render.py` entrypoints in this PR | That is the follow-up's whole content, and it needs a decision on `toml_emit.py`'s scaffold default first. |
| Tighten the two shipped schemas while the evidence is fresh | Published-contract change; the parity gate closes the reachable path here. |
| Assert the four-way equality and call it covered | An equality assertion over four sources is the classic control that cannot fail. Seven mutation probes, each observed red, are the actual coverage. |
| Keep the original slug's implied promise ("single source") by claiming the parity gate makes it one source | It does not. The value is stated twice by construction; the gate makes divergence loud. The spec says so plainly rather than overclaiming. |

## Disposition record — closed items

| # | Question | Disposition | Basis |
| --- | --- | --- | --- |
| 1 | `claude-plugins-dist` or `main`? | **Resolved** | ADR-0072 pins it; the branch layout probe confirms `main` is a dangling fetch. |
| 2 | Which description text wins? | **Resolved** | The published one; the other would change adopter-visible copy. |
| 3 | Where does the single resolution site live? | **Withdrawn** | The question presumed a refactor this spec no longer does. |
| 4 | Extend to `self_host.py`'s third copy? | **Resolved — no** | No writer is touched; the description is instead gated three ways. |
| 5 | Should `make build` move off the deprecated entrypoint? | **Deferred** | `make-build-uses-deprecated-entrypoint`. |
| 6 | Should `_step_output_drift` fire in CI? | **Deferred** | `output-drift-silent-without-dist`. The parity gate covers the invariant under `make ci` meanwhile. |
| 7 | Validate `ref` as a git-ref-safe string? | **Deferred** | `marketplace-ref-not-git-ref-validated`. |
| 8 | Hard-fail an empty `claude-plugin-branch`? | **Deferred** | `catalogue-branch-empty-falls-back-to-upstream-constant`. |
| 9 | Lint maintainer emails to role/noreply addresses? | **Deferred** | `marketplace-maintainer-email-unlinted`. Added a Never-do that this change must not widen personal data in the manifest. |
| 10 | Unify the resolution site across all writers? | **Deferred** | `marketplace-envelope-config-authority`. |

---

# Round-2 review dispositions (2026-08-17)

Both reviewers returned "not clean" and both stated their findings were
artifact-level, not polish on the round-1 revision. They converged: three
findings were raised independently by both. Every finding accepted; each verified
before acting.

| Finding (source) | Verified how | Action |
| --- | --- | --- |
| AC3 anchored the branch everywhere except the artifact adopters read — the committed marketplace states it 14× as `plugins[].source.ref`, guarded only by `CAT-V-015`, which returns `[]` when `config is None` or `.adapt-discovery.toml` is absent (both reviewers) | Read `verify.py:1484-1508` | Added as a fifth branch anchor. |
| The description has a **fourth** statement — `_aggregate_marketplace`'s parameter default — and it, not `_MARKETPLACE_DESCRIPTION`, writes the committed root marketplace (both reviewers) | Read `self_host.py:655-657`; confirmed `run_self_host` passes no `description=` at `:1326` and `:1397` | **Deleted** the literal rather than anchoring it — `self_host.py` already imports from `build.main` at `:60`. The gate now asserts the default is an `ast.Name`, so the duplicate cannot return. Reverses disposition #4. |
| The `ast` read was specified for presence but not uniqueness or literalness; a renamed, doubly-assigned, conditionally-defined, or `BinOp`/`os.environ` symbol could read clean (both reviewers) | Reasoned from `ast` semantics; confirmed implicit adjacent-string concatenation *is* folded to one `Constant` but `BinOp` is not | AC5 now requires exactly one module-level `Assign` to a `str` `Constant`, with every other shape a hard failure naming the source. Implemented in the stub's `read_module_str_constant`. |
| The byte-equality AC could not fail: post-T1 the only value-differing mechanism is the monkey-patch, which AC3/AC4 make a no-op by construction (adversarial) | Reasoned from the plan's own T1 | AC dropped. AC7 carries the behavioural weight and is demonstrated-red by reverting the branch. |
| Its two argv citations were wrong: `make build` passes `--packs-dir`/`--output-dir`, and the verifier's fresh build is **in-process** `build_catalogue()`, not an argv path (adversarial) | Read `Makefile:24`, `verify.py:1325-1330`, `build_gate_chain.py:174-189` | Corrected in the plan's Approach; the argv-pair framing is gone. |
| AC5's seven hand-run probes buy falsifiability once, cannot regress-protect, and mutate tracked security-control files in the live worktree — while the repo already has the stronger pattern (security) | Read `tools/test-lint-claude-plugin-publish-control.py`, which drives `lint.main(argv)` over mutated inputs | Replaced with an automated in-CI mutation suite over a temp tree (T2), with per-source readers taking a root path and a positive control. |
| The round-1 `stub: true` waiver expired with the redesign (adversarial) | `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff* | Materialised `tools/test_marketplace_envelope_parity.py` as a compiling red stub. All three tests red for the intended reasons; the branch test fails on the `catalogue.toml` assertion, proving the four prior anchors resolve and agree. |
| The assumption claimed `lint-claude-plugin-publish-control.py` "asserts the desired-state file against the live ruleset" — it does not (security) | Read `:302-312` (hardcoded `expected_branch`) and `:448-450` (`observed_at` need only be non-empty); `.github/claude-plugin-publish-control.json:37` records `live_branch_negative_tested: false` | Assumption restated to say plainly that **no gate here reads GitHub**, and that the ruleset could be removed in settings with zero commits and every gate stay green. Registered as `publish-control-evidence-freshness-unbounded`; surfaced to the maintainer as a settings action. |
| The `ref` deferral's rationale covered egress only; the schema is also an **ingress** validator, and `sha` is equally bare (security) | Read `archive.py:288-317` (validates a marketplace extracted from a tarball) and `verify.py:1252` | Slug restated as an ingress finding with both citations, widened to `sha`. |
| The fork fail-open is worse than recorded: `source.url` derives from `[pack.links].repository`, which in a fork still points upstream, so a fork's users install upstream code from upstream's branch (security) | Read `build/main.py:286-306` | Slug restated. Also folded in `config.py:377`'s third hardcoded `"main"`, where an *absent* key overrides the ADR pin rather than falling back to it. |
| "all four places it is stated" is false — 38 occurrences across 14 files (both reviewers) | `grep -rn claude-plugins-dist` | Reworded to "the five places the build and publish path read", with an assumption naming the publish-control lint as what pins the rest. |
| The empty-value sentinel (`claude-plugin-branch = ""`) is the cheapest option and the only one making "single source" literally true, and was absent from the register (adversarial) | Reasoned from `_data/catalogue.schema.json:99,110` + `build.py:106` | Added as a fifth rejected entry: it makes the design depend on a fail-open registered in the same PR as a bug, and breaks under the `minLength: 1` fix. |
| AC8's `lint-ci-parity` clause is vacuous — its own docstring says it misses a gate added inside an already-dispositioned step (adversarial) | Reviewer citation, accepted | Demoted to a no-regression check; the greps plus a list-identity comparison are the artifact. Registered `makefile-workflow-pytest-list-parity` for the unenforced Boundary. |
| I claimed a personal-data Never-do rail in disposition #9 but never added it (both reviewers) | Read my own spec | Rail added. |
| AC10 had no verification mode; `workspace.toml` was missing from `Touches:`; register entries need the existing comment + `source` + `Unblocks when:` shape; changelog audience unnamed; Objective didn't disclose the residual; deferral rationale stated canonically twice (adversarial) | Read `workspace.toml:491-519` for the convention | All applied. The spec's deferral assumption now holds the conclusion and points at the plan for the argument. |

## Deferrals — eight slugs, registered in T4

`marketplace-envelope-config-authority` · `output-drift-silent-without-dist` ·
`marketplace-ref-not-git-ref-validated` ·
`catalogue-branch-empty-falls-back-to-upstream-constant` ·
`publish-control-evidence-freshness-unbounded` ·
`make-build-uses-deprecated-entrypoint` ·
`marketplace-maintainer-email-unlinted` ·
`makefile-workflow-pytest-list-parity`

Both reviewers independently confirmed the deferral set is separable and that
none is load-bearing for a remaining AC.

---

# Round-4 dispositions and the instrument change (2026-08-17)

Both round-4 reviewers found bypasses in the gate materialised in round 3. Two I
found independently by probing my own reader. All accepted.

| Finding | Verified how | Action |
| --- | --- | --- |
| Import shadow: `from attacker import _DIST_BRANCH` appended to `build/main.py` leaves one *counted* binding, so the gate reads the correct literal while the runtime uses the shadow (both reviewers; I found it too) | Ran my own reader against the fixture — returned `'claude-plugins-dist'` while the resolved value was the shadow | Instrument changed — see below |
| Four more dynamic rebinds beyond the one `globals()[...]` form handled: `globals().update`, `vars()[...]`, `setattr(sys.modules[__name__], ...)`, `exec(...)` (security) | Reviewer probe | Instrument changed; plus a static tripwire refusing these constructs in an anchor module |
| `def`/`class`/`except as`/`case`/`type`/`del` shadows all uncounted (adversarial) | Reviewer probe; I confirmed `del` was missed because its target ctx is `Del`, not `Store` | Added to `_bound_names`; 19 shadow forms now detected |
| `branches` keyed by the marketplace entry's own **non-unique** `name`, so a duplicate-named entry's clean `ref` overwrote an injected hostile one (adversarial) | Reviewer probe, reproduced | Keyed by index |
| `_pytest_group`'s line-walk narrowed its own comparison scope: a symmetric interior non-`tools` line collapsed both sets 10→6, after which a one-sided deletion stayed green (adversarial) | Reviewer probe, reproduced | Replaced the walk with join-continuations + the single logical command |
| The reference source was never in the failure message — mutating `branch.target` named the four *correct* files, and the `repo` message instructed adopting the attacker's url (adversarial) | Reviewer probe | Both messages now carry `PUBLISH_CONTROL:branch.target=… repo=…` |
| `repo` is pinned by no PR-time gate; `--subject "$GITHUB_REPOSITORY"` is passed only by the publish workflow (security) | Read `lint-claude-plugin-publish-control.py:302-312,438-443` | Pinned to a literal in the gate |
| `source.source` unvalidated and extra sibling keys accepted; `CAT-V-013` fails open when `jsonschema` is absent (security) | Read `verify.py:1229-1231` | Assert `git-subdir` and a closed key set |
| Set equality holds vacuously if neither pytest list names the gate — which was the state (both reviewers) | Reviewer probe | Gate asserts its own membership in both groups |
| `is_file()` follows symlinks; `UnicodeDecodeError`/`OSError` escaped unnamed (security) | Reviewer citation | Symlink refusal + wrapped in `ParityError` |
| A call site passing `description=` reintroduces the fourth statement past the default (security) | Reviewer citation | Assert no such call site |
| `plan.md`'s Status hint listed the *spec* vocabulary (adversarial) | Read `CONVENTIONS.md:404-405` | Corrected to `Drafting \| Approved \| Executing \| Done` |
| Ref-shape completeness: component starting `.`, bare `@`, non-tail `.lock`, non-ASCII confusables (both) | Reviewer probe | Added; 24 unsafe shapes now refused |
| `Nonlocal` can only false-positive; `col_offset` default dead; duplicated raises; single-use helper; hardcoded prose in a parameterised message (adversarial nits) | Reviewer citations | Applied |

## The instrument change

Four rounds of a hand-rolled `ast` reader kept surfacing admitted rebinding forms.
That is the signal that **static analysis was the wrong instrument for "what value
does the build emit"**. The authority moved to the resolved value —
`importlib.import_module("agentbundle.build.main")` plus `getattr` — which answers
the question directly and enumerates nothing. `import agentbundle.build.main as m`
would bind the re-exported `main()` *function*, not the submodule; that is the trap
`catalogue_tooling/build.py:68-71` documents, and it is why `import_module` is used.

The literal check is retained as a second layer, because a resolved value alone
would accept `_DIST_BRANCH = os.environ.get(...)` — correct today,
environment-dependent tomorrow. On the live tree a gap in layer 2 is no longer a
bypass, because layer 1 compares what is actually resolved.

**A hazard I introduced and removed myself.** The first draft also loaded the
publisher by path (`spec_from_file_location` + `exec_module`) taking the tree root as
a parameter — so a future probe passing `resolve=True` with a fixture root would have
executed mutated fixture code inside the gate. Removed: layer 1 now imports only the
installed package, which the surrounding suite imports anyway, and `resolve=True` is
refused for any root but the live tree. The publisher is covered by layer 2 only; the
gate will not exec a script by path to read a constant out of it.

## Residual, named rather than patched

Neither layer bounds a rebind that happens *after* import — a function mutating the
global while the build runs. That needs a different instrument (a runtime assertion
inside the build, or a semgrep rule over the two anchor modules). Registered as
`marketplace-envelope-post-import-rebind-unbounded`.

## Empirical verification

All twelve reviewer-demonstrated attacks are now named probes in the file, and all
twelve are blocked. 19 shadow forms detected; 24 unsafe branch shapes refused; the
subscript-load false positive stays absent; `ruff` clean. The fixture in its
post-T1/T3 state is clean, which also validates the exact T1 edit before it is
applied to the real tree.

---

# Round-5 dispositions (2026-08-18)

One verified bypass, composing three defects. All accepted; each verified myself.

| Finding | Verified how | Fix |
| --- | --- | --- |
| `_DYNAMIC_REBIND` enumerated `globals()`/`vars()` but not `locals()`, which at module scope **is** the module dict | Reviewer payload, reproduced | Added `locals()` and `__dict__[`; extended the tripwire over `self_host.py`, which was checked only by `_bound_names` and so could not see subscript writes |
| `resolved_attr` used `isinstance(value, str)`, admitting a `str` subclass whose `__eq__`/`__ne__` lie — and a subclass wins reflected-operand priority, so flipping operands does not help | Measured: `isinstance` True, `type() is str` False, `liar != x` False, `x != liar` False, `str.__eq__` honest | `type(value) is not str` refusal at the boundary, plus a `_differs()` helper comparing via `str.__eq__` |
| **Layer 1 never asserted which file it imported, and on this machine it imported a different worktree.** `resolved_build_main().__file__` resolved to `.../agent-ready-repo/okf-batch/...` — a sibling checkout — because the editable finder points there | Measured directly. Bare `python3` → sibling tree; `PYTHONPATH=packages/agentbundle` (as `Makefile:7` sets) → this tree | `__file__` provenance assertion against `root / BUILD_MAIN` |
| The documented `resolve=True` root refusal existed only in the docstring, not in code | Grepped for it; absent | Implemented as code |
| The publisher residual was mis-stated as merely "layer 2 only" | Read `publish_claude_plugins.py:235,252,306` | Registered as `marketplace-publisher-branch-layer-2-only` with the two-part precision: stale pack content served from the protected ref, and a built pack tree landing on an arbitrary unprotected branch under the app's repo-wide `contents: write` |
| `source.path` admitted by the closed key set but never compared, though it selects which subtree of the protected ref is executed | Confirmed `path == name` for all 14 entries | Pinned to the entry `name` |
| Dead `allow_import` parameter and a comment naming a value it cannot take | Read the three call sites | Removed |

## Why this round mattered most

The third finding invalidated the *verification method*, not just the code: every
resolved-value reading I took while building layer 1 was reading a sibling checkout
and coincidentally matched, so it looked like the mechanism worked. That is the
failure mode where a read-back shares the write's premise and confirms what you
meant rather than what happened. The `__file__` assertion now fails loudly under
exactly the invocation that misled me.

The structural change worth noting: the two load-bearing defences are now
non-enumerable (`type(value) is str`; `__file__` equality), where every previous
round's fix was another arm on an enumeration that kept leaking.

## Empirical state

15 attacks blocked (rounds 3-5), 19/19 shadow forms detected, subscript-load false
positive absent, unrelated `setattr()` correctly accepted, baseline post-T1/T3
fixture clean, `ruff` clean.

---

# Round-6 dispositions and the close of pre-EXECUTE review (2026-08-18)

Round 6 ran both lenses. The adversarial pass found no new bypass — its findings were
spec/plan drift against the code, which is itself the signal that the code had
stabilised. The security pass found one more real bypass, and it was the important one.

## The bypass, and why the round-5 fix did not stop it

`sys.modules` is the real authority behind an in-process import. Any module-scope
statement in *any* module of the same pytest command can pre-fill it — and pytest
imports every collected module before running any test, so a plant collected *after*
the gate still wins. `getattr(module, "__file__")` then reads an attribute the plant
sets, so round 5's provenance assertion passed. Composed with a tripwire-escaping
indirect rebind (`_n = "_DIST" "_BRANCH"; globals()[_n] = ...` — my round-5 narrowing
to lines *naming* the symbol is what admitted it) and the registered publisher
residual, adopters would resolve the protected repository at an unprotected ref.

## Fix: no in-process trust at all

The resolved-value layer now runs in a child interpreter — `-I` (no environment, no
user site, no cwd on `sys.path`), `--check-hash-based-pycs always`, `sys.path` set
explicitly to the tree under audit — and takes provenance from
`importlib.util.find_spec(...).origin`, i.e. from the finder rather than from the
module. A child cannot inherit an in-process plant, and the finder cannot be talked
out of the real path by the file it is locating. The audited file is additionally
refused if it binds `__file__` at module scope.

Measured, each leg independently:

| Attack | Result |
| --- | --- |
| `sys.modules` plant with forged `__file__` | cannot reach the child — isolation holds |
| indirect `globals()[_n]` rebind | detected: resolved value is `tmp-plugins-dist` |
| two-physical-line `globals()` rebind | detected |
| `__file__` forgery + rebind | detected, and separately refused by the `__file__`-binding check |
| `str` subclass with lying `__ne__` | refused at read — the child reports the type name |
| unmutated baseline | passes |

A side effect worth noting: because the child sets its own `sys.path`, the gate no
longer depends on the parent's `PYTHONPATH`. The developer-loop friction round 5
introduced is gone.

## Other round-6 findings, all applied

Publisher covered by the literal layer only, with the two-part residual, and a note
that the deprecation follow-up would move the last write to `config.py:377` +
`catalogue_tooling/build.py:107` — outside every layer (folded into the registered
slugs). `source.url`'s closure composes with **CAT-V-015**, which the reviewer chased
to the end and confirmed holds today; AC4 now says so instead of implying the gate
closes it alone. `_differs` used at the four remaining comparison sites. The
`col_offset` check deleted — its only reachable case is a semicolon-joined statement,
which *is* module scope, so the message would have misdirected. `name` now blamed for
a `name` defect rather than `path`. The `jsonschema` claim corrected: `build/validate.py`
is a deliberate stdlib-only subset validator, so the real fail-opens are the
`except ImportError` and absent-tree early returns at `verify.py:1224-1231`. AC
numbering made explicit (12 numbered criteria; the stub markers pointed at the wrong
ones while the count was implicit). AC9's mode moved to TDD, since its artifact is an
assertion inside the gate and T2's greps were strictly subsumed by it.

## Basis for closing pre-EXECUTE review

Neither round-6 reviewer returned the literal `Clean — ready to commit.`, so this is a
recorded deviation rather than a satisfied condition. The basis:

1. The human explicitly authorised one further round after round 5, and then directed
   the loop to continue to completion.
2. Round 6's single bypass is closed, and each of its six legs was measured
   individually rather than argued.
3. Round 6's adversarial findings — and every remaining security finding — were
   documentation or consistency, all applied.
4. The two load-bearing defences are now non-enumerable *and* out-of-process: exact
   type at the boundary, and finder-supplied provenance in an isolated child. Six
   rounds of enumeration leaks were the argument for moving off in-process trust.

Residuals remain named and registered, not silently absorbed: nine slugs in
`workspace.toml [backlog].open`, of which `marketplace-publisher-branch-layer-2-only`
and `marketplace-envelope-post-import-rebind-unbounded` are the two a future reader
should weigh first.
