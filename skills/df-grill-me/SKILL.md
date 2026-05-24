---
name: df-grill-me
description: Interviews the user one question at a time to resolve ambiguity in a plan, design, architecture, or requirement set, while proposing a recommended answer drawn from codebase and wiki context. Use when a plan is unclear, a ticket is underspecified, or the user asks to be grilled on an idea.
---

# DF Grill Me

## Goal

Drive ambiguous work toward shared understanding before implementation starts, without overasking.

## Inputs

- The current artifact under discussion (ticket, design doc, plan, code review).
- `wiki/` for project context.
- The current `docs/specs/<ticket>/state.md` if a story is active.

## Preconditions

- The caller has identified that ambiguity exists and is blocking forward progress.

## Workflow

1. Read the available context first: code, docs, wiki, ticket text, or prior decisions.
2. Identify the next most important unresolved question.
3. Ask exactly that one question, including a recommended answer with brief reasoning.
4. Wait for the user's answer.
5. Record the resolved decision where the calling skill expects it (typically `state.md` "Decisions" or the design doc); when a story is active, also update the short resume summary with `df state set <TICKET-ID> phase_detail "<decision summary>"`.
6. Loop until the remaining uncertainty is small enough for the caller to act safely.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-grill-me --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- Resolved decisions written to the location the caller named.
- A clear stop signal when the remaining ambiguity is acceptable.

## Rules

- Ask one question at a time.
- If the codebase or wiki can answer the question, answer it there instead of asking the user.
- Skip branches that are already clear.
- Never bundle multiple questions into a single prompt.
- Always include a recommended answer; never ask an open-ended "what should we do?" without a default.

## Handoff

Return control to the calling skill (commonly `df-clarify`) once the user signals they are satisfied with the resolved set of decisions.

## Good Targets

- underspecified acceptance criteria
- missing edge-case behavior
- unclear ownership between systems
- ambiguous UX, testing, or rollout expectations
