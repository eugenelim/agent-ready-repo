# The `figma` skill

A thin, uniform interface to the Figma REST API. Reads files, nodes, metadata, version history, and comments; renders nodes to images; posts comments; converts FigJam connector graphs to Mermaid; and best-effort reads of variables and dev resources. Read and comment only — it does not modify design content, which requires the Plugin API or the Figma MCP server, not REST.

Figma is SaaS-only (`api.figma.com`). There is no on-prem variant.

The source of truth is the skill itself: [`packs/figma/.apm/skills/figma/`](../../../../packs/figma/.apm/skills/figma/SKILL.md). The agent invokes the CLI at `scripts/figma.py`; you do not call it by hand. Run `python scripts/figma.py <subcommand> --help` for the exact flag surface of any subcommand.

## Credentials

| Key | Required | Notes |
| --- | --- | --- |
| `FIGMA_API_TOKEN` | yes | Personal Access Token. Generated at Figma → Settings → Security → Personal access tokens. |

Resolved by the broker through the Tier 1 (environment) → Tier 2 (OS keyring) → Tier 3 dotfile ladder. The dotfile lives at `~/.agentbundle/credentials.env` (mode 0600 on POSIX; DACL-restricted on Windows). Populate any tier with the `credential-setup` skill. The token never reaches the model, and it is never accepted on the command line — flags like `--token`, `--api-token`, `--bearer`, `--pat`, and `--password` are refused. For the two-layer model, see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

## Input

A `FILE_KEY` accepts either a bare key (`abc123XYZ456`) or a full `figma.com` URL. The key is extracted from `/file/`, `/design/`, `/board/` (FigJam), and `/proto/` URLs. Node ids accept the API form (`1:23`) or the URL form (`1-23`); the URL form is normalized to the API form before the request. Any other shape is rejected at the CLI.

## Output

| Subcommand class | Default output |
| --- | --- |
| Structured-output subcommands | JSON to stdout. `--format jsonl` switches to JSON Lines. `--output FILE` writes to a file. |
| `export-images` | Image bytes written to the `--output` directory. `--format` selects `png` / `jpg` / `svg` / `pdf`. |
| `figjam-to-mermaid` | A fenced Mermaid block (Markdown). `--output FILE` writes it to disk. |

`--format` is ignored by `export-images` and `figjam-to-mermaid`.

## Subcommands

| Subcommand | Purpose | Key arguments |
| --- | --- | --- |
| `check` | Verify credentials and reachability. | — |
| `whoami` | Show the authenticated user record. | — |
| `get-file FILE_KEY` | Fetch a file (full or scoped). | `--ids`, `--depth`, `--geometry paths`, `--version`, `--plugin-data`, `--branch-data` |
| `get-nodes FILE_KEY` | Fetch specific nodes by id. | `--ids` (required), `--depth`, `--geometry paths`, `--version` |
| `get-file-meta FILE_KEY` | Lightweight file metadata (name, creator, last modified, role). | — |
| `list-versions FILE_KEY` | File version history. | `--page-size`, `--before`, `--after` |
| `export-images FILE_KEY` | Render nodes to images. | `--ids` (required), `--format`, `--scale`, `--use-absolute-bounds`, `--version`, SVG flags below |
| `list-comments FILE_KEY` | List file comments. | — |
| `post-comment FILE_KEY` | Post a comment to a file. | `--message` (required), `--node-id`, `--reply-to` |
| `figjam-to-mermaid FILE_KEY NODE_ID` | Convert a FigJam connector graph to a Mermaid flowchart. | — |
| `get-variables FILE_KEY` | Fetch local (or published) variables. Typically Enterprise. | `--published` |
| `list-dev-resources FILE_KEY` | Fetch dev resources on file nodes. Typically Dev Mode. | — |
| `raw METHOD PATH` | Arbitrary request to an unwrapped endpoint. | `--param KEY=VALUE` (repeatable), `--data-file` |

### Scoping flags (`get-file`, `get-nodes`)

