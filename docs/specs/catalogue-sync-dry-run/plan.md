# Plan: catalogue sync — dry-run and check

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/catalogue/upstream-sync.md` is the
  design of record; `state.md` and `derived-catalogue.md` carry current state;
  `docs/specs/self-host-state-schema-3/spec.md` is the phase-1 contract this
  consumes. Analogous production implementations: `commands/catalogue_init.py`
  (a catalogue subcommand's handler, its positional target, and its
  `--format json` branch) and `commands/upgrade.py` (a plan table and its JSON
  `summary`). Their tests: `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`
  and `test_catalogue_init_cli_self_hosted.py`. Construction path: `cli.py`'s
  `cat_subs.add_parser(...)` plus `_lazy("catalogue_sync")`. Named uncertainty:
  `upgrade`'s plan table cannot be called for a path-and-tier row, so this
  reuses its vocabulary and output conventions, not the function.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline — except through § Discovery channel, which bounds a narrower
> post-approval refinement. Execution observations belong in
> `docs/specs/catalogue-sync-dry-run/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, the
> narrative reasons in `Grounding`, and `Risks` are working material, corrected
> in place as the work teaches. A Grounding derivation's **value or oracle** that
> a criterion or verification obligation reads is pinned and changes only through
> the controlled amendment path. A script's **location and invocation arguments**
> are refinable under § Discovery channel, within the bounds that section sets —
> otherwise the pinning rule would cover every row T0's `Tests` reads and the
> channel could never fire.

## Approach

The verb is assembled from code that already ships. Four changes inside
`catalogue_tooling/initialise_self_hosted.py` turn parts of `init`'s pipeline
into callables a read-only caller can drive, and one new command module composes
them. Nothing about the Tier contract, the removal guard, the identity
transform, the leak check, or URI dispatch is written twice.

Two mechanisms are risky enough that they prove themselves inside the task that
introduces them rather than at the end. The removal guard's decline set is
derived from the guard's own AST and compared against the reasons the task
emits, because two hand counts of it disagreed. The no-write invariant is a
whole-tree walk taken before and after, parametrised over every row of the
exit-code table, because a refusal that writes on the way out is what a
success-path test misses.

One surface is projected. The guide T10 edits is mirrored into the docs site, so
T10 regenerates the projection and runs both site gates itself rather than
leaving a later task to discover the drift.

## Grounding

Every measured value this spec and plan rest on, with the command that produces
it. A value is cited from here, never restated. Each probe under
`notes/grounding/` is disposable and re-runnable. The Result column is a dated
illustration only: no criterion, task assertion, or completion check may read
it. Those consumers run the Derivation at verification time.

