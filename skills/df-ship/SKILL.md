---
name: df-ship
description: Opens the GitHub pull request, applies the risk label, requests a Copilot code review, arms auto-merge when the spec marked the change auto-merge eligible, and posts the initial implementation summary back to Jira. Use when preflight is green and the story is ready for the PR. Does NOT wait for merge - that is `df-merge`'s job.
---

# DF Ship

## Goal

Open the PR with everything Copilot review and `df-merge` need to drive it to merge without human intervention on low-risk paths.

## Inputs

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/plan.md`
- `docs/specs/<ticket>/state.md` (must include `risk` and `auto_merge_eligible`)
- `docs/specs/<ticket>/preflight.json` (must have `summary: passed` or `summary: passed-with-warnings`)
- `docs/specs/<ticket>/evidence/INDEX.md`
- The `.github/pull_request_template.md` shape from `df-github-init`.

## Preconditions

- `state.md` is `status: preflight` (or `evidencing` if preflight was skipped explicitly by the user).
- `preflight.json` exists and is not `summary: failed`.
- The branch is pushed to origin.
- `gh auth status` is authenticated.
- `df-github-init` has been run on this repo at least once (the labels `risk:low|medium|high` and `auto_merge_eligible` exist; the `pr-open` workflow is in place).

## Workflow

1. Read `spec.md`, `plan.md`, `state.md`, `preflight.json`, and `evidence/INDEX.md`.
2. Preview the deterministic PR body with `df render-pr-body <TICKET-ID>` if the user asks to review it.
3. Run `df ship <TICKET-ID>` to push the branch, create or update the PR, apply risk labels, arm auto-merge when eligible, and write `pr_url`, `pr_number`, and `status: merging` back to `state.md`.
4. Request Copilot review (defensive; the `pr-open` workflow does this too). If the request fails because Copilot review is not enabled, warn clearly; do not hide the warning in logs:
   ```bash
   gh api -X POST "repos/${REPO}/pulls/${PR_NUMBER}/requested_reviewers" \
     -f reviewers='["copilot-pull-request-reviewer"]' || \
     echo "Copilot reviewer request failed; verify repo Settings -> Code review."
   ```
5. Post the initial Jira summary via Atlassian Rovo MCP, including the PR URL and a one-line evidence summary.

## Outputs

- A new PR on the target repo with the structured body, the `risk:<level>` label, and (when eligible) the `auto_merge_eligible` label.
- Auto-merge armed on eligible PRs.
- Initial Jira comment with the PR URL.
- Updated `state.md` with `pr_url`, `pr_number`, and `status: merging`.

## Rules

- Never open a PR without a green or warning-only preflight result.
- Never set `auto_merge_eligible` from this skill; trust what the spec wrote into `state.md`.
- Never close the Jira story from this skill - that is `df-merge`'s job after merge.
- Never run `gh pr merge --auto` on a PR with `risk: medium` or `risk: high`.
- Never rely on the `auto_merge_eligible` label alone. Auto-merge requires both `risk: low` and `auto_merge_eligible: true` in `state.md` and the PR body.
- Keep the PR title prefixed with the ticket ID (`OFRS2-12345: ...`).
- If `gh pr create` reports the PR already exists, switch to `gh pr edit` and update the body and labels in place.
- Keep module scope visible in the PR test plan.

## Handoff

When the PR is open and `state.md` is `status: merging`, invoke `df-merge`. `df-merge` is responsible for everything from PR open to PR merged, plus the post-merge Jira and wiki updates.
