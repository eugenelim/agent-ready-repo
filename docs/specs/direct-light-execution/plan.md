# Plan: direct-light execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

The change is a **doctrine and routing** change carried almost entirely in prose
contracts (skill bodies, architecture, conventions, guides) plus one small
deterministic seam (`intake_router.py`), one guard refactor
(`intake_transaction.py`), and one new executable harness. Nothing new is built:
a route is added to an existing router, an existing mode is redefined to stop
persisting an artifact, and two brief-authoring gates that currently contradict
each other are deduplicated onto one owner.

Order of operations follows authority. Governance first (T1), because the RFC and
the refining ADR are what make the rest legitimate — every later edit cites them.
Then the mechanical seam plus its fail-closed discriminant and the harness (T2),
because the seam's observable `Route` decides what "no artifact, no membership"
means and the doctrine must match it rather than the reverse. Then the runtime
doctrine that consumes the route (T3). Then the brief convergence (T4), which is
independent of T2/T3. Then the documentation and seed surfaces (T5), the release
and eval obligations (T6), and finally projection regeneration plus the whole
gate chain (T7).

The riskiest part is **not** the new behavior — it is the blast radius of prose
edits across files pinned by substring, byte-equality, and **content-hash**
assertions, plus two places where an obvious-looking edit is actively wrong:

1. **The risk-trigger block has one home, not four.** ADR-0088 (Accepted
   2026-08-19) retired the copies in root `AGENTS.md`,
   `packs/core/seeds/AGENTS.md`, and `docs/CONVENTIONS.md`.
   `tools/lint-agents-md.py:517-586` now reports drift for *any* non-`work-loop`
   `.md` carrying the marker, and
   `tools/test_lint_agents_md_risk_block.py::test_noncanonical_homes_fail`
   asserts those three must fail. Reintroducing a copy would redden CI. The
   block's three live homes are the source and its two projections, kept
   byte-identical by editing the source and running `make build-self`.
2. **Three "the *how*" occurrences are correct and must not be swept.**
   `packs/core/.apm/skills/new-spec/assets/plan.md:64` and
   `guides/core/reference/spec-shape-and-lld.md:14` correctly attribute the *how*
   to the **plan**; `guides/_shared/reference/output-rendering.md:83` is
   unrelated. Only `packs/core/.apm/skills/receive-brief/SKILL.md:17` and
   `guides/core/explanation/why-a-brief-layer.md:36` carry the defect.
3. **`work-loop`'s Step 0 and Finish-checklist prose are sha256-pinned.**
   `tools/test_workspace_status.py:1497-1588` hashes two windows of
   `packs/core/.apm/skills/work-loop/SKILL.md` — `^## Step 0\. ORIENT` →
   `^## Step 1\. PLAN` (`_WORK_LOOP_CONTRACT_HASH`) and `^## Finish checklist` →
   the line matching `Conventional commit format` (`_WORK_LOOP_FINISH_HASH`) — and
   the Makefile runs it (line 397). T3 edits Step 0, so this **will** fail
   `make build-check` at `test-workspace-status`, not at any lint one would run
   first. The pin guards a real ownership invariant (AC3g: the finish checklist
   owns only the `spec.md` `Status: Shipped` write; `workspace-status`, never
   `work-loop`, owns `workspace.toml` queue/active/shipped updates), so
   **re-pinning is the last step, not the fix** — check the edit against that
   invariant first, then recompute by replicating the test's own windowing
   (`split(b'\n')`, join the slice, sha256) rather than trusting the truncated
   hash in the failure message.
4. `packs/core/tests/pack/test_work_intake_surface.py:143-213` pins
   routing-matrix case IDs and per-query eval counts; the `receive-brief` tests
   pin exact substrings and ordering in the files being rewritten.
5. Root `docs/CONVENTIONS.md`, `.claude/**`, `.agents/**`, and
   `docs-site/src/content/docs/**` are projections. Editing them directly passes
   locally and fails the drift gate.

### Sizing

RFC-0090's quantity is **changed** reviewable behavior and test lines, not file
size. The surfaces themselves total ~2,091 current lines, which is the wrong
number and is recorded here only so nobody reuses it.

