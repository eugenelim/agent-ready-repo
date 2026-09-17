# Model selection

Every subagent file declares `model:` in its frontmatter explicitly. The
`agentbundle catalogue verify` (step 11, `_step_agent_artifacts`) linter
enforces this. Reasoning behind each current choice:

| Subagent | Model | Why |
|---|---|---|
| `adversarial-reviewer` | `opus` | Adversarial judgment; stakes are correctness. Owns contract conformance, scope, and structural fit; routes threats to `security-reviewer` rather than judging them. Output drives a hard gate. |
| `security-reviewer` | `opus` | Threat-model reasoning; stakes are security. |
| `quality-engineer` | `opus` | Maintenance lens; spec-level coverage pass. Exclusively owns test strength — whether an assertion can fail — which is judgment, not extraction. Reconsider per observation. |
| `implementer` | `sonnet` | One narrow plan task per dispatch; gates rerun in the primary; supervisor judges merge readiness. Cost beats capability here. |
| `finding-adjudicator` | `opus` | Weighs a reviewer's claim against repository evidence and decides what the loop may act on. A wrong refutation silently discards a real defect, so this is judgment under conflict, not extraction. |

Changing a subagent's model is a behaviour change, not a configuration
tweak — note the change in the PR that makes it, with a one-line
justification. If the change is reversing a previous choice in a way a
future maintainer would ask "why", surface it in the PR description.
