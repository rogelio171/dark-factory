# Dark Factory

Dark Factory is a portable skill pack for running an agent-driven delivery workflow from Jira story intake through implementation, review, evidence collection, pull request creation, Jira updates, and final completion.

It is designed for long-running work that may span multiple sessions. Instead of relying on chat memory, Dark Factory keeps progress on disk through a project wiki and per-story state files so another agent can resume work safely.

## What This Project Solves

Most agent workflows are good at one part of the delivery loop and weak at the rest. Dark Factory is meant to make the full path repeatable:

1. Pull a story from Jira.
2. Understand the codebase and project conventions.
3. Clarify ambiguous requirements.
4. Create a durable PRD and execution record.
5. Implement with TDD in small vertical slices.
6. Review changes in a fix-and-re-review loop.
7. Validate the feature and capture evidence.
8. Create the PR and update Jira with a useful summary.
9. Resume safely if the session is interrupted.

## Core Ideas

### 1. Durable state beats chat memory

Each story gets a working directory under `docs/specs/` with a `spec.md`, `state.md`, `reviews/`, and `evidence/`. This lets a later session continue from disk instead of guessing from chat history.

### 2. The wiki is a persistent project knowledge layer

Dark Factory uses a Karpathy-style wiki under `wiki/` to store architecture, stack, patterns, and domain entities. The goal is to accumulate project knowledge instead of rediscovering it every time.

### 3. TDD and vertical slices keep changes small

The implementation workflow is intentionally conservative: one test, one behavior, one minimum code change, then repeat.

## Included Skills

- `dark-factory`: entry point and workflow orchestrator
- `df-wiki-init`: bootstrap or refresh the project wiki
- `df-story-intake`: retrieve a Jira story and initialize local story state
- `df-grill-me`: reusable one-question-at-a-time interview skill
- `df-clarify`: story-specific clarification using ticket and wiki context
- `df-spec`: create the durable PRD and state files
- `df-implement`: implement through a strict red-green-refactor loop
- `df-review`: run a spec-aware review/fix/re-review loop
- `df-evidence`: collect screenshots and evidence with Playwright MCP
- `df-ship`: create the PR, update Jira, and finish the workflow
- `df-resume`: resume interrupted work from `state.md`

## Repository Layout

```text
dark-factory/
├── README.md
├── install.sh
├── docs/
│   └── WORKFLOW.md
└── skills/
    ├── dark-factory/
    ├── df-wiki-init/
    ├── df-story-intake/
    ├── df-grill-me/
    ├── df-clarify/
    ├── df-spec/
    ├── df-implement/
    ├── df-review/
    ├── df-evidence/
    ├── df-ship/
    └── df-resume/
```

## Prerequisites

Dark Factory is a skill pack, so it is meant to be installed into another project repository where the actual feature work will happen.

Before using it in a target project, make sure the following are available:

- GitHub CLI authenticated for PR creation and PR checks
- Atlassian Rovo MCP configured for Jira access
- Playwright MCP configured for browser-based validation and screenshots
- A coding agent that discovers skills from `.agents/skills/`

## Installation

Install the skill pack into a target project:

```bash
./install.sh /path/to/target-project
```

If no path is provided, the current directory is used as the target.

The installer copies each skill directory into:

```text
.agents/skills/
```

inside the target project.

### Example

```bash
cd /path/to/dark-factory
./install.sh ~/dev/my-app
```

This will create:

```text
~/dev/my-app/.agents/skills/dark-factory
~/dev/my-app/.agents/skills/df-wiki-init
~/dev/my-app/.agents/skills/df-story-intake
...
```

## What Gets Created in the Target Project

When Dark Factory runs inside a target project, it creates two kinds of artifacts.

### 1. Project wiki

```text
wiki/
├── schema.md
├── index.md
├── log.md
├── architecture/
├── patterns/
├── stack/
└── entities/
```

This is the long-lived project knowledge base.

### 2. Story work area

```text
docs/specs/<ticket-slug>/
├── spec.md
├── state.md
├── reviews/
└── evidence/
```

This is the durable record for a single story.

## How To Use Dark Factory

