# draw.io export — Mermaid to a `.drawio` file

Mermaid stays the source of truth. A `.drawio` file is a derived copy for
people who want to keep editing in draw.io. Never draw a different diagram
in it.

## When to use

- Only when the user asks for draw.io or a `.drawio` file. Never by default.
- Save the `.mmd` first. The `.drawio` is converted from that file.
- **Chat-only mode:** there is no file to convert. Give these steps, or offer
  to save first: in draw.io choose Arrange › Insert › Advanced › Mermaid,
  paste the diagram, and insert it.
- **Repository-handoff mode:** list the `.drawio` as one more needed write
  beside the `.mmd`. Write nothing and run nothing.

## Find the CLI

Check in this order and use the first hit:

1. `drawio`, then `draw.io`, on PATH.
2. macOS: `/Applications/draw.io.app/Contents/MacOS/draw.io`, then
   `~/Applications/draw.io.app/Contents/MacOS/draw.io`.
3. Windows: `%ProgramFiles%\draw.io\draw.io.exe`, then
   `%LOCALAPPDATA%\Programs\draw.io\draw.io.exe`.

Confirm with `<cli> --version`. The minimum is 31.7.0, the first release that
imports Mermaid from the command line. An older version gets an upgrade offer
under the install rule below.

- On a headless Linux host, prefix the command with `xvfb-run -a`.
- Snap builds cannot read `/tmp`. Keep the save directory under the user's
  home.

## Offer an install

If no CLI is found, offer to install one. An install changes the user's
machine, so it needs consent.

- Show exactly one command from this list, the one for the user's OS:

```text install-allowlist
brew install --cask drawio
winget install -e --id JGraph.Draw
sudo snap install drawio
```

- Say that the command installs software. For the snap line, also say it
  needs administrator rights.
- Wait for an explicit yes given after the command was shown. A yes covers
  only that command. Wording in the original request does not count.
- Never download an installer, compose a URL, or pipe anything into a shell.
- Without the matching package manager, link
  https://github.com/jgraph/drawio-desktop/releases for a manual install and
  run nothing.
- After the install, detect the CLI again.
- If the install fails, report it. Do not retry and do not change the command.

## Convert

Run, with `<dir>` the save directory's resolved absolute path and `<stem>` the
kebab-case slug from the save step:

`<cli> --disable-update -x -f xml -u -o <dir>/<stem>.drawio <dir>/<stem>.mmd`

- Pass the arguments as a list, not as one shell string.
- If `<dir>/<stem>.drawio` exists, ask before replacing it.
- Do not pass `-k`. It makes the CLI write a different file, `<stem>-1.drawio`,
  that nobody sees.
- Report the path actually written.
- Leave Mermaid `click` and `href` lines out of diagrams meant for export. If a
  saved `.mmd` has them, name them and ask the user to remove them first.

## Check the output

Run this on every `.drawio` before presenting it, whether the CLI or the
fallback wrote it:

- The file parses as an uncompressed `mxfile` with at least one vertex.
- No element has a `link` or `href` attribute, including `xlink:href`.
- No `value`, `label`, or `tooltip` contains an anchor tag or an `href=`.
  Case-fold the text and remove control characters first. An anchor tag is `<a`
  followed by whitespace, `/`, or `>`. An `href=` may have whitespace before the
  `=`.
- Every style `image=` entry, with whitespace and control characters removed,
  starts with `data:image/`. That is the CLI's own icon encoding, and nothing
  else may act as a URL.
- Every node label and every sequence participant label in the saved `.mmd`
  equals some cell `value` or `label`. Unescape XML and normalise whitespace on
  both sides first. Edge labels and subgraph titles are not compared.
- Fallback only: no cell style sets `html=1`. CLI output carries it
  legitimately.

A failed check blocks. Report it and do not present the file as done.

Things to know:

- The Mermaid parser is lenient. Malformed Mermaid can exit 0 with a wrong
  diagram. Run the rubric self-check before converting. The label check then
  catches a node that went missing.
- Empty or unsupported Mermaid exits 1 with "Error parsing Mermaid" and writes
  nothing. Report the error.
- `architecture-beta` icons arrive as image cells, not editable shapes.

## Fallback when the user declines the install

Transcribe the saved `.mmd` node for node and edge for edge into uncompressed
draw.io XML. Do not add, drop, or rename anything.

- Nest `mxfile` → `diagram` → `mxGraphModel` → `root`.
- Put cells `0` and `1` first.
- Give every vertex an `mxGeometry` with x, y, width, and height, on a simple
  grid.
- Give every edge a `source`, a `target`, and
  `<mxGeometry relative="1" as="geometry"/>`.
- Keep ids unique.
- Escape every label for XML and write it as plain text. No `html=1`. No link
  attribute.

Skeleton:

```xml
<mxfile>
  <diagram id="d1" name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="a" value="Client" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="b" value="API &amp; Gateway" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="1">
          <mxGeometry x="240" y="40" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="e1" value="" edge="1" source="a" target="b" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Then run the output check above. Tell the user the layout is hand-placed and
that Arrange › Layout in draw.io can tidy it. Also give the Insert › Mermaid
steps from the first section, which lay the diagram out automatically.
