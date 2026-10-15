# Contracts

Your agent can write the API or event contract first, checked against a house standard, so code and clients follow it.

## Install

Install it once for your user account:

```bash
agentbundle install --pack contracts
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install contracts@agent-ready-repo
```

## What your agent can do

- Write an OpenAPI 3.1 contract from requirements, user stories, or a domain model.
- Write an AsyncAPI contract for an event stream you own, with a standard message envelope.
- Apply a house standard as hard rules. Zalando is the default, and you can swap it.
- Check the contract from the consumer's side: security, error shapes, and missing cases.
- Review or extend a contract you already have.

## Skills

- **`api-contract`** — Writes or reviews an OpenAPI 3.1 contract, validated and ready for code generation, tests, mocks, and SDKs.
- **`event-contract`** — Writes or reviews an AsyncAPI event contract. Use it when your feature produces or owns the event, not when it only consumes it.

## Works with

Works with Claude Code, Codex, Copilot, Kiro IDE, Cursor, and Gemini CLI. [Architect](../architect/README.md) reads an existing contract as a boundary before it proposes a backend. [Core](../core/README.md) grounds code against a contract through `contract-acquisition` when the build loop does not hold it. See [Design an API contract](../../guides/contracts/how-to/generate-an-api-contract.md) and [Author an event contract](../../guides/contracts/how-to/author-an-event-contract.md).

## Questions

**Does it write the implementation?** No. It writes the contract. Code, tests, mocks, and SDKs follow from it.

**Can I use my own standard?** Yes. The API standard and the event envelope are both swappable. The defaults are Zalando and CloudEvents.

**Will it write a contract for an event I only consume?** No. Author an event contract only when your feature produces or owns the event.

**Do I have to start from scratch?** No. Give it the path to an existing spec and it reviews or extends it.

## Details

Scope: user (default), repo · Version: 0.3.8 · Source: [packs/contracts](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/contracts)
