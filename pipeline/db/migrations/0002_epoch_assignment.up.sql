-- 0002_epoch_assignment.up.sql
-- The current arm per (region, epoch) -- what the stateless web tier reads
-- to price a visitor (ADR-0001: "web tier only reads the current epoch's
-- arm"). Written once per epoch by the learner (service_role), same writer
-- as posterior.

create table if not exists public.epoch_assignment (
    region          text        not null,
    epoch_id        bigint      not null,
    price_cents     integer     not null,
    variant_id      text        not null,

    constraint epoch_assignment_pkey primary key (region, epoch_id),
    constraint epoch_assignment_price_cents_positive check (price_cents > 0),
    constraint epoch_assignment_variant_id_not_blank check (length(variant_id) > 0),

    -- Ties the served arm back to a real posterior row -- the learner
    -- cannot point an epoch at a price that isn't a tracked arm.
    constraint epoch_assignment_arm_fkey
        foreign key (region, price_cents)
        references public.posterior (region, price_cents)
);

comment on table public.epoch_assignment is
    'Current price arm per region per epoch (ADR-0001 region-epoch '
    'invariant: one arm, one price, for every visitor in a region during '
    'an epoch). Single writer: the learner cron (service_role). This is '
    'the table the serving/web tier reads to price a visitor -- via the '
    'service_role key on the server, never the anon key from the browser '
    '(see pipeline/db/README.md).';
comment on column public.epoch_assignment.epoch_id is
    'Opaque monotonic epoch identifier. Cadence (wall-clock EPOCH_HOURS vs. '
    'sample-count, per pricing_engine.py epoch_size) is an ADR-0001 '
    'flagged-open item for academic/statistician; not encoded here.';

alter table public.epoch_assignment enable row level security;

-- Same posture as posterior: no anon/authenticated grants at all. Only
-- service_role (BYPASSRLS) writes; only server-side code using the
-- service_role key reads (never exposed to the browser -- F1/F2 boundary:
-- price must be server-computed, never client-supplied or client-readable
-- via a key an attacker could reuse to enumerate other regions' prices).
revoke all on table public.epoch_assignment from anon, authenticated;
