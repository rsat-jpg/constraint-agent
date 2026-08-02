# Changelog

## 0.1.0 — 2026-08-02

- Structural Validate core: typed `Plan` / findings, deterministic `validate_plan`
- Thin optional LLM→Plan adapter (Expansion Gate Decision D1)
- Thin optional runtime trace verification (Expansion Gate Decision D2): `verify_trace` / `linear_trace`, `RUNTIME_*` codes
- Evidence corpus of LLM-shaped fixtures with expected codes and overlaps
- **Structural Validate surface freeze:** 13 finding codes locked for package `0.1.x` (see README); runtime codes are a separate namespace
