---
title: "agentic-skills"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# agentic-skills

Use when a change to an agent skill or equivalent behavior-definition file
alters authority, untrusted-input handling, tools, permissions, sandboxing,
metadata parsing, security-metadata declarations (`metadata.boundaries`,
`metadata.credentialed`), distribution security, or data handling. Ordinary
prompt wording with none of those effects does not load this module.

## Spec-stage

Require minimal permissions, explicit isolation, pinned external references,
and cross-platform preservation of security metadata.

## Implementation checks

- `reason` Review skill prose for malicious or owner-hostile instructions.
- `reason` Match declared tools and capabilities to the skill's purpose.
- `hybrid` Validate skill metadata with safe parsing and schema checks.
- `reason` Pin or refuse external references that become instructions.
- `reason` Require containment for code execution, filesystem, or network use.
- `tool` Confirm version-drift and dependency scanners are wired.
- `reason` Require inventory, audit, and revocation paths.

## Established-helper bypass

Resolve the sanctioned build, metadata-validation, and distribution integrity
paths and flag direct copies or unsafe parsers that bypass them.
