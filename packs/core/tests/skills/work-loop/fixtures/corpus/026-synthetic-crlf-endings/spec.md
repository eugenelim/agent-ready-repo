# Spec: synthetic CRLF line endings

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped -->

Hand-authored. `canonical_contract` folds CRLF and CR to LF as its first step,
and no file in the live tree uses either, so the path is otherwise untested.
This file is stored with LF: `.gitattributes` pins `* text=auto eol=lf`
repo-wide, so committed CR bytes are normalized away in the blob. The CRLF and
bare-CR forms are synthesized from this text at generation and test time — see
`golden_support.crlf_bytes` and the `@crlf` / `@cr` digest keys.

## Acceptance Criteria

- [x] CRLF is folded before hashing.
- [ ] Trailing whitespace is stripped per line.   
