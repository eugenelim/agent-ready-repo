```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": 1,
      "finding_id": "F1",
      "rule_ref": "evals/files/preservation-review/spec.md CRIT-3 (Default search and listing exclude value nodes); implementation-stage check 10, shared-substrate reachability",
      "observation": "`outline()` is the graph's listing operation. It returns every node in `graph.nodes` with no kind filter and no opt-in flag, so value nodes appear in the default listing. Only `search()` got the `include_values` filter. Run: `python3 -I -B -c \"...build(['def run','call run','value limit','call limit']); print(outline(g))\"` printed `['def run', 'call run', 'value limit', 'call limit']` and exited 0.",
      "reachable_path": "build() appends a Node(kind=VALUE) for each `value x` line to the shared `graph.nodes` list (graph.py:28-31). outline() reads that list without opt-in (graph.py:54-56), so any default listing of a graph built from source that has a value line shows the value node.",
      "actual_failure": "The default listing contains `value limit`. CRIT-3 says default listing excludes value nodes, so the listing consumer class is not preserved and CRIT-3 is broken in the shipped code.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/graph.py:54-56",
        "evals/files/preservation-review/graph.py:28-31",
        "evals/files/preservation-review/graph.py:45-51",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "F2",
      "rule_ref": "Implementation-stage check 1, Acceptance Criterion verification: every criterion maps to an existing verification artifact",
      "observation": "No test covers the listing half of CRIT-3: test_graph.py never imports or calls `outline`. The only search test queries `run`, which matches no value node, so nothing checks that default search leaves out a value node either. CRIT-3 cannot be mapped to any artifact `file:line`. This defect comes from a citation (a missing artifact), so no run is owed.",
      "reachable_path": "test_graph.py imports only CALL, VALUE, build, resolve_calls, and search (test_graph.py:3). Its three tests cover node creation (line 8), call resolution (line 14), and a search for `run` (lines 23-26).",
      "actual_failure": "The suite passes even though default listing shows value nodes (see F1). CRIT-3 has no verification artifact, so its breakage ships unnoticed.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/test_graph.py:23-26",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    }
  ]
}
```
