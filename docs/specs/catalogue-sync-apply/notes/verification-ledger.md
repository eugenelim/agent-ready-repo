# Verification ledger — catalogue sync, the apply path and the scoping flags

Execution observations, one section per wave. The plan contract sends them here
rather than into the plan, which is hash-pinned from `plan-locked` onward.

## Shaping — grounding derivations

- **Date:** 2026-09-22

Four read-only probes under
[`grounding/`](grounding/) established the facts the contract rests on. The
plan's § Grounding table holds each invocation; this section holds what each
one printed.

| Derivation | Printed |
| --- | --- |
| `probe-scope-subtrees.py` | `--package credbroker` → `packages/credbroker/`, gated on the `credential-brokers` pack; `--package agentbundle` → `.agentbundle/tooling/agentbundle/`, gated on vendored tooling. `collect_fields` replaces the recorded recipe when `cfg.packs` is not `None`; `_plan_stale_owned_paths`'s `current_paths` is the keep-set |
| `probe-pin-ref.py` | `resolve_catalogue` returns a `Path` only; `_resolve_https` parses the ref from the URI and defaults it to `main`, never resolving it to a commit SHA; the pattern is the module-level `_HTTPS_RE` |
| `probe-jailed-write-admits-planned-paths.py` | external 1,907 planned paths, vendored 2,147; zero rejected as a direct write and zero as a companion write in both modes |
| `probe-rollback-snapshot-bound.py` | external 13.7 MiB, vendored 17.3 MiB of replayed bytes; largest single file 0.2 MiB; worst-case peak 34.5 MiB for replay plus a full-run snapshot |

### Residuals reported

- The architecture's § Granularity calls both `--package` targets "`packages/`
  subtrees". Only `credbroker` is one; the vendored `agentbundle` lands under
  `.agentbundle/tooling/`. AC-0053 corrects it.

## Execution — wave 1

Grounding re-run 2026-09-23 against the rebased base: all ten derivations
reproduce. Two figures the contract leans on hardest were confirmed
unchanged — `write_jailed` 16 call sites across 10 modules against
`write_companion` 4 across 4, and the link publish leaving `st_nlink=2` with
staged residue until the unlink, which the confined reader refuses.

### T1 — the `git+https://` ref helper

`resolve_git_ref` exported from `catalogue.py`; `_resolve_https` delegates and
no longer defaults the ref itself. Gates: lint exit 0, pytest exit 0 over 197
tests. This repository's pytest prints dots and no summary line, so every
count in this ledger is a dot count against an exit code, never a parsed
"N passed".

### T2 — the scope predicate

`select_write_set` plus three private helpers. Gates: lint exit 0, pytest exit
0 over 106 tests.

**Mutation proof.** The `--pack core` / `packs/core-extras/` trap is the case
the task says no other case distinguishes. Dropping the trailing separator
from `f"packs/{name}/"` turns the suite red and restoring it turns it green,
so that guard fails when broken rather than merely passing.

**Observation — the replay the fixture uses.** T2's `Done when` requires the
predicate be tested "against the planned-path set of a real replay, not a
hand-written list". A live-repository replay costs roughly 75 s per
invocation, so the fixture is a small on-disk source driven through a genuine
`replay_derivation()` call rather than the monorepo itself. The clause's
intent holds — no hand-written path list — and the fixture reproduces every
shape the task names, including paths under
`.agentbundle/tooling/packs/catalogue-curation/`, which are exactly what a
narrow reading of clause 5 admits.

### T3 — the state merge and the pin

`build_pin` and `merge_ownership_state`, both pure. Gates: lint exit 0, pytest
exit 0 over 121 tests.

**Observation — AC-0059's absolute clauses do not bind this function.** T3's
first draft asserted that a Tier-3 path and a companion path were absent from
the merged set while supplying neither in any input, so both assertions held
whatever the implementation did. Measured 2026-09-23: feeding
`packs/alpha/README.upstream.md` and an adopter-only path in through the
pre-run `recorded` mapping leaves both in the merged set, so the exclusion was
never a property of `merge_ownership_state`.

Owner decision 2026-09-23, the contribution reading: AC-0059's "a path **the
run classified** Tier-3" binds what this run contributes, and this run
classifies nothing arriving through `recorded`. The two dead assertions were
deleted rather than made fail-able. A suffix filter in the merge would be
wrong outright — AC-0071 establishes that a source may legitimately ship
`x.upstream.md`, refusing only on collision with a Tier-2 `x.md`.

**Obligation handed forward.** The clauses bind the caller, which is the only
seam that knows which paths were companion destinations. **T4 and T6 must
assert that no companion destination ever enters `written`.** Without it,
AC-0059's two absolute clauses have no fail-able check anywhere in the
delivery.
