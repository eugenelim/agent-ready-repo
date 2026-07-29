# Frontend Engineering guides

This guide tree covers the `frontend-engineering` pack: how to build web
surfaces that meet the frontend engineering quality floor, how to use the
pack's atomic craft skills, and a reference for all skills and the reviewer.

## Who these guides are for

Engineers who build product web surfaces in HTML, CSS, and JS — from design
handoff to shipped, gate-passing component. The guides assume you are using
the `frontend-engineering` pack with an agent (Claude Code, Codex, Copilot,
Cursor, Kiro, or Gemini).

## What's here

| Section | Contents |
|---|---|
| [Tutorials](tutorials/scaffold-a-component.md) | Step-by-step: scaffold a component from a screen brief to a gate-passing evidence manifest |
| [How-to](how-to/run-an-audit.md) | Run the full frontend-engineering audit on an existing surface |
| [Reference](reference/frontend-engineering.md) | All 9 skills and the reviewer agent — one-line descriptions and when to use each |

## The quality floor

Every surface built with this pack is held to one shared quality floor:

1. **Handle all states** — every applicable state from the 18-state matrix
   must be implemented (loading, empty, error, content, and the rest that
   apply). A surface that only handles the happy path ships broken.
2. **WCAG 2.2 AA** — accessibility is not a feature. The GATES phase runs
   pa11y/axe-core to `wcag21aa` and adds two manual checks for the WCAG 2.2
   criteria automated tools miss (2.4.11 Focus Appearance, 2.5.8 Target Size).
3. **Token discipline** — no hardcoded hex, rgb, or magic pixel values outside
   the `:root` primitive definition block. All colour and spacing through
   `var(--ds-*)`.
4. **Evidence manifest** — completion is not claimed without a manifest. The
   manifest is the record of what was tested and what was found.

## Co-install

For full genre routing in the pre-flight, co-install with `experience-design`:
```
agentbundle install --pack frontend-engineering --scope user
agentbundle install --pack experience-design --scope user
```
