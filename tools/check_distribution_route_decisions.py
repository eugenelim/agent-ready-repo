#!/usr/bin/env python3
"""Inventory route-selective decisions in shared build-time Python code.

The checker derives its vocabulary from the distribution-route contract and
the bundled build recipes.  It then walks every Python syntax tree in the
selected source root.  Two independent passes cover route-bearing literals
and comparisons that use a route discriminator without spelling a route.

This is deliberately a bounded static check.  It does not claim to interpret
reflection, dynamically generated code, native extensions, or route semantics
hidden behind an unannotated higher-order callback.  Such an escape is emitted
as coverage residue instead of being silently treated as clean.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from os import stat_result
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "packages" / "agentbundle" / "agentbundle"
DEFAULT_CONTRACT = REPO_ROOT / "contracts" / "distribution-routes.toml"
DEFAULT_RECIPES = DEFAULT_SOURCE_ROOT / "build" / "recipes"
EXCLUDED_SHARED_FILES = {
    # This is an installed-client runtime template, not shared build-time code.
    Path("_data/install-marker.py"),
}
# The fields a route value exposes that a decision could branch on. A field added
# to a route type must be added here to be covered; deriving this set from the
# class declarations is part of the route-decision-analysis follow-on.
ROUTE_FIELDS = {
    "identity",
    "route",
    "package_projector",
    "admission_policy",
    "marketplace_projector",
    "lifecycle_trigger",
}
DECISION_CALLS = {"startswith", "endswith"}
# Calls that carry or render a route value without choosing behavior by it.
NON_DECIDING_CALLS = {
    "Path",
    "ResolvedDistributionRoute",
    "ValueError",
    "all",
    "any",
    "dict",
    "frozenset",
    "isinstance",
    "len",
    "list",
    "print",
    "set",
    "sorted",
    "str",
    "tuple",
}
# Types whose values are route discriminators. The value pass is module-local, so
# these are recognised where they are annotated, not across a module boundary.
ROUTE_TYPE_NAMES = {"Recipe", "ResolvedDistributionRoute"}
# Annotations that name data rather than a collaborator. A route-type field
# annotated with one of these holds a value a decision could branch on; anything
# else is something shared code calls through.
PLAIN_ANNOTATION_NAMES = {
    "Any",
    "bool",
    "bytes",
    "dict",
    "float",
    "frozenset",
    "int",
    "list",
    "Mapping",
    "Path",
    "Sequence",
    "set",
    "str",
    "tuple",
}


@dataclass(frozen=True, order=True)
class Finding:
    """One source site where a route discriminator selects behavior."""

    path: str
    line: int
    column: int
    form: str
    shape: str
    detail: str


@dataclass(frozen=True, order=True)
class Residue:
    """One route-value escape the bounded data-flow pass cannot classify."""

    path: str
    line: int
    column: int
    detail: str


@dataclass(frozen=True)
class ScanResult:
    """Deterministic findings and coverage accounting for one source tree."""

    findings: tuple[Finding, ...]
    residue: tuple[Residue, ...]
    python_files: int
    decision_nodes: int
    route_literal_nodes: int
    route_value_decisions: int


def _relative(path: Path, root: Path) -> str:
    """Return a stable POSIX path relative to the scanned source root."""
    return path.relative_to(root).as_posix()


def _string_constant(node: ast.AST) -> str | None:
    """Return a plain string constant without evaluating arbitrary syntax."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _target_names(node: ast.AST) -> set[str]:
    """Collect simple names bound by an assignment target."""
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
    }


def _annotation_names_route(
    annotation: ast.expr | None, carrier_names: set[str] | frozenset[str] = frozenset()
) -> bool:
    """Recognise the route value type without importing production modules."""
    if annotation is None:
        return False
    names = {
        child.id for child in ast.walk(annotation) if isinstance(child, ast.Name)
    }
    return bool(names.intersection(ROUTE_TYPE_NAMES | set(carrier_names)))


def _is_dataclass_definition(node: ast.ClassDef) -> bool:
    """Return whether a class has a syntactic ``dataclass`` decorator."""
    for decorator in node.decorator_list:
        callable_node = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(callable_node, ast.Name) and callable_node.id == "dataclass":
            return True
        if isinstance(callable_node, ast.Attribute) and callable_node.attr == "dataclass":
            return True
    return False


