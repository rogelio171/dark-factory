# DF Audit Reference

## Pre-Ship Checklist

Run before `df-ship` opens or updates the PR. Every item must pass.

1. **Spec/plan/review consistency**: `spec.md` acceptance criteria all map to checked-off tasks in `plan.md`, and the most recent `reviews/<n>.md` has no unresolved `critical` findings.
2. **Evidence completeness**: `docs/specs/<ticket>/evidence/INDEX.md` exists and has at least one evidence entry per acceptance criterion in `spec.md`.
3. **Preflight is current**: `preflight.json`'s `summary` is `passed` or `passed-with-warnings`, and its recorded commit range covers the branch's current HEAD (not a stale run from before the last fix).
4. **Risk fields are set, not defaulted**: `state.md` has a non-empty `risk` and an explicit `auto_merge_eligible` (`true` or `false`), and if `auto_merge_eligible: true`, `spec.md`'s Testing Strategy section names concrete tests for every acceptance criterion (per `df-spec`'s Risk Classification rules).
5. **Observability trail exists**: `df observability run-show "$RUN_ID"` returns at least one session for each phase already recorded in the Phase Checklist of `state.md`, and every session for a phase earlier than the current one has a non-null `ended_at`.
6. **No stale blocker**: `state.md` `status` is not `blocked` and `blocked_reason` is empty.

## Post-Merge Checklist

Run after `df-merge` records `merge_sha`, before `state.md` moves to `status: complete`.

1. **Merge is real**: `merge_sha` in `state.md` is non-empty and matches `gh pr view <pr_number> --json mergeCommit --jq .mergeCommit.oid`.
2. **Threads resolved**: every review thread `df-merge` addressed has both a reply and a resolved status; none were resolved without a reply (see `df-merge`'s Rules).
3. **Wiki update ran or is scheduled**: `df-wiki-update` has appended (or is about to append) a dated entry to `wiki/log.md` for this ticket.
4. **Jira closed**: the ticket's Jira status reflects done, and the final summary comment includes `merge_sha`.
5. **Observability trail is closed**: `df observability run-show "$RUN_ID"` shows every session with a non-null `ended_at`, and the run itself is ready for `df observability run end --run-id "$RUN_ID" --status complete`.
6. **Risk-model feedback, if applicable**: if this story is a hotfix or revert for a prior auto-merged story (per `df-story-intake`), a `risk.revert` event has been recorded via `df observability event record --category risk.revert` referencing the original ticket, per the convention in `df-retro`.

## Recording a Failed Item

When an item fails, the audit note (`docs/specs/<ticket>/audit/<mode>-<n>.md`) records:

```markdown
# Audit: <pre-ship|post-merge> pass <n>

- Item: <checklist item number and name>
- Status: fail
- Evidence: <file path or command output proving the gap>
- Routed to: <skill that owns the fix, or "blocked: <reason>">
```

Re-run the full checklist after the routed fix returns control to `df-audit`; do not assume the rest of the checklist still passes without re-checking.
