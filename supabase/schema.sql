create table if not exists public.agreements (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
    kind text not null,
    party text not null,
    amount numeric(12, 2) not null default 0,
    due date,
    transcript text not null,
    verbatim text not null,
    lang text,
    status text not null default 'Pending' check (status in ('Pending', 'Confirmed')),
    created_at timestamptz not null default now(),
    confirmed_at timestamptz
);

create index if not exists agreements_user_created_idx
    on public.agreements (user_id, created_at desc);

alter table public.agreements enable row level security;

create policy "Users can read their own agreements"
    on public.agreements for select to authenticated
    using ((select auth.uid()) = user_id);

create policy "Users can create their own agreements"
    on public.agreements for insert to authenticated
    with check ((select auth.uid()) = user_id);

create policy "Users can update their own agreements"
    on public.agreements for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

create policy "Users can delete their own agreements"
    on public.agreements for delete to authenticated
    using ((select auth.uid()) = user_id);

create table if not exists public.calendar_entries (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
    title text not null,
    amount numeric(12, 2) not null default 0,
    due date not null,
    remind integer not null default 1 check (remind between 0 and 365),
    created_at timestamptz not null default now()
);

create index if not exists calendar_entries_user_due_idx
    on public.calendar_entries (user_id, due);

alter table public.calendar_entries enable row level security;

create policy "Users can read their own calendar entries"
    on public.calendar_entries for select to authenticated
    using ((select auth.uid()) = user_id);

create policy "Users can create their own calendar entries"
    on public.calendar_entries for insert to authenticated
    with check ((select auth.uid()) = user_id);

create policy "Users can update their own calendar entries"
    on public.calendar_entries for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

create policy "Users can delete their own calendar entries"
    on public.calendar_entries for delete to authenticated
    using ((select auth.uid()) = user_id);

grant select, insert, update, delete on public.agreements to authenticated;
grant select, insert, update, delete on public.calendar_entries to authenticated;
grant usage on schema public to authenticated;
