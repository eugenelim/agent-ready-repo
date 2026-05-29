# Auto-classify yield characterisation (AC12)

A read-only, non-circular pass over the repo's own recent commit history,
measuring how often the Option-A classifier could confidently label a task
`cannot-collide`. **Descriptive only — this asserts no threshold and is not a
regression target.** "All-added" is git ground truth, not the classifier's own
judgement, so the measurement isn't circular.

## Method

`.context/research-workloop-coordination/autoclassify_yield.py 400` (gitignored
scratch) classifies the last N non-merge commits by the mechanical Option-A
rules (`git diff --name-status <commit>~1 <commit>` → status letters + paths):
all-`A` → cannot-collide; rename/delete → dangerous; danger-path → dangerous;
else modified-existing. A commit is a proxy for a task's branch diff.

## Result (368 non-merge commits, 2026-05-29)

```
   299   81.2%  modified-existing  (-> serial, fail-closed)
    29    7.9%  danger-path        (-> serial)
    20    5.4%  cannot-collide     (all-added; the only auto-SAFE label)
    15    4.1%  has-delete         (-> serial)
     3    0.8%  rename/move        (-> serial)
     2    0.5%  empty
```

**confidently-`cannot-collide` ≈ 5.4%.**

## Reading

- The *positive* yield (auto-green-lighting parallel) is low — consistent with
  the parent spec's finding that safely-parallelizable work is a minority
  (only ⅓ of declared-independent waves were even file-disjoint).
- The feature's value is therefore **lopsided toward the defensive side**: it
  removes **100% of the routine per-task classification labor** (the tool
  derives a category for every task, not just the 5%), and it *mechanically*
  serializes the ~13% obviously-dangerous (rename/delete/danger-path) + defaults
  the 81% ambiguous to serial — removing the chance a human hand-classifies a
  migration-touching task as "safe".
- A commit is a per-commit proxy for a per-task diff; planned independent tasks
  (new modules, new specs) likely skew more additive than a random bugfix
  commit, so 5.4% is a rough **lower bound** for the planned-wave population.

## Known-uncovered residual (named, not claimed)

Auto-`cannot-collide` establishes *file-additive* ∧ (via the gate's merge-tree
half) *file-disjoint*, and the cross-branch symbol guard
(`added_paths_may_share_symbol`) catches the common shared-symbol vector (same
basename / same new directory). It does **not** establish ADR-0005's full
*disjoint-no-shared-symbol*: two file-disjoint additive branches that collide on
a **runtime key in a string literal** or a **symbol referenced from a third
file** — with **no test coverage** — remain a silent-break class. That residual
is **the same irreducible class RFC-0015 §2 already names and accepts** for the
parallel-write path, backstopped by the **post-merge integrated test gate** the
work-loop runs in the primary. This spec does not claim to catch it.
