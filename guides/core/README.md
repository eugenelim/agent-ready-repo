---
title: "`core` — guides"
summary: Start durable work through one intake route, then carry approved work through planning, execution, verification, independent review, and merge.
pack: core
kind: explanation
---

# `core` — guides

`core` is the flagship pack: one front door for durable work intake, then a loop your agent can't cut corners in. Describe the work in ordinary language; `work-intake` routes it to the right artifact and lifecycle state. Approved specs continue through hard gates and cold review.

```text
Start work on adding export retention controls for workspace owners.
```

New here? [Why loop engineering](explanation/core-pack.md#why-loop-engineering) is the *why* — the leverage has moved off the prompt and onto the loop. [The `core` pack as a system](explanation/core-pack.md) is the full map. Then build something with [plan and execute non-trivial work](how-to/plan-and-execute-non-trivial-work.md).

## Tutorials

Learning-oriented, start-to-finish.

- [From idea to a walking skeleton](tutorials/start-a-new-project.md) — stand up a new project the structured way, end to end.

## How-to

Task-oriented recipes for a problem you already have.

- [Plan and execute non-trivial work](how-to/plan-and-execute-non-trivial-work.md) — the loop itself, applied to a feature or change.
- [Start or remember work without choosing a skill](how-to/start-or-remember-work.md) — route an ordinary request into the right artifact and workspace state.
- [Fix a bug](how-to/bug-fix.md) — the diagnose-then-fix path, with a regression test as the receipt.
- [Adapt a freshly-installed pack to your project](how-to/adapt-to-project.md) — tailor the defaults to your repo after install.
- [Review a branch or PR you didn't write](how-to/review-someone-elses-pr.md) — point the reviewers at anyone's diff.
- [Close work without losing lasting context](how-to/close-and-disposition-work.md) — verify durable context, settle coordination, and choose a safe disposition.
- [Intake an external brief into a product brief](how-to/intake-an-external-brief.md) — turn unstructured external input (email, message, issue) into a DoR-ready product brief.
- [Receive a product brief and decompose it into specs](how-to/receive-a-product-brief-and-decompose-it-into-specs.md) — turn a multi-feature handoff into shippable specs.
- [Run a 30-minute live workflow demo](how-to/run-a-live-demo.md) — show technical, enterprise, or non-technical teams the canonical Core and Product Engineering handoffs on their own repository.
- [Decide and record your foundation during inception](how-to/record-your-foundation-during-inception.md) — the ADR + `reference.md` you write before the first feature.
- [Migrate a legacy workspace entry safely](how-to/migrate-capture-work.md) — convert one reviewed compatibility entry with ledger-backed recovery and rollback.

## Reference

Information-oriented, dry and complete.

- [Spec `Shape:` and the plan's `## Design (LLD)`](reference/spec-shape-and-lld.md) — the fields, what they mean, and how the stack is derived.
- [Product brief fields](reference/product-brief-fields.md) — the brief field list and the linkage it stamps on derived specs.
- [Work-intake routing and lifecycle](reference/work-intake-routing-and-lifecycle.md) — exact routes, states, processors, and mutation boundaries.
- [workspace.toml schema reference](reference/workspace-toml-schema.md) — target entries, compatibility forms, findings, migration policy, and ledger state.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The `core` pack as a system](explanation/core-pack.md) — how the parts compose, and how it compares to vibe-coding, Spec Kit, and Kiro's spec mode.
- [The token economy of the loop](explanation/token-economy.md) — what the loop wastes, what it spends on purpose, and why the cold reviewer earns its cost.
- [Why the plan owns the LLD](explanation/why-the-plan-owns-the-lld.md) — where the low-level design lives and why it isn't in the spec.
- [About the walking skeleton](explanation/walking-skeleton-vs-throwaway.md) — the thinnest end-to-end slice, and when to throw code away instead.
- [About foundation vs. map](explanation/foundation-vs-map.md) — the two things you record at inception and why they're different.
- [Why a brief layer](explanation/why-a-brief-layer.md) — why a brief sits above the spec when work spans many features.
- [Why work begins with an artifact](explanation/why-work-begins-with-an-artifact.md) — how source, durable meaning, lifecycle, and execution remain separate.
- [Role journeys](explanation/role-journeys.md) — how PMs, engineers, and agents use the system at their operating altitude.

---

Cross-cutting guides — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/).
