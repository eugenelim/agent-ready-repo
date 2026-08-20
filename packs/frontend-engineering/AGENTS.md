# AGENTS.md — frontend-engineering pack

Applies to `packs/frontend-engineering/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

The `frontend-engineering` pack installs 9 skills and a `frontend-reviewer` agent
for HTML/CSS/JS work. The guide tree for all skills lives in
[`guides/frontend-engineering/`](../../guides/frontend-engineering/) —
tutorials, how-to, and a reference page covering all skills and the reviewer.

For full genre routing in the frontend pre-flight (the `experience-design` co-install
that supplies `conversion-design`, `documentation-design`, `analytical-design`, and the
other XD genre skills), `experience-design` must be installed alongside this pack.
The main `frontend-engineering` skill records a named skip when `experience-design`
is absent — the skip is documented in the spec, not silently omitted.
