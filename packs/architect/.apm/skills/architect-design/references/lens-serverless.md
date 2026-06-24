# Serverless / managed-platform lens — the workload-class overlay for serverless designs

A workload-class lens for systems built on serverless / managed platforms —
where the platform, not you, owns the runtime, the scaling, and the binding
limits around them. It reviews the *same* design through the concerns that flat
pillars miss when the platform's contract is load-bearing. Serverless is a
first-class workload class across all three cloud vendors (the AWS Serverless
Applications Lens, the Azure Functions guidance in the Well-Architected
Framework, the Google Cloud Run / serverless best practices) — this is the
cloud-agnostic distillation of that guidance, not any one vendor's.

> Note: this reference is intentionally duplicated into `architect-review`'s
> `references/lens-serverless.md`. Skill autonomy beats DRY at this scale —
> each skill stands alone. See the pack README.

## The serverless class is wider than functions

"Serverless" is a billing-and-scaling *model* — the platform owns provisioning
and scales on demand — not a synonym for FaaS. The concerns below bite across
**four serverless entity types**, and a real design usually combines several:

- **Serverless compute** — functions (FaaS) and scale-to-zero containers; the
  platform runs your code on demand and you do not manage the host.
- **Serverless data** — auto-scaling / on-demand databases and stores billed by
  capacity unit or per request, not by a provisioned cluster you size.
- **Serverless search / analytics** — on-demand query and indexing engines that
  scale (and bill) per query or per byte scanned.
- **Serverless event glue / messaging** — managed queues, topics, and event
  buses that connect the pieces and deliver work asynchronously.

Apply each concern to whichever entities it bites for *this* design — a cost
cliff lands differently on a function than on a per-byte-scanned query engine,
and a cold start lands differently on compute than on a scaled-down store.

## Apply the concerns that bite — a filter, not a worklist

This lens is a filter, not a checklist to recite. A scale-to-zero API with one
function and one on-demand table has a very different surface from an
event-driven pipeline fanning across queues, functions, and an analytics store.
Name the concerns that bite for *this* system and the entities they bite; do not
march the whole list. Version-specific numbers do not live here at all — see
*Numbers live in a platform skill, not here* below.

## Execution & throughput limits + the sync-vs-async gate

Serverless components carry **bounded, often non-configurable ceilings**, and
the design has to live inside them rather than assume they will be raised:

- **Compute & its front doors** — request / integration timeouts on the function
  or container *and* on the **front door** (the API gateway / managed HTTP
  endpoint / load balancer / event source that fronts the component) are bounded
  and frequently capped below what a long operation needs. The *front-door*
  timeout is usually the tighter one and the one a synchronous caller actually
  hits.
- **Serverless data & search** — per-partition / per-unit throughput ceilings
  and throttling cliffs; a hot partition or an unsharded key throttles long
  before the account limit. A store scaled down to its floor also pays
  **query-latency-at-floor** until it scales back up.

The forcing question: **does the worst-case path fit inside the binding
ceiling?**

**The sync-vs-async gate — the viability check this lens owns.** For any
synchronous request path, **sum the worst-case latency across every hop** —
front door → handler cold start → handler work → each downstream call (or model
round, for an inference path) → any synchronous wait on a throttled or at-floor
downstream → per-call and serialization overhead — and **compare the total to
the binding front-door timeout**. If the worst-case sum can exceed that ceiling,
the synchronous shape is **not viable** and the long-running work must move off
the request path. The documented escapes all **change the shape** of the call:

- **stream** partial results so the connection stays productive and no single
  hop owns the whole budget;
- **202-accept-then-poll** — acknowledge immediately, do the work in the
  background, expose a status / result endpoint;
- **fire-and-forget + callback / webhook** when the caller need not block at all.

(Pre-warming is *not* one of these — it only shrinks the cold-start addend in
the sum, not the shape; if the steady-state work alone exceeds the ceiling, the
shape must change regardless of how warm the runtime is.)

A long-running or bursty operation behind a synchronous front door is the
canonical serverless design miss: it passes a happy-path demo and fails the
moment the work runs long. Force the gate at design time, not in production.

## Cold-start & readiness

First-use latency is **not function-only**, and budgeting only the steady state
hides it:

- **Compute** — a scale-to-zero or newly-attached runtime pays a **cold start**,
  worsened by private-network attachment (below) and large deployment artifacts
  / dependencies.
- **Serverless data & search** — a scaled-down or idle store pays a **scale-up /
  first-connection / cache-warm** latency on the first request after idle, which
  a steady-state latency number never shows.

The forcing question: **what does the first request after idle cost on the
critical path, and which posture do we accept for it?** Budget cold start on the
critical path (it compounds into the sync-vs-async sum above) and choose a
posture deliberately: **tolerate** it, **keep-warm** (provisioned concurrency /
minimum instances — note the cost floor below), **pre-warm** ahead of a known
burst, or **shrink the cold path** (smaller artifact, fewer dependencies,
lazy-load). Each posture sits at a different point on the cost / latency
tradeoff — name which one and why.

