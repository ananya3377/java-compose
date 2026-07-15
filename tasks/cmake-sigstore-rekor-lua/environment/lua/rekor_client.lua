local M = {}

local http = require("socket.http")
local ltn12 = require("ltn12")

function M.fetch_entry(base_url, log_index)
  local url = base_url .. "/api/v1/log/entries?logIndex=" .. tostring(log_index)
  local response_body = {}
  local res, code, headers, status = http.request{
    url = url,
    sink = ltn12.sink.table(response_body),
    method = "GET",
    timeout = 10
  }
  if not res or code ~= 200 then
    return nil, string.format("fetch failed (code %s)", code or "nil")
  end
  local body = table.concat(response_body)
  if body == "" then
    return nil, "empty response"
  end
  return body, nil
end

return M
