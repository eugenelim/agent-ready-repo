#!/usr/bin/env python3
"""Self-test for the sibling lint-traceability.py (the structural-orphan lint).

Builds fixture workspaces in a tempdir and runs the linter as a subprocess
against the documented `python <skill>/scripts/lint-traceability.py --root <dir>`
invocation — the same shape the CI gate uses (a real subprocess, not a
synthesised import, so the real file-path entry point is exercised). Covers each
acceptance case: no-op clean, the sidecar-authoritative path (converged / orphan
/ dangling / cycle / bad-schema), the derive-from-artifacts standalone path
(clean / backward orphan / forward orphan / terminal exemption / layer-skip),
the three cross-repo endpoint states (local / satisfied-by-reference pinned and
unpinned / unresolvable), dangling-local and cycle hard violations, container
extraction, the exit-code matrix, and the structural-only / stdlib-only /
no-hardcoded-path NFRs.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LINTER = Path(__file__).resolve().parent / "lint-traceability.py"

FAILURES: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def run(root: Path, *extra: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root), *extra],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_spec(root: Path, slug: str, *, status: str = "Draft",
               brief: str | None = None, contract: str | None = None,
               component: str | None = None, discovery: str | None = None) -> None:
    body = f"# Spec: {slug}\n\n- **Status:** {status}\n"
    if brief is not None:
        body += f"- **Brief:** {brief}\n"
    if contract is not None:
        body += f"- **Contract:** {contract}\n"
    if discovery is not None:
        body += f"- **Discovery:** {discovery}\n"
    if component is not None:
        body += f"- **Component:** {component}\n"
    body += "\n## Acceptance Criteria\n\n- [ ] AC1\n"
    write(root / "docs" / "specs" / slug / "spec.md", body)


def write_brief(root: Path, slug: str, *, parent: str | None = None) -> None:
    body = f"# Brief: {slug}\n\n- **Slug:** `{slug}`\n"
    if parent is not None:
        body += f"- **Parent intent:** {parent}\n"
    write(root / "docs" / "product" / "briefs" / f"{slug}.md", body)


def write_component(root: Path, name: str) -> None:
    """A catalogued component — a `packages/<name>/` dir with the Backstage
    `catalog-info.yaml` marker (id `component:default/<name>`)."""
    d = root / "packages" / name
    d.mkdir(parents=True, exist_ok=True)
    write(d / "catalog-info.yaml",
          f"apiVersion: backstage.io/v1alpha1\nkind: Component\nmetadata:\n  name: {name}\n")


def write_sidecar(root: Path, *, nodes: list[dict], edges: list[dict],
                  root_id: str, leaf_kind: str = "component",
                  schema_version: str = "0.1", initiative: str = "demo") -> None:
    payload = {
        "schema_version": schema_version, "initiative": initiative,
        "root": root_id, "leaf_kind": leaf_kind, "nodes": nodes, "edges": edges,
    }
    write(root / "docs" / "discovery" / initiative / "_state" / "traceability.json",
          json.dumps(payload))


def write_rollup(root: Path, rows: list[str]) -> None:
    body = ("| Component | Brief (repo + slug) | Contract@version | "
            "Status (snapshot) | Coverage pointer |\n| --- | --- | --- | --- | --- |\n")
    body += "".join(rows)
    write(root / "docs" / "product" / "rollups" / "rollup.md", body)


# A small full sidecar chain used by several cases (root=o, leaf=component).
def _chain_nodes_edges():
    nodes = [
        {"id": "o", "kind": "outcome", "backed_by": "ladder"},
        {"id": "cap", "kind": "capability", "backed_by": "ladder"},
        {"id": "scr", "kind": "screen", "backed_by": "file"},
        {"id": "act", "kind": "action", "backed_by": "container"},
        {"id": "svc", "kind": "service", "backed_by": "container"},
        {"id": "ctr@1", "kind": "contract", "backed_by": "file"},
        {"id": "sp", "kind": "spec", "backed_by": "file"},
        {"id": "comp", "kind": "component", "backed_by": "file"},
    ]
    edges = [
        {"from": "o", "to": "cap"}, {"from": "cap", "to": "scr"},
        {"from": "scr", "to": "act"}, {"from": "act", "to": "svc"},
        {"from": "svc", "to": "ctr@1"}, {"from": "ctr@1", "to": "sp"},
        {"from": "sp", "to": "comp"},
    ]
    return nodes, edges


# --------------------------------------------------------------------------
# No-op / graceful degradation (AC15)
# --------------------------------------------------------------------------

def case_noop_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rc, out, err = run(Path(tmp))
        expect(rc == 0, f"empty → exit 0, got {rc}")
        expect(out.strip() == "", f"empty → no stdout, got: {out!r}")
        expect(err.strip() == "", f"empty → no stderr, got: {err!r}")


def case_noop_specs_contracts_packages_only() -> None:
    """A repo with specs, contracts, and components but NO discovery anchor must
    no-op — the critical false-activation guard (this bundle's own self-host)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", contract="`docs/contracts/x.json`")
        write_spec(root, "beta")
        write(root / "docs" / "contracts" / "x.json", "{}")
        write_component(root, "agentbundle")
        rc, out, err = run(root)
        expect(rc == 0, f"specs+contracts+packages, no anchor → exit 0, got {rc}: {err}")
        expect(out.strip() == "", f"no anchor → no stdout (no chain), got: {out!r}")


def case_degrades_malformed_sidecar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "docs" / "discovery" / "d" / "_state" / "traceability.json",
              "{ this is not json")
        write_brief(root, "b")
        write_spec(root, "s", brief="b", component="c")
        write_component(root, "c")
        rc, out, err = run(root)
        expect(rc == 0, f"malformed sidecar → degrade, exit 0, got {rc}: {err}")
        expect("malformed" in out.lower() or "derived from artifacts" in out.lower(),
               f"malformed sidecar reported + derives: {out}")


