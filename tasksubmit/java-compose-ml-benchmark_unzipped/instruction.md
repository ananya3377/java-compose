We need to verify a melanoma triage model by reconstructing computational validation metrics from the report at `/app/data/benchmark-report.md` and raw experimental telemetry measurements in `/app/data/archive.zip`.

Complete the Java class `com.example.ReproAnalyzer` in package `com.example` to perform the numerical evaluation. A starter scaffold exists at `/app/src/main/java/com/example/ReproAnalyzer.java` which you may extend or replace.

The computational routine must dynamically extract parameter bounds from `/app/data/benchmark-report.md` to resolve the experimental configurations and classification threshold parameters:
- Model variant to evaluate (e.g. `vit-b-16`)
- Warmup policy (e.g. `discard-15`)
- Analysis profile (e.g. `triage`)
- Candidate classification thresholds (e.g. `0.55`, `0.61`, `0.65`, `0.70`)
- Safety recall (sensitivity) target (e.g. at least `68.0%`)

Then, import the numerical observations from `/app/data/archive.zip`. Reconcile the experimental observation vectors in alphabetical order, reconciling overlapping telemetry coordinates by retaining only the first valid observation of each `sample_id`. Omit anomalous or faulty telemetry points.

Sort reconciled telemetry series by `sample_id`. Filter out the transient warmup phase samples as defined by the warmup policy extracted from the report (e.g. `discard-15` discards the first 15% of the observation series). Select the highest candidate threshold meeting the safety recall target extracted from the report, and compute the F1-score and mean latency. Do not hardcode the threshold or the configurations.

Export the reconstructed numerical metrics to `/app/out/reproducibility.json` matching `/app/docs/repro-schema.json`. The output JSON must contain:
- `model_variant`: the dynamically resolved model variant string
- `warmup_policy`: the dynamically resolved warmup policy string
- `analysis_profile`: the dynamically resolved analysis profile string
- `threshold`: the computed threshold number
- `f1`: the computed F1-score (4 decimal places)
- `latency_ms`: the computed mean latency (1 decimal place)
- `source`: the exact string `archived-samples`
