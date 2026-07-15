local M = {}

local function trim(value)
  return (value:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function strip_quotes(value)
  value = trim(value)
  if value:sub(1, 1) == '"' and value:sub(-1) == '"' then
    return value:sub(2, -2)
  end
  if value:sub(1, 1) == "'" and value:sub(-1) == "'" then
    return value:sub(2, -2)
  end
  return value
end

function M.load(path)
  local preset = {
    rekor = { base_url = nil },
    policy = {
      allowed_identities = {},
      required_annotations = {},
      min_log_index = 0,
    },
  }

  local section = nil
  local list_key = nil

  for line in io.lines(path) do
    local stripped = trim(line)
    if stripped == "" or stripped:sub(1, 1) == "#" then
      goto continue
    end

    if stripped:match("^%- ") then
      local item = strip_quotes(stripped:sub(3))
      if list_key == "allowed_identities" then
        table.insert(preset.policy.allowed_identities, item)
      elseif list_key == "required_annotations" then
        table.insert(preset.policy.required_annotations, item)
      end
      goto continue
    end

    list_key = nil
    local key, value = stripped:match("^([%w_%.]+)%s*:%s*(.+)$")
    if key and value then
      value = strip_quotes(value)
      if key == "verify.rekor.base_url" or key == "rekor.base_url" then
        preset.rekor.base_url = value
      elseif key == "verify.policy.min_log_index" or key == "policy.min_log_index" then
        preset.policy.min_log_index = tonumber(value) or 0
      elseif key == "verify.rekor.base_url" then
        preset.rekor.base_url = value
      end
      if stripped:match("allowed_identities:") then
        list_key = "allowed_identities"
      elseif stripped:match("required_annotations:") then
        list_key = "required_annotations"
      end
    end

    if stripped:match("base_url:") then
      local url = stripped:match('base_url:%s*"(.-)"')
      if url then
        preset.rekor.base_url = url
      end
    end
    if stripped:match("min_log_index:") then
      local num = stripped:match("min_log_index:%s*(%d+)")
      if num then
        preset.policy.min_log_index = tonumber(num)
      end
    end
    if stripped:match("allowed_identities:") then
      list_key = "allowed_identities"
    elseif stripped:match("required_annotations:") then
      list_key = "required_annotations"
    end

    ::continue::
  end

  if not preset.rekor.base_url then
    error("preset missing rekor.base_url")
  end

  return preset
end

return M
