-- MyTradingAgent Supabase schema
-- Run this in Supabase SQL Editor if you use STORAGE_BACKEND=supabase_rest.
-- STORAGE_BACKEND=supabase_postgres can auto-create these tables, but running
-- this manually is still fine.

create table if not exists public.trade_plans (
    approval_id text primary key,
    payload jsonb not null,
    created_at timestamptz not null
);

create table if not exists public.trade_executions (
    id bigserial primary key,
    approval_id text,
    event_type text not null,
    payload jsonb not null,
    created_at timestamptz not null
);

create index if not exists trade_executions_approval_id_idx
    on public.trade_executions (approval_id);

create index if not exists trade_executions_created_at_idx
    on public.trade_executions (created_at desc);
