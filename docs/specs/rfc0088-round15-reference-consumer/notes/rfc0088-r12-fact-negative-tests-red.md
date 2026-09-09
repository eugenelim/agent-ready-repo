# RFC-0088 round-12 fact-negative-test evidence

This packet preserves the deferred evidence identified by
`rfc0088-r12-fact-negative-tests-red`. The named
`r12-fact-negative-tests.py` apparatus is not tracked in the current repository;
the round-15 specification identifies it as part of an out-of-tree evidence
tree. It must be supplied or reacquired from its authoritative archive rather
than reconstructed from references.

## Evidence request

An authorized operator must provide the archived out-of-tree apparatus and a
supported clean evidence environment. Run the unchanged apparatus against both
the current revision and the specification's clean default-checkout comparator.
Record:

- provenance and integrity information for the supplied apparatus;
- both tested revisions and the environment or runner class;
- the exact failing `MISSED` or `NOT-RESTORED` cases and exit statuses; and
- the differential that identifies whether branch content, platform, or
  persistent state explains the failure.

This packet does not claim that the negative tests pass. It is complete only
when the differential is recorded and any current-branch defect has a
separately owned canonical work item.