This plan does **not** assert a pre-measured total. Every layer below is a
targeted edit to an existing file plus its tests, not a rewrite, so the expected
order of magnitude is low-thousands at most — but an invented per-layer figure
would be a guess dressed as a measurement, and the one-PR conclusion does not
depend on one. The default is a single dependency-ordered pull request because
the layers are tightly coupled through shared invariants.

**Tail-triage decides, not this prediction.** At finish, measure the real diff's
reviewable behavior and test lines. Below 2,000: ship as one PR. Above 2,000:
declare the shape (**MIXED** — mechanical prose sweeps plus non-uniform seam and
test work) and record the boundaries. The task cuts are drawn so a stack is
available without re-planning: T1 | T2+T3 | T4 | T5+T6+T7.

## Constraints

- Sources only. `.claude/**`, `.agents/**`, root `docs/CONVENTIONS.md`, and
  `docs-site/src/content/docs/**` are regenerated, never hand-edited.
- `packs/core/.apm/skills/work-loop/SKILL.md` is the sole documented home of the
  risk-trigger block (ADR-0088). The trigger *set* does not change; only the
  stale comment inside its opening marker is corrected (AC26).
- `workspace.toml`'s schema, collections, and kinds are untouched.
- The normalized intake envelope keeps its existing `contract_version`.
- No accepted RFC or ADR body is rewritten; refinements are recorded in RFC-0092
  and ADR-0090.
- Frozen historical records (accepted RFC/ADR bodies, Shipped and Archived spec
  directories) are exempt from the AC26 sweep and are not edited.
- Transactionality on the intent, brief, spec, defect, and tracker-refresh routes
  is not weakened.
- No repository-only RFC/ADR/spec/AC identifier appears in adopter-shipped
  content.

## Construction tests

Every task names its tests before implementation. TDD tasks carry a red
assertion first; goal-based tasks carry a `Done when:` one-liner. Repository
commands used as gates:

```bash
pytest packs/core/tests/skills/work-intake packs/core/tests/skills/work-loop -q
pytest packs/core/tests/skills/author-brief packs/core/tests/skills/receive-brief -q
pytest packs/core/tests/pack -q
python3 -m agentbundle catalogue lint --root . --deep
python3 -m agentbundle catalogue verify --root .
FORCE=1 make build-self && rm -rf dist && make build && make build-check
make lint-ruff && make lint-mypy
```

`make build-self` refuses to write while the worktree is dirty (exit 2), which is
the normal mid-implementation state; `FORCE=1` relaxes **only** that check. After
regenerating, `dist/` still holds the pre-edit build, so `make build-check` fails
`CAT-V-014 generated output differs` for every touched source unless the full
chain runs in that order.

## Design (LLD)

### Design decisions

- **The direct route is a `Route` value, not a new module.** `route_intake()`
  gains one branch returning `artifact=""`, `lifecycle_membership="none"`,
  `processor="work-loop"`, `mutation="none"`. Reusing the existing frozen
  dataclass keeps the router a pure function with no new I/O surface and keeps
  the no-transaction property observable from the returned value alone.
- **The direct branch is fail-closed, not merely selected.** A
  `direct_light=True` signal that also carries an artifact or an artifact kind
  implying durable membership raises before returning a `Route` (AC16). The
  invariant is enforced in the router, where it is unit-testable, rather than in
  prose at the call site.
- **Eligibility is a semantic classification the caller performs and declares**,
  passed as a bounded signal (`direct_light: bool`) exactly like the existing
  `named_gaps` and `ready_brief` signals. The router must not re-derive risk; it
  stays deterministic over declared signals. The *authority boundary* (AC8) is
  therefore a `work-intake` and `work-loop` prose contract with eval and
  substring coverage — the router cannot see where a signal came from.
- **Non-persistence is proven in two parts, because one instrument cannot do
  it.** `route_intake()` is a pure function with no filesystem actor; the thing
  that would actually write is an agent following `SKILL.md`, which no test drives
  deterministically. So: (1) T2 adds
  `packs/core/tests/skills/work-intake/test_direct_light_no_writes.py`, which
  builds a `tmp_path` fixture repository with a `workspace.toml` and a `docs/`
  tree, snapshots a recursive path→SHA-256 map, drives the decision seam,
  re-snapshots, asserts equality, and asserts the transaction helper was never
  invoked. Whole-map equality — not three named absences — is what makes an
  unforeseen *code-path* write fail. (2) T7 records one real manual-QA run of the
  shipped skill in a fixture (AC34). Neither is presented as the other; AC31 says
  in terms what the harness cannot establish.
