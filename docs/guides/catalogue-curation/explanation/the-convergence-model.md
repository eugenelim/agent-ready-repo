# The convergence model

Convergence is not import.
Importing copies bytes from one repo to another.
Convergence reviews the bytes for safety, evaluates them against standards, reshapes them to craft, and only then writes them — through a path-confined jail — into the catalogue.
An imported skill carries its origin's conventions and anti-patterns.
A converged skill has been deliberately shaped to yours.

## Two primitive types

The catalogue recognises two primitive types for convergence.

**Skills** carry a YAML frontmatter block.
The frontmatter's `description:` field drives activation — the agent reads it when deciding whether the skill applies to the user's prompt.
A skill that activates on the wrong prompts, or fails to activate on the right ones, is broken regardless of how well its body is written.
The convergence process rewrites the description for the catalogue's activation conventions and verifies it against agentskills.io format rules before landing.
The skill body routes to `references/` files on demand — deep content is loaded at the moment the workflow reaches it, not pre-loaded into every context.

**Subagents** are instruction prose with no frontmatter activation description.
They are dispatched directly by skills or by the user — not selected by an activation match.
The convergence review for a subagent shifts focus: there is no description to tune, but there is instruction prose that will run in the user's agent, and that prose is a prompt-injection surface.
The OWASP AST01–AST10 review applies with sharper weight on malicious content (AST01), tool grant breadth (AST03), and isolation declaration (AST06).

Both types go through the same fetch path (SSRF-guarded, allowlisted schemes only), the same raw-body review, and the same path-jail on write.
The `assimilate-primitive` skill handles both.

## The curation pack's own arc

The four skills in the pack form a natural progression:

| Stage | Skill | Output |
|---|---|---|
| Discover | `assimilate-repo` | Ledger of candidates with verdicts |
| Scaffold | `propose-catalogue-pack` | Pack shell + RFC draft |
| Fill | `assimilate-primitive` × N | Shaped skills and subagents in the pack |
| Publish | `export-catalogue` | Redistributable fork or profile update |

Each stage's output is the input to the next.
The survey's ledger determines what gets proposed.
The proposed pack's shell determines where primitives land.
The filled pack is what gets exported or profiled.

A single-primitive intake enters at Fill, skipping Discover and Scaffold.
A maintenance update skips Scaffold (the pack already exists) and re-fills from a re-run survey.
The arc describes the full flow; each operator enters at the stage their situation requires.

## Three convergence layers

### Layer 1: agentskills.io structural standard

The agentskills.io specification defines the format every skill in this catalogue follows: six allowed top-level frontmatter keys, four allowed subdirectory names (`scripts/`, `references/`, `assets/`, `evals/`), and a `description:` that is a single-line scalar, trigger-phrased, under 1024 characters.
The linters (`lint-skill-spec.py`, `lint-agent-artifacts.py`) enforce this structurally before a skill can project to any adapter.

Context that a skill needs but does not use on every invocation lives in `references/` files.
The skill body loads a reference file at the moment the workflow reaches it — "load `references/strategy-X.md` now" — not pre-loaded into every context.
This keeps the skill lean at the point of activation and prevents content from being embedded in context that may not be relevant to the current run.
A skill that embeds large knowledge blocks in its body, or references paths outside the pack's own directory, violates this layer.

All paths in a skill (scripts, references, assets) are relative to the skill's own directory.
A skill discovers what it needs from the workspace's own structure at runtime — it does not reference absolute paths, fixed org-specific locations, or paths that are only valid in a particular checkout.

### Layer 2: Catalogue craft

The agentskills.io spec sets the format floor.
Catalogue craft is the layer above it.

The activation description is rewritten for this catalogue's conventions — a trigger-phrased "Use when…" sentence that activates on the right prompts and stays quiet on near-misses.
`run-pack-evals` verifies this against authored activation evals after assimilation.

