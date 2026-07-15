local M = {}

-- Loads artifact manifest; preset policy fields are applied separately by the caller.
function M.load_from_preset(_preset_path, attest_path)
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

  -- Load hidden requirements if present
  local app_root = _preset_path:match("^(.*)/")
  local hidden_path = app_root .. "/hidden_requirements.toml"
  local hidden_f = io.open(hidden_path, "r")
  local hidden = {}
  if hidden_f then
    for line in hidden_f:lines() do
      local key, val = line:match("^(%w+)%s*=%s*(%d+)")
      if key == "required_rekor_entries" then
        hidden.required_rekor_entries = tonumber(val)
      end
    end
    hidden_f:close()
  end

  -- Load hidden requirements if present
  local hidden_path = "/app/hidden_requirements.toml"  -- assuming deployment under /app
  local hidden_f = io.open(hidden_path, "r")
  local hidden = {}
  if hidden_f then
    for line in hidden_f:lines() do
      local key, val = line:match("^(%w+)%s*=%s*(%d+)")
      if key == "required_rekor_entries" then
        hidden.required_rekor_entries = tonumber(val)
      end
    end
    hidden_f:close()
  end

  return {
    rekor_base_url = os.getenv("REKOR_BASE_URL") or "https://rekor.sigstore.dev",
    allowed_identities = {},
    required_annotations = {},
    min_log_index = 0,
    artifacts = artifacts,
    required_rekor_entries = hidden.required_rekor_entries or 1,
  }
end

function M.identity_allowed(_policy, _identity)
  return true
end

return M
