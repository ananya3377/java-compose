# 00-core — Accepted Task Lanes

**Scope:** Applies to every new task idea and every new submission in this repo.

These are the lanes that survive review. Build inside them; do not bargain.

## BLOCKED CATEGORIES (as of 2026-07-11)

> **`software-engineering`, `debugging`, and `data-processing` categories are blocked from submission.** The team has reached capacity on these categories. Do not start new tasks with `category = "software-engineering"`, `category = "debugging"`, or `category = "data-processing"`. Any submission using these categories will be rejected. Choose an alternative category from the valid list (`build-and-dependency-management`, `system-administration`, `devops`, `distributed-systems`, `optimization`, `security`, `scientific-computing`, `machine-learning`, etc.).
>
> **Milestone tasks are also blocked (max limit reached).** Do not start new milestone tasks (`steps/milestone_N/` layout, `workdir`/milestone-only fields). The team has reached the milestone-task cap. Build **flat (non-milestone)** tasks only. Any new milestone submission will be rejected.

## Repo-wide defaults (this repo, all new tasks)

1. **Flat-only (milestone cap reached, 2026-07-11).** Milestone tasks (`steps/milestone_N/` layout) are **blocked** — the team has hit the milestone-task limit. Build **flat (non-milestone)** tasks only until this block lifts. (Historically milestone was the preferred lane; that preference is suspended while the cap holds.)
2. **Non-Python primary language.** Go, TypeScript / Node, Rust, Java, Bash, Ruby, Zig, Elixir, Perl, Kotlin, C / C++ — pick whichever fits the problem. **Use Python only if the task is genuinely hard** (e.g., complex parsing, ML internals, autograd). Python "fix this script" tasks are rejected.
3. **No tmux as task subject.** `tmux` (and `asciinema`) **must be installed in the Docker image** — the harness requires them. But never design a task whose challenge is *about* tmux: don't ask the agent to wrangle tmux panes, sessions, scripted captures, or pipe replays. Same goes for asciinema.
4. **Difficulty:** `medium` or `hard` only. No `easy`, no `minimal`-codebase submissions.
5. **`codebase_size`:** `small` (20–199 env files), `large` (≥200 env files), or `minimal` (< 20 env files; re-allowed as of May 11, 2026). See [task-toml.md](../10-task-shape/task-toml.md).
6. **Single-container.** No multi-container compose unless explicitly approved.
7. **`allow_internet` must be honest.** If the task needs internet at solve time (e.g., HuggingFace downloads, pip install at agent runtime), set `allow_internet = true`. If the task is fully offline, set `allow_internet = false`. A static check now enforces this: declaring `false` when the task actually needs internet emits an ERROR and blocks submission. Default is still `false` for fully offline tasks.

## Most accepted lanes

> **Category note (2026-07-11):** `data-processing` is now blocked alongside `software-engineering` and `debugging`. Lanes below that previously used `data-processing` must pick a still-open category (`build-and-dependency-management`, `system-administration`, `devops`, `distributed-systems`, `optimization`, `security`, `scientific-computing`, `machine-learning`). All lanes must be **flat**, not milestone.

### 1. TypeScript / Node API + SQLite
- Category: `system-administration` (**not** `software-engineering`, `debugging`, or `data-processing` — blocked)
- Subcategories: `api_integration`, `db_interaction`
- Strong behaviors: request validation, pagination, idempotency, transaction rollback, duplicate handling, report generation, malformed-input recovery.

### 2. Go CLI or service debugging
- Category: `system-administration` or `build-and-dependency-management` (**not** `debugging` or `data-processing` — blocked)
- Strong behaviors: log replay, checksum repair, binary/JSONL decoding, restart handling, malformed record recovery, deterministic export.

### 3. Rust parser or binary decoder
- Category: `build-and-dependency-management` or `system-administration` (**not** `debugging` or `data-processing` — blocked)
- Strong behaviors: byte offsets, checksum validation, streaming decode, strict CLI output, deterministic artifact generation.

### 4. Java service / config / migration
- Category: `system-administration` (**not** `software-engineering` or `data-processing` — blocked)
- Subcategories: `api_integration` or `db_interaction`
- Strong behaviors: config precedence, schema migration, validation, retry policy, audit export.