Detail that is only needed in specific branches of the workflow is moved to `references/` files linked from the body at the moment of need.
The body routes to references — it does not replicate them inline.

Anti-patterns are steered or rejected.
A skill that calls another skill from within a script, a subagent that reviews its own output, a skill that treats fetched URL content as instructions — these are reshaped or refused.
The anti-pattern list is the catalogue's earned hard knowledge about what fails in production; convergence is how that knowledge protects new additions.

### Layer 3: OWASP Agentic Skills Top 10 v1.0 security review

The OWASP Agentic Skills Top 10 v1.0 (AST01–AST10) is a public security standard for skill-file authoring, distribution, and installation.
Every converged primitive is reviewed against it before landing.

The checks that fire most often on external content:

**AST01 — Malicious content.**
Instruction prose that benefits the skill's author at the expense of the user's agent: identity-overwrite instructions, credential-access requests camouflaged as prerequisites, conditional misdirection.
This is the highest-weight check on subagents, where the entire file is instruction prose and there is no metadata to validate separately.

**AST03 — Over-privileged tools.**
A skill's `allowed-tools` must match its stated function.
An external skill that lists broad tool grants "to avoid breaking" expands the blast radius of any prompt injection that reaches it.
Every tool listed must be necessary for the skill's stated purpose.

**AST04 — Insecure metadata.**
Frontmatter fields are attacker-controlled inputs when the skill source is untrusted.
The review checks that metadata is validated before use and free of injected payloads in display fields.

**AST05 — External reference pinning.**
A skill that fetches external URLs at runtime and treats the response as instructions is a mutable attack surface.
Fetched content must be pinned or treated as data context, not executed directly.

**AST06 — Isolation declaration.**
A skill that instructs code execution without naming a containment boundary is a finding.
The containment mechanism must be declared, not implied.

**AST07 — Version drift.**
Dependency references in skill manifests must be pinned, not open-ranged.

**AST09 — Governance gap.**
A converged skill must be inventoried — registered in an auditable record with name, version, content hash, and install source.
The pack's ledger and `agentbundle show` inventory are this record.
A skill with no inventory entry is ungoverned regardless of its content.

**AST10 — Cross-platform metadata survival.**
Security metadata (risk tier, permission manifest) must survive projection across adapters.
The projection pipeline and `lint-agent-artifacts.py` enforce this.

AST02 (supply chain) defers to the supply-chain security module.
AST08 is addressed structurally by the `tool`/`hybrid`/`reason` review taxonomy built into the security review process.

The full AST01–AST10 check detail lives in the `security-checklists` skill's agentic-skills reference module, loaded during any security review pass.

## Why shaping, not pasting

External work carries the conventions of the project it came from.
An activation description written for a different catalogue's trigger patterns may collide with this catalogue's existing skills.
A skill body that calls another skill by path rather than by name will break on projection to a different adapter layout.
A subagent with no stated tool constraints is functionally over-permissioned from the moment it lands.

Convergence catches these before they become production problems.
The shaping step is not reformatting — it is craft review with jurisdiction over what enters the catalogue.

## No merge-back

The canonical direction of data flow is: upstream source → catalogue.
There is no "sync my fork's edits back upstream" flow.

If a skill in the catalogue is improved, that improvement can be submitted as a PR to the upstream repo.
The upstream will run its own convergence review on the contribution — it treats the contribution as a fresh primitive, not a trusted sync from a known derivative.
This is deliberate: bidirectional sync between a catalogue and its derivatives is where divergence accumulates silently and identity-leak accidents happen.
One source is authoritative; derivatives are derived, not collaborative branches of it.

## Where to go next

[agentskills.io specification — applied reference](../../_shared/reference/agentskills-io-standard.md) ·
[Catalogue operator journey](catalogue-operator-journey.md) ·
[Your first assimilation](../tutorials/first-assimilation.md) ·
[Your first subagent](../tutorials/your-first-subagent.md)
