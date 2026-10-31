+++
schema = 1
id = "ddccbba0-fcde-49ac-b3f8-0067ca6f93eb"
anchor = "core402--2026-10-30-ddccbba0fcde49acb3f80067ca6f93eb"
date = 2026-10-30
[[packages]]
name = "core"
version = "4.0.2"
+++
## Highlights
- The work-loop supervisor's `status` now checks a spec's committed run records in a checkout that never ran the supervisor (a fresh clone, CI, or `main` after a squash merge), instead of refusing `supervisor-changed`. It reports `"verification": "committed-records-only"` there and `"pinned"` where it compared the local pins, and every other verb still refuses without the pins.
