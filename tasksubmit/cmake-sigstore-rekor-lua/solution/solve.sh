#!/bin/bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
mkdir -p "$APP_ROOT/lua"



chmod +x "$APP_ROOT/tools/fetch_rekor_entry.sh"

cmake -S "$APP_ROOT" -B "$APP_ROOT/build"
cmake --build "$APP_ROOT/build" --target verify-release
