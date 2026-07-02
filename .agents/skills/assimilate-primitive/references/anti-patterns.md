# Anti-pattern catalogue — steer to our shape, or reject

External primitives often carry misuse patterns this repo forbids. Assimilation
**detects** each, then **reshapes to convention or rejects** — naming the
anti-pattern and citing the rule it steers toward. Never launder misuse in.

The "right shape" authority: the repo's *Authoring skills* conventions, the
agent-authoring conventions, and `AGENTS.md`.

## 1. A script or hook that triggers a skill or agent — HARD anti-pattern

Deterministic scripts stay deterministic; **skills activate by description**,
**agents are dispatched by the loop** — neither is invoked from a script or hook.

- *Tell:* a `scripts/*.py` or hook that shells out to `claude`/an agent CLI, or
  parses a SKILL.md to "run" it, or a hook whose job is "call skill X".
- *Steer:* split the deterministic part into a real script (data in / data out),
  and let the skill's own activation surface handle invocation. If the primitive
  exists *only* to auto-trigger another primitive, **reject** it.

## 2. An agent used the wrong way

- *Self-review* — an agent that reviews or grades its own output (agents don't
  mark their own homework). Steer to the reviewer-after-implementer pattern, or
  reject.
- *Over-broad tool grant* — an agent granted `*` or write/exec tools it doesn't
  need. Narrow to the minimal surface its job requires.
- *Skill-vs-agent confusion* — judgment/authoring work modeled as an agent when
  it should be a skill, or a read-only forked-context review modeled as a skill
  when it should be a subagent. Re-home to the right primitive type.

## 3. A "skill" that is a flooding prompt

A SKILL.md that dumps a wall of instructions instead of a terse, activated
procedure with progressive disclosure. Reshape per the craft checklist (detail →
`references/`, mechanical → `scripts/`), or reject if it can't be made terse.

## 4. Other tells worth catching

- Hardcoded absolute paths / machine-specific assumptions → parameterize or reject.
- A hook doing heavy logic that belongs in a script or skill.
- Duplicated activation surface that collides with an existing skill (see the
  craft checklist's collision check).

When in doubt, prepare the finding (what you saw, the convention it violates,
the steer or the reject) and let the operator decide — guided, not flooded.
