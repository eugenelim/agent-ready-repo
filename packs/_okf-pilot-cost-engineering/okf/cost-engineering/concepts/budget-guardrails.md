---
title: "Budget guardrail design"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# Budget guardrail design

Use this concept when a maintainer is deciding how to express a spending limit
for a generic workload. A guardrail may be a notification, review checkpoint, or
manual approval threshold; this pilot does not authorize automatic enforcement.

Prefer guardrails that name an owner, interval, threshold, and recovery action.
Avoid thresholds that depend on hidden account state or undocumented unit
conversions.