# --------------------------------------------------------------------------
# Sidecar-authoritative path (AC14, AC6, AC9, AC10, AC12)
# --------------------------------------------------------------------------

def case_sidecar_converged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"converged sidecar → exit 0, got {rc}: {err}")
        expect("no structural orphans" in out, f"converged → no orphans: {out}")
        expect("sidecar (authoritative)" in out, f"reports sidecar source: {out}")


def case_sidecar_orphan_and_strict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        edges = [e for e in edges if e != {"from": "ctr@1", "to": "sp"}]  # cut edge
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"orphan default → exit 0 (informational), got {rc}")
        expect("ORPHAN sp" in out and "no producer" in out,
               f"sp is a backward orphan: {out}")
        # The contract loses its consumer too (forward orphan).
        expect("ORPHAN ctr@1" in out, f"ctr@1 forward orphan: {out}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 1, f"orphan + --strict → exit 1, got {rc2}")


def case_sidecar_dangling_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        edges.append({"from": "sp", "to": "ghost"})  # endpoint not in inventory
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 1, f"sidecar dangling → exit 1 always, got {rc}")
        expect("ghost" in err and "DANGLING" in err, f"dangling on stderr: {err}")


def case_sidecar_cycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "b", "kind": "spec"}]
        edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a", leaf_kind="component")
        rc, out, err = run(root)
        expect(rc == 1, f"cycle → exit 1, got {rc}")
        expect("CYCLE" in err, f"cycle reported on stderr: {err}")


