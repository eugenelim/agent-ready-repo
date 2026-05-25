---
name: missing-dont-block
description: Credentialed-CLI fixture missing the `### Security rules (non-negotiable)` heading; AC26(a) finding expected.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

This fixture declares `metadata.credentialed: true` but omits the "Don't" block.
T10's lint must report the missing heading.
