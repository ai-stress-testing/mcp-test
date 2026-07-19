# Role Name — Spec

**Team**: team-slug
**Persona**: A short narrative — how this agent thinks and communicates,
not just what it does.

**Capabilities**
- Bullet list of concrete things this agent can produce or decide.

**Model**: `model-alias` (full model id) — one sentence on why this model
and not a cheaper or more expensive one for this specific job.

**Tools**: list — one sentence on why this set and not a wider one
(least privilege: if the agent doesn't need to write files, it doesn't get
Edit/Write; if it doesn't need a shell, it doesn't get Bash).

**System prompt**: `agent.md` in this folder.

**Acceptance criteria** (this agent's output is done when):
- [ ] Checkable criterion, not "make it good".
- [ ] Another checkable criterion.

**Handoffs**: → next role/agent, and under what condition it escalates to
a human or to `pm` instead of guessing.
