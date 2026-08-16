# RFC-0087 adapter preservation spike

Run on 2026-08-15 from the repository root:

```bash
env PYTHONPATH=packages/agentbundle \
  python3 docs/rfc/0087-notes/verify_adapter_spike.py
```

The fixture is embedded as bytes in the script. It is an Agent Skill containing
`references/okf/playbooks/triage.md`; the concept has OKF-like frontmatter, an
`x-agentbundle` object, an unknown `x-foreign-system` object, and a Markdown
procedure. The script invokes the repository's real adapter modules using
`contracts/adapter.toml`, finds the concept in each output tree, and requires
byte equality with the source before printing `PASS`.

Observed output:

```text
PASS claude-code sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .claude/skills/okf-router/references/okf/playbooks/triage.md
PASS kiro-ide sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .kiro/skills/okf-router/references/okf/playbooks/triage.md
PASS kiro-cli sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .kiro/skills/okf-router/references/okf/playbooks/triage.md
PASS copilot sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .agents/skills/okf-router/references/okf/playbooks/triage.md
PASS cursor sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .agents/skills/okf-router/references/okf/playbooks/triage.md
PASS codex sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .agents/skills/okf-router/references/okf/playbooks/triage.md
PASS gemini sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900 .agents/skills/okf-router/references/okf/playbooks/triage.md
```

This establishes only that the current adapters preserve nested regular-file
bytes inside a Skill. It does not test the proposed compiler, schemas, router
quality, security review boundary, or catalogue-discovery response.
