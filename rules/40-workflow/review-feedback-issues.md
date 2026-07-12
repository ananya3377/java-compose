# 40-workflow — Review feedback issues (`issues.txt`)

**Scope:** Every task before `tasksubmit/<task-name>.zip` is built. Source: [`issues.txt`](../../issues.txt) (May 27, 2026 trial feedback).

**Hard rule:** Do **not** zip until every applicable item below is fixed or explicitly N/A with evidence. This gate runs **after** the four quality gates (ruff, abs-path, oracle, nop) and **before** section 11 of [pre-submit-checklist.md](pre-submit-checklist.md).

## Environment Problems (Dockerfile / container defects — Jun 3, 2026)

These are the patterns the reviewer "Environment Problems" category flags. Each is a blocker when present.

| Pattern | Rule |
|---|---|
| Missing `tmux` or `asciinema` in image | [dockerfile.md §1](../20-environment/dockerfile.md) |
| Runtime network installs in `test.sh` (`pip install`, `apt-get`, `curl`) | [runtime-verifier.md](../20-environment/runtime-verifier.md) |
| AI-scaffolding filenames (`CLAUDE.md`, `skills.md`) in `environment/` | [dockerfile.md §Image hygiene](../20-environment/dockerfile.md) |
| `solution/` or `tests/` baked into the image via `COPY` | [dockerfile.md §5](../20-environment/dockerfile.md) |
| Privileged mode required | [dockerfile.md §14](../20-environment/dockerfile.md) |
| Reserved-directory conflicts (`/logs/verifier/`, `/tests/`, `/solution/` written in Dockerfile) | [dockerfile.md §15](../20-environment/dockerfile.md) |
| Oversized build context (`environment/` > 100 MiB total or any file > 50 MiB) | [dockerfile.md §12](../20-environment/dockerfile.md) |
| Unsanctioned final runtime base image | [dockerfile.md §13](../20-environment/dockerfile.md) |

```bash
# Quick environment-problems scan
grep -nE '^[[:space:]]*FROM ' tasks/<task-name>/environment/Dockerfile | grep -v '@sha256:'  # unpinned base
grep -rn 'CLAUDE.md\|skills.md\|AGENTS.md' tasks/<task-name>/environment/ 2>/dev/null        # AI filenames
grep -nE '^COPY (solution|tests)' tasks/<task-name>/environment/Dockerfile                   # baked solution/tests
du -sh tasks/<task-name>/environment/                                                         # context size
```

## Critical (blockers)

### 1. Rubrics on the platform — not in the repo

- [ ] Rubric criteria authored in the **Snorkel submission UI** (not empty at submit time).
- [ ] **No** `rubric.md` / `rubric.txt` anywhere under `tasks/<task-name>/`.

```bash
find tasks/<task-name>/ \( -name 'rubric.md' -o -name 'rubric.txt' \) -print
# must print nothing
```

When building or rebuilding a zip, **emit the rubric in chat** that same turn (see [rubric.md](rubric.md)).

### 2. No canary strings

```bash
grep -RIn 'CANARY-' tasks/<task-name>/ || echo "OK"
grep -RIn 'BENCHMARK DATA SHOULD NEVER APPEAR' tasks/<task-name>/ || echo "OK"
grep -RIn 'canary GUID' tasks/<task-name>/ || echo "OK"
```

- [ ] No `CANARY-*`, benchmark-canary line, or `# canary GUID:` anywhere.

### 3. Test deps in Dockerfile — not in `tests/`

```bash
find tasks/<task-name> \( -name '*.whl' -o -name wheels -type d \) -print
grep -RnE 'pip install|python -m venv|python3 -m venv' \
  tasks/<task-name>/tests/ tasks/<task-name>/steps/*/tests/ 2>/dev/null || echo "OK"
grep -nE 'verifier-venv|verifier-requirements' tasks/<task-name>/environment/Dockerfile
```

- [ ] No `.whl` files or `wheels/` under any `tests/`.
- [ ] No `pip install` or venv creation in any `test.sh`.
- [ ] `environment/Dockerfile` builds `/opt/verifier-venv` from pinned lockfile (see [../20-environment/verifier-deps.md](../20-environment/verifier-deps.md)).

### 4. No hints or answer leakage in `environment/`

```bash
grep -RInE '\b(BUG|FIXME|HACK|XXX)\b' tasks/<task-name>/environment/ || echo "OK"
grep -RInE 'Bug:|broken baseline|TODO.*(solution|fix|bug)|fix (this|me|the bug)' \
  tasks/<task-name>/environment/ || echo "OK"
grep -RInE 'VERIFY_CONFIG|expected_|answer\.|solution/' tasks/<task-name>/environment/ || echo "OK"
find tasks/<task-name>/environment -name '*expected*' -o -name '*answer*' 2>/dev/null
```

