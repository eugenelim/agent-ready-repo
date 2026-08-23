# Tools instructions

Applies to `tools/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

- New additions to `tools/` must be pure-stdlib Python `.py` files. Existing
  `.sh` files stay; this rule applies forward.
- Path triggers in `.github/workflows/docs.yml` must invoke matching scripts as
  `python3 <script>`.
- The repo-only hook implementation and wiring guide is
  [`tools/hooks/README.md`](hooks/README.md). Keep this pointer out of shipped
  pack content because adopters do not receive the maintainer guide.
