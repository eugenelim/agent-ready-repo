---
name: jira-align-refresh
description: Reviewed Jira Align refresh processor with fail-closed unsupported write-back capability.
allowed-tools: Read Bash
metadata:
  boundaries:
    - network_fetch
    - filesystem_read_untrusted
    - filesystem_write
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: jiraalign
  keys: ["API_TOKEN"]
---

# Jira Align Refresh

This processor is invoked by `work-intake` refresh after the shared refresh
runtime has resolved local authority and lifecycle state. Current Jira Align
refresh support is read acquisition only; write-back actions remain
unsupported because the Jira Align client exposes generic record updates rather
than narrow trace, pull-request, status, comment, or closure commands.

Unsupported actions refuse before payload construction or transport use.
