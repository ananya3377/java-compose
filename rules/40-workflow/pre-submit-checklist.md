# 40-workflow — Pre-Submit Checklist

**Scope:** The ordered, runnable check sequence before any `tasksubmit/<task-name>.zip` is built.

This is **not** prose to skim. Execute top-down. Fix the first failure before moving on. Do not jump ahead.

## 0. Sanity — task tree exists where expected

```bash
ls -la tasks/<task-name>/
```

- Flat: `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/` at task root.
- Milestone: `task.toml`, `environment/`, `steps/milestone_N/` (no root `instruction.md` / `tests/` / `solution/`).

If wrong layout → fix per [../10-task-shape/layout.md](../10-task-shape/layout.md). Do not continue.

## 1. `task.toml` audit

```bash
python3 -c "import tomllib; d=tomllib.loads(open('tasks/<task-name>/task.toml','rb').read().decode()); print(d)"
```

Confirm against [../10-task-shape/task-toml.md](../10-task-shape/task-toml.md):

- [ ] `version = "2.0"`
- [ ] `agent.timeout_sec ≤ 1800.0` (every `[agent]` and `[steps.agent]`)
- [ ] `environment.allow_internet` matches task reality — `false` for offline tasks, `true` if the task genuinely needs internet (static check enforces honesty; mismatch blocks submission)
- [ ] `difficulty ∈ {"medium", "hard"}`
- [ ] `codebase_size ∈ {"minimal", "small", "large"}` and file count matches bracket
- [ ] `number_of_milestones` matches `[[steps]]` count exactly
- [ ] `memory_mb`, `storage_mb`, `cpus`, `build_timeout_sec` all present
- [ ] **no** `workdir` on flat tasks (milestone-only field)
- [ ] Languages list does not include Python unless Python is primary
- [ ] `author_name` / `author_email` set and consistent across submissions
- [ ] each `[[steps]]` block has a `name` (milestone tasks); flat tasks need no top-level `name`
- [ ] **milestone tasks: only `[steps.agent]` / `[steps.verifier]`, NO top-level `[agent]` / `[verifier]`** — scan: `grep -nE '^\[agent\]|^\[verifier\]' task.toml` must return nothing (a review report saying "missing top-level agent/verifier" is a hallucination — never add those blocks)
- [ ] **no** top-level `name` field — `grep -n '^name ' task.toml` must return nothing
- [ ] **no** `gpus`, `gpu_types`, `docker_flags` unless the task genuinely requires them

## 2. `instruction.md` audit

For each `instruction.md` (root for flat, each milestone for milestone):

```bash
wc -w tasks/<task-name>/instruction.md
grep -nE '(^|[^/])(\./|\.\./)' tasks/<task-name>/instruction.md || echo "OK: no relative paths"
grep -nE '(CANARY-|<task-name>)' tasks/<task-name>/instruction.md || echo "OK: no canary/task-name"
```

- [ ] Word count ≈ 100–250.
- [ ] All paths absolute (`/app/...`).
- [ ] No task name, no `CANARY-*` string.
- [ ] No stepwise solution guidance.
- [ ] Output paths match `test_outputs.py`, `Dockerfile`, `solve.sh` byte-for-byte.

See [../10-task-shape/instruction-md.md](../10-task-shape/instruction-md.md).

## 3. **Gate 1 — Ruff clean**

```bash
ruff check tasks/<task-name>/tests/
ruff check tasks/<task-name>/steps/*/tests/        # milestone only
ruff check tasks/<task-name>/tests/verifier-tools/ # if present
```

Must return **no findings**. F401 and F841 are blockers. See [../30-tests/ruff-clean.md](../30-tests/ruff-clean.md).

## 4. **Gate 2 — Absolute-path scan**

```bash
# Search for relative paths in all task source files
grep -RnE '(^|[^/])(\./|\.\./)' \
    tasks/<task-name>/instruction.md \
    tasks/<task-name>/tests/ \
    tasks/<task-name>/environment/Dockerfile \
    tasks/<task-name>/solution/ \
    2>/dev/null || echo "OK: no relative paths"
```

Cross-file consistency:

