---
name: df-review
description: Runs a subagent-based code review loop against the current story spec, fixing blocking findings until the implementation is clean enough to move to evidence collection. Use when implementation is complete enough for review or the user wants a spec-aware review pass.
---

# DF Review

## Goal

Find and fix issues before evidence collection and PR creation.

## Inputs

- `docs/specs/<ticket>/spec.md` (acceptance criteria, vertical slices, testing strategy).
- `docs/specs/<ticket>/plan.md`.
- `docs/specs/<ticket>/state.md`.
- `wiki/project-profile.md`.
- The current branch diff vs. the merge base.

## Preconditions

- `state.md` is `status: reviewing`.
- All slices in `spec.md` are checked off and tests are green.

## Workflow

1. Read `spec.md`, `plan.md`, `wiki/project-profile.md`, deterministic state fields via `df state get`, and the current diff.
2. Launch a spec compliance reviewer with the spec, plan, module scope, diff, and acceptance criteria.
3. Launch a code quality reviewer only after spec compliance is clean.
4. Categorize findings:
   - critical: must fix now
   - suggestion: should improve if low risk
   - optional: nice to have
5. Save the categorized findings under `docs/specs/<ticket>/reviews/<n>.md`.
6. Fix the critical findings.
7. Re-run scoped tests and relevant checks.
8. Launch fresh review subagents.
9. Repeat until no critical findings remain.
10. Record the clean pass with `df state set <TICKET-ID> phase_detail "review clean"` before advancing.

## Delegation Model

The main agent is the review coordinator. It should not be the only reviewer for non-trivial diffs.

- Launch at least one subagent review pass for every review phase; use parallel specialist reviewers when the diff spans multiple domains.
- Ask reviewers to return findings categorized as critical, suggestion, or optional, with file paths and acceptance-criteria impact.
- The coordinator deduplicates findings, decides which fixes are in scope, records review notes, and routes scoped fixes.
- After fixes, launch a fresh review subagent instead of relying on the same main-context judgment.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-review --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- One review note per pass under `docs/specs/<ticket>/reviews/`.
- Code fixes for every critical finding.
- Updated `state.md` with the pass count and outstanding suggestions.

## Rules

- Review against the spec, not just code style.
- Keep spec compliance, code quality, test adequacy, and module-boundary safety as separate review concerns.
- Save findings under `docs/specs/<ticket>/reviews/`.
- Do not ignore failing tests while closing review issues.
- If a requested fix would expand scope, run `df state block <TICKET-ID> --reason "review finding requires scope expansion: <summary>"` and stop to ask the user; `df state unblock <TICKET-ID>` resumes the review loop once the user decides.
- Do not collapse multiple critical findings into one fix commit; keep changes scoped.
- Prefer subagents or agent teams for review passes; the coordinator owns categorization, scope control, and state updates.

## Handoff

When the review loop is clean (no critical findings, optional findings noted), advance `state.md` to `status: evidencing` and invoke `df-evidence`.

## Files

- Spec reviewer prompt: `prompts/spec-reviewer.md`.
- Code quality reviewer prompt: `prompts/code-quality-reviewer.md`.
