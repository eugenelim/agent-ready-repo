# Manual QA — installed skill entry points

Date: 2026-08-11

This record deliberately uses generic `<skill-dir>` notation. Resolved install,
home, profile, and protected paths are not retained.

## Project-root class probes

The shell was rooted at a project that has no top-level `scripts/` directory.

| Class | Command recorded in generic form | Exit | Result |
| --- | --- | ---: | --- |
| Credentialed Python | `python <skill-dir>/scripts/jira.py --help` | 0 | Help named the resolved Jira entry and contained neither a bare-relative command nor the literal `<skill-dir>`. |
| Dependency-reporting Python | `python <skill-dir>/scripts/render_mermaid.py --check` | 0 | The installed entry ran and reported `OK: mmdc is on PATH`. |
| Node | `node <skill-dir>/scripts/render.js --help` | 0 | Help named the resolved renderer entry, contained no literal `<skill-dir>`, and ran before loading optional Node packages. |

The three probes were repeated successfully in the final verification run from
the active Codex project-root session after `FORCE=1 make build-self`. A Claude
session runtime was not exposed in this environment, so no Claude result is
claimed.

## Missing-entry classes

A self-hosted Claude/Codex harness that can install a disposable skill
and remove its entry point is not exposed in this environment. Directly asking
Python or Node to open an absent file is not a valid substitute: it bypasses the
agent-side preflight and recreates the exit-code collision this change removes.

The three missing-entry classes are therefore evidenced by their committed
behavior eval cases and pack-local source-contract tests:

| Class | Expected bounded outcome |
| --- | --- |
| Credentialed Python | Name only the unavailable entry; no credential, token, or SSO-capture remediation. |
| Dependency-reporting Python | Name only the unavailable entry; do not recommend installing `mmdc`. |
| Node | Name only the unavailable entry; do not recommend installing Node packages. |

These cases also reject absolute/profile paths and raw interpreter/runtime
stderr. This limitation is explicit rather than claiming a manual agent-session
result that the available runtime cannot produce.