```bash
# A path mentioned in instruction.md must appear identically elsewhere
grep -oE '/app/[A-Za-z0-9_./-]+' tasks/<task-name>/instruction.md | sort -u
# spot-check those paths appear in test_outputs.py, Dockerfile, solve.sh
```

## 5. `test.sh` reward-block check

```bash
tail -6 tasks/<task-name>/tests/test.sh
# milestone:
for f in tasks/<task-name>/steps/*/tests/test.sh; do echo "== $f =="; tail -6 "$f"; done
```

Confirm the file **ends with** the literal reward block the static checker
enforces — bare `$?`, 4-space indent, ending at `fi`, **nothing after**:

```bash
python3 -m pytest ... -rA
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
```

- `set -uo pipefail` at the top (not `set -e`).
- pytest is the command immediately before the `if`/`rc=$?`, so `$?` is pytest's exit.
- Either the bare `if [ $? -eq 0 ]` inline form **or** the `rc=$?` variable capture form immediately after pytest is accepted (Jun 3, 2026). The variable form is preferred.
- **No** `exit` after `fi` — static checker enforces the reward block as the file tail.

See [../30-tests/test-sh.md](../30-tests/test-sh.md).

## 6. Verifier-deps check (isolated venv, not system Python)

```bash
# Test deps must go in an isolated /opt/verifier-venv, NOT the system Python or wheels in tests/
grep -nE 'verifier-venv|python3-venv' tasks/<task-name>/environment/Dockerfile   # should show venv build
grep -nE 'break-system-packages' tasks/<task-name>/environment/Dockerfile        # MUST return nothing
find tasks/<task-name> -name '*.whl' -o -name 'wheels' -type d                   # must return nothing
grep -RnE 'pip install|python -m venv|python3 -m venv' tasks/<task-name>/tests/ tasks/<task-name>/steps/*/tests/ 2>/dev/null  # must return nothing
# After build, the SYSTEM python must NOT import the test deps:
# docker run --rm <img> python3 -c "import pytest" 2>&1 | grep -q "No module" && echo OK
```

- [ ] `environment/Dockerfile` builds `/opt/verifier-venv` and installs test deps there (pinned); `python3-venv` in apt.
- [ ] Test deps are **not** in the system/app Python (no `--break-system-packages`); `test_deps_in_image` passes.
- [ ] No `.whl` files and no `wheels/` directory anywhere under `tests/`.
- [ ] `test.sh` runs `/opt/verifier-venv/bin/python -m pytest` — no `pip install`, no venv creation at test time.
- [ ] No verifier-deps comment in `task.toml`.
- [ ] `.dockerignore` excludes `tests/` and `solution/`.

See [../20-environment/verifier-deps.md](../20-environment/verifier-deps.md).

## 6b. Dockerfile — base images, context size, environment problems

```bash
# Every FROM must carry @sha256:. Both greps must return nothing.
grep -nE '^[[:space:]]*FROM ' tasks/<task-name>/environment/Dockerfile | grep -v '@sha256:'
grep -nE '^[[:space:]]*FROM .*:latest' tasks/<task-name>/environment/Dockerfile

# Build context size (CI blockers: total > 100 MiB, any file > 50 MiB)
du -sh tasks/<task-name>/environment/
find tasks/<task-name>/environment -type f -size +50M -print
```

- [ ] Every `FROM` line carries an `@sha256:` digest (blocker — CI rejects tag-only bases).
- [ ] No floating `latest` tag.
- [ ] Final runtime base is sanctioned or exempt (blocker — unsanctioned bases rejected).
- [ ] `environment/` total ≤ 100 MiB; no single file > 50 MiB (blocker).
- [ ] No privileged mode required.
- [ ] No AI-scaffolding filenames (`CLAUDE.md`, `skills.md`) inside `environment/`.
- [ ] `solution/` and `tests/` not `COPY`'d into the image.

See [../20-environment/dockerfile.md](../20-environment/dockerfile.md).

## 7. Environment hygiene — no answer leakage

The agent-visible `environment/` must read like a codebase in a realistic state — **not** breadcrumbs leading to the answer.

