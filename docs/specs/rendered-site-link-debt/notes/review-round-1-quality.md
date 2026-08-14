# Quality implementation review — round 1

## Finding

- **Concern:** exit-2 errors raised while classifying or resolving an href did
  not name the source page or raw href, making CI failures unnecessarily hard
  to reproduce.

## Resolution

Per-link audit errors now add the source page and a repr-escaped href before
propagating to the CLI. A focused malformed-percent test pins the diagnostic
context and exit code.