def case_sidecar_self_edge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}]
        edges = [{"from": "a", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a")
        rc, out, err = run(root)
        expect(rc == 1, f"self-edge → exit 1, got {rc}")
        expect("self-referential" in err.lower(), f"self-edge reported: {err}")


def case_sidecar_cycle_three_node() -> None:
    """A 3-node cycle exercises the multi-hop stack-slice reconstruction (the
    2-node case and self-edge don't)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "b", "kind": "spec"},
                 {"id": "c", "kind": "spec"}]
        edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "c"},
                 {"from": "c", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a")
        rc, out, err = run(root)
        expect(rc == 1, f"3-node cycle → exit 1, got {rc}")
        expect("CYCLE" in err, f"3-node cycle reported: {err}")


def case_deep_chain_no_crash() -> None:
    """A long linear sidecar chain must terminate (iterative DFS), not overflow
    the recursion limit — the degrade-never-crash contract on untrusted input."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        n = 3000
        nodes = [{"id": f"n{i}", "kind": "spec"} for i in range(n)]
        edges = [{"from": f"n{i}", "to": f"n{i + 1}"} for i in range(n - 1)]
        # leaf_kind=spec so no node needs an out-edge → no orphans, clean exit.
        write_sidecar(root, nodes=nodes, edges=edges, root_id="n0", leaf_kind="spec")
        rc, out, err = run(root)
        expect(rc == 0, f"deep chain → clean exit 0, got {rc}: {err[:200]}")
        expect("RecursionError" not in err and "Traceback" not in err,
               f"no crash on a deep chain: {err[:200]}")


def case_drift_warn_only() -> None:
    """AC14: a spec present on disk but absent from an authoritative sidecar is
    DRIFT — warn-only (exit 0), this spec's firm shipped contract."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "spec:known", "kind": "spec"},
                 {"id": "comp", "kind": "component"}]
        edges = [{"from": "spec:known", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="spec:known")
        write_spec(root, "extra")  # on disk, absent from the sidecar → drift
        rc, out, err = run(root)
        expect(rc == 0, f"drift is warn-only → exit 0, got {rc}: {err}")
        expect("DRIFT (warn-only)" in out and "spec:extra" in out,
               f"drift reported warn-only: {out}")


def case_layout_base_escape_confined() -> None:
    """A layout `[traceability]` base that escapes `--root` (absolute / `..`) is
    ignored, not read — the path-confinement guard."""
    import sys as _sys
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")  # anchor, so the report (incl. notes) prints
        write(root / "agentbundle-layout.toml",
              '[traceability]\nspec = "/etc"\n')
        rc, out, err = run(root)
        expect(rc == 0, f"escaping layout base → no crash, exit 0, got {rc}: {err}")
        if _sys.version_info >= (3, 11):  # tomllib present → layout parsed
            expect("escapes root" in out,
                   f"escaping base reported + ignored: {out}")


def case_catalog_symlink_confined() -> None:
    """A `catalog-info.yaml` symlinked outside `--root` is not followed — the
    nested-read confinement. Skipped where symlinks aren't permitted (Windows)."""
    with tempfile.TemporaryDirectory() as tmp, \
            tempfile.TemporaryDirectory() as outside:
        root = Path(tmp)
        secret = Path(outside) / "secret.yaml"
        secret.write_text("kind: Component\nmetadata:\n  name: PWNED\n  namespace: stolen\n")
        write_brief(root, "b")  # anchor
        cdir = root / "packages" / "c1"
        cdir.mkdir(parents=True)
        try:
            (cdir / "catalog-info.yaml").symlink_to(secret)
        except (OSError, NotImplementedError):
            return  # symlinks unavailable — skip
        rc, out, err = run(root)
        expect("PWNED" not in (out + err) and "stolen" not in (out + err),
               f"escaping catalog-info.yaml symlink not read: {out}{err}")


def case_sidecar_unknown_schema_degrades() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o",
                      schema_version="99.0")
        write_brief(root, "b")
        write_spec(root, "s", brief="b", component="c")
        write_component(root, "c")
        rc, out, err = run(root)
        expect(rc == 0, f"unknown schema → degrade not crash, got {rc}: {err}")
        expect("unrecognized" in out and "derived from artifacts" in out,
               f"unknown schema warns + derives: {out}")


# --------------------------------------------------------------------------
# Standalone derive-from-artifacts path (AC1, AC4, AC6, AC7, AC8)
# --------------------------------------------------------------------------

def case_standalone_clean() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        expect(rc == 0, f"clean standalone → exit 0, got {rc}: {err}")
        expect("no structural orphans" in out, f"clean → no orphans: {out}")
        expect("derived from artifacts" in out, f"reports derived source: {out}")


def case_standalone_backward_orphan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        write_spec(root, "beta", component="beta-svc")  # no producer → orphan
        write_component(root, "beta-svc")
        rc, out, err = run(root)
        expect(rc == 0, f"backward orphan default → exit 0, got {rc}")
        expect("ORPHAN spec:beta" in out and "no producer" in out,
               f"spec:beta backward orphan: {out}")


def case_standalone_forward_orphan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b")  # no Component → forward orphan
        write_component(root, "other-svc")    # component layer populated
        rc, out, err = run(root)
        expect(rc == 0, f"forward orphan default → exit 0, got {rc}")
        expect("ORPHAN spec:alpha" in out and "no consumer" in out,
               f"spec:alpha forward orphan: {out}")


def case_standalone_orphan_component() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        write_component(root, "lonely")  # no spec points at it → backward orphan
        rc, out, err = run(root)
        expect("ORPHAN component:default/lonely" in out and "no producer" in out,
               f"unparented component is a backward orphan: {out}")


def case_terminal_exemption() -> None:
    """component (leaf) is never a forward orphan; the discovery root is never a
    backward orphan."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        # alpha-svc has a producer (the spec) and is leaf → must NOT be flagged.
        expect("ORPHAN component:default/alpha-svc" not in out,
               f"leaf component not a forward orphan: {out}")


def case_layer_skip_globally_unpopulated() -> None:
    """A spec→component edge across the globally-unpopulated contract/service/…
    layers is fine (skip to nearest populated); the spec is not orphaned for
    'skipping' an everywhere-empty layer."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        expect("no structural orphans" in out,
               f"layer-skip across empty layers → no orphan: {out}")


