# Dark Factory

Dark Factory is a portable skill pack for running an agent-driven delivery workflow from Jira story intake through implementation, review, evidence collection, pull request creation, Jira updates, and final completion.

It is designed for long-running work that may span multiple sessions. Instead of relying on chat memory, Dark Factory keeps progress on disk through a project wiki and per-story state files so another agent can resume work safely.

## What This Project Solves

Most agent workflows are good at one part of the delivery loop and weak at the rest. Dark Factory is meant to make the full path repeatable:

1. Pull a story from Jira.
2. Understand the codebase and project conventions.
3. Clarify ambiguous requirements.
4. Create a durable PRD and execution record, including a risk classification.
5. Implement with TDD in small vertical slices.
6. Review changes in a fix-and-re-review loop.
7. Validate the feature and capture multi-kind evidence.
8. Mirror CI locally before pushing.
9. Open the PR, request a Copilot review, and arm auto-merge.
10. Babysit the PR through review and CI without human intervention on low-risk paths.
11. Update the wiki with newly learned patterns after merge.
12. Resume safely if the session is interrupted at any point.

## Core Ideas

### 1. Durable state beats chat memory

Each story gets a working directory under `docs/specs/` with a `spec.md`, `state.md`, `reviews/`, and `evidence/`. This lets a later session continue from disk instead of guessing from chat history.

### 2. The wiki is a persistent project knowledge layer

Dark Factory uses a Karpathy-style wiki under `wiki/` to store architecture, stack, patterns, and domain entities. The goal is to accumulate project knowledge instead of rediscovering it every time.

`wiki/project-profile.md` records repository layout, module boundaries, target working roots, and validation commands so Dark Factory does not accidentally run checks or make changes across unrelated sibling modules.

### 3. TDD and vertical slices keep changes small

The implementation workflow is intentionally conservative: one test, one behavior, one minimum code change, then repeat.

### 4. The main agent coordinates, subagents do heavy work

Dark Factory is designed to keep the main agent's context small. The main agent routes phases, updates durable state, asks for decisions, and synthesizes results. It should prefer subagents or agent teams for broad exploration, implementation research, review, evidence capture, preflight diagnosis, and PR babysitting.

## Included Skills

- `dark-factory`: entry point and workflow orchestrator
- `using-dark-factory`: conservative activation guidance
- `df-wiki-init`: bootstrap or refresh the project wiki
- `df-project-profile`: record module layout and scoped validation commands
- `df-story-intake`: retrieve a Jira story and initialize local story state
- `df-workspace`: record or create a safe story workspace
- `df-grill-me`: reusable one-question-at-a-time interview skill
- `df-clarify`: story-specific clarification using ticket and wiki context
- `df-spec`: create the durable PRD and state files, including risk classification
- `df-plan`: create the exact implementation plan
- `df-implement`: implement through a strict red-green-refactor loop
- `df-review`: run a spec-aware review/fix/re-review loop
- `df-evidence`: collect multi-kind evidence (UI, API, CLI, unit, migration)
- `df-preflight`: mirror CI locally before opening the PR
- `df-ship`: open the PR, label risk, request Copilot review, arm auto-merge only for low-risk eligible changes
- `df-merge`: babysit the PR through Copilot review and CI until merged
- `df-wiki-update`: append patterns, entities, and log entries after merge
- `df-github-init`: scaffold the GitHub-side automation (Actions, CODEOWNERS, Copilot instructions)
- `df-resume`: resume interrupted work from `state.md`
- `df-observability`: record full agent events and export audit data to SQLite

### 5. Enterprise observability is built in

Every installed target repo gets `.agents/dark-factory/observability.db` (gitignored) plus a committed `observability.toml` retention policy (default 365 days). Agents record full conversation history, tool/MCP calls, phase transitions, and GitHub/Jira/CI snapshots through `df observability`. Batch export supports compliance, debugging, and delivery metrics. See [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) for the compliance and operations guide.

## Repository Layout

