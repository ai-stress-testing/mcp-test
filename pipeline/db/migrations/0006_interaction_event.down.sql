-- 0006_interaction_event.down.sql
drop policy if exists interaction_event_anon_insert on public.interaction_event;
drop table if exists public.interaction_event;
