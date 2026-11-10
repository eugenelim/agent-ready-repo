+++
schema = 1
id = "33e440c1-efb6-48c3-b0fa-b2bb2ba5bdf1"
anchor = "core500--2026-11-09-33e440c1efb648c3b0fab2bb2ba5bdf1"
date = 2026-11-09
[[packages]]
name = "core"
version = "5.0.0"
+++
## Highlights
- The work loop no longer asks for a knowledge capture when a spec is approved or when a run starts. Delivery facts already feed knowledge candidates, and a capture is still one explicit command away.

## Changed
- Removed the `spec-approved` and `plan-locked` capture gates. The human approval gates `spec-approved` and `plan-approved` are unchanged. The `work-loop` producer profile of `project-knowledge` keeps its enquiry modes and loses `--capture` and `--distill`, which are now refused with no write. Close-time `work-item` capture and plain `--capture` and `--distill --pending` are unchanged.
- Replaced `delivery-fact-feed.v1` with `delivery-fact-feed.v2`. The page has no `shadow_services` member, lists only the four `log-*` unread reasons, and has new snapshot ids and continuation tokens. Candidate mode refuses a v1 page.
- Removed `compatibility_snapshot` and `reverse_read` from the policy import module. Nothing called them.
- For in-flight work: a spec approved before this release runs unchanged.
- For in-flight work: a pending capture that a `plan-locked` gate stored earlier drains through a plain `--distill --pending`.
- For in-flight work: a feed continuation token issued before this release is refused with `snapshot-changed`; start the scan again.
