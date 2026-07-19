-- 0005_orders.down.sql
drop trigger if exists orders_price_matches_assignment_trg on public.orders;
drop function if exists public.orders_price_matches_assignment();
drop table if exists public.orders;
