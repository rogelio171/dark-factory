# {{TICKET-ID}} - {{Title}}

## Story Metadata

- Ticket: `{{TICKET-ID}}`
- Branch: `{{TICKET-ID}}-{{kebab-case-title}}`
- Status: `[ ] intake [ ] clarifying [ ] specifying [ ] implementing [ ] reviewing [ ] evidencing [ ] preflight [ ] shipping [ ] merging [ ] complete`
- Last updated: `YYYY-MM-DD`

## Problem Statement

Describe the problem from the story and business context.

## Acceptance Criteria

- Criterion 1
- Criterion 2
- Criterion 3

## Clarifications

- Clarification 1 captured
- Clarification 2 captured

## Relevant Wiki Context

- Page: `wiki/...`
- Why it matters:

## Implementation Approach

Describe the intended approach in enough detail for a new agent to continue safely.

## Risk Assessment

Set `risk` and `auto_merge_eligible` in `state.md` based on the planned diff.

- Risk level: `low | medium | high`
- Triggers used to decide:
  - [ ] Touches migrations or schema changes -> high
  - [ ] Touches infra (`infra/`, `terraform/`, `k8s/`, `helm/`) -> high
  - [ ] Touches CI configuration (`.github/workflows/`) -> high
  - [ ] Touches authentication, authorization, or secrets handling -> high
  - [ ] Changes a public API surface or wire format -> high
  - [ ] Touches a path with named CODEOWNERS -> medium
  - [ ] Touches cross-module shared code -> medium
  - [ ] None of the above -> low
- Auto-merge eligible: `true` only when `risk == low` and the test plan is green.
- Reviewers required beyond Copilot:

## Vertical Slices

### Slice 1 -

- Test to write first
- Minimum code change
- Validation step

### Slice 2 -

- Test to write first
- Minimum code change
- Validation step

## Testing Strategy

- Identify the first behavior to test
- Keep tests at the public-behavior level
- Prefer existing nearby test patterns

## Evidence Plan

Map each acceptance criterion to one of the supported evidence kinds (see `df-evidence/REFERENCE.md`):

- `ui` - Playwright screenshot under `evidence/ui/`
- `api` - request and response transcript under `evidence/api/`
- `cli` - terminal transcript under `evidence/cli/`
- `unit` - test report path under `evidence/unit/`
- `migration` - before/after schema dump under `evidence/migration/`

| Criterion | Evidence kind | Capture step |
| --- | --- | --- |
| Criterion 1 | ui | playwright snapshot of the toggle |
| Criterion 2 | api | curl recording for the new endpoint |

## Review Checklist

- Acceptance criteria mapped to implementation
- No unnecessary scope added
- TDD path is clear
- Evidence plan is clear
- Risk and auto-merge fields set in `state.md`

## Out of Scope

- Item 1

## Continuation Notes

- Current status:
- Next step:
- Open questions:
