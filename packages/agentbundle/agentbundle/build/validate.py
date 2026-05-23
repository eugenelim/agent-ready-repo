"""Stdlib-only JSON-Schema subset validator.

The build pipeline depends on stdlib only (per spec § Boundaries —
Never do), so we cannot import a JSON-Schema library. This module
ships the subset RFC-0001 + spec AC #6 commit to:

Supported keywords:
  - `type`: one of "object", "array", "string", "integer", "boolean"
  - `properties`: object → schema map (only meaningful when type=object)
  - `required`: list of property names (only meaningful when type=object)
  - `enum`: list of allowed scalar values
  - `pattern`: regex string applied to strings (via `re`)
  - `items`: schema applied element-wise (only meaningful when type=array)
  - `additionalProperties`: bool or schema (only meaningful when type=object)
  - `minItems`: integer; array must have at least this many items
  - `contains`: subschema; array must have at least one item matching it
  - `if` / `then` / `else`: conditional subschemas (all three applied to
    the same instance as the parent). RFC-0004's pack.schema.json uses
    this trio to express "v0.2 packs require `[pack.install]`" and
    "default-scope ∈ allowed-scopes."

Unsupported by design: `$ref`, `$defs`, `oneOf`, `anyOf`, `allOf`,
`not`, `format`, `minimum`/`maximum`, `minLength`/`maxLength`. If the
contract grows a need, an RFC amends this subset; the validator does
not silently expand.

`validate(instance, schema)` returns a list of error strings — empty
list means valid. Callers decide how to surface (the CLI's `validate`
subcommand prints them to stderr and exits non-zero).
"""

from __future__ import annotations

import re
from typing import Any

_TYPE_PYTHON = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "boolean": bool,
}


def validate(instance: Any, schema: dict, path: str = "$") -> list[str]:
    """Validate `instance` against `schema`. Return a list of error strings."""
    errors: list[str] = []
    if not isinstance(schema, dict):
        return [f"{path}: schema is not an object"]

    expected_type = schema.get("type")
    if expected_type is not None:
        if expected_type not in _TYPE_PYTHON:
            return [f"{path}: unsupported type {expected_type!r}"]
        py_type = _TYPE_PYTHON[expected_type]
        # bool is a subclass of int in Python; reject bool when integer is expected
        # and reject int when boolean is expected.
        if expected_type == "integer" and isinstance(instance, bool):
            errors.append(f"{path}: expected integer, got boolean")
            return errors
        if expected_type == "boolean" and not isinstance(instance, bool):
            errors.append(f"{path}: expected boolean, got {type(instance).__name__}")
            return errors
        if not isinstance(instance, py_type):
            errors.append(
                f"{path}: expected {expected_type}, got {type(instance).__name__}"
            )
            return errors

    if "enum" in schema:
        if instance not in schema["enum"]:
            errors.append(
                f"{path}: value {instance!r} not in enum {schema['enum']!r}"
            )

    if "pattern" in schema and isinstance(instance, str):
        if re.search(schema["pattern"], instance) is None:
            errors.append(
                f"{path}: value {instance!r} does not match pattern {schema['pattern']!r}"
            )

    # `required`, `properties`, `additionalProperties` apply whenever the
    # instance is a dict — per JSON-Schema 2020-12, these keywords are
    # vacuously true for non-object instances. Gating on `expected_type ==
    # "object"` (the previous shape) caused subschemas with no `type`
    # declaration (e.g. RFC-0004's `if`/`then` blocks) to silently skip
    # their constraints — surprising callers and breaking the cross-field
    # `default-scope ∈ allowed-scopes` invariant. Stay safe-by-default:
    # apply when the instance matches.
    if isinstance(instance, dict):
        for required_key in schema.get("required", []):
            if required_key not in instance:
                errors.append(f"{path}: missing required property {required_key!r}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            subpath = f"{path}.{key}"
            if key in properties:
                errors.extend(validate(value, properties[key], subpath))
            else:
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    errors.append(f"{path}: additional property {key!r} not allowed")
                elif isinstance(additional, dict):
                    errors.extend(validate(value, additional, subpath))

    if isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, element in enumerate(instance):
                errors.extend(validate(element, item_schema, f"{path}[{index}]"))
        min_items = schema.get("minItems")
        # bool is a subclass of int in Python — accept only true integers.
        if isinstance(min_items, int) and not isinstance(min_items, bool):
            if len(instance) < min_items:
                errors.append(
                    f"{path}: array has {len(instance)} item(s), minItems={min_items}"
                )
        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict):
            if not any(
                not validate(element, contains_schema, f"{path}[{index}]")
                for index, element in enumerate(instance)
            ):
                errors.append(
                    f"{path}: no item matches the 'contains' subschema"
                )

    # Conditional subschemas — applied last so type/required/enum errors on
    # the instance surface before any conditional branch fires. The 'if'
    # subschema is evaluated silently (its errors are not surfaced); only
    # the chosen branch's errors propagate. Per JSON-Schema 2020-12,
    # missing 'then' or 'else' is a no-op for that branch.
    if "if" in schema and isinstance(schema["if"], dict):
        if_errors = validate(instance, schema["if"], path)
        branch_key = "then" if not if_errors else "else"
        branch_schema = schema.get(branch_key)
        if isinstance(branch_schema, dict):
            errors.extend(validate(instance, branch_schema, path))

    return errors
