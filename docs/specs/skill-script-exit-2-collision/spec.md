# Spec: Skill script exit-2 collision

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0006, RFC-0013, ADR-0003, RFC-0035, ADR-0026,
  RFC-0084, ADR-0080
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what `done` means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents invoke the installed scripts for Jira, Jira Align, Confluence Publisher,
Confluence Crawler, Figma, Linear, Mermaid Renderer, and Markdown to HTML from
the project-root working directory without guessing that `scripts/` is beneath
that directory. Each skill resolves its installer-supplied skill directory,
canonicalizes and confines the expected entry point beneath that skill's
`scripts/` directory, verifies that the target is a regular file, and passes
the resulting path as one process argument while project-relative content paths
continue to resolve from the project root. A missing, escaping, or unresolved
entry point is reported through a bounded skill installation or invocation
diagnostic; it never masquerades as missing credentials, invalid credentials,
an absent Mermaid CLI, or a renderer dependency failure. The scripts' existing
exit-code meanings, operator-only SSO capture boundary, and credential
protections remain unchanged.

### Affected invocation roster

This table is the canonical enumeration for the spec and plan. “Surfaces” means
every shipped location under the named skill root that can teach, request,
relay, or emit an invocation, including script-emitted help, usage, diagnostics,
and remediation. Bare-relative text retained as inert test input is explicitly
classified and cannot be an expected or recommended command.

| Skill | Entry points | Surfaces |
| --- | --- | --- |
| Jira | `jira.py`, `setup_sso.py` | skill body, loaded references, evals, emitted remediation |
| Jira Align | `jira_align.py` | skill body, loaded references, evals, emitted remediation |
| Confluence Publisher | `publish_page.py` | skill body, loaded references, evals, emitted remediation |
| Confluence Crawler | `crawl_space.py`, `setup_sso.py` | skill body, loaded references, evals, emitted remediation |
| Figma | `figma.py` | skill body, loaded references, evals, emitted remediation |
| Linear | `linear.py` | skill body, loaded references, evals, emitted remediation |
| Mermaid Renderer | `render_mermaid.py` | skill body, loaded references, evals, emitted remediation |
| Markdown to HTML | `render.js` | skill body, loaded references, evals, emitted remediation |

## Boundaries

### Always do

- Use the harness- or installer-supplied directory containing the active
  `SKILL.md` as the trusted base for every script invocation, including
  secondary Atlassian setup commands.
- Canonicalize the trusted base and expected entry point, require a regular file
  whose resolved target remains beneath the resolved skill-owned `scripts/`
  directory, and interpret the child exit code only after that preflight
  succeeds.
- Edit canonical `packs/<pack>/.apm/skills/<skill>/` sources, update each
  affected pack's tests and eval expectations, and regenerate projections
  through the catalogue build.

### Ask first

- Change the numeric meaning or remediation contract of any script exit code.
- Add a shared resolver, helper module, dependency, environment variable, or
  adapter-specific installation-path table.
- Expand the behavior change beyond the eight named skills or alter how their
  project-relative input and output paths resolve.

### Never do

- Never invoke a named entry point through a bare `scripts/<file>` path or pass
  the literal `<skill-dir>` placeholder to a subprocess.
- Never accept a user-supplied base, an environment-derived base, or an entry
  point that resolves outside the installed skill's `scripts/` directory.
- Never treat an interpreter or runtime `cannot open script` failure as evidence
  that credentials or a renderer dependency are missing.
- Never print a resolved absolute install path, home/profile path, environment
  value, protected path, or raw interpreter diagnostic when reporting a missing
  entry point; name only its basename or the generic
  `<skill-dir>/scripts/<entry>` form.
- Never edit generated adapter projections directly, expose credential values,
  add a new module boundary, add a dependency, or add a top-level directory.

## Testing Strategy

- **Invocation resolution and preflight — goal-based source-contract tests.**
  Each affected skill has a pack-local test that checks its invocation rule,
  complete roster of shipped invocation surfaces, canonical containment and
  regular-file preflight, preflight-before-exit interpretation, and absence of
  executable bare-relative script forms. The checks require argv-vector
  invocation where the tool accepts structured arguments and the repository's
  platform-specific quoted fallback where it does not. This is
  configuration-shaped prose, so an exact structural check is more honest than
  a mock subprocess.
- **Agent remediation behavior — goal-based behavior evals.** Each affected
  primitive's eval corpus includes or updates one successful-invocation case
  and one missing-script case. The success rubric requires a resolved skill
  path; the failure rubric forbids credential, re-authentication, Mermaid CLI,
  and renderer-dependency remediation when the entry point itself is absent or
  escapes confinement. It also forbids absolute install/profile paths and raw
  interpreter stderr. Atlassian cases preserve operator-only headed SSO
  capture. Linear gains the pack eval surface required for a non-cosmetic skill
  update.
- **Exit-code preservation — goal-based regression checks.** Existing
  credentialed CLI exit-code tests remain green after their command-text
  assertions adopt the resolved form. A new pack-local Mermaid Renderer test
  pins its exit constants, documented meanings, and `mmdc`-missing remediation.
- **Projection and catalogue integrity — goal-based integration checks.**
  Catalogue lint/verify and self-host drift checks prove the source instructions,
  eval assets, manifests, generated projections, versions, and marketplace
  metadata agree across supported adapters.
