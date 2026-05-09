---
name: df-workspace
description: Establishes a safe branch or isolated worktree for a Dark Factory story and records workspace state. Use when Jira intake is complete and before clarification, spec, planning, or implementation work begins.
---

# DF Workspace

## Goal

Protect the user's current checkout and make story work resumable by recording the exact workspace and branch in `state.md`.

## Inputs

- `docs/specs/<ticket>/state.md`.
- `wiki/project-profile.md`.
- Current git repository state.

## Preconditions

- Story intake has created `state.md`.
- The repository has no unrelated uncommitted changes, or those changes are explicitly outside this story.

## Workflow

1. Read `state.md` and `wiki/project-profile.md`.
2. Detect repository state:
   - `git rev-parse --show-toplevel`
   - `git rev-parse --git-dir`
   - `git rev-parse --git-common-dir`
   - `git rev-parse --show-superproject-working-tree`
3. If already in a linked worktree and not a submodule, record it and continue.
4. If in a normal checkout, ask whether to create an isolated worktree unless the user already gave a preference.
5. If creating a project-local worktree:
   - prefer existing `.worktrees/`, then `worktrees/`
   - otherwise use `.worktrees/`
   - verify the chosen directory is ignored before creating it
6. Run baseline setup and validation commands from `wiki/project-profile.md` when available.
7. Update `state.md` with `workspace_path`, `workspace_isolated`, `working_root`, and `validation_commands`.

## Outputs

- Updated `state.md` with workspace path, isolation status, working root, and validation commands.
- Baseline validation status recorded in `state.md` when commands were run.

## Rules

- Never create a nested worktree inside an existing linked worktree.
- Treat git submodules as normal repositories, not worktrees.
- Do not create `.worktrees/` unless it is ignored or the user approves adding it to `.gitignore`.
- If baseline validation fails, record the failure in `state.md` and ask before continuing.
- Do not start coding from this skill.

## Handoff

When the workspace is ready, set the next status to:

- `clarifying` if requirements still need clarification
- `specifying` if the story is clear enough to specify
