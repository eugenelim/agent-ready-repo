# Manual-QA dogfood — `security-reviewer` reasons from the new `llm-agent` checks

Recorded artifact for the spec's manual-QA acceptance criterion ("The
security-reviewer reasons from the new module checks"). The `security-reviewer`
subagent — the actual consumer of the `llm-agent` module — was run with the
**extended** module (this PR's version) inlined into its brief against a
synthetic agentic snippet, since this PR's own diff is pure prose with no agentic
sink. Pass condition: the report cites the three new checks as the control depth.
The reviewer's verdict on the snippet is its own and is **not** gated.

## Synthetic agentic snippet exercised

```python
# A research agent that delegates to a code-runner sub-agent and persists notes.
def run(task, user):
    plan = llm(f"User {user} asked: {task}. Plan tool calls.")
    for step in plan.steps:
        if step.tool == "python_exec":
            result = subprocess.run(["python", "-c", step.code], capture_output=True)  # no sandbox
        elif step.tool == "delegate":
            sub = spawn_subagent(step.goal, creds=ADMIN_TOKEN)   # passes admin creds down
        notes = retrieve(step.query)            # pulls web/docs
        memory.append(notes)                    # persisted to vector store, no trust check
    return llm(f"Summarize from memory: {memory.all()}")
```

## Result — all three new checks fired, each cited as control depth

- **Execution isolation & blast radius (Agentic ASI02 / ASI05)** — fired on the
  `subprocess.run([... ], # no sandbox)` line. The reviewer reasoned the tool is
  *authorized* but not *contained*, and named all three confinement axes as
  absent: **filesystem scope** (inherits parent FS), **network egress**
  (`hybrid` facet — can reach internal services / cloud-metadata, cross-ref
  `outbound-ssrf`), and **resource/time caps** (no CPU/memory/wall-clock bound).
- **Inter-agent identity/privilege propagation (Agentic ASI03)** — fired on
  `spawn_subagent(step.goal, creds=ADMIN_TOKEN)`. The reviewer reasoned the
  hand-off resets to the agent's own broad credential instead of bounding the
  callee by the caller's narrow grant — the multi-agent confused deputy, with the
  sub-agent goal LLM-derived from untrusted input.
- **Memory & context poisoning (Agentic ASI06 / LLM04)** — fired on both sides:
  the **write gate** (`memory.append(notes)` with no trust-check on retrieved
  content) and the **read side** (`llm("Summarize from memory: " + memory.all())`
  feeding the unvetted store back into a prompt).

The reviewer reasoned from the module text (not a cross-cutting OWASP/STRIDE
fallback) and cited each new check on its intended line(s) at control altitude.
**The AC is satisfied.** (The reviewer additionally noted existing-check LLM01
prompt injection on the planning line — not one of the three under test.)

## Verdict (not gated)

The reviewer's own verdict on the snippet was three exploitable Blockers — its
judgment on the synthetic code, recorded for completeness and explicitly outside
the AC's pass condition.
