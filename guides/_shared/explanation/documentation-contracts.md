# Documentation contracts

What each documentation page promises its reader, regardless of where the file
lives. Relocated from the retired repository conventions document.

The user-facing documentation, organized by [Diátaxis](https://diataxis.fr/).
Four kinds of content, each serving a different reader need. **Mixing kinds
is the most common cause of bad docs.** The four kinds are:

- **tutorial** — *learning-oriented.* An on-rails lesson: one path, one
  guaranteed outcome, no detours.
- **how-to** — *task-oriented.* A recipe for a reader who has a specific
  named problem to solve.
- **reference** — *information-oriented.* Authoritative, dry, complete
  description of interfaces, config, commands.
- **explanation** — *understanding-oriented.* Why a design works the way
  it does, what concepts mean, how systems fit together.

**Each piece of content belongs in exactly one of these.** When a tutorial
wants to explain *why*, link out to an explanation page. When a how-to
wants to enumerate every option, link out to reference. The "link out"
discipline is the whole framework.

The four kinds are authoring contracts, not mandatory directory names.
How you organize the `guides/` tree is a local decision — by pack, by
topic, by quadrant, or flat. The contracts govern what each page promises
its reader regardless of where the file lives.

**Specs become user docs when features ship.** A shipped feature's spec
is the team's permanent record of the contract. Its *user-facing*
documentation lands in the appropriate `guides/` location (reference for
authoritative description, how-to if users need recipes, explanation if
it introduces a concept). The spec workflow is not done until those are
updated.

**Lifecycle for all three:** updated whenever the code or product changes
in a way that makes the description wrong. Keep them short — the goal is
to *orient* a reader, not to duplicate the code or the spec.

**Phase-slice doctrine applies here.** When a feature phase ships, its guides ship with it — not in a terminal documentation wave. A phase whose tooling is shipped but whose guides are absent is not a complete slice. See [§ Enforcement](../../core/how-to/plan-and-execute-non-trivial-work.md#enforcement) in *How to plan and execute non-trivial work*.
