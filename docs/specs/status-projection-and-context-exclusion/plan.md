# Plan: Status projection and context exclusion

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)
- **Owner:** eugenelim
- **Repository anchors:** `_load_source_authority_parser`
  (`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:1828`)
  and `_source_authority_module_path` (`:1785`) are the analogous production
  implementation for loading a sibling skill module; their tests are
  `tools/test_workspace_status_cli.py::CLIImportPurityTests:1184` and the
  packaged-pair assertions in `tests/roster/test_workspace_status_projection.py:80`
  and `:203`. The directory-confinement analogue is `_specs_root_safe`
  (`workspace_status_engine.py:3408-3416`) with its four-axis comment at
  `:3402-3407`. The packaged-copy construction path is
  `packages/agentbundle/agentbundle/build/self_host.py::_runtime_projections:87`,
  whose real-write branch at `:1436-1439` performs
  `bundled_path.write_bytes(source_path.read_bytes())` — verified. The
  finding-code documentation gate is
  `tests/roster/test_workspace_status_projection.py:486-495`, which requires a
  reason and a next action for every `_FINDING_NEXT_ACTIONS` key in **two**
  files. Named deviations from the precedent: its dev-source branch
  (`:1809-1824`) is unconfined and this implementation confines; and it falls
  through silently on a failed candidate where this one records the escape.

## Approach

Three moves, no new subsystem.

1. **Resolve the cooled set exactly once per ordinary-orientation run.** One
   entry point, `_resolve_cooled_state(root)`, owns **both** stages: resolving
   the cooling module and reading the directory. It returns
   `(frozenset[Path], tuple[RoutingFinding, ...])`, and a module-resolution
   failure is a member of that same findings tuple — which is what makes the
   emitted claim derivable from one list rather than two. The pair is carried on
   `WorkspaceStatusResult` as `cooled` and `cooling_findings`, and passed
   explicitly into `_canonical_projection` so the canonical evaluation and the
   emitter see the same values the scans saw. Nothing recomputes it.
2. **Filter where candidates are chosen, not where files are read.** There is
   no single artifact-body read choke point — bodies are opened at `:1909`,
   `:2121`, `:3170`, and `:3187`. There are four *selection* points, and every
   read is downstream of one of them.
3. **Project what is already computed, and derive the claim from the same
   list.** `project_closeout_status:539` exists, is correct, and has no
   production caller. Unfuse its Wave 4 guard, call it, and emit it beside a
   `cooling` block with `cooling_context_visible` derived from the single
   findings list returned in step 1.

## Design (LLD)

### Two new finding codes, and why not one more

`_FINDING_NEXT_ACTIONS` (`:83`) gains exactly two keys:

| Code | Meaning | Next action |
| --- | --- | --- |
| `invalid_lifecycle_record` | one record failed to load, was a symlink, or was not a regular file | Repair or remove that record; other records still cool. |
| `cooling_state_unavailable` | the cooled set could not be established at all — directory unusable or escaping, or no cooling module resolved | Install `close-work` or repair `docs/lifecycle/`; no artifact is excluded this run. |

**No existing code is reused.** `configuration_mismatch` is load-bearing
elsewhere: `workspace_status.py:682-687` blanks the shaping projections and
empties `type2_cleanup_ops`, `:753-757` drops every
`plan.automatic_operations`, and `workspace_mcp.py:928-932` clears
`legacy_analysis_allowed`. An adopter without the `close-work` skill would lose
their whole shaping queue. AC39 pins that this does not happen.

Both codes need a documented reason and next action in
`packs/core/.apm/skills/workspace-status/SKILL.md` **and**
`guides/core/reference/workspace-toml-schema.md`, or
`tests/roster/test_workspace_status_projection.py:486-495` reds. That is T4
work, and `workspace-toml-schema.md` is a Durable Output for this reason.

### Module loading

`_cooling_module_path()` mirrors `_source_authority_module_path:1785` and
confines every candidate:

| Order | Candidate | Confined by |
| --- | --- | --- |
| 1 | `<skill-root>/close-work/scripts/cooling.py` | `resolve(strict=True)` + `relative_to(skill_root)` |
| 2 | `<engine-dir>/cooling.py` | `resolve(strict=True)` + `relative_to(engine_dir)` |
| 3 | `<checkout>/packs/core/.apm/skills/close-work/scripts/cooling.py`, gated on `AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY == "1"` | `resolve(strict=True)` + `relative_to(parents[4])` — **added; the precedent omits it** |
| 4 | `importlib.import_module("agentbundle._data.cooling")` | import system |

