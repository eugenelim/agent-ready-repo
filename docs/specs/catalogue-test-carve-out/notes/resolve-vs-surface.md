# Resolve-vs-surface record

Run: `4240730b-bec0-44e1-9c51-ecaac560dadd`

| Item | Disposition | Evidence or next action |
| --- | --- | --- |
| Remote base freshness unavailable | Resolved | Human explicitly authorised the local checkout as the baseline because this workspace cannot reach `origin`. |
| Work-loop state files cannot be written by the agent shell | Resolved | Human runs state-mutating work-loop commands; the agent verifies state read-only before continuing. |
| Ownership of contested test classes | Resolved | Human approved all seven consolidated T1d dispositions on 2026-08-09 before relocation. |
| `contracts/adapter.toml` ownership | Resolved | Engine input and published mirror; all affected rows remain engine-owned. |
| Adversarial archive/path findings | Resolved | Added the missing workspace-status destination gate, rejected archive residue and drive-relative aliases, made source-to-sdist completeness byte-exact, narrowed skip policy, and made initialized conformance consume bundled contracts. The iterated adversarial pass returned clean. |
| Security: generic construction-skip policy | Resolved | `STUB` skips are accepted only from six byte-pinned pre-existing construction-test modules; a new module or any edit to those modules fails the release gate until the explicit policy is reviewed. |
| Security: conformance hard-link smuggling | Resolved | Both source packaging and self-hosted init now use one confined regular-file reader that rejects symlinks, special files, hard links, path escape, and discovery/open inode changes; both shipping routes have construction tests. |
| Security: unaudited build backend | Resolved | The SCA leg extracts `build-system.requires` directly from both package `pyproject.toml` files and feeds them to `pip-audit`; missing declarations fail closed. |
| Security: materialized cache residue | Resolved | Source-copy materialization now prunes caches, bytecode, and egg metadata independently of the test-tree exclusion policy; a conformance-cache construction test pins the boundary. |
| Security: validated-file read bypasses | Resolved | Default and source-flavour archive paths plus self-hosted init all snapshot through the shared confined regular-file reader, and manifests/validation parse those captured bytes rather than reopening source paths. |
| Quality: synthetic-only sdist proof | Resolved | Added a real `python -m build --sdist --no-isolation` construction test that drives `check_sdist` through extraction, completeness comparison, collection, and execution. |
| Quality: direct-API-only init proof | Resolved | Added public CLI lifecycle tests for bare init and self-hosted external/vendored init, each followed by execution of the materialized conformance suite. |
| Quality: real-sdist CI prerequisites and timeout | Resolved | Moved the export-boundary step after the existing credbroker install and raised the job timeout to 25 minutes, above the gate's 120-second collection plus 900-second execution bounds and setup time. |
