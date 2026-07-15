#!/bin/bash
set -euo pipefail
base_url="${REKOR_BASE_URL:?REKOR_BASE_URL not set}"
log_index="${REKOR_LOG_INDEX:?REKOR_LOG_INDEX not set}"
curl -sS -f "${base_url}/api/v1/log/entries?logIndex=${log_index}"
