# Copilot Instructions

These instructions apply to GitHub Copilot for both code generation and code review in this repository. Dark Factory's `df-github-init` populates the project-specific sections from the wiki; do not edit the wiki references away.

## Project context

- Stack: see `wiki/stack/` (filled by `df-github-init`).
- Architecture: see `wiki/architecture/` (filled by `df-github-init`).
- Patterns: see `wiki/patterns/` (filled by `df-github-init`).
- Domain entities: see `wiki/entities/` (filled by `df-github-init`).

> When you generate or review code, prefer the patterns documented in `wiki/patterns/` over inventing new ones.

## Review priorities (in order)

1. Correctness against the PR's `## Summary` and the linked spec under `docs/specs/<ticket>/spec.md`.
2. Test coverage: every behavior described in `## Test plan` should map to a test in the diff.
3. Security: secrets, authentication, authorization, injection, deserialization. Tag any finding here as `security:` so the auto-fix loop escalates instead of self-fixing.
4. Conformance to the patterns documented in the wiki.
5. Style and naming.

## Auto-fix-eligible findings

When the auto-fix loop sees one of your comments and the comment includes a concrete code suggestion, it will apply the fix automatically:

- lint, formatting, and import-order issues
- type errors with an obvious annotation fix
- missing tests that exercise behavior already in the diff
- naming, dead code, and small refactors with a code block
- docstring and comment improvements

## Escalate (never auto-fix)

Always tag these with the prefix in parentheses so the loop escalates:

- `security:` - any security concern
- `api-contract:` - any change to a public API surface
- `scope:` - the comment expands the scope of the PR
- `spec-conflict:` - the comment conflicts with `spec.md`'s acceptance criteria

## Project conventions

<!-- df-github-init replaces the block below with conventions distilled from
     wiki/patterns/, wiki/stack/, and any explicit STYLE.md files. -->

- Add language-, framework-, and team-specific conventions here.
- Keep this section grounded in real repo files; do not invent rules.
