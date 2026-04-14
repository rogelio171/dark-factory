# Dark Factory

Dark Factory is a portable skill pack for agent-driven delivery from Jira ticket intake through PR, evidence collection, Jira update, and completion.

## What It Includes

- `dark-factory`: orchestrator for the full workflow
- `df-wiki-init`: Karpathy-style wiki bootstrap for new or existing codebases
- `df-story-intake`: Jira story retrieval and branch initialization
- `df-grill-me`: reusable one-question-at-a-time interview skill
- `df-clarify`: story-specific clarification wrapper
- `df-spec`: durable PRD and state templates
- `df-implement`: TDD implementation loop
- `df-review`: review and fix loop
- `df-evidence`: Playwright-based evidence collection
- `df-ship`: PR creation, Jira summary, and completion flow
- `df-resume`: resume interrupted work from disk

## Install

```bash
./install.sh /path/to/target-project
```

If no path is provided, the current directory is used as the target.

The installer copies the skills into `.agents/skills/` inside the target project.

## Prerequisites

- GitHub CLI authenticated for PR creation
- Atlassian Rovo MCP configured for Jira access
- Playwright MCP configured for browser validation

## Layout

```text
skills/
  dark-factory/
  df-wiki-init/
  df-story-intake/
  df-grill-me/
  df-clarify/
  df-spec/
  df-implement/
  df-review/
  df-evidence/
  df-ship/
  df-resume/
```

## Usage

Install the skills into a project, then ask your agent to use `dark-factory` on a Jira ticket.

For the end-to-end workflow, see `docs/WORKFLOW.md`.
