-- 0004_impression.up.sql
-- Analytics only (PRD req. 2 / sub-issue #4). Never joined into a pricing
-- decision or into posterior/epoch_assignment. Not the sticky-assignment
-- record (that's assignment_event) -- this is page-view/impression
-- telemetry, many rows per visitor allowed.

create table if not exists public.impression (
    id              bigint      generated always as identity primary key,
    visitor_id      text        not null,
    region          text        not null,
    epoch_id        bigint      not null,
    variant_id      text        not null,
    -- Analytics-only, same rule as assignment_event.device_class: never
    -- read by any pricing query.
    device_class    text,
    occurred_at     timestamptz not null default now(),

    constraint impression_variant_id_not_blank check (length(variant_id) > 0),

    -- An impression only makes sense for a visitor who was actually
    -- assigned a price.
    constraint impression_visitor_fkey
        foreign key (visitor_id)
        references public.assignment_event (visitor_id)
);

create index if not exists impression_region_epoch_idx
    on public.impression (region, epoch_id);
create index if not exists impression_visitor_id_idx
    on public.impression (visitor_id);

comment on table public.impression is
    'Analytics-only page-view/impression log. No raw IP column (F8). '
    'device_class is present for UX/conversion analytics and is never '
    'read by a pricing query (PRD req. 2).';

alter table public.impression enable row level security;

revoke all on table public.impression from anon, authenticated;
grant insert on table public.impression to anon;

create policy impression_anon_insert
    on public.impression
    for insert
    to anon
    with check (true);
