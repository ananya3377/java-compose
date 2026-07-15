We need the CMake release attestation verifier under `/app` repaired so signed research artifacts are accepted only when their digests appear in the Sigstore Rekor transparency log at the endpoint configured in `/app/cmake-presets.yaml`.

The current Lua modules and CMake targets fail CI: the static-analysis gate rejects unsafe shell patterns, and `cmake --build --target verify-release` accepts artifacts without validating Rekor log entries against `/app/release-attestations.toml`.

Repair the Lua verifier modules and CMake integration so `cmake --build --target verify-release` enforces policy from `/app/cmake-presets.yaml`, queries Rekor using the preset base URL, and compares artifact SHA-256 digests to logged entries per `/app/docs/rekor-api-contract.md`. The implementation must satisfy `/app/docs/static-analysis-rules.md`.

Run verification from a build directory under `/app/build`. Do not disable the `static-analysis` target.

**Expected Behavior Details**

- The `verify-release` target must output the exact string `verify-release: ok` on stdout when verification succeeds (checked by `test_verify_release_passes`).
- On verification failure, the tool must write clear error messages to stderr/stdout:
  * `digest mismatch` – when the artifact digest does not match any entry in the Rekor log.
  * `identity not allowed` – when the signing identity is not permitted by the policy.
- The Lua client (`rekor_client.lua`) must invoke the helper script `fetch_rekor_entry.sh`. The script returns a JSON response whose body is Base64‑encoded; the client must decode this payload before parsing the Rekor entry.
- All static‑analysis rules in `/app/docs/static-analysis-rules.md` must be satisfied, including the use of `fetch_rekor_entry.sh` for Rekor queries.
