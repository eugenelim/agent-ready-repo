# Spec: synthetic status with appended free text

- **Status:** Implementing — scope now also covers the adjacent surface <!-- Draft | Approved -->

Hand-authored. Only the status *token* is spliced out; anything else on the line
stays pinned, so appending scope prose to the status line MUST move the digest.
`_STATUS_RE`'s whole group(1) span is deliberately not spliced.

## Acceptance Criteria

- [x] The token is replaced by the placeholder.
- [ ] The appended free text remains part of the digest.
