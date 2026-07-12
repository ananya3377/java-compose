#!/bin/bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
mkdir -p "$APP_ROOT/out"
javac -d "$APP_ROOT/out" $(find "$APP_ROOT/src/main/java" -name '*.java' | sort)
java -Dapp.root="$APP_ROOT" -cp "$APP_ROOT/out" com.example.ReproCli
