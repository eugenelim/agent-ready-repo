# Dogfood brief — hyperscaler (managed services)

> **Fixture for `well-architected-cloud` manual QA.** Exercises the
> managed-service (Class-1) by-construction path and confirms the primitives
> "gaps" framing is **not** misapplied. Referenced by path so the gesture is
> replayable.

## The brief

We're building a **B2B SaaS reporting product** on **AWS**. We're already
committed to AWS and comfortable using managed services — we'd rather pay for
managed than run our own. Expected shape:

- API behind **API Gateway** + Lambda / Fargate.
- **Aurora** (managed Postgres) for the relational store; **DynamoDB** for
  high-volume event data.
- **Cognito** for customer identity; **CloudFront** in front of the static app.
- Multi-AZ from day one; we have an availability target of 99.9%.

Constraints: enterprise customers, SOC 2 on the roadmap, a real on-call rotation.

Question: is this well-architected? What are we missing per pillar?

---

## Expected observables (QA scaffolding — not part of the brief)

- `architect-design` concept names **provider-managed-service pillar
  achievement** — reliability via Multi-AZ Aurora, security via Cognito + IAM +
  KMS, performance via managed autoscaling, etc. (the managed service that
  carries each pillar).
- It does **not** apply the primitives **"capability gaps you must build
  yourself"** framing — that framing is for the primitives class, not a
  hyperscaler with managed services. (Misapplying it here would be the failure
  this fixture guards against.)
- The 99.9% target becomes a **quality-attribute scenario** with a measure where
  the design asserts availability.
