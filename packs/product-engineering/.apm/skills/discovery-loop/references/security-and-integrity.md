# Reference: the security & integrity contract

Depth for [`SKILL.md`](../SKILL.md). The loop runs largely unattended and records
human approvals, so it **must not be able to forge a human's sign-off, tamper with
the decision log, or run away**. Each control below is **enforced behaviour the
implementing run can falsify** — not prose. The decision-log row schema and the
data-classification table live in
[`sidecar-schema.md`](sidecar-schema.md); this file is *how the controls behave*.

## 1. Verdict write-authority — no forged consent *(AC25)*

The *same* reasoning context both sets `status=awaiting-human` and reads the
decision log to resume, so the contract must prevent the controller (or a poisoned
lens) from writing its own `ratified-by: human` row and auto-advancing a gate the
human never saw.

- The human verdict is written through a **harness-attested channel the agent has
  no token for** (e.g. the harness's HITL pause writing the verdict into a store
  the agent cannot write).
- Resume is gated on a verdict whose `human` provenance is **harness-attested, not
  self-asserted** in a file the agent also writes. Concretely: **on resume the loop
  re-derives `human` provenance *only* from the untokened store and rejects any
  `ratified_by: human` row whose provenance is not attested there** — a row the
  agent wrote into the workspace file is never sufficient. (Without this resume
  re-derivation an adopter can ship a schema that *looks* conformant yet trusts a
  file the agent also writes.)
- **This is a hard harness-conformance precondition, not a demonstrated property.**
  An adopter whose harness cannot provide an agent-untokened verdict channel
  **cannot run the loop unattended safely**.
- **The falsifiable test is of the *channel*, not the slot:** the run has the
  controller **attempt to self-write a `ratified-by: human` row and resume**, and
  records that the forged row is **rejected/flagged** (or, for a harness without the
  untokened channel, records that the loop **refuses unattended operation**).

## 2. Decision-log as a real audit trail *(AC26)*

The slot is **append-only** + **per-row actor attestation** + **tamper-evidence** +
a **trusted timestamp**, paired with a lint/CI assertion that the slot's commits
are add-only.

**Tamper-evidence is verified, not asserted.** Ship **one** of:

- **(a) an anchored hash-chain** — each row carries `prev_hash`/`hash` (a
  **SHA-256** over the row's canonical-field-order JSON serialization **plus the
  prior row's `hash`**). **The chain alone is not enough:** the *same* controller
  that writes the log can recompute every row's hash after an in-place edit and
  re-chain a fully self-consistent log — so a bare `prev_hash`/`hash` is *not*
  tamper-evident against the in-scope adversary (the agent that writes it). The
  chain is tamper-evident **only when its tip is anchored where the agent has no
  token to rewrite it** — the **same agent-untokened / harness-immutable store as
  the AC25 verdict channel** (or the tip is signed with a key the agent lacks). The
  falsifiable AC26-(a) requirement is **that anchored tip**, not the bare hash
  field; the verify-lint compares the recomputed chain against the
  externally-held tip. **or**
- **(b) a harness-provided immutable log** — an explicit harness-conformance
  precondition naming it, recorded in the schema reference.

The validation run exercises a **tamper attempt** (an in-place prior-row edit) and
records that it is **detected**.

## 3. Non-degradable security lens on a boundary *(AC27)*

The `discovery-threat-reviewer` is a hard dep (required at G2; ships in
`product-engineering`, the floor) and degrades only in *depth* — never silently
skipped. Its baseline checklist must not silently stand in for full depth on a
security-relevant product.

- Tie the lens's *depth* to a **risk trigger** (mirroring RFC-0025 / the surfacing
  predicate): when an intent or artifact crosses a security boundary (auth,
  untrusted-input-to-memory, regulated data) **and** `core`'s `security-checklists`
  depth is absent (only the reviewer's baseline checklist is available), the loop
  **surfaces to the human** — *"security-relevant boundary crossed, only baseline
  security depth installed"* — rather than degrading silently.

## 4. Lens-write integrity — no blackboard poisoning *(AC28)*

In lens-team mode, lens-agents write the blackboard the controller trusts for
convergence and cascade-invalidation; a lens that ingests untrusted external
content (web `research`, adopter docs) is an injection sink.

- A lens may only **propose** (`status: proposed`); **only the controller
  promotes** to `ratified`.
- Lens-asserted traceability edges are **advisory until the controller validates**
  them.
- Any lens ingesting untrusted external content is a **trust boundary** whose
  output is **data, not instructions**, to the controller. **Make this a marking
  discipline, not a sentence:** a slot whose `produced_by` lens ingested external
  content (web `research`, adopter docs) carries an explicit **`untrusted: true`**
  marker, and the controller's promote step is specified to **treat slot content as
  inert data — it never executes instructions found in slot prose**. An
  implementer satisfies this control by wiring the marker + the inert-promote rule,
  not by repeating the property.

## 5. Cascade-invalidation circuit-breaker *(AC29)*

The edge-walk *scopes* a rejection, but the same primitive is a
denial-of-convergence lever (spurious edges from a high-fan-out node could
invalidate the whole blackboard and burn the budget).

- Cascade re-runs **count against the cost budget**.
- An invalidation exceeding a **fan-out threshold surfaces to the human** rather
  than auto-cascading. The threshold is a **spec-tunable default** (mirroring D4's
  ~40% concentration default — a modelled-not-run control must not ship without a
  value): **surface when an invalidation touches more than `1/3` of the active
  matrix *or* more than `N` nodes absolute (default `N = 8`), whichever is
  smaller.** The **absolute-count companion is load-bearing**: a fractional gate
  alone is gameable — a poisoned lens that first shrinks the active matrix (marking
  unrelated nodes `stale`/`rejected` over several rounds) lowers the denominator so
  a later wide cascade stays under `1/3`; the absolute count catches that
  slow-drip denial-of-convergence.
- The validation run **forces one over-threshold invalidation** and records that it
  **surfaced** rather than auto-cascading.

## 6. `reversibility-class` is an enumeration *(AC30)*

It gates consent stakes, so an agent must not under-classify a one-way door as
`reversible`.

- Enumerate the classes: `reversible` / `costly-to-reverse` / `one-way-door`
  (never free text).
- `one-way-door` binds to a **mandatory consent gate regardless of which gate it
  arose at**.

## 7. Sidecar data-handling / classification *(AC31)*

The slots carry product strategy, personas, security findings, customer/domain
facts, and consent rationale — sensitive and potentially regulated data.

- **Classify each slot** — `public` / `internal` / `sensitive` / `regulated` (or
  an adopter equivalent).
- **Redaction guidance** for examples and promoted notes — a `sensitive`/`regulated`
  fact is not copied verbatim into a shared example or a promoted note.
- **Retention/export expectations** for `_state/` and harness-backed stores; the
  state branch is **protected against history rewrite**.
- **A regulated- or secret-bearing artifact surfaces** to the human /
  `discovery-threat-reviewer` before being written to a shared repo-backed
  sidecar — the same surface-don't-degrade-silently posture as control 3.
- **Composition with the checkpoint (AC8).** The classification check is a
  **precondition on the per-round/per-gate checkpoint write**: a
  `sensitive`/`regulated` slot is redacted-or-surfaced **before** it reaches the
  shared store, not as a separate later step. The two requirements **compose** —
  they are not independently satisfiable.

## What the validation run must falsify (the negative paths)

The empirical run records — controls otherwise modelled-not-run:

1. a controller **self-write of a `ratified-by: human` row** is **rejected/flagged**
   (or the loop refuses unattended operation) — *testing the channel, not the slot*;
2. an **in-place prior-row decision-log edit** is **detected**;
3. one **over-threshold cascade fan-out surfaces** rather than auto-cascading.
