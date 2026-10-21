# Physical architecture and bill of materials

Load this when step 7 offers a physical architecture and bill of materials
(BOM), or when the user asks for one on an existing design. The template is
`assets/physical-architecture-bom.md`.

## Start from the design

A design with no deployment model gets no BOM. Say so and offer to write the
design first. Do not invent deployment units.

Every deployment unit in the design's deployment section maps to at least one
BOM line, or is listed as not costed with a reason.

A physical choice that contradicts the design is raised as a design finding.
Never change it silently.

## Line identity

Every BOM line has a `Kind` of exactly `cloud service`, `container image`,
`open-source library`, `hardware`, `network connection`, or `licence`.
`Identifier` says what the item is. `Tier / size` says how big it is. Take each
identifier from the design, the repository, a lock file or manifest, or a cited
provider, vendor, or registry source.

| Kind | `Identifier` | `Tier / size` |
| --- | --- | --- |
| `cloud service` | provider SKU and service identifier | the tier |
| `container image` | registry URI | image size or n/a |
| `open-source library` | package URL (purl) with version, plus SPDX licence identifier | n/a |
| `hardware` | vendor model or part number | CPU, memory, storage and network interface |
| `network connection` | link type, both endpoints, and port or circuit identifier | the bandwidth |
| `licence` | vendor product, edition and licence SKU of commercial software | edition limits or n/a |

A paid support subscription for an open-source library is its own `licence`
line.

An open-source library's version comes from a lock file or manifest, never from
memory. Write it as a purl such as `pkg:pypi/<name>@<version>`.

A container image is written `registry/repository:tag`. It gains
`@sha256:<digest>` only from evidence: a registry listing, a lock file, or a
deployment manifest. An unpublished image gets the visible placeholder
`<registry>/<repository>:<tag>` and a note naming who publishes it. Never
invent a URI or a digest.

## Price status

Every line has one price status.

- `priced`: cites its source, date, and region.
- `unpriced`: a cost exists but is not grounded. Leave these lines out of the
  total and count them.
- `no direct cost`: either names the line that carries its cost, for example an
  image whose cost sits on the line that runs it, or states why the item is
  free to use. For an open-source library the reason is its SPDX identifier.

No price comes from model memory. Ground prices in this order: a curated
platform skill, then the provider's official pricing page or calculator, then
`desk-research`. Use USD unless the user names another currency.

When no provider is chosen, draw the topology at provider-class level and mark
every line `unpriced`.

## Architecture-change altitude

The architecture-change altitude produces a delta BOM. Each line carries a
`Change` of add, remove, or resize. The totals state the net monthly change.

## Arithmetic and totals

Do the arithmetic: `Monthly` is `Qty` times `Unit price` for the period the
price covers. Show a total per environment. Name the currency, the count of
`unpriced` lines, and any excluded costs such as data transfer, support, or
taxes.

## Sequence

1. Offer, once, at the end of step 7.
2. Draft the topology, the diagram, the BOM, and the totals.
3. Save once through step 8.

Save as the sibling `physical-architecture.md` in the same per-effort folder,
using step 8's operating modes and confinement. If the design is not saved yet,
one confirmation covers both files. If it is saved, the BOM saves alone.
