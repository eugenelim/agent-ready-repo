# Subagent present but unrunnable

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/specs/claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md

## Summary

Sub-agent degradation fallbacks are keyed on the agent being absent, so none fires on a surface where it is present but unrunnable, letting a Shipped named-skip guarantee pass silently