def _route_carrier_fields(tree: ast.Module) -> dict[str, set[str]]:
    """Index dataclass fields that carry route values, including nested carriers."""
    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and _is_dataclass_definition(node)
    }
    fields: dict[str, set[str]] = {}
    changed = True
    while changed:
        changed = False
        carrier_names = set(fields)
        for name, class_node in classes.items():
            route_fields = {
                statement.target.id
                for statement in class_node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and _annotation_names_route(statement.annotation, carrier_names)
            }
            if not route_fields:
                continue
            before = fields.get(name, set())
            combined = before | route_fields
            if combined != before:
                fields[name] = combined
                changed = True
    return fields


def _route_dispatch_fields(tree: ast.Module) -> set[str]:
    """Index route-type fields holding a collaborator rather than a plain value.

    Shared code reaches a route's registered behavior through such a field, so a
    call made through it is dispatch rather than a decision. The field name is
    read from the class definition instead of being fixed here, so renaming the
    field cannot silently widen what this check exempts.
    """
    dispatch: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in ROUTE_TYPE_NAMES:
            continue
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign) or not isinstance(
                statement.target, ast.Name
            ):
                continue
            names = {
                child.id
                for child in ast.walk(statement.annotation)
                if isinstance(child, ast.Name)
            } | {
                child.attr
                for child in ast.walk(statement.annotation)
                if isinstance(child, ast.Attribute)
            }
            if names and not names & (PLAIN_ANNOTATION_NAMES | ROUTE_TYPE_NAMES):
                dispatch.add(statement.target.id)
    return dispatch


def _route_vocabulary(contract_path: Path, recipes_dir: Path) -> set[str]:
    """Derive route names, output roots, and recipe names from owned data."""
    contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
    routes = contract.get("route")
    if not isinstance(routes, dict) or not routes:
        raise ValueError("distribution-route contract has no route table")

    vocabulary: set[str] = set()
    for route_name, body in routes.items():
        if not isinstance(route_name, str) or not isinstance(body, dict):
            raise ValueError("distribution-route contract contains an invalid route")
        vocabulary.add(route_name)
        identity = body.get("identity")
        if isinstance(identity, str):
            vocabulary.add(identity)
        layout = body.get("package-layout")
        if isinstance(layout, dict):
            output_subdir = layout.get("output-subdir")
            if isinstance(output_subdir, str):
                vocabulary.add(output_subdir)

    for recipe_path in sorted(recipes_dir.glob("*.toml")):
        recipe_document = tomllib.loads(recipe_path.read_text(encoding="utf-8"))
        recipe = recipe_document.get("recipe")
        if not isinstance(recipe, dict) or not isinstance(recipe.get("route"), str):
            continue
        name = recipe.get("name")
        route_name = recipe["route"]
        route_tokens = {route_name, route_name.removesuffix("s")}
        if isinstance(name, str) and any(token in name for token in route_tokens):
            vocabulary.add(name)
    return vocabulary


def _contains_route_literal(node: ast.AST, vocabulary: set[str]) -> bool:
    """Report literals that equal a route value or a route-rooted path."""
    for child in ast.walk(node):
        value = _string_constant(child)
        if value is None:
            continue
        if value in vocabulary:
            return True
        if any(value.startswith(f"{item}/") for item in vocabulary):
            return True
    return False


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """Index each syntax node's immediate parent."""
    return {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }


def _nearest(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    kinds: type[ast.AST] | tuple[type[ast.AST], ...],
) -> ast.AST | None:
    """Return the nearest ancestor whose type is in ``kinds``."""
    current = parents.get(node)
    while current is not None:
        if isinstance(current, kinds):
            return current
        current = parents.get(current)
    return None


