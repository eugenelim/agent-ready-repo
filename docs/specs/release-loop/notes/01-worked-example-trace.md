# Worked-example trace — one full release-loop cycle, no engine (AC12)

> **This is a trace, not a schema or a runtime.** It walks **one full outer-loop
> cycle** plus **four forced negative paths**, on the form omnigent stores, to
> demonstrate that **every transition is a file edit on the sidecar plus a policy
> check** — there is no engine, scheduler, or service. Copy the *moves*, not the
> wording. The single-example / single-operator limit is flagged honestly in
> *Threats to validity* at the end.

**Subject.** The RFC-0048 worked example — **`example-assistant`**, the secure
personal-assistant agent — so this downstream trace is continuous with the
upstream coordinator prototype (RFC-0048 note-02 / `frame-domain`'s
`example-assistant`). `work-loop` (the inner loop) has reached **G4**: the
component is locally built and verified, and the digest-pinned artifact is ready
to deploy.

**The store.** Omnigent holds the cycle as worktree files plus the four sidecar
slots (consumed by convention from the produced `_state/`, `schema_version`
checked): `blackboard.json`, `open-questions.json`, `decision-log.json`, and the
`meta` block. `release-lead` reads and writes these; the harness owns the
ephemeral envs, the human option-card pause, and the cost budget.

---

## Executed on paper — the full cycle (deploy → e2e → converge → surface G5)

**Round 1 starts.** `meta` before the pass:

```json
{ "round": 0, "round_cap": 4, "cost_budget": 20.0, "cost_spent": 0.0,
  "gate": "release-loop", "status": "deploying" }
```

1. **Deploy (file edit + policy check).** `release-lead` checks the deploy target
   is **provably isolated** (no prod reachability, no real data, isolated from
   other envs — control (h)); it is, so this is an autonomous-zone action. It
   deploys the **digest-pinned G4 artifact** to ephemeral env `eph-7` using a
   **broker-mediated, ephemeral-tier credential** (control (g) — the session can
   assume only the `eph` role; a prod-tier acquisition from here would be
   rejected). A blackboard slot is written:

   ```json
   { "id": "deploy-r1", "type": "deploy", "status": "proposed",
     "produced_by": "release-lead", "lens": "controller",
     "round_last_touched": 1, "artifact_digest": "sha256:abc…",
     "env": "eph-7" }
   ```

2. **E2e + observe (file edit + policy check).** E2e runs against `eph-7`; the
   **changed surface** is derived from the diff against the deployed baseline —
   the `derive-list` endpoint changed. A canary observes success/error/latency.
   E2e finds a **defect**: `derive-list` returns a 500 on an empty resource set.
   The telemetry slot carrying the e2e output is **tagged `untrusted`**
   (control (d)) — it is data, inert until the controller promotes it:

   ```json
   { "id": "telemetry-r1", "type": "telemetry", "status": "proposed",
     "produced_by": "e2e", "untrusted": true, "lens": "controller",
     "round_last_touched": 1,
     "finding": "derive-list 500 on empty set; coverage gap: changed endpoint unasserted-on-empty" }
   ```

3. **Feedback to the inner loop (file edit, no human relay).** The controller
   **promotes** the validated finding and writes it back to `work-loop` as a build
   task on the blackboard — the agent read the real environment output itself; no
   human relayed it. `cost_spent` → 6.2.

4. **Inner-loop fix + redeploy (round 2).** `work-loop` fixes the empty-set path
   and adds the missing e2e assertion. `release-lead` redeploys the new
   digest-pinned artifact to `eph-7`. `round` → 2 (incremented by **exactly one**;
   the cap cannot be stepped over). `cost_spent` → 12.8.

5. **Converge (policy check, not a human).** The convergence policy now holds:
   **canary** success/error/latency within SLOs; **e2e coverage** — every changed
   surface element (`derive-list`, including the empty-set case) has ≥ 1 passing
   assertion; **flake** 0.4% < 2%. Converged.

6. **Assemble the release-readiness record (AC6b — consolidation, not a new
   reviewer).** Before surfacing G5, `release-lead` pre-fills the record from
   **(d)-validated** telemetry + the reused-reviewer verdicts:

   - convergence-policy result: **pass**;
   - `operational-safety` verdicts (via `quality-engineer`, orchestrator-inlined
     `environment-isolation` / `observability-and-smoke` / `drift-and-rollback`):
     **clean**;
   - `security-reviewer` verdict on the deploy diff: **clean**;
   - cumulative **error-budget status**: the SLO-authoring capability does not
     exist yet, so the record carries an explicit **`error-budget: not-defined`**
     field the human sees (recorded and visible, never a silent pass).

