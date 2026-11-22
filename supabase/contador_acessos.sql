-- Contador de acessos do painel Olist (ver acessos.py).
-- Rodar uma vez no SQL Editor do Supabase. Pode ser o mesmo projeto do F1:
-- tabela e função têm nome próprio e não mexem em public.page_views.

create table if not exists public.olist_page_views (
  id smallint primary key default 1 check (id = 1),
  total bigint not null default 0
);
insert into public.olist_page_views (id, total) values (1, 0) on conflict do nothing;

-- RLS ligado e sem políticas: a publishable key (papel anon) não lê nem altera
-- a tabela direto; só executa a função abaixo, que apenas soma 1.
alter table public.olist_page_views enable row level security;

create or replace function public.increment_olist_page_views()
returns bigint
language sql
security definer
set search_path = ''
as $$
  update public.olist_page_views set total = total + 1 where id = 1 returning total;
$$;

revoke all on function public.increment_olist_page_views() from public;
grant execute on function public.increment_olist_page_views() to anon;
