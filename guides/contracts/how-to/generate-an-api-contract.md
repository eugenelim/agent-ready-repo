---
title: "Design an API contract"
summary: "Get a checked contract for your API, ready for code generators and mock servers."
pack: contracts
kind: how-to
uses: [contracts]
aliases:
  - guides/contracts/how-to/author-an-event-contract
---

# Design an API contract

A contract is a machine-readable description of what your API accepts and returns. Describe the API in plain words, and your agent writes the contract, which tools can turn into code, mocks, and SDKs.

## Write the API contract

To get an OpenAPI 3.1 contract for an API you own, ask:

```text
Use api-contract to generate an OpenAPI contract for an order-management service: create an order, fetch it, list a customer's orders, cancel one.
```

The `api-contract` skill designs the URLs, payloads, errors, and security, and checks the result against the design standard before showing it. The standard is Zalando's by default, or your organization's own if you plugged one in. Hand it a partial OpenAPI file and it fills the gaps instead of starting over.

## Write an event contract

Events are messages you publish, such as an order placed. When your feature owns the event, ask:

```text
Use event-contract to author the AsyncAPI contract for the order events we publish: order.placed, order.cancelled. Order is the resource we own.
```

The `event-contract` skill writes an AsyncAPI document in `contracts/asyncapi/`, with channels, messages, and payload schemas, using CloudEvents envelopes by default.

## Write contracts only for what you own

If you only consume an API or an event, point to the owner's contract and write none, because a contract you author for someone else's API drifts from the real one. If the event's contract already sits in `contracts/asyncapi/`, reference it. If its producer is outside your repository, note the type you depend on and write nothing.

Next, [write a spec](../../core/how-to/write-the-contract.md) that the build follows and tests against this contract.
