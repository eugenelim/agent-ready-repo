# Inspect a Figma file

**Use this when:** you have a Figma URL and need to read page or frame structure, metadata, comments, version history, render frames to images, or convert a FigJam connector diagram to Mermaid.
**Prerequisites:** `figma` pack installed and a Figma Personal Access Token stored via `credential-setup`.
**Result:** the requested Figma content retrieved and reported — page list, node structure, comment threads, rendered image files, or a Mermaid diagram — without any edits to the design file.

You have a Figma URL and you want what's inside it: the page list, a specific frame, the file's metadata, the comments, a rendered image, or the structure of a FigJam board. The `figma` skill reads all of it over the REST API. It never edits design content — REST can't.

## Before you start

`figma` is a credentialed skill. It needs a Figma Personal Access Token, resolved in-process so it never reaches the model — see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md). If `check` reports missing credentials, run the `credential-setup` skill yourself (it's interactive) and enter your token. Generate one at Figma → Settings → Security → Personal access tokens.

You don't run the CLI by hand. Ask the agent for what you want and it dispatches the right subcommand. The recipes below are what it does under the hood, and the variations worth knowing.

## Pass a URL or a key

Every file operation takes a `FILE_KEY`. Hand the agent the whole URL — `https://www.figma.com/design/<KEY>/<name>`, a `/file/`, `/board/`, or `/proto/` link — and the key is extracted for you. A bare key works too. Node ids work in either form: the `1:23` shape from API responses or the `1-23` shape from a `node-id=` URL param.

## Probe before you pull

`get-file` returns the entire document. On a large file that's tens of megabytes of JSON. Start cheap:

- **Metadata only** — name, creator, last modified, your role. The fastest way to confirm a key is reachable.
- **Pages only** (`--depth 1`) — discover the canvases before drilling in.
- **A page and its children** (`--depth 2`) — a quick "what's on each page".

Then scope down to what you actually want:

- **Specific nodes** — fetch just the subtrees under given node ids, without dragging the whole document.

For a big file, the pattern is: pages first, then nodes for the one subtree you care about. Don't ask for full depth you won't read.

## Read the version history and comments

- **Version history** lists named and autosaved versions, newest first, with paging if the history is long.
- **Comments** lists every comment thread on the file. Reads are safe.

You can also post a comment, but treat that like a git push — it's visible to every collaborator. Confirm the file, the message, and the target node before you ask the agent to post. Comments can be file-level, pinned to a node, or a reply to an existing thread.

## Render a frame to an image

Rendering goes through Figma's render endpoint and downloads the result to a directory you name. Pick the format and scale:

- Formats: `png`, `jpg`, `svg`, `pdf`.
- Scale is any value in `(0, 4]`; `2` gives you a crisp 2x raster.
- SVG has its own knobs (outline text, simplify strokes, include node ids).

Batch the node ids into one render call rather than looping — the render endpoint is rate-limited, and the client already honors `Retry-After` for you. If a node isn't renderable (say, a bounds-less section), that id is skipped with a warning and the rest still download.

This is also your fallback for diagrams that aren't connector graphs: render the frame and let the agent look at the picture.

## Turn a FigJam board into Mermaid

For a FigJam board whose edges are drawn with the **connector tool**, the skill walks the node tree and emits a Mermaid `flowchart TB`. Point it at the board's file and the node id of the frame, section, or page to convert.

What survives the conversion:

- Containment — frames, groups, and sections become Mermaid subgraphs.
- Connector direction — arrowheads map to `---`, `-->`, `<--`, or `<-->`.
- Shape types where a Mermaid primitive exists (rectangle, rounded, ellipse, diamond, parallelogram, cloud, database).
- Text on a connector becomes the edge label.

What doesn't:

- Visual layout, colors, and sizes — Mermaid lays out its own.
- Arrows drawn freehand instead of with the connector tool — invisible to the API.
- Connectors that magnet to empty canvas instead of to a node — dropped, there's nothing to point at.
- Triangles — Mermaid has no triangle, so they collapse to a best-fit flag.

If the source is a regular design frame with no connectors, you'll get a flat list of shapes. Render it to an image instead.

## When something fails

The CLI uses banded exit codes. The two you'll see most:

- **User must act** — the token is missing, invalid, expired, or lacks the scope a request needs (Variables typically need Enterprise; Dev Resources typically need Dev Mode). Re-run `credential-setup`, or regenerate the PAT with the right scope, then retry. The agent won't run setup for you.
- **Functional error** — an unknown key (404), a server 5xx, or a transport failure. Check the URL or key; don't blindly retry.

## See also

- [The `figma` skill reference](../reference/figma-skill.md) — every subcommand, flag, and exit code.
- [The `figma` skill itself](../../../../packs/figma/.apm/skills/figma/SKILL.md) — the source of truth the agent reads.
