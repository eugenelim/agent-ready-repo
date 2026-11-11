# ADR-0001: <script>alert("xss")</script> hostile title

- **Status:** Accepted<script>document.cookie</script>
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

This record contains hostile HTML in the H1 title and in the Status field value.
The navigator must treat both as untrusted data: the title and status remain
inert text in query output and HTML output. The script tags must not execute,
load resources, or alter document structure.

javascript:alert(1) and data:text/html,<b>test</b> and onerror=alert(1)
must all remain as inert text.

## Decision

- **D1:** Hostile content in records is treated as inert untrusted data.

<img src="x" onerror="alert(1)">
