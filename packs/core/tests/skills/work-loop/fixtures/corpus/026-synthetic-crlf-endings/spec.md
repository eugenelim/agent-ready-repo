# Spec: synthetic CRLF line endings

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped -->

Hand-authored. `canonical_contract` normalizes CRLF and CR to LF as its first
step; no file in the live tree uses CRLF, so this path is otherwise untested.

## Acceptance Criteria

- [x] CRLF is folded before hashing.
- [ ] Trailing whitespace is stripped per line.   
