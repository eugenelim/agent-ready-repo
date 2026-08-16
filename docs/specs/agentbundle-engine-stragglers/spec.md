# Spec: agentbundle-engine-stragglers

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** `packages/agentbundle` public surface — this spec changes one
  public function signature (`render_packs_to_dir`) and turns on three dormant
  diagnostic codes (CAT-L007/8/9). Both are release-impacting; the PR ships the
  version bump and changelog entry.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Two risk triggers fire: (1) public-interface change —
render_packs_to_dir gains a required parameter, and a shared helper is lifted
across two catalogue_tooling modules; (2) structural — the lifted helper creates a
new shared call site. The G-plan human approval gates are satisfied by the
operator's standing authorization for this run; every other full-mode obligation
(spec, plan, gates, review, doc-drift) is run as written. -->

## Objective

Four `packages/agentbundle` defects recorded in `[backlog].open` share one
property: each is a code path that reads the wrong thing, and none of them has an
in-repo caller loud enough to catch it. They are fixed together because three of
the four are release-impacting under `tools/repo/check_release_impact.py`, so
shipping them separately would mean three version bumps for four small fixes.

Success: each defect's wrong read is corrected, each correction is pinned by a
test that fails against the pre-change code, and one release carries all four.

## Acceptance Criteria

- [x] **AC1 — `render_packs_to_dir` takes its aggregate scope as a parameter.**
  `render.py:104` hard-codes `aggregate_scope="catalogue"`, so an adopter
  rendering a repo-only subset through this public helper gets the catalogue's
  exclusion lines on stderr where the single-pack sibling is silent.

  The parameter is **required and keyword-only**, matching `run_recipe`
  (`build/main.py:602`) whose docstring states the reason explicitly: "A default
  would let `render_packs_to_dir` and `cmd_build --recipe` inherit the wrong
  policy silently." Making it optional here would reintroduce exactly the defect
  the docstring warns about.

  This is a breaking signature change, and it is safe to make: the function has
  no callers anywhere in the tree — a fact the owning spec already records
  (`docs/specs/claude-plugin-route-scope/spec.md:128`, "a function with no callers
  anywhere in the tree, so its parameter is unreachable today"). Verified again in
  this change: `grep -rn "render_packs_to_dir"` returns only its definition, two
  prose mentions, and the backlog entry.

- [x] **AC2 — the signature test covers the new parameter.**
  `test_aggregate_scope_is_required_with_no_default`
  (`tests/unit/test_plugin_scope_filter.py:106`) asserts `run_recipe`,
  `_run_aggregate` and `_run_per_pack` all take `aggregate_scope` as a
  keyword-only parameter with no default. `render_packs_to_dir` joins that tuple.

- [x] **AC3 — `catalogue_tooling` lint reads the real manifest path.**
  `lint.py:1254` and `:1286` probe `<pack>/plugin.json`, but every pack keeps its
  manifest at `<pack>/.claude-plugin/plugin.json`, so CAT-L007 (invalid JSON),
  CAT-L008 (missing `name`/`version`) and CAT-L009 (pack.toml ↔ plugin.json
  parity) have never fired. Both probes read the correct path after this change.

- [x] **AC4 — the path literal exists once, not three times.** `verify.py:130`
  already carries `_plugin_json_path`; `lint.py` must not grow a second copy. The
  helper is lifted to a shared location inside `catalogue_tooling` and imported by
  both modules. After this change `grep -rn '"plugin.json"' catalogue_tooling/`
  shows the manifest filename in exactly one place.

- [x] **AC5 — each turned-on code has a regression test.** One test per code
  (CAT-L007, CAT-L008, CAT-L009) builds a fixture pack whose manifest sits at
  `.claude-plugin/plugin.json` and asserts the diagnostic fires. Each test fails
  against the pre-change probe path — that is what proves the check was dormant.

- [x] **AC6 — turning the checks on leaves the catalogue green.** All 22 packs
  pass CAT-L007/8/9. Measured before implementation (0 findings across 22 packs);
  re-confirmed by `make build-check` after.

- [x] **AC7 — `InitResult` carries `next_steps`.** `SelfHostedInitResult` has
  `next_steps: list[str]` (`initialise_self_hosted.py:173`) and serialises it
  (`:212`); `InitResult` has neither, so an automation consumer reading the JSON
  gets next-step hints from one init verb and not the other. `InitResult` grows
  the field, `init_catalogue()` populates it, and the JSON branch emits it.

- [x] **AC8 — the `list-targets` help string stops lying, and cannot drift
  silently again.** `cli.py:236` names six targets ("claude-code, kiro-ide,
  kiro-cli, kiro (deprecated → kiro-ide), copilot, codex") and omits `cursor` and
  `gemini`. The registry actually holds eight. The help string is corrected to
  match the registry's real names.

  It is **not** generated from the registry at parser-construction time, and that
  is a deliberate departure from the backlog entry's proposed fix. Importing
  `agentbundle.render` costs a measured 429 ms, and `cli.py:1228` `_lazy()`
  documents that command modules are imported lazily precisely so
  `agentbundle --version` and `--help` stay fast. Generating the help eagerly
  would put that 429 ms on every CLI invocation. Drift is prevented by a test
  instead: a unit test asserts the help string names exactly `list_adapters()`.
  Test-time import cost is irrelevant.

- [x] **AC9 — the release-impact gate stops listing a deleted directory.**
  `check_release_impact.py:30` lists `docs/contracts/`, a directory ADR-0055
  deleted, and does not list `contracts/`. The prefix is swapped.

  Not a live hole today — `contracts/adapter.toml` is a byte-identical twin of the
  packaged `_data/adapter.toml`, which is listed, so a real contract change still
  trips the gate through the packaged copy. It becomes a hole the moment a
  `contracts/` file stops having a packaged twin (`catalogue.schema.json`,
  `guide.schema.json` are already in that position).

- [x] **AC10 — the swapped prefix is pinned by a test.** A test asserts that a
  `contracts/`-only changeset carrying no release indicator exits 1, and that the
  same changeset with a release indicator exits 0.

- [x] **AC11 — one release covers all four.** `packages/agentbundle` version is
  bumped once and `docs/product/changelog.md` carries one entry describing the
  four fixes. Gate G (`check_release_impact.py`) passes.

- [x] **AC12 — the backlog entries are dispositioned in this PR.** The four
  entries are removed from `[backlog].open`, except
  `lint-plugin-json-probes-wrong-path`, which **narrows**: its two folded-in
  verify residuals (parity's `if pt_name and pj_name` guard silently passing a
  manifest missing a key; `except Exception: continue` skipping parity with no
  diagnostic of its own) are not fixed here. Both need a new diagnostic code,
  which is a contract change, not a path fix.

## Boundaries

### Always do

- Prove each dormant check was dormant: every AC5 test must fail against the
  pre-change probe path before it passes against the new one.
- Keep the manifest path literal in exactly one place (AC4).

### Never do

- Never give `aggregate_scope` a default value anywhere. The whole point of the
  parameter is that the caller states its policy.
- Never import `agentbundle.render` (or any other heavy module) at `cli.py`
  parser-construction time. See AC8.
- Never add a new diagnostic code in this PR. AC12's residuals need one; they stay
  in the backlog.

## Testing Strategy

- **TDD** for AC3/AC5 (dormant diagnostics), AC8's drift test, and AC10's
  release-gate test: each is a compressible invariant with a clear red state.
- **Goal-based** for AC1/AC2 (signature shape — `inspect.signature` proves it),
  AC6 (`make build-check`), AC11 (Gate G).
- **Manual QA** for AC7 and AC8: run `agentbundle catalogue init --json` and
  `agentbundle list-targets --help` against the built artifact and record the
  observed output. A passing unit test does not prove the CLI prints it.

## Assumptions

- The catalogue is clean under the turned-on checks. Verified before
  implementation: 0 findings across all 22 packs. If a pack were dirty, AC6 would
  turn `make build-check` red and the correct response is to fix the pack, not to
  soften the check.
- `render_packs_to_dir` has no external adopters whose build this breaks. The repo
  cannot prove a negative about downstream users; the version bump and changelog
  entry are the disclosure.
