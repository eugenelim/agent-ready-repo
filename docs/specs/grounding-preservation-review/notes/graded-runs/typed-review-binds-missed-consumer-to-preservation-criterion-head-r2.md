```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": 1,
      "finding_id": "F1",
      "rule_ref": "CRIT-3 (Default search and listing exclude value nodes); adversarial-reviewer implementation-stage check 10, shared-substrate reachability",
      "observation": "The change adds VALUE members to Graph.nodes, a collection that outline() reads with no kind filter and no opt-in, so the default listing includes value nodes. Only search() received the include_values filter.",
      "reachable_path": "build() appends Node(name, VALUE) for every `value x` line (graph.py:30-31) -> outline(graph) iterates every graph.nodes entry (graph.py:54-56) -> the listing returns `value limit`.",
      "actual_failure": "Run: `python3 -B -c 'from graph import build, outline, search; g = build([\"def run\", \"call run\", \"value limit\", \"call limit\"]); print(outline(g)); print(search(g, \"limit\"))'` printed `['def run', 'call run', 'value limit', 'call limit']` and `[Node(name='limit', kind='call')]`. Default search excludes the value node, but default listing exposes it, which breaks CRIT-3. Fix: default listing must exclude value nodes, and any inclusion must need an explicit opt-in, as search already requires.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/graph.py:30-31",
        "evals/files/preservation-review/graph.py:54-56",
        "evals/files/preservation-review/graph.py:45-51",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "F2",
      "rule_ref": "CRIT-3; adversarial-reviewer implementation-stage check 1, acceptance criterion verification",
      "observation": "No test verifies CRIT-3. test_graph.py never imports or calls outline(), and its one search test queries `run`, which matches no value node, so value exclusion from search or listing is never exercised.",
      "reachable_path": "test_graph.py:3 imports only CALL, VALUE, build, resolve_calls, and search. test_search_finds_definitions (test_graph.py:23-26) searches for `run` against LINES (test_graph.py:5), whose only value node is `limit`.",
      "actual_failure": "CRIT-3 maps to no verification artifact file:line. That is why the listing defect in F1 passes the suite unseen. Fix: CRIT-3 needs a verification artifact that fails when default search or default listing returns a value node. It must cover both surfaces the criterion names. This is a missing artifact the citation establishes, so it owes no run.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/test_graph.py:5",
        "evals/files/preservation-review/test_graph.py:23-26",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    }
  ]
}
```