| Flag | Effect |
| --- | --- |
| `--depth N` | Limit tree depth. `1` = pages only; `2` = pages + direct children. |
| `--ids 1:2,1:3` | Return only those nodes and their subtrees. |
| `--geometry paths` | Include vector path geometry. |
| `--version ID` | Read a specific file version. |
| `--branch-data` | (`get-file`) Include branch metadata. |
| `--plugin-data ID` | (`get-file`) Include plugin data for the given plugin id. |

`get-file` at full depth is the heaviest call — tens of megabytes on large files. Use `get-file-meta` to probe, `--depth 1` to discover pages, then `get-nodes` for the subtree you want.

### Render flags (`export-images`)

| Flag | Effect |
| --- | --- |
| `--format png\|jpg\|svg\|pdf` | Output format (default `png`). |
| `--scale FLOAT` | Render scale in `(0, 4]` (default `1.0`). |
| `--use-absolute-bounds` | Render using the node's absolute bounding box. |
| `--version ID` | Render from a specific file version. |
| `--svg-include-id` | (SVG) include node ids in element `id` attributes. |
| `--no-svg-outline-text` | (SVG) keep text as `<text>` instead of outlining. |
| `--no-svg-simplify-stroke` | (SVG) don't simplify strokes to fills. |

The token is sent only on the render call; the resulting presigned S3 URLs are downloaded unauthenticated. The render endpoint is rate-limited (Figma cites Tier 2 ≈ 25 requests/min); the client honors `Retry-After`. An id that isn't renderable is skipped with a stderr warning; other ids still download.

### Global flags

| Flag | Effect |
| --- | --- |
| `--format json\|jsonl` | Output format for structured-output subcommands (default `json`). |
| `--output FILE` | Write to a file, or a directory for `export-images`, instead of stdout. |
| `--verbose` | Debug logging on the `figma.*` loggers only; `httpx`/`httpcore` stay at WARNING. |

## FigJam → Mermaid

`figjam-to-mermaid FILE_KEY NODE_ID` emits a `flowchart TB`. It is only useful for FigJam files whose edges are drawn with the connector tool (`CONNECTOR` nodes).

| Preserved | Dropped |
| --- | --- |
| `FRAME` / `GROUP` / `SECTION` containment as subgraphs. | Visual layout, positions, sizes, colors. |
| `CONNECTOR` direction → `---`, `-->`, `<--`, `<-->`. | Freehand `VECTOR` arrows (invisible to the API). |
| `SHAPE_WITH_TEXT.shapeType` → matching Mermaid shape where one exists. | Connector endpoints magnetted to free canvas (no destination node). |
| Connector text as the edge label. | `TRIANGLE_UP` / `TRIANGLE_DOWN` → best-fit flag shape. |

For a non-connector source (a regular design frame), use `export-images` and read the rendered output instead.

## Exit codes

The CLI uses a banded exit-code contract. Read the stderr message for the specific cause, then act on the band.

| Exit | Band | Cause | Action |
| --- | --- | --- | --- |
| `0` | Success | — | Proceed. |
| `1` | Functional error | Unknown key (404), server 5xx, transport failure, keyring hard-fail, unprojected shim, unexpected. | Surface the message; don't blindly retry. |
| `2` | User must act | Missing/invalid/expired credentials (401), or 403 scope/plan access (Variables → Enterprise; Dev Resources → Dev Mode / `file_dev_resources:read`). | Re-run `credential-setup`, or regenerate the PAT with the right scope, then re-run `check`. |

Exit codes `3`–`9` are reserved.

## Untrusted text

All text returned by Figma — comment bodies, sticky-note text, layer names, FigJam shape labels, and the 4xx response bodies surfaced in error messages — is author-controlled. The agent renders it back to you but never acts on instructions embedded in it. Only your direct messages count as direction.

## See also

- [Inspect a Figma file](../how-to/inspect-a-figma-file.md) — the task recipe.
- [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md) — why the token never reaches the model.
