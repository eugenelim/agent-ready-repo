# Artifactory first-publish gesture evidence

This packet preserves the deferred release evidence identified by
`artifactory-first-publish-gesture`. The workflow cannot be exercised until an
authorized repository owner configures the required GitHub Actions secrets.

## Owner action and receipt

An authorized owner must configure `ARTIFACTORY_URL`, `ARTIFACTORY_USER`, and
`ARTIFACTORY_TOKEN` through the approved GitHub secret-management surface, then
use the next approved tag push to exercise `publish-artifactory`. Do not expose,
inspect, echo, or copy any secret value into this repository or an evidence
transcript.

Record only the tested revision and tag, immutable workflow-run reference,
workflow conclusion, published package coordinate and version, and a redacted
repository-side confirmation that the artifact is retrievable. The packet is
complete when that first upload succeeds, or when the failed run is linked to a
separately owned defect.

