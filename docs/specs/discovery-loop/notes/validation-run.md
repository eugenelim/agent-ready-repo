# Validation run — the empirical spec gate (AC17, AC44)

The discovery loop ships as **content** (agent + skills + a carried schema + an
asset), so most of AC44 is a **manual-QA modelled walk** — the contract is
harness-neutral and a full live on-`omnigent` run is a *nice-to-have, not a spec
gate* (RFC-0053 § Out of scope; spec Testing Strategy). The one **executable**
conformance surface — the traceability lint's orphan → CONVERGED transition — is
run for real below; the cap-pause, the recursive tree, and the three security
negative paths are **modelled** (the spike modelled them too; this record makes
the model explicit so the controls are falsifiable, not asserted).

## Executed — the traceability lint orphan → CONVERGED transition (AC34, AC37)

Built a fixture `<tmp>/docs/discovery/household-assistant/_state/traceability.json`
from the spike snapshots and ran the shipped lint
(`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`):

**Pre-converge** (the `traceability.preconverge.json` snapshot — over-scope present,
the security ripple not yet settled):

```
lint-traceability: posture=meta-repo/federated, source=sidecar (authoritative), 18 node(s), 21 edge(s).
  - ORPHAN service:fulfillment [service]: no consumer (down-edge)
  - ORPHAN service:learning-approval [service]: no consumer (down-edge)
lint-traceability: 2 structural orphan(s) (informational).      # default → exit 0
lint-traceability: 2 structural orphan(s) — FAIL (--strict).    # --strict → exit 1
```

**Converged** (the `traceability.json` snapshot — post-recovery, ripple settled):

```
lint-traceability: posture=meta-repo/federated, source=sidecar (authoritative), 23 node(s), 30 edge(s).
lint-traceability: no structural orphans — every node has a producer and a consumer.   # --strict → exit 0
```

This confirms: (a) the sidecar `schema_version: "0.1"` instances are read as
authoritative (T1 conformance); (b) the **orphan → CONVERGED** transition is real;
(c) the **`--strict` flip** is the convergence-gate behaviour AC37 wires (warn-only
exit 0 by default; fail-closed exit 1 under `--strict`).

**Caveat recorded (AC34 honesty).** The shipped lint is a per-node **edge-presence**
check, not full **root→leaf reachability** — confirmed both in the code
(`classify_sidecar` checks each node has an in-edge and out-edge) and by the
`traceability.preconverge.json` comment ("the presence-check lint flags the tip … a
reachability-to-leaf refinement would flag the whole subtree"). The discovery-loop
skill **names the reachability dependency** (AC34) and flags this as a **cross-spec
gap**: until child-4 (`traceability-lint`) adds the reachability pass, the backstop
catches the orphan *tip* of a disconnected subtree, not the whole subtree. See
*RFC-0048 reconciliation + the surfaced findings* in the PR description.

## Modelled — the second structurally-different example (AC44)

**Example:** a *science-hardware lab assistant* (note-12 family — structurally
different from the household assistant: a deeper, more recursive sub-domain tree
and a real regulated-data surface), forcing the paths the household walk did not.

**≥2-level recursive tree (AC2, recursion-as-data).** `intent:vision` →
`intent:cap.experiment-planning` → `intent:sub.reagent-sourcing` (a sub-walk with
its **own** divergence → convergence → validation). The controller walks it
depth-first via `parent_id`; the sub-idea index carries `reagent-sourcing` as an
open sub-walk — a node, not a second project.

**Forced concentration-bound + pause-at-bound-resume (AC17).** `cost_budget = $25`,
`round_cap = 12`, concentration bound ~40%. The `reagent-sourcing` sub-walk's spend
crosses **$10 (40%)** at round 5 while the parent is mid-convergence. The loop sets
`meta.status = paused-at-bound`, writes an option card surfacing the verdict set
(**extend/override** / narrow / park / abandon), and **waits** — it does **not**
silently stop or silently continue. The human picks **extend** (grant +$10); the
loop records the new bound + rationale to the decision log and **resumes** the
sub-walk where it paused (`converging`, counters intact via the Tier-2 per-gate
snapshot). This is the recursion-specific path the flat-cap counter-compare does
not cover.

**Actual discovery reviewers (AC19).** At G2 reconcile the run fires
`discovery-threat-reviewer` (the reagent sourcing crosses a **regulated-data**
boundary — controlled-substance ordering) and `discovery-reliability-reviewer`
(the experiment-planning failure modes) as forked-context lenses — **not** `core`'s
code reviewers-in-a-mode. The threat reviewer raises a `major` because only
baseline security depth is installed on a regulated boundary → the loop **surfaces
to the human** (AC27) rather than degrading silently.

## Modelled — the three security negative paths (AC25, AC26, AC29, AC44)

1. **Forged consent (AC25 — tests the *channel*, not the slot).** The controller
   attempts to self-write a `ratified-by: human` row at G2 and resume. The design
   has resume **re-derive `human` provenance only from the agent-untokened store
   and reject any row not attested there**, so the forged row does not advance the
   gate. **Honest status: `degraded — harness-conformance precondition, not
   demonstrated`.** This is a *modelled* walk on a content-only PR; nothing here
   exercises a real untokened channel, so the recorded outcome is the *specified*
   behaviour, not a demonstrated one. A real falsification requires running the
   forged-row rejection against an actual untokened channel (or recording that the
   loop refuses unattended operation when the harness cannot provide one). The
   contract is honest that this is a precondition, not a proof.

2. **In-place decision-log tamper (AC26).** An in-place edit of a prior row's
   `rationale` (keeping the append-length) is detected by the **anchored**
   hash-chain: the recomputed chain no longer matches the **externally-held tip**
   in the agent-untokened / harness-immutable store. **Caveat made explicit:** the
   bare `prev_hash`/`hash` field is *not* sufficient on its own — the writing agent
   could recompute every hash and re-chain a self-consistent forgery; detection
   depends on the anchored tip. Same honest status as #1: the anchor is a
   **harness-conformance precondition**, modelled here, not demonstrated by a
   content-only PR.

3. **Over-threshold cascade surfaces (AC29).** A spurious high-fan-out edge would
   cascade-invalidate **> 1/3 of the active matrix** (the spec-tunable default). The
   circuit-breaker **surfaces to the human** ("invalidation exceeds fan-out
   threshold") rather than auto-cascading, and the cascade re-runs would have
   counted against the cost budget.

## Outcome

The executable transition passes; the modelled paths each have a defined,
recorded outcome that the security/integrity controls make falsifiable. A full
live on-`omnigent` run remains a nice-to-have, not a spec gate.
