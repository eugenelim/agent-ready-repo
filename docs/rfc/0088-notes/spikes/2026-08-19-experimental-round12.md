# RFC-0088 Experimental round 12 — consumer-shaped residuals

**Status:** complete measurements; no RFC decision or disposition changed.

## Findings

### Destination-scoped worker policy is split

Registration blocking is destination-scopable only by partitioning destinations into separate contexts; shared-session scoping is not demonstrated. Two distinct loopback origins both registered into one shared `Default/Service Worker` store, and a post-purge scan retained no worker-store directory. The persisted-store purge is not destination-scopable. The earlier single-origin fixture could not measure that outcome; this result is a declared finding after recursive discovery and post-purge observation. The whole-profile control establishes no credential survival conclusion.

### Page-resident replay holds ONLY with no-store

The page-resident init script receives the token while the driver does not; removing the shim leaves the same issuer page without it, and navigation preserves page delivery. The issuer is a distinct loopback process, bounded by `rfc0088-same-uid-attach-exposure`: any local process able to connect to the loopback listener can obtain the token without client authentication. The otherwise identical default-cache control finds the live token in browser user-data, so `no-store` is a construction requirement. The declared finding records only a role-relative store name. A buffer without a detected decoy is recorded as unverifiable and contributes no absence claim. Bounded byte scans record offsets for labelled decoys only; logs are searched then removed through confined removal.

The candidate holds only when the issuing response is marked `no-store`; without it, the default-cache control finds the live token at rest in browser user-data. The remaining browser-written buffers are unknown rather than clean where their detector did not recover a planted decoy.

The encrypted cookie store is not byte-verifiable, and other surfaces without a detected decoy remain absence-unverifiable; their inventory is retained in the results member, not turned into an absence claim. The separate no-shim context has no token while the otherwise identical init-script context has one, proving the control can report both outcomes.

### Signing identity has an attributable discriminator

The system channel passes strict and requirement verification. An OS-signed control passes strict verification but fails the requirement, making the discriminator requirement-attributable. The bundled channel fails resource sealing before requirement evaluation and is not the discriminator. A modified temporary copy fails verification. Update survival and whether bundled-channel digest pinning remains necessary are not measured; update survival remains `rfc0088-signing-identity-update-survival`.

The discrimination is attributable to the requirement.

The approver-authorised attended post-authentication arm observed re-attach surviving
worker suppression with zero registrations under both policies. It is bounded to one
destination, one device, and one point in time, and closes the deleted post-auth register text.

## Apparatus corrections and limits

Both organisation-identifier consumers now require an external operator source and refuse absent, empty, or count-mismatched input. A planted member term is refused; restoring it succeeds. The privacy sweep continues to decode its corpus and report no findings.

The confined-removal helper records root-relative removals and refuses symlink, traversal, sibling-root, depth, and entry-bound escapes. `dotdot` and sibling-prefix are each covered by lexical and resolved-parent boundary guards; their mutation disables that pair.

Its confinement claim assumes no concurrent same-uid writer mutates the root between validation and removal; `rfc0088-confined-removal-toctou` remains open before round-13 inventory work.

The selector must name the set its claim is about. Round 12 found two filesystem globs standing in for `MEMBERS` and a filename substring standing in for round-12 artifacts. Claim accounting now iterates `MEMBERS`: the archive digest was identical before, with, and after an unrelated scratch result. The verifier glob remains a recorded follow-up. Four round-12 carry-on artifacts were produced after the row-inventory requirement without declaring an inventory and are recorded inventory-absent in `r12-row-inventory-compatibility.json`. E2 had been misspelled past the former substring selector. The claim-accounting import failed only on the promotion path, which the earlier gate run did not exercise; its manifested-member load now resolves relative to the script itself.

The evidence tree is durable working state under temporary-storage cleanup scope. Round 13 must treat that location as an operational risk; this round does not relocate it.

The three commissioned measurement arms have individually mutation-covered rows and comment-only no-op controls that demonstrate their harnesses can report a non-failure. The named apparatus controls are separately mutation-tested. The four carry-on artifacts are uncovered. A coverage claim is not evidence until its no-op mutation proves the harness can say no; a mutation that cannot discriminate can also reveal a redundant guard rather than a missing fixture. The expected-failing-row gate also caught this round’s sharpest regression: an absence-oriented fix suppressed a positive cache detection until its counted finding disagreed with the declared row; promotion then caught a runner edit exercised only on its mutation path. Gate diagnostics retain the first actionable harness error rather than only a runtime banner.

RFC-0088 remains `Experimental`.
