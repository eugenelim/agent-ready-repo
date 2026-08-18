---
title: "access-control"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# access-control

Use when the change crosses authorization, object-level access, function-level
access, or a new endpoint/handler/RPC boundary.

## Spec-stage

Require the access rule as an acceptance criterion: which identity is checked,
where the check occurs before the side effect, and what an out-of-scope caller
receives.

## Implementation checks

- `reason` Name who is allowed to call every new or changed route.
- `reason` Fetch protected rows scoped to the caller, not fetch-then-filter.
- `reason` Check privileged function-level access before the side effect.
- `reason` Confirm request bodies cannot mass-assign privileged fields.
- `hybrid` Use route-auth scanner output only as the starting point.

## Established-helper bypass

Resolve the repo's sanctioned authorization middleware, policy helper, or
decorator and flag ad-hoc checks that bypass it.
