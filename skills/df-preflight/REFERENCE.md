# DF Preflight Reference

## `preflight.json` schema

```json
{
  "ticket": "OFRS2-12345",
  "branch": "OFRS2-12345-add-dark-mode-toggle",
  "ran_at": "2026-04-19T19:55:00Z",
  "merge_base": "abc1234",
  "head": "def5678",
  "summary": "passed | failed | passed-with-warnings",
  "stages": [
    {
      "name": "lint",
      "command": "npm run lint",
      "status": "passed | failed | skipped | warning",
      "duration_ms": 4231,
      "exit_code": 0,
      "tail": "...",
      "skipped_reason": null
    }
  ],
  "blockers": [
    "test stage failed: 2 tests failing in src/components/Toggle.test.tsx"
  ]
}
```

`summary` is `failed` if any stage has `status: failed`, `passed-with-warnings` if any stage has `status: warning` and none failed, otherwise `passed`. `df-ship` refuses to run unless `summary` is `passed` or `passed-with-warnings`.

## Stage detection catalog

| Manifest detected | lint | typecheck | test | build |
| --- | --- | --- | --- | --- |
| `package.json` with script | `npm run lint` | `npm run typecheck` or `tsc --noEmit` | `npm test --silent` | `npm run build` |
| `pnpm-lock.yaml` | `pnpm lint` | `pnpm typecheck` | `pnpm test` | `pnpm build` |
| `yarn.lock` | `yarn lint` | `yarn typecheck` | `yarn test` | `yarn build` |
| `pyproject.toml` with `ruff` | `ruff check .` | `mypy .` if configured | `pytest -q` | `python -m build` if configured |
| `pyproject.toml` only | `flake8` if installed | `mypy .` if configured | `pytest -q` | skipped |
| `go.mod` | `go vet ./...` | (covered by build) | `go test ./...` | `go build ./...` |
| `Cargo.toml` | `cargo fmt --check` then `cargo clippy --all-targets -- -D warnings` | (covered by check) | `cargo test --all` | `cargo build --all-targets` |
| `Makefile` with target | `make lint` | `make typecheck` | `make test` | `make build` |
| Nothing detected | skipped with reason `"no lint tooling detected"` | skipped | skipped | skipped |

If multiple manifests are present, run all that apply (e.g., a polyglot repo with `package.json` and `pyproject.toml`).

## Security scans

| Tool | Command | Trigger |
| --- | --- | --- |
| gitleaks | `gitleaks detect --source . --no-git -v` | `gitleaks` on PATH |
| npm audit | `npm audit --omit=dev --json` | `package-lock.json` present |
| pnpm audit | `pnpm audit --prod --json` | `pnpm-lock.yaml` present |
| pip-audit | `pip-audit --format json` | `pip-audit` on PATH and Python project |
| cargo audit | `cargo audit --json` | `cargo-audit` installed |

Treat secret-scan findings as `failed` (they cannot ship). Treat dependency-audit findings as `warning` unless severity is `critical`, in which case `failed`.

## Commit-message lint

Compute the range with `git rev-list "$(git merge-base HEAD origin/$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@'))"..HEAD`. For each commit subject, validate the regex:

```
^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?(!)?: .{1,72}$
```

Failures are stage `commit-lint` with status `failed`.

## Re-running preflight after fixes

Always re-run from scratch. Preflight is cheap relative to a failed CI cycle and should not be partial. Overwrite `preflight.json` each run.
