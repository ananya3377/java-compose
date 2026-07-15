We need to verify a melanoma triage model by reconstructing computational validation metrics from the report at `/app/data/benchmark-report.md` and raw experimental telemetry measurements in `/app/data/archive.zip`.

Complete the Java class `com.example.ReproAnalyzer` in package `com.example` to perform the numerical evaluation. A starter scaffold exists at `/app/src/main/java/com/example/ReproAnalyzer.java` which you may extend or replace.

**Entry point**: `com.example.ReproAnalyzer` provides a `public static void main(String[] args)` method. Compile with `javac -d /app/out /app/src/main/java/com/example/ReproAnalyzer.java` and run with `java -cp /app/out com.example.ReproAnalyzer`.

**Project layout**
- `/app/src/main/java/com/example/ReproAnalyzer.java` – starter source file (entry point).
- `/app/data/` – benchmark report and archive.
- `/app/docs/` – JSON schema (`repro-schema.json`).
- `/app/out/` – directory where the compiled classes and `reproducibility.json` will be placed.

**Project layout**
- `/app/src/main/java/com/example/ReproAnalyzer.java` – entry point CLI (you may also create `ReproCli.java`).
- `/app/data/` – benchmark report and archive.
- `/app/docs/` – JSON schema (`repro-schema.json`).
- `/app/out/` – output directory for `reproducibility.json`.

The computational routine must dynamically extract parameter bounds from `/app/data/benchmark-report.md` to resolve the experimental configurations and classification threshold parameters:
- Model variant to evaluate (e.g. `vit-b-16`)
- Warmup policy (e.g. `discard-15`)
- Analysis profile (e.g. `triage`)
- Candidate classification thresholds (e.g. `0.55`, `0.61`, `0.65`, `0.70`)
- Safety recall (sensitivity) target (e.g. at least `68.0%`)

Then, import the numerical observations from `/app/data/archive.zip`. Reconcile the experimental observation vectors in alphabetical order, reconciling overlapping telemetry coordinates by retaining only the first valid observation of each `sample_id`. Omit anomalous or faulty telemetry points.

Sort reconciled telemetry series by `sample_id`. Filter out the transient warmup phase samples as defined by the warmup policy extracted from the report (e.g. `discard-15` discards the first 15% of the observation series). Select the highest candidate threshold meeting the safety recall target extracted from the report, and compute the F1-score and mean latency. Do not hardcode the threshold or the configurations.

Export the reconstructed numerical metrics to `/app/out/reproducibility.json` matching `/app/docs/repro-schema.json`. The output JSON must contain the following fields with exact names:
- `model_variant` (string): dynamically resolved model variant.
- `warmup_policy` (string): dynamically resolved warmup policy.
- `analysis_profile` (string): must be the constant "triage".
- `threshold` (number): the selected classification threshold.
- `f1` (number): computed F1-score (4 decimal places).
- `latency_ms` (number): computed mean latency (1 decimal place).
- `source` (string): must be the constant "archived-samples".

```json
{
  "source": {
    "type": "string",
    "const": "archived-samples",
    "description": "Fixed identifier for the archived sample set"
  }
}
```
