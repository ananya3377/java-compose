# Static analysis rules for release verification Lua modules

The checker at `/app/tools/static_analysis_check.py` scans `/app/lua/*.lua` before `verify-release` runs.

## Blocked patterns

1. **Shell injection via string concatenation.** Any `os.execute(` or `io.popen(` call whose argument expression contains the Lua concatenation operator `..` is rejected.
2. **Hardcoded Rekor endpoints.** Literal substrings `rekor.sigstore.dev` or `https://rekor` inside Lua sources are rejected. The Rekor base URL must come from the preset loader.
3. **Missing digest gate.** `verify_release.lua` must call `digest.compare_artifact` (or `digest.compare_artifact_hash`) before accepting an entry.

## Required patterns

- `verify_release.lua` imports and uses `policy.load_from_preset` so preset fields govern verification.
- `rekor_client.lua` fetches entries through `/app/tools/fetch_rekor_entry.sh` (fixed argv; no inline shell assembly in Lua).
