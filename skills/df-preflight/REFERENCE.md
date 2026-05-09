# DF Preflight Reference

## `preflight.json` schema

```json
{
  "ticket": "OFRS2-12345",
  "branch": "OFRS2-12345-add-dark-mode-toggle",
  "ran_at": "2026-04-19T19:55:00Z",
  "repo_root": "/path/to/repo",
  "working_root": "packages/app",
  "target_modules": ["packages/app"],
  "merge_base": "abc1234",
  "head": "def5678",
  "summary": "passed | failed | passed-with-warnings",
  "stages": [
    {
      "name": "lint",
      "command": "npm run lint",
      "cwd": "packages/app",
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
| `package.json` with script + `package-lock.json` | `npm run lint` | `npm run typecheck` or `npx tsc --noEmit` | `npm test` | `npm run build` |
| `package.json` with script + `pnpm-lock.yaml` | `pnpm lint` | `pnpm typecheck` | `pnpm test` | `pnpm build` |
| `package.json` with script + `yarn.lock` | `yarn lint` | `yarn typecheck` | `yarn test` | `yarn build` |
| `package.json` with script only | `npm run lint` after `npm install` | `npm run typecheck` or `npx tsc --noEmit` after `npm install` | `npm test` after `npm install` | `npm run build` after `npm install` |
| `pyproject.toml` with `ruff` | `ruff check .` from module root | `mypy .` from module root if configured | `pytest -q` from module root | `python -m build` from module root if configured |
| `pyproject.toml` only | `flake8` from module root if installed | `mypy .` from module root if configured | `pytest -q` from module root | skipped |
| `go.mod` | `go vet ./...` from module root | (covered by build) | `go test ./...` from module root | `go build ./...` from module root |
| `Cargo.toml` | `cargo fmt --check` then `cargo clippy --all-targets -- -D warnings` | (covered by check) | `cargo test --all` | `cargo build --all-targets` |
| `Makefile` with target | `make lint` | `make typecheck` | `make test` | `make build` |
| Nothing detected | skipped with reason `"no lint tooling detected"` | skipped | skipped | skipped |

If multiple manifests are present, run only those selected by `target_modules` in `state.md`. Run all that apply only when `wiki/project-profile.md` records the whole repo as the intended scope.

## Security scans

| Tool | Command | Trigger |
| --- | --- | --- |
| gitleaks | `gitleaks detect --source . --no-git -v` | `gitleaks` on PATH |
| npm audit | `npm audit --omit=dev --json` | `package-lock.json` present |
| pnpm audit | `pnpm audit --prod --json` | `pnpm-lock.yaml` present |
| yarn audit | `yarn npm audit --severity critical` | `yarn.lock` present |
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
