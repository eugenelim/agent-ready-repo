```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": 1,
      "finding_id": "QE-1",
      "rule_ref": "quality-engineer Test design #3 (tautological test) and Preservation evidence #35; spec CRIT-2",
      "observation": "test_ordinary_calls_resolve_to_definitions builds its expected value by calling resolve_calls itself (test_graph.py:17-19) and then asserts resolve_calls(graph) == expected (test_graph.py:20), so the expected side is not independent of the code under test and the oracle can never fail.",
      "reachable_path": "build(LINES) yields the call node `limit` and the value node `limit`; resolve_calls (graph.py:37-42) maps each call to its targets; the test compares that result with itself.",
      "actual_failure": "Named mutation: change graph.py:37 to `targets = [n for n in graph.nodes if n.kind in (DEF, VALUE)]`. The ordinary call `limit` then resolves to the value node `limit`, breaking CRIT-2, and the test stays green. CRIT-2 has no evidence that can fail.",
      "affected_acceptance_criteria": ["CRIT-2"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:14-20",
        "evals/files/preservation-review/graph.py:35-42",
        "evals/files/preservation-review/spec.md:7"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "QE-2",
      "rule_ref": "quality-engineer Test design #4 (no exercised exclusion case) and Preservation evidence #35; spec CRIT-3",
      "observation": "test_search_finds_definitions searches for `run` (test_graph.py:26), which matches no value node in LINES, so the default-search value exclusion is never exercised; there is no case searching `limit` with the default flag and no positive control with include_values=True.",
      "reachable_path": "search(graph, \"run\") with include_values defaulting to False (graph.py:45-51); the `include_values or n.kind != VALUE` clause at graph.py:50 is never decisive for any node the query matches.",
      "actual_failure": "Named mutation: reduce graph.py:50 to `if name in n.name`. Default search then returns the value node `limit`, breaking CRIT-3, and the test stays green because the `run` query result is unchanged.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:23-26",
        "evals/files/preservation-review/graph.py:45-51",
        "evals/files/preservation-review/spec.md:8"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "QE-3",
      "rule_ref": "quality-engineer Severity guidance (missing test for stated behaviour) and Preservation evidence #35; spec CRIT-3",
      "observation": "No test covers listing: outline is not imported or called in test_graph.py (import at test_graph.py:3), and outline (graph.py:54-56) lists every node including value nodes, contrary to CRIT-3's default listing exclusion.",
      "reachable_path": "outline(build(LINES)) iterates all graph.nodes with no kind filter and returns ['def run', 'call run', 'value limit', 'call limit'].",
      "actual_failure": "The default listing already emits `value limit`, so CRIT-3 is violated today and the suite stays green; the listing half of CRIT-3 has missing evidence. The code-versus-spec disagreement itself also warrants the adversarial-reviewer conformance lens.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/graph.py:54-56",
        "evals/files/preservation-review/spec.md:8"
      ],
      "material": true
    }
  ]
}
```
