---
name: team-role-slug
description: One or two sentences. State what the agent does, when to invoke it, and what it explicitly does NOT do (helps a caller pick the right agent instead of the closest-sounding one).
tools: Read, Grep, Glob
model: sonnet
---

# Role Name

One-line persona: how this agent thinks, in a phrase.

Responsibilities:
- What it does, as verbs, not a job description.
- Keep this list short — 3-5 bullets, not a manual.

(Implementer roles: insert the shared Method ladder block here — see any implementer agent.md.)

Handoff: who receives this agent's output, and when to escalate instead of
guessing.

Never: the 2-3 things this agent should refuse even if asked, because
they belong to a different role.

Acceptance criteria: see SPEC.md.

Depth pack (optional, loaded on a depth trigger): see DEPTH.md — docs/depth-packs.md.
