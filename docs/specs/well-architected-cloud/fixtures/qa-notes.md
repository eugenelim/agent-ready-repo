# Dogfood QA notes — well-architected-cloud

Manual QA for the pure-markdown skill + loop behavior, run by exercising the
enhanced `architect-design` / `architect-review` against the committed brief
fixtures in this directory. These skills have no runtime; the gesture is the
agent applying the skill procedure to the brief. Recorded here so the result is
inspectable and the gesture is replayable.

> Run on 2026-06-12 against the implemented skills. The agentic-hetzner gesture
> is traced in full because it exercises the concept stage, the convergence
> loop (auto-resolve / stasis escape / surface-judgment), and WA-mode review;
> the other four confirm their specific observable.

---

## 1. `brief-agentic-hetzner.md` — design concept + loop + review

### Stage-0 concept (drafted from `assets/concept.md`)

- **Problem & context:** A2UI multi-agent assistant that drives a web UI for the
  user; planner + worker agents calling tools and acting in the UI.
- **Constraints:** small team, cost-sensitive, EU data residency, Hetzner (no
  managed-cloud commitment).
- **Candidate shapes:** (A) agents on Hetzner cloud servers behind a Hetzner LB,
  self-managed Postgres, external LLM API; (B) same but self-hosted inference.
- **Provider / provider-class:** **primitives provider (Hetzner-class)** — by
  construction, pillars are met by *building them yourself*. Routed to
  `cloud-primitives.md`; capability gaps named: **managed data tier** (run
  Postgres + replication + backups yourself), **edge/CDN** (no edge — front the
  UI yourself), managed identity, serverless. ✅ *names primitives class + data-
  tier + edge/CDN gaps.*
- **Top prioritized quality attributes** (business-importance × risk):
  1. **Security (agentic)** — agents act in the UI and send internal docs to an
     external LLM; highest blast radius.
  2. **Performance** — interactive assistant, latency-sensitive.
  3. Reliability — stateful, but ranked behind the two above. ✅ *prioritizes
     Security (agentic) + Performance.*
- **Key tradeoff / open decision:** **self-host inference vs. external LLM API**
  — control + EU residency vs. operational burden + capability lag. Surfaced as
  a tradeoff / sensitivity point. ✅

### Convergence loop (`convergence-loop.md`)

Reviewer seeded with artifact + agreed concept + constraints (cold-read floor
here, since same session; flagged as weaker isolation than a fresh context).

- **Pass 1 findings:**
  - **F1 🔧 mechanical** — internal-document → external-LLM-API call crosses an
    **unlabeled trust boundary**. Fix fully determined by the spine → **auto-
    resolved**: design labels the egress boundary, names what crosses (internal
    docs in the prompt), flags residency. *(no human asked)* ✅
  - **F2 🔧 mechanical (provisional)** — "highly available" + self-managed
    Postgres but **no stated RPO/restore target**. Spine requires a recovery
    target → attempt to auto-resolve, but **no constraint supplies the value**.
  - **F3 🧭 judgment** — self-host inference vs. external LLM API (tradeoff).
    **Not auto-resolved.**
- **Pass 2 findings:** F1 resolved (boundary now labeled). **F2 reappears** — the
  loop still can't determine an RPO from anything given. → **stasis escape**:
  F2 escalated to the human as a judgment finding rather than looped. ✅
- **Terminates** at pass 2 (no mechanical findings remain that can be resolved;
  cap not even reached). ✅
- **Surfaced to human as decisions:** F3 (self-host vs. external) and F2
  (acceptable RPO / restore target for the data tier). Loop did **not** pick a
  side on either. ✅ *(never auto-resolve a judgment finding)*

### `architect-review` WA mode (GenAI/agentic + security lenses)

Risk register (`assets/risk-register.md`) names, among others:

- **🔧 mechanical 🟥** — internal-data → external-LLM **egress boundary** unlabeled
  / un-minimized (determinate: label + minimize prompt payload).
- **🧭 judgment 🟥** — **A2UI surface-authority risk**: a worker agent that can act
  in the UI is a confused-deputy surface; how much autonomy/confirmation to
  require is a risk-acceptance decision.
- Each finding carries severity **and** a mechanical/judgment tag. ✅

**Result: all agentic-hetzner observables met.**

---

## 2. `brief-enterprise-brain.md` — leading-edge path

- `architect-design` finds **no shipped pillar/lens/provider reference** fits
  "living ontologies / enterprise brain" → takes `leading-edge-domains.md`:
  **flags novelty** explicitly. ✅
- **Composes with `research`** (`applied`/`deep`) when installed for a grey-lit
  survey; **degrades** to first-principles + flagged novelty + **lowered
  confidence** when absent (does not error/require it). ✅
- **Synthesizes an ad-hoc enterprise-brain lens** (memory types / knowledge
  stratums / provenance / governance) for this engagement only. ✅
- Surfaces **centralized-vs-federated-ontology** as a **judgment** finding
  carrying **source + confidence**. ✅
- Ships **no enterprise-brain content** in the pack (method only). ✅

## 3. `brief-local-first.md` — local-first on-ramp

- Concept treats local-first as a **legitimate starting topology**. ✅
- Names the **local→production delta** (`local-dev.md`): TLS + domain, secrets
  store, durable data tier (backups + restore), object storage for uploads,
  observability, scaling/availability. ✅
- Names a **graduation path** to a provider class + what becomes real first
  (TLS + secrets + durable data before CDN/multi-region). ✅
- Prescribes **no local toolchain** (no docker-compose, no images). ✅
- Graduation order surfaced as a **judgment** call. ✅

## 4. `brief-hyperscaler.md` — managed-service by-construction

- Concept names **provider-managed-service pillar achievement** (Multi-AZ Aurora
  → reliability, Cognito + IAM + KMS → security, managed autoscaling →
  performance, CloudFront → edge). ✅
- Does **not** apply the primitives **"gaps you must build"** framing — correct,
  managed services carry the pillars here. ✅
- 99.9% target framed as a quality-attribute scenario with a measure. ✅

## 5. `brief-non-cloud.md` — graceful degradation

- Stage-0 concept **still runs**: problem / constraints / candidate shapes
  (streaming vs. two-pass) / quality attributes (large-file performance,
  maintainability). ✅
- Does **not** force provider selection or pillar-by-construction scaffolding —
  no cloud is manufactured. ✅
- Streaming-vs-two-pass surfaced as the key tradeoff (memory vs. random access).
  ✅

---

**All seven gestures produce the named observables.**
