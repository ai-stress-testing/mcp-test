# Environments

Implements PRD `sprint-7-26-19-26/prd.md` §7: two environments with
byte-for-byte **image parity** — a **test** environment on self-hosted
Supabase (Docker, free) and a **production** environment on managed
Supabase (or equivalent managed Postgres). Config comes from the
environment, not a rebuild; no secrets in the repo or in any image.

Owner: `devops/containerization-engineer` (this stack + the parity
contract). Out of scope here, by design — see "Handoffs" below.

## The two-environment model

| | test | prod |
|---|---|---|
| Postgres | `db` container, `supabase/postgres:17.6.1.136` | managed Supabase project (or equivalent managed Postgres) |
| Auth / REST / gateway | `auth`, `rest`, `kong`, `meta`, `studio` containers (this folder) | the managed project's built-in Auth/REST/gateway |
| Config | `environments/test/.env` (from `.env.example`, gitignored) | injected by the deploy platform's secret manager at deploy/runtime |
| Stripe | **test-mode** keys (`sk_test_...`) | **live-mode** keys (`sk_live_...`) |
| Compose file | `environments/test/docker-compose.yml` | none — prod runs no Supabase-platform containers at all |

**What "the same image promotes" means concretely**: the *app* image
(built elsewhere, outside this folder — see "Handoffs") never bakes in a
Supabase URL, an API key, or a Stripe key. It reads `SUPABASE_URL`,
`SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `STRIPE_SECRET_KEY`,
etc. from the process environment at container start. Point the exact
same image at `environments/test/.env`'s values and it runs against the
Docker stack in this folder; point it at `environments/prod/.env`'s
values (injected, not committed) and it runs against the managed
project. Nothing about the image changes between the two — only which
`.env` supplied the config, which is the whole point of PRD §7.

This folder does **not** contain the app's Dockerfile or its DB
schema/migrations — those are `backend/backend-dev`'s ticket (see
`environments/test/volumes/db/init/README.md` for the exact seam). This
folder stands up the *platform* the app is promoted onto.

## Why this service subset

Self-hosted Supabase's full upstream compose has ~11 services. This
stack runs five, because those are the only ones the pricing/checkout
app (per `issue-specs/pricing-pipeline.md` and `ADR-0001`) actually
talks to:

- **`db`** (`supabase/postgres:17.6.1.136`) — Postgres itself; the
  learner's state store per ADR-0001.
- **`auth`** (`supabase/gotrue:v2.189.0`) — issues/verifies JWTs; the
  anon/service-role key model the app's Supabase client expects.
- **`rest`** (`postgrest/postgrest:v14.12`) — auto-generated REST over
  the schema backend-dev owns.
- **`meta`** (`supabase/postgres-meta:v0.96.6`) — Studio's introspection
  backend; Studio doesn't function without it.
- **`studio`** (`supabase/studio:2026.07.07-sha-a6a04f2`) — local admin
  UI, for a human to inspect the test DB. Not part of the prod topology
  at all (managed Supabase provides its own).
- **`kong`** (`kong/kong:3.9.1`) — single front door
  (`http://localhost:${KONG_HTTP_PORT}`) that the app's `SUPABASE_URL`
  points at, routing `/auth/v1/*` and `/rest/v1/*` to the containers
  above with key-auth enforced (`environments/test/kong.yml`).

**Omitted on purpose** (not forgotten): `realtime`, `storage`,
`imgproxy`, `functions` (edge runtime), `supavisor` (connection
pooler). Nothing in the current spec needs live subscriptions, file
storage, or edge functions, and a single test Postgres doesn't need a
pooler in front of it. If a later ticket needs one of these, add the
service to `docker-compose.yml` and mirror the routing block in
`kong.yml` for it — same pattern as `rest-v1`.

All images are pinned to an explicit version (no `:latest`), current as
of the versions Supabase's own `docker/docker-compose.yml` referenced
when this stack was written. Bump them deliberately, not by drift.

## Bring-up steps (test)

Requires Docker + the `docker compose` v2 plugin. Not run in this
sandbox — see "What was and wasn't run" below.

