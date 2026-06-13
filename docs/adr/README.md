# Architecture Decision Records

> Immutable records of architectural decisions. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr)
> for what goes here and what doesn't.

| #    | Title                                       | Status   |
| ---- | ------------------------------------------- | -------- |
| 0001 | [Adopt AGENTS.md and doc hierarchy](0001-adopt-agents-md-and-doc-hierarchy.md) | Accepted |
| 0002 | [Install-scope is a per-pack default + allowance, not a per-item or adopter-only choice](0002-install-scope-per-pack-default-and-allowance.md) | Accepted |
| 0003 | [Four-broker contract for credentialed skills; in-process shim + adapter-root subprocess as the two v1 transports](0003-credential-broker-contract.md) | Accepted |
| 0004 | [Per-IDE direct writes are the repo-scope install default; dist-tree is opt-in](0004-repo-scope-per-adapter-projection.md) | Accepted |
| 0005 | [Supervisor mode — topological-order default, gated parallel writes](0005-supervisor-topological-default-and-write-gate.md) | Accepted |
| 0006 | [Doc drift — prevented by construction + judgment for adopters; mechanically gated only as catalogue governance](0006-doc-drift-construction-and-judgment.md) | Accepted |
| 0007 | [Ship the doc-drift spec-metadata lint to adopters as a work-loop skill script](0007-ship-doc-drift-lint-as-work-loop-skill-script.md) | Accepted |
| 0008 | [Contract authoring integrates via an agnostic, convention-first seam (not a core merge); contracts live in a repo-level tree](0008-contract-authoring-seam.md) | Accepted |
| 0009 | [A product-brief layer sits between roadmap and spec; the low-level design lives in the plan with a derived (never baked) stack](0009-product-brief-layer-and-plan-owned-lld.md) | Accepted |
| 0010 | [A normative `reference.md` is the repo's golden path — template-instantiated on demand, never a core seed, populated by repo context](0010-reference-architecture-foundation.md) | Accepted |
| 0011 | [Greenfield inception is a new `init-project` flow that composes existing skills — value gate over fed-in discovery, recorded foundation, then a walking skeleton; not an autonomous generator](0011-greenfield-inception-front-door.md) | Accepted |
| 0012 | [Split `kiro` into `kiro-ide` and `kiro-cli` with `kiro` as a deprecated alias, and activate `kiro-ide-hook` at contract v0.9](0012-kiro-adapter-split.md) | Accepted |
| 0013 | [Copilot is a full-parity, user-scope-capable adapter](0013-copilot-full-parity-user-scope-adapter.md) | Accepted |
| 0014 | [Rigor scales with risk — `work-loop` light/full modes](0014-rigor-scales-with-risk-work-loop-modes.md) | Accepted |
| 0015 | [Cursor is a full-parity distribution adapter](0015-cursor-full-parity-distribution-adapter.md) | Accepted |
| 0016 | [Gemini CLI is a full-parity distribution adapter](0016-gemini-cli-full-parity-adapter.md) | Accepted |
| 0017 | [Adopt Bandit + pip-audit + Semgrep as the repo's SAST/SCA gate](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) | Accepted |
| 0018 | [Shift security review left and deliver its depth via an orchestrator-loaded progressive-disclosure skill](0018-shift-security-review-left-progressive-disclosure.md) | Accepted |
| 0019 | [Product shaping is a recursive level-tagged `intent` tree; a brief is a feature-intent projected onto one repo; contracts mature by stage](0019-product-intent-ontology-and-brief-projection.md) | Accepted |

## Adding a new ADR

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr)

# Create from template
cp .claude/skills/new-adr/assets/adr.md docs/adr/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-adr "<title>"` (defined in `.claude/skills/new-adr/SKILL.md`).
