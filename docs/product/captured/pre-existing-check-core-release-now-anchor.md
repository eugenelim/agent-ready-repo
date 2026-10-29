# Pre existing check-core-release now-anchor

- **Status:** Open
- **Kind:** defect

## Summary

`python3 tools/check-core-release.py --base <base>` fails on `main` at
`b1be32193` (Core 3.1.38) with "/now/ payload bullets differ from the core
3.1.38 changelog entry". `tools/build-site.py` `project_now_highlights` appends
the next release's `<a id="…"></a>` anchor to the last Highlights bullet, so the
projected bullet never equals the changelog entry's bullet. The same failure
hits every Core release, including 3.1.39. No CI workflow or Makefile target
runs this check.
