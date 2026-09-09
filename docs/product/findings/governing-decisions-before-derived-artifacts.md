# Finding: Derive lifecycle architecture from governing decisions before derived artifacts

## Finding

An existing helper or serialized projection can look like the architecture it
serves while encoding a wider, narrower, or older question. Starting from that
derived artifact can therefore produce a coherent implementation of the wrong
contract.

The direct-skill lifecycle exposed this failure shape. The available capability
comparison included content digests, payload changes, and skill-set changes in
addition to permission axes. Reusing its aggregate re-consent result for direct
upgrade would have refused every content update the governing decision required
the route to perform. Likewise, applying a general source canonicalizer would
have changed collision identity through URL and working-directory transforms
that were not part of the stored-source decision.

## Practice

Begin with the governing decision's identity, transitions, and failure rules.
Then map each existing helper, state field, projection, or renderer to one of
those rules and use only the part whose semantics match. Treat the derived
artifact as implementation evidence, not as authority for the architecture.

For each reused artifact, write one counterexample before implementation:

- a value the artifact merges that the decision keeps distinct;
- a value the artifact distinguishes that the decision treats as one; or
- an outcome the artifact reports that the decision does not permit.

If such a counterexample exists, add a narrow decision-shaped adapter or direct
comparison instead of inheriting the artifact's whole model.

## Evidence

- [RFC-0098 D4](../../rfc/0098-direct-skill-repository-installation.md#d4--manifestless-identity-and-lifecycle)
  owns direct identity and makes revision a version of that identity.
- [ADR-0106](../../adr/0106-direct-skill-identity-and-upgrade-revision-route.md)
  records the narrow stored-source and capability-history decisions needed by
  direct upgrade.

## Reuse

Apply this check when a new lifecycle route is built over an older comparison
engine, renderer, state projection, compatibility shim, or generated artifact.
It is especially valuable when the existing component's name sounds broader
than the contract it actually implements.
