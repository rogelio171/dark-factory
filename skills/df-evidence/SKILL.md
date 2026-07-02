---
name: df-evidence
description: Validates completed story behavior using the evidence kind that fits the change (UI, API, CLI, unit, migration) and records proof for each acceptance criterion. Use when implementation and review are done and the story needs proof that the requested behavior works.
---

# DF Evidence

## Goal

Produce reusable, kind-appropriate proof that the story satisfies every acceptance criterion.

## Inputs

- `docs/specs/<ticket>/spec.md`, especially the `Evidence Plan` section.
- A working local environment for the change (running app for `ui`, runnable CLI for `cli`, etc.).
- Playwright MCP for `ui` evidence.

## Preconditions

- Implementation is complete and tests are green.
- The Evidence Plan in `spec.md` maps each acceptance criterion to an evidence kind.

## Evidence Kinds

| Kind | Captures | Stored under |
| --- | --- | --- |
| `ui` | Playwright screenshot (and optional trace) of the user-visible behavior. | `evidence/ui/` |
| `api` | Recorded request and response transcript for new or changed endpoints. | `evidence/api/` |
| `cli` | Terminal session transcript for new or changed commands. | `evidence/cli/` |
| `unit` | Path to the test report or recorded test output that proves the behavior. | `evidence/unit/` |
| `migration` | Before-and-after schema dump and the upgrade/downgrade output. | `evidence/migration/` |

## Workflow

1. Read `spec.md` and confirm the Evidence Plan is complete.
2. Create the evidence subdirectories that the plan calls for.
3. For each acceptance criterion, capture evidence using the catalog in [REFERENCE.md](REFERENCE.md):
   - `ui`: drive the app through Playwright MCP and save screenshots.
   - `api`: run the request and save request and response under a single file.
   - `cli`: run the command and save the transcript.
   - `unit`: run the targeted test set and save the report path and the relevant excerpt.
   - `migration`: dump the schema before and after and save the upgrade output.
4. For each captured file, add a small `<file>.yaml` sidecar when the criterion name is not obvious from the file name.
5. Run `df evidence index <TICKET-ID>` to write `docs/specs/<ticket>/evidence/INDEX.md` deterministically.
6. Update unresolved evidence gaps with `df state set <TICKET-ID> phase_detail "<missing evidence summary>"`.

## Delegation Model

The main agent coordinates the evidence plan and final `INDEX.md`. Prefer subagents or agent teams for evidence capture so each worker can focus on one evidence kind or acceptance criterion.

- Use a browser-capable subagent for UI evidence and ask it to return saved screenshot paths plus the criterion proven.
- Use API, CLI, unit, or migration specialist subagents when those evidence kinds can be captured independently.
- The coordinator verifies every acceptance criterion has observable proof, writes `evidence/INDEX.md`, and records blockers in `state.md`.
- Do not let one agent accumulate all app-running, browser, API, and test-output context unless the evidence plan is trivial.


## Observability

- Read `run_id` from `state.md`. If missing, run `df observability run start <TICKET-ID> --write-state`.
- Open a phase session: `df observability session start --run-id "$RUN_ID" --skill df-evidence --role coordinator`.
- Record every user message, assistant response, and tool/MCP call via `df observability message record` or `df observability batch`.
- Record external snapshots after Jira, GitHub, or CI interactions relevant to this phase.
- Close the session with `df observability session end --session-id "$DF_SESSION_ID"` before handoff.
- Full contract: `df-observability`.

## Outputs

- Per-kind evidence files under `docs/specs/<ticket>/evidence/<kind>/`.
- `docs/specs/<ticket>/evidence/INDEX.md` mapping criterion to file(s).
- Updated `state.md`.

## Rules

- Do not claim a criterion is complete without observable proof of the matching kind.
- One file per important checkpoint; do not bundle multiple criteria into a single screenshot.
- Use descriptive, stable file names (`criterion-1-toggle-on.png`, not `screenshot-2026-04-19-1.png`).
- If the app cannot be run or reached for a `ui` or `api` criterion, run `df state block <TICKET-ID> --reason "<what is unreachable and what the user must fix>"` so the blocker survives a session restart, then stop.
- If a criterion does not fit any of the five kinds, stop and ask the user; do not invent a sixth kind silently. If the ambiguity cannot be resolved in this session, block with `df state block` before stopping.
- Prefer subagents or agent teams for evidence capture; the coordinator owns coverage mapping and final synthesis.

## Handoff

When every criterion has evidence and `INDEX.md` is written, advance to `df-preflight`.

## Files

- For per-kind capture commands and the `INDEX.md` shape, see [REFERENCE.md](REFERENCE.md).
