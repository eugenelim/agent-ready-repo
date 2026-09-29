# Codex Collaboration Causal Methodology

This record freezes the reusable method for `codex-collaboration-r1`. It is a
manual handoff workbench: the controller prepares slots, records launches,
ingests terminal receipts, grades simulated receipts, and emits bounded
summaries. It does not invoke a model or execute experiment subjects during
the adapter validation step.

The design has a 600-start outer ceiling and a maximum planned use of 566
starts. The 34 unused starts are refusal headroom, not an adaptive reserve.
Holdouts are unreleased until the main manifest, scoring rule, selection rule,
and tie handling are frozen.

The adapter records unavailable telemetry as unavailable. It does not estimate
wall clock, token use, served model identity, or session identity.

Candidate-executing commands must be literal argv arrays with a confined
working directory, explicit secret-free environment, denied network and egress,
bounded output, controller timeout, process-tree cleanup, and confined read and
write roots. If any property is absent or unobservable, the command receives a
terminal non-executed record.

Raw artifacts have byte limits and a controller privacy screen before
persistence or reuse. Suspected secret or private material is represented only
by digest and generic quarantine status.

Provider-labelled causal outputs must not overwrite legacy `results.json`,
`evidence-index.json`, `wave-1.json`, or gate memo records. The failed provider
blocks and retrospective churn records remain separate evidence classes.
