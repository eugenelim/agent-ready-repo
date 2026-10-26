# Direct lifecycle capability inspection

- **Status:** Open
- **Kind:** defect
- **Parent intent:** intent:direct-skill-lifecycle

## Summary

Re-read what an installed direct skill declares: allowed-tools, metadata.boundaries, metadata.credentialed, the SKILL.md digest, and every payload digest, per skill. Probed 2026-09-01: show, list-installed --format json, and the state file each carry none of them, so an adopter who consented at install has no route back to what they agreed to. The show contract sets additionalProperties false over a closed key set docs/specs/okf-catalogue-discovery owns, so that spec needs amending alongside.
