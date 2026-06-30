# Self-coverage module — scenario variation

Part of the [self-coverage gate](coverage-record.md). Runs at **divergence** (to
widen the candidate set) and at **convergence** (to stress the chosen spine). It is
also the module `explore-options` reuses to generate candidate shapes.

## The move

The happy path hides the design's real edges. Vary the scenario along axes the
default walk never leaves, and check the spine still holds:

- **Altitude** — narrow-slice ↔ whole-domain. The myopic-greedy default picks the
  narrow slice; force the whole-domain variant and the deeper sub-domain.
- **Mechanic** — draft-and-approve / coordination-layer / knowledge-graph-first /
  ambient-capture. The same outcome under a different mechanic is a different
  product.
- **Persona edge** — the non-modal user (the one who *won't* maintain precise
  state; the adversarial user; the accessibility-dependent user).
- **State edge** — empty / partial / error / denied, not just the success state.
- **Scale edge** — one item vs. thousands; one user vs. a household vs. an org.
- **Adversarial edge** — untrusted input reaching memory; a poisoned external
  source; a regulated fact in a shared store.

## Output

Each variation either **absorbed** (the spine already handles it — note how) or a
**finding** (the spine breaks — route to a verdict: widen the divergence, add a
slot, or surface). Variations the loop *cannot* resolve carry to the coverage
record. This is the module that turns a single coherent framing into a tested one.
