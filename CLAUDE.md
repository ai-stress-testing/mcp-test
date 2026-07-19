# mcp-test — session operating manual

Docs + agent-org conventions adopted from
[Ges-Talt](https://github.com/ai-stress-testing/Ges-Talt), which remains
the source of truth for the convention itself — this repo carries the
scaffold, not a fork of the workflow apparatus. Consult Ges-Talt directly
for the fuller machinery (verdict loop, comms format, model tiers, credit
ledger) once this roster grows past the scaffold stage; don't copy those
pieces here ahead of actually needing them.

## On session start

1. Ensure the docs scaffold exists: `python3 scripts/init_docs.py .`
   (idempotent; safe to run every session).
2. Identify the current sprint folder: `docs/sprint-<m>-<y>-<dd>-<dd>/`
   (month, 2-digit year, start day, end day — e.g. `sprint-7-26-19-26`
   = 2026-07-19 → 07-26). If today falls outside every sprint window,
   scaffold the next one before starting work.

## Docs convention

- `docs/backlog.md` — one table row per issue.
- `docs/sprint-*/prd.md` — the sprint's requirements; issues cite `§n`.
- `docs/sprint-*/sprint-log/` — one dated entry per working session
  (template: `docs/templates/sprint-log-entry.md`). Write one before
  ending substantial work; decisions recorded there are not re-litigated.
- `docs/sprint-*/user-journeys/` — one file per journey
  (template: `docs/templates/user-journey.md`).

## Roster rules

- Agents live in `agents/<team>/<role>/` as `agent.md` + `SPEC.md`
  (template: `agents/TEMPLATE/`).
- After adding/changing agents: `python3 scripts/build_index.py` must
  exit 0 (it regenerates `agents/INDEX.md` and lints the roster — same
  rules as Ges-Talt: full frontmatter, an `agent.md`+`SPEC.md` pair per
  role, opus never holds Edit/Bash).
- This repo has no `scripts/models.toml` or `scripts/tools-baseline.json`
  yet — `build_index.py` degrades gracefully without them (every
  `model:` value must then be a concrete id). Pull those files from
  Ges-Talt's `scripts/` the first time a role actually needs a
  capability tier or the tool-widening lint.
