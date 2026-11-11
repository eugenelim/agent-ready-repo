# Knowledge freshness pins bytes and the pins do not hold

- **Status:** Open
- **Kind:** defect

## Summary

36 of 71 pinned source digests are stale across 24 of 101 knowledge topics and 9 more pins name a file that no longer opens; the store validates digest shape rather than currency, so no gate reds and enquiry returns them as fresh. tools/lint-knowledge-freshness.py now detects it but no gate runs it, and the baseline cannot ratchet down because re-pinning costs one pending captured observation per topic and wiring needs a capture-free maintenance mutation or a freshness contract off byte digests first
