# Self-coverage module — conditional domain-grounding

Part of the [self-coverage gate](coverage-record.md). Runs at **PLAN /
pre-convergence**, and is conditional: it fires **only when the design rests on an
ungrounded load-bearing domain claim**; otherwise it degrades to *"`frame-domain`
already grounds this."*

## The move

The agent cannot reason through a domain it does not know — left ungrounded it
**hallucinates the domain and over-scopes** (the deepest correctness lever, and
`frame-domain`'s whole reason to exist). Before designing a screen, service, or
architecture on a domain claim, ground it.

- **Identify the load-bearing domain claims** — the facts about *how the activity
  is really done* that the spine depends on (cadence, the real-vs-planned gap, the
  naive-design failure modes).
- **Ground each via `frame-domain`** (which wraps `desk-research` applied mode +, for
  brownfield, `decision-archaeology`). The output is the `domain-framing` +
  `scope-boundary` slots.
- **Never assert an ungrounded domain claim as fact.** A finding the wrapped
  research could not ground is a **named residual assumption**, surfaced for the
  human at the MVP boundary — not stated as fact in the artifact body.

## Distinction from the EXECUTE contract-grounding gate

This grounds **domain claims** (how the world works). It is **distinct** from
`work-loop`'s EXECUTE contract-grounding gate, which grounds **API/library
contracts** (signatures, schemas). Discovery rarely hits the contract gate; it
lives and dies on the domain gate.

## Output

Each load-bearing domain claim either **grounded** (cite the `frame-domain`
referent) or a **residual assumption** (surfaced, carried to the coverage record
and labelled in the provisional spine). The honest output when there is *no*
ungrounded load-bearing claim is to record that — not to manufacture a grounding
exercise.
