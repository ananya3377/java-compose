local M = {}

local function read_file(path)
  local handle = io.open(path, "rb")
  if not handle then
    return nil
  end
  local data = handle:read("*a")
  handle:close()
  return data
end

function M.sha256_file(path)
  local tmp_in = os.tmpname()
  local tmp_out = os.tmpname()
  local data = read_file(path)
  if not data then
    error("cannot read artifact: " .. path)
  end

  local in_handle = io.open(tmp_in, "wb")
  in_handle:write(data)
  in_handle:close()

  local ok = os.execute(string.format("sha256sum %q | awk '{print $1}' > %q", tmp_in, tmp_out))
  os.remove(tmp_in)
  if not ok then
    os.remove(tmp_out)
    error("sha256sum failed for " .. path)
  end

  local out_handle = io.open(tmp_out, "r")
  local digest = out_handle:read("*l")
  out_handle:close()
  os.remove(tmp_out)
  return digest
end

function M.compare_artifact(path, expected_hex)
  local actual = M.sha256_file(path)
  return actual == expected_hex:lower()
end

function M.compare_artifact_hash(path, expected_hex)
  return M.compare_artifact(path, expected_hex)
end

return M