## Scale-to-zero economics, capacity floors & cost cliffs

"Serverless" names a billing / scaling *model*, **not a guarantee of zero idle
cost** — and the model **differs by entity**:

- **Components that reach zero** — FaaS, on-demand request-priced stores,
  scale-to-zero containers: no traffic, (near) no cost.
- **Components that floor at a minimum capacity unit** — some serverless data /
  search tiers, and any keep-warm posture, **never reach zero**; they bill a
  continuous minimum even when idle.

The forcing question: **which components actually reach zero, and which floor —
and what is each cliff?** Two cliffs follow, both design-time decisions:

- **The standing floor** — min-capacity components and keep-warm settings bill
  continuously; ten idle environments each holding a floor is a recurring cost
  the "scales to zero" framing hides.
- **The per-request / per-byte-scanned cliff** — a pay-per-use store or query
  engine where an **unbounded scan, a missing index, or a runaway loop is a
  denial-of-wallet surface**: cost scales with work, and a bug or an attacker can
  drive the work. Bound the query, cap the fan-out, put a budget alarm on it.

## Statelessness, idempotency & delivery semantics

Serverless compute is **ephemeral and share-nothing** — no in-process state
survives between invocations, a warm instance is an optimization you cannot rely
on, and **work scheduled after the handler returns may simply not run** (the
host can freeze or reclaim the instance). Anything durable goes to an external
store; anything that must complete runs *before* you return.

The serverless event / messaging glue is **at-least-once by default**, which
forces three questions:

- **consumers must be idempotent** — the same message will be redelivered, so
  processing it twice must be safe;
- **poison messages need a dead-letter path** — a message that always fails must
  drain somewhere, or it blocks the queue and retries forever (a cost cliff too);
- **ordering is guaranteed only by an explicitly ordered / FIFO variant** —
  default topics and queues do not preserve order.

Multi-step flows are **orchestrated by a state machine**, not chained in-process
across function calls — the orchestration, retries, and compensation belong in a
durable coordinator, not in a handler that may not survive to make the next
call.

## Private-serverless network reachability

A serverless component reaching a **private (VPC / VNet-resident) dependency** —
a database, an internal service, a cache — needs **explicit network
attachment**, and that attachment has consequences:

- it **adds cold-start latency** (the runtime joins the private network on a cold
  start);
- it requires the **full set of egress paths** the component needs — a private
  endpoint or NAT path for each private dependency *and* for any external API it
  still calls; a **missing path surfaces as a silent timeout, not a clear
  error**, which is among the hardest serverless failures to diagnose;
- some **serverless hosting tiers cannot attach to a private network at all** —
  the reachability requirement can rule a hosting choice out, so the forcing
  question — **can this hosting tier even reach the private dependency, and at
  what cold-start cost?** — belongs in the Stage-0 shape, not a late surprise.

## Routes into the security boundary

This lens names trust boundaries at **design altitude only**. Several serverless
concerns sit on a security boundary — a component's **execution identity and
least-privilege scoping** (what the function / container role may touch),
**secrets handling** for the platform credentials it carries, **public-vs-private
exposure** of a front door, and the **egress paths** above as an SSRF /
data-exfiltration surface. Name these boundaries here; route their control-level
verification to the repo's `security-reviewer` / `security-checklists` like every
other security-boundary concern, per `cross-cutting-questions.md`. Name
implementation frameworks never — this lens reasons about the platform's binding
contract and the boundaries it crosses, not which serverless product to buy.

## Numbers live in a platform skill, not here

This lens carries the **durable rule** and an **illustrative example flagged
"confirm current specifics with the provider"** — never a bundled number. The
**binding figures** — a specific integration-timeout ceiling, a store's
minimum-capacity-unit floor, a runtime's payload / duration limits, a managed
runtime's packaging / entrypoint model — are version-specific and rot, so they
belong in a **curated platform skill** for that vendor, consulted when the design
depends on the exact figure. When you are on an unfamiliar managed surface and no
such skill is installed, that is the signal to recommend installing one (or to
ground the figure in official docs / `research`) — not to guess, and not to bake
the number into this lens.

Whichever source you reach for, **ground the figure rather than recall it**:
carry it with its **source and a confidence level**, and **lower confidence and
flag** any load-bearing limit you could not ground — never assert a binding
contract from memory. A binding limit recalled wrong is the design miss that
surfaces two days into the build, not at review.

## Use, don't recite

Apply the concerns that bite for *this* serverless design, across the entities it
actually uses. A scale-to-zero single-function API and a fan-out event pipeline
across queues, functions, and an analytics store have very different timeout,
cold-start, cost, and delivery surfaces — name theirs, not a generic list.
