# Credential broker capture and refresh have bounded modes and errors

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/jira-check-sso-auto-login AC35](../../specs/jira-check-sso-auto-login/spec.md)
- **Authority:** [spec/skill-script-exit-2-collision review](../../specs/skill-script-exit-2-collision/spec.md)

## Outcome

Credential-broker capture and refresh expose explicit operator modes and bounded caller-facing failures.

## Opportunity

`_capture` represents three valid modes with two Boolean axes, while interactive refresh inherits child-process stderr before `credbroker` can translate it.

## What this absorbs

### sso-capture-mode-enum

`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py:1130` still declares `_capture` with `persist: bool,` and the `headless` Boolean axis, giving four combinations for three valid modes and refusing the meaningless fourth. Introduce `operator-register`, `ephemeral-register`, and `automatic-refresh` modes. Separate browser driving from profile writes. **BLOCKER:** this change touches protected `packs/credential-brokers/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. That trailer applies at commit time.

### credbroker-refresh-stderr-bounding

`packages/credbroker/credbroker/_sso.py:363` documents that refresh stderr stays inherited, and the broker still inherits child stderr when it spawns the interactive refresh path. Capture and translate refresh stderr before the caller receives the failure, while preserving headed operator output. This prevents paths and engine detail from escaping the bounded error. **BLOCKER:** this change touches protected `packs/credential-brokers/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. That trailer applies at commit time.

## Assumptions

- The protected-tree trailer requirement applies to the landing commit, not to this Draft intent.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