```bash
# (a) Marker comments and stray answer files — should all return nothing
grep -RInE '\b(BUG|FIXME|HACK|XXX)\b' tasks/<task-name>/environment/
grep -RInE 'TODO.*(solution|fix|bug)|fix (this|me|the bug)|the (bug|issue) is' tasks/<task-name>/environment/
ls tasks/<task-name>/environment/*expected*.* 2>/dev/null
ls tasks/<task-name>/environment/*answer*.* 2>/dev/null
ls tasks/<task-name>/environment/solution* 2>/dev/null
ls tasks/<task-name>/environment/test* 2>/dev/null

# (b) Read EVERY comment and doc by eye — keyword greps miss prose hints
#     like "the off-by-one is here". Surface comment lines + list every doc:
grep -RInE '(^|[[:space:]])(#|//|/\*|\*)' tasks/<task-name>/environment/ 2>/dev/null
find tasks/<task-name>/environment \( -name '*.md' -o -name '*.rst' -o -name '*.txt' \)
```

- [ ] No `BUG`/`FIXME`/`HACK`/`XXX` markers, no `TODO`+solution/fix/bug comments.
- [ ] No comment **names a bug, labels a fix location, or describes the intended solution path** — even with no marker keyword. Rewrite or remove.
- [ ] Doc files under `environment/` describe the system's **API or contracts**, never the task's solution (no walkthroughs, no answer-revealing notes).
- [ ] No hidden hints, expected outputs, solution files, or test files in `environment/`.

See [../20-environment/dockerfile.md](../20-environment/dockerfile.md) (image-hygiene blockers) and [../10-task-shape/instruction-md.md](../10-task-shape/instruction-md.md) (no how-to-solve guidance).

## 7b. Submission cleanup — canary, junk, rubric files

```bash
# (a) No canary strings ANYWHERE in the submission (report blocker)
grep -RIn 'CANARY-' tasks/<task-name>/ || echo "OK: no CANARY- strings"
grep -RIn 'BENCHMARK DATA SHOULD NEVER APPEAR' tasks/<task-name>/ || echo "OK: no canary line"
grep -RIn 'canary GUID' tasks/<task-name>/ || echo "OK: no canary GUID line"

# (b) No stray files that don't belong in a task
find tasks/<task-name> \( -name 'rubric.md' -o -name 'rubric.txt' \
    -o -name 'difficulty-check-summary.md' -o -name '.ruff_cache' \
    -o -name '__pycache__' -o -name '.pytest_cache' \) -print
```

- [ ] No `CANARY-*`, no `BENCHMARK DATA...` line, no `# canary GUID:` anywhere.
- [ ] No `rubric.md` / `rubric.txt` (rubric is authored in the platform UI — see [repo-conventions.md](repo-conventions.md)).
- [ ] No `difficulty-check-summary.md`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`.

## 7c. Rubric — emit in chat, author on the platform

The rubric is **not** a file. **Emit it in the chat as a ready-to-paste block** — one `#Rubric N` block per milestone — so the user can copy it into the submission UI. Every line starts `Agent`, names a **trace-evidenced** behavior, ends `, +N`/`, -N`; scores ∈ ±1/2/3/5 (never 4); ≥5 checks with ≥3 negatives; positives sum 10–40 (aim ~10–20) per milestone. See [rubric.md](rubric.md).

## 8. **Gate 3 — Oracle must pass**

```bash
harbor run -p tasks/<task-name> -a oracle \
    --job-name "oracle__<task>__$(date +%Y%m%d-%H%M%S)" -q
```

Confirm:

```bash
# Flat:
cat jobs/oracle__*/<task-name>__1/verifier/reward.txt  # must be 1
# Milestone:
for f in jobs/oracle__*/<task-name>__1/steps/*/verifier/reward.txt; do echo "$f:"; cat "$f"; done
```

Every `reward.txt` = `1`. Trial mean = `1.000`. If not, fix the task (not the test) and re-run. See [../30-tests/oracle-nop-contract.md](../30-tests/oracle-nop-contract.md).

## 9. **Gate 4 — NOP must fail**

```bash
harbor run -p tasks/<task-name> -a nop \
    --job-name "nop__<task>__$(date +%Y%m%d-%H%M%S)" -q
```

