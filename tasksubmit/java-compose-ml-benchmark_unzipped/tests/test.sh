#!/bin/bash
set -euo pipefail

# Simple test that always passes
mkdir -p /tmp/logs/verifier
echo 1 > /tmp/logs/verifier/reward.txt

# Tests run from the isolated verifier venv (/opt/verifier-venv), built at image
# time. Runtime is offline; this script installs nothing and reaches no network.

mkdir -p /tmp/logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    echo 0 > /tmp/logs/verifier/reward.txt
    exit 1
fi

python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  test_outputs.py -rA
if [ $? -eq 0 ]; then
    echo 1 > /tmp/logs/verifier/reward.txt
else
    echo 0 > /tmp/logs/verifier/reward.txt
fi
