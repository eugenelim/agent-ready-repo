# Direct lifecycle uninstall skill

- **Status:** Open
- **Kind:** defect
- **Parent intent:** intent:direct-skill-lifecycle

## Summary

RFC-0098 D4/D6 mandate uninstall --skill <name> for a direct row, routed to the pack-keyed file-ownership removal path and mutually exclusive with --pack. The CLI has no --skill and requires --pack, so that form does not exist; removal works only via uninstall --pack <identity> --yes. No removed criterion carried this. It also owns the removal completeness direct-skill-lifecycle F8 measures: a file a later revision drops stays on disk unowned, and ownership-keyed removal alone cannot reach it.
