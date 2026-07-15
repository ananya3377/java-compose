We need the CMake release attestation verifier under `/app` repaired so signed research artifacts are accepted only when their digests appear in the Sigstore Rekor transparency log at the endpoint configured in `/app/cmake-presets.yaml`.

The current Lua modules and CMake targets fail CI: the static-analysis gate rejects unsafe shell patterns, and `cmake --build --target verify-release` accepts artifacts without validating Rekor log entries against `/app/release-attestations.toml`.

Repair the Lua verifier modules and CMake integration so `cmake --build --target verify-release` enforces policy from `/app/cmake-presets.yaml`, queries Rekor using the preset base URL, and compares artifact SHA-256 digests to logged entries per `/app/docs/rekor-api-contract.md`. The implementation must satisfy `/app/docs/static-analysis-rules.md`.

Run verification from a build directory under `/app/build`. Do not disable the `static-analysis` target.
