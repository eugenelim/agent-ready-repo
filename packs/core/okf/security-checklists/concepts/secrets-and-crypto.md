---
title: "secrets-and-crypto"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# secrets-and-crypto

Use when the change handles secrets, keys, tokens, hashing, signing,
encryption, decryption, or security-relevant randomness.

## Spec-stage

Require broker-mediated secrets and named key/algorithm sources rather than
ad-hoc reads or a vague promise to encrypt.

## Implementation checks

- `tool` Confirm secret scanning for committed credentials.
- `tool` Confirm weak primitive detection is wired.
- `reason` Store passwords with memory-hard KDFs and per-password salt.
- `reason` Use CSPRNG sources for tokens, nonces, and reset codes.
- `reason` Trace secrets through logs, errors, and serialized responses.
- `reason` Require a key lifecycle and rotation path.

## Established-helper bypass

Resolve the sanctioned secrets broker and crypto helper and flag direct secret
reads or hand-rolled encryption.
