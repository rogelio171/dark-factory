---
name: df-spec
description: Creates a durable story PRD in `docs/specs/` with implementation slices, test intent, evidence plan, and a risk classification used by `df-ship` to decide auto-merge eligibility. Use when a Jira story is clear enough to plan implementation or when a detailed `spec.md` is missing.
---

# DF Spec

## Goal

Write `docs/specs/<ticket-slug>/spec.md` and `docs/specs/<ticket-slug>/state.md` so another agent can continue the work without relying on chat history, and so `df-ship` can decide whether to arm auto-merge.

## Inputs

- The Jira ticket and any clarifications captured by `df-clarify`.
- Relevant `wiki/` pages (architecture, patterns, stack, entities).
- The repository's `.github/CODEOWNERS` if it exists.

## Preconditions

- `state.md` exists for the story (created by `df-story-intake`).
- The story is clear enough to plan (otherwise drop back to `df-clarify`).

## Workflow

1. Read the Jira story, clarification notes, and relevant wiki pages.
2. Sketch the planned diff at the path level (which directories and files will change).
3. Compute the risk level using the rules in "Risk Classification" below.
4. Create or update `spec.md` from `templates/spec-template.md`, filling the `Risk Assessment` and `Evidence Plan` sections.
5. Keep the original acceptance criteria visible and traceable.
6. Break the work into thin vertical slices with checkboxes.
7. Update `state.md` with the new fields:
   - `risk: low | medium | high`
   - `auto_merge_eligible: true | false`
   - reviewer requirements beyond Copilot
8. Record current progress and the next safe step.

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

## Handoff

When `spec.md` and `state.md` are complete, advance the story to `status: implementing` and invoke `df-implement`.

## Files

- Use `templates/spec-template.md`.
- Use `templates/state-template.md`.
