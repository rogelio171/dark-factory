# Dark Factory Workflow

## Purpose

Dark Factory is a repeatable agent workflow for taking a Jira story from intake to completion with durable documentation, TDD implementation, review, evidence, PR creation, Jira updates, and resume support.

## Setup

1. Install the skill pack into a target project with `./install.sh /path/to/project`.
2. Make sure the target project has:
   - GitHub CLI authenticated
   - Atlassian Rovo MCP configured
   - Playwright MCP configured
3. Ask the agent to use `dark-factory`.

## Phase Flow

### 1. Wiki bootstrap

- If `wiki/` does not exist, `df-wiki-init` creates the Karpathy-style wiki.
- For existing codebases, it summarizes architecture, stack, patterns, and entities.

### 2. Story intake

- `df-story-intake` fetches the Jira story.
- It creates the branch and the `docs/specs/<ticket>/` working area.

### 3. Clarification

- `df-clarify` decides whether the ticket is already clear enough.
- If not, it uses `df-grill-me` to ask one high-value question at a time.

### 4. Spec creation

- `df-spec` writes `spec.md` and `state.md`.
- The spec should be detailed enough for another agent to resume without chat history.

### 5. Implementation

- `df-implement` follows red-green-refactor.
- Work is done in thin vertical slices with minimal code changes.

### 6. Review loop

- `df-review` launches subagent review passes.
- Blocking findings are fixed and re-reviewed until clean.

### 7. Evidence

- `df-evidence` validates acceptance criteria with Playwright MCP.
- Evidence is stored in `docs/specs/<ticket>/evidence/`.

### 8. Ship

- `df-ship` creates or updates the PR.
- It posts the implementation summary and evidence back to Jira.
- It updates final docs and closes the story when appropriate.

### 9. Resume

- `df-resume` reads `state.md` and supporting artifacts to continue safely after interruptions.

## Durable Artifacts

Each story should end up with:

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/state.md`
- `docs/specs/<ticket>/reviews/`
- `docs/specs/<ticket>/evidence/`

The project should also maintain:

- `wiki/schema.md`
- `wiki/index.md`
- `wiki/log.md`

## Design Principles

- State on disk beats chat memory.
- Existing project patterns beat invention.
- TDD beats bulk implementation.
- Evidence beats claims.
- Small scoped changes beat over-engineering.
