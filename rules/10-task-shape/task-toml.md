# 10-task-shape — `task.toml`

**Scope:** The `task.toml` at the root of every task directory.

## Schema (Terminus Edition 2)

```toml
version = "2.0"

[metadata]
author_name = "Anonymous"
author_email = "Anonymous"
category = "<one of the valid categories>"
subcategories = ["<...>"]
difficulty = "medium"        # or "hard" — never "easy" / "minimal" for new tasks
codebase_size = "small"      # or "large" — never "minimal"
number_of_milestones = 0     # 0 for flat; exact milestone count otherwise
languages = ["go"]           # primary language first; do not list Python unless Python is primary
tags = ["debugging", "..."]
expert_time_estimate_min = 45.0
junior_time_estimate_min = 120.0

[agent]
timeout_sec = 1800.0         # HARD CAP — see "Agent timeout cap" below

[verifier]
timeout_sec = 420.0          # tune to task; no hard ceiling in practice

[environment]
allow_internet = false       # false for offline tasks; true if task needs internet
build_timeout_sec = 600.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
# no workdir on flat tasks — it is a milestone-only field (see below)
```

Milestone task adds `[[steps]]` blocks (one per milestone) and **must omit** root `[agent]` / `[verifier]` — each milestone carries its own `[steps.agent]` / `[steps.verifier]`:

```toml
[[steps]]
name = "milestone_1"

[steps.agent]
timeout_sec = 1800.0

[steps.verifier]
timeout_sec = 300.0

[[steps]]
name = "milestone_2"
# ...
```

### Milestone tasks: no top-level `[agent]` / `[verifier]` — HARD BLOCKER

A milestone `task.toml` has **only** the per-step `[steps.agent]` / `[steps.verifier]`
blocks. Do **not** add a top-level `[agent]` or `[verifier]` section under any
circumstances — the per-step timeouts are the only timeouts that apply.

**If an Agent Review / Quality Review report says "missing top-level `[agent]`/`[verifier]`":
that is a confirmed LLM-judge hallucination. Do NOT add those blocks. Adding them
introduces the very metadata error that CI flags.**

Scan to verify a milestone task is clean:

```bash
# Must return NOTHING for a milestone task
grep -nE '^\[agent\]|^\[verifier\]' tasks/<task-name>/task.toml
```

Flat (non-milestone) tasks **do** use top-level `[agent]` / `[verifier]` and have no `[[steps]]`.

Some **older accepted tasks** in `tasks/` still carry the top-level blocks. That is
**not** a precedent — match the official `milestone-template/task.toml` (which omits
them), not the stragglers. A human reviewer confirmed (2026-06) the top-level blocks
must be removed from a milestone task even though accepted tasks contained them.

## Hard rules

### Agent timeout cap — `agent.timeout_sec ≤ 1800.0`

Terminus CI (`run_static_checks.py --version edition_2`) enforces `1 ≤ agent.timeout_sec ≤ 1800`. **Anything above 1800 fails the build** with `agent.timeout_sec must be between 1 and 1800 seconds, got <N>`.

This applies to **every** `[agent]` and `[steps.agent]` block. If a task feels like it needs more, trim scope — do not raise the cap.

Verifier timeout has no equivalent ceiling in practice (420 has been accepted), but keep it reasonable.

### `codebase_size` thresholds

CI counts meaningful files in `environment/` (excluding `Dockerfile` and `docker-compose*`):

| `codebase_size` | Env file count |
|---|---|
| `small` | 20–199 |
| `medium` | (in between — generally avoid) |
| `large` | ≥ 200 |
| `minimal` | < 20 files — **accepted** (re-allowed May 11, 2026; CI no longer blocks) |

**Never pad with filler files** to clear a threshold — the size must be intrinsically justified by the task.

### `allow_internet` — declare honestly

A static check enforces that the declared value matches what the task actually needs. **Declaring `false` when the task requires internet emits an ERROR and blocks submission.**

- Default is `false` (offline). Use it for tasks whose agent code and verifier need no network.
- Set `true` if the task genuinely requires internet at solve time (e.g., HuggingFace downloads, live API).

See [../20-environment/runtime-verifier.md](../20-environment/runtime-verifier.md).

### `number_of_milestones` must match `[[steps]]` count

A `number_of_milestones = 3` with two `[[steps]]` blocks fails CI. Count them.

### Milestone tasks: ONLY `[steps.agent]` / `[steps.verifier]` — never top-level `[agent]` / `[verifier]`

A milestone task declares its timeouts **per step**, inside each `[[steps]]` block as
`[steps.agent]` and `[steps.verifier]`. It must **not** also carry root-level `[agent]`
or `[verifier]` blocks. (Flat tasks are the opposite: they carry root `[agent]` /
`[verifier]` and have no `[[steps]]`.)

