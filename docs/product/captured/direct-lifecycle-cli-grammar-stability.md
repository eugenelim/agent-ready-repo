# Direct lifecycle cli grammar stability

- **Status:** Open
- **Kind:** defect
- **Parent intent:** intent:direct-skill-lifecycle

## Summary

Install, validate, and list-installed grammar clauses that left with AC7 and AC9: list-installed adds no new flag and --no-check, --offline, and --check-drift keep their meanings; a catalogue row whose drift was never computed renders an em dash rather than a 0; and the exit-2 set for bare upgrade, bare primitive upgrade, bare uninstall, bare install, conflicting pack/profile, pack/profile with a direct source, and upgrade --pack P --scope local. AC7/AC9 at c794be99c are the authority.
