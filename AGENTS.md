# AGENTS.md — Project Terminus

> Entry point for any AI agent (Claude, Cursor, etc.) working in this repository.
> Read this file first, then load every file under [`rules/`](rules/) before starting any task work.

## What this repo is

Project Terminus is a local task-factory for **Terminal-Bench 3.0** (Terminus Edition 2) submissions. We build Harbor-format tasks that push beyond current frontier-model abilities, then package them as zips for review.

## How to work here — the short version

1. **Read [`rules/index.md`](rules/index.md)** — it lists every rule file in load order with a one-line description. Load all of them.
2. **Default to milestone tasks** in non-Python languages. Avoid tmux-as-subject.
3. **Pass all four quality gates** (ruff, absolute-path scan, oracle = 1.0, nop = 0.0) before zipping.
4. **Pass every item in [`issues.txt`](issues.txt)** via [`rules/40-workflow/review-feedback-issues.md`](rules/40-workflow/review-feedback-issues.md) — no canary strings, no answer leakage in `environment/`, no wheels in `tests/`, valid metadata, docstrings, instruction tone. **Do not zip until this audit passes.**
5. **Zip flat-root to `tasksubmit/<task-name>.zip`** — never to `ready_to_submit/`.

The full rationale, schemas, and exact commands are in `rules/` — this file is a sign-in, not a substitute.

## Rule hierarchy (load all of these)

```
rules/
├── index.md                          ← entry: load order + conflict rule
├── 00-core/                          ← non-negotiable
│   ├── anti-hallucination.md
│   ├── accepted-lanes.md             ← milestone-first, non-Python, no-tmux-as-subject
│   └── quality-gates.md              ← ruff, abs-path, oracle, nop
├── 10-task-shape/                    ← layout, instruction.md, task.toml
├── 20-environment/                   ← Dockerfile, runtime verifier, offline wheels
├── 30-tests/                         ← test.sh, ruff clean, oracle/nop contract
├── 40-workflow/                      ← this-repo conventions, pre-submit checklist, revision
└── 90-reference/                     ← examples, archived deep spec
```

On conflict between any two rules, prefer the **stricter** one. The memory layer (see below) overrides rules when newer and time-bounded.

## Repo layout

```
Project-Terminus/
├── AGENTS.md                # this file
├── CLAUDE.md                # Claude-specific entry; aliases AGENTS.md
├── rules/                   # canonical task-authoring rules (load all)
├── .cursor/rules/           # archived legacy .mdc files (deep reference only)
├── ideas.md                 # task-idea backlog
├── tasks/<task-name>/       # active task development
├── tasksubmit/              # zips ready for submission
└── jobs/                    # harbor run output (gitignored)
```

There is no `Makefile`, `ready_to_submit/`, or `scripts/` workflow in the current repo state — those have been retired in favor of `harbor` CLI commands directly.

## Submission workflow (one screen)

```bash
# 1. Develop the task under tasks/<task-name>/ following rules/10-task-shape/layout.md

# 2. Run the quality gates (rules/00-core/quality-gates.md)
ruff check tasks/<task-name>/tests/
ruff check tasks/<task-name>/steps/*/tests/    # milestone tasks
grep -RnE '(^|[^/])(\./|\.\./)' tasks/<task-name>/    # absolute-path scan
harbor run -p tasks/<task-name> -a oracle --job-name "oracle__<task>__$(date +%Y%m%d-%H%M%S)" -q
harbor run -p tasks/<task-name> -a nop    --job-name "nop__<task>__$(date +%Y%m%d-%H%M%S)" -q

# 3. Verify oracle = 1.0 and nop = 0.0 from jobs/<job>/.../verifier/reward.txt and result.json

# 4. Zip with flat root layout (rules/40-workflow/repo-conventions.md)
cd "tasks/<task-name>" && zip -r "../../tasksubmit/<task-name>.zip" . \
    -x "environment/target/*" -x "**/__pycache__/*" -x "**/*.pyc" -x "**/.pytest_cache/*"

# 5. Verify task.toml is at the zip root (not nested under <task-name>/)
unzip -l tasksubmit/<task-name>.zip | head
```

