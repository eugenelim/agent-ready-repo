# `core` — guides

`core` is the flagship pack: the loop your agent can't cut corners in. Plan and surface assumptions, hard gates between "done" and done, adversarial review in a fresh session, and capture what was learned. The skills (`work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`), the four reviewer/executor subagents, and the `pre-pr` + `session-start` hooks all compose into one loop.

New here? [Why loop engineering](explanation/core-pack.md#why-loop-engineering) is the *why* — the leverage has moved off the prompt and onto the loop. [The `core` pack as a system](explanation/core-pack.md) is the full map. Then build something with [plan and execute non-trivial work](how-to/plan-and-execute-non-trivial-work.md).

## Tutorials

Learning-oriented, start-to-finish.

- [From idea to a walking skeleton](tutorials/start-a-new-project.md) — stand up a new project the structured way, end to end.

## How-to

Task-oriented recipes for a problem you already have.

- [Plan and execute non-trivial work](how-to/plan-and-execute-non-trivial-work.md) — the loop itself, applied to a feature or change.
- [Fix a bug](how-to/bug-fix.md) — the diagnose-then-fix path, with a regression test as the receipt.
- [Adapt a freshly-installed pack to your project](how-to/adapt-to-project.md) — tailor the defaults to your repo after install.
- [Review a branch or PR you didn't write](how-to/review-someone-elses-pr.md) — point the reviewers at anyone's diff.
- [Intake an external brief into a product brief](how-to/intake-an-external-brief.md) — turn unstructured external input (email, message, issue) into a DoR-ready product brief.
- [Receive a product brief and decompose it into specs](how-to/receive-a-product-brief-and-decompose-it-into-specs.md) — turn a multi-feature handoff into shippable specs.
- [Decide and record your foundation during inception](how-to/record-your-foundation-during-inception.md) — the ADR + `reference.md` you write before the first feature.

## Reference

Information-oriented, dry and complete.

- [Spec `Shape:` and the plan's `## Design (LLD)`](reference/spec-shape-and-lld.md) — the fields, what they mean, and how the stack is derived.
- [Product brief fields](reference/product-brief-fields.md) — the brief field list and the linkage it stamps on derived specs.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The `core` pack as a system](explanation/core-pack.md) — how the parts compose, and how it compares to vibe-coding, Spec Kit, and Kiro's spec mode.
- [The token economy of the loop](explanation/token-economy.md) — what the loop wastes, what it spends on purpose, and why the cold reviewer earns its cost.
- [Why the plan owns the LLD](explanation/why-the-plan-owns-the-lld.md) — where the low-level design lives and why it isn't in the spec.
- [About the walking skeleton](explanation/walking-skeleton-vs-throwaway.md) — the thinnest end-to-end slice, and when to throw code away instead.
- [About foundation vs. map](explanation/foundation-vs-map.md) — the two things you record at inception and why they're different.
- [Why a brief layer](explanation/why-a-brief-layer.md) — why a brief sits above the spec when work spans many features.

---

Cross-cutting guides — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/).