def _positioned_node(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> ast.AST:
    """Return ``node`` or its nearest ancestor carrying a source position."""
    current = node
    while not hasattr(current, "lineno"):
        parent = parents.get(current)
        if parent is None:
            raise ValueError("decision node has no positioned ancestor")
        current = parent
    return current


def _assigned_literal_collections(
    tree: ast.Module, vocabulary: set[str]
) -> dict[str, ast.Assign | ast.AnnAssign]:
    """Index named collections that carry route-derived literal members."""
    assignments: dict[str, ast.Assign | ast.AnnAssign] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        value = node.value
        if value is None or not isinstance(
            value, (ast.Dict, ast.List, ast.Set, ast.Tuple, ast.Call)
        ):
            continue
        if isinstance(value, ast.Call) and not (
            isinstance(value.func, ast.Name)
            and value.func.id in {"frozenset", "list", "set", "tuple"}
        ):
            continue
        if not _contains_route_literal(value, vocabulary):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            for name in _target_names(target):
                assignments[name] = node
    return assignments


def _loads_any_name(node: ast.AST, names: set[str]) -> bool:
    """Return whether ``node`` loads one of ``names``."""
    return any(
        isinstance(child, ast.Name)
        and isinstance(child.ctx, ast.Load)
        and child.id in names
        for child in ast.walk(node)
    )


def _literal_collection_decisions(
    tree: ast.Module,
    relative_path: str,
    assignments: dict[str, ast.Assign | ast.AnnAssign],
    parents: dict[ast.AST, ast.AST],
) -> list[Finding]:
    """Find decision sinks fed by a named route-literal collection."""
    names = set(assignments)
    findings: list[Finding] = []
    for node in ast.walk(tree):
        shape: str | None = None
        positioned_node: ast.AST = node
        if isinstance(node, ast.Compare) and _loads_any_name(node, names):
            shape = "collection-comparison"
        elif (
            isinstance(node, ast.For | ast.AsyncFor | ast.comprehension)
            and _loads_any_name(node.iter, names)
        ):
            shape = "collection-iteration"
        elif isinstance(node, ast.Subscript) and _loads_any_name(node.value, names):
            shape = "collection-lookup"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in DECISION_CALLS
            and any(_loads_any_name(argument, names) for argument in node.args)
        ):
            shape = f"collection-{node.func.attr}-prefix"
        elif isinstance(node, ast.Call) and any(
            _loads_any_name(argument, names)
            for argument in [*node.args, *(item.value for item in node.keywords)]
        ):
            shape = "collection-argument"
            positioned_node = next(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
                and child.id in names
            )
        if shape is None:
            continue
        positioned_node = _positioned_node(positioned_node, parents)
        findings.append(
            Finding(
                path=relative_path,
                line=positioned_node.lineno,
                column=positioned_node.col_offset + 1,
                form="route-literal",
                shape=shape,
                detail=ast.unparse(node).splitlines()[0],
            )
        )
    return findings


def _literal_decision_owner(
    literal: ast.Constant,
    parents: dict[ast.AST, ast.AST],
    collection_assignments: dict[str, ast.Assign | ast.AnnAssign],
) -> tuple[ast.AST, str] | None:
    """Locate the decision site controlled by a route-bearing literal."""
    current: ast.AST | None = literal
    while current is not None:
        parent = parents.get(current)
        if parent is None:
            return None
        if isinstance(parent, ast.Compare):
            return parent, "comparison"
        if isinstance(parent, ast.For | ast.AsyncFor) and parent.iter is current:
            return parent, "iteration"
        if isinstance(parent, ast.comprehension) and parent.iter is current:
            return parent, "comprehension-iteration"
        if isinstance(parent, ast.keyword) and parent.arg == "choices":
            call = parents.get(parent)
            return (call or parent), "argparse-choices"
        if isinstance(parent, ast.keyword) and "route" in (parent.arg or ""):
            call = parents.get(parent)
            return (call or parent), "route-argument"
        if isinstance(parent, ast.Call):
            function = parent.func
            if isinstance(function, ast.Attribute) and function.attr in DECISION_CALLS:
                return parent, f"{function.attr}-prefix"
        if isinstance(parent, ast.Subscript) and parent.slice is current:
            return parent, "mapping-key"
        if isinstance(parent, ast.Dict):
            owner = _nearest(parent, parents, (ast.Assign, ast.AnnAssign))
            if owner is not None:
                return owner, "dispatch-map"
        if isinstance(parent, ast.Assign | ast.AnnAssign):
            names = _target_names(parent)
            if names.intersection(collection_assignments):
                return parent, "route-collection"
            return parent, "route-path"
        if isinstance(parent, ast.Return):
            return parent, "route-result"
        current = parent
    return None


