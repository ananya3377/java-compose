#!/bin/bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
mkdir -p "$APP_ROOT/lua"

if [ -d "/solution/lua" ]; then
  cp -f /solution/lua/*.lua "$APP_ROOT/lua/"
fi

chmod +x "$APP_ROOT/tools/fetch_rekor_entry.sh"

cmake -S "$APP_ROOT" -B "$APP_ROOT/build"
cmake --build "$APP_ROOT/build" --target verify-release
