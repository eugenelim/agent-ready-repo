# Pre-change route-decision baseline

The accepted checkout has 15 route-consuming surfaces and a recorded inventory of
decision origins and sinks in shared build-time Python. The source under
`packages/agentbundle/` matches local commit
`1134701ba584ce5375358943f2cbab4ea69574a0`; unrelated documentation and workspace
changes were present and are outside this measurement.

This human-readable roster fixes the pre-change evidence before dispatch work begins.
`tools/check_distribution_route_decisions.py --write-baseline` produces the machine
baseline, including the same local commit, exact AST locations, coverage counts, and
any unclassified residue.

## Route-set surfaces

The fifteen-surface audit remains the surface-level roster. Its definition and sink
anchors are reconciled in
[`agent-plugin-surface-gaps.md`](agent-plugin-surface-gaps.md). Row 15 is the non-code
golden fixture; the other fourteen surfaces map to the following Python decisions.

| Surface | Decision origin and sinks |
| --- | --- |
| Default build recipes | `build/main.py:402,2388` |
| Pack-declarable recipes | `commands/validate.py:37,182` |
| Install-route emission | `commands/install.py:59,1187` |
| Install dist-tree detection | `commands/install.py:1380` |
| Install route discovery | `commands/install.py:1908` |
| Install pack subtree paths | `commands/install.py:2451` |
| Install subtree roots | `commands/install.py:2591` |
| Install subtree iteration | `commands/install.py:2619` |
| Diff dist-tree detection | `commands/diff.py:160` |
| Upgrade dist-tree detection | `commands/upgrade.py:84` |
| Render targets | `commands/render.py:136-139,156-159` |
| Catalogue verification roots | `catalogue_tooling/verify.py:1348,1353,1360` |
| Build-check output checks | `build/self_host.py:1607-1659,1713-1742` |
| Route capability lint | `build/lint_packs.py:517` |

## Contract validation and dispatch decisions

These decisions do not add route-set surfaces. They are still in scope because shared
code chooses route-specific validation, admission, projection, or filesystem behavior
at each site.

| Decision | Origin and sinks |
| --- | --- |
| Declared route membership | `build/main.py:1241` |
| Admission-policy table | `build/main.py:1256-1267` |
| Adapter-projector table | `build/main.py:1272-1290` |
| Agent Plugin discovery path | `build/main.py:1367,1392,1398,1409,1420,1428` |
| Agent Plugin pre-uniqueness controls | `build/main.py:1670,1681` |
| Package-projector dispatch | `build/main.py:1738,1743` |
| Claude-plugin admission filter | `build/main.py:1763` and its `route_filtered` consumers |
| Claude-plugin projection contract | `build/main.py:1843` |
| Claude-plugin hook projection | `build/main.py:1938` and its `plugin_route` consumers |
| Default-build diagnostic route | `build/main.py:2386` |
| Explicit-recipe diagnostic route | `build/main.py:2426-2428` |
| Claude-plugin manifest verification root | `catalogue_tooling/verify.py:1228` |

`build/main.py:702` is not a distribution-route decision. It reads the Agent Plugin
manifest extension namespace inside code dedicated to that manifest format. Source
tree `.apm` paths and CLI prose are likewise not route decisions merely because they
contain the three-letter string.

## Reproducible check

The checker derives route identities and output roots from
`contracts/distribution-routes.toml`, then derives route-bearing recipe names from the
bundled recipe TOMLs. It parses every non-test Python file under the shared package
root and runs two passes:

- The literal pass finds inline comparisons, membership collections, dispatch-map
  keys, argument choices, indirect collection consumers, route-valued arguments and
  results, fixed route paths, and output-prefix checks.
- The data-flow pass starts from typed resolved-route values and route-named parameters,
  follows local assignments to a fixed point, and reports comparisons or conditionals
  controlled by a contract-derived discriminator even when no route literal appears.

Writing the baseline is explicit and does not need shell redirection:

```bash
python3 tools/check_distribution_route_decisions.py \
  --write-baseline docs/specs/distribution-route-registry/route-decision-baseline.json
```

At the measuring commit, exact reproduction uses `--verify-baseline` with that path.
After relocation, `--check` must return zero findings and zero coverage residue.

## Checkable completeness argument

The completeness claim is bounded to executable Python in the shared package tree.
Within that boundary, the check walks every parsed AST decision node, not only files or
lines containing known route words. Its vocabulary comes from the contract and recipe
declarations, and its second pass begins from resolved-route values rather than from
literals. The generated baseline records the number of Python files, decision nodes,
route-bearing literals, derived-value decisions, and unclassified escapes. A parse
failure or an unresolved route-value call is coverage residue and makes write mode
return 2 and check mode fail. A third party can therefore falsify completeness by
adding an unsupported escape or an unparseable file; agreement with the surface audit
is not an input to this result.

The check cannot establish behavior hidden in reflection, generated Python, native
extensions, or non-Python files. It also cannot follow a route value through an
unannotated higher-order callback; it reports the direct escape but does not interpret
the callback. Finally, syntax coverage cannot prove that a business concept with no
connection to a contract value or derived vocabulary is secretly a route alias. Those
limits require code review or a broader semantic analysis and are not claimed away.

## Mutation set

`tools/test_check_distribution_route_decisions.py` makes the following mutations in
isolated source fixtures. Each must create a finding.

| Mutation | Forbidden form | Why it is present |
| --- | --- | --- |
| `route == "apm"` | Shared code names a route | Direct comparison floor |
| A route literal collection later used by membership | Shared code names a route | Covers an origin separated from its sink |
| `{"apm": handler}` | Shared code names a route | Covers dispatch-map keys |
| `choices=["apm"]` | Shared code names a route | Covers argument enumerations |
| `startswith(("apm/", "claude-plugins/"))` | Shared code names a route | Covers literals embedded in output prefixes |
| `resolved.identity == some_key` through a local alias | Contract-derived value, no route literal | Proves the second pass is independent of literal search |
| `handlers[resolved.identity]` | Contract-derived value, no comparison | Covers a lookup decision with no comparison |
| `context.resolved_route.identity == some_key` | Contract-derived value behind a carrier | Covers a decision reached through a dataclass field |
| `resolved.output_subdir == other` | Contract-derived value on a derived field | Proves the discriminator set comes from the route types, not a hand-kept list |
| `registry.read(raw)` then `declaration.identity == other` | Contract-derived value across modules | Covers the module-qualified reader call every consumer uses |
| `{"apm-package": …}` keyed dispatch | Per-route projector identity | Covers the discriminator the registration seam itself matches on |
| A tuple naming a module as a behavior factory | Minted exemption | Proves the single-route permission cannot be granted by an unrelated file |

The set mirrors every syntactic shape observed before the change, adds the literal-free
mutations the earlier audit method could not see, and — after the post-gates review
found three of them evadable — the cross-module, derived-field, and minted-exemption
forms. `tools/test_route_branch_guard.py` runs all of them against the shipped tree.
