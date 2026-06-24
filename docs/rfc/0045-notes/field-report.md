# RFC-0045 field report — two builds, the design phase reasoning from memory

Scrubbed evidence behind RFC-0045. Two real multi-day builds on different AWS
stacks, both of which used the `architect` pack to shape the design *before*
building. Identifiers, account details, and product specifics are removed; only
the design-phase failure pattern is retained.

## Build 1 — the structurally-fatal latency miss (an agent system)

**Stack shape.** A managed agent runtime (multi-round LLM tool-use loop) behind
a managed HTTP API gateway with a JWT authorizer and a thin facade function;
state in a managed NoSQL store.

**What the design said.** The design doc modelled the request path as a
**fully synchronous, blocking** call: the facade invokes the agent runtime and
returns its full result to the client. It explicitly considered and **dismissed
the async alternative** as "over-engineered for a real-time conversational
agent." Nowhere did it state the front door's integration timeout, sum the
end-to-end latency of the chain, or compare the two.

**The binding fact it never named.** The managed HTTP API has a
**non-configurable ~29-second integration timeout**. A single agent turn is
three sequential inference rounds (≈5–8 s each) plus per-tool gateway hops plus
first-call cold start — **28–43 s+ typical**. The synchronous path is
structurally impossible; no bug-fix can make it fit.

**How it surfaced.** Two days of `504 Gateway Timeout` during build. The agent
first mis-diagnosed it (chased a context bug, then a wall-clock-timeout bug)
before the human forced *"pressure test the architecture in case there is a
problem,"* after which the structural conclusion landed. The fix is the
**202-accept-then-poll** pattern (return a job id; async-invoke a worker with no
gateway timeout; client polls a status store) — which is AWS's own documented
prescriptive guidance for exactly this case.

**The review missed it too.** The `architect-review` pass on this design
returned **"SHIP WITH CHANGES"** with thorough security and data-model findings
— and **zero** mentions of latency, duration, synchronous/asynchronous, or the
timeout contract. The single highest-impact, two-day-costing flaw was invisible
to both the design *and* its review. → motivates the **dual-consumed** viability
check (V) and grounding discipline (C): the reviewer must be grounded on the
platform contract, not only the author.

## Build 2 — managed-service contract assumptions from memory (a GraphRAG stack)

**Stack shape.** A "serverless"-first GraphRAG template: a managed serverless
graph store + a managed vector store inside a private network, a serverless
ingestion task, and a VPC-attached query function.

**Contract assumptions asserted from memory, corrected only at deploy:**
- *"The graph store is VPC-only / has no public endpoint."* Too absolute — the
  engine gained an optional (off-by-default) public endpoint in a later version.
- *Single-AZ subnet topology.* The store's DB subnet group requires subnets in
  **≥2 AZs** or provisioning fails — "single-AZ" can only describe the running
  instance, not the subnet group.
- **The load-bearing one — "serverless = scales to zero."** The managed graph
  store is "serverless" but **floors at a minimum capacity unit and bills
  continuously** (it does not pause to zero). And at that floor, per-query
  latency (~hundreds of ms) made the chosen **per-edge sequential traversal**
  blow the query function's timeout on **every** live call — invisible against
  the in-memory test store, dominant live. The fix was a batched per-hop query.
- *VPC-attached function cold start* (network-attach + first SDK init + first
  model call) exceeded the initial timeout; *a no-NAT private network* needs the
  **full** set of egress endpoints provisioned, or a missing one surfaces as a
  **silent timeout**, not a clear error.

## The common thread

Both builds: **the design was shaped, and reviewed, against model memory and
abstract pillars — not the platform's binding contract.** This is RFC-0044's
memory-vs-ground-truth thesis, one inner-loop stage earlier, where there is no
deployed artifact and no toolchain oracle to run. The design-time answer is to
**ground load-bearing platform claims in authoritative prose** (a curated
platform skill / official docs / `research`) with confidence, and to **back the
serverless lens** that carries the recurring binding concerns — at both
construction and review. The version-specific numbers (the ~29 s ceiling, the
minimum-capacity-unit floor, payload/duration limits) belong in a curated
platform skill, never bundled per-vendor into the agnostic lens.
