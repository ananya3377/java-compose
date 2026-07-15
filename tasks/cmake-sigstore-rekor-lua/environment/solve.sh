#!/bin/bash
set -euo pipefail

# Force APP_ROOT to /app when running inside the Docker container environment
if [ -d "/app" ]; then
    export APP_ROOT="/app"
else
    export APP_ROOT="$(pwd)"
fi

# Navigate to the environment subdirectory containing the source CMake files
cd "$APP_ROOT/environment"
rm -rf build/

export LUA_PATH="$APP_ROOT/environment/lua/?.lua;$APP_ROOT/environment/?.lua;/app/?.lua;;"

echo "Configuring build with CMake from: $(pwd)"
cmake -B build -S .

echo "Executing verify-release target..."
cmake --build build --target verify-release
