#!/usr/bin/env python3
"""Static analysis gate for Lua release verifier modules."""

from __future__ import annotations

import re
import os
import sys
from pathlib import Path


APP_ROOT = os.getenv('APP_ROOT', '.')
# Determine correct Lua directory location
candidate1 = Path(APP_ROOT) / 'environment' / 'lua'
candidate2 = Path(APP_ROOT) / 'lua'
if candidate1.is_dir():
    LUA_DIR = candidate1
elif candidate2.is_dir():
    LUA_DIR = candidate2
else:
    # Fallback to original expectation
    LUA_DIR = candidate1
VERIFY_FILE = LUA_DIR / 'verify_release.lua'

BLOCKED_CONCAT = re.compile(
    r"(os\.execute|io\.popen)\s*\([^)]*\.\.",
    re.MULTILINE | re.DOTALL,
)
HARDCODED_REKOR = re.compile(r"rekor\.sigstore\.dev|https://rekor", re.IGNORECASE)
DIGEST_GATE = re.compile(
    r"digest\.compare_artifact(?:_hash)?\s*\(",
    re.MULTILINE,
)
PRESET_LOADER = re.compile(r"policy\.load_from_preset\s*\(", re.MULTILINE)


def main() -> int:
    errors: list[str] = []

    if not LUA_DIR.is_dir():
        print(f"lua directory missing: {LUA_DIR}", file=sys.stderr)
        return 1

    for path in sorted(LUA_DIR.glob("*.lua")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(LUA_DIR)

        if BLOCKED_CONCAT.search(text):
            errors.append(f"{rel}: shell invocation uses string concatenation")

        if HARDCODED_REKOR.search(text):
            errors.append(f"{rel}: hardcoded Rekor endpoint")

    if VERIFY_FILE.is_file():
        verify_text = VERIFY_FILE.read_text(encoding="utf-8")
        if not DIGEST_GATE.search(verify_text):
            errors.append("verify_release.lua: missing digest.compare_artifact gate")
        if not PRESET_LOADER.search(verify_text):
            errors.append("verify_release.lua: must call policy.load_from_preset")
    else:
        errors.append("verify_release.lua: file missing")

    if errors:
        for err in errors:
            print(f"static-analysis: {err}", file=sys.stderr)
        return 1

    print("static-analysis: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
