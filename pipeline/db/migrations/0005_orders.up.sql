-- 0005_orders.up.sql
-- Named `orders` (plural), not the ADR/ticket's bare `order`: ORDER is a
-- reserved SQL keyword and using it unquoted breaks, and quoting it
-- everywhere forever is needless attack surface for typos. Same entity
-- the ticket specifies -- see pipeline/db/README.md "Naming note".
--
-- F6 (idempotency): stripe_session_id and stripe_event_id are each
-- UNIQUE, so duplicate webhook delivery for the same Checkout session or
-- the same Stripe event id cannot create a second order -- a retried
-- insert hits the unique violation and the app treats that as "already
-- processed" (upsert / ON CONFLICT DO NOTHING semantics), not an error.
--
-- F2 (price integrity): price_paid_cents is reconciled against the
-- visitor's assignment_event by the trigger below -- see the comment on
-- orders_price_matches_assignment().

create table if not exists public.orders (
    id                  bigint      generated always as identity primary key,
    stripe_session_id  text        not null,
    stripe_event_id    text        not null,
    visitor_id          text        not null,
    region              text        not null,
    epoch_id            bigint      not null,
    variant_id          text        not null,
    price_paid_cents    integer     not null,
    created_at          timestamptz not null default now(),

    constraint orders_stripe_session_id_unique unique (stripe_session_id),
    constraint orders_stripe_event_id_unique unique (stripe_event_id),
    constraint orders_price_paid_cents_positive check (price_paid_cents > 0),
    constraint orders_variant_id_not_blank check (length(variant_id) > 0),

    -- An order must trace back to a real sticky assignment for that
    -- visitor -- the reconcilable path F2 asks for. Equality of the
    -- price itself is enforced by the trigger below (a plain FK/CHECK
    -- can't express a cross-row/cross-table equality in Postgres).
    constraint orders_visitor_fkey
        foreign key (visitor_id)
        references public.assignment_event (visitor_id)
);

create index if not exists orders_visitor_id_idx on public.orders (visitor_id);
create index if not exists orders_created_at_idx on public.orders (created_at);

comment on table public.orders is
    'One row per fulfilled Stripe Checkout session (ADR/ticket "order"). '
    'stripe_session_id and stripe_event_id are both UNIQUE (F6): duplicate '
    'webhook delivery cannot create two orders. price_paid_cents is '
    'reconciled to the visitor''s assignment_event.price_cents by a '
    'trigger (F2). No raw IP column (F8). Single writer: the webhook '
    'handler running as service_role.';
comment on column public.orders.stripe_session_id is
    'Idempotency key (F6): UNIQUE. The webhook handler upserts on this '
    'column (ON CONFLICT DO NOTHING) so a redelivered '
    'checkout.session.completed event is a no-op, not a second order.';
comment on column public.orders.stripe_event_id is
    'The processed Stripe event id, also UNIQUE (F6) -- belt-and-suspenders '
    'against replay independent of session id reuse.';
comment on column public.orders.price_paid_cents is
    'Integer cents (F10). Must equal the visitor''s assignment_event.price_cents '
    '-- enforced primarily in the webhook handler (compare Stripe''s '
    'amount_total to the stored assignment BEFORE writing this row, per '
    'opsec-gate.md F2/F6) and backstopped by the trigger below.';

alter table public.orders enable row level security;

-- Only service_role (BYPASSRLS) may touch this table -- no anon/
-- authenticated grants at all. Orders are written exclusively by the
-- signature-verified webhook handler (F4/F6), never from the browser.
revoke all on table public.orders from anon, authenticated;

-- --------------------------------------------------------------------
-- F2 defense-in-depth: reject an order whose (region, epoch_id,
-- variant_id, price_paid_cents) doesn't match the visitor's recorded
-- assignment_event. This is a backstop, NOT the primary control -- the
-- primary F2 control is the webhook handler asserting
-- `amount_total == stored assignment price` BEFORE it ever attempts this
-- insert (opsec-gate.md F2). The trigger exists so that an application
-- bug produces a rejected write, not a silently wrong order record.
--
-- SECURITY DEFINER for the same reason as
-- assignment_event_matches_epoch() (0003): the writer here is
-- service_role, which does have its own grants, but pinning this to the
-- owner's rights (with search_path fixed against schema-shadowing) keeps
-- the validation trigger's behavior independent of whatever grants a
-- given deployment happens to give service_role.
-- --------------------------------------------------------------------

create or replace function public.orders_price_matches_assignment()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    v_region      text;
    v_epoch_id    bigint;
    v_variant_id  text;
    v_price_cents integer;
begin
    select region, epoch_id, variant_id, price_cents
      into v_region, v_epoch_id, v_variant_id, v_price_cents
      from public.assignment_event
     where visitor_id = new.visitor_id;

    if not found then
        raise exception
            'orders: no assignment_event for visitor_id=%', new.visitor_id;
    end if;

    if v_region is distinct from new.region
       or v_epoch_id is distinct from new.epoch_id
       or v_variant_id is distinct from new.variant_id
       or v_price_cents is distinct from new.price_paid_cents then
        raise exception
            'orders/assignment_event mismatch (F2): order has region=% epoch_id=% variant_id=% price_paid_cents=%, assignment_event has region=% epoch_id=% variant_id=% price_cents=% for visitor_id=%',
            new.region, new.epoch_id, new.variant_id, new.price_paid_cents,
            v_region, v_epoch_id, v_variant_id, v_price_cents, new.visitor_id;
    end if;

    return new;
end;
$$;

create trigger orders_price_matches_assignment_trg
    before insert on public.orders
    for each row
    execute function public.orders_price_matches_assignment();
