local M = {}

function M.fetch_entry(base_url, log_index)
  os.setenv("REKOR_BASE_URL", base_url)
  os.setenv("REKOR_LOG_INDEX", tostring(log_index))
  local handle = io.popen("/app/tools/fetch_rekor_entry.sh")
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