Full ordered checklist with every check spelled out: [`rules/40-workflow/pre-submit-checklist.md`](rules/40-workflow/pre-submit-checklist.md).

## Anti-hallucination policy (this is enforced)

- Never claim a file exists without reading it.
- Never claim a test passed without running it (read the actual `reward.txt`).
- Never claim "CI-clean" or "ready" without local oracle + nop runs.
- Difficulty without agent data is **target**, not confirmed.
- Codebase size requires a counted-files justification.

The mandatory self-check before declaring a task done lives in [`rules/00-core/anti-hallucination.md`](rules/00-core/anti-hallucination.md).

## Memory layer (Claude-specific, optional for other agents)

Claude operating in this repo has a persistent memory layer under `~/.claude/projects/-home-adarsh-ambiguous-Project-Terminus/memory/`. It contains:

- **Feedback overrides** — corrections the user has given that bind future behavior (e.g., agent timeout cap, zip-root layout, reward-tail block).
- **References** — pointers to external resources (e.g., harbor CLI requirements).

When a memory entry conflicts with these rules, the **newer entry wins** (memory tracks live corrections; rules track the durable spec). See [`CLAUDE.md`](CLAUDE.md) for the memory map.

## Harbor CLI requirements

| Task type | Minimum Harbor version |
|---|---|
| Flat (root `instruction.md`, `tests/`, `solution/`) | 0.1.45 or 0.8.0+ |
| Milestone (`steps/milestone_N/`, `[[steps]]` blocks) | **0.8.0+** |

Upgrade: `uv tool upgrade harbor`.

## Common failure modes (and where they're covered)

| Symptom | Likely cause | Rule file |
|---|---|---|
| Reviewer rejects for Bug comments / answer leakage | `environment/` hints not stripped | [`rules/40-workflow/review-feedback-issues.md`](rules/40-workflow/review-feedback-issues.md) |
| Zip shipped with canary / wheels / rubric.md | Skipped `issues.txt` audit before zip | [`rules/40-workflow/review-feedback-issues.md`](rules/40-workflow/review-feedback-issues.md) |
| `agent.timeout_sec must be between 1 and 1800` | timeout > 1800 in `task.toml` | [`rules/10-task-shape/task-toml.md`](rules/10-task-shape/task-toml.md) |
| `RewardFileNotFoundError` | `set -e` killed `test.sh` before reward block | [`rules/30-tests/test-sh.md`](rules/30-tests/test-sh.md) |
| CI rejects `test.sh` tail | non-canonical reward block | [`rules/30-tests/test-sh.md`](rules/30-tests/test-sh.md) |
| Oracle = 0 on platform but 1 locally | path mismatch / missing dep | [`rules/30-tests/oracle-nop-contract.md`](rules/30-tests/oracle-nop-contract.md) |
| NOP returns 1 | expected output in `environment/` or tests too lenient | [`rules/30-tests/oracle-nop-contract.md`](rules/30-tests/oracle-nop-contract.md) |
| ruff F401 / F841 | unused imports or unused locals in tests | [`rules/30-tests/ruff-clean.md`](rules/30-tests/ruff-clean.md) |
| Zip has nested `<task-name>/task.toml` | zipped the folder instead of its contents | [`rules/40-workflow/repo-conventions.md`](rules/40-workflow/repo-conventions.md) |
| `codebase_size` rejected | thresholds (small ≥ 20, large ≥ 200 env files) | [`rules/10-task-shape/task-toml.md`](rules/10-task-shape/task-toml.md) |
| Verifier fails on milestone | Harbor < 0.8.0 | [`rules/40-workflow/repo-conventions.md`](rules/40-workflow/repo-conventions.md) |

## What this repo will reject

- Python "fix this script" tasks (Python only if genuinely hard).
- Tasks whose subject is tmux / asciinema / shell-replay capture.
- `easy` difficulty or `minimal` codebase submissions.
- UI-building or multi-container tasks without prior approval.
- Tasks where the oracle hardcodes the answer.
- Tasks where tests reveal the exact expected output.
- Anything that requires internet at runtime.

Full reject list in [`rules/00-core/accepted-lanes.md`](rules/00-core/accepted-lanes.md#avoid-list-rejected-on-sight).
