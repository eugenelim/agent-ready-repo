# Pre-existing enterprise AgentBundle full-suite evidence

This packet preserves the deferred verification identified by
`pre-existing-enterprise-agentbundle-full-suite`. It does not amend the frozen
acceptance criteria in the local-CI or catalogue-verifier specifications.

## Why local verification is not sufficient

The managed development profile blocks two fixture classes before the behavior
under test is reached: temporary trust-store CA material and protected
key-material paths. The affected failures reproduce outside the initiative's
diff. Retrying in the same profile cannot settle the acceptance criteria, and
the production credential policy and tests must not be weakened to make that
profile pass.

The cold-start failure set recorded on 2026-08-16 was:

- pip/`ensurepip` temporary trust-store setup:
  `test_credentials_wheel.py::test_agentbundle_credentials_is_removed_from_installed_wheel`
  and
  `test_editable_source_detection.py::test_editable_detection_against_real_install`;
- protected key-material fixture reads:
  `integration/test_trust_fallback_tls.py`, `unit/test_system_trust.py`, and
  `unit/test_https_catalogue.py::test_build_opener_custom_ca_bundle`.

## Evidence request

An authorized operator must run `python3 -m pytest packages/agentbundle/tests/ -q`
in CI or another supported profile that permits both isolated fixture classes.
Record:

- the immutable run reference and tested revision;
- the command and supported profile or runner class;
- the final test summary and exit status; and
- any remaining failures, without copying credentials or private key material.

This packet is complete when the full suite passes in that supported profile,
or when any product defect exposed there has a separately owned canonical work
item. Local cleanup-sensitive cases remain for CI or a supported profile.
