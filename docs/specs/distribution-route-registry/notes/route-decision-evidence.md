# Pre-change distribution-route decision evidence

The baseline records every decision found by the bounded Python analysis at commit
`1134701ba584ce5375358943f2cbab4ea69574a0`. Generate it without shell redirection:

```bash
python3 tools/check_distribution_route_decisions.py --write-baseline docs/specs/distribution-route-registry/route-decision-baseline.json
```

The generated JSON records the measuring commit, inventory, coverage counts, unresolved
coverage residue, limits, and killing mutations. Reproduce it while the measured inputs
still match that commit:

```bash
python3 tools/check_distribution_route_decisions.py --verify-baseline docs/specs/distribution-route-registry/route-decision-baseline.json
```

## What the check measures

The check parses every Python file below `packages/agentbundle/agentbundle/`, except the
installed-client marker template. Its vocabulary comes from route keys, identities,
output subdirectories, and unambiguous route-bearing recipe names in the owned TOML
data. It does not use a maintained list of the three current route names.

The literal pass walks every string syntax node. It reports inline comparisons,
membership collections and their later sinks, dispatch-map keys, argparse choices,
iterations and comprehensions, route arguments and results, and route-root prefixes
passed to `startswith` or `endswith`.

The value-flow pass starts from `Recipe` and `ResolvedDistributionRoute` annotations,
from dataclass fields annotated with one of them (followed transitively), and from
same-module functions whose return annotation carries a route value. It computes
assignment aliases and direct same-module call arguments to a fixed point. It is
module-local by construction: a route value handed across a module boundary reaches its
consumer untainted, which the checker records as a limit and the
`route-decision-analysis-depth` intent tracks. It reports conditions,
comparisons, matches, and mapping lookups even when no route literal is present. A route
value passed across an unresolved call boundary is coverage residue, so it cannot be
mistaken for a clean result.

`--check` exits zero only when both the finding set and coverage residue are empty. The
baseline therefore supplies three independently checkable counts: all parsed decision
nodes, all route-literal nodes, and all contract-derived decisions. During T1, the live
repository scan was checked explicitly for the previously missed prefix,
separated-collection, and comprehension sites. The lasting fixture suite exercises each
of those syntax shapes without pinning later tasks to the pre-change source. Any of
those checks can come out negative.

## Completeness boundary

This is a falsifiable completeness argument for the stated static model, not proof over
all possible program behavior. It establishes that every parsed Python decision reached
from the derived literal vocabulary or the typed value-flow roots is either a finding,
explicit residue, or one of the exemptions enumerated in the checker's own `limits`
list, which is the single canonical home for them.

It cannot establish decisions implemented by reflection, generated code, native code,
or non-Python files. It also cannot discover a route value returned through an untyped
cross-module or higher-order interface when no route-bearing annotation or literal is
visible at the receiving site. Proving those cases would require whole-program typed
data-flow across imports, callbacks, and runtime code generation. The checker states
these limits in the baseline instead of claiming semantic exhaustiveness.

## Audit reconciliation

Fourteen of the fifteen audit rows have at least one matching inventory site. Row 15
is `tests/fixtures/distribution-routes/golden.json`, which is neither Python nor inside
the scanned root, so it is covered by the golden suite rather than by this inventory. The
inventory is intentionally finer grained: it records a collection definition and each
decision sink separately. It also records route resolution and dispatch branches in
`build/main.py`, the Agent Plugin extension-metadata selection at `build/main.py:701`,
and the Claude-plugin verification root at `catalogue_tooling/verify.py:1228`. These are
route decisions, but they are not additional route-set surfaces, so the audit remains
fifteen rows.

The audit had been short in three ways: it named only collection definitions, omitted
the dist-tree prefix forms that do not contain a bare route-name literal, and did not
name the Agent Plugin metadata decision. Its site column and completeness note now make
those distinctions explicit.

## Killing mutations

| Mutation | Forbidden form | Why it is distinct |
| --- | --- | --- |
| `return candidate == "apm"` | Shared code names a route | Direct comparison. |
| `ROUTES = {"apm", "claude-plugins"}; return candidate in ROUTES` | Shared code names a route | Separates the literals from the later membership decision. |
| `return path.startswith(("apm/", "claude-plugins/"))` | Shared code names a route | Exercises rooted prefixes missed by bare-name searches. |
| `return resolved.identity == some_key` | Contract-derived route value | Contains no route literal and survives parameter renaming. |
| `return HANDLERS[resolved.identity]` | Contract-derived route value | Contains neither a route literal nor a comparison. |

`tools/test_route_branch_guard.py` is the executable mutation set: it runs each
forbidden form against an isolated tree and fails if any goes unreported. The JSON
baseline records the same forms in machine-readable prose for audit, and the table above
summarises them for a reader; the guard is what actually runs
without scraping this prose.
