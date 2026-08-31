---
name: render-release-notes
description: Render release notes to HTML and check the rendered output in a browser.
metadata:
  boundaries: [filesystem_read_untrusted]
---

# render-release-notes

Render the supplied changelog to HTML and report layout problems in the
rendered page.

## Verification

The skill ships a browser test suite. Workers are set to the machine's CPU
count. Dependencies install with the package manager's default install command
at test time. The suite reuses one browser profile directory across workers so
startup stays cheap.
