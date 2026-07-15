local json = require("json")
local policy = require("policy")
local digest = require("digest")
local rekor_client = require("rekor_client")

local APP_ROOT = os.getenv("APP_ROOT") or "/app"
local preset_path = APP_ROOT .. "/cmake-presets.yaml"
local attest_path = APP_ROOT .. "/release-attestations.toml"

local function decode_body(body_b64)
  local handle = io.popen(string.format("printf '%%s' %q | base64 -d", body_b64))
  local decoded = handle:read("*a")
  handle:close()
  return json.decode(decoded)
end

local function annotations_ok(entry_body, required)
  local metadata = entry_body.metadata or {}
  local annotations = metadata.annotations or {}
  for _, key in ipairs(required) do
    if annotations[key] ~= "true" and annotations[key] ~= true then
      return false
    end
  end
  return true
end

local function verify_artifact(cfg, artifact)
  local artifact_path = APP_ROOT .. "/" .. artifact.path
  local raw, err = rekor_client.fetch_entry(cfg.rekor_base_url, artifact.log_index)
  if not raw then
    return false, err or "rekor fetch failed"
  end

  local envelope = json.decode(raw)
  local entry = nil
  for _, value in pairs(envelope) do
    entry = value
    break
  end
  if not entry or not entry.body then
    return false, "malformed rekor entry"
  end

  if entry.logIndex < cfg.min_log_index then
    return false, "log index below policy minimum"
  end

  if not policy.identity_allowed(cfg, artifact.identity) then
    return false, "identity not allowed"
  end

  local body = decode_body(entry.body)
  if not annotations_ok(body, cfg.required_annotations) then
    return false, "missing required annotations"
  end

  local hash_value = body.spec.data.hash.value
  local algorithm = body.spec.data.hash.algorithm
  if algorithm ~= "sha256" then
    return false, "unexpected hash algorithm"
  end

  if not digest.compare_artifact(artifact_path, hash_value) then
    return false, "artifact digest mismatch"
  end

  return true, nil
end

local cfg = policy.load_from_preset(preset_path, attest_path)
for _, artifact in ipairs(cfg.artifacts) do
  local ok, err = verify_artifact(cfg, artifact)
  if not ok then
    io.stderr:write(string.format("verify failed for %s: %s\n", artifact.name, err or "unknown"))
    os.exit(1)
  end
end

print("verify-release: ok")
os.exit(0)