- [ ] No comment or doc **names a bug, labels a fix location, or describes the intended solution path**.
- [ ] Docs under `environment/` describe **API/contracts only**, not step-by-step fix guidance.
- [ ] No ground-truth, expected-output, or test-fixture names in agent-visible source.

Read comment lines and every `environment/**/*.md` by eye — keyword greps miss prose hints.

## Serious

### 5. No spammy / padding markdown

```bash
find tasks/<task-name>/environment \( -name '*.md' -o -name '*.rst' \) -exec wc -w {} + | sort -n
```

- [ ] Every doc serves a realistic codebase purpose (contracts, README, plausible internal docs).
- [ ] No large generated manuals/policy tomes added only to inflate context length.

### 6. Natural, human-authored feel

- [ ] Code comments sound like a real developer wrote them (no uniform `// Bug: …` skeleton across files).
- [ ] Instructions are conversational, not LLM boilerplate ("You are an expert…", checklist dumps).
- [ ] No excessive markdown structure or identical phrasing repeated across every file.

## Cleanup

### 7. No stray root / junk files

```bash
find tasks/<task-name> \( -name 'rubric.md' -o -name 'rubric.txt' \
  -o -name 'difficulty-check-summary.md' -o -name '.ruff_cache' \
  -o -name '__pycache__' -o -name '.pytest_cache' \) -print
```

- [ ] None of the above present anywhere in the task tree.

### 8. Valid `task.toml` metadata

```bash
python3 -c "import tomllib; print(tomllib.loads(open('tasks/<task-name>/task.toml','rb').read().decode()))"

# Milestone-specific: top-level [agent]/[verifier] must NOT exist — must return nothing
grep -nE '^\[agent\]|^\[verifier\]' tasks/<task-name>/task.toml

# name field must NOT exist — must return nothing
grep -n '^name ' tasks/<task-name>/task.toml
```

- [ ] Flat tasks: **no** `workdir` in `[environment]`.
- [ ] Milestone tasks: `workdir = "/app"` in shared `[environment]`; each `[[steps]]` has `name`.
- [ ] `number_of_milestones` matches `[[steps]]` count.
- [ ] **Milestone tasks:** no top-level `[agent]`/`[verifier]` (CI blocker; agent review flagging this as "missing" is a hallucination — do NOT add them).
- [ ] **No** top-level `name` field (not a recognized field; flagged in every batch).
- [ ] **No** `gpus`, `gpu_types`, `docker_flags` unless genuinely needed.

### 9. Test function docstrings

```bash
# Every test_* method in tests/ should have a docstring on the next line
grep -Rn 'def test_' tasks/<task-name>/tests/ tasks/<task-name>/steps/*/tests/test_*.py
```

- [ ] Every `test_*` function has a docstring explaining what behavior it validates.

### 10. Instruction tone and length

```bash
for f in tasks/<task-name>/instruction.md tasks/<task-name>/steps/*/instruction.md; do
  [ -f "$f" ] && echo -n "$f: " && wc -w < "$f"
done
```

- [ ] Each instruction ≈ **150–200 words** (see [../10-task-shape/instruction-md.md](../10-task-shape/instruction-md.md)).
- [ ] Conversational developer prompt — not a dense spec dump or step-by-step fix guide.

## Difficulty label

- [ ] If platform agent data exists, declared `difficulty` matches pass-rate bands in [`issues.txt`](../../issues.txt).
- [ ] If no agent data, label as **target** difficulty only — never claim "confirmed hard".

## One-shot audit script

```bash
TASK=tasks/<task-name>
echo "=== 2 canary ===" && grep -RIn 'CANARY-|canary GUID|BENCHMARK DATA' "$TASK" || echo OK
echo "=== 3 wheels ===" && find "$TASK" \( -name '*.whl' -o -name wheels \) -print || echo OK
echo "=== 4 hints ===" && grep -RInE 'Bug:|broken baseline|\b(BUG|FIXME)\b' "$TASK/environment" || echo OK
echo "=== 7 junk ===" && find "$TASK" \( -name rubric.md -o -name rubric.txt -o -name .ruff_cache \) -print || echo OK
echo "=== 9 docstrings ===" && ruff check "$TASK"/tests/ "$TASK"/steps/*/tests/ 2>/dev/null; echo "(also spot-check test_* docstrings by eye)"
echo "=== 10 word counts ===" && for f in "$TASK"/instruction.md "$TASK"/steps/*/instruction.md; do [ -f "$f" ] && wc -w "$f"; done
```

Fix every failure before zipping. Re-run oracle + nop if any fix touches behavior, paths, Dockerfile, or tests.
