---
name: df-ship
description: Opens the GitHub pull request, applies the risk label, requests a Copilot code review, arms auto-merge when the spec marked the change auto-merge eligible, and posts the initial implementation summary back to Jira. Use when preflight is green and the story is ready for the PR. Does NOT wait for merge - that is `df-merge`'s job.
---

# DF Ship

## Goal

Open the PR with everything Copilot review and `df-merge` need to drive it to merge without human intervention on low-risk paths.

## Inputs

- `docs/specs/<ticket>/spec.md`
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

1. Read `spec.md`, `state.md`, `preflight.json`, and `evidence/INDEX.md`.
2. Push the current branch if it is ahead of origin: `git push -u origin HEAD`.
3. Build the PR body from `.github/pull_request_template.md`, filling:
   - `## Summary` from the spec's Problem Statement and Implementation Approach.
   - `## Test plan` from the spec's Testing Strategy and `preflight.json` results.
   - `## Evidence` with links to each file in `evidence/INDEX.md`.
   - `## Risk` with the `risk` and `auto_merge_eligible` values from `state.md`.
   - `## Related` with the Jira URL and spec/state paths.
4. Open the PR:
   ```bash
   gh pr create --title "<TICKET-ID>: <title>" --body-file <(printf '%s\n' "$body")
   ```
5. Capture the PR URL and number from the command output.
6. Apply labels:
   ```bash
   gh pr edit "$PR_NUMBER" --add-label "risk:$risk"
   if [ "$auto_merge_eligible" = "true" ]; then
     gh pr edit "$PR_NUMBER" --add-label "auto_merge_eligible"
   fi
   ```
7. Request Copilot review (defensive; the `pr-open` workflow does this too). If the request fails because Copilot review is not enabled, warn clearly; do not hide the warning in logs:
   ```bash
   gh api -X POST "repos/${REPO}/pulls/${PR_NUMBER}/requested_reviewers" \
     -f reviewers='["copilot-pull-request-reviewer"]' || \
     echo "Copilot reviewer request failed; verify repo Settings -> Code review."
   ```
8. Arm auto-merge only when `risk: low` AND `auto_merge_eligible: true`:
   ```bash
   if [ "$risk" = "low" ] && [ "$auto_merge_eligible" = "true" ]; then
     gh pr merge "$PR_NUMBER" --auto --squash
   fi
   ```
9. Post the initial Jira summary via Atlassian Rovo MCP, including the PR URL and a one-line evidence summary.
10. Update `state.md`:
    - `status: merging`
    - `pr_url`, `pr_number`
    - `phase_detail: "PR open, awaiting Copilot review and CI"`

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

## Handoff

When the PR is open and `state.md` is `status: merging`, invoke `df-merge`. `df-merge` is responsible for everything from PR open to PR merged, plus the post-merge Jira and wiki updates.
