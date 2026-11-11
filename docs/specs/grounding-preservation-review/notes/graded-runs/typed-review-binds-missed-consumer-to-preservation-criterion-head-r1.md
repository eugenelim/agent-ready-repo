```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": "1",
      "finding_id": "F1",
      "rule_ref": "CRIT-3 (Default search and listing exclude value nodes); implementation-stage checks 1 and 10, shared-substrate reachability",
      "observation": "outline() is the listing consumer of Graph.nodes and observes every node without an opt-in filter, so value nodes appear in the default listing. Only search() applies the include_values filter. Run: python3 -I -B -c 'from graph import *; print(outline(build([\"def run\",\"call run\",\"value limit\",\"call limit\"])))' printed ['def run', 'call run', 'value limit', 'call limit'].",
      "reachable_path": "build() appends Node(name, VALUE) for each `value x` line into the shared Graph.nodes list (graph.py:30-31); outline() iterates graph.nodes with no kind filter (graph.py:54-56) and returns 'value limit'.",
      "actual_failure": "The default listing includes value nodes, which CRIT-3 forbids. Fix: the default listing must exclude value nodes, with any inclusion only behind an explicit opt-in, as search() already does.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/spec.md:9",
        "evals/files/preservation-review/graph.py:30-31",
        "evals/files/preservation-review/graph.py:54-56"
      ],
      "material": true
    },
    {
      "schema_version": "1",
      "finding_id": "F2",
      "rule_ref": "CRIT-3; implementation-stage check 1, Acceptance Criterion verification (every criterion maps to a verification artifact file:line)",
      "observation": "No test verifies CRIT-3. test_graph.py does not import or call outline(), so listing has no verification. The only search test uses the query 'run', which matches no value node, so value exclusion in default search is never exercised.",
      "reachable_path": "CRIT-3 (spec.md:9) maps to no test in test_graph.py. test_search_finds_definitions (test_graph.py:23-26) searches 'run' against LINES, whose only value node is 'limit' (test_graph.py:5). No test in the file references outline.",
      "actual_failure": "CRIT-3 has no verification artifact, so the listing defect in F1 passes the suite unseen. Fix: CRIT-3 needs a verification artifact in test_graph.py that fails when default search or default listing returns a value node.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/spec.md:9",
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/test_graph.py:5",
        "evals/files/preservation-review/test_graph.py:23-26"
      ],
      "material": true
    }
  ]
}
```
