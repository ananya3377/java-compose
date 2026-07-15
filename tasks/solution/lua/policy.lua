local preset_loader = require("preset_loader")

local M = {}

function M.load_from_preset(preset_path, attest_path)
  local preset = preset_loader.load(preset_path)
  local artifacts = {}

  local current = nil
  for line in io.lines(attest_path) do
    local stripped = line:match("^%s*(.-)%s*$")
    if stripped == "[[artifacts]]" then
      current = {}
      table.insert(artifacts, current)
    elseif current and stripped:match('^name%s*=') then
      current.name = stripped:match('=%s*"(.-)"')
    elseif current and stripped:match('^path%s*=') then
      current.path = stripped:match('=%s*"(.-)"')
    elseif current and stripped:match('^log_index%s*=') then
      current.log_index = tonumber(stripped:match("=(%d+)"))
    elseif current and stripped:match('^identity%s*=') then
      current.identity = stripped:match('=%s*"(.-)"')
    end
  end

  return {
    rekor_base_url = preset.rekor.base_url,
    allowed_identities = preset.policy.allowed_identities,
    required_annotations = preset.policy.required_annotations,
    min_log_index = preset.policy.min_log_index,
    artifacts = artifacts,
  }
end

function M.identity_allowed(policy, identity)
  for _, allowed in ipairs(policy.allowed_identities) do
    if allowed == identity then
      return true
    end
  end
  return false
end

return M
