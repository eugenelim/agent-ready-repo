---
name: Wicked Estate code intelligence
pluginInstallable: true
scope: repo
tagline: "Ask what calls this and what breaks if I change it — from a real call graph."
skills:
  - code-intelligence
installCommand: "agentbundle install --pack wicked-estate"
docsUrl: /docs/guides/
---

Index a repository with [Wicked Estate](https://github.com/mikeparcewski/wicked-estate), then ask an agent what depends on a symbol, how a subsystem is organised, or what a change would touch. Answers come from resolved call and import edges, and they carry the index's own limits — the call sites it could not bind, the rows it truncated, the revision it was built from. Two subagents run the same discipline in a forked context: `code-investigator` for evidence-driven investigation, `impact-analyst` for change-impact analysis. Requires the `wicked-estate` CLI and an index you build; it never writes to the graph without asking.
