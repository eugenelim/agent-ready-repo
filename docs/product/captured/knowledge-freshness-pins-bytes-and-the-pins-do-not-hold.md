# Knowledge freshness pins bytes and the pins do not hold

- **Status:** Open
- **Kind:** defect

## Summary

34 of 60 pinned source digests are stale across 22 of 101 knowledge topics; the store validates digest shape rather than currency, so no gate reds and enquiry returns them as fresh. tools/lint-knowledge-freshness.py now detects it but no gate runs it, and the baseline cannot ratchet down because re-pinning costs one pending captured observation per topic and wiring needs a capture-free maintenance mutation or a freshness contract off byte digests first
