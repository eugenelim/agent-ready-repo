# secrets-and-crypto — secrets, keys, hashing, signing, randomness

> **Loaded when:** the change handles secrets/keys/tokens, hashes or signs
> data, encrypts/decrypts, or generates security-relevant random values.
> **Standards:** OWASP Top 10:2025 A04 (Cryptographic Failures) · ASVS 5.0 V11
> (Cryptography) · CWE Top 25 (CWE-798 Hardcoded Credentials) · Proactive
> Controls 2024 C8 (Protect Data Everywhere).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is **broker-mediated secrets, not ad-hoc reads** —
the spec should name where a secret comes from (a secrets manager / broker /
mounted secret) rather than implying an inline read of an env var or file at
the call site. For data at rest, name the algorithm class and key source as
criteria, not "encrypt it" (ASVS 5.0 V11; Proactive Controls 2024 C8).

## Implementation checks

- `tool` **Hardcoded secrets (CWE-798).** Committed keys/passwords/tokens are
  secret-scanner territory — confirm a secret scanner runs in CI; if none is
  detected, flag `degraded: no scanner` and eyeball the diff rather than
  asserting it's clean.
- `tool` **Weak/broken primitives.** `MD5`/`SHA-1` for security, DES, ECB
  mode, hardcoded IVs — SAST rules catch the common shapes; confirm the rule
  is wired, and reason about any primitive the rule wouldn't recognize.
- `reason` **Password storage.** Passwords must use a memory-hard KDF
  (argon2/bcrypt/scrypt) with a per-password salt — not a fast hash. This is a
  design judgment a generic scanner won't make.
- `reason` **Randomness source.** Security-relevant values (tokens, nonces,
  reset codes) must come from a CSPRNG (`secrets`, `crypto.randomBytes`), never
  a non-crypto `random()`.
- `reason` **Secrets in logs / errors.** Trace the secret forward — is it
  logged, echoed in an error, or serialized into a response? Disclosure
  through the error path is the common leak.
- `reason` **Key lifecycle.** Hardcoded keys, no rotation path, or a key
  checked into config are design gaps even when the primitive is strong.

## Established-helper bypass

Resolve the repo's sanctioned secrets broker / config-secret accessor and its
crypto helper. Flag code that reads a secret directly from the environment or
a file at the call site, or hand-rolls encryption, when the blessed broker /
crypto helper exists — the broker is where access is mediated, audited, and
rotated.
