-- 0006_interaction_event.up.sql
-- Anonymous interaction/heatmap capture (product-brief "owner-only
-- analytics" + "interaction heatmaps"; threat-model/opsec-gate F8).
--
-- session_id here is DELIBERATELY NOT assignment_event.visitor_id (the
-- pricing-path identifier) and is never joined to it anywhere in this
-- schema or in store.py -- keeping interaction analytics structurally
-- unlinkable to a visitor's price/order record is itself part of the F8
-- control, not an oversight. It is minted by the app the same way
-- visitor_id is (an opaque secrets.token_urlsafe cookie value), just on
-- its own separate cookie -- see main.py's ANALYTICS_COOKIE_NAME.
--
-- F8: no raw IP column, no text/keystroke capture -- only bounded
-- numeric/enum fields. event_type is a closed enum (CHECK), not free
-- text. Percent fields are 0-100 integers, enforced by CHECK as a
-- database-level backstop to the app-layer clamp in main.py's /track
-- handler (same "primary control in the app, DB CHECK/trigger as
-- backstop" pattern F2 uses in 0003/0005).

create table if not exists public.interaction_event (
    id              bigint      generated always as identity primary key,
    session_id      text        not null,
    event_type      text        not null,
    path            text        not null,
    x_pct           smallint,
    y_pct           smallint,
    scroll_pct      smallint,
    viewport_w      integer     not null,
    occurred_at     timestamptz not null default now(),

    constraint interaction_event_session_id_not_blank check (length(session_id) > 0),
    constraint interaction_event_event_type_check
        check (event_type in ('pageview', 'click', 'scroll', 'cta_view', 'cta_click')),
    constraint interaction_event_path_not_blank check (length(path) > 0 and length(path) <= 512),
    constraint interaction_event_x_pct_range check (x_pct is null or (x_pct between 0 and 100)),
    constraint interaction_event_y_pct_range check (y_pct is null or (y_pct between 0 and 100)),
    constraint interaction_event_scroll_pct_range check (scroll_pct is null or (scroll_pct between 0 and 100)),
    constraint interaction_event_viewport_w_range check (viewport_w between 0 and 20000)
);

create index if not exists interaction_event_path_event_type_idx
    on public.interaction_event (path, event_type);
create index if not exists interaction_event_occurred_at_idx
    on public.interaction_event (occurred_at);
create index if not exists interaction_event_session_id_idx
    on public.interaction_event (session_id);

comment on table public.interaction_event is
    'Anonymous interaction/heatmap capture (clicks, scroll depth, CTA '
    'funnel views). session_id is an opaque per-browser token, NEVER '
    'assignment_event.visitor_id and never FK''d to it -- analytics is '
    'structurally unlinkable to pricing/order data (F8). No raw IP, no '
    'free-text/keystroke column exists or may be added. Insert-only for '
    'anon; reads are service_role-only and only ever in aggregate (see '
    'store.py region_metrics/funnel_counts/heatmap_bins -- no endpoint in '
    'this service returns raw interaction_event rows).';
comment on column public.interaction_event.session_id is
    'Opaque token from a dedicated analytics cookie, distinct from the '
    'pricing visitor_id cookie. Not PII, not an IP, not the pricing '
    'identifier.';
comment on column public.interaction_event.event_type is
    'Closed enum, not free text: pageview | click | scroll | cta_view | '
    'cta_click.';
comment on column public.interaction_event.x_pct is
    'Click/tap X position as a 0-100 integer percent of viewport width. '
    'Null for non-positional events (pageview, scroll, cta_view).';
comment on column public.interaction_event.y_pct is
    'Click/tap Y position as a 0-100 integer percent of viewport height. '
    'Null for non-positional events.';
comment on column public.interaction_event.scroll_pct is
    'Max scroll depth as a 0-100 integer percent. Null for non-scroll '
    'events.';
comment on column public.interaction_event.viewport_w is
    'Viewport width in CSS pixels, clamped app-side (and DB-side, '
    'CHECK) to [0, 20000]. Analytics-only (bucketing/responsive context), '
    'never a pricing input.';

alter table public.interaction_event enable row level security;

-- Same posture as assignment_event/impression (0003/0004): anon may
-- INSERT its own event and nothing else. Reads (SELECT) are service_role
-- only -- no policy exists for anon/authenticated SELECT, so it is
-- default-denied even before the explicit REVOKE ALL below.
revoke all on table public.interaction_event from anon, authenticated;
grant insert on table public.interaction_event to anon;

-- Defense-in-depth mirror of the app-layer /track validation (main.py):
-- even a malicious/buggy client using the anon key directly cannot
-- insert an out-of-enum event_type or an out-of-range percent.
create policy interaction_event_anon_insert
    on public.interaction_event
    for insert
    to anon
    with check (
        event_type in ('pageview', 'click', 'scroll', 'cta_view', 'cta_click')
        and (x_pct is null or x_pct between 0 and 100)
        and (y_pct is null or y_pct between 0 and 100)
        and (scroll_pct is null or scroll_pct between 0 and 100)
    );