### 5. Tool-specific pipeline (FFmpeg, ImageMagick, Graphviz, jq, SQLite, CMake, Cargo, npm)
- Category: `build-and-dependency-management` (**not** `data-processing` — blocked)
- Subcategories: use `build_pipeline` or a domain-appropriate one — **`tool_specific` is not a valid subcategory** (flagged in Batch 2 reviews; see also [revision.md](../40-workflow/revision.md))
- Strong behaviors: repair a pipeline, validate generated artifacts semantically, deterministic output.

### 6. DB interaction (SQLite preferred for single-container)
- Category: `system-administration` (**not** `software-engineering` or `data-processing` — blocked)
- Subcategories: `db_interaction`
- Strong behaviors: migrations, constraints, indexes, backfill, rollback, query correctness.

### 7. Milestone debugging — ⛔ BLOCKED (milestone cap reached, 2026-07-11)
- Milestone tasks are blocked entirely; do not build this lane until the cap lifts.
- (For reference only: was `data-processing` / `build-and-dependency-management`, 2–4 milestones, M1 ingestion/parsing → M2 state/DB consistency → M3 reporting/export.)

### 8. Long-context (rare; requires 50k+ token document with real semantic load)
- Subcategory: `long_context`
- Avoid documents solvable by grep or simple lookup.

## Avoid list (rejected on sight)

- **`category = "software-engineering"`, `category = "debugging"`, or `category = "data-processing"`** — all three are blocked as of 2026-07-11; CI will reject.
- **Milestone tasks** (`steps/milestone_N/` layout) — blocked as of 2026-07-11 (cap reached); build flat tasks only.
- Simple Python script repair / Python medium task.
- One failing unit test with one obvious bug.
- Pure CSV conversion / basic JSON formatting.
- "Read files and calculate" with no code repair.
- **Anything where the task subject is `tmux` / `asciinema` / terminal multiplexing / shell-replay capture.**
- UI-building tasks (unless explicitly approved).
- Multi-container compose tasks (unless explicitly approved).
- FastAPI-only tasks (unless unusually strong).
- Tasks where tests reveal the exact expected output.
- Tasks where the oracle just writes hardcoded output files.
- Tasks whose difficulty comes only from many edge cases enumerated in the instruction.
- Tasks with long checklist-like prompts.
- Tasks requiring internet data or external APIs.
- Latency / performance optimization tasks with timing thresholds.
- TerminalBench reskins (existing patterns with only names changed).
- Any task a frontier model can plausibly solve in one short edit.

## Good vs. bad difficulty

**Good difficulty:** multiple interacting bugs; persistent state across runs; DB constraints and rollback; malformed-input recovery; duplicate/replayed events; cross-file schema mismatch; deterministic computed reports; anti-cheat via mutated fixtures.

**Bad difficulty:** vague instruction; many random edge cases; brittle formatting; performance timing; secret exact strings not in instruction; tests that enforce unstated behavior; requiring a specific implementation rather than behavior.

## Difficulty threshold rule (when agent data exists)

**Benchmark models (as of 2026-06-12): Claude Opus 4.8 and GPT-5.5.** Difficulty checks run
the task against these two. "best model" / "worst model" below mean the higher- and
lower-scoring of the two on this task. The threshold bands are **unchanged** — only the
models producing the pass rates changed.

> **Recalibrate.** Both benchmark models are stronger than the previous pair, so a task that
> rated `medium` or `hard` under the old models can now land easier. Do not trust a stale
> difficulty rating — re-derive it from fresh agent data, and expect to need a harder task to
> hold the same band.

Evaluate in order — stop at first match:

- **Hard:** best model ≤ 20%, **or** best > 20% AND worst ≤ 20%.
- **Medium:** worst > 20% and ≤ 60%.
- **Easy:** worst > 60% and ≤ 80% (not eligible for new submissions in this repo).

Without agent data, use **target difficulty** only.

## Default starter (when no specific idea is given)

A **flat** task in one of lanes 1–6 above (milestone is blocked as of 2026-07-11), leaning toward Go log-replay (lane 2), Rust binary decoder (lane 3), or TypeScript+SQLite reconciliation (lane 1). Pick a still-open category (avoid `data-processing`, `software-engineering`, `debugging`). Default to medium-or-hard, small codebase, single container.
