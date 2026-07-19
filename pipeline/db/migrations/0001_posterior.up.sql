-- 0001_posterior.up.sql
-- ADR-0001: the learner cron is the SINGLE writer of posteriors. The web
-- tier never mutates this table; it only ever reads epoch_assignment
-- (0002), which the learner derives from this table once per epoch.
--
-- One row per (region, price_cents) = one Beta(alpha, beta) arm, matching
-- pipeline/pricing_engine.py's PriceArm(region, price, alpha, beta).
--
-- F10: price is INTEGER CENTS, never float, so the F2 amount-equality
-- check downstream (orders vs. assignment) is exact-integer, not
-- float-drift-prone. The app-layer seam (learner.py, not built yet) is
-- responsible for converting pricing_engine.py's float dollar price to
-- integer cents at the point it writes here.

create table if not exists public.posterior (
    region          text        not null,
    price_cents     integer     not null,
    alpha           double precision not null default 1.0,
    beta            double precision not null default 1.0,
    updated_epoch   bigint      not null,

    constraint posterior_pkey primary key (region, price_cents),
    constraint posterior_price_cents_positive check (price_cents > 0),
    constraint posterior_alpha_positive check (alpha > 0),
    constraint posterior_beta_positive check (beta > 0)
);

comment on table public.posterior is
    'Bandit posterior per (region, price arm). Single writer: the offline '
    'learner cron (service_role). The web/serving tier is read-only against '
    'epoch_assignment, never against this table directly. No IP or raw PII '
    'column here or anywhere in this schema (F8).';
comment on column public.posterior.price_cents is
    'Integer cents (F10) -- never a float. Avoids float-drift breaking the '
    'F2 price-integrity check between assignment and order.';
comment on column public.posterior.updated_epoch is
    'Epoch id the posterior was last updated in. Epoch cadence (time-based '
    'vs sample-count-based) is an open item flagged to academic/statistician '
    'in ADR-0001 -- kept as an opaque bigint here so that decision does not '
    'require a schema change.';

-- RLS: enabled with ZERO policies for anon/authenticated -> default-deny
-- for every command (select/insert/update/delete) for those roles. Only
-- service_role (which carries BYPASSRLS in Supabase) may read or write
-- this table. See pipeline/db/README.md "Roles & RLS".
alter table public.posterior enable row level security;

revoke all on table public.posterior from anon, authenticated;