```text
dark-factory/
├── README.md
├── install.sh
├── docs/
│   ├── SKILL_CONTRACT.md
│   ├── WORKFLOW.md
│   └── OBSERVABILITY.md
└── skills/
    ├── dark-factory/
    ├── using-dark-factory/
    ├── df-wiki-init/
    ├── df-project-profile/
    ├── df-story-intake/
    ├── df-workspace/
    ├── df-grill-me/
    ├── df-clarify/
    ├── df-spec/
    ├── df-plan/
    ├── df-implement/
    ├── df-review/
    ├── df-evidence/
    ├── df-preflight/
    ├── df-ship/
    ├── df-merge/
    ├── df-wiki-update/
    ├── df-github-init/
    └── df-resume/
```

## Prerequisites

Dark Factory is a skill pack, so it is meant to be installed into another project repository where the actual feature work will happen.

Before using it in a target project, make sure the following are available:

- GitHub CLI authenticated for PR creation, PR checks, and branch-protection setup
- Atlassian Rovo MCP configured for Jira access
- Playwright MCP configured for browser-based validation and screenshots
- A coding agent that discovers skills from `.agents/skills/`
- Repository admin permissions on the target repo if you intend to run `df-github-init` (it configures branch protection and required reviewers)

## Installation

### Install as a Claude Code plugin

Add this repository as a Claude Code plugin marketplace, then install Dark Factory from it:

```text
/plugin marketplace add rogelioorona/dark-factory
/plugin install dark-factory@dark-factory
```

From a shell, use the equivalent Claude Code CLI commands:

```bash
claude plugin marketplace add rogelioorona/dark-factory
claude plugin install dark-factory@dark-factory --scope project
```

Use `--scope project` to save the plugin enablement in the target repository's `.claude/settings.json`, or omit it to install at the user scope.

Claude Code loads the skills under the plugin namespace. Common entry points include:

```text
/dark-factory:dark-factory
/dark-factory:df-spec
/dark-factory:df-resume
```

The Claude Code plugin metadata lives in `.claude-plugin/plugin.json`, and the single-plugin marketplace catalog lives in `.claude-plugin/marketplace.json`.

### Install as a generic skill pack

For Cursor or another agent that discovers skills from `.agents/skills/`, install the skill pack into a target project:

```bash
./install.sh --target /path/to/target-project
```

If no path is provided, the current directory is used as the target.

Pass `--with-github` to print the follow-up command that scaffolds the GitHub-side automation:

```bash
./install.sh --with-github /path/to/target-project
```

Use `--dry-run` to preview changes. The installer refuses suspicious targets such as `/`, `$HOME`, or directories without project markers unless `--force` is passed.

The installer copies each skill directory into:

```text
.agents/skills/
```

inside the target project, installs the deterministic `df` CLI into `.agents/bin/df`, installs the Python harness package under `.agents/lib/dark_factory`, initializes the SQLite observability store under `.agents/dark-factory/`, writes a `.dark-factory-version` stamp from the source repo's `git rev-parse HEAD`, and skips any skill whose source content is unchanged since the last install.

Use `--runtime cursor|claude|generic` to record the intended runtime surface:

```bash
./install.sh --runtime cursor --target /path/to/target-project
```