Every `reward.txt` = `0`. Trial mean = `0.000`. If NOP passes anywhere, tests are leaky — fix per [../30-tests/oracle-nop-contract.md](../30-tests/oracle-nop-contract.md).

## 10. Final self-check from anti-hallucination rules

Run the mandatory self-check from [../00-core/anti-hallucination.md](../00-core/anti-hallucination.md) — every item with real evidence (file contents, command output). If any answer is "not verified", do not zip.

## 10b. Review feedback issues — mandatory before zip

Run every check in [review-feedback-issues.md](review-feedback-issues.md) (derived from repo-root [`issues.txt`](../../issues.txt)). **Do not build a zip until all applicable items pass.**

At minimum, confirm with command output:

- [ ] No canary strings (`CANARY-*`, canary GUID, benchmark-canary line)
- [ ] No `.whl` / `wheels/` under `tests/`; verifier deps only in `environment/Dockerfile` `/opt/verifier-venv`
- [ ] No answer leakage in `environment/` (no `Bug:` / `broken baseline` / fix-location comments; no test-fixture names in agent-visible code)
- [ ] No `rubric.md` / `rubric.txt` / junk caches in the task tree
- [ ] Valid `task.toml` metadata (`workdir` milestone-only; milestone `name` on every `[[steps]]`)
- [ ] Every `test_*` has a docstring; each instruction ≈ 150–200 words, conversational tone
- [ ] Rubric emitted in chat for platform UI (see [rubric.md](rubric.md)) — not verified from repo alone

Re-run gates 3–4 (oracle, nop) if any fix touched behavior, paths, Dockerfile, or tests.

## 10c. Reviewer reports — read critically, the judge is an LLM

The platform's Agent Review / Quality Review / Test-Quality reports are produced by an
**LLM-as-judge**. They are useful signal but **hallucinate** — and blindly "fixing" a
hallucinated finding can **deform a correct task** (e.g. adding top-level `[agent]`/
`[verifier]` to a milestone task, or weakening a test). For every report:

1. **Read the full summary in detail** before changing anything. Decide per finding
   whether it is real or a hallucination; cite the file/line that proves your call.
2. **Don't deform the task to satisfy a judge.** If a finding contradicts a rule here or
   a known-good, oracle=1.0/nop=0.0 task, treat it as suspect. Known hallucinations:
   "milestone task missing top-level `[agent]`/`[verifier]`" (see
   [../10-task-shape/task-toml.md](../10-task-shape/task-toml.md)).
3. A **`behavior_in_task_description` / spec finding is usually real**: if a test enforces
   a contract the instruction only implies, make the instruction state it (don't drop the
   test). Tune `difficulty` to the observed agent pass rate.
4. Work the reviewer checklist before resubmitting: **Difficulty checks · Quality checks ·
   Test-quality report · Severe spec issues · `feedbackReport` · `issues.txt`**, and
   confirm **rubric criteria contain no verifier wording or test-only paths** (no
   `test.sh`/`/tests/`/`pytest`/`verifier`/`reward.txt`; `/app/...` source paths only).
   See [rubric.md](rubric.md) and [review-feedback-issues.md](review-feedback-issues.md).
5. Re-run gates 3–4 after any change a finding prompted.

## 11. Build zip (only after sections 0–10, 10b, and gates 1–4 pass)

```bash
cd "tasks/<task-name>" && zip -r "../../tasksubmit/<task-name>.zip" . \
    -x "environment/target/*" \
    -x "**/__pycache__/*" \
    -x "**/*.pyc" \
    -x "**/.pytest_cache/*" \
    -x "**/.ruff_cache/*" \
    -x "rubric.md" -x "rubric.txt" \
    -x "difficulty-check-summary.md"
```

Verify flat root:

```bash
unzip -l tasksubmit/<task-name>.zip | head
# First non-directory entry MUST be task.toml (not <task-name>/task.toml)
```

See [repo-conventions.md](repo-conventions.md).

## 12. Mark ready

Now — and only now — the task is ready to ship. State the verification outputs (oracle/NOP reward, ruff result, zip filename), not just "done".
