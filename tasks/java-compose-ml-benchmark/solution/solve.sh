#!/bin/bash
set -euo pipefail

APP_ROOT="$(pwd)"

# If the reference solution source exists (oracle run), copy it to the app root
if [ -d "/solution/src" ]; then
    cp -rf /solution/src/* "$APP_ROOT/src/"
fi

# Compile all Java sources and execute the computational verification routine
find "$APP_ROOT/environment/src/main/java" -name '*.java' -print0 | sort -z | xargs -0 javac -d "$APP_ROOT/out"
java -Dapp.root="$APP_ROOT" -cp "$APP_ROOT/out" com.example.ReproAnalyzer
