# DF Merge Reference

## Auto-fix eligibility matrix

A Copilot (or human) review comment is auto-fix-eligible when ALL of these are true:

- The comment includes a concrete code suggestion (a fenced code block, a `suggestion` block, or a clear "change X to Y").
- The change is contained within files already touched by the PR.
- The change does not introduce a new public API or wire format.
- The comment is not prefixed with one of the escalate tags below.
- The file the comment is on is not owned by anyone in `.github/CODEOWNERS`.

Eligible categories:

| Category | Examples |
| --- | --- |
| lint, formatting | "trailing whitespace", "use single quotes", "missing semicolon" |
| typing | "annotate `foo` as `Optional[int]`", "use `string` not `String`" |
| missing tests | "add a test for the empty-input case" (when the behavior already exists in the diff) |
| naming | "rename `tmp` to `pendingItem`" |
| dead code | "remove unused import `os`", "remove unreachable branch" |
| docstrings | "add a one-line docstring describing the parameter" |
| small refactor | "extract this expression into a `is_eligible()` helper" |

## Escalate matrix

Always escalate (post a reply explaining and stop) when ANY of these are true:

- Comment is prefixed with `security:`, `api-contract:`, `scope:`, or `spec-conflict:`.
- Comment touches a file owned by someone in `.github/CODEOWNERS`.
- Comment requests behavior not in `spec.md`'s acceptance criteria.
- Comment requests adding a new dependency.
- Comment requests changes to migrations, infra (`infra/`, `terraform/`, `k8s/`, `helm/`), or CI configuration.
- Comment is open-ended ("consider whether ..."): no concrete patch, no auto-fix.
- The PR's risk label is `risk:medium` or `risk:high` and the comment is non-trivial.

## CI failure fix recipes

| Failure | Recipe |
| --- | --- |
| lint | Run the project's lint formatter (`npm run lint -- --fix`, `ruff check . --fix`, `cargo fmt --all`, `gofmt -w .`), commit the result. |
| typecheck | Read the type error, add the minimal annotation or guard, re-run locally, commit. Never silence with `any` / `# type: ignore` unless the spec says so. |
| test | Read the test output, decide if the test or the code is wrong (per the spec). Fix one test at a time. Never delete a test to get green. |
| build | Read the build error. Likely cause: missing import, missing type export, or a path alias change. Fix at the source. |
| security (gitleaks) | Stop and escalate. Do not push secrets out of history from this skill; instruct the user. |
| security (audit) | If the failing dependency is project-owned, bump it (`npm update <pkg>`, `pip install -U <pkg>`, etc.). If it is transitive, escalate. |

For any failure category not listed above: escalate.

## GitHub GraphQL: resolve a thread

GitHub does not expose thread resolution in `gh pr edit`; use the GraphQL API.

### Get thread IDs

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $pr:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$pr) {
        reviewThreads(first:100) {
          nodes {
            id
            isResolved
            comments(first:1) { nodes { id databaseId body path } }
          }
        }
      }
    }
  }' -F owner="$OWNER" -F repo="$REPO" -F pr="$PR_NUMBER"
```

### Resolve a thread

```bash
gh api graphql -f query='
  mutation($id:ID!) {
    resolveReviewThread(input:{threadId:$id}) {
      thread { id isResolved }
    }
  }' -F id="$THREAD_ID"
```

### Reply on a thread before resolving

```bash
gh api -X POST "repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments/${COMMENT_ID}/replies" \
  -f body="Addressed in commit ${SHA}: ${one_line_summary}"
```

`COMMENT_ID` is the `databaseId` from the thread query.

## Polling cadence

- First poll: immediately after entering the loop.
- After a push: poll within 10 seconds (CI re-trigger).
- After a green poll with no review activity: 30 -> 60 -> 120 -> 300 seconds, capped.
- Never poll faster than 10 seconds; respect rate limits.

## Stopping conditions

| Condition | Action |
| --- | --- |
| `state == "MERGED"` | Run post-merge steps and set `status: complete`. |
| `state == "CLOSED"` (not merged) | Set `status: blocked`, reason "PR closed", stop. |
| Escalate-tagged comment | Reply, set `status: blocked` with the comment ID, stop. |
| Required check failure with no recipe | Reply on the PR, set `status: blocked`, stop. |
| Auto-fix loop applied 5+ commits with no convergence | Stop, set `status: blocked`, reason "auto-fix not converging". |
