```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": 1,
      "finding_id": "QE-1",
      "rule_ref": "quality-engineer review check 35 (preservation evidence: expected side independent of the code under test, oracle fails on a named mutation); check 3 (tautological tests)",
      "observation": "test_ordinary_calls_resolve_to_definitions builds its expected dict by calling resolve_calls(graph) itself, then asserts resolve_calls(graph) == expected. The expected side is the code under test, so the assertion can never fail. Nothing checks that a call resolves to no value node.",
      "reachable_path": "Mutate graph.py:37 to `targets = [n for n in graph.nodes if n.kind in (DEF, VALUE)]`. With LINES, `call limit` then resolves to [Node('limit', 'value')], which breaks CRIT-2. Both sides of the assertion change together, so the test stays green.",
      "actual_failure": "CRIT-2 has tautological evidence only. A regression that lets ordinary calls resolve to value nodes ships with a green suite. Fix: the CRIT-2 artifact must state an expected result independent of resolve_calls (for `call limit`, no value node; for `call run`, only the def node) and must go red under the named mutation.",
      "affected_acceptance_criteria": ["CRIT-2"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:14-20",
        "evals/files/preservation-review/graph.py:35-42",
        "evals/files/preservation-review/spec.md:8"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "QE-2",
      "rule_ref": "quality-engineer review check 35 (preservation evidence: oracle fails on a named mutation; feature-only evidence); check 4 (no positive control for the excluded case)",
      "observation": "test_search_finds_definitions searches for `run`, and no value node matches `run`. The default exclusion of value nodes is never exercised. The test only shows that search finds definitions and calls, which is feature-only evidence.",
      "reachable_path": "Delete the `(include_values or n.kind != VALUE)` clause at graph.py:50. search(graph, 'run') still returns ['def', 'call'], so the test stays green, while search(graph, 'limit') would now return the value node.",
      "actual_failure": "The search half of CRIT-3 has evidence that cannot fail when value nodes leak into default search. Fix: the CRIT-3 search artifact must query a name that matches a value node, assert the value node is absent by default, and include a positive control that the node appears with include_values=True. It must go red under the named mutation.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:23-26",
        "evals/files/preservation-review/graph.py:45-51",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "QE-3",
      "rule_ref": "quality-engineer review check 35 (a family the preservation criterion names with no current result)",
      "observation": "CRIT-3 names two families, default search and listing. No test touches listing: test_graph.py never imports or calls outline. outline at graph.py:54-56 lists every node, value nodes included, so with LINES it returns `value limit`.",
      "reachable_path": "outline(build(LINES)) returns ['def run', 'call run', 'value limit', 'call limit']. The value node is listed by default, and no test result exists that would show it.",
      "actual_failure": "The listing family of CRIT-3 has no current result. Its present behaviour disagrees with the criterion, and the suite stays green. Fix: CRIT-3 must have a current listing result that fails while default listing includes value nodes. The code or the spec must then be brought into agreement.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/graph.py:54-56",
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    }
  ]
}
```
