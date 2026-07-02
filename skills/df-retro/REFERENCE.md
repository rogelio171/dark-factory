# DF Retro Reference

## The `risk.revert` Convention

`df-story-intake` is the recording side: when a new story reverts, hotfixes, or otherwise directly corrects a previously auto-merged Dark Factory story, it records:

```bash
df observability event record \
  --category risk.revert \
  --ticket <ORIGINAL-TICKET-ID> \
  --status failure \
  --summary "<what regressed and why>"
```

`df-retro` is the consuming side: it queries these events and turns repeated hits on the same path into a standing note that `df-spec` reads on every future story (see the Risk-Model Drift subsection of `df-spec`'s Risk Classification).

## `wiki/patterns/risk-model-drift.md` Format

One entry per affected path, deduplicated. Refresh `last_seen` and `count` instead of appending a new entry for the same path.

```markdown
# Risk Model Drift

Paths in this file were classified low or medium risk by the static path matrix in
`df-spec`, but have since caused a `risk.revert` event. `df-spec` raises risk by one
level for any planned diff touching these paths until removed here.

## src/billing/invoice_totals.py

- First seen: 2026-03-02 (OFRS2-8841 reverted OFRS2-8790)
- Last seen: 2026-06-14 (OFRS2-9910 reverted OFRS2-9887)
- Count: 2
- Cause: rounding regression not covered by existing unit tests.

## src/notifications/digest_scheduler.ts

- First seen: 2026-05-11 (OFRS2-9420 reverted OFRS2-9388)
- Last seen: 2026-05-11
- Count: 1
- Cause: timezone handling edge case, auto-merged as low risk without a DST test case.
```

Remove an entry once a story explicitly hardens the path (adds the missing test class, fixes the root cause) and the user confirms it should drop back to the path-based default; do this by hand, not automatically, since `df-retro` should never silently lower a risk signal it did not personally verify.

## `wiki/patterns/recurring-blockers.md` Format

```markdown
# Recurring Blockers

## Atlassian Rovo MCP not configured

- Count: 4
- Last seen: 2026-06-20
- Typical phase: intake
- Suggested fix: confirm Rovo MCP is configured in the runtime before starting story work; add to onboarding checklist.

## `gh auth status` unauthenticated mid-run

- Count: 2
- Last seen: 2026-06-18
- Typical phase: shipping, merging
- Suggested fix: check `gh auth status` in `df doctor` before any story reaches `df-ship`.
```

## `wiki/retro-log.md` Entry Format

```markdown
## 2026-07-02 - window: 2026-06-02..2026-07-02

- Runs: 14 complete, 2 blocked, 1 in progress
- risk.revert events: 1 (src/billing/invoice_totals.py, OFRS2-9910)
- Recurring blockers refreshed: Atlassian Rovo MCP not configured (count 4)
- Pages touched: wiki/patterns/risk-model-drift.md, wiki/patterns/recurring-blockers.md
- Needs a human decision: none
```
