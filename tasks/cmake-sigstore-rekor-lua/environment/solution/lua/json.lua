local M = {}

local function skip_ws(text, index)
  while index <= #text do
    local ch = text:sub(index, index)
    if ch == " " or ch == "\n" or ch == "\r" or ch == "\t" then
      index = index + 1
    else
      break
    end
  end
  return index
end

local function parse_string(text, index)
  index = index + 1
  local parts = {}
  while index <= #text do
    local ch = text:sub(index, index)
    if ch == '"' then
      return table.concat(parts), index + 1
    end
    if ch == "\\" then
      local next_ch = text:sub(index + 1, index + 1)
      table.insert(parts, next_ch)
      index = index + 2
    else
      table.insert(parts, ch)
      index = index + 1
    end
  end
  error("unterminated string")
end

local function parse_number(text, index)
  local start = index
  while index <= #text do
    local ch = text:sub(index, index)
    if ch:match("[%d%-%.eE]") then
      index = index + 1
    else
      break
    end
  end
  return tonumber(text:sub(start, index - 1)), index
end

local function parse_value(text, index)
  index = skip_ws(text, index)
  local ch = text:sub(index, index)
  if ch == '"' then
    return parse_string(text, index)
  end
  if ch == "{" then
    return M.decode_object(text, index)
  end
  if ch == "[" then
    return M.decode_array(text, index)
  end
  if ch:match("[%d%-]") then
    return parse_number(text, index)
  end
  if text:sub(index, index + 3) == "true" then
    return true, index + 4
  end
  if text:sub(index, index + 4) == "false" then
    return false, index + 5
  end
  if text:sub(index, index + 3) == "null" then
    return nil, index + 4
  end
  error("invalid json at " .. index)
end

function M.decode_array(text, index)
  index = index + 1
  local arr = {}
  index = skip_ws(text, index)
  if text:sub(index, index) == "]" then
    return arr, index + 1
  end
  while index <= #text do
    local value
    value, index = parse_value(text, index)
    table.insert(arr, value)
    index = skip_ws(text, index)
    local ch = text:sub(index, index)
    if ch == "]" then
      return arr, index + 1
    end
    if ch == "," then
      index = skip_ws(text, index + 1)
    else
      error("expected , or ] in array")
    end
  end
  error("unterminated array")
end

function M.decode_object(text, index)
  index = index + 1
  local obj = {}
  index = skip_ws(text, index)
  if text:sub(index, index) == "}" then
    return obj, index + 1
  end
  while index <= #text do
    index = skip_ws(text, index)
    local key
    key, index = parse_string(text, index)
    index = skip_ws(text, index)
    if text:sub(index, index) ~= ":" then
      error("expected : in object")
    end
    index = skip_ws(text, index + 1)
    local value
    value, index = parse_value(text, index)
    obj[key] = value
    index = skip_ws(text, index)
    local ch = text:sub(index, index)
    if ch == "}" then
      return obj, index + 1
    end
    if ch == "," then
      index = skip_ws(text, index + 1)
    else
      error("expected , or } in object")
    end
  end
  error("unterminated object")
end

function M.decode(text)
  local value, index = parse_value(text, 1)
  return value
end

return M
