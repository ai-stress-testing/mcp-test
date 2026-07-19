# DB schema seam

Empty by design. `docker-compose.yml` mounts this folder read-only to
`/docker-entrypoint-initdb.d` — the `supabase/postgres` image runs every
`*.sql` / `*.sh` file here, in filename order, on first boot of a fresh
`db-data` volume.

This is where `backend/backend-dev` puts the pricing/checkout schema
(pricing arms, assignment events, orders) once that ticket starts —
**not** this agent's scope (containerization-engineer stands up the
platform, not the data model). Numbering convention: `0001_*.sql`,
`0002_*.sql`, ... so ordering is explicit.

To pick up new files here after the volume already initialized once:
`docker compose -f environments/test/docker-compose.yml down -v` (drops
the volume, re-runs init) — test-only, never do this against prod.
