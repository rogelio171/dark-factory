# Dark Factory Workflow

## Purpose

Dark Factory is a repeatable agent workflow for taking a Jira story from intake to completion with durable documentation, TDD implementation, review, evidence, PR creation, automated PR babysitting, post-merge wiki updates, and resume support.

## Setup

1. Install the skill pack into a target project with `./install.sh /path/to/project`.
2. Make sure the target project has:
   - GitHub CLI authenticated
   - Atlassian Rovo MCP configured
   - Playwright MCP configured (if any acceptance criteria use UI evidence)
3. Run `df-github-init` once per target repository to scaffold the GitHub-side automation (Actions, CODEOWNERS, Copilot instructions, branch protection).
   - `pr-checks.yml` runs for pull requests without assuming `main` or `master`.
   - `pr-fix-loop.yml` is disabled until its agent runtime placeholder is replaced and `DF_MERGE_RUNTIME_CONFIGURED` is set to `true`.
4. Ask the agent to use `dark-factory`.

## Operating Model

The main agent is a coordinator. It routes phases, keeps `state.md` current, asks for user decisions, and synthesizes results into durable files. It should prefer subagents or agent teams for broad exploration, implementation research, review, evidence capture, preflight diagnosis, and PR babysitting so the main context stays small.

## Phase Flow

### 1. Wiki bootstrap

- If `wiki/` does not exist, `df-wiki-init` creates the Karpathy-style wiki.
- For existing codebases, it delegates broad exploration to subagents or agent teams, then summarizes architecture, stack, patterns, and entities.

### 2. Story intake

- `df-story-intake` fetches the Jira story.
- It creates the branch and the `docs/specs/<ticket>/` working area.

### 3. Clarification

- `df-clarify` decides whether the ticket is already clear enough.
- If not, it uses `df-grill-me` to ask one high-value question at a time.

### 4. Spec creation

- `df-spec` writes `spec.md` and `state.md`.
- The spec must include a risk classification (`low | medium | high`) and `auto_merge_eligible` flag.
- The spec should be detailed enough for another agent to resume without chat history.

### 5. Implementation

- `df-implement` follows red-green-refactor.
- Work is done in thin vertical slices with minimal code changes.
- The coordinator may delegate test discovery, pattern research, validation, or isolated slice work when the runtime supports agent teams.

### 6. Review loop

- `df-review` launches subagent or agent-team review passes.
- Blocking findings are fixed and re-reviewed until clean.

### 7. Evidence

- `df-evidence` validates acceptance criteria using the appropriate kind: `ui`, `api`, `cli`, `unit`, or `migration`.
- Evidence is stored in `docs/specs/<ticket>/evidence/<kind>/`.
- The coordinator may delegate evidence capture by criterion or evidence kind, then writes the final evidence index.

### 8. Preflight

- `df-preflight` mirrors CI locally before the PR is opened.
- It runs lint, typecheck, test, build, secret scan, dependency audit, and commit-message lint.
- Output is written to `docs/specs/<ticket>/preflight.json` and consumed by `df-ship`.
- Diagnostics for failed stages should be delegated when they require broad log or codebase analysis.

### 9. Ship

- `df-ship` opens the PR with the structured PR template body and inline evidence links.
- Applies `risk:<level>` label and, when eligible, `auto_merge_eligible` label.
- Requests a Copilot code review.
- When `risk: low` and `auto_merge_eligible: true`, runs `gh pr merge --auto --squash`.
- Generated PR automation also verifies both fields before arming auto-merge; the label alone is not sufficient.
- Posts the initial implementation summary to Jira.
- Sets `status: merging` and exits.

### 10. Merge

- `df-merge` watches required checks and the Copilot review.
- Auto-fixes eligible Copilot comments (lint, types, naming, missing tests, docstrings, dead code, suggested refactors with concrete code blocks).
- Escalates to a human when comments hit a CODEOWNERS path, are tagged security, conflict with `spec.md`, or expand scope.
- The coordinator may delegate thread classification and CI diagnostics, but it owns pushes, thread-resolution decisions, and escalation.
- After merge: invokes `df-wiki-update`, posts the final Jira summary with the merge SHA, and transitions the ticket to done.
- Sets `status: complete`.

### 11. Wiki update

- `df-wiki-update` runs after merge.
- Appends new patterns to `wiki/patterns/`, new entities to `wiki/entities/`, and a dated entry to `wiki/log.md`.
- Updates `wiki/index.md` if files were added.

### 12. Resume

- `df-resume` reads `state.md` and supporting artifacts to continue safely after interruptions, including resuming the merging phase from the recorded `pr_url`.

## Durable Artifacts

Each story should end up with:

- `docs/specs/<ticket>/spec.md`
- `docs/specs/<ticket>/state.md`
- `docs/specs/<ticket>/preflight.json`
- `docs/specs/<ticket>/reviews/`
- `docs/specs/<ticket>/evidence/{ui,api,cli,unit,migration}/`

The project should also maintain:

- `wiki/schema.md`
- `wiki/index.md`
- `wiki/log.md`
- `.github/workflows/{pr-checks,pr-open,pr-fix-loop}.yml`
- `.github/CODEOWNERS`
- `.github/copilot-instructions.md`

## Design Principles

- State on disk beats chat memory.
- Existing project patterns beat invention.
- TDD beats bulk implementation.
- Evidence beats claims.
- Small scoped changes beat over-engineering.
- Copilot review beats human review on low-risk paths; CODEOWNERS is a risk filter, not a default.
- Auto-merge is armed only when the spec says the change is low risk and the test plan is green.
- Coordinator context beats single-agent accumulation; use subagents or agent teams for context-heavy work.
