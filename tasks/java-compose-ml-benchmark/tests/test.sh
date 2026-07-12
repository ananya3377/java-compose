#!/bin/bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
mkdir -p /logs/verifier

if [ ! -f "$APP_ROOT/out/reproducibility.json" ]; then
  echo "Missing $APP_ROOT/out/reproducibility.json" >&2
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

python - <<'PY'
import json, os, sys
from pathlib import Path

expected = {
    "model_variant": "vit-b-16",
    "threshold": 0.61,
    "warmup_policy": "none",
    "analysis_profile": "triage",
    "f1": 0.8214,
    "latency_ms": 184.0,
    "source": "archived-predictions"
}

app_root = Path(os.environ.get('APP_ROOT', '/app'))
with (app_root / 'out' / 'reproducibility.json').open() as fh:
    actual = json.load(fh)

if actual != expected:
    print(json.dumps(actual, indent=2))
    sys.exit(1)
PY
status=$?
if [ "$status" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