def _attribute_chain(node: ast.AST) -> tuple[str, ...]:
    """Return the dotted names in an attribute expression."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return tuple(reversed(parts))


def _subscript_key(node: ast.Subscript) -> str | None:
    """Return a constant string key from a subscript expression."""
    return _string_constant(node.slice)


def _uses_route_value(
    node: ast.AST,
    tainted_names: set[str],
    carrier_fields: dict[str, set[str]],
) -> bool:
    """Whether an expression consumes a known route discriminator."""
    parents = _parent_map(node)
    route_fields = ROUTE_FIELDS.union(
        field for fields in carrier_fields.values() for field in fields
    )
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute):
            chain = _attribute_chain(child)
            if (
                chain
                and chain[0] in tainted_names
                and child.attr in route_fields
            ):
                return True
        if isinstance(child, ast.Subscript):
            key = _subscript_key(child)
            if key in route_fields and any(
                isinstance(base, ast.Name) and base.id in tainted_names
                for base in ast.walk(child.value)
            ):
                return True
        if isinstance(child, ast.Name) and child.id in tainted_names:
            current: ast.AST = child
            parent = parents.get(current)
            is_expression_base = False
            while isinstance(parent, ast.Attribute | ast.Subscript):
                if parent.value is not current:
                    break
                is_expression_base = True
                current = parent
                parent = parents.get(current)
            if not is_expression_base:
                return True
    return False


def _is_none_only_compare(node: ast.Compare) -> bool:
    """Ignore presence guards; they do not choose one route over another."""
    values = [node.left, *node.comparators]
    return any(isinstance(value, ast.Constant) and value.value is None for value in values)


def _is_route_value_expression(
    node: ast.AST,
    tainted_names: set[str],
    route_returning_functions: set[str],
    carrier_fields: dict[str, set[str]],
) -> bool:
    """Recognise aliases and direct reads of route discriminator fields."""
    route_fields = ROUTE_FIELDS.union(
        field for fields in carrier_fields.values() for field in fields
    )
    if isinstance(node, ast.Name):
        return node.id in tainted_names
    if isinstance(node, ast.Attribute):
        chain = _attribute_chain(node)
        return bool(
            chain and chain[0] in tainted_names and node.attr in route_fields
        )
    if isinstance(node, ast.Subscript):
        return _subscript_key(node) in route_fields and any(
            isinstance(base, ast.Name) and base.id in tainted_names
            for base in ast.walk(node.value)
        )
    if isinstance(node, ast.Call):
        return (
            isinstance(node.func, ast.Name)
            and node.func.id in route_returning_functions | set(carrier_fields)
        )
    if isinstance(node, ast.IfExp):
        return _is_route_value_expression(
            node.body, tainted_names, route_returning_functions, carrier_fields
        ) or _is_route_value_expression(
            node.orelse, tainted_names, route_returning_functions, carrier_fields
        )
    return False


def _function_arguments(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.arg]:
    """Return parameters in positional-then-keyword-only call order."""
    return [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]


def _annotation_names_carrier(
    annotation: ast.expr | None, carrier_fields: dict[str, set[str]]
) -> bool:
    """Recognise a module-local route-carrier annotation."""
    if annotation is None:
        return False
    return any(
        isinstance(child, ast.Name) and child.id in carrier_fields
        for child in ast.walk(annotation)
    )


def _carrier_instance_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    carrier_fields: dict[str, set[str]],
) -> set[str]:
    """Compute local aliases whose value is a route-bearing dataclass."""
    carrier_names = {
        argument.arg
        for argument in _function_arguments(function)
        if _annotation_names_carrier(argument.annotation, carrier_fields)
    }
    changed = True
    while changed:
        changed = False
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign | ast.AnnAssign) or node.value is None:
                continue
            value = node.value
            is_source = (
                isinstance(value, ast.Name) and value.id in carrier_names
            ) or (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id in carrier_fields
            ) or (
                isinstance(node, ast.AnnAssign)
                and _annotation_names_carrier(node.annotation, carrier_fields)
            )
            if not is_source:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            before = len(carrier_names)
            for target in targets:
                carrier_names.update(_target_names(target))
            changed = changed or len(carrier_names) != before
    return carrier_names


def _is_contract_selected_carrier_call(
    call: ast.Call,
    tainted_names: set[str],
    carrier_names: set[str],
    carrier_fields: dict[str, set[str]],
    dispatch_fields: set[str],
) -> bool:
    """Recognise a carrier passed into behavior selected from a route value."""
    if not isinstance(call.func, ast.Attribute):
        return False
    callable_chain = _attribute_chain(call.func)
    if (
        not callable_chain
        or callable_chain[0] not in tainted_names
        or callable_chain[0] in carrier_names
        or not set(callable_chain[1:-1]) & dispatch_fields
    ):
        return False
    return any(
        (isinstance(argument, ast.Name) and argument.id in carrier_names)
        or (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id in carrier_fields
        )
        or (
            isinstance(argument, ast.Attribute)
            and argument.attr in ROUTE_FIELDS
        )
        for argument in [*call.args, *(keyword.value for keyword in call.keywords)]
    )


def _tainted_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    route_returning_functions: set[str],
    carrier_fields: dict[str, set[str]],
    propagated_parameters: set[str] | None = None,
) -> set[str]:
    """Compute a local fixed point for route discriminator aliases.

    Names holding a *container* of route values are tracked separately: they can
    be iterated to reach a route value, but using one is not itself a decision.
    """
    tainted = {
        argument.arg
        for argument in _function_arguments(function)
        if _annotation_names_route(argument.annotation, set(carrier_fields))
    }
    tainted.update(propagated_parameters or set())
    changed = True
    while changed:
        changed = False
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign | ast.AnnAssign) or node.value is None:
                continue
            value = node.value
            is_source = _is_route_value_expression(
                value, tainted, route_returning_functions, carrier_fields
            ) or (
                isinstance(node, ast.AnnAssign)
                and _annotation_names_route(node.annotation, set(carrier_fields))
            )
            if not is_source:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            before = len(tainted)
            for target in targets:
                tainted.update(_target_names(target))
            changed = changed or len(tainted) != before
    return tainted


def _propagated_route_parameters(
    tree: ast.Module, carrier_fields: dict[str, set[str]]
) -> tuple[
    dict[ast.FunctionDef | ast.AsyncFunctionDef, set[str]],
    dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
]:
    """Propagate discriminator arguments across direct same-module calls."""
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    by_name: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    ambiguous: set[str] = set()
    for function in functions:
        if function.name in by_name:
            ambiguous.add(function.name)
        else:
            by_name[function.name] = function
    for name in ambiguous:
        by_name.pop(name, None)

    route_returning_functions = {
        function.name
        for function in functions
        if _annotation_names_route(function.returns, set(carrier_fields))
    }
    propagated = {function: set() for function in functions}
    changed = True
    while changed:
        changed = False
        for caller in functions:
            tainted = _tainted_names(
                caller, route_returning_functions, carrier_fields, propagated[caller]
            )
            for call in (
                node for node in ast.walk(caller) if isinstance(node, ast.Call)
            ):
                if not isinstance(call.func, ast.Name):
                    continue
                callee = by_name.get(call.func.id)
                if callee is None:
                    continue
                parameters = _function_arguments(callee)
                additions: set[str] = set()
                for index, argument in enumerate(call.args):
                    if index < len(parameters) and _uses_route_value(
                        argument, tainted, carrier_fields
                    ):
                        additions.add(parameters[index].arg)
                parameters_by_name = {
                    parameter.arg: parameter for parameter in parameters
                }
                for keyword in call.keywords:
                    if (
                        keyword.arg in parameters_by_name
                        and _uses_route_value(keyword.value, tainted, carrier_fields)
                    ):
                        additions.add(keyword.arg)
                before = len(propagated[callee])
                propagated[callee].update(additions)
                changed = changed or len(propagated[callee]) != before
    return propagated, by_name


def _route_value_findings(
    tree: ast.Module,
    relative_path: str,
    vocabulary: set[str],
    carrier_fields: dict[str, set[str]],
) -> tuple[list[Finding], list[Residue]]:
    """Find no-literal comparisons and unsupported route-value escapes."""
    findings: list[Finding] = []
    residue: list[Residue] = []
    dispatch_fields = _route_dispatch_fields(tree)
    propagated, local_functions = _propagated_route_parameters(tree, carrier_fields)
    route_returning_functions = {
        function.name
        for function in propagated
        if _annotation_names_route(function.returns, set(carrier_fields))
    }
    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ):
        tainted = _tainted_names(
            function, route_returning_functions, carrier_fields, propagated[function]
        )

        carrier_names = _carrier_instance_names(function, carrier_fields)
        for node in ast.walk(function):
            if isinstance(node, ast.Compare):
                if (
                    _is_none_only_compare(node)
                    or _contains_route_literal(node, vocabulary)
                    or not _uses_route_value(node, tainted, carrier_fields)
                ):
                    continue
                findings.append(
                    Finding(
                        path=relative_path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        form="contract-derived-value",
                        shape="comparison",
                        detail=ast.unparse(node),
                    )
                )
            elif isinstance(node, ast.If | ast.While | ast.IfExp):
                if any(isinstance(child, ast.Compare) for child in ast.walk(node.test)):
                    continue
                if not _uses_route_value(node.test, tainted, carrier_fields):
                    continue
                findings.append(
                    Finding(
                        path=relative_path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        form="contract-derived-value",
                        shape="conditional",
                        detail=ast.unparse(node.test),
                    )
                )
            elif isinstance(node, ast.Match) and _uses_route_value(
                node.subject, tainted, carrier_fields
            ):
                findings.append(
                    Finding(
                        path=relative_path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        form="contract-derived-value",
                        shape="match",
                        detail=ast.unparse(node.subject),
                    )
                )
            elif (
                isinstance(node, ast.Subscript)
                and _uses_route_value(node.slice, tainted, carrier_fields)
                and _subscript_key(node) not in ROUTE_FIELDS
            ):
                findings.append(
                    Finding(
                        path=relative_path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        form="contract-derived-value",
                        shape="mapping-lookup",
                        detail=ast.unparse(node),
                    )
                )

        # Calls are the only supported inter-function propagation boundary.
        # Passing a discriminator to an unresolved callable is coverage residue.
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
            arguments = [*call.args, *(kw.value for kw in call.keywords)]
            if not any(
                _uses_route_value(argument, tainted, carrier_fields)
                for argument in arguments
            ):
                continue
            if isinstance(call.func, ast.Name) and call.func.id in local_functions:
                continue
            if isinstance(call.func, ast.Name) and call.func.id in NON_DECIDING_CALLS:
                continue
            if (
                isinstance(call.func, ast.Name)
                and call.func.id in carrier_fields
            ):
                continue
            if _is_contract_selected_carrier_call(
                call, tainted, carrier_names, carrier_fields, dispatch_fields
            ):
                continue
            if isinstance(call.func, ast.Attribute) and call.func.attr in {
                "append",
                "get",
                "rstrip",
            }:
                continue
            residue.append(
                Residue(
                    path=relative_path,
                    line=call.lineno,
                    column=call.col_offset + 1,
                    detail=f"route value passed to unresolved call: {ast.unparse(call.func)}",
                )
            )
    return findings, residue


def scan_tree(
    source_root: Path,
    contract_path: Path,
    recipes_dir: Path,
) -> ScanResult:
    """Scan a shared Python tree and return deterministic evidence."""
    vocabulary = _route_vocabulary(contract_path, recipes_dir)
    findings: set[Finding] = set()
    residue: set[Residue] = set()
    python_files = 0
    decision_nodes = 0
    route_literal_nodes = 0

    for path in sorted(source_root.rglob("*.py")):
        relative = Path(_relative(path, source_root))
        if relative in EXCLUDED_SHARED_FILES or "__pycache__" in relative.parts:
            continue
        python_files += 1
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=relative.as_posix())
        except SyntaxError as exc:
            residue.add(
                Residue(
                    path=relative.as_posix(),
                    line=exc.lineno or 1,
                    column=exc.offset or 1,
                    detail="Python source could not be parsed",
                )
            )
            continue
        parents = _parent_map(tree)
        assignments = _assigned_literal_collections(tree, vocabulary)
        decision_nodes += sum(
            isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.IfExp,
                    ast.Compare,
                    ast.Match,
                    ast.For,
                    ast.AsyncFor,
                    ast.comprehension,
                ),
            )
            for node in ast.walk(tree)
        )
        for literal in (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ):
            if not _contains_route_literal(literal, vocabulary):
                continue
            route_literal_nodes += 1
            owner = _literal_decision_owner(literal, parents, assignments)
            if owner is None:
                continue
            site, shape = owner
            positioned_site = site if hasattr(site, "lineno") else literal
            column = positioned_site.col_offset + 1 if hasattr(site, "lineno") else 1
            findings.add(
                Finding(
                    path=relative.as_posix(),
                    line=positioned_site.lineno,
                    column=column,
                    form="route-literal",
                    shape=shape,
                    detail=ast.unparse(site).splitlines()[0],
                )
            )

        findings.update(
            _literal_collection_decisions(
                tree, relative.as_posix(), assignments, parents
            )
        )

        carrier_fields = _route_carrier_fields(tree)
        value_findings, value_residue = _route_value_findings(
            tree,
            relative.as_posix(),
            vocabulary,
            carrier_fields,
        )
        findings.update(value_findings)
        residue.update(value_residue)

    ordered_findings = tuple(sorted(findings))
    ordered_residue = tuple(sorted(residue))
    return ScanResult(
        findings=ordered_findings,
        residue=ordered_residue,
        python_files=python_files,
        decision_nodes=decision_nodes,
        route_literal_nodes=route_literal_nodes,
        route_value_decisions=sum(
            finding.form == "contract-derived-value" for finding in ordered_findings
        ),
    )


def _git_commit(repo_root: Path) -> str:
    """Read the local measuring commit without contacting a remote."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _artifact(result: ScanResult, measuring_commit: str) -> dict[str, object]:
    """Build the stable baseline document written by the CLI."""
    return {
        "schema": "distribution-route-decision-baseline.v1",
        "measuring_commit": measuring_commit,
        "scope": "packages/agentbundle/agentbundle/**/*.py shared build-time code",
        "excluded": sorted(path.as_posix() for path in EXCLUDED_SHARED_FILES),
        "limits": [
            "reflection and dynamically generated Python are not interpreted",
            "native extensions and non-Python decision surfaces are outside this scan",
            "unannotated higher-order route-value flow is reported as coverage residue",
            "route-bearing dataclass carriers are followed transitively within one "
            "module; carrier annotations imported from another module are not resolved",
            "the value pass is module-local: a route value handed across a module "
            "boundary reaches its consumer untainted, so a decision made on it there "
            "is not reported. Closing that is tracked by the route-decision-analysis "
            "follow-on",
            "a call made through a route type's declared collaborator field, passing "
            "only carriers or the route's own declared fields, is read as dispatch "
            "rather than a decision",
            "dispatch spelled `mapping.get(route_value)` is not reported; the "
            "subscript form `mapping[route_value]` is. Covering both is part of the "
            "route-decision-analysis-depth follow-on",
            "a per-route projector identity — the `manifest-projector.name`, "
            "`package-layout.name` or `marketplace-projector` value a registration "
            "seam matches on — is not vocabulary, so shared code keying behavior off "
            "one is not reported. Covering it needs an exemption for the modules that "
            "legitimately match on it, which the same follow-on carries",
            "a route-bearing annotation written as a quoted forward reference is not "
            "recognised as a taint source; this tree uses postponed evaluation, so "
            "bare annotations are the idiom, but a quoted one would evade the value "
            "form",
        ],
        "mutations": [
            {
                "form": "shared-code-route-literal",
                "source": 'return candidate == "apm"',
                "why": "kills an inline route-name comparison",
            },
            {
                "form": "shared-code-route-literal",
                "source": 'ROUTES = {"apm", "claude-plugins"}; return candidate in ROUTES',
                "why": "kills a separated literal collection and its later decision sink",
            },
            {
                "form": "shared-code-route-literal",
                "source": 'HANDLERS = {"apm": handler}',
                "why": "kills a route-keyed dispatch map",
            },
            {
                "form": "shared-code-route-literal",
                "source": 'parser.add_argument("--route", choices=["apm"])',
                "why": "kills a route enumeration in an argument list",
            },
            {
                "form": "shared-code-route-literal",
                "source": 'return path.startswith(("apm/", "claude-plugins/"))',
                "why": "kills route-root prefixes that a bare-name search misses",
            },
            {
                "form": "contract-derived-route-value",
                "source": "return resolved.identity == some_key",
                "why": "kills a route decision with no route literal present",
            },
            {
                "form": "contract-derived-route-value",
                "source": "return handlers[resolved.identity]",
                "why": "kills a lookup decision with no comparison or route literal",
            },
            {
                "form": "contract-derived-route-value",
                "source": (
                    "@dataclass(frozen=True)\n"
                    "class Context:\n"
                    "    resolved_route: ResolvedDistributionRoute\n"
                    "return context.resolved_route.identity == some_key"
                ),
                "why": "kills a decision reached through a route-bearing dataclass field",
            },
        ],
        "coverage": {
            "python_files": result.python_files,
            "decision_nodes": result.decision_nodes,
            "route_literal_nodes": result.route_literal_nodes,
            "route_value_decisions": result.route_value_decisions,
            "residue_count": len(result.residue),
        },
        "findings": [asdict(finding) for finding in result.findings],
        "coverage_residue": [asdict(item) for item in result.residue],
    }