# --------------------------------------------------------------------------
# Cross-repo endpoint states (AC5, AC11, AC13)
# --------------------------------------------------------------------------

def case_crossrepo_pinned() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="payments-api@3")
        write_rollup(root, ["| `payments-api@3` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"pinned cross-repo ref → exit 0, got {rc}")
        expect("satisfied-by-reference (pinned)" in out, f"pinned ref: {out}")
        expect("meta-repo/federated" in out, f"rollup → federated posture: {out}")


def case_crossrepo_unpinned() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/web-app")
        write_rollup(root, ["| `cat:ns/web-app` | `r` · `s` | — | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"unpinned cross-repo ref → exit 0 (never fatal), got {rc}")
        expect("unpinned" in out, f"unpinned soft-warning: {out}")


def case_crossrepo_unresolvable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/uncatalogued")
        # a rollup exists (federated posture) but does not list this id
        write_rollup(root, ["| `something-else` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"unresolvable cross-repo → never fatal, got {rc}")
        expect("unknown / not-yet-catalogued" in out, f"honest gap term: {out}")


def case_dangling_local_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="ghost-local")  # plain slug, missing
        rc, out, err = run(root)
        expect(rc == 1, f"dangling local target → exit 1, got {rc}")
        expect("DANGLING" in err and "ghost-local" in err, f"dangling on stderr: {err}")
        # AC9: one break, one class — the dangling spec must NOT also be a forward
        # ORPHAN (the down edge is asserted, just broken).
        expect("ORPHAN spec:alpha" not in out,
               f"dangling node not also an orphan (AC9): {out}")


def case_up_field_fallthrough_reference() -> None:
    """A cross-repo-shaped (unresolvable) `Contract:` must not shadow a valid
    `Brief:` up-edge: up-fields are alternatives, the first that resolves wins,
    and a well-formed cross-repo reference is not a defect."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        # Contract first, cross-repo-shaped (unresolvable, informational) + Brief.
        write_spec(root, "alpha", brief="b", contract="cat:ns/external-contract")
        rc, out, err = run(root)
        expect(rc == 0, f"valid Brief behind a cross-repo Contract → exit 0, got {rc}: {err}")
        expect("DANGLING" not in err, f"cross-repo ref is not dangling: {err}")
        expect("ORPHAN spec:alpha" not in out,
               f"spec parented via Brief is not an orphan: {out}")


def case_dangling_up_field_still_fires() -> None:
    """AC9: a *dangling* (missing-local-shaped) up-field is a hard violation in
    every mode, fired even when a sibling up-field resolves — but the spec is NOT
    also a backward orphan (the resolving Brief gives it a producer)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", contract="ghost-local")  # bare, missing
        rc, out, err = run(root)
        expect(rc == 1, f"dangling up-field → exit 1 every mode, got {rc}")
        expect("DANGLING" in err and "ghost-local" in err,
               f"broken pointer fires even behind a resolving sibling: {err}")
        expect("ORPHAN spec:alpha" not in out,
               f"resolving Brief means not also a backward orphan: {out}")


# --------------------------------------------------------------------------
# Root→leaf reachability (sidecar mode) — the AC34 disconnected-subtree backstop
# --------------------------------------------------------------------------

# A healthy chain (root=o → spec-h → comp-h, a real component leaf) shared by the
# reachability fixtures so a clean terminus exists; each case bolts a broken branch
# onto the root `o`.
_HEALTHY_NODES = [
    {"id": "o", "kind": "outcome"},
    {"id": "spec-h", "kind": "spec"},
    {"id": "comp-h", "kind": "component"},
]
_HEALTHY_EDGES = [{"from": "o", "to": "spec-h"}, {"from": "spec-h", "to": "comp-h"}]


def case_reach_dead_end_subtree_whole_not_just_tip() -> None:
    """The preconverge "whole subtree" case: a locally-edged dead-end branch where
    every interior node has a producer AND a consumer edge, but the branch never
    reaches a leaf. Presence flags only the tip (no out-edge); reachability flags
    the stranded interior the presence check passes — union = the whole subtree."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "cap-d", "kind": "capability"},
            {"id": "scr-d", "kind": "screen"},
            {"id": "svc-d", "kind": "service"},  # tip — no out-edge
        ]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "cap-d"}, {"from": "cap-d", "to": "scr-d"},
            {"from": "scr-d", "to": "svc-d"},
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        # Presence flags ONLY the tip; the interior is passed by presence.
        expect("ORPHAN svc-d" in out and "no consumer" in out,
               f"presence flags the tip svc-d: {out}")
        expect("ORPHAN cap-d" not in out and "ORPHAN scr-d" not in out,
               f"presence passes the interior nodes: {out}")
        # Reachability flags the interior (which presence passed) — not just the tip.
        expect("UNREACHABLE cap-d" in out and "UNREACHABLE scr-d" in out,
               f"reachability flags the stranded interior: {out}")
        # AC9 — one break, one class: the tip is the presence ORPHAN, not also
        # double-reported as UNREACHABLE.
        expect("UNREACHABLE svc-d" not in out,
               f"tip is the presence orphan, not also UNREACHABLE: {out}")
        # Union covers the whole subtree {cap-d, scr-d, svc-d}.
        expect(rc == 0, f"reachability informational by default → exit 0, got {rc}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 1, f"UNREACHABLE + --strict → exit 1, got {rc2}")


def case_reach_floating_subtree_disconnected_from_root() -> None:
    """The forward-from-root clause: a subtree internally edged and even reaching a
    leaf, but with no path from `root`, is flagged (its source is a presence
    backward orphan; its leaf — passed by presence — is UNREACHABLE)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "spec-f", "kind": "spec"},
            {"id": "comp-f", "kind": "component"},
        ]
        edges = _HEALTHY_EDGES + [{"from": "spec-f", "to": "comp-f"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect("ORPHAN spec-f" in out and "no producer" in out,
               f"floating source is a presence backward orphan: {out}")
        expect("UNREACHABLE comp-f" in out and "not forward-reachable" in out,
               f"floating leaf flagged not-reachable-from-root: {out}")
        expect(rc == 0, f"informational by default → exit 0, got {rc}")


def case_reach_federated_resolved_terminus_not_flagged() -> None:
    """Open-world: a branch whose leaf is a rollup-RESOLVED satisfied-by-reference
    endpoint reaches a clean terminus across the boundary — never flagged."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [{"id": "spec-x", "kind": "spec"}]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "spec-x"}, {"from": "spec-x", "to": "ext-comp@2"},
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        write_rollup(root, ["| `ext-comp@2` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"federated resolved terminus → exit 0, got {rc}: {err}")
        expect("satisfied-by-reference (pinned)" in out,
               f"cross-repo leaf is a resolved reference: {out}")
        expect("UNREACHABLE spec-x" not in out and "ORPHAN spec-x" not in out,
               f"a federated branch is not flagged: {out}")
        expect("DANGLING" not in err,
               f"a cross-repo sidecar endpoint is not dangling: {err}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 0, f"--strict + only a resolved federated leaf → exit 0, got {rc2}")


def case_reach_unresolvable_tip_surfaced_never_silently_green() -> None:
    """The fabricated-edge boundary: a stranded tip whose only out-edge is an
    UNRESOLVABLE (forged-eligible) cross-repo token is NOT a clean terminus — the
    branch is surfaced as a distinct informational finding, never silently green and
    never promoted by --strict (the untrusted-input control-integrity guard)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "cap-u", "kind": "capability"},
            {"id": "scr-u", "kind": "screen"},
        ]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "cap-u"}, {"from": "cap-u", "to": "scr-u"},
            {"from": "scr-u", "to": "forged/x"},  # unresolvable cross-repo token
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"unresolvable tip → never fatal, exit 0, got {rc}: {err}")
        expect("DANGLING" not in err,
               f"a well-formed cross-repo token is not dangling: {err}")
        expect("unknown / not-yet-catalogued" in out,
               f"the forged endpoint is surfaced honestly: {out}")
        expect("reaches a leaf only via an unresolved cross-repo reference" in out,
               f"the stranded branch is surfaced, not silently green: {out}")
        expect("(informational)" in out, f"surfaced informationally: {out}")
        # Critically NOT flagged as a clean pass and NOT promoted by --strict.
        rc2, out2, _ = run(root, "--strict")
        expect(rc2 == 0,
               f"--strict does NOT promote an unresolvable hop, got {rc2}: {out2}")


def case_reach_dangling_adjacent_not_double_reported() -> None:
    """AC9 one-break-one-class: a node whose sole producer edge has a *dangling
    source* (the producer is a missing-local target) is surfaced by the DANGLING
    violation, not ALSO as UNREACHABLE."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [{"id": "mid", "kind": "spec"}]
        edges = _HEALTHY_EDGES + [
            {"from": "ghostsrc", "to": "mid"},  # ghostsrc absent → dangling source
            {"from": "mid", "to": "comp-h"},    # mid does reach a leaf
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 1, f"dangling source → exit 1 every mode, got {rc}")
        expect("DANGLING" in err and "ghostsrc" in err,
               f"the dangling edge is the hard violation: {err}")
        expect("UNREACHABLE mid" not in out,
               f"the dangling-edge consumer is not also UNREACHABLE (AC9): {out}")


def case_reach_skips_without_root() -> None:
    """Graceful, isolated degradation: a sidecar with no declared root, or a root
    absent from the inventory, skips ONLY the reachability pass (a note, no crash)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "comp", "kind": "component"}]
        edges = [{"from": "a", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="")  # → root None
        rc, out, err = run(root)
        expect("reachability skipped" in out and "no root" in out,
               f"rootless sidecar skips reachability with a note: {out}")
        expect("Traceback" not in err, f"no crash on a rootless sidecar: {err}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "comp", "kind": "component"}]
        edges = [{"from": "a", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="ghost-root")
        rc, out, err = run(root)
        expect("reachability skipped" in out and "absent from inventory" in out,
               f"absent declared root skips reachability with a note: {out}")
        expect("Traceback" not in err, f"no crash on an absent-root sidecar: {err}")


def case_reach_degenerate_cases() -> None:
    """Degenerate graphs: a single-node root==leaf is clean; an empty-edge graph
    strands non-root nodes (caught by presence; reachability adds nothing — the
    non-overlap property); a self-loop is termination-safe."""
    # (1) Single node, root == leaf → reachable/clean, no skip.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "comp", "kind": "component"}], edges=[],
                      root_id="comp")
        rc, out, err = run(root)
        expect(rc == 0 and "no structural orphans" in out,
               f"single-node root==leaf is clean: {out}")
        expect("UNREACHABLE" not in out and "reachability skipped" not in out,
               f"root==leaf is reachable, pass runs: {out}")
    # (2) Empty edges, multiple nodes → every non-root node is a presence orphan;
    # reachability adds NO UNREACHABLE (all stranded nodes already presence orphans).
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "o", "kind": "outcome"},
                                   {"id": "x", "kind": "spec"},
                                   {"id": "comp", "kind": "component"}],
                      edges=[], root_id="o")
        rc, out, err = run(root)
        expect("ORPHAN x" in out and "ORPHAN comp" in out,
               f"empty-edge non-root nodes are presence orphans: {out}")
        expect("UNREACHABLE" not in out,
               f"reachability is additive — no double-report on presence orphans: {out}")
        expect("Traceback" not in err, f"no crash on an empty-edge sidecar: {err}")
    # (3) Self-loop on an on-path node → termination-safe, not spuriously flagged
    # (the self-edge itself is the hard violation; reachability must not hang).
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "o", "kind": "outcome"},
                                   {"id": "a", "kind": "spec"},
                                   {"id": "comp", "kind": "component"}],
                      edges=[{"from": "o", "to": "a"}, {"from": "a", "to": "a"},
                             {"from": "a", "to": "comp"}], root_id="o")
        rc, out, err = run(root)
        expect(rc == 1 and "self-referential" in err.lower(),
               f"self-edge is the hard violation: {err}")
        expect("Traceback" not in err and "RecursionError" not in err,
               f"reachability terminates on a self-loop: {err}")
        expect("UNREACHABLE a" not in out and "UNREACHABLE comp" not in out,
               f"on-path nodes not spuriously flagged despite the self-loop: {out}")


