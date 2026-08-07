# Zalando standard — quality-gate checklist

> The machine-checkable MUST / MUST-NOT items the `api-contract` method
> verifies before finalizing output when the active standard is **zalando**.
> Lifted verbatim from the skill's former inline `## Quality Gates` section;
> referenced from `standards-manifest-zalando.yaml` (`quality_gates`).

Before finalizing the output, verify every item. A single failure means the spec is not ready.

### Structural Validity

- [ ] Valid OpenAPI 3.1 YAML (parseable, no `$ref` errors)
- [ ] `info.title`, `info.description`, `info.version`, `info.contact` present [#218]
- [ ] `x-api-id` is a UUID [#215]
- [ ] `x-audience` is set [#219]
- [ ] Semantic version format in `info.version` [#116]

### Security

- [ ] Every operation has a `security` entry [#104]
- [ ] OAuth2 scopes defined and assigned [#105]
- [ ] Scope names follow `<api>.<resource>.<access>` [#225]

### URL Design

- [ ] All paths kebab-case, plural, verb-free [#129][#134][#141]
- [ ] No `/api` prefix [#135]
- [ ] Sub-resource depth at most 3 [#147]
- [ ] Query parameters are snake_case [#130]

### Representations

- [ ] All request/response bodies are JSON-based (`application/json`, `application/merge-patch+json`, or `application/problem+json`) [#167]
- [ ] All top-level responses are objects (no bare arrays) [#110]
- [ ] Properties are snake_case [#118]
- [ ] Boolean properties are non-nullable [#122]
- [ ] Array properties are pluralized [#120] and non-null when empty [#124]
- [ ] Number properties have explicit `format` [#171]
- [ ] Date-time uses ISO 8601 `format: date-time` [#169]
- [ ] Enums are UPPER_SNAKE_CASE [#240]
- [ ] Money uses common object [#173]

### Responses & Errors

- [ ] Every operation specifies success + error responses [#151]
- [ ] Error responses use `application/problem+json` [#176]
- [ ] No stack traces in error examples [#177]
- [ ] Only official HTTP status codes used [#243]

### Pagination

- [ ] All list endpoints paginated [#159]
- [ ] Pagination links provided [#161]
- [ ] Page object uses common schema [#248]

### Compatibility

- [ ] No breaking changes to existing published fields [#106]
- [ ] Extensible enums use `examples` keyword (not closed `enum`) [#112]
- [ ] No URL versioning [#115]
