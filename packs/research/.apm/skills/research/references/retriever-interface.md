# Retriever interface

`/research` standard and deep modes enumerate retrievers from three
surfaces before dispatching queries. This document is the convention
for the third surface — user-registered Python script retrievers.

## The three surfaces

1. **Built-in** — `WebFetch` and `WebSearch`. Always available on
   Claude Code. No registration needed.
2. **MCP tools** — any retrieval-shaped MCP tools registered in the
   session (search APIs, vector stores, internal knowledge bases). MCP
   is the heavyweight surface: a separate process, separate config,
   separate auth. Use MCP for shared/team access and any authenticated
   service that already has an MCP server.
3. **User-registered Python script retrievers** — files at
   `scripts/<name>-retriever.py` in this skill directory, invoked from
   the main session via the `Bash` tool. Use scripts for personal,
   lightweight, already-credentialed-CLI-wrapper retrievers. The
   subagents (`evidence-retriever`, `source-extractor`) do not execute
   scripts — their tool surface excludes `Bash` deliberately.

## Script retriever interface

A script retriever is a Python file at
`packs/research/.apm/skills/research/scripts/<name>-retriever.py`. The
flat-layout convention applies — no nested subdirectories under
`scripts/`.

Each script:

1. Exposes a function `retrieve(query: str) -> dict`.
2. The returned dict has the schema below.
3. Declares its auth shape via `metadata.auth` in a module-level
   docstring or comment header. Permitted values in this pack: `env`
   (read a secret from environment) or `cli` (wrap an already-
   authenticated CLI binary). Unauthenticated retrievers omit the
   `metadata.auth` line entirely — see `arxiv-retriever.py` for the
   no-auth precedent. `creds` and `sso-cookie` broker shapes require
   the `credential-brokers` pack which `research` does not depend on
   and are not permitted in this pack.

### Return schema

```json
{
  "content": "string — the substantive material",
  "citations": [
    {"url": "string", "title": "string", "primacy": "primary|secondary|tertiary"}
  ],
  "shape": "raw"
}
```

The three top-level keys are required: `"content"`, `"citations"`,
`"shape"`.

### Shape values

| Value | Meaning | `citations` required? |
|---|---|---|
| `"raw"` | Returns extracted material verbatim. Caller synthesises. | yes — non-empty |
| `"synthesized"` | Returns a model-synthesised summary already. Caller cites and rates. | yes — non-empty |
| `"meta"` | Returns retrieval metadata only (counts, availability, capabilities). | empty array permitted |

A retriever returning `"raw"` or `"synthesized"` with an empty
`citations` array is a contract violation — `/research` refuses
un-citable answers.

## Invocation from the main session

`/research` enumerates available scripts in standard or deep mode by
listing `packs/research/.apm/skills/research/scripts/*-retriever.py`,
reading each script's docstring for description and auth shape, and
invoking the chosen scripts via `Bash` from the main session:

```bash
python packs/research/.apm/skills/research/scripts/arxiv-retriever.py \
  "query text here"
```

The script prints its JSON return value to stdout; the main session
parses and integrates.

Subagents (`evidence-retriever`, `source-extractor`) do not invoke
scripts — their tool surface excludes `Bash` deliberately, so script-
based retrieval is a main-session concern only.

## Example retrievers shipped

This skill ships two example retrievers as the canonical reference:

- `scripts/arxiv-retriever.py` — unauthenticated arXiv API wrapper.
  Returns `"shape": "raw"`. Demonstrates the no-auth case.
- `scripts/perplexity-retriever.py` — Perplexity Sonar API wrapper.
  Reads `PERPLEXITY_API_KEY` from environment (`metadata.auth: env`).
  Returns `"shape": "synthesized"`. Demonstrates the env-broker case.

Either is a starting template for a new retriever. Drop a new file at
`scripts/<your-name>-retriever.py`, expose `retrieve(query)`, return
the schema above.

## Adding a new retriever

1. Copy one of the example retrievers to a new filename ending in
   `-retriever.py`.
2. Implement `retrieve(query: str) -> dict` against the target service.
3. Set the appropriate `metadata.auth` in the module docstring (`env`
   if you read an environment variable; `cli` if you wrap an
   already-authenticated CLI binary).
4. Return the schema above. Choose `"shape"` honestly — if your
   service returns search hits, that's `"raw"`; if it returns a
   model-synthesised answer, that's `"synthesized"`.
5. Test the retriever stand-alone via `python <your-script>.py
   "test query"`; verify the JSON return.
6. `/research` picks the new retriever up automatically the next time
   it enumerates `scripts/`.