`generic` keeps the portable `.agents/skills/` layout. `cursor` and `claude` are checked by `df doctor --runtime <name>` so setup problems are surfaced before story work starts.

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
~/dev/my-app/.agents/bin/df
~/dev/my-app/.agents/lib/dark_factory
~/dev/my-app/.agents/dark-factory/observability.toml
~/dev/my-app/.agents/dark-factory/observability.db   # gitignored
```

## Deterministic Harness CLI

Dark Factory now ships a thin Python CLI named `df`. Skills still describe the workflow and judgment rules, but deterministic mechanics are executed by commands so any agent runtime can behave the same way.

Core commands:

```bash
df doctor --runtime generic
df state init|get|set|list|block|unblock
df detect-tooling
df classify-risk --diff-base origin/main
df preflight <ticket>
df evidence index <ticket>
df render-pr-body <ticket>
df ship <ticket>
df pr poll|resolve-thread|reply-thread|fix-checks
df resume [--ticket <ticket>]
df observability init|doctor|stats|report
df observability run start|end
df observability session start|end|show
df observability message record|event record|snapshot record|batch
df observability query|tail|run-show|export|prune|migrate-states
```

The agent remains responsible for judgment-heavy work: clarification, implementation, review, evidence capture, failure diagnosis, and Copilot comment classification. The CLI owns state mutation, risk path matching, command detection, preflight schema generation, evidence index rendering, PR body rendering, PR plumbing, resume dispatch, and observability recording/query/export.

## What Gets Created in the Target Project

When Dark Factory runs inside a target project, it creates three kinds of artifacts.

### 1. Observability store

Installed automatically by `install.sh`:

```text
.agents/dark-factory/
├── observability.toml      # retention + redaction policy (committed)
├── observability.db        # SQLite store (gitignored)
├── redaction-patterns.txt  # optional custom secret/PII patterns
└── exports/                # batch export output (gitignored)
```

Every `df` command, phase transition, preflight run, and GitHub/Jira snapshot can be recorded here. Agents also persist full conversation history (user, assistant, tool/MCP calls) through `df observability`. See `df-observability` for the agent recording contract and [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) for compliance and operations.

Common operations:

```bash
df observability doctor
df observability tail --ticket OFRS2-123
df observability export --ticket OFRS2-123 --format jsonl
df observability report --since 30d
df observability prune --dry-run
```

For repos that already had story state before observability was added:

```bash
df observability migrate-states
```

### 2. Project wiki

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

### 3. Story work area

```text
docs/specs/<ticket-slug>/
├── spec.md
├── plan.md
├── state.md
├── preflight.json
├── reviews/
└── evidence/
    ├── ui/
    ├── api/
    ├── cli/
    ├── unit/
    └── migration/
