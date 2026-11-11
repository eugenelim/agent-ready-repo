```json
{
  "terminal_status": "findings",
  "findings": [
    {
      "schema_version": 1,
      "finding_id": "QE-1",
      "rule_ref": "quality-engineer #35 preservation evidence; #3 tautological tests",
      "observation": "test_ordinary_calls_resolve_to_definitions builds its expected mapping by calling resolve_calls(graph) itself, so the expected side is not independent of the code under test and the assertion compares resolve_calls with itself.",
      "reachable_path": "pytest test_graph.py::test_ordinary_calls_resolve_to_definitions -> build(LINES) -> resolve_calls(graph) used for both expected and actual; LINES includes `value limit` and `call limit`, the exact case CRIT-2 protects.",
      "actual_failure": "Mutating graph.py:37 to select targets with n.kind in (DEF, VALUE) makes `call limit` resolve to the value node `limit`, breaking CRIT-2, and the test stays green; no mutation of resolve_calls can make it fail.",
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
      "rule_ref": "quality-engineer #35 preservation evidence; #4 empty-set and missing control assertions",
      "observation": "test_search_finds_definitions searches for `run`, and no value node in LINES matches `run`, so the value-exclusion filter in search is never exercised; the test is feature-only evidence for CRIT-3.",
      "reachable_path": "pytest test_graph.py::test_search_finds_definitions -> search(graph, \"run\") with default include_values=False -> graph.py:50 filter `n.kind != VALUE` never meets a matching value node.",
      "actual_failure": "Deleting `and (include_values or n.kind != VALUE)` at graph.py:50, so default search returns value nodes and breaks CRIT-3, leaves the test green.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:5",
        "evals/files/preservation-review/test_graph.py:23-26",
        "evals/files/preservation-review/graph.py:45-51",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    },
    {
      "schema_version": 1,
      "finding_id": "QE-3",
      "rule_ref": "quality-engineer #35 preservation evidence (missing); severity guidance: missing test for stated behaviour",
      "observation": "No test exercises listing: outline is not imported or called in test_graph.py, and outline at graph.py:54-56 returns every node including value nodes, which disagrees with CRIT-3's default-listing exclusion.",
      "reachable_path": "outline(build([\"def run\", \"value limit\"])) returns [\"def run\", \"value limit\"]; test_graph.py imports only CALL, VALUE, build, resolve_calls, search.",
      "actual_failure": "The listing half of CRIT-3 has no evidence, and the current code already lists value nodes by default, so the regression ships with all tests green.",
      "affected_acceptance_criteria": ["CRIT-3"],
      "evidence_refs": [
        "evals/files/preservation-review/test_graph.py:3",
        "evals/files/preservation-review/graph.py:54-56",
        "evals/files/preservation-review/spec.md:9"
      ],
      "material": true
    }
  ]
}
```
