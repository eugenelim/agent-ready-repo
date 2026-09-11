# Portable Agent Plugin projection

- **Status:** Draft
- **Level:** feature

## Outcome

A deterministic portable Agent Plugin package projects existing canonical skills and validated extension namespaces after the route contract exists.

## Opportunity

The catalogue has no portable Agent Plugin distribution output.

## Coverage 2026-09-10 — nine of fifteen, and not the interesting nine

Measured against the pack tree, **user-scope packs only**. Repo-scope packs are
out of scope for every distribution route and are not counted here.

**Ships (9):** `agent-skill-engineering`, `atlassian`, `contracts`,
`converters`, `figma`, `github`, `linear`, `product-documentation`,
`product-strategy`.

**Refused (6):**

| Pack | Why refused |
| --- | --- |
| `product-engineering` | 3 sub-agents |
| `desk-research` | 2 sub-agents |
| `architect` | 1 sub-agent |
| `experience-design` | 1 sub-agent |
| `frontend-engineering` | 1 sub-agent |
| `credential-brokers` | 3 shared-libs, 4 adapter-root-bins, 1 user-libs |

Five of the six are refused for one reason: **Agent Plugins 1.0.0 has no agent
component type.** Confirmed against the standard itself, not inferred from our
route — v1 defines exactly two component types, Agent Skills and MCP servers,
and deliberately so: both "already have specifications and meaningful adoption
of their own, and Agent Plugins does not attempt to redefine them". The TSC is
AWS, Cursor, Microsoft, OpenAI and Vercel.

So the route's `agent = dropped` and its refusal to emit a partial artifact are
faithful to the standard, not a gap in our implementation. Emitting a
sub-agent-bearing pack without its sub-agents would be the defect.

### What this means for investment

**We do not invest in an inferior surface.** The refused set is not a random
six: it contains three of the four discipline packs and the architecture pack —
the ones whose methods are richest and whose audience this catalogue most wants
to reach. A route that carries the thin packs and drops the thick ones does not
serve the adopter we are aiming at.

This intent therefore stands as **portability groundwork, not a distribution
bet**. It is worth having because the package format is vendor-neutral and the
projection is deterministic; it is not worth extending, profiling, or
marketing until the standard grows an agent component type.

**Revisit when:** Agent Plugins adds an agent component type, or a named
adopter needs a pack that is already in the shipping nine.

## Assumptions

- This slice introduces no new canonical primitive; existing direct agentbundle skill installation remains the parity baseline.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
