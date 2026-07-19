# Agents (the brains)

Organized by **team → role**, not by feature. A team owns a durable
subclass of problems (frontend, backend, networking, logic review); roles
are the specific personas within it. Teams may have one role or several
nested ones — see `frontend/` for the nested case.

## Convention

Every role gets its own folder: `agents/<team>/<role>/`, containing:

- **`agent.md`** — the loadable Claude Code subagent. YAML frontmatter
  (`name`, `description`, `tools`, `model`) + a lean system prompt. This is
  what actually runs. Keep it short — persona, responsibilities, handoff,
  a short "never" list. No restated code comments, no vibe copy.
- **`SPEC.md`** — the full card: persona narrative, capabilities,
  model choice + why, tool list + why (least privilege), acceptance
  criteria for this agent's output, and who it hands off to.

`agent.md` is the contract an orchestrator reads to invoke the agent.
`SPEC.md` is the contract a human reads to decide whether the agent is
built right. They shouldn't duplicate each other's prose — `SPEC.md` can
just say "see agent.md" for the prompt itself.

## Adding a new agent

1. Copy `agents/TEMPLATE/` to `agents/<team>/<role>/` (new team, or a new
   role under an existing one).
2. Fill in both files. Pick the cheapest model that can do the job and the
   narrowest tool set the job needs — don't default to Opus + all-tools.
3. Add a row to the roster table below.

## Roster

See [INDEX.md](INDEX.md) — generated from every agent's frontmatter by
`scripts/build_index.py`. Regenerate after adding or changing agents:

```
python3 scripts/build_index.py
```

The script also lints the roster: every role must have both files, full
frontmatter, and no opus role may hold write tools (opus buys reasoning
depth, not blast radius). It exits non-zero on violations, so it can gate
CI later.

Model and tool choices are per-agent decisions, not fixed by team —
justify the choice in that agent's `SPEC.md`, don't just copy a sibling's
row.