# --------------------------------------------------------------------------
# Container-embedded + file-backed recognition (AC1, AC2)
# --------------------------------------------------------------------------

def case_container_and_file_recognition() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # intent ladder: outcome + opportunity (kinds) + capability (level)
        write(root / "docs" / "product" / "intents" / "o.md",
              "# I\n\n- **Slug:** `o`\n- **Kind:** outcome\n")
        write(root / "docs" / "product" / "intents" / "opp.md",
              "# I\n\n- **Slug:** `opp`\n- **Kind:** opportunity\n- **Parent intent:** o\n")
        write(root / "docs" / "product" / "intents" / "cap.md",
              "# I\n\n- **Slug:** `cap`\n- **Level:** capability\n- **Parent intent:** opp\n")
        # journey action + blueprint service
        write(root / "docs" / "product" / "journeys" / "j.md",
              "# J\n\n- **Action:** checkout\n")
        write(root / "docs" / "product" / "blueprints" / "bp.md",
              "# B\n\n- **Service:** payments\n")
        # file-backed screen + contract + spec
        write(root / "docs" / "product" / "screens" / "home.md",
              "# S\n\n- **Type:** screen-brief\n")
        write(root / "docs" / "contracts" / "api" / "pay.v2.json", "{}")
        write_spec(root, "alpha", discovery="cap")
        rc, out, err = run(root)
        # The ladder up-pointers (opp→o, cap→opp) and spec discovery=cap resolve
        # LOCALLY only if the ladder kinds (outcome/opportunity) and level
        # (capability) were each recognized with the right id — so the absence
        # of any DANGLING is itself proof they were extracted.
        expect("DANGLING" not in err,
               f"ladder kinds/level recognized (their up-edges resolve local): {err}")
        # The container-embedded + file-backed unwired nodes surface as ORPHANs
        # under their exact recognized ids — proves the @version contract id and
        # the journey/blueprint entry extraction.
        for nid in ("action:checkout", "service:payments", "screen:home",
                    "contract:pay@2"):
            expect(f"ORPHAN {nid}" in out, f"recognized {nid}: {out}")
        # 8 nodes: outcome:o, opportunity:opp, capability:cap, screen:home,
        # action:checkout, service:payments, contract:pay@2, spec:alpha.
        m = re.search(r"(\d+) node\(s\)", out)
        expect(m is not None and int(m.group(1)) == 8,
               f"exactly the 8 recognized nodes: {out}")


