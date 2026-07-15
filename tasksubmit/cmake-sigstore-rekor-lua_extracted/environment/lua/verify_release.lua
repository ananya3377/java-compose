local APP_ROOT = os.getenv("APP_ROOT") or "."
package.path = package.path .. ";" .. APP_ROOT .. "/lua/?.lua"

local json = require("json")
local policy = require("policy")
local rekor_client = require("rekor_client")
local digest = require("digest")

local APP_ROOT = os.getenv("APP_ROOT") or "/app"
local preset_path = APP_ROOT .. "/cmake-presets.yaml"
local attest_path = APP_ROOT .. "/release-attestations.toml"

local cfg = policy.load_from_preset(preset_path, attest_path)

for _, artifact in ipairs(cfg.artifacts) do
local raw, err = rekor_client.fetch_entry(cfg.rekor_base_url, artifact.log_index)
  if not raw then
    io.stderr:write(string.format("verify failed for %s: %s\n", artifact.name, err or "unknown"))
    os.exit(1)
  end

  -- Decode Rekor entry JSON
  local envelope = json.decode(raw)

  -- Compute local artifact absolute path
  local artifact_path = APP_ROOT .. "/" .. artifact.path

  -- Compute and compare local artifact digest (static analysis gate)
   local local_digest = digest.sha256_file(artifact_path)
   digest.compare_artifact(artifact_path, local_digest)
   artifact.digest = local_digest

  local function digest_matches(entry, artifact)
  local hashes = entry.integratedTime and entry.integratedTime.hashes or {}
  for _, h in ipairs(hashes) do
    if h.algorithm == "sha256" or h.algorithm == "sha3-256" then
      if h.digest == artifact.digest then
        return true
      end
    end
  end
  return false
end

local required_entries = cfg.required_rekor_entries or 1
local match_count = 0
for _, entry in ipairs(envelope.entries or {}) do
  if digest_matches(entry, artifact) then
    match_count = match_count + 1
  end
end
if match_count < required_entries then
  io.stderr:write(string.format("verify failed for %s: insufficient Rekor entries (found %d, required %d)\n", artifact.name, match_count, required_entries))
  os.exit(1)
end
end

print("verify-release: ok")
os.exit(0)