```

This is the durable record for a single story. `state.md` also carries `run_id`, which links the story to rows in `.agents/dark-factory/observability.db`.

### 4. GitHub-side automation (created by `df-github-init`)

```text
.github/
├── workflows/
│   ├── pr-checks.yml
│   ├── pr-open.yml
│   └── pr-fix-loop.yml
├── CODEOWNERS
├── pull_request_template.md
└── copilot-instructions.md
```

This is what lets Copilot review and the auto-fix agent merge low-risk PRs without human approval.

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
- If module scope is missing, it uses `df-project-profile`.
- If `.github/workflows/pr-checks.yml` is missing in the target repo, it suggests `df-github-init`.
- If the story has not been initialized, it uses `df-story-intake`.
- If the workspace has not been recorded, it uses `df-workspace`.
- If requirements are unclear, it uses `df-clarify`.
- If `spec.md` is missing or incomplete, it uses `df-spec`.
- If `plan.md` is missing, it uses `df-plan`.
- If the story is ready to build, it uses `df-implement`.
- If implementation needs review, it uses `df-review`.
- If review is clean, it uses `df-evidence`.
- If evidence is recorded, it uses `df-preflight` to mirror CI locally.
- If preflight is green, it uses `df-ship` to open the PR and arm auto-merge.
- If a PR is open, it uses `df-merge` to babysit the PR through Copilot review and CI.
- If `df-merge` finishes a merge, it invokes `df-wiki-update` to fold new patterns into the wiki.
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
- starts a delivery run in the observability store and writes `run_id` into `state.md` (via `df story init`)

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

`df-evidence` validates the finished feature and stores proof under `docs/specs/<ticket>/evidence/` using the kind that fits the change: UI screenshots through Playwright MCP, API request/response transcripts, CLI session captures, unit test reports, or before/after schema dumps for migrations.

### 8. Preflight

`df-preflight` mirrors CI locally before the PR is opened. It runs the project's lint, typecheck, test, build, secret scan, and dependency audit, lints the branch's commit messages, and writes `docs/specs/<ticket>/preflight.json`. Any failure blocks `df-ship`.

The generated `pr-checks.yml` runs on pull requests and pushes without assuming the default branch is named `main` or `master`. `df-github-init` still detects the default branch for branch-protection setup.

### 9. Shipping

`df-ship`:

- opens the GitHub PR with a structured body and links to evidence
- applies a `risk:<level>` label and, when eligible, an `auto_merge_eligible` label
- requests a Copilot code review
- arms auto-merge only when both `risk: low` and `auto_merge_eligible: true` are present in the state and PR body
- posts an initial summary to Jira
- sets `status: merging` and exits

### 10. Merging

`df-merge` babysits the PR until it merges:

- watches required checks and fixes scoped failures
- classifies Copilot review comments and applies auto-fixes for the eligible ones
- escalates back to a human when a comment hits a CODEOWNERS path, conflicts with the spec, or requires scope expansion
- on merge, invokes `df-wiki-update`, posts the final Jira summary, and transitions the ticket to done

### 11. Resume

`df-resume` reads the on-disk state and supporting artifacts to continue safely after an interruption, including resuming the merging phase from `state.md`'s `pr_url` field.

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

### Scaffold GitHub automation in a new repo

```text
Use df-github-init to set up the PR workflows and Copilot instructions.
```

### Babysit a PR that is open but not merged

```text
Use df-merge on the current story's PR.
```

## Reducing Human Intervention in PR Review

Dark Factory removes humans from the review path on low-risk changes by combining four pieces:

1. `df-spec` writes a `risk` and `auto_merge_eligible` field into `state.md` based on which paths the change touches.
2. `df-github-init` scaffolds GitHub Actions, a CODEOWNERS file used as a risk filter, and `copilot-instructions.md` derived from the project wiki so Copilot reviews against project conventions.
3. `df-ship` opens the PR, requests Copilot review, and arms `gh pr merge --auto --squash` when the change is low risk.
4. `df-merge` runs as the GitHub-side fix loop: it watches required checks, classifies Copilot comments, applies the auto-fix-eligible ones (lint, types, naming, missing tests, docstrings, dead code, suggested refactors with concrete code), and escalates to a human only on CODEOWNERS paths, security-tagged comments, or scope-expanding requests.

The fix-loop workflow ships runtime-agnostic and disabled by default. `df-github-init` writes a clearly marked `AGENT RUNTIME PLACEHOLDER` step inside `.github/workflows/pr-fix-loop.yml` with three commented examples (Cursor CLI, Cursor Cloud, Claude Code Action). Pick the one that matches your tooling, replace the placeholder, and set `DF_MERGE_RUNTIME_CONFIGURED: "true"`. Until then, the workflow exits successfully without attempting fixes.

## Maintaining This Skill Pack

This repository validates itself with `.github/workflows/validate.yml`. The validation checks:

- `SKILL.md` frontmatter and required section order
- referenced sibling files in skill docs
- required coordinator/subagent delegation guidance for heavy-work skills
- valid `df <command>` references in skill docs
- state-template schema drift
- fail-by-default placeholders in generated workflow templates
- generated GitHub workflow YAML syntax
- `install.sh` smoke behavior: first install, idempotent reinstall, and selective reinstall after a changed skill
- pytest coverage under `tools/dark_factory/tests/` exercises CLI primitives against temporary repositories

Run the same checks locally with:

```bash
python -m pip install pyyaml pytest  # needed for workflow YAML and CLI tests
bash scripts/run-tests.sh
```

## Updating the Skill Pack in a Target Project

If you make changes to this repository and want to refresh the installed copy in a target project, run the installer again:

```bash
./install.sh --target /path/to/target-project
```

The installer skips unchanged skills, atomically replaces changed skill directories in `.agents/skills/`, and writes `.agents/skills/.dark-factory-version`.

## Troubleshooting

### Jira access is not working

Check that Atlassian Rovo MCP is configured and available to the agent. Dark Factory expects Jira access through MCP rather than through ad hoc shell scripts.

### Browser validation is not working

Check that Playwright MCP is available and that the target project can actually run locally.

### The workflow was interrupted

Use `df-resume`. The intended source of truth is `docs/specs/<ticket>/state.md`, not the previous chat thread.

### The workflow is blocked on something only I can fix

Check `docs/specs/<ticket>/state.md` for `status: blocked`, `blocked_reason`, and `blocked_from` (also printed by `df resume`). Fix the underlying issue (credentials, scope decision, closed PR, etc.), then run `df state unblock <TICKET-ID>` to restore `status: <blocked_from>` and continue with `df-resume`. This works from any session, at any time, because the blocker and its cause are recorded on disk rather than in chat history.

### The wiki is stale

Run `df-wiki-init` again in the target project to refresh the project knowledge base.

## Additional Documentation

- For the concise lifecycle summary, see `docs/WORKFLOW.md`.
- For the exact instructions each phase uses, read the `SKILL.md` files under `skills/`.

