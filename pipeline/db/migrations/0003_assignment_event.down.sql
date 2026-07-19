-- 0003_assignment_event.down.sql
drop trigger if exists assignment_event_matches_epoch_trg on public.assignment_event;
drop function if exists public.assignment_event_matches_epoch();
drop table if exists public.assignment_event;