| Claim | Derivation | Dated illustration at 2026-09-17 — not an oracle |
| --- | --- | --- |
| The terminal-safe check admits every value in the criterion's declared sink class and rejects each hostile variant | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/probe-sink-class.py` — benign/hostile forms for every current value kind, including the rendered source URI and a descriptor's `artifact` URL, plus non-string shapes and the length bound | All current benign forms admitted and hostile forms rejected; non-strings rejected; the bound is exact |
| `safety.classify` over a synthesised `State` returns the Tier contract's verdict for all five path states | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/probe-tier.py` | Five verdicts match; a present `sha256: null` path reaches Tier-2 and an absent one reaches Tier-1 |
| The mypy gate's file set and the synthesised-state package's optionality mode | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/probe-mypy-scope.py tools/lint-mypy.py pyproject.toml` | `tools/lint-mypy.py` passes three typed package directories that exclude `docs/**`, overriding the configured file set; `no_strict_optional` is on for the package that carries the synthesised state |
| The removal guard's decline branches, which emit a reason, and the residual | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/derive-decline-branches.py packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py` | Pre-change baseline: 6 branches, 3 silent; T2's required compound-condition split is expected to raise the branch count, and an unchanged post-change count is a failure |
| Whose digest each digest-bearing form verifies | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/probe-digest-provenance.py` | `archive+https://` refuses pre-fetch without its fragment, so the digest is adopter-supplied; `catalogue+https://` reads `descriptor["sha256"]` from the same origin |
| The catalogue subcommand roster and its nested residual | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/derive-subcommands.py` | Pre-change baseline: 9 direct children; T5 is expected to add one; `contracts` carries 3 nested verbs; zero residual |
| The citation set this change must re-pin | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/derive-citations.py` | see the script's output; it reports a residual set it cannot resolve, which § Follow-ons owns |
| Which representation each site gate reads | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/derive-site-gates.py` | the entry-link gate reads authored `guides/**` by design and runs on every pull request; the rendered-links checker reads the generated tree and raises on an unsafe one |
| The release surfaces a version bump touches | `python3 docs/specs/catalogue-sync-dry-run/notes/grounding/derive-release-surfaces.py packages/AGENTS.md docs/guides/explanation/release-coupling.md` | The set is derived from the version-bump rule and release-coupling definition, independently of current version occurrences; unclassified candidate surfaces are reported as a residual |

`notes/grounding/` is authored by T0 and is part of this change. A claim whose
derivation is absent is not a grounded claim.

## Discovery channel

A task section locks when execution begins, and a completed section is
immutable. For an **unstarted** task, T0 may refine only the mechanics of a
Grounding script: where it lives and the arguments used to invoke it. Fixture
shapes, helper choices, criterion values, and comparison oracles are outside
this channel.

- **Discovery predicate.** T0 resolves only the location and invocation
  mechanics of scripts under `notes/grounding/`. A change to any value or
  oracle a criterion reads is a controlled amendment, even when a script emits
  it.
- **Kill condition.** If the terminal-safe check rejects any member of the full
  class spec AC-0012 declares, T0 stops. The probe covers every current member
  of that class, but its current enumeration does not narrow the criterion.
- **Bounded alternative.** If the kill condition fires, T0 may add a
  rendering-time escaper. Narrowing spec AC-0012's sink class is a controlled
  amendment, not a discovery refinement.
- **Refinable tasks.** T0 only, and only while it is unstarted.
- **Decision record.** Append-only, in `notes/grounding/decisions.md`. One entry
  per refinement: date, predicate resolved, task refined, and the derivation.
- **Scoped review.** A refinement re-reviews the changed task and its declared
  dependants, not the whole plan.
- **History.** Amendment history and completed-task evidence are preserved; a
  refinement appends and never rewrites.

Any change outside those bounds — an acceptance criterion, a task outcome, a
dependency edge, a verification obligation, or a started task — uses the
controlled amendment path.

## Construction tests

**Integration test:** one, the spec's load-bearing check. A whole-tree walk
helper — non-dereferencing, recording relative path, entry kind, mode, symlink
target, and bytes for regular files only — taken before and after a `sync`
invocation and compared. Its domain is spec AC-0015's: **every row of AC-0013's
table**, not "this task's paths". T4 introduces the first return paths and adds
them; every later task adds its own rows to the same parametrisation.

**Manual verification:** the real CLI against a derived catalogue built by
`catalogue init --preset self-hosted` in a temporary directory —
`sync --dry-run`, `--dry-run --format json`, `--check`, and
`--check --compare-tree` — with observed stdout, stderr and exit code recorded
in the ledger. Not exercised in that pass, and stated so it is not mistaken for
coverage: a digest-bearing source, a leak violation, an underivable state, and a
compatibility fixture, each of which a TDD case owns.

**Stub tally:** eleven tasks. Covered 8 — T2, T3, T4, T5, T6, T7, T8, T9.
Uncovered 0. `no stub (goal-based)` 3 — T0, T1, T10, none of which declares a
TDD outcome. The eight covered tasks carry nine stubs because T6 carries two:
the Tier verdict and the count identity. Every stub
was compiled and **run** against the T1 fixture set in disposable scratch, and
the failure recorded per task is the one observed. Six share one red, because
until the command module exists that is the failure; a separate invented red per
stub would be fiction.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `upstream-sync.md` | T10 | § Rollout phase 2 struck; § Stage 3 re-pinned; § Granularity's vacated name | spec AC-0022, AC-0023, AC-0024 |
| `derived-catalogue.md` | T10 | Citations re-pinned; recipe bullet rewritten | spec AC-0022, AC-0025 |
| `agentbundle.md` § 2 | T10 | Entrypoint list equals the derived roster | spec AC-0021 |
| `atomic-write-symlink-harden` spec + plan | T10 | Both citations re-pinned after T4's move | spec AC-0022 |
| The self-hosted how-to guide | T10 | The new section, plus the regenerated site projection and both gates run | spec AC-0026 |
| `README-pypi.md` | T10 | "What's new in" naming the version | roster suite dispatched, result in the ledger |
| Both changelogs | T10 | Topmost entry, adopter-first | spec AC-0027 |
| `packages/AGENTS.local.md` | T0 | The criterion-ordinal exemption and which source yields | spec AC-0028, AC-0029 |

## Design (LLD)

### Design decisions

**One new module.** `commands/catalogue_sync.py` is required by the CLI's
dispatch convention — `_lazy("<module stem>")` makes the module name the wiring
— which is rung 4 of the ladder, a native platform capability. Rungs 1–3 were
walked: there is no verb without a handler; the bounded search returned
`commands/catalogue_init.py`, rejected because `init` and `sync` have different
write contracts; and the standard library has no opinion about dispatch tables.
Everything else stays in `initialise_self_hosted.py`, which already owns it.

**The Tier classifier is reused by synthesising its input.** `safety.classify`
takes the *install* state, a different file that per `state.md` does not read the
derivation state. `sync` builds a one-row `State` from `managed_paths` and calls
the shipped function. A null-sha entry is recorded with the `"sha"` key omitted
rather than present-and-`None` — not because a gate rejects the latter, which
§ Grounding shows it does not, but because `dict[str, str]` carrying `None` is a
type lie that survives only through `no_strict_optional` and an `Any` hole.

**The mode fields are never read.** `collect_fields` takes all three from `cfg`,
and `_SelfHostRecipeInput` has no such attribute, so a recorded mode cannot
reach the replay. This phase keeps that shape: spec AC-0007 reports what the run
resolved from flags, so no call site holds a recorded mode string.

**The exit-code table is the single home.** Spec AC-0013 is the only place a
code is bound to a condition; every other criterion cites it. Rows are read
top to bottom and the first match wins, which makes the table disjoint by
construction rather than by cross-checking its antecedents pairwise. Disjointness
is all first-match-wins buys: totality is a separate obligation, and spec AC-0014
is what carries it.

**Confinement goes through the declared helpers.** Every read and hash under the
target uses `catalogue_tooling.file_safety`, replacing the guard's inline
resolve-then-`relative_to` followed by a separate `exists()` and `read_bytes()`
— two resolutions where the helper does one canonicalise-then-verify and rejects
reparse points.

### Interfaces & contracts

```
agentbundle catalogue sync [TARGET]
    --source <uri>
    [--attribution white-label|attributed] [--tooling external|vendored]
    [--guides-mode none|selected] [--format table|json]
    ( --dry-run | --check [--compare-tree] )
```

`TARGET` is positional, `nargs="?"`, `default="."`, mirroring `init`; it is the
tree every count and verdict is measured against. `--source` is required.
`--guides-mode` carries the guides replay mode under a name phase 3's
restrictor will not want. Spec AC-0013 owns the codes; the only mechanism note
is that code 2 follows `catalogue_init.py`'s usage-error convention.

### Component decomposition

| Callable | Change | Used by |
| --- | --- | --- |
| `_plan_stale_owned_paths` | the decision half of `_remove_stale_owned_paths`, plus a reason on each silent branch | `_remove_stale_owned_paths`, `sync` |
| `collect_fields(..., interactive=)` | one keyword | `init` (True), `sync` (False) |
| `replay_derivation` | steps 1–9 of `init_self_hosted`, lifted | `init_self_hosted`, `sync` |
| the confined read/hash seam | `file_safety` helpers replacing the inline guard | both |

### Failure, edge cases & resilience

The four trust boundaries the design of record names map to existing controls;
this plan cites `upstream-sync.md` § Trust boundaries rather than restating
them. The one this phase closes by construction rather than by reuse is
self-replacement, because nothing is written.

### Dependencies & integration

Standard library only: `argparse`, `dataclasses`, `hashlib`, `json`, `re`,
`shutil`, `stat`, `sys`, `pathlib`.

## Tasks

### T0: the grounding derivations exist and the marker conflict is resolved at its owner

**Depends on:** none

**Touches:** `docs/specs/catalogue-sync-dry-run/notes/grounding/`, `packages/AGENTS.local.md`

**Tests:** `no stub (goal-based)` — this task emits derivations, not behaviour.
- Every row of § Grounding names a script under `notes/grounding/` that exists
  and exits 0.
- `packages/AGENTS.local.md` carries the criterion-ordinal exemption, and every
  criterion-ordinal label under `packages/agentbundle/tests/` is bare, carrying
  no path or section reference (spec AC-0028, AC-0029).

**Approach:**
- Materialise the probes and generators § Grounding declares so each command
  resolves from the repository root.
- Open `notes/grounding/decisions.md` as the discovery channel's append-only
  record.

**Done when:** every § Grounding command runs from the repository root and exits
0, spec AC-0028 and AC-0029 pass, `make lint-ruff` passes, and
`python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
reports clean metadata.

### T1: the shared fixture set exists

**Depends on:** T0 — the fixtures consume the source forms and path states the
Grounding derivations establish.

**Touches:** `packages/agentbundle/tests/unit/conftest.py`

**Tests:** `no stub (goal-based)` — a fixture set has no behaviour of its own.
- `self_hosted_source`, `upstream`, `derived_tree` and
  `upstream_with_bumped_pack` resolve, and a throwaway test that requests all
  four runs to a real assertion rather than a setup error.

**Approach:**
- Materialise the fixture set validated in scratch: a minimal source catalogue
  with one pack, a derived tree carrying a schema-3 state with a recipe and a
  null-digest pin, and a source whose pack version has moved past the derived
  tree's copy.

**Done when:** all four fixtures resolve and the throwaway consumer named in
this task's `Tests:` reaches its real assertion without a setup error.

### T2: the removal guard is one implementation, a dry run can ask it, and every decline names a reason

**Depends on:** T0 — the decline-branch derivation must exist before this task
changes the guard it reads.

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`, `docs/specs/catalogue-sync-dry-run/notes/grounding/derive-decline-branches.py`, `tests/roster/test_catalogue_sync_decline_branch_alignment.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `.workspace-prune-protected.toml`

**Tests:**
- `test_plan_stale_owned_paths_names_every_decline` — stub below, `stub: true`,
  spec AC-0017. Compiled: yes. **Red observed:** `AttributeError: module
  'agentbundle.catalogue_tooling.initialise_self_hosted' has no attribute
  '_plan_stale_owned_paths'`.
- One independently pinned fixture per decline branch in the post-change guard,
  each asserting its reason token, plus pairwise token distinctness and equality
  between the fixture count and the post-change § Grounding derivation. Deleting
  a branch fails its fixture even when the derived count also shrinks. **This is
  the inline proof for a risky mechanism:** the derivation checks completeness;
  the independent fixtures make branch loss able to fail.
- Each reason classified decided or undecided, and the undecided set is what
  spec AC-0013's "could not be compared" reads (spec AC-0017).
- Hard-linked, non-regular, and reparse-point recorded paths are refused by the
  applicable declared confinement helper before comparison (spec AC-0020).
- The existing removal cases are green with no assertion edited.

```python
# STUB: AC-0017
import hashlib

from agentbundle.catalogue_tooling import initialise_self_hosted as ish


def test_plan_stale_owned_paths_names_every_decline(tmp_path):
    doomed = tmp_path / "packs" / "gone.md"
    doomed.parent.mkdir(parents=True)
    doomed.write_bytes(b"upstream\n")
    (tmp_path / "packs" / "nosha.md").write_bytes(b"n\n")
    old_state = {
        "managed_paths": [
            {"path": "packs/gone.md",
             "sha256": hashlib.sha256(b"upstream\n").hexdigest()},
            {"path": "", "sha256": "x" * 64},
            {"path": "packs/absent.md", "sha256": "y" * 64},
            {"path": "packs/nosha.md", "sha256": None},
        ]
    }

    removable, reasons = ish._plan_stale_owned_paths(tmp_path, old_state, set())

    assert removable == ["packs/gone.md"]
    assert len({r.split(": ", 1)[1] for r in reasons}) == len(reasons)
    assert doomed.exists()
```

**Approach:**
- Split the per-entry loop into `_plan_stale_owned_paths(target, old_state,
  current_paths)` returning removable paths and reasons. Preserve branch order.
- Add a reason to each branch the derivation reports as silent, and separate the
  compound condition so a malformed entry is distinguishable from a not-stale
  path.
- Route the read and hash through the declared `file_safety` helpers.
- Reduce `_remove_stale_owned_paths` to calling the planner and unlinking.

**Done when:** this task's assertions are green and
`python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py -q` passes.

### T3: `collect_fields` resolves defaults on a TTY without prompting

**Depends on:** T1 — the stub drives a schema-3 state through the fixture set.

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`

**Tests:**
- `test_collect_fields_replays_flag_modes_not_recorded_ones` — stub below,
  `stub: true`, spec AC-0003. Compiled: yes. **Red observed:** `TypeError:
  collect_fields() got an unexpected keyword argument 'interactive'`. The state
  carries all three contrary recorded modes, so the assertions remain
  discriminating after the keyword exists.
- Phase 1's TTY case green unchanged through the default argument.
- `_prompt` patched to raise, asserting it is never reached under
  `interactive=False`. A call count of zero is also what an unexercised path
  reports, so the raise is the observation.

```python
# STUB: AC-0003
import json

from agentbundle.catalogue_tooling import initialise_self_hosted as ish


def test_collect_fields_replays_flag_modes_not_recorded_ones(
    derived_tree, self_hosted_source, monkeypatch
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["recipe"].update(
        attribution="attributed", tooling="vendored", guides="none"
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")

    diagnostics = []
    raw_state = ish._load_ownership_state(derived_tree, diagnostics)
    recipe = ish._load_self_host_recipe(raw_state, self_hosted_source, diagnostics)
    cfg = ish.SelfHostedInitConfig(
        target=derived_tree, source=self_hosted_source
    )
    monkeypatch.setattr(
        ish,
        "_prompt",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("prompted")),
    )

    resolved = ish.collect_fields(cfg, {"catalogue": {}}, recipe, interactive=False)

    assert resolved.attribution == "white-label"
    assert resolved.tooling == "external"
    assert resolved.guides == "selected"
```

**Approach:**
- Add `interactive: bool = True`, routing every `_prompt` through one local
  helper that returns the default when False. The non-TTY path already resolves
  to defaults, so this closes the TTY path only — which is the adopter-facing
  one.

**Done when:** this task's assertions are green and the phase-1 suite passes
with no assertion edited.

### T4: the derivation replay is one implementation, callable without writing

**Depends on:** T3 — `replay_derivation` calls `collect_fields` with
`interactive=False`.

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`

**Review shape:** MIXED — the extraction is mechanical but the seam is a
judgement call, so it lands as its own layer and leaves the repository working.

**Tests:**
- `test_replay_derivation_writes_nothing_to_target` — stub below, `stub: true`,
  spec AC-0015. Compiled: yes. **Red observed:** `AttributeError: module
  'agentbundle.catalogue_tooling.initialise_self_hosted' has no attribute
  'replay_derivation'`.
- `test_catalogue_tooling_self_hosted_init.py` and
  `test_catalogue_init_cli_self_hosted.py` green before and after with no
  assertion edited — the primary evidence, since the extraction has no
  observable behaviour of its own.
- A leaking source yields the violation list under `white-label` and an
  unrecognised attribution value, driven against the callable (spec AC-0004,
  AC-0005).
- One state file through both readers, admitted values and diagnostics compared
  for equality (spec AC-0006).
- The whole-tree walk from § Construction tests is written here and parametrised
  over T4's return rows of spec AC-0013's table (spec AC-0015).

```python
# STUB: AC-0015
from agentbundle.catalogue_tooling import initialise_self_hosted as ish


def test_replay_derivation_writes_nothing_to_target(tmp_path, self_hosted_source):
    target = tmp_path / "derived-new"
    cfg = ish.SelfHostedInitConfig(target=target, source=self_hosted_source)

    result = ish.replay_derivation(cfg)

    assert result.file_bytes
    assert not target.exists()
```

**Approach:**
- Lift steps 1–9 into `replay_derivation(cfg)`, returning the planned byte map,
  file kinds, anchors, resolved config, selections, diagnostics, identity
  replacements and violations.
- Leave `init_self_hosted` as its caller plus steps 10–14. Do not touch the
  `CONFLICT` abort or the unconditional overwrite; they are phase 3's.

**Done when:** both named suites pass with no assertion edited and this task's
cases are green.

### T5: the verb exists, binds its target, and names the fidelity token

**Depends on:** T4 — the command module calls `replay_derivation`.

**Touches:** `packages/agentbundle/agentbundle/commands/catalogue_sync.py`, `packages/agentbundle/agentbundle/cli.py`, `packages/agentbundle/tests/unit/test_catalogue_sync.py`

**Tests:**
- `test_sync_names_fidelity_token_per_source_form` — stub below, `stub: true`,
  spec AC-0001. Compiled: yes. **Red observed:** `ImportError: cannot import
  name 'catalogue_sync' from 'agentbundle.commands'`.
- Parametrised over the four source forms for the token and both pin values,
  patching `fetch_catalogue_archive_with_provenance` and `resolve_catalogue`.
- Both attribution modes over all three channels (spec AC-0002).
- Resolution and verification refusals over all three channels, with the source
  URI absent under every non-`attributed` mode (spec AC-0002).
- An explicit target and an omitted one resolving to the current directory.
- The extracted directory is gone on the succeeding and each refusing path.
- T5's rows added to the tree-walk parametrisation.

```python
# STUB: AC-0001
from agentbundle.cli import _build_parser


def test_sync_names_fidelity_token_per_source_form(derived_tree, upstream, capsys):
    # The real parser, never a hand-rolled Namespace: a hand-rolled one carries
    # no parser defaults, so a missing default reads as a passing test.
    from agentbundle.commands import catalogue_sync

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert "local-path" in capsys.readouterr().out
```

**Approach:**
- Register the subcommand beside `init` with a positional target mirroring it.
- Dispatch on the scheme prefix to the existing entry point per form, returning
  path, fidelity token, pin values and cleanup ownership. The two digest forms
  get distinct tokens because § Grounding shows they differ in whose digest is
  verified.

**Done when:** this task's assertions are green and `--help` lists the eight
flags § Interfaces declares.

### T6: every planned path carries the Tier verdict, the counts reconcile, and the tree is untouched

**Depends on:** T5 — classification runs in the command module; T2 — the
would-remove set and its reasons come from `_plan_stale_owned_paths`.

**Touches:** `packages/agentbundle/agentbundle/commands/catalogue_sync.py`, `packages/agentbundle/tests/unit/test_catalogue_sync.py`

**Tests:**
- `test_sync_reports_tier_verdict_and_selection` — stub below, `stub: true`,
  spec AC-0010. Compiled: yes. **Red observed:** `ImportError: cannot import
  name 'catalogue_sync' from 'agentbundle.commands'`.
- The five path states, the companion path from `safety.companion_path`
  (spec AC-0011), and the reported selection equal to the recipe's.
- `test_sync_reports_seven_counts_and_the_identity` — second stub, `stub: true`,
  spec AC-0016, same observed red. Asserts the seven keys and the identity
  `compared + uncompared == |recorded paths|`. **Inline proof:** the identity is
  what makes both counts checkable; a constant zero fails it.
- The identity's denominator is the raw `managed_paths` array before filtering;
  malformed and unrenderable entries land in `uncompared` (spec AC-0016).
- Each of spec AC-0009's underivable states, including every ownership-state
  loader failure, exits the cannot-answer code
  with its condition named.
- T6's rows added to the tree-walk parametrisation.

```python
# STUB: AC-0010
from agentbundle.cli import _build_parser


def test_sync_reports_tier_verdict_and_selection(derived_tree, upstream, capsys):
    from agentbundle.commands import catalogue_sync

    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"adopter\n")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream), "--dry-run"]
    )

    catalogue_sync.run(args)

    out = capsys.readouterr().out
    assert "would-companion" in out
    assert "packs/alpha/README.md" in out
```

```python
# STUB: AC-0016
import json

from agentbundle.cli import _build_parser


def test_sync_reports_seven_counts_and_the_identity(derived_tree, upstream, capsys):
    from agentbundle.commands import catalogue_sync

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )

    catalogue_sync.run(args)
    summary = json.loads(capsys.readouterr().out)["summary"]

    assert set(summary) == {
        "would_update", "would_companion", "untouched", "would_remove",
        "schema_1_inert", "compared", "uncompared",
    }
    assert summary["compared"] + summary["uncompared"] == 1
```

**Approach:**
- Build the one-row `State`, omitting `"sha"` for a null entry, and call
  `safety.classify` per planned path.
- Derive compared and uncompared from T2's decided/undecided classification.

**Done when:** this task's assertions are green and the tree walk is unchanged
across every case.

### T7: rendering is bounded on all three channels

**Depends on:** T6 — rendering consumes the counts.

**Touches:** `packages/agentbundle/agentbundle/commands/catalogue_sync.py`, `packages/agentbundle/tests/unit/test_catalogue_sync.py`

**Tests:**
- `test_unrenderable_recorded_value_is_reported_by_field_not_value` — stub
  below, `stub: true`, spec AC-0012. Compiled: yes. **Red observed:**
  `ImportError: cannot import name 'catalogue_sync' from
  'agentbundle.commands'`.
- One rejecting case per value kind § Grounding's sink-class row enumerates,
  asserting the field name and reason appear and the value does not (spec
  AC-0012). This includes the rendered source URI and a descriptor's `artifact`
  URL. **Inline proof for a risky mechanism:** the pass direction cannot
  distinguish an applied check from an absent one.

```python
# STUB: AC-0012
import json

from agentbundle.cli import _build_parser


def test_unrenderable_recorded_value_is_reported_by_field_not_value(
    derived_tree, upstream, capsys
):
    from agentbundle.commands import catalogue_sync

    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append(
        {"path": "packs/alpha/\x1b[2Kevil.md", "sha256": "z" * 64}
    )
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )

    catalogue_sync.run(args)
    captured = capsys.readouterr()

    assert "managed_paths" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err
```
- The three replayed modes appear and two runs whose recorded modes differ
  produce identical plans (spec AC-0007, AC-0008).
- The `--format json` document's content on each refusing row of spec AC-0013.

**Approach:**
- Render the table to stdout and the JSON document with a `summary`, following
  `upgrade._build_json_doc`'s vocabulary.
- Route every value the command did not author through the terminal-safe check
  before rendering, whatever its origin.

**Done when:** this task's assertions are green.

### T8: the exit-code table is total and disjoint

**Depends on:** T7 — the ordered predicates land here, once T7 has made every
row's verdict, count, and diagnostic observable on each output channel.

**Touches:** `packages/agentbundle/agentbundle/commands/catalogue_sync.py`, `packages/agentbundle/tests/unit/test_catalogue_sync.py`

**Tests:**
- `test_check_returns_cannot_answer_when_pin_has_no_digest` — stub below,
  `stub: true`, spec AC-0013. Compiled: yes. **Red observed:** `ImportError:
  cannot import name 'catalogue_sync' from 'agentbundle.commands'`. Written and
  made to pass first: it is the only case that exists in the field.
- One input per row of spec AC-0013's table, asserting the observed code equals
  the row's, plus that no input produces a code outside the four.
- Malformed input and a resolver exception both reach a named table row without
  an uncaught exception or traceback determining the process status (spec
  AC-0014).
- A state whose `managed_paths` is a scalar rather than an array — a valid
  recipe paired with `0` — under both `--dry-run` and `--check --compare-tree`,
  reaching the cannot-answer row and printing no plan (spec AC-0014).
  **Inline proof:** the recipe is derivable, so this input passes the
  selection rows; it is the case that separates a malformed *entry*, which
  AC-0016 routes to `uncompared`, from a container that cannot be iterated at
  all.
- A recorded `archive_sha256` of `""`, `0`, `{}` and a 63-character hex string,
  each routing to cannot-answer rather than to difference.
- `--compare-tree` over a clean tree, an edited tree, an empty recorded set, and
  a partially dropped recorded set. **Inline proof:** the last two are the
  inputs that separate "nothing differs" from "nothing was compared", and the
  partial-drop case is why the compared count exists.
- T8's rows added to the tree-walk parametrisation.

```python
# STUB: AC-0013
from agentbundle.cli import _build_parser


def test_check_returns_cannot_answer_when_pin_has_no_digest(
    derived_tree, upstream, capsys
):
    from agentbundle.commands import catalogue_sync

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--check"]
    )

    assert catalogue_sync.run(args) == 3
    assert "archive_sha256" in capsys.readouterr().err
```

**Approach:**
- Implement the table as an ordered sequence of predicates, first match wins, so
  disjointness holds by construction. Totality does not follow from the ordering:
  spec AC-0014 carries it, and this task's boundary cases — malformed input, a
  resolver exception, and a scalar recorded-path container — are what establish
  it.

**Done when:** this task's assertions are green and the manual verification is
recorded in the ledger.

### T9: compatibility warns and never refuses, while the existing gate still refuses

**Depends on:** T5 — the rows, confined baseline read, and existing gate run in
the command module.

**Touches:** `packages/agentbundle/agentbundle/commands/catalogue_sync.py`, `packages/agentbundle/tests/unit/test_catalogue_sync.py`, `packages/agentbundle/tests/fixtures/`

**Tests:**
- `test_moved_pack_version_warns_without_changing_exit_code` — stub below,
  `stub: true`, spec AC-0018. Compiled: yes. **Red observed:** `ImportError:
  cannot import name 'catalogue_sync' from 'agentbundle.commands'`.
- Two arms of one parametrisation: each signal present, and the same run with it
  absent, comparing the exit code between them. One arm compares to a constant.
- A fixture pack declaring adapter-contract major `1`, refused (spec AC-0019).
- The derived-tree baseline manifest read uses the declared confinement helper;
  recorded-path read and hash cases remain covered with T2 (spec AC-0020).
- T9's refusal row added to the tree-walk parametrisation.

```python
# STUB: AC-0018
from agentbundle.cli import _build_parser


def test_moved_pack_version_warns_without_changing_exit_code(
    derived_tree, upstream_with_bumped_pack, capsys
):
    from agentbundle.commands import catalogue_sync

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream_with_bumped_pack), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert "pack version" in capsys.readouterr().out
```

**Approach:**
- Compare each selected pack's versions in the source against the derived tree's
  own copy, read through the declared confinement helper.
- Evaluate `[pack.dependencies]` against the replay's resolved selection.
- Call `check_spec_version_gate` for the refusal.

**Done when:** this task's assertions are green.

### T10: the durable outputs are current, including the projected surface

**Depends on:** T4 — citations move when the extraction lands; T5 — the
entrypoint list names the registered verb.

**Touches:** `docs/architecture/catalogue/upstream-sync.md`, `docs/architecture/catalogue/derived-catalogue.md`, `docs/architecture/agentbundle.md`, `docs/specs/atomic-write-symlink-harden/spec.md`, `docs/specs/atomic-write-symlink-harden/plan.md`, `guides/_shared/how-to/create-a-self-hosted-catalogue.md`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/README-pypi.md`, `packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md`, `tests/roster/test_okf_catalogue_discovery.py`

**Tests:** `no stub (goal-based)` — delivery conditions, run at delivery and not
committed. A citation check pinned into the suite reds on the next unrelated
edit to the file it cites.
- Each citation the § Grounding citation derivation reports in any file this
  change edits is opened at its new line and read to confirm it names the
  construct its sentence describes, and the residual is empty within that scope
  (spec AC-0022). An absence check passes against a wrong re-pin, so resolution
  is the oracle.
- The delivered STATUS banner, struck phase-2 entry, and two-phases-remain
  sentence (spec AC-0023); the § Granularity vacated-name record (spec AC-0024);
  and the recipe bullet (spec AC-0025).
- The entrypoint list against the § Grounding subcommand derivation (spec AC-0021).
- The guide section (spec AC-0026), then **`python3 tools/build-site.py`** to
  regenerate the projection, then both site gates — the authored-source
  entry-link gate, which runs on every pull request, and the rendered-links
  checker over the regenerated tree. § Grounding records which reads which.
- The version across the independently derived release surfaces, with an empty
  unclassified residual (spec AC-0027).
- The marker-conflict exemption states which source yields and why, and every
  criterion-ordinal label under the package test tree is bare (spec AC-0028,
  AC-0029).
- `python3 -m pytest tests/roster/test_okf_catalogue_discovery.py -q`, dispatched
  explicitly because no pull request triggers it, result in the ledger.

**Approach:**
- Re-pin every citation the derivation reports, including the two in
  `atomic-write-symlink-harden`, which cite the `atomic_write` call T4 shifts. A
  line-reference re-pin is a permitted meaning-preserving mechanical rewrite
  even in a `Shipped` spec.
- Rewrite `derived-catalogue.md`'s recipe bullet to current state; mark § Rollout
  phase 2 done; record the vacated `--guides` name in § Granularity.
- Bump the version and write both changelog entries adopter-first.

**Done when:** every check this task's `Tests:` names passes, both site gates
pass over the regenerated projection,
`python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
reports clean metadata, and the roster result is in the ledger.

## Rollout

Additive and reversible: removing the subcommand registration restores the
status quo, because the verb writes nothing that survives its removal. No flag,
canary, migration, or new infrastructure. The one sequencing constraint is
internal — T4's extraction moves line citations, so T10 follows it.

## Risks

- **T4 moves ~220 lines of a shipped pipeline.** Phase 1's 22 criteria over that
  pipeline run in seconds, so the net exists before the move. The residual is a
  behaviour phase 1 did not assert; the whole-tree walk is the second net for
  the class that matters, an unintended write.
- **T4's extraction shifts citations outside this spec.** Two references in
  `atomic-write-symlink-harden` cite the `atomic_write` call that moves. T10
  re-pins them, and spec AC-0022 is a resolve-to-construct check so a wrong
  re-pin cannot pass.
- **The recorded state is attacker-authored.** Every predicate quantified over
  the recorded path set is satisfiable by shrinking that set, which is why the
  compared count and the empty-set condition are both required rather than
  either alone.
- **A bare `sync` against a vendored tree reports a large would-remove set,**
  because the replay defaults `tooling` to `external`. That is truthful, and
  spec AC-0007's named modes are what stop it reading as a recommendation.
- **Splitting the removal guard could reorder it.** The reason an adopter sees
  depends on which branch fires first, so T2 drives each branch separately and
  compares against the AST derivation rather than a stated count.

## Changelog

- 2026-09-17: initial plan.
- 2026-09-17: revised against 42 adjudicated round-1 findings.
- 2026-09-17: revised against 37 adjudicated round-2 findings, then recalibrated
  to ground each load-bearing claim with evidence fitted to the claim. Six
  derivations replaced stated values; the decline branches are derived from the
  post-change guard at verification time. Each stub was run against the T1
  fixture set and its red recorded
  as observed. § Discovery channel and § Grounding are new. The claim that
  `{"sha": None}` reds `make lint-mypy` was refuted by measurement —
  `no_strict_optional` is on — so the shape choice was re-argued from the data
  model instead.
