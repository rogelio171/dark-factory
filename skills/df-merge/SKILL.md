---
name: df-merge
description: Babysits an open Dark Factory PR through Copilot review and CI by auto-fixing eligible review comments, watching required checks, resolving threads it has addressed, and on merge running `df-wiki-update`, posting the final Jira summary, and transitioning the ticket to done. Use when `df-ship` has set `status: merging` or when the user asks to babysit a specific PR.
---

# DF Merge

## Goal

Take a PR from "open" to "merged + Jira done + wiki updated" without human intervention on auto-fix-eligible feedback, and stop fast on anything that is not.

## Inputs

- `docs/specs/<ticket>/spec.md` (used to detect spec-conflicting review comments).
- `docs/specs/<ticket>/state.md` (must include `pr_url` and `pr_number`).
- `gh pr view <pr_number> --json state,mergeable,reviews,statusCheckRollup,labels,comments`.
- The repo's `.github/CODEOWNERS` (used to detect escalate paths).

## Preconditions

- `state.md` is `status: merging` and has `pr_url` and `pr_number` populated.
- `gh auth status` is authenticated.
- The branch from the PR is locally checkoutable (`gh pr checkout <pr_number>`).

## Workflow

1. Check out the PR head: `gh pr checkout "$PR_NUMBER"`.
2. Loop until terminal:
   1. Fetch PR status with `df pr poll "$PR_NUMBER"`.
   2. If `state == "MERGED"`: break to step 3 (post-merge).
   3. If `state == "CLOSED"`: stop, set `status: blocked` with reason "PR closed without merge".
   4. If any required check failed: run `df pr fix-checks "$PR_NUMBER"` to fetch failing logs, apply a scoped fix per the matrix in [REFERENCE.md](REFERENCE.md), `git push`, then loop.
   5. If Copilot (or another reviewer) submitted `changes_requested`:
      - For each unresolved review comment, classify using the matrix in [REFERENCE.md](REFERENCE.md).
      - For auto-fix-eligible comments: apply the fix, push, reply with `df pr reply-thread`, then resolve with `df pr resolve-thread`.
      - For escalate comments: post a reply explaining the escalation, set `status: blocked` in `state.md` with the comment ID, and exit.
   6. If checks are green and review is approved and no auto-merge is set, run `gh pr merge "$PR_NUMBER" --squash` only when `risk: low` and `auto_merge_eligible: true`; otherwise leave the merge button for a human.
   7. If nothing changed since the last poll, sleep with backoff (30s, 60s, 120s, capped at 300s).
3. Post-merge:
   1. Capture the merge SHA: `gh pr view "$PR_NUMBER" --json mergeCommit --jq .mergeCommit.oid`.
   2. Write `merge_sha` into `state.md`.
   3. Post the final Jira summary via Atlassian Rovo MCP, including merge SHA and a recap of what changed.
   4. Transition the Jira ticket to its done state.
   5. Invoke `df-wiki-update`.
   6. Set `state.md` to `status: complete`.

## Delegation Model

The main agent coordinates the PR babysitting loop and owns escalation decisions. Prefer subagents or agent teams for focused review-thread classification, CI failure diagnosis, and fix recommendations.

- Use a specialist subagent to classify unresolved review threads against [REFERENCE.md](REFERENCE.md) and the story spec.
- Use a diagnostic subagent for failing CI logs; it should return the minimal fix path or an escalation reason.
- If the runtime supports write-capable agent teams, delegate one scoped fix at a time and have the coordinator verify the diff before pushing.
- The coordinator re-fetches PR status after every push, updates `state.md`, replies to threads, and decides when to stop or escalate.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-merge --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- A merged PR.
- All addressed review threads resolved with replies.
- `state.md` advanced to `status: complete` with `merge_sha`.
- Final Jira comment with the merge SHA.
- Wiki updates appended via `df-wiki-update`.

## Rules

- Never amend commits that have been pushed.
- Never push to a branch that is not the PR's head branch.
- Never resolve a review thread you did not address.
- Never close the PR. If forward progress is impossible, set `status: blocked` and stop.
- Never auto-merge a PR that is `risk: medium`, `risk: high`, or missing `auto_merge_eligible: true`. Wait for the required human reviewer.
- Always reply on a thread before resolving it; the reply explains what was done.
- Always re-fetch PR status after pushing fixes; never rely on the previous poll.
- When in doubt about whether a comment is auto-fix-eligible, escalate.
- Prefer subagents or agent teams for classification and diagnostics; the coordinator owns pushes, thread resolution decisions, and state.

## Handoff

On `status: complete`: return to the `dark-factory` orchestrator. On `status: blocked`: stop and surface the comment that caused the escalation.

## Files

- For the auto-fix eligibility matrix, the GitHub GraphQL calls used to resolve threads, and the per-CI-failure fix recipes, see [REFERENCE.md](REFERENCE.md).