- **Ready-gate ownership is expressed by deletion, not by a new mechanism.**
  `author-brief` loses its Appetite and Rabbit-hole preconditions and its
  "DoR-compliant" claim; `receive-brief`'s step-4 list becomes the single named
  home; the template stops asserting mandatory fields the gate does not require.
- **`lint-spec-status.py` is unchanged.** Direct-light creates no spec, so the
  lint has nothing to inspect. The invariant is enforced by not calling it and
  proven by the harness's empty diff, not by new code.
- **Legacy persisted light specs stay first-class.** `Mode: light` is retained as
  a *readable* marker on already-persisted specs and drops only as a *creation*
  obligation. The light-mode resumption table stays, scoped to "a persisted spec
  that carries the marker", so an adopter mid-flight is unaffected (AC11).

### Interfaces & contracts

`RoutingSignals` gains one optional boolean with a `False` default, so every
existing caller and fixture keeps its current meaning. `Route`'s shape is
unchanged; only the value combination and one rejection path are new.

Representation is fixed once to stop fixtures encoding conflicting meanings: the
router carries `artifact=""` for an absent artifact and
`lifecycle_membership="none"` for absent membership. `none` in user-facing output
is a **rendering** literal produced at the output boundary, not a value the
router stores. The routing-matrix fixture therefore uses `""` for `artifact` and
`"none"` for `lifecycle_membership`.

### Failure, edge cases & resilience

- Direct-light plus a matching canonical ready/active/blocked item → surface the
  conflict, start nothing (AC13).
- Direct-light plus a supplied governing spec → use the spec (AC10).
- Trigger discovered mid-implementation → stop at the boundary, preserve the
  diff, author spec and plan describing the intended final state *and* the
  observed repository reality, run the human gates, re-verify the whole diff; no
  backfilled chronology (AC6).
- Needs another session, a second worktree is touching the same files, or gates
  cannot be repaired in-session → stop, surface, escalate to the durable path
  (AC14).
- Source fails confidentiality or path-independent safety → terminal refusal
  before classification and before any implementation write (AC9).
- A `direct_light` signal carrying an artifact or workspace membership →
  terminal rejection in the router before any write (AC16).

### Quality attributes (NFRs)

Fewer writes to `workspace.toml` reduces cross-worktree contention; the change
must not add any transient light-mode lifecycle write to compensate.

### Dependencies & integration

No new dependency. `governance-extras`' `new-rfc` / `new-adr` author T1's
artifacts; `core` is the changed surface.

## Traceability

| Task | Acceptance criteria covered |
| --- | --- |
| T1 | AC29 |
| T2 | AC9 (intake half, incl. locator confinement), AC15, AC16, AC17, AC18, AC19, AC31, AC30 (direct-path and artifact-bearing cases) |
| T3 | AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC10, AC11, AC12, AC13, AC14, AC30 (argless and embedded-text cases) |
| T4 | AC20, AC21, AC22, AC23, AC24, AC30 (brief and Ready cases) |
| T5 | AC25, AC26, AC27, AC28 |
| T6 | AC32 |
| T7 | AC33, AC34, and re-verification of AC26/AC28 after projection |

Every AC appears at least once; every task carries at least one AC.
`intake_transaction.py`'s refactor is required by AC17 and its fail-closed
counterpart AC16 — it is not an unattributed change.

## Tasks

### T1: Governance — RFC-0092 and refining ADR-0090

**Depends on:** none. **Verification mode:** goal-based. **Covers:** AC29.
**Files:** `docs/rfc/0092-<slug>.md`, `docs/adr/0090-<slug>.md`,
`docs/rfc/README.md`, `docs/adr/README.md`.

