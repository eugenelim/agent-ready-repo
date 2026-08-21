# Evidence method

## Required surface ledger

Status documentation, source, tests, manifests/dependencies, CI/CD,
deployment/release/IaC, schemas/migrations, runtime configuration,
operational evidence, and read-only history. Use `observed`, `missing`, `unavailable`,
`denied`, `out of scope`, or `not applicable`; absence is not a clean result.

## Evidence ladder

Prefer evidence closest to behavior while preserving why it exists:

1. exercised runtime, operational, and fault evidence;
2. executable tests, schemas, policies, and infrastructure definitions;
3. implemented source and configuration;
4. manifests, dependency graphs, CI/release definitions, and history;
5. current decision records, runbooks, and maintained architecture docs;
6. reported stakeholder context and unconfirmed documentation;
7. generic corpus knowledge and model inference.

Higher is not automatically better: runtime symptoms without implementation
context can mislead, while a binding schema may be stronger than a transient
trace. Record the evidence class, locator, observation, date/freshness when
material, confidence, counter-evidence, and validation gap.

## Claim calibration

- **Observed** — directly supported by a current artifact or authorized
  exercise.
- **Inferred** — the evidence supports the explanation but alternatives remain.
- **Reported** — supplied by attributed enterprise or stakeholder context.
- **Unknown** — material evidence is absent, denied, stale, or contradictory.

Architecture knowledge supplies questions and expected mechanisms, not target
observations. A missing mechanism is not a defect until the applicable scenario
and evidence show the consequence.
