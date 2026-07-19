# Issue: <title>

**Sprint**: sprint-<m>-<y>-<dd>-<dd> · **Source**: `prd.md` §<n> / `user-journeys/<file>`
**Assignee (parent)**: `agents/<team>/<role>`
**Goal**: one sentence tying this issue to the user goal it serves. If it
doesn't trace to the PRD or a user journey, it doesn't get created.

## Spec

What must be true when this issue closes — contracts, constraints,
references. Statements a reviewer can falsify, not prose about intent.

## Sub-issues

Granularity rule: one deliverable, one owner, independently verifiable.
If a sub-issue needs two agents or two deliverables, split it again.
Decomposition overhead is itself a cost — don't split past the point
where the tracking outweighs the deliverable.

### 1. <title>
- **Assignee**: `agents/<team>/<role>` (narrowest fit from `agents/INDEX.md`)
- **Scope**: the single deliverable, stated as a noun.
- **Acceptance criteria**:
  - [ ] Checkable criterion — no "works well", name the observable result.
  - [ ] Another, if needed. Fewer, sharper criteria beat a long vague list.
- **Negative prompt** (do NOT):
  - Files/systems this sub-issue must not touch.
  - Abstractions/dependencies it must not introduce.
  - Scope it must not absorb, even if adjacent and tempting.
- **Verify**: the exact command or observation that proves it done.

### 2. <title>
…same shape.

## Dependencies

Direction, not vibes: `#1 blocks #2` — never just "related".