```sh
cd environments/test
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, JWT_SECRET (openssl rand -base64 48),
# and the minted SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY — see
# "Minting local Supabase keys" below. Stripe keys are only needed once
# the payments ticket (MT-13) is live; leave the placeholders until then.

docker compose up -d
docker compose ps        # all five services should report healthy
open http://localhost:${STUDIO_PORT:-3001}   # Studio, local admin UI
```

Point the app at it with `SUPABASE_URL=http://localhost:${KONG_HTTP_PORT:-8000}`
plus the two keys from `.env`.

Tear down: `docker compose down` (keeps the `db-data` volume) or
`docker compose down -v` (drops it — re-runs
`volumes/db/init/*.sql` on next `up`, test-only).

### Minting local Supabase keys

`SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` are HS256 JWTs signed
with `JWT_SECRET`, carrying `{"role": "anon"}` / `{"role":
"service_role"}`. Generate them with any JWT library once `JWT_SECRET`
is set, e.g.:

```sh
python3 - <<'PY'
import hmac, hashlib, base64, json, time

def b64url(d):
    return base64.urlsafe_b64encode(d).rstrip(b"=")

def make(role, secret):
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    now = int(time.time())
    payload = b64url(json.dumps({
        "role": role, "iss": "supabase-demo",
        "iat": now, "exp": now + 60 * 60 * 24 * 365 * 10,
    }).encode())
    signing_input = header + b"." + payload
    sig = b64url(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return (signing_input + b"." + sig).decode()

secret = "PASTE_YOUR_JWT_SECRET_HERE"
print("SUPABASE_ANON_KEY=", make("anon", secret))
print("SUPABASE_SERVICE_ROLE_KEY=", make("service_role", secret))
PY
```

These keys are meaningful only to *this* local stack (they're just JWTs
signed with a secret only these containers know) — they grant no access
to anything outside your Docker network and are not "real" Supabase
credentials.

## Bring-up steps (prod)

No compose file, no containers to stand up here — prod uses the managed
Supabase console to create the project, then `environments/prod/.env.example`
documents which values the deploy platform must inject:
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
`DATABASE_URL`, live-mode Stripe keys, `SITE_URL`. Apply the same
schema/migrations that live under `environments/test/volumes/db/init/`
to the managed project (backend-dev's migration path — this agent does
not own that step).

## Secrets discipline

- `.env` is gitignored in both `environments/test/` and
  `environments/prod/`; only `.env.example` (placeholders, no real
  values) is tracked.
- Nothing here bakes a secret into an image or a compose file — every
  credential is `${VAR}` interpolation from `.env` / the platform's
  secret manager.
- Prod secrets are never staged as a file on disk outside the deploy
  platform's own secret store; `environments/prod/.env.example` documents
  shape only.

## What was and wasn't run

This sandbox has the `docker` CLI and the `compose` v2 plugin but **no
Docker daemon** (`docker info` fails to reach `/var/run/docker.sock`) —
containers cannot actually be pulled or started here. What *was* run and
verified: `environments/check-compose.sh`, which calls `docker compose
config` — a static parse/interpolate/merge step that talks to the CLI
only, not the daemon. It passed against the real
`environments/test/docker-compose.yml`, and was confirmed to fail loudly
(non-zero exit, error to stderr) against a deliberately corrupted copy of
the same file. Actually pulling images, booting the stack, and hitting
Studio/Kong over HTTP has not been done and needs a real Docker daemon —
noted as a follow-up rather than claimed done.

## Handoffs

- Image vulnerability scanning of the pinned tags above →
  `security/appsec-engineer`.
- Multi-service orchestration/scheduling beyond a local Compose stack
  (if this ever needs to run somewhere other than a laptop/CI runner) →
  `devops/kubernetes-engineer`.
- App Dockerfile, DB schema/migrations under
  `environments/test/volumes/db/init/`, and the app's own env-var
  contract → `backend/backend-dev`.
- Network egress / secret-injection policy beyond what's declared here →
  per `docs/backlog.md` MT-18 (OPSEC gate) and MT-19 owners.