def case_screen_nested_brief_recognized() -> None:
    """A per-screen brief nested under a flow folder
    (`screens/<slug>/<screen>.md` — the shape `map-screen-flow` emits) is
    recognized: `recognize_screens` walks the screens base recursively (the
    `recognize_contracts` precedent), so the brief is found by marker even though
    it is not a flat `screens/*.md` file. A nested screen-flow *file*
    (`type: screen-flow`, no bold-body `**Type:** screen-brief`) is NOT a screen."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # nested per-screen brief — the real producer output path
        write(root / "docs" / "product" / "screens" / "checkout" / "confirm.md",
              "# Screen brief\n\n## Place in the whole\n- **Type:** screen-brief\n")
        # a flat flow file carrying the document-level frontmatter type only
        write(root / "docs" / "product" / "screens" / "checkout-flow.md",
              "---\ntype: screen-flow\n---\n\n# Flow\n")
        # a populated below-layer (journey action) so the recognized screen surfaces
        # by id as a forward orphan — the unambiguous recognition signal.
        write(root / "docs" / "product" / "journeys" / "j.md",
              "# J\n\n- **Action:** checkout\n")
        rc, out, err = run(root)
        expect("ORPHAN screen:confirm" in out,
               f"nested per-screen brief recognized by marker: {out}")
        expect("screen:checkout-flow" not in out and "screen:flow" not in out,
               f"a screen-flow file is not a screen node: {out}")
        expect("DANGLING" not in err, f"no dangling on a nested-brief fixture: {err}")


# --------------------------------------------------------------------------
# Structural-only / output-shape / stdlib / no-hardcoded-path NFRs
# --------------------------------------------------------------------------

def case_no_semantic_vocabulary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "beta", component="beta-svc")  # orphan, produces output
        write_component(root, "beta-svc")
        rc, out, err = run(root)
        banned = ["scope-creep", "semantic", "wrong outcome", "incorrect",
                  "should be parented", "appetite"]
        blob = (out + err).lower()
        for term in banned:
            expect(term not in blob, f"no semantic vocabulary ({term!r}): {blob}")


def case_output_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="ghost")  # dangling → stderr
        rc, out, err = run(root)
        expect(out.startswith("lint-traceability:"), f"stdout report header: {out}")
        expect("lint-traceability:" in err, f"stderr violation prefix: {err}")
        # One-line summary present on stdout.
        expect(any("orphan" in ln for ln in out.splitlines()),
               f"one-line summary present: {out}")


def case_strict_never_promotes_softs() -> None:
    """--strict promotes orphans but NEVER unresolvable-cross-repo / unpinned."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/uncatalogued")
        write_rollup(root, ["| `x` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root, "--strict")
        expect(rc == 0, f"--strict + only unresolvable-cross-repo → exit 0, got {rc}")


def case_stdlib_only() -> None:
    import ast
    tree = ast.parse(LINTER.read_text(encoding="utf-8"))
    stdlib = {"__future__", "argparse", "json", "re", "subprocess", "sys",
              "pathlib", "tomllib", "os"}
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    for mod in sorted(mods):
        expect(mod in stdlib, f"only stdlib imports, found {mod!r}")


def case_no_hardcoded_path() -> None:
    """Every quoted artifact-root segment (`"docs"`/`"packages"` — the giveaway
    of a path shortcut) must live inside the path-defaults registry block."""
    lines = LINTER.read_text(encoding="utf-8").splitlines()
    start = end = None
    for i, ln in enumerate(lines):
        if "path-defaults:start" in ln:
            start = i
        elif "path-defaults:end" in ln:
            end = i
    expect(start is not None and end is not None, "registry block markers present")
    if start is None or end is None:
        return
    for i, ln in enumerate(lines):
        if re.search(r'"(docs|packages)"', ln) and not (start < i < end):
            FAILURES.append(f"hardcoded artifact path at line {i + 1}: {ln.strip()}")


def main() -> int:
    cases = [v for k, v in sorted(globals().items()) if k.startswith("case_")]
    for case in cases:
        try:
            case()
        except Exception as exc:  # a crashing case is itself a failure
            FAILURES.append(f"{case.__name__} raised {exc!r}")
    if FAILURES:
        print(f"test-lint-traceability: {len(FAILURES)} failure(s):", file=sys.stderr)
        for f in FAILURES:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"test-lint-traceability: {len(cases)} case(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