A candidate that fails confinement is skipped without executing its body and the
next candidate is tried (AC40). Only exhaustion of all four yields
`cooling_state_unavailable` (AC38).

**Env-var reuse is deliberate.** Candidate 3 is gated on
`AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY`, the variable the source-authority
parser already uses. A second variable adds operator surface for no separable
decision. The deviation that matters is the confinement check.

**The packaged closure is three files.** `cooling.load_record:733` calls
`_close_work().file_safety()`; `_close_work` (`cooling.py:486-495`) loads
sibling `close_work.py`, which loads sibling `file_safety.py`
(`close_work.py:916-931`). Measured: with `cooling.py` alone a schema-valid
record returns `record-invalid`; with both siblings present it loads. Keeping
`load_record` over the dependency-free `parse_record_bytes` is deliberate — it
keeps `file_safety.read_confined_regular_file`'s `O_NOFOLLOW|O_DIRECTORY` parent
walk (`file_safety:208-233`) in the chain, which is this feature's CWE-73
confinement depth. The engine cannot import that helper directly
(`CLIImportPurityTests:1225`, literal ban `:1243`), so inheriting it through
Wave 5's reader is the only route to that depth.

`close_work.py:26-27` sets `SKILLS_DIR = SCRIPT_DIR.parents[1]`, which under
`_data/` resolves to site-packages. Wave 6's `load_record` chain never reaches
`surface_resolver()` (`:934-944`), but shipping the file exposes it, so AC41
pins that it raises rather than executing outside `_data/`.

### The cooled set

```
_resolve_cooled_state(root) -> tuple[frozenset[Path], tuple[RoutingFinding, ...]]
    # stage 1: _load_cooling_module()  -> module | RuntimeError
    #          on failure, return (frozenset(), (cooling_state_unavailable,))
    # stage 2: _cooled_locators(root, module)
```

Both stages contribute to **one** findings tuple. `_cooled_locators` is not
called directly by any consumer; `_resolve_cooled_state` is the only entry
point, which is why the emitted `cooling_context_visible` can be derived from a
single list without merging a second channel.

Confines `root/"docs"/"lifecycle"` as `_specs_root_safe` confines `docs/specs` —
`resolve()` then `relative_to(root.resolve())`, catching
`(OSError, ValueError, RuntimeError)` — emitting `cooling_state_unavailable`
when it is a non-directory, unenumerable, or escaping. A genuinely absent
directory returns `(frozenset(), [])` with no finding.

Enumerates non-recursively, sorted, `*.json` only, refusing symlinks and
non-regular entries with `invalid_lifecycle_record`. Each survivor goes through
`cooling.load_record`; a non-accepted `CoolingResult` yields one
`invalid_lifecycle_record` carrying the repo-relative path and no record body.

**Cooling pairs.** A record contributes members only when
`(disposition, post_closeout_result)` is one of
`("cool-30-days", "Cooling")`, `("cool-30-days", "Retired")`, or
`("retain-exception", "Retired")`. `("retain-exception", "Retained")` and
`("retain-exception", "ExternalAdvisory")` contribute none — they are still
projected.

**Membership is resolved real paths**, because every read site canonicalizes
(`_safe_spec_path:3069`, `_confined_artifact_path:1723`). Resolution is
non-strict: a locator whose artifact does not exist contributes no member and is
not an error. Identity is `Path.resolve()` equality; hardlink aliases are out of
scope.

### The four selection points

| Site | Line today | Filter |
| --- | --- | --- |
| Type 1 forward walk | `_run_type1_scan:3465` | `continue` **before** `files_read += 1` when `(_current_resolved / "spec.md")` is cooled |
| Type 2/3 declared scan | `_run_type23_scan:3499`, `:3516` | skip after `_safe_spec_path` resolves, before dereference |
| Canonical evaluation | `run_canonical_reconciliation:2829` entry loop | drop the entry before `_metadata_from_root:1895` opens it |
| **Dependency probe** | `_dependency_is_satisfied` (`:2352-2407`) | see below — a narrowly scoped short-circuit placed after the structural guard |

