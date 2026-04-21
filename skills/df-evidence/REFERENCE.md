# DF Evidence Reference

## Per-kind capture catalog

### `ui`

- Tooling: Playwright MCP.
- Steps:
  1. Open the app at the URL the spec specifies.
  2. Navigate to the screen named by the criterion.
  3. Trigger the user action.
  4. Take a screenshot named `<criterion-id>-<state>.png` (e.g., `ac-1-toggle-on.png`).
  5. Optionally save a Playwright trace as `<criterion-id>.zip` for hard-to-reproduce flows.
- Storage: `docs/specs/<ticket>/evidence/ui/`.

### `api`

- Tooling: `curl`, `httpie`, or the project's HTTP client.
- Steps:
  1. Capture both request and response in a single Markdown file:
     ```
     # AC-2: GET /api/toggle returns the current state

     ## Request
     ```bash
     curl -sS -X GET https://localhost:3000/api/toggle -H 'authorization: bearer <token>'
     ```

     ## Response
     ```json
     { "enabled": true }
     ```
     ```
  2. Redact secrets and tokens before saving.
- Storage: `docs/specs/<ticket>/evidence/api/<criterion-id>.md`.

### `cli`

- Tooling: `script` (POSIX) or terminal copy.
- Steps:
  1. Run the command and capture the full transcript.
  2. Save as `<criterion-id>.txt` with the command line at the top followed by the output.
- Storage: `docs/specs/<ticket>/evidence/cli/`.

### `unit`

- Tooling: project test runner.
- Steps:
  1. Run only the tests that prove the criterion (`pytest path::test`, `npm test -- --testPathPattern=...`, `go test -run`).
  2. Save the test runner output to `<criterion-id>.txt`.
  3. Note the test file path and test name in the file header.
- Storage: `docs/specs/<ticket>/evidence/unit/`.

### `migration`

- Tooling: project migration tool plus a schema dump (`pg_dump --schema-only`, `mysqldump --no-data`, `sqlite3 .schema`).
- Steps:
  1. Dump schema before the migration as `<criterion-id>-before.sql`.
  2. Run the migration and capture the runner output as `<criterion-id>-up.txt`.
  3. Dump schema after as `<criterion-id>-after.sql`.
  4. Optionally roll back and capture `<criterion-id>-down.txt`.
- Storage: `docs/specs/<ticket>/evidence/migration/`.

## `INDEX.md` shape

```markdown
# Evidence Index for OFRS2-12345

| Criterion | Kind | Files |
| --- | --- | --- |
| AC-1: toggle persists across reload | ui | evidence/ui/ac-1-toggle-on.png, evidence/ui/ac-1-after-reload.png |
| AC-2: GET /api/toggle returns state | api | evidence/api/ac-2.md |
| AC-3: migration adds preferences table | migration | evidence/migration/ac-3-before.sql, evidence/migration/ac-3-up.txt, evidence/migration/ac-3-after.sql |

## Notes

- App version under test: <git sha>
- Environment: <local | staging | preview>
- Date: 2026-04-19
```

## Choosing a kind

- If the user can see it in a browser, use `ui`.
- If a service or library exposes it over HTTP, use `api`.
- If a developer or operator runs it from a terminal, use `cli`.
- If only a test exercises it (a refactor, a guard against regression), use `unit`.
- If a database schema changes, always include `migration` even if other kinds also apply.

A single criterion may carry multiple kinds (for example `ui` and `api` for a feature that touches both layers). List all relevant files in `INDEX.md`.
