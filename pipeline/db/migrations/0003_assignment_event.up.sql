-- 0003_assignment_event.up.sql
-- One row per visitor's FIRST assignment (sticky pin, ADR-0001: "users
-- pinned at first assignment"). visitor_id is an opaque, cookie-derived
-- token -- not itself pricing input, not an IP. No raw IP column exists
-- anywhere in this schema (F8): geolocation happens upstream of this
-- table and only its derived `region` output is ever persisted.
--
-- visitor_id is the PRIMARY KEY so "first assignment wins" is enforced by
-- the database itself: the app does `insert ... on conflict (visitor_id)
-- do nothing returning *`, then re-reads the existing row on conflict --
-- no read-then-write race is possible.

create table if not exists public.assignment_event (
    visitor_id      text        primary key,
    region          text        not null,
    epoch_id        bigint      not null,
    variant_id      text        not null,
    price_cents     integer     not null,
    -- Analytics-only. NEVER read by the pricing path -- pricing_engine.py
    -- enforces ALLOWED_PRICING_INPUTS == {"state_code"} in code, and no
    -- query in this schema or the (not-yet-built) app may join this
    -- column into a pricing decision.
    device_class    text,
    assigned_at     timestamptz not null default now(),

    constraint assignment_event_price_cents_positive check (price_cents > 0),
    constraint assignment_event_variant_id_not_blank check (length(variant_id) > 0),

    -- The assignment must reference a real (region, epoch) arm.
    constraint assignment_event_epoch_fkey
        foreign key (region, epoch_id)
        references public.epoch_assignment (region, epoch_id)
);

create index if not exists assignment_event_region_epoch_idx
    on public.assignment_event (region, epoch_id);

comment on table public.assignment_event is
    'One row per visitor''s FIRST price assignment (sticky). Analysis unit '
    'per ADR-0001 is DISTINCT visitor_id, backed here by visitor_id being '
    'the primary key. Insert-only for the anon role (see RLS below); never '
    'updated once written -- a sticky assignment does not change.';
comment on column public.assignment_event.visitor_id is
    'Opaque token (e.g. signed cookie value). Not an IP address. Treat as '
    'pseudonymous personal data for retention/DPO purposes (F8) even '
    'though it is not directly identifying on its own.';
comment on column public.assignment_event.device_class is
    'UX/conversion analytics ONLY (PRD req. 2). Structurally never read by '
    'any pricing query in this schema -- it is not referenced by any '
    'FK, trigger, or view that feeds posterior/epoch_assignment/orders.';

alter table public.assignment_event enable row level security;

revoke all on table public.assignment_event from anon, authenticated;
grant insert on table public.assignment_event to anon;

-- anon may create its own first-assignment row (and nothing else -- no
-- select/update/delete policy exists for anon, so those commands are
-- default-denied even though a table-level GRANT is absent for them too).
create policy assignment_event_anon_insert
    on public.assignment_event
    for insert
    to anon
    with check (true);

-- --------------------------------------------------------------------
-- F2 defense-in-depth: an assignment_event's price must match the price
-- that epoch_assignment says was live for that (region, epoch) at write
-- time. Primary F2 enforcement is application-layer (the assignment
-- endpoint reads epoch_assignment and echoes its price_cents back into
-- this insert); this trigger is the backstop that turns an app bug into
-- a rejected write instead of a silently-wrong sticky price. See
-- pipeline/db/README.md.
--
-- SECURITY DEFINER: anon has no SELECT grant on epoch_assignment (by
-- design -- see README "Roles & RLS"), so the lookup below must run with
-- the function owner's privileges, not the invoking (anon) role's, or
-- every legitimate anon insert fails with "permission denied" before the
-- price comparison ever happens. search_path is pinned to prevent a
-- schema-shadowing attack on a SECURITY DEFINER function.
-- --------------------------------------------------------------------

create or replace function public.assignment_event_matches_epoch()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    v_price_cents integer;
    v_variant_id  text;
begin
    select price_cents, variant_id
      into v_price_cents, v_variant_id
      from public.epoch_assignment
     where region = new.region
       and epoch_id = new.epoch_id;

    if not found then
        raise exception
            'assignment_event: no epoch_assignment for region=% epoch_id=%',
            new.region, new.epoch_id;
    end if;

    if v_price_cents is distinct from new.price_cents
       or v_variant_id is distinct from new.variant_id then
        raise exception
            'assignment_event/epoch_assignment mismatch (F2): got price_cents=% variant_id=%, epoch_assignment has price_cents=% variant_id=% for region=% epoch_id=%',
            new.price_cents, new.variant_id, v_price_cents, v_variant_id, new.region, new.epoch_id;
    end if;

    return new;
end;
$$;

create trigger assignment_event_matches_epoch_trg
    before insert on public.assignment_event
    for each row
    execute function public.assignment_event_matches_epoch();
