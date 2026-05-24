---
name: df-spec
description: Creates a durable story PRD in `docs/specs/` with module scope, implementation slices, test intent, evidence plan, and a risk classification used by `df-ship` to decide auto-merge eligibility. Use when a Jira story is clear enough to plan implementation or when a detailed `spec.md` is missing.
---

# DF Spec

## Goal

Write `docs/specs/<ticket-slug>/spec.md` and `docs/specs/<ticket-slug>/state.md` so another agent can continue the work without relying on chat history, and so `df-ship` can decide whether to arm auto-merge.

## Inputs

- The Jira ticket and any clarifications captured by `df-clarify`.
- Relevant `wiki/` pages (architecture, patterns, stack, entities).
- `wiki/project-profile.md` for module boundaries and validation commands.
- The repository's `.github/CODEOWNERS` if it exists.

## Preconditions

- `state.md` exists for the story (created by `df-story-intake`).
- The story is clear enough to plan (otherwise drop back to `df-clarify`).

## Workflow

1. Read the Jira story, clarification notes, and relevant wiki pages.
2. Read `wiki/project-profile.md` and copy the selected module scope into `state.md`.
3. Sketch the planned diff at the path level (which directories and files will change).
4. Run `df classify-risk --diff-base origin/<default-branch>` when a branch diff exists; otherwise apply the same risk matrix below to the planned path sketch.
5. Create or update `spec.md` from `templates/spec-template.md`, filling the `Module Scope`, `Risk Assessment`, and `Evidence Plan` sections.
6. Keep the original acceptance criteria visible and traceable.
7. Break the work into thin vertical slices with checkboxes.
8. Update `state.md` using `df state set` for the new fields: `risk`, `auto_merge_eligible`, `target_modules`, `validation_commands`, and reviewer requirements beyond Copilot.
9. Record current progress and the next safe step.

## Risk Classification

Set `risk: high` if the planned diff touches any of:

- database migrations or schema files (`migrations/`, `*.sql`, schema definitions)
- infrastructure (`infra/`, `terraform/`, `k8s/`, `helm/`, `Dockerfile`, `docker-compose.yml`)
- CI configuration (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`)
- authentication, authorization, secrets, or cryptography paths (`auth/`, `security/`, `crypto/`, anywhere named after a secret manager)
- public API surfaces or wire formats (OpenAPI, protobuf, GraphQL schemas, public TypeScript types, exported library entry points)
- billing, payments, or PII handling

Set `risk: medium` if not high but any of:

- the planned diff touches a path with a named owner in `.github/CODEOWNERS`
- the change crosses module boundaries that other teams depend on
- the change introduces a new external dependency

Set `risk: low` otherwise.

Set `auto_merge_eligible: true` only when both:

- `risk: low`
- The Testing Strategy section names concrete tests that will cover every acceptance criterion.

When `risk` is `medium` or `high`, list the human reviewers required beyond Copilot in `state.md` under "Risk".


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-spec --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- `docs/specs/<ticket-slug>/spec.md` populated from the template.
- `docs/specs/<ticket-slug>/state.md` with `status: specifying`, `risk`, `auto_merge_eligible`, and reviewer notes set.

## Rules

- Write for continuation, not just planning.
- Keep implementation decisions concrete but not over-engineered.
- Include testing intent before implementation starts.
- Prefer tracer bullets over big-bang plans.
- Mark the story phase as `specifying` while this skill is active.
- Never mark `auto_merge_eligible: true` without a green Testing Strategy section.
- If the planned diff is unknown (the story is exploratory), set `risk: medium` by default and document why in the spec.
- Do not leave `target_modules` or `validation_commands` blank unless the user confirms the whole repo is the target.

## Handoff

When `spec.md` and `state.md` are complete, advance the story to `status: planning` and invoke `df-plan`.

## Files

- Use `templates/spec-template.md`.
- Use `templates/state-template.md`.
