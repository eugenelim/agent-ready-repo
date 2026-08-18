---
title: "path-and-file"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# path-and-file

Use when a filesystem path comes from input, files are uploaded or served, or
archives are extracted.

## Spec-stage

Require confinement to a designated root after canonicalization, not just
blocking `..` segments.

## Implementation checks

- `hybrid` Detect traversal into file operations.
- `reason` Resolve then verify the path remains under the intended root.
- `reason` Refuse symlink and junction escapes.
- `reason` Handle tree-walk aliasing, visited-set timing, and resolve errors.
- `reason` Validate target-format encoding and strict JSON constraints.
- `reason` Validate every archive entry destination.
- `reason` Do not trust upload filenames or client content types.

## Established-helper bypass

Resolve the sanctioned path-confinement or safe-join helper and flag raw string
joins or bare traversal stripping.
