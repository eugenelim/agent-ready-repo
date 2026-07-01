# `release-engineering` — guides

`release-engineering` is the SRE/ops outer loop: deployed end-to-end validation above `work-loop`'s inner build loop. Where `core` validates that code works locally — it compiles, tests pass, the diff is clean — `release-engineering` validates that the **deployed whole** works: the integrated artifact, running in a real environment, observed through real telemetry.

The pack ships two primitives: `release-lead` (the supervisor agent) and `release-loop` (the skill doctrine). Together they cover the full arc from "deploy-ready artifact" to "prod ship ratified by a human" — autonomously on ephemeral environments, and with an explicit consent gate at the only irreversible exit.

**Before you start:** `release-engineering` hard-depends on `core`. Install `core` first.

```bash
agentbundle install --pack core           # required first
agentbundle install --pack release-engineering
```

New here? Read [The release loop explained](explanation/the-release-loop.md) for the *why* — the inner/outer split and the minimum-regret autonomy carve. Then run your first release with [Your first release](tutorials/your-first-release.md).

---

## Tutorials

Learning-oriented walkthroughs.

- [Your first release](tutorials/your-first-release.md) — from a deploy-ready build to a ratified prod ship, end to end.

## How-to

Task-oriented recipes for when you already know what you're doing.

- [Run a release](how-to/run-a-release.md) — trigger `release-lead`, monitor convergence rounds, review the release-readiness record, and ratify at G5.

## Reference

Information-oriented — dry, complete, look-it-up-when-you-need-it.

- [The release-readiness record](reference/release-readiness-record.md) — the convergence output format: every field, what each verdict means, and how to read the record at G5.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The release loop explained](explanation/the-release-loop.md) — the inner/outer loop split, the minimum-regret autonomy carve, the ephemeral environment model, the convergence policy, and the feedback seam between the outer and inner loops.

---

Cross-cutting guides — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/). For the full picture of how the release loop composes with discovery and build, see [the three loops as a system](../_shared/explanation/the-three-loops.md).
