# docs/decisions/

Decision records: one immutable file per non-trivial design/architecture
decision — using Michael Nygard's minimal headers (Title, Status, Context,
Decision, Consequences), plus a `Date:` line under Status. Distill the
decision itself, not the full planning narrative behind it.

A reversed decision gets a new record whose Status reads
`Superseded by 00NN`; the old file stays as-is. Routine notes belong in
`CLAUDE.md` instead of here; PR-description-only detail doesn't need a
record at all.

Numbered `NNNN-title.md`, sequential, never reused.

## Format

```markdown
# NNNN: <Title>

## Status

Accepted — YYYY-MM-DD

## Context

...

## Decision

...

## Consequences

...
```
