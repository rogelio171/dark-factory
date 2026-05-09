---
name: df-resume
description: Resumes interrupted Dark Factory work by reading story state, specs, review notes, evidence folders, and any open PR, to determine the next safe phase. Use when a session ended early, work was partially completed, or the user asks to continue an existing story.
---

# DF Resume

## Goal

Recover the current story state from disk (and from GitHub when a PR is already open) instead of relying on chat memory.

## Inputs

- `docs/specs/*/state.md` for every active story.
- `spec.md`, `plan.md`, `reviews/`, `evidence/`, and `preflight.json` for the chosen story.
- `wiki/project-profile.md`.
- `gh pr view <pr_number>` if `state.md` records an open PR.

## Preconditions

- The repository is checked out and the branch is on the recorded ticket branch (or can be switched to it).

## Workflow

1. Find active stories under `docs/specs/`.
2. Read each `state.md`.
3. Identify the most recent in-progress story or ask the user which one to resume.
4. Read the supporting artifacts for that story:
   - `spec.md`
   - `plan.md`
   - `reviews/`
   - `evidence/INDEX.md`
   - `preflight.json`
5. If `state.md` records a `pr_url`, fetch `gh pr view <pr_number> --json state,mergeable,reviews,statusCheckRollup` and reconcile with the file's recorded status.
6. Confirm the repository state matches the recorded phase (current branch, checked-in files).
7. Update `last_updated` in `state.md` to the current timestamp.
8. Dispatch to the correct next skill based on `status`.

## Outputs

- Updated `state.md` with the new `last_updated` timestamp and any reconciled PR status.
- A clear next step printed to the user before invoking the next skill.

## Rules

- Treat `state.md` as the primary resume source.
- If the repo state and `state.md` disagree, stop and reconcile first.
- If module scope in `state.md` no longer matches `wiki/project-profile.md`, refresh the profile before continuing.
- If GitHub says the PR has merged but `state.md` is still `merging`, run `df-wiki-update` and advance to `complete` rather than re-running `df-merge`.
- Prefer the safest next action over the fastest one.

## Handoff

Resume into the phase named in `state.md`:

- `intake` -> `df-story-intake`
- `workspace` -> `df-workspace`
- `clarifying` -> `df-clarify`
- `specifying` -> `df-spec`
- `planning` -> `df-plan`
- `implementing` -> `df-implement`
- `reviewing` -> `df-review`
- `evidencing` -> `df-evidence`
- `preflight` -> `df-preflight`
- `shipping` -> `df-ship`
- `merging` -> `df-merge`
- `complete` -> stop and report the merge SHA.
