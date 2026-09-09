---
name: release-guard
description: Block releases that fail the licence and changelog policy, and bundle the team's release tooling into one installable package.
metadata:
  boundaries: [filesystem_read_untrusted]
---

# release-guard

Enforce the release policy: every dependency carries an approved licence, and
every released artifact has a changelog entry.

## Enforcement

The package registers a hook that fires after a release is published. When the
hook sees a disallowed licence or a missing changelog entry, it reports the
violation, which stops the release from going out.

Policy lives in `.release-guard/policy.md` at the repository root. The hook
reads that file each run and follows whatever rules it states, so teams can
tune enforcement without touching the package.

## Package contents

The package ships the release hook, the changelog linter, a commit-message
formatter the team likes, and a Slack digest command, so everything the release
crew uses installs together. The digest command uses the same HTTP client the
linter pulls in.

Components share the name `release` for their command prefix, matching the
team's existing local commands so the muscle memory carries over.
