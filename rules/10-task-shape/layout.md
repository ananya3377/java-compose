# 10-task-shape — Directory Layout

**Scope:** Applies to every new task's on-disk structure.

## Non-milestone (flat) layout

```
tasks/<task-name>/
  instruction.md
  task.toml
  environment/
    Dockerfile
    .dockerignore
    <agent-visible files>
  solution/
    solve.sh
  tests/
    test.sh
    test_outputs.py
    verifier-tools/        # optional reference utilities
    # no wheels/ — test deps live in /opt/verifier-venv (built in environment/Dockerfile)
```

## Milestone layout — ⛔ BLOCKED for new tasks (2026-07-11)

> Milestone tasks are at capacity and **blocked from submission**. Build **flat** tasks (above) only until the cap lifts. See [accepted-lanes.md](../00-core/accepted-lanes.md). The layout below is retained for reference and for revising already-submitted milestone tasks.

```
tasks/<task-name>/
  task.toml
  environment/
    Dockerfile
    .dockerignore
    <agent-visible files>
  steps/
    milestone_1/
      instruction.md
      tests/
        test.sh
        test_m1.py
      solution/
        solve.sh
    milestone_2/
      instruction.md
      tests/
        test.sh
        test_m2.py
      solution/
        solve.sh
    ...
```

### Milestone hard rules

- **Never** create a root-level `instruction.md`, `tests/`, `solution/`, `milestones.md`, `milestone_1.md`, root `solveN.sh`, or root `test_mN.py` in a milestone task.
- Each milestone owns its own `instruction.md`, `tests/`, and `solution/`.
- Each milestone's `instruction.md` covers **only that milestone** — never reveal future milestones.
- Each milestone's `tests/test_mN.py` defines class `TestMilestoneN`.
- Each milestone's `solution/solve.sh` does the actual work for **that milestone only**. Do not ship redundant numbered scripts (`solveN.sh`) alongside it.
- **`solve.sh` must NOT re-run or re-implement prior milestones' logic** — Harbor shares one container across steps, so prior milestone state already exists. Copying files already written by a previous milestone's `solve.sh` is also wrong — each `solve.sh` operates only on what its own milestone requires. (Batch 2 review: noted in 20/53 submissions.)
- Each milestone depends on the previous milestone's state but must not reveal it.

## What never goes inside `environment/`

- Tests (`test.sh`, `test_*.py`).
- Solution scripts (`solve*.sh`).
- Ground-truth files (`expected_*.json`, `answer.txt`).
- Hidden hints, `BUG:` / `Bug:` comments, `broken baseline` annotations, `TODO: solution here` markers, or any comment that names the defect or fix location.
- Hidden expected-output snapshots.
- AI-specific filenames (`CLAUDE.md`, `skills.md`, `AGENTS.md` — those belong at repo root if anywhere).

Anything under `environment/` is agent-visible. Treat it as the user-facing workspace.

### Docs in `environment/` — contracts yes, the fix no

A doc may describe **contracts**: the output schema/field names, the public API, what
a command should do, the on-disk *layout* of a structure (which fields exist, in what
order). It must **not** spell out the exact algorithm or magic constant that the
**buggy code gets wrong** — that turns "fix the bug" into "copy the value from the doc."

Concretely, for a debugging task: do not ship an `environment/` doc that gives the
exact polynomial/seed/mask/hash an agent must restore, the step-by-step algorithm the
broken function should implement, or a worked example of the corrected computation.
A reviewer reads such a doc as answer leakage even when it has no `BUG:`/`TODO:`
breadcrumbs (real 2026-06 rejection: `crc32c.md`/`bloom-filter.md` that printed the
Castagnoli polynomial and the bloom seed the code was supposed to use).

The litmus test: **with the spec docs deleted, is every remaining bug still inferable
from the code itself** (a visible inconsistency, a misleading name, a wrong-but-named
algorithm like a `crc32c` fn using the IEEE polynomial)? If a bug hinges on an
arbitrary constant that lived only in a doc, the task is unsolvable once the doc is
(rightly) removed — make that constant correct in the broken code and leave a bug the
code reveals. Keep the per-milestone output schema in `instruction.md` as a fenced
contract block (allowed), not in a separate spec doc.

## What never gets copied into the Docker image

- `solution/` (any form).
- `tests/` (any form).
- Hidden verifier-tools.

The verifier mounts `tests/` and `solution/` at runtime; the image must not contain them. See [../20-environment/dockerfile.md](../20-environment/dockerfile.md).

## Cross-check before zipping

```bash
ls -la tasks/<task-name>/
# Flat:   instruction.md, task.toml, environment/, solution/, tests/
# Milestone: task.toml, environment/, steps/milestone_1/.../, ...
```

If you see both a root `instruction.md` *and* a `steps/` directory, the layout is broken — pick one.