- **Project-root behavior — manual QA.** In self-hosted Claude Code and Codex
  sessions, Jira (`--help`), Mermaid Renderer (`--check`), and Markdown to
  HTML exercise the credentialed Python, dependency-reporting Python, and Node
  entry-point classes from a project root with no local `scripts/` directory.
  The other five skills and other adapter projections are covered by
  source-contract, eval, and projection checks rather than manual sessions. A
  missing-entry fixture exercises the bounded resolution diagnostic without
  launching headed SSO or making an external API call.

## Acceptance Criteria

- [x] Every skill in the [affected invocation roster](#affected-invocation-roster)
  defines `<skill-dir>` as the installer-supplied directory containing its
  active `SKILL.md`, replaces the placeholder with that actual path, and
  preserves the project root as the working directory for user content.
- [x] Every executable instruction, loaded reference example, eval expectation,
  and script-emitted help, usage, diagnostic, or remediation in the roster uses
  the resolved skill directory. No executable bare `python scripts/…`,
  `python3 scripts/…`, or `node scripts/…` form remains; any retained
  bare-relative string is explicitly marked and tested as inert input.
- [x] Before an affected command runs, its canonical entry point is a regular
  file whose resolved path remains beneath the canonical skill-owned
  `scripts/` directory. A missing, non-file, or escaping target stops before
  interpreter/runtime launch.
- [x] The resolved entry point is passed as one argv element wherever the
  execution tool accepts structured arguments. A shell-only fallback uses the
  platform-specific quoted form established by Workspace Status when the path
  is safely representable and refuses otherwise. Tests cover spaces, both quote
  characters, `$()`, backticks, and variable-shaped text; no shell expansion
  selects the entry point.
- [x] A script-resolution refusal names only the entry-point basename or the
  generic `<skill-dir>/scripts/<entry>` form. It emits no absolute install,
  home/profile, environment, or protected path and does not relay raw
  interpreter/runtime diagnostics into the agent transcript.
- [x] Jira, Jira Align, Confluence Publisher, Confluence Crawler, Figma, and
  Linear interpret exit 2 as credential or user action only after the resolved
  script passed preflight and ran; a resolution failure never recommends
  `credential-setup`, re-authentication, token regeneration, or SSO capture.
- [x] Jira and Confluence Crawler continue to relay headed
  `check --register` and `setup_sso.py` capture commands for the operator to
  run; an agent never executes them. Automatic recovery remains headless, and a
  missing-script branch never routes into capture.
- [x] Mermaid Renderer interprets exit 2 as an absent `mmdc` only after the
  resolved `render_mermaid.py` passed preflight and ran; a missing renderer
  script never recommends installing Mermaid CLI.
- [x] Markdown to HTML invokes the resolved `render.js` while retaining its
  existing exit-1 dependency behavior; a missing `render.js` is reported as a
  skill installation or invocation error rather than missing Node packages.
- [x] Pack-local source-contract tests and behavior evals cover the success,
  missing, non-file, and escaping-script branches for every roster row. The
  Linear pack has a compliant eval roster for each user-triggered skill and
  pins the `linear` primitive's resolved-path behavior.
- [x] Existing credentialed exit-code tests remain green after only their
  expected command text adopts the resolved form, and a pack-local Mermaid
  Renderer test pins exit 0, 1, and 2 plus the `mmdc`-missing remediation,
  without changing exit constants, credential loaders, API clients, renderer
  logic, or runtime dependencies.
- [x] Atlassian, Figma, Linear, and Converters each receive exactly one patch
  version bump in `pack.toml` and `.claude-plugin/plugin.json`; changelog,
  generated projections, and marketplace metadata match the `.apm` sources.
  The living invocation architecture and knowledge entry describe the corrected
  contract, both related backlog entries are removed, and catalogue lint,
  catalogue verify, self-host drift, targeted pack tests, and eval validation
  pass.

## Assumptions

- Technical: CPython exits 2 before a missing script begins execution (source:
  `python3 /definitely-not-a-skill/scripts/example.py` returned 2 with
  `can't open file`).
- Technical: the collision roster is Jira, Jira Align, Confluence Publisher,
  Confluence Crawler, Figma, Linear, and Mermaid Renderer (source:
  `workspace.toml:476-489` and a focused scan of their source `SKILL.md` files).
- Technical: Markdown to HTML shares the bare-relative path defect, while
  Node's missing-module failure exits 1 rather than colliding with the
  user-action band (source:
  `docs/architecture/binder-publishing/invocation.md`).
- Technical: Workspace Status establishes the repository's resolved
  `<skill-dir>/scripts/…` and discrete-argument invocation pattern (source:
  `packs/core/.apm/skills/workspace-status/SKILL.md:33-44`).
- Process: multi-pack, credential-boundary, and published-interface changes use
  full mode (source: `AGENTS.md:98-109`).
- Process: `.apm` is the skill source of truth, tests are owned by their pack
  and skill, and projections are generated (source: `packs/AGENTS.md` and
  `packs/AGENTS.local.md`).
- Product: this spec closes the seven Python collision cases and Markdown to
  HTML's companion resolution defect together (source: user confirmation
  2026-08-11).
- Product: missing entry points produce skill installation or invocation
  guidance without credential or dependency remediation (source: user
  confirmation 2026-08-11).
- Process: the confirmed boundaries preserve exit codes, forbid shared runtime
  machinery and new dependencies, and require source plus eval coverage
  (source: user confirmation 2026-08-11).
- Process: this is an integration-shaped change with no standalone API or schema
  contract (source: user confirmation 2026-08-11).
- Process: headed SSO capture remains operator-only and automatic recovery
  remains headless (source: RFC-0084, ADR-0080, and
  `docs/specs/jira-check-sso-auto-login/spec.md`).