After installing the skills into the target repository, open that repository in your agent and invoke the workflow through the `dark-factory` skill.

### Typical entry prompts

Use prompts like:

```text
Use dark-factory on Jira story OFRS2-12345.
```

```text
Start Dark Factory for OFRS2-12345.
```

```text
Resume Dark Factory for the current in-progress story.
```

### What the orchestrator does

The `dark-factory` skill decides what phase to run next:

- If `wiki/` is missing, it starts with `df-wiki-init`.
- If the story has not been initialized, it uses `df-story-intake`.
- If requirements are unclear, it uses `df-clarify`.
- If `spec.md` is missing or incomplete, it uses `df-spec`.
- If the story is ready to build, it uses `df-implement`.
- If implementation needs review, it uses `df-review`.
- If review is clean, it uses `df-evidence`.
- If the feature is validated, it uses `df-ship`.
- If work was interrupted, it uses `df-resume`.

## End-to-End Workflow

### 1. Wiki bootstrap

`df-wiki-init` creates or refreshes the project wiki.

- For a new project, it creates the basic wiki structure.
- For an existing codebase, it summarizes architecture, patterns, stack, testing style, and domain entities.

### 2. Story intake

`df-story-intake`:

- reads the Jira ticket via Atlassian Rovo MCP
- extracts title, description, and acceptance criteria
- creates the working branch
- creates the story directory under `docs/specs/`

### 3. Clarification

`df-clarify` determines whether the ticket is already safe to implement.

- If the story is clear, it moves directly to spec creation.
- If the story is ambiguous, it uses `df-grill-me` to ask one useful question at a time.

### 4. Spec creation

`df-spec` creates:

- `spec.md`: the durable PRD and implementation record
- `state.md`: the current phase, next step, and resume state

The goal is for another agent to continue the work with no hidden chat context.

### 5. Implementation

`df-implement` follows the red-green-refactor loop:

1. choose one thin vertical slice
2. write one failing test
3. make the smallest code change to pass
4. validate and record progress
5. repeat

### 6. Review loop

`df-review` launches a review pass against the current story spec and acceptance criteria.

- Critical issues are fixed immediately.
- Then a new review pass is run.
- The loop continues until there are no blocking findings left.

### 7. Evidence collection

`df-evidence` validates the finished feature through Playwright MCP and stores screenshots in `docs/specs/<ticket>/evidence/`.

### 8. Shipping

`df-ship`:

- creates or updates the GitHub PR
- summarizes the changes and test results
- posts the summary and evidence back to Jira
- updates final documentation if needed
- transitions the story when appropriate

### 9. Resume

`df-resume` reads the on-disk state and supporting artifacts to continue safely after an interruption.

## Day-To-Day Usage Patterns

### Start a new story

```text
Use dark-factory for Jira ticket OFRS2-12345.
```

### Resume interrupted work

```text
Use df-resume and continue the current story.
```

### Force wiki generation first

```text
Use df-wiki-init to create the project wiki before starting story work.
```

### Clarify before planning

```text
Use df-clarify on OFRS2-12345 before creating the spec.
```

### Stress-test a design directly

```text
Use df-grill-me on this implementation approach.
```

## Updating the Skill Pack in a Target Project

If you make changes to this repository and want to refresh the installed copy in a target project, run the installer again:

```bash
./install.sh /path/to/target-project
```

The installer replaces the existing skill directories in `.agents/skills/`.

## Troubleshooting

### Jira access is not working

Check that Atlassian Rovo MCP is configured and available to the agent. Dark Factory expects Jira access through MCP rather than through ad hoc shell scripts.

### Browser validation is not working

Check that Playwright MCP is available and that the target project can actually run locally.

### The workflow was interrupted

Use `df-resume`. The intended source of truth is `docs/specs/<ticket>/state.md`, not the previous chat thread.

### The wiki is stale

Run `df-wiki-init` again in the target project to refresh the project knowledge base.

## Additional Documentation

- For the concise lifecycle summary, see `docs/WORKFLOW.md`.
- For the exact instructions each phase uses, read the `SKILL.md` files under `skills/`.
