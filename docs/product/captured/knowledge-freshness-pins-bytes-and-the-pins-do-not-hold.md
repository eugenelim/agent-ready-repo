# Knowledge freshness pins bytes and the pins do not hold

- **Status:** Open
- **Kind:** defect

## Summary

Knowledge topic pins hold a source byte digest, and the store validates digest shape rather than currency, so a pin can go stale with no gate red and enquiry still returns the topic as fresh. tools/lint-knowledge-freshness.py now detects it, and the corpus is clean (29 pins across 101 topics, none stale) after dropping the pins that could not hold. No gate runs the checker yet, so new drift stays invisible until one does; re-pinning still costs one pending captured observation per topic, so wiring needs either that cost accepted or a freshness contract off byte digests
