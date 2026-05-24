---
name: missing-dont-block
description: Credentialed-CLI fixture missing the `### Security rules (non-negotiable)` heading; AC26(a) finding expected.
credentialed: true
primitive-class: credentialed-cli
---

This fixture declares `credentialed: true` but omits the "Don't" block.
T10's lint must report the missing heading.
