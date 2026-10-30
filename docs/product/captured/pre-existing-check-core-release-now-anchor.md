# Pre existing check-core-release now-anchor

- **Status:** Closed
- **Resolution:** fixed
- **Kind:** defect

## Summary

`python3 tools/check-core-release.py --base <base>` fails on `main` at
`b1be32193` (Core 3.1.38) with "/now/ payload bullets differ from the core
3.1.38 changelog entry". `tools/build-site.py` `project_now_highlights` appends
the next release's `<a id="…"></a>` anchor to the last Highlights bullet, so the
projected bullet never equals the changelog entry's bullet. The same failure
hits every Core release, including 3.1.39. No CI workflow or Makefile target
runs this check.

## Resolution

The `/now/` parser in `tools/changelog.py` now ends a Highlights bullet at a
blank line followed by an unindented line, as CommonMark does. The anchor line
no longer joins the last bullet, and `check-core-release.py` passes. The real
`/now/` page never showed the anchor: it reads fragment bullets directly, and
its payload is byte-identical before and after the fix.
