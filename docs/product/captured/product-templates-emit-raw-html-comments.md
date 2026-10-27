# Product templates emit raw html comments

- **Status:** Open
- **Kind:** defect

## Summary

The shipped intent, spec, plan and brief templates carry their author guidance as HTML comments, so every artifact made from them contains raw HTML a CommonMark editor drops or shows verbatim. Measured 2026-09-24 with markdown-it-py over the repository: 543 of 921 spec and plan files, 53 of 104 RFCs, 26 of 154 intents and 5 of 20 briefs are affected, 891 tokens in total, of which 201 are multi-line blocks. intent-template.md alone ships 20. Fixing the templates is what stops new artifacts inheriting it; a sweep over existing files is separate and is NOT purely mechanical, because nine intent comments carry content rather than guidance (five discovery-chain rungs, one deliberate product-vision altitude, and three recording that a needs edge is stated but unenforced), the Status annotations are the only place a reader sees the lifecycle enum, and scanner-suppression-and-pin-hygiene.md contains the literal <!-- --> in prose as one of four comment syntaxes, so a regex sweep corrupts that sentence
