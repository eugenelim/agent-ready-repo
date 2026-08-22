# architect

Understand the architecture you have before deciding what to change. Start with:

> Assess architecture and provide an action plan.

The agent first frames the decision, maps the implemented system, and shows an
evidence ledger and attention heat map. You correct the map before it drills
down, then redirect or accept the proposed hotspots. A standard run finishes
with evidence-backed findings, strengths, unknowns, and dependency-aware action
waves. Inspection is read-only by default; private knowledge, executable checks,
and file writes require separate approval.

```text
Assessment target   billing platform
Intent              hardening / risk reduction
Mode                standard
Current state       API + workers + ledger + payment provider
Evidence coverage   source ✓ tests ✓ CI ✓ operations partial

Map checkpoint — correct a boundary, or say “continue”.
```

## Start with the outcome you need

| Say this | What you get |
| --- | --- |
| “Assess architecture and provide an action plan.” | A standard current-state assessment, bounded investigations, and traced action waves |
| “Give me a quick architecture survey; stop before drill-down.” | A correctable map, evidence coverage, attention heat, and recommended investigations |
| “Do a deep launch-readiness assessment; ask before runtime access.” | A standard assessment extended with separately authorized operational or experimental evidence |
| “How should we design the replacement?” | A Stage-0 concept, full design doc, and convergence through `architect-design` |
| “Draw the current deployment topology.” | A self-checked Mermaid diagram through `architect-diagram` |
| “Review this assessment report.” | An evidence-and-methodology critique through `architect-review` or the cold-context reviewer |

The generated `architecture-lenses-reference` skill is an internal knowledge
router. You do not invoke it directly; assessment, design, and review load only
the concepts their current question needs.

## What the assessment reads and changes

The default pass may read documentation, source, tests, manifests, CI/CD,
deployment and infrastructure definitions, schemas, configuration, operations
files, and current local Git history. Its optional profiler executes no
repository code, excludes protected path classes before evidence creation,
shares finite entry/byte/path/time budgets across every phase, and emits
signals, not an architecture score.

It does not run builds, tests, migrations, deploys, network calls, private
enterprise queries, or experiments without asking. Saving is also optional. If
you approve it, the assessment lands as
`<architecture output_dir>/<topic-slug>/assessment.md`.

## Install

```bash
agentbundle install --pack architect --scope user <catalogue>
```

Adapters: `claude-code`, `codex`, `copilot`, `kiro-ide`, `kiro-cli`, `cursor`,
and `gemini`. Default scope: user.

## Go deeper

- [Assess a repository](../../guides/architect/how-to/assess-a-repository.md)
- [Architecture assessment reference](../../guides/architect/reference/architecture-assessment.md)
- [Your first architecture session](../../guides/architect/tutorials/architect-first-session.md)
- [Shape an architecture concept](../../guides/architect/how-to/shape-an-architecture-concept.md)
- [Diagram a system](../../guides/architect/how-to/diagram-a-system.md)
- [Review an architecture artifact](../../guides/architect/how-to/review-an-architecture-artifact.md)
- [Establish a reference architecture](../../guides/architect/how-to/establish-reference-architecture.md)

Maintainers: [design and invariants](DESIGN.md).
