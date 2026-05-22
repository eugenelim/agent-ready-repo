# packages/

Shared libraries consumed by apps and other packages. One directory per
package; each owns its own build/test surface.

- [`_example/`](_example/) — template package, copy this to start a new
  one. Use the `new-package` skill (`monorepo-extras` pack) to scaffold.

A package's `AGENTS.md` (if present) describes per-package rules that
override or extend the root `AGENTS.md`. Cross-package work — anything
that touches more than one package — goes through the
[`work-loop`](../.claude/skills/work-loop/SKILL.md) skill.
