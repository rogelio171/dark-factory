---
name: df-github-init
description: Scaffolds the GitHub-side automation in the target repository (Actions for PR checks, PR-open, and PR-fix-loop, plus CODEOWNERS as a risk filter, a structured PR template, and Copilot instructions derived from the wiki) so Copilot review and auto-merge can replace human review on low-risk PRs. Use when setting up a target repository for Dark Factory automation or refreshing the PR automation.
---

# DF GitHub Init

## Goal

Stand up the GitHub-side automation that lets `df-ship` arm auto-merge and `df-merge` close PRs without human approval on low-risk paths.

## Inputs

- The target repository (must be a GitHub repo, `gh` authenticated).
- The project `wiki/` (used to seed `.github/copilot-instructions.md`).
- `wiki/project-profile.md` (used to scope PR checks to modules).
- The default branch name (from `gh repo view --json defaultBranchRef`).

## Preconditions

- `gh auth status` reports an authenticated user with admin permissions on the target repo (needed for branch protection).
- `wiki/` exists. If it does not, drop back to `df-wiki-init` first.

## Workflow

1. Detect the default branch and the repository slug.
2. Copy template files from `templates/` into the target repo, preserving paths:
   - `.github/workflows/pr-checks.yml`
   - `.github/workflows/pr-open.yml`
   - `.github/workflows/pr-fix-loop.yml`
   - `.github/CODEOWNERS`
   - `.github/pull_request_template.md`
3. Review `wiki/project-profile.md` and replace the placeholder module matrix in `pr-checks.yml` with explicit module commands before enabling branch protection.
4. Generate `.github/copilot-instructions.md` from the wiki:
   - Pull conventions from `wiki/patterns/`, stack notes from `wiki/stack/`, and architecture summaries from `wiki/architecture/`.
   - Use `templates/copilot-instructions.md` as the skeleton and fill the project-specific sections.
5. If the repo does not already have the labels `risk:low`, `risk:medium`, `risk:high`, `auto_merge_eligible`, create them with `gh label create`.
6. Print (do not silently run) the branch-protection command from "Branch protection" below and ask the user to confirm.
7. After the user confirms, run the command and report the result.
8. Open `.github/workflows/pr-fix-loop.yml` and instruct the user to fill the `AGENT RUNTIME PLACEHOLDER` step with their chosen runtime (Cursor CLI, Cursor Cloud, Claude Code Action, etc. - examples are commented in the file), then set `DF_MERGE_RUNTIME_CONFIGURED: "true"`. Until then, the workflow exits successfully without running fixes.
9. Commit the changes on a branch named `chore/df-github-init` and open a PR titled "chore: scaffold Dark Factory GitHub automation".

## Branch protection

Print and confirm before running:

```bash
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"
gh api -X PUT "repos/{owner}/{repo}/branches/${DEFAULT_BRANCH}/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "typecheck", "test", "build", "security"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "required_conversation_resolution": true,
  "allow_auto_merge": true,
  "restrictions": null
}
JSON
```

`require_code_owner_reviews: true` is what makes CODEOWNERS act as a risk filter: paths without an owner are satisfied by Copilot's review alone; paths with an owner require that owner.

## Outputs

- `.github/workflows/pr-checks.yml`, `.github/workflows/pr-open.yml`, `.github/workflows/pr-fix-loop.yml` in the target repo.
- `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.github/copilot-instructions.md`.
- Repo labels: `risk:low`, `risk:medium`, `risk:high`, `auto_merge_eligible`.
- Branch protection on the default branch matching the spec above.
- A PR titled "chore: scaffold Dark Factory GitHub automation" merging the scaffolding into the default branch.

## Rules

- Never overwrite an existing `.github/workflows/*.yml` without showing the diff and asking. Always create a backup `*.yml.bak` if the user accepts the overwrite.
- Never run the branch-protection command without explicit confirmation.
- Never set `enforce_admins: true`; that locks out the user who runs this skill.
- Never assume Copilot review is enabled on the repo. If it is not, instruct the user to enable it under repo Settings -> Code review.
- Do not commit secrets. The fix-loop workflow expects a `CURSOR_API_KEY` (or analogous) secret; only document the requirement, do not fabricate values.
- Keep `pr-open.yml` fail-closed: auto-merge may only be armed when the PR body records `risk: low` and `auto_merge_eligible: true`.
- Keep `pr-checks.yml` free of hard-coded default-branch names; branch protection targets the detected default branch, while PR checks run for pull requests regardless of whether the branch is named `main`, `master`, or something else.
- Do not generate broad root-probing CI for monorepos. Prefer explicit module commands from `wiki/project-profile.md`.
- Leave placeholder commands visible if the project profile is incomplete; ask the user to fill them before enabling branch protection.

## Handoff

When the scaffolding PR merges and the user confirms Copilot review is enabled in repo settings, the GitHub side is ready. `df-ship` and `df-merge` can then operate end-to-end.

## Files

- Templates live in [templates/](templates/).
- Branch-protection command shape lives in this file under "Branch protection".
