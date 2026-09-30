# Artifactory first-publish gesture evidence

This packet preserves the deferred release evidence identified by
`artifactory-first-publish-gesture`. It covers this upstream repository's
GitHub-hosted wheel release workflow. It is not the provider-neutral setup
contract for downstream catalogue publishers.

## Owner action and receipt

An authorized owner must configure `ARTIFACTORY_URL`, `ARTIFACTORY_USER`, and
`ARTIFACTORY_TOKEN` through this repository's approved GitHub secret-management
surface, then use the next approved tag push to exercise
`publish-artifactory`. The username is required by this workflow's Twine client;
it is not a general catalogue-publication requirement. Use a restricted service
identity, not an individual developer credential. Do not expose, inspect, echo,
or copy any secret value into this repository or an evidence transcript.

Downstream organizations should map the same controls to their CI provider's
protected secret store and release lock. GitLab CI uses protected, masked, and
hidden CI/CD variables plus protected release tags. Jenkins and other runners
use their equivalent protected credentials and deployment serialization.

Record only the tested revision and tag, immutable workflow-run reference,
workflow conclusion, published package coordinate and version, and a redacted
repository-side confirmation that the artifact is retrievable. The packet is
complete when that first upload succeeds, or when the failed run is linked to a
separately owned defect.
