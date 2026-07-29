# Example Pack

<!-- Pack display name: Example Pack -->
<!-- One-sentence user outcome: Run this pack to demonstrate the standard skill layout. -->

A minimal example pack. Replace this line with the user outcome your pack delivers — one sentence,
written from the user's perspective ("Use this pack to...").

## Audience

Who benefits from this pack and in what situation. For example: "Software engineers who want to
automate code reviews in any repo."

## What this pack provides

- **example-skill** — a minimal skill demonstrating the standard layout. Replace with your real skills.

## Installation

```bash
agentbundle install example-pack
```

Default scope: `repo`. Supports `repo` and `user` scopes.

Supported adapters: claude-code, kiro, codex, copilot.

## First useful invocation

After installation, open your agent and say:

```
run example
```

### Expected result

The agent greets you and lists any files mentioned in the conversation.

## Writes and trust-relevant behavior

This pack writes nothing. It contains no hooks, no credentials, and no browser automation.
Replace this section with accurate write-behavior information for your pack.

## Dependencies

This pack has no required dependencies.

Recommended composition: none.

## Documentation

Full documentation: <https://example.com/docs>

Changelog: <https://example.com/changelog>

## Development

```bash
# Validate pack sources
agentbundle catalogue lint --root .

# Full verification
agentbundle catalogue verify --root .
```

---

*This README is the canonical template for new packs. Copy `packs/_example` to `packs/<your-pack>`,
update the identity fields, and replace the placeholder content.*
