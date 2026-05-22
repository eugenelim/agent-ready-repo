#!/usr/bin/env bash
# Release preflight: refuse to ship dist/agentbundle.pyz unless the git
# tag `contract-v<SPEC_VERSION>` already exists in this repo's history.
# The spec's ship-time AC binds the `.pyz`'s `--version` output to a
# canonical referential anchor in git history; without the tag, a
# downloaded `.pyz` claiming "spec 0.1" has no way to be checked
# against the source of truth.
#
# Exit codes:
#   0 — tag exists; safe to upload the release asset.
#   1 — tag missing; refuse with a one-line stderr telling the operator
#       exactly which tag is required.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

SPEC_VERSION="$(
  PYTHONPATH=packages/agentbundle python -c \
    "import agentbundle; print(agentbundle.SPEC_VERSION)"
)"

if [[ -z "$SPEC_VERSION" ]]; then
  echo "release-check: failed to read SPEC_VERSION from agentbundle" >&2
  exit 1
fi

TAG="contract-v${SPEC_VERSION}"

if ! git rev-parse --verify "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "release-check: missing tag '${TAG}'; tag the commit before uploading dist/agentbundle.pyz" >&2
  exit 1
fi

echo "release-check: ✓ tag '${TAG}' present"
exit 0
