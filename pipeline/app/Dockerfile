# syntax=docker/dockerfile:1
#
# App service image — ADR-0002 Decision 3 (docs/sprint-7-26-19-26/adr/
# ADR-0002-supabase-store-environments.md): the pricing/checkout request
# path (`/assign`, `/webhook`) as a small containerized FastAPI service,
# talking to Postgres via the DAO (no Supabase client libs baked in here
# per Decision 1's guardrail).
#
# THE IMAGE IS THE CONTRACT: this exact digest is built once and promoted
# test -> prod unmodified (environments/README.md, ADR-0002 Decision 4).
# Only ${VAR} env supplied at container start differs between
# environments/test/.env and environments/prod/.env — nothing here bakes
# in DATABASE_URL, STRIPE_*, or any other secret.
#
# Build context is pipeline/ (widened from pipeline/app/ during integration
# so the image includes pricing_engine.py and web/, which main.py imports
# and serves at runtime via _PIPELINE_DIR) — see
# environments/test/docker-compose.yml's `app.build.context` and
# pipeline/.dockerignore. Image layout mirrors the repo: /app/app/main.py,
# /app/pricing_engine.py, /app/web/ — so main.py's _PIPELINE_DIR (parent of
# app/) resolves the engine and the static page exactly as in a checkout.
# Fixed contract this Dockerfile builds to (do not change without a new
# ticket): Python 3.12 FastAPI app, entry pipeline/app/main.py, ASGI
# object `app`, listens on :8000, deps in pipeline/app/requirements.txt
# (authored by backend/backend-dev, referenced here not written here),
# GET /healthz -> 200.

# ---------------------------------------------------------------------------
# Stage 1: builder — resolve + install deps into a venv. Compilers and any
# other build-only tooling live here and never reach the runtime stage.
# ---------------------------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copied first so dependency layers cache independently of app source
# changes. Context is pipeline/, so the manifest is at app/requirements.txt.
COPY app/requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime — slim base, no compilers, no pip cache, non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS runtime

# Fixed, non-login, unprivileged runtime identity.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home \
        --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Mirror the repo's pipeline/ layout into the image: /app/app (service),
# /app/pricing_engine.py (engine), /app/web (static page). pipeline/.dockerignore
# keeps db/, tests, caches, and env files out of the context.
COPY --chown=app:app . /app/

# Run from the service dir so `import store`/`stripe_gateway` (flat siblings)
# resolve via uvicorn's cwd, while main.py inserts _PIPELINE_DIR (/app) for
# `import pricing_engine` and locates /app/web/index.html.
WORKDIR /app/app

USER app

EXPOSE 8000

# Fixed contract: GET /healthz -> 200. No curl in this slim base, so use
# the interpreter that's already here rather than installing one.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u,sys; sys.exit(0 if u.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

# Config (DATABASE_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, etc.)
# comes from the process environment at container start — never baked in.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
