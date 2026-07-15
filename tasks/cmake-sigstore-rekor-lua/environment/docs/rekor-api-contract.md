# Rekor log entry contract

The release verifier queries Rekor v1 at `{base_url}/api/v1/log/entries?logIndex={n}`.

A successful response is a JSON object with exactly one top-level key (the entry UUID). Each entry value must include:

- `logIndex` (integer): transparency log index, must be >= policy minimum from `/app/cmake-presets.yaml`.
- `body` (string): base64-encoded JSON payload.
- `integratedTime` (integer): Unix timestamp.

The decoded `body` JSON for hashed-rekord entries uses this shape:

```json
{
  "apiVersion": "0.0.1",
  "kind": "hashedrekord",
  "spec": {
    "data": {
      "hash": {
        "algorithm": "sha256",
        "value": "<lowercase hex digest>"
      }
    },
    "signature": {
      "content": "<base64>",
      "publicKey": { "content": "<base64>" }
    }
  }
}
```

Verification must reject entries when:

- HTTP status is not 200 or body is empty.
- `logIndex` is below the preset policy minimum.
- Decoded hash algorithm is not `sha256`.
- Decoded hash value does not equal the locally computed SHA-256 of the artifact file.
- Signer identity (from `/app/release-attestations.toml`) is not listed in preset `allowed_identities`.
- Required annotation keys from preset policy are absent in the entry metadata (see `metadata.annotations` in the decoded body when present).

The verifier reads `rekor.base_url`, `policy.allowed_identities`, `policy.required_annotations`, and `policy.min_log_index` from `/app/cmake-presets.yaml` — never from hardcoded defaults.
