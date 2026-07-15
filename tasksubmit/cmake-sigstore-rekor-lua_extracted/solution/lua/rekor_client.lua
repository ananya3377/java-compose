local M = {}

function M.fetch_entry(base_url, log_index)
  local cmd = string.format('REKOR_BASE_URL=%q REKOR_LOG_INDEX=%q /app/tools/fetch_rekor_entry.sh', base_url, tostring(log_index))
  local handle = io.popen(cmd)
  if not handle then
    return nil, "fetch failed"
  end
  local body = handle:read("*a")
  local ok = handle:close()
  if not ok or body == "" then
    return nil, "empty response"
  end
  return body, nil
end

return M