The fourth site is not optional. Dependency targets are reached by a synthetic
`WorkspaceEntry` built from `entry.needs`, not from workspace membership, so an
untracked cooled artifact is read there even though the entry loop never sees
it. **That function builds two such probes** — `:2370-2377` for the
`dep.kind == "defect"` branch and `:2389-2396` for the general branch — so a
check placed at only the second site leaves the first reading cooled bodies.

**The short-circuit is deliberately narrow, and its position is load-bearing.**
A lifecycle record is attacker-writable (see the spec's Assumptions), and a
single record carries up to 17 locators through `aliases`. Placed at the top of
the function it would override the `structurally_blocked_paths` refusal
(`:2358`), the kind-mismatch refusal (`:2364-2366`), the
`defect`-must-be-`backlog.closed` arm (`:2367-2382`), and every
`_dependency_metadata_safety_finding` arm (`:2396-2400`) — turning a suppression
primitive into an affirmative gate bypass. So:

- it runs **after** the `structurally_blocked_paths` check at `:2358`;
- it applies **only** when `dep.type == "local"` and `dep.kind == "spec"`;
- within that scope a cooled dependency is treated as **satisfied**, because a
  lifecycle record is the strongest available evidence the dependency shipped
  and closed out, and returning `missing_dependency` instead would drop the
  *depending* spec out of `canonical.ready` — punishing live work for its
  dependency's completion.

AC14 pins the permissive half; AC55 and AC56 pin the two refusals that survive.

Placing the Type 1 filter before the counter increment is what makes AC16
observable. Dropping the canonical entry before `_metadata_from_root` keeps the
cooled artifact's sibling `plan.md` unopened, since that function resolves and
probes it (`:1943-1958`).

`run_reconciliation:3533` gains `cooled: frozenset[Path] = frozenset()`,
defaulting to empty, so its four call sites in `tools/test_workspace_status.py`
(`:714`, `:820`, `:864`, `:910`) are unaffected.

### `run_canonical_reconciliation`'s five call sites

There are **eight**, not five. Verified by search, 2026-08-30.

| Call site | Root | Cooled set |
| --- | --- | --- |
| `workspace_status.py:456` — `_canonical_projection`, reached by `status`, `reconcile`, `explain` **and `repair-plan`** | yes | mode-dependent, see below |
| `workspace_status.py:1536` — migration rollback | no | empty; cannot resolve |
| `workspace_status.py:1571` — migration rollback | no | empty; cannot resolve |
| `workspace_status.py:1700` — `apply_migration_operation` ledger call | yes | **empty** — Wave 7 deferral |
| `workspace_status_engine.py:3983` — `repair-apply` revalidation | yes | **empty** — Wave 7 deferral |
| `workspace_status_engine.py:4034` — `repair-apply` revalidation | yes | **empty** — Wave 7 deferral |
| `workspace_status_engine.py:4744` — migration planning | yes | **empty** — Wave 7 deferral |
| `packages/agentbundle/agentbundle/workspace_mcp.py:831` | yes | resolved and applied |

`:456` is shared: `_build_repair_plan_json:753` → `_build_json:682` →
`_canonical_projection:451` reaches the same call. So `_canonical_projection`
takes the cooled state as an explicit argument rather than resolving it, and the
caller decides — `status`, `reconcile`, and `explain` pass the resolved pair;
`repair-plan` passes an empty one. `analyze` at `workspace_status.py:2386`
(repair-plan's own scan) likewise receives an empty set. Without that argument
the Wave 7 parity claim is aspirational rather than true, because repair-plan's
canonical block would be silently exclusion-filtered.

### The clock

`analyze`, `analyze_bounded`, and `run_canonical_reconciliation` take
`now: datetime.datetime | None = None`, resolving `None` to
`datetime.datetime.now(datetime.timezone.utc)` at the boundary — an aware
instant, so `is_due` never sees `naive-clock`. AC43 exercises that default path
with no injected instant.

### Output and the mode gate

`_build_json:635` emits `cooling` and `closeout` **only when `mode` is `status`
or `reconcile`**. It is the builder `_build_repair_plan_json:753` delegates to,
so the gate is a positive test on `mode`. `_build_explain_json:739` is
untouched. `project_closeout_status` must be added to `_bind_engine`'s
`globals().update({...})` map (`workspace_status.py:78-129`) or the emit path
cannot reach it.

```
"cooling":  {"due_count": int, "due": [...], "records": [...], "exceptions": [...]}
"closeout": {..., "cooling_context_visible": <derived>}
```

`cooling_context_visible` is `False` **iff the findings tuple returned by
`_resolve_cooled_state` is empty** — the tuple that carries both the
module-resolution failure and the per-record failures, read off
`WorkspaceStatusResult.cooling_findings`. Scoped by construction: it reads that
tuple and nothing else, so an unrelated `configuration_mismatch` from a
locator-only entry cannot flip it (AC34). Fail open on the set — refusing to
project the workspace would cost availability for no gain — and fail closed on
the claim.

### Failure, edge cases, and resilience

- A locator that does not resolve contributes no member and is not an error.
- Two records naming the same real file produce one member and two projected
  records.
- The record is read but the artifact is not, so a cooled artifact that is
  unreadable, absent, or malformed cannot affect the run.
- Record count is deliberately uncapped: `_run_type1_scan:3418-3479` already
  walks all of `docs/specs` uncapped over a larger surface, and
  `docs/lifecycle/` is Git-tracked with `close-work` as its only writer.

## Tasks

### T1: Module loading and the cooled-locator set

**ACs:** AC1–AC12, AC37–AC41.
**Verification mode:** TDD.
**Depends on:** none.

**Tests:** stub: true. The spec holds the canonical statement of each criterion;
the notes below are fixture construction only.

- AC1–AC4 need one record per cooling pair plus the two non-cooling pairs, and
  AC3/AC4 need existing Approved queued specs so `canonical.ready` is meaningful.
- AC9's record must sit under the escaping symlink target, so the criterion
  detects a non-read rather than asserting one.
- AC37 compares three file pairs.
- AC40 needs a candidate whose module body writes a marker, exercised twice —
  outside its root (marker absent) and inside (marker present).
- AC38 needs a real seam, because routes 1 and 4 resolve in every environment
  the roster suite runs in, and routes 2 and 4 point at the same file once AC37
  lands. Load the engine from a temporary skill tree with no `cooling.py`
  sibling, with the env gate unset, and with `agentbundle._data.cooling` both
  absent from `sys.modules` and blocked from import. AC39 reuses this fixture.
- AC41 loads the engine from `_data/` and calls `close_work.surface_resolver()`
  in a layout where a loadable `work-intake/scripts/surface_resolver.py` *is*
  present outside `_data/`, so the criterion proves confinement rather than
  absence.

```python
# tests/roster/test_status_projection_and_context_exclusion.py
"""RFC-0096 Wave 6 — status projection and context exclusion."""

import datetime
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = (
    ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
)
CLOSE_WORK_SCRIPTS = ROOT / "packs/core/.apm/skills/close-work/scripts"
PACKAGED_DATA = ROOT / "packages/agentbundle/agentbundle/_data"
PACKAGED_CLOSURE = ("cooling.py", "close_work.py", "file_safety.py")
SG = "Asia/Singapore"
COOLING_PAIRS = (
    ("cool-30-days", "Cooling"),
    ("cool-30-days", "Retired"),
    ("retain-exception", "Retired"),
)


def _record(*, disposition="cool-30-days", result="Cooling", **overrides) -> dict:
    """A schema-valid delivery-lifecycle-record.v1 payload."""
    raise NotImplementedError  # STUB: shared fixture builder


def _tree(tmp_path, *, records=(), specs=(), queue=(), lifecycle=True):
    """Build a repo fixture; `lifecycle=False` is the control run."""
    raise NotImplementedError  # STUB: shared fixture builder


# STUB: AC1
def test_only_finished_work_cools(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC2
def test_aliases_cool_with_the_locator(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC3
def test_live_obligation_stays_visible(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC4
def test_settled_exception_cools(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC5
def test_invalid_record_cools_nothing_and_is_named(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC6
def test_non_record_file_is_skipped_silently(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC7
def test_absent_directory_is_not_an_error(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC8
def test_unusable_directory_is_named(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC9
def test_lifecycle_directory_is_confined(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC10
def test_symlinked_record_is_refused(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC11
def test_oversized_record_refuses_without_raising(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC12
def test_membership_is_decided_on_the_real_file(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC37
def test_packaged_runtime_carries_the_whole_closure() -> None:
    raise NotImplementedError


# STUB: AC38
def test_every_resolution_route_failing_is_named(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC39
def test_failed_cooling_resolution_costs_nothing_else(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC40
def test_escaping_module_candidate_is_not_executed(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC41
def test_packaged_closure_opens_nothing_outside_itself(tmp_path) -> None:
    raise NotImplementedError
```

**Approach:** add the two finding codes to `_FINDING_NEXT_ACTIONS`, then
`_cooling_module_path`, `_load_cooling_module`, and `_cooled_locators` beside the
source-authority pair. Add the three `_runtime_projections` entries and run
`FORCE=1 make build-self`.

**Mutation proofs (write each with its guard):**
delete the `is_symlink()` refusal → AC10 fails.
delete the directory `relative_to` check → AC9 fails.
drop the cooling-pair predicate → AC3 fails.
store raw strings instead of resolved paths → AC12 fails.
drop candidate 3's `relative_to` → AC40 fails.
reuse `configuration_mismatch` instead of the new code → AC39 fails.
ship only `cooling.py` → AC37 and AC13 fail.

### T2: Context exclusion at the four selection points

**ACs:** AC13–AC22, AC36, AC55–AC56.
**Verification mode:** TDD.
**Depends on:** T1.

**Tests:** stub: true. Every criterion's control is the identical fixture with
`docs/lifecycle/` removed.

- AC13's `alpha` carries `- **Brief:** COOLSENTINEL42` and is declared in a
  queued spec's `needs`; the control run must **contain** the sentinel, which is
  what proves the fixture works.
- AC16 carries uncooled `gamma`; AC18 carries uncooled `beta`. Both are the
  exclude-everything controls for their counter.

```python
# tests/roster/test_status_projection_and_context_exclusion.py (continued)

# STUB: AC13
def test_cooled_body_never_reaches_the_output(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC14
def test_cooled_dependency_does_not_block_its_dependant(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC15
def test_cooled_spec_raises_no_type1_finding(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC16
def test_global_scan_counter_moves_by_exactly_one(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC17
def test_cooled_queue_entry_never_becomes_dispatchable(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC18
def test_declared_spec_counter_moves_by_exactly_one(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC19
def test_uncooled_sibling_still_dispatches(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC20
def test_legacy_entry_is_excluded_identically(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC21
def test_bounded_mode_excludes_identically(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC22
def test_mcp_surface_inherits_the_exclusion(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC36
def test_explain_mode_excludes_too(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC55
def test_cooling_never_satisfies_a_blocked_dependency(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC56
def test_cooling_satisfies_only_local_spec_dependencies(tmp_path) -> None:
    raise NotImplementedError
```

**Approach:** thread the single cooled set into `_run_type1_scan`,
`_run_type23_scan`, `run_canonical_reconciliation`, and
`_dependency_is_satisfied`; give `run_reconciliation` the empty-set default;
pass an empty set at the repair and migration call sites.

**Mutation proofs:** move the Type 1 `continue` below the counter increment →
AC16 fails while AC15 still passes. Filter only `locator` and not `aliases` →
AC2 and an alias-cooled AC17 variant fail. Apply the filter in `analyze` but not
`analyze_bounded` → AC21 and AC22 fail. Omit the dependency-probe site → AC13
fails. Return `missing_dependency` for a cooled dependency instead of satisfied
→ AC14 fails. Make the predicate match every spec → AC16 and AC19 fail. Check
only the second probe site (`:2389`) and not the first → a `defect`-kind AC13
variant fails. Move the short-circuit above the `structurally_blocked_paths`
guard → AC55 fails. Drop the `dep.kind == "spec"` restriction → AC56 fails.
Compare the raw `dep.path` instead of its resolved real path → an
alias-declared AC13 variant fails.

### T3: Projection, the derived claim, and the guard

**ACs:** AC23–AC35, AC42–AC44.
**Verification mode:** TDD.
**Depends on:** T2.

**Tests:** stub: true.

```python
# tests/roster/test_status_projection_and_context_exclusion.py (continued)

# STUB: AC23
def test_due_reviews_are_counted(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC24
def test_due_review_is_named_with_a_closed_key_set(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC25
def test_projected_record_field_set_is_closed(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC26
def test_completion_evidence_is_projected(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC27
def test_exception_carries_owner_role_and_review_date(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC28
def test_finished_work_is_not_a_due_review(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC29
def test_closeout_facts_are_projected(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC30
def test_paused_initiative_changes_the_next_action(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC31
def test_unshipped_spec_becomes_a_blocker(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC32
def test_all_shipped_unpaused_work_invites_closeout(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC33
def test_exclusion_claim_is_earned_not_declared(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC34
def test_unrelated_refusal_does_not_flip_the_claim(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC35
def test_only_ordinary_orientation_carries_the_new_keys(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC42
def test_dueness_is_answered_in_the_recorded_zone(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC43
def test_production_clock_path_works(tmp_path) -> None:
    raise NotImplementedError


# STUB: AC44
def test_non_boolean_visibility_fact_is_still_refused() -> None:
    raise NotImplementedError
```

**Approach:** delete only the `raise ValueError("Wave 4 cannot exclude cooling
context")` at `:552-553`, leaving the `isinstance` check at `:547-551` intact.
Bind `project_closeout_status` in `_bind_engine` and call it from the emit path
with the derived flag. Add the `cooling` block behind the mode gate.
`paused`, `all_specs_shipped`, and `closeout_blockers` are derived from the
`WorkspaceStatusResult` for the single active initiative — `paused` from its
pause overlay entry, `all_specs_shipped` from `work.queue`/`work.active` being
empty, and `closeout_blockers` from the Type 2/3 reconciliation findings. When
more than one initiative is active, the projection is emitted for the first by
slug order and that choice is stated in `SKILL.md`.

**Mutation proofs:** delete the `isinstance` bool check → AC44 fails.
Hard-code `cooling_context_visible` to `False` → AC33 fails. Derive it from all
`canonical.findings` rather than the cooling list → AC34 fails. Return a
hard-coded `due=True` → AC23 fails. Compare `review_on` against the UTC date
instead of the recorded zone → AC42 fails. Resolve `now=None` to a naive
datetime → AC43 fails. Emit `cooling` without the mode gate → AC35 fails.
Project every loaded record into `cooling.due` → AC28 fails.

### T4: Surfaces, documentation, release, and projections

**ACs:** AC45–AC54.
**Verification mode:** goal-based.
**Depends on:** T3.

**Tests:** `no stub (mode)`.

**Done when:** every criterion AC45–AC54 holds as written in `spec.md`. This
task adds no observable the spec does not already state; the digests, version
floor, and string pairs live there and are not repeated here.

Work items:

1. Replace `test_workspace_status_refuses_wave6_context_exclusion` in
   `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`
   with the surviving non-boolean refusal; touch no other function.
2. Add reason and next-action rows for both new codes to
   `packs/core/.apm/skills/workspace-status/SKILL.md`'s table (`:160-190`) and
   `guides/core/reference/workspace-toml-schema.md`'s table (`:322-345`).
3. Amend the architecture boundary sentence and the roster test that pins it.
4. Amend the reference guide and `SKILL.md`'s visibility prose; document the
   `cooling` output section and the multi-initiative rule.
5. Both follow-on slugs are already registered in `workspace.toml
   [backlog].open` (done at drafting, because `lint-spec-status.py` invariant
   (iv) is a hard gate that would otherwise red from the landing commit).
   Verify they are still present.
6. Bump Core to 2.17.0 across `pack.toml`, `plugin.json`, and a topmost dated
   `[core]` changelog heading.
7. Run `env FORCE=1 make build-self`; confirm a second run leaves a clean tree.

Wave 4's `spec.md` is not opened for writing.

## Rollout and risk

The change is additive to the output shape of two subcommands and subtractive to
what four selection points scan. An adopter with no `docs/lifecycle/` records
sees two new keys and byte-identical scan behaviour, because the cooled set is
empty and every filter is a no-op.

Three edits reverse existing behaviour. The guard at `:552-553` is covered from
both sides — AC33 proves the new permission through the emitted surface and
AC44 proves the surviving refusal, so removing the whole validation block fails
AC44. The Wave 4 test is replaced rather than deleted, and AC45 asserts the
replacement exists. The dependency probe changes what a cooled dependency means,
and AC14 pins that a live dependant still dispatches.
