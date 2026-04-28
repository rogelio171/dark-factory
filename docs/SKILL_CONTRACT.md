# Dark Factory Skill Contract

Every `SKILL.md` in this pack follows the same shape so the orchestrator's dispatch decisions stay deterministic and so a new skill can be authored quickly.

## Required frontmatter

```markdown
---
name: <skill-name>
description: <one or two sentences. Start with what the skill does. End with "Use when ..." so the agent knows when to pick it.>
---
```

The `description` is the trigger. Make the "Use when" clause specific, not generic.

## Required body sections (in this order)

1. `# <Title>` (H1).
2. `## Goal` - one or two sentences naming the outcome.
3. `## Inputs` - bullet list of files, env vars, MCP tools, or upstream artifacts the skill reads.
4. `## Preconditions` - bullet list of states that must be true before the skill runs (e.g., "story is `status: implementing`", "`spec.md` exists").
5. `## Workflow` - numbered list of steps the skill performs.
6. `## Outputs` - bullet list of files, state changes, side effects, and any data the next skill consumes.
7. `## Rules` - bullet list of constraints and "do not" rules.
8. `## Handoff` - one or two sentences naming the next skill or stop condition.

## Optional sections

- `## Files` - pointer to `REFERENCE.md` or any templates the skill uses. Place last.
- Any skill-specific section (e.g., `## Risk Classification` in `df-spec`, `## Evidence Kinds` in `df-evidence`) goes between `Workflow` and `Outputs`.
- `## Delegation Model` - required for orchestrator or heavy-work skills. Place it between `Workflow` and `Outputs`.

## Delegation model

Dark Factory should preserve the main agent's context. The main agent is a coordinator by default: it routes phases, keeps `state.md` current, asks for user decisions, and synthesizes outputs. It should prefer subagents or agent teams for context-heavy work.

Use subagents or agent teams for:

- broad repository exploration and wiki synthesis
- test discovery, implementation-slice research, and validation
- review passes, CI failure diagnosis, and fix recommendations
- evidence capture for UI, API, CLI, unit, and migration proofs
- long-running PR babysitting loops where specialist agents can classify comments or failures

The main agent may perform small, scoped edits when that is the safest path, but it should avoid loading the entire implementation, review, and validation context into one thread. Every heavy-work skill must say how the coordinator delegates work and how results are summarized back into durable files.

## REFERENCE.md

Skills with non-trivial detail (state schemas, command catalogs, eligibility matrices) keep that detail in a sibling `REFERENCE.md`. The SKILL.md links to it from the `Files` section.

## Templates

When a skill writes structured documents, those documents live under `templates/` next to the SKILL.md. The skill body says which template to use.

## Authoring rules

- Keep SKILL.md scannable: a smart reader should pick the right action in under a minute.
- Prefer concrete file paths and exact commands over abstractions.
- Never duplicate content between SKILL.md and REFERENCE.md; SKILL.md decides, REFERENCE.md catalogs.
- Never include fence-broken YAML or unterminated frontmatter; the loader will reject the skill.
- Never reference skills that do not exist in this pack.
- Prefer subagents or agent teams over single-agent execution for context-heavy work.
- Keep coordinator instructions separate from worker instructions: the coordinator owns state, synthesis, escalation, and handoff; workers own focused exploration, validation, review, or fix tasks.

## Validation checklist

Before merging a SKILL.md change, confirm:

- [ ] Frontmatter parses (open and close `---`, valid YAML between).
- [ ] All eight required sections are present in order.
- [ ] `Preconditions` and `Outputs` are concrete and testable.
- [ ] `Handoff` names a real next skill or "stop and ask the user".
- [ ] No phase names are used that are not in `dark-factory/REFERENCE.md`.
- [ ] Orchestrator and heavy-work skills include a concrete `Delegation Model`.

Run the automated validator before merging:

```bash
python scripts/validate_skill_pack.py
bash scripts/smoke_install.sh
```
