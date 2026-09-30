#!/usr/bin/env python3
"""Pure-stdlib validation for spec-retirement candidate documents.

The schema document is the source of truth.  This module implements the JSON
Schema keywords used by ``spec-retirement-candidates.schema.json`` and resolves
local ``$ref`` pointers against the supplied schema.  It deliberately carries
no copied blocker or refusal vocabulary.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence


def _join(path: str, part: str | int) -> str:
    """Append one JSON-path component to a diagnostic path."""
    return f"{path}/{part}" if path else str(part)


def _json_equal(left: object, right: object) -> bool:
    """Compare JSON values without Python's ``True == 1`` coercion."""
    return type(left) is type(right) and left == right


def _matches_type(instance: object, expected: str) -> bool:
    """Return whether *instance* has the requested JSON Schema primitive type."""
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    return False


def _resolve_local_ref(root_schema: Mapping[str, object], ref: str) -> object:
    """Resolve one RFC 6901 local JSON pointer from the root schema."""
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported non-local schema reference: {ref}")
    node: object = root_schema
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, Mapping) or part not in node:
            raise ValueError(f"unresolvable local schema reference: {ref}")
        node = node[part]
    return node


def _validate(
    instance: object,
    schema: object,
    root_schema: Mapping[str, object],
    path: str,
) -> list[str]:
    """Validate one instance node against one schema node."""
    if schema is True:
        return []
    if schema is False:
        return [f"{path or '$'}: rejected by false schema"]
    if not isinstance(schema, Mapping):
        return [f"{path or '$'}: schema node is not an object or boolean"]

    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str):
            return [f"{path or '$'}: schema $ref is not a string"]
        try:
            target = _resolve_local_ref(root_schema, ref)
        except ValueError as exc:
            return [f"{path or '$'}: {exc}"]
        return _validate(instance, target, root_schema, path)

    errors: list[str] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _matches_type(instance, expected_type):
        return [f"{path or '$'}: expected {expected_type}"]

    if "const" in schema and not _json_equal(instance, schema["const"]):
        errors.append(f"{path or '$'}: value does not match const")

    enum = schema.get("enum")
    if isinstance(enum, list) and not any(_json_equal(instance, item) for item in enum):
        errors.append(f"{path or '$'}: value is not in schema enum")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for name in required:
                if isinstance(name, str) and name not in instance:
                    errors.append(f"{_join(path, name)}: required property is missing")

        properties = schema.get("properties", {})
        if isinstance(properties, Mapping):
            for name, child_schema in properties.items():
                if name in instance:
                    errors.extend(
                        _validate(
                            instance[name], child_schema, root_schema, _join(path, name)
                        )
                    )
            if schema.get("additionalProperties") is False:
                for name in instance.keys() - properties.keys():
                    errors.append(f"{_join(path, name)}: additional property is forbidden")

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{path or '$'}: fewer than {min_items} items")
        if isinstance(max_items, int) and len(instance) > max_items:
            errors.append(f"{path or '$'}: more than {max_items} items")
        if "items" in schema:
            for index, item in enumerate(instance):
                errors.extend(
                    _validate(item, schema["items"], root_schema, _join(path, index))
                )
        if "contains" in schema and not any(
            not _validate(item, schema["contains"], root_schema, _join(path, index))
            for index, item in enumerate(instance)
        ):
            errors.append(f"{path or '$'}: no array item matches contains")

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        if isinstance(min_length, int) and len(instance) < min_length:
            errors.append(f"{path or '$'}: shorter than {min_length} characters")
        if isinstance(max_length, int) and len(instance) > max_length:
            errors.append(f"{path or '$'}: longer than {max_length} characters")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, instance) is None:
            errors.append(f"{path or '$'}: value does not match schema pattern")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and instance < minimum:
            errors.append(f"{path or '$'}: value is below minimum {minimum}")
        if isinstance(maximum, (int, float)) and instance > maximum:
            errors.append(f"{path or '$'}: value is above maximum {maximum}")

    all_of = schema.get("allOf")
    if isinstance(all_of, Sequence) and not isinstance(all_of, (str, bytes)):
        for child_schema in all_of:
            errors.extend(_validate(instance, child_schema, root_schema, path))

    if_schema = schema.get("if")
    if if_schema is not None and not _validate(instance, if_schema, root_schema, path):
        then_schema = schema.get("then")
        if then_schema is not None:
            errors.extend(_validate(instance, then_schema, root_schema, path))

    not_schema = schema.get("not")
    if not_schema is not None and not _validate(instance, not_schema, root_schema, path):
        errors.append(f"{path or '$'}: instance matches forbidden schema")

    return errors


def validate_document(document: object, schema: Mapping[str, object]) -> list[str]:
    """Return all contract violations for *document* against *schema*.

    The caller supplies the parsed live schema.  No enum, required-field list,
    or conditional rule is copied into this module, so changing the schema
    changes validation on the next call.

    Args:
        document: Parsed JSON-compatible output document.
        schema: Parsed JSON Schema document.

    Returns:
        Deterministically ordered diagnostic strings.  An empty list means the
        document conforms to the supplied schema.
    """
    # Reject non-JSON-compatible inputs before schema evaluation.  Round-trip
    # serialization is stdlib-only and catches sets, paths, NaN, and cycles.
    try:
        json.dumps(document, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        return [f"$: document is not JSON-compatible: {type(exc).__name__}"]
    return _validate(document, schema, schema, "")