def _measured_evidence(document: dict[str, object]) -> dict[str, object]:
    """Return only what a scan measured, dropping the checker's own prose.

    `limits` and `mutations` describe the checker, not the tree it measured, so
    comparing them would make a pre-change baseline unreproducible the moment
    the checker gains coverage — which is the opposite of what the baseline is
    for. Reproduction is judged on findings, residue, coverage, and scope.
    """
    return {
        key: value
        for key, value in document.items()
        if key not in {"limits", "mutations"}
    }


def _confined_output_path(path: Path, repo_root: Path) -> Path:
    """Resolve a single-link regular output path inside the repository."""
    root = repo_root.resolve(strict=True)
    candidate = path if path.is_absolute() else root / path
    if candidate.name in {"", ".", ".."} or ".." in candidate.parts:
        raise ValueError("baseline output must name a file")
    resolved_parent = candidate.parent.resolve(strict=False)
    resolved = resolved_parent / candidate.name
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("baseline output must stay inside the repository") from exc

    current = candidate.parent
    while current != root:
        if current.exists() and current.is_symlink():
            raise ValueError("baseline output parent must not be a symbolic link")
        current = current.parent
    if candidate.exists() or candidate.is_symlink():
        metadata: stat_result = candidate.stat(follow_symlinks=False)
        if candidate.is_symlink() or not candidate.is_file() or metadata.st_nlink != 1:
            raise ValueError("baseline output must be a single-link regular file")
    return resolved


