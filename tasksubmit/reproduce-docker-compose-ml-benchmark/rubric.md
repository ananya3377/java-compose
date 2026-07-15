# Rubric for Reproduce Docker‑Compose ML Benchmark

## Evaluation Criteria

- **Output file**: `out/reproducibility.json` must exist.
- **Required fields**: `model_variant`, `warmup_policy`, `analysis_profile`,
  `threshold`, `f1`, `latency_ms`, `source`.
- **F1‑value correctness**: `payload['f1']` must equal the dynamically
  computed `expected_f1` (asserted by `test_f1_value`).
- **F1 formatting**: `f1` must have exactly four decimal places
  (checked by `test_f1_formatting`).
- **Threshold whitelist**: Only thresholds `{0.55, 0.61, 0.65, 0.70}` are
  considered valid; the solver must respect this constraint.
- **Java scaffold**: The environment scaffold is a stub; the solver must
  implement the logic themselves.

## Scoring

| Criterion | Pass | Fail |
|-----------|------|------|
| Output file exists | ✅ | ❌ |
| All required fields present | ✅ | ❌ |
| F1 value matches expected | ✅ | ❌ |
| F1 formatting (4 decimals) | ✅ | ❌ |
| Threshold whitelist respected | ✅ | ❌ |
| No solution leakage (stub only) | ✅ | ❌ |

All criteria must pass for the task to be accepted.