Author RFC-0092 at `heavy` weight recording one decision: bounded low-risk work
executes directly from the explicit current request and creates no durable
planning artifact, while durable, queued, resumable, coordinated, or explicitly
spec-driven work keeps spec-and-plan. It carries the reversal analysis —
`docs/rfc/0025-…md:37` explicitly rejected a no-spec mode ("we keep a lean
spec") and `:77` rejected option D — and the compatibility analysis for existing
persisted specs, workspace entries, and adopters.

RFC-0092 also refines RFC-0083's artifact-first clauses — `:33` "only an
existing spec and plan may authorize execution" and `:57` the router "dispatches
only an existing spec and plan" — while preserving its workspace-dispatch rule.

ADR-0090 refines exactly three accepted clauses, editing no accepted body:
ADR-0014's "A lean spec written inline" light mode (`:37-43`); ADR-0076's
"agents may dispatch work only from structured workspace entries that reference
those files" (`:16-18`); and ADR-0078's "**Start or do this:** classify
normalized content, materialize the canonical …" start route (`:66`) together
with its "every captured item must materialize a canonical artifact before it
can become executable" tradeoff (`:22`). It states that ADR-0078's
*dispatchability* rule (`:121-127`) is **preserved** — it already scopes itself
to workspace entries, which direct-light never creates — and that ADR-0088's
single-home rule is untouched.

**Done when:** both files exist with registered index rows and
`pytest packs/core/tests/pack -q` plus the governance lints pass.
**Mutation proof:** delete ADR-0090's refinement of ADR-0078 → the repository
simultaneously asserts "start materializes a canonical artifact" (ADR-0078:66)
and "direct-light materializes nothing" (work-loop), and adversarial review must
reject the contradiction.

### T2: `work-intake` direct route, fail-closed discriminant, and the harness

**Depends on:** T1. **Verification mode:** TDD.
**Covers:** AC9 (intake half), AC15–AC19, AC31, AC30 (two cases).
**Files:** `packs/core/.apm/skills/work-intake/SKILL.md`,
`packs/core/.apm/skills/work-intake/scripts/intake_router.py`,
`packs/core/.apm/skills/work-intake/scripts/intake_transaction.py`,
`packs/core/.apm/skills/work-intake/evals/evals.json`,
`packs/core/.apm/skills/work-intake/evals/eval_queries.json`,
`packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json`,
new `packs/core/.apm/skills/work-intake/evals/files/routing/start-direct-light.json`.
**Tests:** `packs/core/tests/skills/work-intake/test_work_intake.py`,
`packs/core/tests/skills/work-intake/test_intake_transaction.py`,
new `packs/core/tests/skills/work-intake/test_direct_light_no_writes.py`,
`packs/core/tests/pack/test_work_intake_surface.py`.

Red first, in this order: (a) the direct-route `Route` assertion; (b) the
fail-closed rejection for a `direct_light` signal carrying an artifact or
workspace membership, parameterized over intent / brief / spec / defect; (c) the
whole-tree path→digest equality harness. Then implement. Rewrite the SKILL.md
routing table to the six routes, scope "materialize before register" to
artifact-creating routes, state that artifact routes continue to resolve targets
through `resolve_confined_target()` and the direct route has no target to
confine, state that validation and confidentiality refusals are terminal before
classification, replace the "one actor plus one bounded capability always enters
`new-spec`" rule, and make `artifact: none` / `workspace membership: none` legal
output. Update the routing matrix and the eval counts
`test_work_intake_surface.py:143-213` pins.

**Mutation proof:** make the direct branch fall through to
`_START_ROUTES["spec"]` → the router test fails on `processor` and `mutation`,
and the harness fails its "transaction helper never invoked" assertion. (It does
**not** fail on a non-empty diff — neither branch writes; claiming otherwise
would be a proof that cannot fail.) Remove the fail-closed guard → the
artifact-bearing parameterized cases fail. Point the harness's snapshot at a
directory the seam does touch → the digest-map equality fails, proving the
snapshot comparison itself discriminates.

### T3: `work-loop` direct-light doctrine

**Depends on:** T2. **Verification mode:** TDD for asserted text contracts and
evals; goal-based for the lint-not-invoked property.
**Covers:** AC1–AC8, AC10–AC14, AC30 (two cases).
**Files:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/work-loop/references/*` (audit; edit only where light
persistence is cross-referenced),
`packs/core/.apm/skills/work-loop/evals/evals.json`.
**Tests:** `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py`,
`packs/core/tests/skills/work-loop/test_lint_spec_status.py` (confirm no corpus
fixture depends on light-as-persisted semantics),
`packs/core/tests/pack/test_work_intake_surface.py`.

Rewrite the light-mode block as the direct-light procedure with its explicit
do-not list, the pre-write decision record (AC2), and the five-part handoff.
Add the eligibility conjunction and the durability-trigger disjunction as a
decision table, one case per predicate. Add the authority-boundary rule (AC8).
Rewrite Step 0 so the presence of `workspace.toml` no longer forces an explicit
current request to a canonical spec, while argless start, supplied-spec
preflight, and fresh-session resume keep their fail-closed rules; state that a
direct-light run is not resumable through `workspace-status`. Add the two
escalation paths (pre-code, mid-implementation) and the in-session-failure
escalation (AC14). Make every spec-related step conditional on a spec existing.
Keep the light-mode resumption table but scope it to a persisted spec carrying
the `Mode: light` marker (AC11).

Because this task edits Step 0, reconcile the edit against AC3g first (work-loop
writes only `spec.md` status; `workspace-status` owns `workspace.toml` lifecycle
updates), then recompute `_WORK_LOOP_CONTRACT_HASH` — and
`_WORK_LOOP_FINISH_HASH` if the Finish checklist changed — in
`tools/test_workspace_status.py` by replicating that test's own windowing. Re-pin
last.

**Mutation proof:** reinstate "Run `new-spec` to scaffold" in the light-mode
block → the no-spec-creation assertion fails; re-add argless direct dispatch →
the argless-start test fails; delete the authority-boundary rule → the
embedded-text falsification cases fail. Re-pinning the hash without reconciling
AC3g is itself the failure mode the pin exists to catch, so the hash is updated
only after the ownership check is stated in the PR.

### T4: Brief convergence

**Depends on:** T1. Independent of T2 and T3. **Verification mode:** TDD.
**Covers:** AC20–AC24, AC30 (two cases).
**Files:** `packs/core/.apm/skills/author-brief/SKILL.md`,
`packs/core/.apm/skills/receive-brief/SKILL.md`,
`packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/seeds/docs/product/briefs/_template.md`.
**Tests:** `packs/core/tests/skills/author-brief/**`,
`packs/core/tests/skills/receive-brief/test_work_intake_processors.py`,
`packs/core/tests/skills/receive-brief/test_project_knowledge_handoff.py`,
`packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py`.

`author-brief`: drop the "DoR-compliant" claim and the Appetite/Rabbit-hole
preconditions; require a safe source, an identifiable multi-slice outcome or an
explicitly named blocking gap, recorded provenance, and named missing Ready
fields; **retain** the step-1 normalize / redact / confidentiality terminal gate
verbatim in force and say so (AC21); keep Draft-only, no-invention, and
no-brief-for-a-single-direct-light-change.

`receive-brief`: name the six canonical semantic Ready fields once, mark the Spec
map mechanically-present-and-possibly-empty, mark metrics / instrumentation /
stories / design artifacts optional, and fix line 17's "a spec is one feature and
carries the *how*".

`new-spec`: replace line 24's universal "Even a one-day feature benefits from a
one-paragraph spec" trigger with the five warranted-invocation conditions.

Template: add a safe source/provenance section and an Assumptions/Risks section,
mark Success metrics / Instrumentation / User stories / Design artifacts optional,
delete the "At least one entry is required for the DoR gate" claim on Rabbit
holes, and delete explanations `receive-brief` owns.

**Mutation proof:** give `author-brief` a `Status: Ready` write → the
Ready-ownership test fails. Reinstate the template's mandatory-Rabbit-hole
comment → the template/gate agreement test fails. Add an Appetite precondition to
Draft creation → the incomplete-input Draft test fails. Delete the retained
normalization sentence → the AC21 containment test fails.

### T5: Architecture, conventions, seeds, guides

**Depends on:** T3, T4. **Verification mode:** goal-based.
**Covers:** AC25–AC28.

**Sources to edit:**

| File | Edit |
| --- | --- |
| `docs/architecture/work-intake-and-artifact-routing.md` | narrowed invariant at §5.3; three-branch classification flow |
| `packs/core/seeds/docs/CONVENTIONS.md` | replace the lean-inline-spec claim (line ~1248); light/full section wording |
| `AGENTS.md` | concise `work-loop` pointer only; no routing policy; no trigger copy |
| `packs/core/seeds/AGENTS.md` | same, kept deliberately non-identical to root |
| `docs/specs/README.md` and `packs/core/seeds/docs/specs/README.md` | specs are durable delivery contracts, not a prerequisite for direct-light |
| `packs/core/DESIGN.md` | qualify any claim that light always has a spec |
| `packs/core/README.md` | light-mode public description; keep the durable-spec example valid |
| `guides/_shared/explanation/the-three-loops.md` (line 63) | replace "lean inline spec" |
| `guides/core/explanation/token-economy.md` (lines 42, 77, 85) | remove light durable-spec claims |
| `guides/core/explanation/why-a-brief-layer.md` (line 36) | "the spec stays the *how*" → the spec is the behavior contract, the plan the strategy |
| `packs/core/.apm/skills/new-spec/evals/evals.json` | retire the lean-spec eval expectation |
| `packs/core/tests/skills/work-loop/test_lint_spec_status.py` | update any lean-spec fixture expectation |

**Do not edit** (correct as written): `packs/core/.apm/skills/new-spec/assets/plan.md:64`,
`guides/core/reference/spec-shape-and-lld.md:14`,
`guides/_shared/reference/output-rendering.md:83`.

**Projections regenerated, never edited:** root `docs/CONVENTIONS.md`,
`.claude/**`, `.agents/**`, and `docs-site/src/content/docs/guides/**`.

**Correction:** `docs-site/src/content/docs/getting-started/three-loops.md` is
**not** a projection — `tools/build-site.py` aggregates `guides/**` into
`docs-site/src/content/docs/guides/**` only, so `getting-started/**` is a
hand-authored, tracked source and must be edited directly. `make site-sync`
leaves it untouched.

**Done when:** the AC26 sweep returns only frozen records
(`docs/rfc/**`, `docs/adr/**`, Shipped/Archived `docs/specs/**`) and this spec
directory, **and** its positive control still matches.
**Mutation proof:** restore the architecture invariant's original sentence → the
narrowed-invariant assertion fails.

### T6: Release, evals, changelog

**Depends on:** T5. **Verification mode:** goal-based. **Covers:** AC32.
**Files:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`docs/product/changelog.md`, the changed skills' `evals/`.

Bump the core pack from `2.9.5` (minor — adopter-facing behavior change) and set
the plugin manifest to the same value. Add the adopter-facing changelog entry
using no repository-only identifier. Add eval cases and activation near-misses
for every changed public skill.

**Done when:** `python3 -m agentbundle catalogue lint --root . --deep` and
`catalogue verify --root .` pass, and pack and manifest versions are equal.

### T7: Projection, the gate chain, and the recorded run

**Depends on:** T6. **Verification mode:** goal-based, plus manual QA for AC34.
**Covers:** AC33, AC34.

Run `FORCE=1 make build-self && rm -rf dist && make build` after every source
edit is final, then `make site-sync`. Run the full gate chain unfiltered, reading
each exit code directly — never through `tail` or `grep`, which report the
filter's exit code. Re-run the
AC26 and AC28 sweeps against the regenerated projections.

Then perform AC34's recorded manual-QA run: create a throwaway fixture
repository containing a `workspace.toml` and a `docs/` tree, record its
`workspace.toml` SHA-256, drive one real direct-light run of the shipped skill
against a bounded low-risk change in that fixture, and record the post-run
digest plus `find` output for `docs/specs`, `state.json`, and
`engine-state.json`.

**Done when:** `make build-check` exits 0, `make lint-ruff`, `make lint-mypy`,
and the focused suites pass, the terminology sweeps return only frozen records
with passing positive controls, and AC34's evidence is recorded.

## Rollout

Single pull request on `eugenelim/light-spec`. No migration: existing persisted
specs, plans, and workspace entries keep working unchanged — the change removes a
*creation* obligation, not a *reading* capability, and AC11 pins that a
`Mode: light` spec already on disk stays resumable. Adopters who pull the bumped
core pack get the new light-mode behavior on their next `work-loop` invocation;
nothing in their repository needs editing. Rollback is a revert of the single PR
plus `make build-self`.

## Risks

- **Prose-contract blast radius.** Substring and byte-equality assertions pin the
  files being rewritten. Mitigation: each task names its asserting tests; T7 runs
  every gate unfiltered.
- **Sweeping a correct occurrence.** Three "the *how*" lines are right.
  Mitigation: the do-not-edit list in T5.
- **Reintroducing a retired risk-trigger home.** ADR-0088 makes the intuitive
  "keep all four in sync" edit a CI failure. Mitigation: named in Constraints,
  the Never list, and this Approach section.
- **Silently weakening a durability trigger.** Mitigation: AC5's ten refusal
  cases are tested individually, not as a group.
- **Grep-based completion claims.** A pattern that matches nothing reads as a
  clean sweep. Mitigation: every sweep grep carries a positive control.
- **Proving non-persistence with the wrong instrument.** A transaction-level test
  cannot see a route that bypasses the transaction, and a pure-function harness
  cannot see an agent. Mitigation: AC31 states what the harness proves and AC34
  carries the end-to-end property as recorded manual QA.
- **Breaking a content-hash pin without noticing why it exists.** Editing Step 0
  fails `test-workspace-status`, and the tempting fix is to re-pin. Mitigation:
  hazard 3 above requires the AC3g ownership reconciliation before the constant
  moves.

## Changelog

- 2026-08-19 — Initial plan drafted.
- 2026-08-19 — Revised after two independent pre-EXECUTE reviews. Corrected the
  risk-trigger model from four byte-identical homes to ADR-0088's single home
  (the original was factually wrong and would have reddened CI); added ADR-0078
  to the set of clauses ADR-0090 must refine (its start route requires
  materialization, which direct-light reverses); replaced the manual
  fresh-fixture gesture with a committed whole-tree digest harness, because the
  direct route bypasses the transaction the earlier test would have exercised;
  added the fail-closed route discriminant, the authority boundary, the pre-write
  decision record, the legacy `Mode: light` resumption policy, and the
  in-session-failure escalation; replaced the file-size sizing figure with a
  per-hunk changed-line estimate; completed the T5 living-surface inventory and
  added an explicit do-not-edit list.
- 2026-08-19 — Second revision after round-2 reviews, which both reported that
  most surviving defects were fix-induced. Narrowed rather than added: AC31 no
  longer claims the harness proves an end-to-end no-write property (`route_intake`
  is a pure function with no filesystem actor), and the end-to-end property moved
  to AC34 as recorded manual QA; AC16 narrowed to the input combinations the
  router can actually observe, since workspace membership is computed in `Route`
  rather than supplied; the T2 mutation proof's false "harness sees a non-empty
  diff" claim was replaced with a discriminating one. Added: RFC-0083's
  artifact-first clauses to RFC-0092's refinement set; locator-derived path
  confinement to AC9; a canonical representation rule for absent
  artifact/membership. Resolved an internal contradiction where AC1 named an issue
  or PR as *authority* while AC8 called their text data — the invocation may now
  reference them, but their content is context. Replaced the fabricated per-layer
  line estimates with an explicit deferral to tail-triage measurement. Added an
  Accepted limitations section recording the caller-declared-signal residual risk
  (a runtime provenance token was considered and rejected as unimplementable), the
  fact that light mode never had a human approval gate, and the difference between
  evidencing and enforcing the no-write property.
- 2026-08-19 — Added two hazards recovered from a prior session's notes and
  verified against the tree: `tools/test_workspace_status.py:1497-1588`
  sha256-pins `work-loop`'s Step 0 and Finish-checklist prose windows (T3 edits
  Step 0, so `make build-check` fails at `test-workspace-status`; re-pinning is
  the last step, after the AC3g ownership reconciliation), and `make build-self`
  refuses a dirty tree so the regeneration chain is
  `FORCE=1 make build-self && rm -rf dist && make build && make build-check`.
  The round-1 discovery sweep missed the hash pin because it searched only
  `packs/core/tests/**` and not `tools/`.
- 2026-08-20 — Corrected a projection misattribution found during T5. The plan
  listed `docs-site/src/content/docs/getting-started/three-loops.md` as a
  regenerated projection; `tools/build-site.py` maps `guides/**` to
  `docs-site/src/content/docs/guides/**` only, so that page is a hand-authored
  tracked source. `make site-sync` ran clean without touching it, which is what
  exposed the error. The stale lean-spec claim there was edited directly.
