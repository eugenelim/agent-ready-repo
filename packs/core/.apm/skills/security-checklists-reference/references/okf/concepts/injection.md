---
title: "injection"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# injection

Use when untrusted input reaches an interpreter, template, deserializer, query,
HTML sink, shell, or command boundary.

## Spec-stage

Require a parameterized, escaped, or typed interface by design rather than a
promise to sanitize strings later.

## Implementation checks

- `hybrid` Use parameterized queries, not string-built SQL.
- `hybrid` Prefer argv execution over shell strings.
- `hybrid` Contextually escape HTML and template output.
- `reason` Refuse unsafe deserializers for untrusted bytes.
- `tool` Confirm SAST/SCA covers parser and driver vulnerability classes.

## Established-helper bypass

Resolve the sanctioned query builder, encoder, and safe-loader paths and flag
raw string interpolation or unsafe loading.