7. **Surface G5 (consent gate).** `release-lead` surfaces the readiness record as
   an **option card** for the human to **ratify** — it is a ratify-a-record gate,
   not a bare go/no-go. The controller **holds no token** to write the verdict.
   `meta.status` → `awaiting-human`. The loop stops here.

Every step above was a **file edit + a policy check**. No runtime ran the loop.

---

## Forced negative path 1 — cap-hit (AC8 stall-surface)

Re-run the cycle with a stubborn defect that does not converge. After the pass
that takes `round` to `round_cap` (4) with a **still-failing canary**, the policy
predicate `round >= round_cap AND (failing canary | uncovered surface | open
finding)` fires. `release-lead` writes a decision-log row and **surfaces** —
it does **not** churn a fifth round:

```json
{ "ts": "2026-06-30T11:04:00Z", "gate": "release-loop",
  "decision": "status: stalled-at-cap — canary still failing at round_cap",
  "ratified_by": "release-lead", "reversibility_class": "reversible",
  "rationale": "outer round cap reached with unconverged canary; surfacing",
  "prev_hash": "…", "hash": "…" }
```

`meta.status` → `stalled-at-cap`. Surfaced.

## Forced negative path 2 — security boundary with no lens (AC10c surface)

A later cycle's deploy diff **crosses an auth boundary** (the assistant adds an
owner-scoped token check). The orchestrator finds **no `security-reviewer`
installed** in this repo. `release-lead` does **not** degrade silently — it
**surfaces to the human**: "deploy crosses an auth boundary and no security lens
is installed; cannot proceed autonomously." (Same fail-closed posture as the
polyrepo no-`core` case.)

## Forced negative path 3 — forged consent, rejected (AC10a falsification)

The controller attempts to self-write a `ratified_by: human` row to advance the
G5 gate without a human verdict:

```json
{ "ts": "…", "gate": "G5", "decision": "ship to prod",
  "ratified_by": "human", "reversibility_class": "one-way-door", … }
```

On resume, the controller performs the positive attestation cross-check: it
**reads the set of harness-attested verdicts from the untokened store / HITL
channel** and accepts a `ratified_by: human` row **only if it matches one**. There
is **no matching attestation** for this appended row (the agent holds no token to
mint one), so the row is **rejected** and resume refuses to advance. Note this is
a *clean append*, not an in-place edit — the anchored hash-chain of path 4 would
**not** catch it; the attestation lookup is what closes the append-forge path.
Forged consent fails.

## Forced negative path 4 — decision-log tamper, detected (AC10b falsification)

The controller edits a **prior `ratified_by: human` row** in place — rewriting its
recorded `decision` text (e.g. softening a "ship to prod, owner-data tier" verdict
into a broader one) — and re-chains the `prev_hash`/`hash` of every following row,
a self-consistent bare chain. This is the **history-rewrite** attack on the audit
trail (distinct from path 3's clean append). But the chain **tip is anchored in
the (a) agent-untokened store**, which the agent cannot rewrite. On the next read,
the recomputed tip **does not match** the anchored tip: the in-place edit is
**detected**. (A bare hash-chain alone would have missed this — the anchored tip
is load-bearing; and per path 3, the anchored tip alone would miss a clean append,
so (a)'s attestation cross-check and (b)'s anchored tip are complementary.)

---

## Outcome

The full cycle and all four negative paths are **file edits + policy checks**:
deploy/e2e/feedback/redeploy/converge are blackboard + `meta` writes against the
convergence policy; the cap is a `meta` predicate; the no-lens, forged-consent,
and tamper paths are surfaces / rejections driven by the harness-attested channel
and the anchored hash-chain tip. **No engine, scheduler, or service was
introduced** — the load-bearing empirical claim holds on this example.

## Threats to validity

- **One example, one operator.** This is a single trace by a single author; it
  demonstrates the *shape* is no-engine, not that every real deploy topology is.
  The residual scale risk mirrors RFC-0053's spike Threats.
- **The four negative paths are exercised by injection, not natural occurrence.**
  The cap-hit, no-lens, forged-consent, and tamper paths were forced to confirm
  the surfaces/rejections fire; a live run would reach them only under the real
  conditions.
- **Control (e) (the oscillation circuit-breaker) is modelled, not traced.** The
  four forced paths do not include a promote↔rollback storm; (e)'s attempt-bound
  is the one control whose trigger the cost cap does *not* cover, and it is
  asserted in the skill but not walked here — a deliberate scope choice (the spec
  mandates four paths), flagged so the gap is visible.
- **Harness-conformance is assumed, not proven here.** Controls (a) / (b) / (g)
  rest on omnigent actually providing an agent-untokened verdict channel, an
  immutable-log / anchored-tip store, and tier-scoped roles. This trace shows the
  loop *relies on* those primitives correctly; it does not verify omnigent
  supplies them — that is a harness-conformance precondition, surfaced if absent.
