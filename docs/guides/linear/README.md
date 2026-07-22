# `linear` — guides

Linear integration for the agent-ready-repo catalogue. Read Linear Issues
and Projects, then turn them into shippable product briefs or keep existing
briefs in sync as issues evolve.

The API key never reaches the model. `linear` is a credentialed skill: it
invokes a CLI that resolves your Personal API Key in-process and makes the
GraphQL call itself.

New here? Generate a Personal API Key at Linear → Settings → API → Personal
API keys, then run `credential-setup` to store it. Then read
[When to use `linear-brief-intake` vs `linear-brief-sync`](how-to/linear-brief-intake-and-sync.md)
to decide where to start.

## How-to

Task-oriented recipes for a problem you already have.

- [When to use `linear-brief-intake` vs `linear-brief-sync`](how-to/linear-brief-intake-and-sync.md) — decide which workflow fits your situation, set up credentials, and run your first intake or sync.

---

The two-layer credential model — why the skill never holds your token — lives
with the [`credential-brokers`](../credential-brokers/) pack. Installing and
upgrading the catalogue live in [`../_shared/`](../_shared/).