If an Agent/Quality Review flags a milestone task as "missing top-level `[agent]` /
`[verifier]`", that is a **hallucination** (the reviewer is an LLM judge — see
[../40-workflow/pre-submit-checklist.md](../40-workflow/pre-submit-checklist.md) §10c).
Do **not** add the blocks to satisfy it — doing so introduces the very metadata error
CI flags. Confirmed via team guidance 2026-06.

### Fixed values

- `version = "2.0"`
- `author_name` / `author_email` — pick one identity and use it consistently across submissions; the example above uses `"Anonymous"`.

### Never add a top-level `name` field (Batch 2 feedback — June 1, 2026)

`name` is **not a recognized field** in `task.toml`. It is flagged on almost every submission that includes it. Do not add `name = "..."` at the root level or anywhere else in `task.toml`.

```bash
# Must return nothing
grep -n '^name ' tasks/<task-name>/task.toml
```

### Optional resource flags — only when actually needed

`gpus`, `gpu_types`, and `docker_flags` must **not** appear in `task.toml` unless the task genuinely requires them. Adding them speculatively is flagged as unnecessary metadata and is a rejection risk.

### `workdir` is milestone-only

Per 2026-05-27 trial feedback, **`workdir` is a milestone-only field. Flat (non-milestone) tasks must not include it** — its presence on a flat task is a cleanup-issue rejection. (This reverses the earlier rule that required `workdir = "/app"` on flat tasks.) Milestone tasks set `workdir = "/app"` in the shared global `[environment]` block (as the `milestone-template` `task.toml` shows).

### Difficulty

- `medium` or `hard` only for new submissions (see [../00-core/accepted-lanes.md](../00-core/accepted-lanes.md)).
- If no agent data exists, the difficulty value is **target** — never claim "confirmed hard" without platform results.

## Valid categories

`software-engineering`, `system-administration`, `build-and-dependency-management`, `data-processing`, `games`, `machine-learning`, `debugging`, `security`, `scientific-computing`, `devops`, `distributed-systems`, `optimization`, `other`.

> **Blocked for new submissions (2026-07-11):** `software-engineering`, `debugging`, and `data-processing` are at capacity — do not use them. **Milestone tasks are also blocked** (cap reached): set `number_of_milestones = 0` and build flat only. See [../00-core/accepted-lanes.md](../00-core/accepted-lanes.md).

## Required `[environment]` resources

| Field | Required | Typical value |
|---|---|---|
| `allow_internet` | yes | `false` |
| `build_timeout_sec` | yes | 600.0 |
| `cpus` | yes | 1–4 |
| `memory_mb` | yes | 2048–8192 |
| `storage_mb` | yes | 10240 |
| `workdir` | **no** on flat tasks (milestone-only) | — |

`memory_mb` and `storage_mb` are commonly forgotten — both are required, both fail CI when missing.

## Comments allowed in `task.toml`

Keep any comments terse (1–2 lines max). **Do not** add a verifier-deps comment (e.g.
"Verifier-only deps … are installed in environment/Dockerfile") — reviewers have cited
that line as evidence of a `test_deps_in_image` violation. The accepted pattern keeps
`task.toml` free of such notes (see [../20-environment/verifier-deps.md](../20-environment/verifier-deps.md)).

Never cite internal rule filenames (e.g. no `terminus-runtime-verifier.mdc`, no `rules/00-core/...`) in committed task files.

## Audit pass before zipping

```bash
# Quick smoke-test (adjust path)
python3 -c "import tomllib; print(tomllib.loads(open('tasks/<task>/task.toml','rb').read().decode()))"
```

Confirm:
- [ ] `version = "2.0"`
- [ ] `agent.timeout_sec ≤ 1800.0` (every block)
- [ ] `allow_internet` matches task reality (`false` for offline, `true` if internet needed)
- [ ] `difficulty ∈ {medium, hard}`
- [ ] `codebase_size ∈ {minimal, small, large}` and file count matches
- [ ] `number_of_milestones` matches `[[steps]]` count
- [ ] `memory_mb`, `storage_mb`, `cpus`, `build_timeout_sec` all present
- [ ] **no** `workdir` on flat tasks (milestone-only field)
- [ ] **no** top-level `name` field (not a recognized field — always flagged)
- [ ] **no** `gpus`, `gpu_types`, `docker_flags` unless actually needed
- [ ] **milestone tasks**: only `[steps.agent]`/`[steps.verifier]` — **no** top-level `[agent]`/`[verifier]`