def write_baseline(
    path: Path,
    result: ScanResult,
    measuring_commit: str,
    repo_root: Path,
) -> None:
    """Write a complete baseline atomically without shell redirection."""
    output = _confined_output_path(path, repo_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(
                json.dumps(
                    _artifact(result, measuring_commit), indent=2, sort_keys=True
                )
                + "\n"
            )
        temporary.replace(output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _load_baseline(path: Path) -> dict[str, object]:
    """Load one baseline document for exact reproduction checks."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("baseline root must be an object")
    return document


def _baseline_commit(document: dict[str, object]) -> str:
    """Return the baseline's recorded full commit identifier."""
    value = document.get("measuring_commit")
    if not isinstance(value, str) or len(value) != 40 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("baseline measuring_commit must be 40 lowercase hex digits")
    return value


def _sources_match_commit(
    commit: str,
    source_root: Path,
    contract_path: Path,
    recipes_dir: Path,
    repo_root: Path,
) -> bool:
    """Return whether every measured input matches the recorded commit."""
    root = repo_root.resolve(strict=True)
    relative_paths: list[str] = []
    for path in (source_root, contract_path, recipes_dir):
        resolved = path.resolve(strict=True)
        try:
            relative_paths.append(resolved.relative_to(root).as_posix())
        except ValueError as exc:
            raise ValueError("measured inputs must stay inside the repository") from exc
    completed = subprocess.run(
        ["git", "diff", "--quiet", commit, "--", *relative_paths],
        cwd=root,
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError("git could not compare measured inputs to the baseline commit")
    return completed.returncode == 0


def _print_result(result: ScanResult) -> None:
    """Render findings and coverage residue for humans and CI logs."""
    for finding in result.findings:
        print(
            f"{finding.path}:{finding.line}:{finding.column}: "
            f"{finding.form}/{finding.shape}: {finding.detail}"
        )
    for item in result.residue:
        print(
            f"{item.path}:{item.line}:{item.column}: coverage-residue: "
            f"{item.detail}"
        )
    print(
        "summary: "
        f"{len(result.findings)} decision(s), {len(result.residue)} residue item(s), "
        f"{result.python_files} Python file(s), {result.decision_nodes} decision node(s)"
    )


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Inventory route-selective decisions in shared Python code."
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--recipes", type=Path, default=DEFAULT_RECIPES)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--write-baseline",
        type=Path,
        metavar="PATH",
        help="write the measured findings and local commit to PATH",
    )
    action.add_argument(
        "--verify-baseline",
        type=Path,
        metavar="PATH",
        help="reproduce PATH and fail on any difference",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="fail when a forbidden decision or coverage residue remains",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected evidence mode and return a process exit status."""
    args = _parser().parse_args(argv)
    result = scan_tree(args.source_root, args.contract, args.recipes)
    measuring_commit = _git_commit(REPO_ROOT)
    _print_result(result)

    if args.write_baseline is not None:
        write_baseline(args.write_baseline, result, measuring_commit, REPO_ROOT)
        print(f"wrote baseline: {args.write_baseline}")
        return 0 if not result.residue else 2
    if args.verify_baseline is not None:
        expected = _load_baseline(args.verify_baseline)
        recorded_commit = _baseline_commit(expected)
        if not _sources_match_commit(
            recorded_commit,
            args.source_root,
            args.contract,
            args.recipes,
            REPO_ROOT,
        ):
            print(
                "measured inputs differ from the baseline commit", file=sys.stderr
            )
            return 1
        actual = _artifact(result, recorded_commit)
        if _measured_evidence(expected) != _measured_evidence(actual):
            print("baseline differs from the current tree", file=sys.stderr)
            return 1
        print("baseline reproduced exactly")
        return 0
    return 0 if not result.findings and not result.residue else 1


if __name__ == "__main__":
    raise SystemExit(main())
